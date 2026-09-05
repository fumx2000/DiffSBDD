#!/usr/bin/env python3
"""Independent fail-closed checker for the with-TP2 readiness census V1."""

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
    covapie_completed_human_decision_reconciliation_with_tp2_v1 as reconciliation,
)
from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_with_tp2_v1 as subject,
)


BASELINE_COMMIT = "43ba4586e0275968aa252fecc7065621c0f6586f"
EXPECTED_CENSUS_SHA256 = "634f2f2d1c5a7f63d11f30bfe49eb5881edc681cfd94321a5cb5047f574b467a"
EXPECTED_SUMMARY_SHA256 = "9862d0a4434560c12c0573a7076732192d15f6b24fe73e515b049d5bcb5fc1b4"
EXPECTED_BINDINGS_SHA256 = "94a9796b82301a89e856d08cfe96aaf1915e2ab87a6d0916e44a5fd08ae5b45c"
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


def _verify_materialized_output_bytes_v1(
    expected: Mapping[str, bytes], observed: Mapping[str, bytes],
) -> None:
    if dict(observed) != dict(expected):
        raise ValueError("MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED")


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
    payload = _read(
        root / subject.TP2_RECONCILIATION_ARTIFACT_RELATIVE,
        "TP2_RECONCILIATION_ARTIFACT",
    )
    expected_bytes, expected_digest, _ = subject._TP2_RECONCILIATION_ARTIFACT_SPEC_V1
    if len(payload) != expected_bytes or _sha(payload) != expected_digest:
        raise ValueError("TP2_RECONCILIATION_ARTIFACT_BINDING_INVALID")
    queue = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "FROZEN_PRIORITY_QUEUE")
    if len(queue) != 50116 or _sha(queue) != (
        "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
    ):
        raise ValueError("FROZEN_PRIORITY_QUEUE_BINDING_INVALID")


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
    target = set(subject.TP2_EXACT4_EVENT_IDS_V1)
    if changed != target:
        raise ValueError("CHANGED_EVENTS_NOT_TP2_EXACT4")
    field_sets = {
        event: {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event][field] != after[event][field]
        }
        for event in target
    }
    if any(fields != subject._ACTUAL_CHANGED_TP2_FIELDS_V1 for fields in field_sets.values()):
        raise ValueError("ACTUAL_CHANGED_FIELDS_NOT_EXACT16")
    if any(
        before[event] != after[event]
        for event in set(before) - target
    ):
        raise ValueError("NON_TARGET_ROW_CHANGED")
    expected_target = {
        "current_global_status": "COMPLETED_HUMAN_NEGATIVE",
        "current_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "human_review_completed": "true",
        "chemistry_disposition": "POSITIVE",
        "task_relevance_disposition": "NOT_RELEVANT",
        "training_use_disposition": "NOT_APPLICABLE",
        "training_materialization_allowed_current_source": "false",
        "reactive_pair_sample_authoritative": "true",
        "role_partition_sample_authoritative": "true",
        "role_profile": subject.base.STRICT_PROFILE,
        "canonical_mask_structural_labels_available": "true",
        "structurally_applicable_task_ids_json": "[0,1,2,3,4]",
        "human_training_excluded": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    if any(
        any(after[event][field] != value for field, value in expected_target.items())
        for event in target
    ):
        raise ValueError("TP2_EXACT4_PROJECTED_SEMANTICS_INVALID")
    return {
        "changed_event_count": len(changed),
        "unchanged_event_count": len(before) - len(changed),
        "actual_changed_fields": sorted(next(iter(field_sets.values()))),
    }


def independently_verify_counts_v1(rows: Sequence[Mapping[str, str]]) -> dict[str, object]:
    if len(rows) != 1000 or any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows):
        raise ValueError("CENSUS_SCHEMA_INVALID")
    expected = {
        "chemistry": Counter({"POSITIVE": 152, "NOT_ESTABLISHED": 90, "UNRESOLVED": 758}),
        "task": Counter({"RELEVANT": 137, "NOT_RELEVANT": 106, "UNRESOLVED": 757}),
        "training": Counter(
            {"INCLUDE": 64, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 106, "UNRESOLVED": 758}
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
            "post_geometry_source_evidence_available",
            "post_geometry_training_target_available",
            "pre_geometry_authoritative",
            "pre_geometry_training_target_available",
            "training_use_include",
            "future_training_admission_candidate",
            "formal_training_admitted",
            "current_runtime_model_usable",
            "human_training_excluded",
        )
    }
    if boolean_counts != {
        "reactive_pair_sample_authoritative": 152,
        "role_partition_sample_authoritative": 144,
        "canonical_mask_structural_labels_available": 144,
        "post_geometry_sample_authoritative": 21,
        "post_geometry_source_evidence_available": 867,
        "post_geometry_training_target_available": 17,
        "pre_geometry_authoritative": 0,
        "pre_geometry_training_target_available": 0,
        "training_use_include": 64,
        "future_training_admission_candidate": 47,
        "formal_training_admitted": 5,
        "current_runtime_model_usable": 17,
        "human_training_excluded": 72,
    }:
        raise ValueError("GLOBAL_AUTHORITY_COUNTS_INVALID")
    profiles = Counter(
        row["role_profile"] for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    if profiles != Counter({subject.base.DIRECT_PROFILE: 88, subject.base.STRICT_PROFILE: 56}):
        raise ValueError("ROLE_PROFILE_COUNTS_INVALID")
    applicability: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    if applicability != Counter({0: 144, 1: 56, 2: 56, 3: 144, 4: 144}):
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
        | set(subject.TP2_EXACT4_EVENT_IDS_V1)
    )
    if orthogonal != expected_orthogonal or len(orthogonal) != 16:
        raise ValueError("ORTHOGONAL_EXACT16_INVALID")
    return {**boolean_counts, "orthogonal_count": len(orthogonal)}


