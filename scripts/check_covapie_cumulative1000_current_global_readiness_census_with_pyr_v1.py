#!/usr/bin/env python3
"""Independent fail-closed checker for the with-PYR readiness census V1."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_with_pyr_v1 as subject,
)


BASELINE_COMMIT = "ffbe4e2cdd9f8c562623c54a2ebd42d50909766b"
EXPECTED_CENSUS_SHA256 = "e1c2b9c465401f544fe91d2641e10274cc2dd489fbb0b9a4c197779f55f405e2"
EXPECTED_SUMMARY_SHA256 = "65727588da7d18556d6e092eebbc6e91d898ff21a9bace59eb2618da43727ab8"
EXPECTED_BINDINGS_SHA256 = "c20eafc7f5409b762fdf31bf44413fb72a1cebc342e838506402c1d87c46479f"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
PROTECTED_PREFIXES = ("data/raw/", "checkpoints/", "equivariant_diffusion/")
PROTECTED_FILES = {
    "dataset.py", "lightning_modules.py", "data/prepare_crossdocked.py",
}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _checker_fail(token: str) -> None:
    raise ValueError(subject.ERROR_TOKEN + ":" + token)


def _read(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        _checker_fail("NOT_REGULAR_FILE:" + label)
    return path.read_bytes()


def _validate_text(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        _checker_fail("UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(subject.ERROR_TOKEN + ":NOT_UTF8:" + label) from error
    if "\r" in text or "\x00" in text:
        _checker_fail("TEXT_ENCODING_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        _checker_fail("FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _checker_fail("TRAILING_WHITESPACE:" + label)


def _parse_csv(payload: bytes, expected_header: Sequence[str]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(expected_header):
        _checker_fail("CSV_HEADER_INVALID")
    return [dict(row) for row in reader]


def _verify_materialized_output_bytes_v1(
    expected: Mapping[str, bytes], observed: Mapping[str, bytes],
) -> None:
    if dict(observed) != dict(expected):
        _checker_fail("MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED")


def _validate_output_inventory_names_v1(entry_names: Sequence[str]) -> None:
    expected = {subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE}
    if len(entry_names) != 3 or set(entry_names) != expected:
        _checker_fail("OUTPUT_DIRECTORY_NOT_EXACT3")


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    try:
        metadata = output.lstat()
    except OSError as error:
        raise ValueError(subject.ERROR_TOKEN + ":OUTPUT_DIRECTORY_READ_FAILED") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _checker_fail("OUTPUT_DIRECTORY_NOT_REAL_DIRECTORY")
    _validate_output_inventory_names_v1(tuple(entry.name for entry in output.iterdir()))
    records: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, relative)
        _validate_text(payload, relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode not in {0o644, 0o664} or mode & 0o111:
            _checker_fail("CANDIDATE_FILESYSTEM_MODE_INVALID:" + relative)
        if len(payload) >= 1024 * 1024:
            _checker_fail("CANDIDATE_FILE_NOT_BELOW_1_MIB:" + relative)
        records.append(
            {"path": relative, "byte_count": len(payload), "sha256": _sha(payload), "mode": mode}
        )
    return records


def verify_frozen_bindings_v1(root: Path) -> None:
    for role, relative, namespace, byte_count, digest, _executable in subject._ADDITIVE_SOURCE_SPECS_V1:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        if len(payload) != byte_count or _sha(payload) != digest:
            _checker_fail("FROZEN_SOURCE_BINDING_INVALID:" + role)
    for relative, spec, token in (
        (
            subject.PREDECESSOR_MANIFEST_RELATIVE,
            subject._PREDECESSOR_MANIFEST_SPEC_V1,
            "PREDECESSOR_MANIFEST_BINDING_INVALID",
        ),
        (
            subject.PYR_RECONCILIATION_ARTIFACT_RELATIVE,
            subject._PYR_RECONCILIATION_ARTIFACT_SPEC_V1,
            "PYR_RECONCILIATION_ARTIFACT_BINDING_INVALID",
        ),
        (
            subject.PRIORITY_QUEUE_RELATIVE,
            subject._PRIORITY_QUEUE_SPEC_V1,
            "FROZEN_PRIORITY_QUEUE_BINDING_INVALID",
        ),
    ):
        payload = _read(root / relative, token)
        if len(payload) != spec[0] or _sha(payload) != spec[1]:
            _checker_fail(token)


def independently_verify_pyr_publications_v1(
    result: object, matrix: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    if (
        len(result.source_bindings) != 27
        or len(result.normalized_facts) != 151
        or len(result.reconciled_rows) != 338
        or result.review_summary
        != {
            "universe_event_count": 338,
            "universe_review_unit_count": 131,
            "completed_positive_event_count": 127,
            "completed_positive_unit_count": 21,
            "completed_negative_event_count": 48,
            "completed_negative_unit_count": 10,
            "completed_total_event_count": 175,
            "completed_total_unit_count": 31,
            "in_progress_event_count": 0,
            "in_progress_unit_count": 0,
            "unreviewed_event_count": 163,
            "unreviewed_unit_count": 100,
        }
    ):
        _checker_fail("PYR_RECONCILIATION_PUBLICATION_INVALID")
    if (
        len(matrix) != 4
        or any(tuple(row) != subject.ingestion.MATRIX_HEADER for row in matrix)
        or len(subject.ingestion.MATRIX_HEADER) != 75
        or tuple(row["canonical_event_id"] for row in matrix) != subject.PYR_EXACT4_EVENT_IDS_V1
    ):
        _checker_fail("PYR_MATRIX_PUBLICATION_INVALID")
    expected = {
        "source_formal_generation_domain_decision": "IN_DOMAIN",
        "normalized_task_relevance_disposition": "RELEVANT",
        "source_formal_training_use_decision": "EXCLUDE",
        "normalized_training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "pair_sample_authority": "true",
        "role_sample_authority": "true",
        "task_applicability_sample_authority": "true",
        "structurally_applicable_task_ids_json": "[0,3,4]",
        "training_use_allowed": "false",
        "human_training_excluded": "true",
        "future_training_admission_candidate": "false",
        "training_materialization_allowed": "false",
    }
    if any(any(row[key] != value for key, value in expected.items()) for row in matrix):
        _checker_fail("PYR_MATRIX_NORMALIZATION_OR_AUTHORITY_INVALID")
    facts = [
        fact for fact in result.normalized_facts
        if fact.canonical_event_id in set(subject.PYR_EXACT4_EVENT_IDS_V1)
    ]
    if len(facts) != 4 or any(
        (
            fact.legacy_completed_review_status,
            fact.task_relevance_disposition,
            fact.chemistry_disposition,
            fact.training_disposition,
            fact.human_training_excluded,
        )
        != (
            "COMPLETED_HUMAN_POSITIVE", "RELEVANT", "POSITIVE",
            "EXCLUDE_FROM_TRAINING_ONLY", True,
        )
        for fact in facts
    ):
        _checker_fail("PYR_RECONCILIATION_FACTS_INVALID")
    return {"sources": 27, "facts": 151, "matrix_rows": 4, "matrix_columns": 75}


def independently_verify_delta_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    successor_rows: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    if len(predecessor_rows) != 1000 or len(successor_rows) != 1000:
        _checker_fail("ROW_COUNT_NOT_EXACT1000")
    if any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in successor_rows):
        _checker_fail("CENSUS_SCHEMA_INVALID")
    before = {row["canonical_event_id"]: row for row in predecessor_rows}
    after = {row["canonical_event_id"]: row for row in successor_rows}
    if set(before) != set(after):
        _checker_fail("EVENT_UNIVERSE_CHANGED")
    changed = {event for event in before if before[event] != after[event]}
    target = set(subject.PYR_EXACT4_EVENT_IDS_V1)
    if changed != target:
        _checker_fail("CHANGED_EVENTS_NOT_PYR_EXACT4")
    field_sets = {
        event: {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event][field] != after[event][field]
        }
        for event in target
    }
    if any(fields != subject._ACTUAL_CHANGED_PYR_FIELDS_V1 for fields in field_sets.values()):
        _checker_fail("ACTUAL_CHANGED_FIELDS_NOT_EXACT17")
    unchanged_sets = {
        event: {
            field for field in subject._AUTHORIZED_PYR_OVERLAY_FIELDS_V1
            if before[event][field] == after[event][field]
        }
        for event in target
    }
    if any(
        fields != subject._AUTHORIZED_BUT_UNCHANGED_PYR_FIELDS_V1
        for fields in unchanged_sets.values()
    ):
        _checker_fail("AUTHORIZED_BUT_UNCHANGED_FIELDS_NOT_EXACT2")
    expected = {
        "current_global_status": "COMPLETED_HUMAN_POSITIVE",
        "current_review_status": "COMPLETED_HUMAN_POSITIVE",
        "human_review_completed": "true",
        "human_review_authority_source": subject.PYR_HUMAN_DECISION_SOURCE,
        "chemistry_disposition": "POSITIVE",
        "chemistry_authority_source": subject.PYR_EVENT_MATRIX_SOURCE,
        "positive_authority_source": subject.PYR_EVENT_MATRIX_SOURCE,
        "task_relevance_disposition": "RELEVANT",
        "task_relevance_authority_source": subject.PYR_EVENT_MATRIX_SOURCE,
        "training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "human_training_excluded": "true",
        "reactive_pair_sample_authoritative": "true",
        "role_partition_sample_authoritative": "true",
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "canonical_mask_structural_labels_available": "true",
        "structurally_applicable_task_ids_json": "[0,3,4]",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "training_materialization_allowed_current_source": "false",
    }
    if any(
        any(after[event][field] != value for field, value in expected.items())
        for event in target
    ):
        _checker_fail("PYR_EXACT4_PROJECTED_SEMANTICS_INVALID")
    return {
        "pyr_changed_row_count": 4,
        "non_pyr_changed_row_count": 0,
        "unchanged_row_count": 996,
        "authorized_overlay_field_count": 19,
        "authorized_but_unchanged_field_count": 2,
        "actual_changed_field_count": 17,
    }


def independently_verify_counts_v1(
    rows: Sequence[Mapping[str, str]], summary: Mapping[str, object],
) -> dict[str, object]:
    expected = {
        "global": Counter(subject._EXPECTED_GLOBAL_STATUS_COUNTS_V1),
        "chemistry": Counter({"POSITIVE": 164, "NOT_ESTABLISHED": 90, "UNRESOLVED": 746}),
        "task": Counter({"RELEVANT": 145, "NOT_RELEVANT": 110, "UNRESOLVED": 745}),
        "training": Counter(
            {"INCLUDE": 68, "EXCLUDE_FROM_TRAINING_ONLY": 76, "NOT_APPLICABLE": 110, "UNRESOLVED": 746}
        ),
    }
    actual = {
        "global": Counter(row["current_global_status"] for row in rows),
        "chemistry": Counter(row["chemistry_disposition"] for row in rows),
        "task": Counter(row["task_relevance_disposition"] for row in rows),
        "training": Counter(row["training_use_disposition"] for row in rows),
    }
    if actual != expected:
        _checker_fail("GLOBAL_DISTRIBUTION_COUNTS_INVALID")
    positive = [row for row in rows if row["chemistry_disposition"] == "POSITIVE"]
    include = [row for row in rows if row["training_use_disposition"] == "INCLUDE"]
    boolean_counts = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "human_training_excluded", "reactive_pair_sample_authoritative",
            "role_partition_sample_authoritative",
            "canonical_mask_structural_labels_available",
            "training_use_include", "future_training_admission_candidate",
            "current_runtime_model_usable", "formal_training_admitted",
        )
    }
    if boolean_counts != {
        "human_training_excluded": 76,
        "reactive_pair_sample_authoritative": 164,
        "role_partition_sample_authoritative": 156,
        "canonical_mask_structural_labels_available": 156,
        "training_use_include": 68,
        "future_training_admission_candidate": 51,
        "current_runtime_model_usable": 17,
        "formal_training_admitted": 5,
    }:
        _checker_fail("BOOLEAN_COUNTS_INVALID")
    applicability = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    if applicability != Counter({0: 156, 1: 56, 2: 56, 3: 156, 4: 156}):
        _checker_fail("CANONICAL_APPLICABILITY_COUNTS_INVALID")
    orthogonal = {
        row["canonical_event_id"] for row in rows
        if (
            row["task_relevance_disposition"], row["chemistry_disposition"],
            row["training_use_disposition"],
        ) == ("NOT_RELEVANT", "POSITIVE", "NOT_APPLICABLE")
    }
    expected_orthogonal = (
        set(subject.GVE_EXACT4_EVENT_IDS_V1) | set(subject.LCY_EXACT4_EVENT_IDS_V1)
        | set(subject.ZERO_D8_EXACT4_EVENT_IDS_V1) | set(subject.TP2_EXACT4_EVENT_IDS_V1)
        | set(subject.SIX_OA_EXACT4_EVENT_IDS_V1)
    )
    if orthogonal != expected_orthogonal or len(orthogonal) != 20:
        _checker_fail("ORTHOGONAL_POPULATION_NOT_FROZEN_EXACT20")
    blockers = summary.get("blockers")
    if blockers != {
        **blockers,
        "chemistry_unresolved": {"all_1000": 746},
        "pair_authority_absent": {"all_1000": 836, "within_chemistry_positive": 0},
        "role_authority_absent": {"all_1000": 844, "within_chemistry_positive": 8},
        "human_training_exclusion": {"within_chemistry_positive": 76},
        "missing_split_authority": {"within_chemistry_positive": 123, "within_training_include": 43},
        "missing_POST_training_authority": {"within_chemistry_positive": 147, "within_training_include": 51},
        "missing_training_admission": {"within_chemistry_positive": 159, "within_training_include": 63},
        "feature_semantics_pending": {"within_chemistry_positive": 164},
    }:
        _checker_fail("SUMMARY_BLOCKER_POPULATIONS_INVALID")
    tensor = blockers["missing_tensor_integration"]
    if (
        tensor["within_chemistry_positive"] != 123
        or tensor["within_training_include"] != 39
        or tensor["missing_source_composition"].get("PYR") != 4
        or summary["chemistry"]["positive_source_composition"].get("PYR") != 4
        or "PYR" in summary["training_stage"]["future_candidate_source_composition"]
        or len(positive) != 164
        or len(include) != 68
    ):
        _checker_fail("SUMMARY_SOURCE_COMPOSITION_INVALID")
    for section, field, value in (
        ("chemistry", "POSITIVE", "POSITIVE"),
        ("chemistry", "UNRESOLVED", "UNRESOLVED"),
        ("task_relevance", "RELEVANT", "RELEVANT"),
        ("task_relevance", "UNRESOLVED", "UNRESOLVED"),
        ("training_use", "EXCLUDE_FROM_TRAINING_ONLY", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("training_use", "UNRESOLVED", "UNRESOLVED"),
    ):
        source_field = {
            "chemistry": "chemistry_disposition",
            "task_relevance": "task_relevance_disposition",
            "training_use": "training_use_disposition",
        }[section]
        events = {row["canonical_event_id"] for row in rows if row[source_field] == value}
        digest = subject._event_set_sha256(events)
        if summary[section][field] != {"count": len(events), "event_set_sha256": digest}:
            _checker_fail("SUMMARY_EVENT_SET_DIGEST_INVALID:" + section + ":" + field)
    return {"boolean_counts": boolean_counts, "applicability": [applicability[i] for i in range(5)]}


def independently_verify_next_pending_v1(
    root: Path, result: object, summary: Mapping[str, object],
) -> dict[str, object]:
    queue = _parse_csv(_read(root / subject.PRIORITY_QUEUE_RELATIVE, "QUEUE"), subject._QUEUE_HEADER_V1)
    statuses: dict[str, set[str]] = defaultdict(set)
    events: dict[str, list[str]] = defaultdict(list)
    for row in result.reconciled_rows:
        unit = row["raw_review_unit_id"]
        statuses[unit].add(row["current_review_status"])
        events[unit].append(row["canonical_event_id"])
    pending = []
    for row in queue:
        status_set = statuses[row["review_unit_id"]]
        if len(status_set) != 1:
            _checker_fail("PENDING_UNIT_STATUS_AMBIGUOUS")
        if next(iter(status_set)) in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            pending.append((-int(row["event_count"]), int(row["priority_rank"]), row))
    pending.sort(key=lambda item: (item[0], item[1], item[2]["review_unit_id"]))
    top = pending[0][2]
    expected = {
        "unit": subject.NEXT_PENDING_REVIEW_UNIT_ID_V1,
        "raw_priority_rank": 32,
        "event_count": 3,
        "ligands": ["ME7"],
        "pdb_ids": ["3QVY", "3QVZ"],
        "event_ids": list(subject.NEXT_PENDING_EVENT_IDS_V1),
    }
    observed = {
        "unit": top["review_unit_id"],
        "raw_priority_rank": int(top["priority_rank"]),
        "event_count": int(top["event_count"]),
        "ligands": json.loads(top["ligand_component_ids_json"]),
        "pdb_ids": json.loads(top["pdb_ids_json"]),
        "event_ids": events[top["review_unit_id"]],
    }
    first = summary["top_pending_review_units_by_event_yield"][0]
    boundary = summary["authority_boundary"]
    if (
        len(pending) != 100
        or observed != expected
        or first["rank"] != 1
        or first["raw_priority_rank"] != 32
        or first["pdb_ids"] != ["3QVY", "3QVZ"]
        or first["ligand_component_ids"] != ["ME7"]
        or boundary.get("next_priority_review_pdb_ids") != ["3QVY", "3QVZ"]
        or "next_priority_review_pdb" in boundary
        or "PYR_REVIEW_STATE_CREATED" in boundary
    ):
        _checker_fail("NEXT_PENDING_ME7_MULTI_PDB_INVALID")
    return observed


def _reject_stale_or_dynamic_manifest_v1(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if key in {"PYR_REVIEW_STATE_CREATED", "next_priority_review_pdb"}:
                _checker_fail("MANIFEST_STALE_FIELD:" + path + "." + key)
            if lowered in {
                "timestamp", "hostname", "pid", "head", "commit_subject", "ahead", "behind",
                "lifecycle_profile",
            }:
                _checker_fail("MANIFEST_DYNAMIC_FIELD:" + path + "." + key)
            if (
                "manifest" in lowered
                and "sha256" in lowered
                and item is not False
                and item is not None
            ):
                _checker_fail("MANIFEST_SELF_SHA256_RECORDED")
            _reject_stale_or_dynamic_manifest_v1(item, path + "." + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_stale_or_dynamic_manifest_v1(item, f"{path}[{index}]")
    elif isinstance(value, str) and PurePosixPath(value).is_absolute():
        _checker_fail("MANIFEST_ABSOLUTE_PATH:" + path)


def verify_manifest_v1(
    root: Path, manifest: Mapping[str, object], materialized: Mapping[str, bytes],
) -> None:
    if manifest.get("schema_version") != subject.SCHEMA_VERSION or manifest.get("stage") != subject.STAGE:
        _checker_fail("MANIFEST_SCHEMA_OR_STAGE_INVALID")
    inventory = manifest.get("candidate_inventory")
    if inventory != {"exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)}:
        _checker_fail("MANIFEST_CANDIDATE_INVENTORY_INVALID")
    expected_contract = []
    for role, relative in (
        ("PRODUCTION_OWNER", subject.PRODUCTION_RELATIVE),
        ("CHECKER", subject.CHECKER_RELATIVE),
        ("TARGETED_TESTS", subject.TEST_RELATIVE),
        ("GUIDE", subject.GUIDE_RELATIVE),
    ):
        payload = _read(root / relative, role)
        expected_contract.append(
            {"artifact_role": role, "path": relative.as_posix(), "byte_count": len(payload), "sha256": _sha(payload)}
        )
    if manifest.get("candidate_contract_bindings") != expected_contract:
        _checker_fail("MANIFEST_DYNAMIC_CONTRACT_BINDINGS_INVALID")
    predecessor_manifest = json.loads(_read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST"))
    bindings = manifest.get("semantic_source_bindings")
    predecessor_roles = {
        item["artifact_role"] for item in predecessor_manifest["semantic_source_bindings"]
    }
    additive_roles = [item["artifact_role"] for item in bindings[186:]] if isinstance(bindings, list) else []
    if (
        type(bindings) is not list
        or len(bindings) != 192
        or bindings[:186] != predecessor_manifest["semantic_source_bindings"]
        or additive_roles != [item[0] for item in subject._ADDITIVE_SOURCE_SPECS_V1]
        or len(additive_roles) != len(set(additive_roles))
        or predecessor_roles & set(additive_roles)
        or len({(item["path_namespace"], item["path"]) for item in bindings}) != 192
        or _sha(_canonical_json(bindings).encode("utf-8")) != EXPECTED_BINDINGS_SHA256
        or manifest.get("semantic_source_binding_count") != 192
    ):
        _checker_fail("MANIFEST_SEMANTIC_BINDINGS_INVALID")
    expected_outputs = [
        {
            "artifact_role": role,
            "path": (subject.OUTPUT_DIRECTORY_RELATIVE / name).as_posix(),
            "byte_count": len(materialized[name]),
            "sha256": _sha(materialized[name]),
        }
        for role, name in (
            ("REFRESHED_CENSUS_CSV", subject.CENSUS_FILE),
            ("REFRESHED_SUMMARY_JSON", subject.SUMMARY_FILE),
        )
    ]
    if manifest.get("output_bindings_excluding_manifest_self") != expected_outputs:
        _checker_fail("MANIFEST_OUTPUT_BINDINGS_INVALID")
    refresh = manifest.get("refresh_contract", {})
    expected_refresh = {
        "row_count": 1000,
        "column_count": 47,
        "pyr_overlay_event_count": 4,
        "non_pyr_changed_row_count": 0,
        "unchanged_event_count": 996,
        "authorized_overlay_field_count": 19,
        "authorized_but_unchanged_field_count": 2,
        "actual_changed_field_count_per_pyr_row": 17,
        "semantic_source_binding_count": 192,
        "predecessor_semantic_source_binding_count": 186,
        "additive_semantic_source_binding_count": 6,
        "task_negative_chemistry_positive_population_count": 20,
        "pyr_orthogonal_population_count": 0,
        "queue_refreshed": False,
        "next_review_started": False,
        "review_state_created_by_this_refresh": False,
        "me7_review_state_created": False,
        "pyr_review_completed": True,
        "pyr_reconciliation_consumed": True,
        "derived_refresh_not_new_authority": True,
        "task_label_authority": False,
        "event_task_label_rows_materialized": False,
        "training_mask_targets_created": False,
        "training_materialization_allowed": False,
        "formal_training_admitted_by_refresh": False,
        "ready_for_training": False,
        "training_started": False,
        "feature_semantics_audit_performed": False,
        "feature_semantics_audit_required_before_training": True,
    }
    if any(refresh.get(key) != value for key, value in expected_refresh.items()):
        _checker_fail("MANIFEST_REFRESH_CONTRACT_INVALID")
    digests = manifest.get("derived_projection_contract_digests")
    if digests != {
        "refreshed_census_sha256": EXPECTED_CENSUS_SHA256,
        "refreshed_summary_sha256": EXPECTED_SUMMARY_SHA256,
        "semantic_source_bindings_sha256": EXPECTED_BINDINGS_SHA256,
        "authority_created": False,
    }:
        _checker_fail("MANIFEST_DERIVED_DIGESTS_INVALID")
    if manifest.get("manifest_self_SHA256_recorded") is not False:
        _checker_fail("MANIFEST_SELF_SHA256_RECORDED")
    _reject_stale_or_dynamic_manifest_v1(manifest)


def _expect_tamper(name: str, expected_token: str, callable_: Callable[[], object]) -> str:
    try:
        callable_()
    except subject.Cumulative1000CurrentGlobalReadinessCensusWithPYRError as error:
        message = str(error)
        if not message.startswith(subject.ERROR_TOKEN + ":"):
            raise ValueError("TAMPER_WRONG_ERROR_PREFIX:" + name) from error
        if expected_token not in message:
            raise ValueError("TAMPER_WRONG_SEMANTIC_TOKEN:" + name + ":" + message) from error
        return expected_token
    except (TypeError, KeyError, AssertionError, IndexError):
        raise
    except ValueError as error:
        raise ValueError("TAMPER_WRONG_ERROR_CLASS_OR_PREFIX:" + name) from error
    raise ValueError("TAMPER_ACCEPTED:" + name)


def check_semantic_probes_v1(
    root: Path, computation: object, frozen: object, result: object,
    matrix: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    target = subject.PYR_EXACT4_EVENT_IDS_V1[0]
    non_target = next(
        row["canonical_event_id"] for row in computation.rows
        if row["canonical_event_id"] not in set(subject.PYR_EXACT4_EVENT_IDS_V1)
    )

    def mutate_row(event_id: str, **changes: str) -> object:
        rows = deepcopy(list(computation.rows))
        next(row for row in rows if row["canonical_event_id"] == event_id).update(changes)
        return replace(computation, rows=tuple(rows))

    def validate(value: object) -> bool:
        return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_pyr_v1(
            value,
            repo_root=root,
            predecessor_computation=frozen,
            reconciliation_result=result,
            matrix_rows=matrix,
        )

    probes = {
        "pyr_still_unreviewed": _expect_tamper(
            "pyr_still_unreviewed", "PYR_CHANGED_FIELD_SET_NOT_EXACT17",
            lambda: validate(mutate_row(target, current_review_status="CURRENTLY_UNREVIEWED")),
        ),
        "training_include": _expect_tamper(
            "training_include", "PYR_REFRESHED_SEMANTICS_INVALID",
            lambda: validate(mutate_row(target, training_use_disposition="INCLUDE")),
        ),
        "training_not_applicable": _expect_tamper(
            "training_not_applicable", "PYR_REFRESHED_SEMANTICS_INVALID",
            lambda: validate(mutate_row(target, training_use_disposition="NOT_APPLICABLE")),
        ),
        "human_exclusion_false": _expect_tamper(
            "human_exclusion_false", "PYR_CHANGED_FIELD_SET_NOT_EXACT17",
            lambda: validate(mutate_row(target, human_training_excluded="false")),
        ),
        "future_candidate_true": _expect_tamper(
            "future_candidate_true", "PYR_CHANGED_FIELD_SET_NOT_EXACT17",
            lambda: validate(mutate_row(target, future_training_admission_candidate="true")),
        ),
        "pair_authority_false": _expect_tamper(
            "pair_authority_false", "PYR_CHANGED_FIELD_SET_NOT_EXACT17",
            lambda: validate(mutate_row(target, reactive_pair_sample_authoritative="false")),
        ),
        "non_target_change": _expect_tamper(
            "non_target_change", "PREDECESSOR_DELTA_NOT_EXACT_PYR_EXACT4",
            lambda: validate(mutate_row(non_target, feature_semantics_status="TAMPER")),
        ),
    }
    duplicate_rows = deepcopy(list(computation.rows))
    duplicate_rows[0]["canonical_event_id"] = duplicate_rows[1]["canonical_event_id"]
    probes["duplicate_event"] = _expect_tamper(
        "duplicate_event", "CENSUS_EVENT_ID_EMPTY_OR_DUPLICATE",
        lambda: validate(replace(computation, rows=tuple(duplicate_rows))),
    )
    tampered_summary = deepcopy(computation.summary)
    tampered_summary["blockers"]["chemistry_unresolved"]["all_1000"] = 747
    probes["wrong_population_count"] = _expect_tamper(
        "wrong_population_count", "SUMMARY_NOT_EXACTLY_SOURCE_DERIVED",
        lambda: validate(replace(computation, summary=tampered_summary)),
    )
    stale_summary = deepcopy(computation.summary)
    stale_summary["authority_boundary"]["next_priority_review_pdb"] = "3QVY"
    probes["stale_single_pdb"] = _expect_tamper(
        "stale_single_pdb", "SUMMARY_STALE_KEY",
        lambda: subject._assert_no_stale_summary_keys(stale_summary),
    )
    bad_matrix = deepcopy(list(matrix))
    bad_matrix[0]["B3_present"] = "false"
    probes["b3_missing"] = _expect_tamper(
        "b3_missing", "PYR_EVENT_MATRIX_SEMANTICS_INVALID",
        lambda: subject._validate_pyr_matrix_rows_v1(bad_matrix),
    )
    bad_matrix = deepcopy(list(matrix))
    bad_matrix[0]["sixth_task"] = "true"
    probes["sixth_task"] = _expect_tamper(
        "sixth_task", "PYR_EVENT_MATRIX_SEMANTICS_INVALID",
        lambda: subject._validate_pyr_matrix_rows_v1(bad_matrix),
    )
    return probes


def _probe_materialized_raw_byte_rejection_v1(built: Mapping[str, bytes]) -> str:
    observed = dict(built)
    corrupted = bytearray(observed[subject.CENSUS_FILE])
    corrupted[-2] ^= 1
    observed[subject.CENSUS_FILE] = bytes(corrupted)
    try:
        _verify_materialized_output_bytes_v1(built, observed)
    except ValueError as error:
        message = str(error)
        if message != subject.ERROR_TOKEN + ":MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED":
            raise ValueError("RAW_BYTE_PROBE_WRONG_TOKEN") from error
        return "MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED"
    raise ValueError("TAMPER_ACCEPTED:raw_byte_corruption")


def _parse_git_index_entries_v1(
    lines: Sequence[str], expected_paths: Sequence[str],
) -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for line in lines:
        fields = line.split(maxsplit=3)
        if len(fields) != 4:
            _checker_fail("TRACKED_GIT_INDEX_RECORD_INVALID")
        mode, object_id, stage, path = fields
        if mode != "100644":
            _checker_fail("TRACKED_GIT_INDEX_MODE_INVALID")
        if stage != "0":
            _checker_fail("TRACKED_GIT_INDEX_STAGE_NOT_ZERO")
        parsed.append({"mode": mode, "object_id": object_id, "stage": stage, "path": path})
    paths = [item["path"] for item in parsed]
    if len(paths) != len(set(paths)):
        _checker_fail("TRACKED_GIT_INDEX_PATH_DUPLICATE")
    if sorted(paths) != sorted(expected_paths):
        _checker_fail("TRACKED_GIT_INDEX_PATH_SET_INVALID")
    return parsed


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
    _checker_fail("EXACT7_ARTIFACT_PLACEMENT_INVALID")


def _validate_history_scope_v1(changed: Sequence[str]) -> None:
    for path in changed:
        if path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES):
            _checker_fail("PROTECTED_HISTORY_PATH:" + path)
        if path.lower().endswith(FORBIDDEN_SUFFIXES):
            _checker_fail("FORBIDDEN_HISTORY_SUFFIX:" + path)


def _classify_repository_lifecycle_v1(
    *, branch: str, placement: str, head: str, origin: str, ahead: int, behind: int,
    baseline_is_ancestor_of_head: bool, baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool, baseline_to_head_changed_paths: Sequence[str],
    tracked_modification_count: int = 0, staged_count: int = 0,
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    changed = set(baseline_to_head_changed_paths)
    if branch != "main":
        _checker_fail("BRANCH_NOT_MAIN")
    if tracked_modification_count or staged_count:
        _checker_fail("DIRTY_TRACKED_OR_STAGED_LIFECYCLE_INVALID")
    if placement == "CANDIDATE_UNTRACKED":
        if not (
            head == origin == BASELINE_COMMIT and ahead == behind == 0
            and baseline_is_ancestor_of_head and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head and not changed
        ):
            _checker_fail("CANDIDATE_UNTRACKED_LIFECYCLE_INVALID")
        return placement
    if placement != "TRACKED_CLEAN":
        _checker_fail("LIFECYCLE_PLACEMENT_INVALID")
    _validate_history_scope_v1(tuple(changed))
    if (
        head == BASELINE_COMMIT or behind != 0 or ahead < 0
        or not baseline_is_ancestor_of_head or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head or not expected <= changed
    ):
        _checker_fail("TRACKED_CLEAN_LIFECYCLE_INVALID")
    if (ahead == 0) != (origin == head):
        _checker_fail("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")
    return placement


def check_lifecycle_simulations_v1() -> dict[str, bool]:
    expected = list(subject.EXACT7_PATHS_V1)
    candidate = dict(
        branch="main", placement="CANDIDATE_UNTRACKED",
        head=BASELINE_COMMIT, origin=BASELINE_COMMIT, ahead=0, behind=0,
        baseline_is_ancestor_of_head=True, baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True, baseline_to_head_changed_paths=[],
    )
    if _classify_repository_lifecycle_v1(**candidate) != "CANDIDATE_UNTRACKED":
        _checker_fail("CANDIDATE_SIMULATION_FAILED")
    tracked = {
        **candidate,
        "placement": "TRACKED_CLEAN", "head": "successor", "ahead": 1,
        "baseline_to_head_changed_paths": expected,
    }
    if _classify_repository_lifecycle_v1(**tracked) != "TRACKED_CLEAN":
        _checker_fail("COMMITTED_UNPUSHED_SIMULATION_FAILED")
    _classify_repository_lifecycle_v1(
        **{**tracked, "head": "successor", "origin": "successor", "ahead": 0}
    )
    _classify_repository_lifecycle_v1(
        **{**tracked, "head": "descendant", "origin": "descendant", "ahead": 0}
    )
    return {
        "candidate_untracked": True,
        "committed_unpushed": True,
        "published_successor": True,
        "legal_descendant": True,
    }


def _is_ancestor(root: Path, older: str, newer: str) -> bool:
    return subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer), cwd=root,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def verify_git_safety_v1(root: Path) -> dict[str, object]:
    tracked = _git(root, "ls-files", "--", *subject.EXACT7_PATHS_V1)
    tracked_stage = _git(root, "ls-files", "--stage", "--", *subject.EXACT7_PATHS_V1)
    index_entries: list[dict[str, str]] = []
    if tracked:
        index_entries = _parse_git_index_entries_v1(tracked_stage, subject.EXACT7_PATHS_V1)
    all_untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    expected = set(subject.EXACT7_PATHS_V1)
    exact_untracked = [path for path in all_untracked if path in expected]
    placement = _classify_exact7_artifact_placement_v1(tracked, exact_untracked)
    if set(all_untracked) != set(exact_untracked):
        _checker_fail("ORDINARY_UNTRACKED_NOT_EXACT7")
    modified = _git(root, "diff", "--name-only")
    staged = _git(root, "diff", "--cached", "--name-only")
    if modified or staged:
        _checker_fail("TRACKED_OR_STAGED_DIRTY")
    branch = _git(root, "branch", "--show-current")[0]
    head = _git(root, "rev-parse", "HEAD")[0]
    origin = _git(root, "rev-parse", "origin/main")[0]
    ahead, behind = map(
        int, _git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main")[0].split()
    )
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
    if any(path.lower().endswith(FORBIDDEN_SUFFIXES) for path in all_untracked):
        _checker_fail("FORBIDDEN_UNTRACKED_SUFFIX")
    if any(
        path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES)
        for path in (*modified, *staged, *all_untracked)
    ):
        _checker_fail("PROTECTED_SOURCE_DIRTY")
    return {
        "lifecycle": lifecycle,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(all_untracked),
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "forbidden_file_count": 0,
        "protected_source_diff_count": 0,
        "git_index_mode_checked": bool(tracked),
        "expected_git_publication_mode": "100644",
        "git_index_entries": index_entries,
    }


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    records = verify_exact7_inventory_v1(root)
    verify_frozen_bindings_v1(root)
    computation, frozen, result, matrix = subject._compute_components_v1(root)
    built_once = subject._build_artifacts_from_computation_v1(root, computation)
    built_twice = subject._build_artifacts_from_computation_v1(root, computation)
    if built_once != built_twice:
        _checker_fail("DOUBLE_BUILD_NOT_BYTE_IDENTICAL")
    materialized = {
        name: _read(root / subject.OUTPUT_DIRECTORY_RELATIVE / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    _verify_materialized_output_bytes_v1(built_once, materialized)
    if _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256:
        _checker_fail("CENSUS_DIGEST_INVALID")
    if _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256:
        _checker_fail("SUMMARY_DIGEST_INVALID")
    predecessor_rows = _parse_csv(
        _read(root / subject.PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS"),
        subject.CENSUS_COLUMNS_V1,
    )
    rows = _parse_csv(materialized[subject.CENSUS_FILE], subject.CENSUS_COLUMNS_V1)
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    manifest = json.loads(materialized[subject.MANIFEST_FILE])
    delta = independently_verify_delta_v1(predecessor_rows, rows)
    counts = independently_verify_counts_v1(rows, summary)
    publication = independently_verify_pyr_publications_v1(result, matrix)
    next_pending = independently_verify_next_pending_v1(root, result, summary)
    verify_manifest_v1(root, manifest, materialized)
    probes = check_semantic_probes_v1(root, computation, frozen, result, matrix)
    probes["raw_output_bytes"] = _probe_materialized_raw_byte_rejection_v1(built_once)
    lifecycle_simulations = check_lifecycle_simulations_v1()
    git = verify_git_safety_v1(root)
    boundary = summary["authority_boundary"]
    required_false = (
        "NEXT_REVIEW_STARTED", "QUEUE_REFRESH", "QUEUE_REFRESH_PERFORMED",
        "ME7_REVIEW_STATE_CREATED", "review_state_created_by_this_refresh",
        "READY_FOR_TRAINING", "READY_FOR_FORMAL_TRAINING", "TRAINING_STARTED",
        "NEW_HUMAN_AUTHORITY_CREATED", "NEW_SCIENTIFIC_AUTHORITY_CREATED",
        "NEW_REUSABLE_AUTHORITY_CREATED", "TASK_LABEL_AUTHORITY",
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED", "MASK_TENSOR_TARGETS_CREATED",
        "FORMAL_TRAINING_ADMITTED", "TRAINING_MATERIALIZATION_ALLOWED",
        "PARAMETER_UPDATE_AUTHORIZATION", "FEATURE_SEMANTICS_AUDIT_PERFORMED",
    )
    if any(boundary[key] is not False for key in required_false):
        _checker_fail("AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if (
        boundary["PYR_REVIEW_COMPLETED"] is not True
        or boundary["PYR_RECONCILIATION_CONSUMED"] is not True
        or boundary["CENSUS_REFRESH_PERFORMED"] is not True
        or boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING"] is not True
        or boundary["STEP12D_STATUS"]
        != "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
    ):
        _checker_fail("AUTHORITY_OR_FEATURE_AUDIT_WARNING_MISSING")
    return {
        "status": "PASS",
        "records": records,
        "delta": delta,
        "counts": counts,
        "pyr_publication": publication,
        "next_pending": next_pending,
        "semantic_probes": probes,
        "lifecycle_simulations": lifecycle_simulations,
        "git": git,
        "materialized_equals_fresh_build": True,
        "deterministic_double_build": True,
    }


def main() -> int:
    result = run_check_v1()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_PYR_V1_PASS=true")
    print("PYR_OVERLAY_EVENT_COUNT=4")
    print("NON_PYR_CHANGED_ROW_COUNT=0")
    print("UNCHANGED_ROW_COUNT=996")
    print("AUTHORIZED_OVERLAY_FIELD_COUNT=19")
    print("AUTHORIZED_BUT_UNCHANGED_FIELD_COUNT=2")
    print("ACTUAL_CHANGED_FIELD_COUNT=17")
    print("CURRENTLY_UNREVIEWED=163")
    print("COMPLETED_HUMAN_POSITIVE=127")
    print("COMPLETED_HUMAN_NEGATIVE=78")
    print("CHEMISTRY_POSITIVE_COUNT=164")
    print("TASK_RELEVANT_COUNT=145")
    print("HUMAN_TRAINING_EXCLUDED_COUNT=76")
    print("TRAINING_INCLUDE_COUNT=68")
    print("FUTURE_TRAINING_ADMISSION_CANDIDATE_COUNT=51")
    print("REACTIVE_PAIR_SAMPLE_AUTHORITATIVE_COUNT=164")
    print("ROLE_PARTITION_SAMPLE_AUTHORITATIVE_COUNT=156")
    print("CANONICAL_TASK_APPLICABILITY_COUNTS=[156,56,56,156,156]")
    print("ORTHOGONAL_TASK_NEGATIVE_CHEMISTRY_POSITIVE_COUNT=20")
    print("NEXT_PRIORITY_REVIEW_LIGAND=ME7")
    print('NEXT_PRIORITY_REVIEW_PDB_IDS=["3QVY","3QVZ"]')
    print("NEXT_PRIORITY_REVIEW_RAW_PRIORITY_RANK=32")
    print("NEXT_PRIORITY_REVIEW_CURRENT_PENDING_RANK=1")
    print("NEXT_PRIORITY_REVIEW_EVENT_COUNT=3")
    print("NEXT_PRIORITY_REVIEW_UNIT=COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129")
    print("PREDECESSOR_SEMANTIC_SOURCE_BINDING_COUNT=186")
    print("SUCCESSOR_SEMANTIC_SOURCE_BINDING_COUNT=192")
    print("CENSUS_REFRESH_PERFORMED=true")
    print("QUEUE_REFRESH_PERFORMED=false")
    print("NEXT_REVIEW_STARTED=false")
    print("ME7_REVIEW_STATE_CREATED=false")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