def independently_verify_tp2_publications_v1(result, matrix) -> dict[str, int]:
    target = set(subject.TP2_EXACT4_EVENT_IDS_V1)
    facts = [fact for fact in result.normalized_facts if fact.canonical_event_id in target]
    matrix_rows = [row for row in matrix if row["canonical_event_id"] in target]
    if (
        len(result.source_bindings) != 24
        or len(result.normalized_facts) != 139
        or len(result.reconciled_rows) != 338
        or result.review_summary != {
            "universe_event_count": 338,
            "universe_review_unit_count": 131,
            "completed_positive_event_count": 119,
            "completed_positive_unit_count": 19,
            "completed_negative_event_count": 44,
            "completed_negative_unit_count": 9,
            "completed_total_event_count": 163,
            "completed_total_unit_count": 28,
            "in_progress_event_count": 0,
            "in_progress_unit_count": 0,
            "unreviewed_event_count": 175,
            "unreviewed_unit_count": 103,
        }
        or len(facts) != 4
        or any(
            fact.legacy_completed_review_status != "COMPLETED_HUMAN_NEGATIVE"
            or fact.task_relevance_disposition != "NOT_RELEVANT"
            or fact.chemistry_disposition != "POSITIVE"
            or fact.training_disposition != "NOT_APPLICABLE"
            or fact.human_training_excluded is not False
            for fact in facts
        )
        or len(matrix_rows) != 4
        or any(len(row) != 134 for row in matrix_rows)
        or any(
            row["completed_lane"] != "COMPLETED_TASK_DOMAIN_NEGATIVE"
            or row["negative_chemistry"] != "false"
            or row["task_domain_negative"] != "true"
            or row["role_profile"] != subject.base.STRICT_PROFILE
            or row["structurally_applicable_task_ids_json"] != "[0,1,2,3,4]"
            or row["strict_profile_applicable_task_ids_json"] != "[0,1,2,3,4]"
            or row["formal_training_admitted"] != "false"
            or row["POST_source_evidence_available"] != "true"
            or row["POST_geometry_training_authority"] != "false"
            or row["PRE_source_graph_count"] != "0"
            or row["PRE_mapping_count"] != "0"
            for row in matrix_rows
        )
    ):
        raise ValueError("TP2_MATRIX_RECONCILIATION_PUBLICATION_INVALID")
    return {"source_count": 24, "fact_count": 139, "reconciled_row_count": 338}


def verify_manifest_v1(
    root: Path, manifest: Mapping[str, object], artifacts: Mapping[str, bytes],
) -> None:
    if manifest.get("candidate_inventory") != {
        "exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)
    }:
        raise ValueError("MANIFEST_EXACT7_INVALID")
    if manifest.get("semantic_source_binding_count") != 174:
        raise ValueError("MANIFEST_BINDING_COUNT_INVALID")
    bindings = manifest.get("semantic_source_bindings")
    if type(bindings) is not list or len(bindings) != 174:
        raise ValueError("MANIFEST_BINDINGS_INVALID")
    if len({(item["path_namespace"], item["path"]) for item in bindings}) != 174:
        raise ValueError("MANIFEST_BINDING_IDENTITY_COLLISION")
    predecessor_roles = {item["artifact_role"] for item in bindings[:168]}
    additive_roles = [item["artifact_role"] for item in bindings[168:]]
    predecessor_manifest = json.loads(
        _read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    )
    if bindings[:168] != predecessor_manifest["semantic_source_bindings"]:
        raise ValueError("MANIFEST_PREDECESSOR_BINDING_PREFIX_CHANGED")
    if additive_roles != [item[0] for item in subject._ADDITIVE_SOURCE_SPECS_V1]:
        raise ValueError("MANIFEST_ADDITIVE_SOURCE_ROLES_INVALID")
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
    if manifest.get("tp2_reconciliation_artifact_validation_binding") != {
        "artifact_role": "TP2_RECONCILIATION_ARTIFACT_VALIDATION_IDENTITY",
        "path": subject.TP2_RECONCILIATION_ARTIFACT_RELATIVE.as_posix(),
        "path_namespace": "repository_relative",
        "byte_count": 335923,
        "sha256": "0869d55d446202d3d8464f69a6482e83d0994b6eccac0af3a8b01b3d9d5497eb",
        "expected_executable": False,
        "computational_source": False,
    }:
        raise ValueError("MANIFEST_TP2_RECONCILIATION_VALIDATION_BINDING_INVALID")
    lowered = artifacts[subject.MANIFEST_FILE].decode("utf-8").lower()
    for token in ('"timestamp"', '"hostname"', '"pid"', '"head"', '"ahead"', '"behind"'):
        if token in lowered:
            raise ValueError("MANIFEST_DYNAMIC_FIELD_PRESENT")


def independently_verify_next_pending_v1(
    root: Path, result, rows: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    queue_payload = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "FROZEN_PRIORITY_QUEUE")
    queue_reader = csv.DictReader(io.StringIO(queue_payload.decode("utf-8"), newline=""))
    queue = [dict(row) for row in queue_reader]
    if len(queue) != 131:
        raise ValueError("INDEPENDENT_PRIORITY_QUEUE_IDENTITY_INVALID")
    status_by_unit: dict[str, set[str]] = {}
    for row in result.reconciled_rows:
        status_by_unit.setdefault(row["raw_review_unit_id"], set()).add(row["current_review_status"])
    pending = []
    for row in queue:
        statuses = status_by_unit.get(row["review_unit_id"])
        if statuses is None or len(statuses) != 1:
            raise ValueError("INDEPENDENT_PENDING_STATUS_INVALID")
        status = next(iter(statuses))
        if status in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            pending.append((-int(row["event_count"]), int(row["priority_rank"]), row["review_unit_id"], row))
    pending.sort(key=lambda item: item[:3])
    if len(pending) != 103 or any(item[2] == subject.TP2_REVIEW_UNIT_ID_V1 for item in pending):
        raise ValueError("INDEPENDENT_PENDING_SET_INVALID")
    _negative, raw_rank, unit, first = pending[0]
    census_by_event = {row["canonical_event_id"]: row for row in rows}
    if (
        raw_rank != 28
        or unit != subject.NEXT_PENDING_REVIEW_UNIT_ID_V1
        or int(first["event_count"]) != 4
        or json.loads(first["ligand_component_ids_json"]) != ["NWJ"]
        or json.loads(first["pdb_ids_json"]) != ["4CM5"]
        or any(
            census_by_event[event]["current_review_status"] != "CURRENTLY_UNREVIEWED"
            for event in subject.NEXT_PENDING_EVENT_IDS_V1
        )
    ):
        raise ValueError("INDEPENDENT_NEXT_PENDING_NWJ_INVALID")
    return {"review_unit_id": unit, "raw_priority_rank": raw_rank, "current_pending_rank": 1}


def _expect_failure(callable_) -> None:
    try:
        callable_()
    except (subject.Cumulative1000CurrentGlobalReadinessCensusWithTP2Error, ValueError):
        return
    raise ValueError("SEMANTIC_TAMPER_ACCEPTED")


def check_semantic_probes_v1(
    root: Path, computation, frozen, result, matrix: Sequence[Mapping[str, str]],
) -> dict[str, bool]:
    target = subject.TP2_EXACT4_EVENT_IDS_V1[0]

    def mutate_row(event_id: str, **changes: str):
        rows = deepcopy(list(computation.rows))
        next(row for row in rows if row["canonical_event_id"] == event_id).update(changes)
        return replace(computation, rows=tuple(rows))

    def validate(candidate) -> None:
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_tp2_v1(
            candidate,
            repo_root=root,
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
        (target, {"role_profile": subject.base.DIRECT_PROFILE}),
        (target, {"structurally_applicable_task_ids_json": "[0,4]"}),
        (target, {"training_use_disposition": "INCLUDE", "training_use_include": "true"}),
        (target, {"formal_training_admitted": "true"}),
        (target, {"reactive_pair_training_target_available": "true"}),
        (target, {"post_geometry_training_target_available": "true"}),
        (target, {"pre_geometry_authoritative": "true"}),
    )
    for event_id, changes in row_probes:
        _expect_failure(lambda event_id=event_id, changes=changes: validate(mutate_row(event_id, **changes)))

    matrix_mutations = (
        {"canonical_event_id": target + ":TAMPER"},
        {"role_partition_human_authoritative": "false"},
        {"role_profile": subject.base.DIRECT_PROFILE},
        {"strict_profile_applicable_task_ids_json": "[0,3,4]"},
        {"B3_present": "false"},
        {"sixth_task": "true"},
        {"chemistry": "NEGATIVE"},
        {"formal_event_training_use_decision": "INCLUDE"},
        {"training_mask_targets_available_now": "true"},
    )
    for changes in matrix_mutations:
        tampered = deepcopy(list(matrix))
        tampered[0].update(changes)
        _expect_failure(lambda tampered=tampered: subject._validate_tp2_matrix_rows_v1(tampered))

    summary = deepcopy(computation.summary)
    summary["human_review"]["completed_event_count"] = 154
    _expect_failure(lambda: validate(replace(computation, summary=summary)))
    summary = deepcopy(computation.summary)
    summary["top_pending_review_units_by_event_yield"][0]["raw_priority_rank"] = 27
    _expect_failure(lambda: validate(replace(computation, summary=summary)))
    summary = deepcopy(computation.summary)
    orthogonal = summary["orthogonal_task_negative_chemistry_positive"]
    orthogonal.pop(
        "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_exact16"
    )
    orthogonal["task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_exact12"] = True
    _expect_failure(lambda: validate(replace(computation, summary=summary)))
    bindings = list(deepcopy(computation.semantic_source_bindings))
    bindings[-1]["path"] = bindings[-2]["path"]
    _expect_failure(lambda: validate(replace(computation, semantic_source_bindings=tuple(bindings))))
    return {
        "event_identity": True,
        "non_target_row": True,
        "task_chemistry_pair_role_profile_applicability": True,
        "exact5_b3_no_sixth": True,
        "training_promotions": True,
        "next_pending_summary_bindings": True,
    }


def _probe_materialized_raw_byte_rejection_v1(
    built_once: Mapping[str, bytes],
) -> bool:
    observed = dict(built_once)
    original = observed[subject.CENSUS_FILE]
    corrupted = bytearray(original)
    corrupted[-2] ^= 1
    observed[subject.CENSUS_FILE] = bytes(corrupted)
    if observed[subject.CENSUS_FILE] == original:
        raise ValueError("RAW_BYTE_PROBE_MUTATION_NOT_APPLIED")
    try:
        _verify_materialized_output_bytes_v1(built_once, observed)
    except ValueError as error:
        if str(error) != "MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED":
            raise
        return True
    raise ValueError("RAW_BYTE_PROBE_DID_NOT_FAIL")


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
    computation, frozen, result, matrix = subject._compute_components_v1(root)
    built_once = subject._build_artifacts_from_computation_v1(root, computation)
    built_twice = subject._build_artifacts_from_computation_v1(root, computation)
    if built_once != built_twice:
        raise ValueError("DOUBLE_BUILD_NOT_BYTE_IDENTICAL")
    materialized = {
        name: _read(root / subject.OUTPUT_DIRECTORY_RELATIVE / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    _verify_materialized_output_bytes_v1(built_once, materialized)
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
    if tuple(predecessor_manifest["semantic_source_bindings"]) != frozen.semantic_source_bindings:
        raise ValueError("PREDECESSOR_BINDING_PREFIX_NOT_MANIFEST_EXACT")
    publication = independently_verify_tp2_publications_v1(result, matrix)
    next_pending = independently_verify_next_pending_v1(root, result, rows)
    probes = check_semantic_probes_v1(root, computation, frozen, result, matrix)
    probes["raw_output_bytes"] = _probe_materialized_raw_byte_rejection_v1(built_once)
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
        "tp2_publication": publication,
        "next_pending": next_pending,
        "semantic_probes": probes,
        "lifecycle_simulations": lifecycle_simulations,
        "git": git,
        "deterministic_double_build": True,
    }


def main() -> int:
    result = run_check_v1()
    print("TP2_CURRENT_GLOBAL_READINESS_CENSUS_V1_PASS=true")
    print("CENSUS_ROWS=1000")
    print("CENSUS_COLUMNS=47")
    print("CHANGED_EVENT_COUNT=4")
    print("UNCHANGED_EVENT_COUNT=996")
    print("CHEMISTRY_POSITIVE_COUNT=152")
    print("TASK_NOT_RELEVANT_COUNT=106")
    print("TRAINING_NOT_APPLICABLE_COUNT=106")
    print("PAIR_AUTHORITY_COUNT=152")
    print("ROLE_AUTHORITY_COUNT=144")
    print("CANONICAL_MASK_STRUCTURAL_LABEL_COUNT=144")
    print("STRICT_PROFILE_COUNT=56")
    print("DIRECT_PROFILE_COUNT=88")
    print("TASK_NEGATIVE_CHEMISTRY_POSITIVE_POPULATION_COUNT=16")
    print("EXACT5_B3_PRESENT=true")
    print("SIXTH_TASK=false")
    print("NEXT_PRIORITY_REVIEW_LIGAND=NWJ")
    print("NEXT_PRIORITY_REVIEW_RAW_PRIORITY_RANK=28")
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
