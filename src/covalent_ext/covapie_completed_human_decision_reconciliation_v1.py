"""Reconcile completed human decisions without interpreting chemistry details.

This additive, metadata-only owner projects the frozen FFQ and POA formal
human decisions into a small event-level contract and overlays those facts on
the committed historical cumulative1000 review reconciliation in memory.  It
does not write files, modify the historical reconciliation, infer roles or
chemistry, create reusable authority, admit samples, tensorize data, or train
a model.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import csv
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from . import (
    covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1
    as ffq_owner,
)


SCHEMA_VERSION = "covapie_completed_human_decision_reconciliation_v1"

HISTORICAL_RECONCILIATION_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1/"
    "covapie_cumulative1000_current_review_status_reconciliation_v1.csv"
)
HISTORICAL_RECONCILIATION_BYTE_COUNT = 99335
HISTORICAL_RECONCILIATION_SHA256 = (
    "4eb608e2d97b60230ae1e0ca4e4be6a7fe8b3dc45af3467cbc98f685c385862f"
)

FFQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    ffq_owner.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
FFQ_FORMAL_DECISION_BYTE_COUNT = ffq_owner.FORMAL_DECISION_BYTE_COUNT
FFQ_FORMAL_DECISION_SHA256 = ffq_owner.FORMAL_DECISION_SHA256
FFQ_FORMAL_DECISION_SCHEMA = "covapie_ffq_formal_human_decision_v1"
FFQ_REVIEW_UNIT_ID = ffq_owner.EXPECTED_REVIEW_UNIT_ID

POA_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "POA_COVAPIE_BULK_REVIEW_UNIT_6A4D564E712634EB/"
    "formal-human-decision-v1/poa_formal_human_decision_v1.json"
)
POA_FORMAL_DECISION_BYTE_COUNT = 15675
POA_FORMAL_DECISION_SHA256 = (
    "263eec2e33a7b50001f6c058959b9218601fc7fb122dc97e937b517f98c90ba8"
)
POA_FORMAL_DECISION_SCHEMA = "covapie_poa_formal_human_decision_v1"
POA_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_6A4D564E712634EB"

HISTORICAL_RECONCILIATION_HEADER = (
    "raw_priority_rank",
    "raw_review_unit_id",
    "raw_unit_event_count",
    "canonical_event_id",
    "current_review_status",
    "current_status_authority_sources_json",
    "calibration_eligible",
    "calibration_exclusion_reason",
)

CURRENTLY_UNREVIEWED = "CURRENTLY_UNREVIEWED"
CURRENTLY_IN_PROGRESS = "CURRENTLY_IN_PROGRESS"
COMPLETED_HUMAN_POSITIVE = "COMPLETED_HUMAN_POSITIVE"
COMPLETED_HUMAN_NEGATIVE = "COMPLETED_HUMAN_NEGATIVE"
COMPLETED_PARTIAL_AUTHORITY = "COMPLETED_PARTIAL_AUTHORITY"
CURRENT_RUNTIME_MODEL_USABLE = "CURRENT_RUNTIME_MODEL_USABLE"
PUBLISHED_EXACT_AUTO_NEGATIVE = "PUBLISHED_EXACT_AUTO_NEGATIVE"

TASK_RELEVANT = "RELEVANT"
TASK_NOT_RELEVANT = "NOT_RELEVANT"
CHEMISTRY_POSITIVE = "POSITIVE"
CHEMISTRY_NEGATIVE = "NEGATIVE"
CHEMISTRY_NOT_ESTABLISHED = "NOT_ESTABLISHED"
TRAINING_INCLUDE = "INCLUDE"
TRAINING_EXCLUDE = "EXCLUDE_FROM_TRAINING_ONLY"
TRAINING_NOT_APPLICABLE = "NOT_APPLICABLE"

_TASK_RELEVANCE_VALUES = frozenset((TASK_RELEVANT, TASK_NOT_RELEVANT))
_CHEMISTRY_VALUES = frozenset(
    (CHEMISTRY_POSITIVE, CHEMISTRY_NEGATIVE, CHEMISTRY_NOT_ESTABLISHED)
)
_TRAINING_VALUES = frozenset(
    (TRAINING_INCLUDE, TRAINING_EXCLUDE, TRAINING_NOT_APPLICABLE)
)
_LEGACY_COMPLETED_VALUES = frozenset(
    (COMPLETED_HUMAN_POSITIVE, COMPLETED_HUMAN_NEGATIVE)
)
_HISTORICAL_REVIEW_STATUS_VALUES = frozenset(
    (
        CURRENTLY_UNREVIEWED,
        CURRENTLY_IN_PROGRESS,
        COMPLETED_HUMAN_POSITIVE,
        COMPLETED_HUMAN_NEGATIVE,
        COMPLETED_PARTIAL_AUTHORITY,
        CURRENT_RUNTIME_MODEL_USABLE,
        PUBLISHED_EXACT_AUTO_NEGATIVE,
    )
)
_SOURCE_PATH_NAMESPACES = frozenset(
    ("repository_relative", "repository_parent_relative", "synthetic")
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class CompletedDecisionReconciliationError(ValueError):
    """Raised whenever completed-decision reconciliation cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationError(token)


@dataclass(frozen=True, slots=True)
class SourceBinding:
    """Strict provenance for one source-specific formal human decision."""

    source_path: str
    path_namespace: str
    byte_count: int
    sha256: str
    schema_version: str
    review_unit_id: str

    @property
    def stable_identity(self) -> str:
        return f"{self.path_namespace}:{self.source_path}@{self.sha256}"


@dataclass(frozen=True, slots=True)
class NormalizedCompletedDecisionFact:
    """Population-neutral event fact consumed by the generic reconciler."""

    canonical_event_id: str
    review_unit_id: str
    human_review_completed: bool
    legacy_completed_review_status: str
    task_relevance_disposition: str
    chemistry_disposition: str
    training_disposition: str
    human_training_excluded: bool
    source_decision_schema: str
    source_decision_sha256: str
    source_binding_path: str


@dataclass(frozen=True, slots=True)
class NormalizedDecisionSource:
    """One verified source binding and its complete normalized review unit."""

    binding: SourceBinding
    facts: tuple[NormalizedCompletedDecisionFact, ...]


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Deterministic in-memory result; no materialization method is exposed."""

    reconciled_rows: tuple[dict[str, str], ...]
    source_bindings: tuple[SourceBinding, ...]
    normalized_facts: tuple[NormalizedCompletedDecisionFact, ...]
    review_summary: dict[str, int]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _reject_json_constant(value: str) -> None:
    _fail("JSON_NONFINITE_CONSTANT:" + value)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result


def _strict_json_value(payload: bytes, label: str) -> Any:
    if type(payload) is not bytes:
        _fail("SOURCE_PAYLOAD_NOT_BYTES:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CompletedDecisionReconciliationError(
            "SOURCE_PAYLOAD_NOT_UTF8:" + label
        ) from error
    if text.startswith("\ufeff") or "\x00" in text:
        _fail("SOURCE_PAYLOAD_TEXT_INVARIANT_INVALID:" + label)
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as error:
        raise CompletedDecisionReconciliationError(
            "SOURCE_JSON_PARSE_FAILED:" + label
        ) from error


def _strict_json_object(payload: bytes, label: str) -> dict[str, Any]:
    value = _strict_json_value(payload, label)
    if type(value) is not dict:
        _fail("SOURCE_JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _validate_stable_relative_path(path: str, label: str) -> None:
    if type(path) is not str or not path or "\\" in path:
        _fail("SOURCE_PATH_INVALID:" + label)
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        _fail("SOURCE_PATH_INVALID:" + label)


def _validate_source_binding(binding: SourceBinding) -> None:
    if type(binding) is not SourceBinding:
        _fail("SOURCE_BINDING_TYPE_INVALID")
    _validate_stable_relative_path(binding.source_path, "binding")
    if binding.path_namespace not in _SOURCE_PATH_NAMESPACES:
        _fail("SOURCE_PATH_NAMESPACE_INVALID")
    if type(binding.byte_count) is not int or binding.byte_count <= 0:
        _fail("SOURCE_BYTE_COUNT_INVALID")
    if type(binding.sha256) is not str or not _SHA256_PATTERN.fullmatch(
        binding.sha256
    ):
        _fail("SOURCE_SHA256_INVALID")
    if type(binding.schema_version) is not str or not binding.schema_version:
        _fail("SOURCE_SCHEMA_INVALID")
    if type(binding.review_unit_id) is not str or not binding.review_unit_id:
        _fail("SOURCE_REVIEW_UNIT_INVALID")


def _verified_source_binding(
    payload: bytes,
    *,
    source_path: str,
    path_namespace: str,
    expected_byte_count: int,
    expected_sha256: str,
    expected_schema: str,
    expected_review_unit_id: str,
    label: str,
) -> tuple[SourceBinding, dict[str, Any]]:
    if type(payload) is not bytes:
        _fail("SOURCE_PAYLOAD_NOT_BYTES:" + label)
    if len(payload) != expected_byte_count:
        _fail("SOURCE_BYTE_COUNT_MISMATCH:" + label)
    observed_sha = _sha256(payload)
    if observed_sha != expected_sha256:
        _fail("SOURCE_SHA256_MISMATCH:" + label)
    formal = _strict_json_object(payload, label)
    if formal.get("schema_version") != expected_schema:
        _fail("SOURCE_SCHEMA_MISMATCH:" + label)
    if formal.get("review_unit_id") != expected_review_unit_id:
        _fail("SOURCE_REVIEW_UNIT_MISMATCH:" + label)
    binding = SourceBinding(
        source_path=source_path,
        path_namespace=path_namespace,
        byte_count=len(payload),
        sha256=observed_sha,
        schema_version=expected_schema,
        review_unit_id=expected_review_unit_id,
    )
    _validate_source_binding(binding)
    return binding, formal


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _fact(
    *,
    event_id: str,
    binding: SourceBinding,
    training_disposition: str,
    human_training_excluded: bool,
) -> NormalizedCompletedDecisionFact:
    return NormalizedCompletedDecisionFact(
        canonical_event_id=event_id,
        review_unit_id=binding.review_unit_id,
        human_review_completed=True,
        legacy_completed_review_status=COMPLETED_HUMAN_POSITIVE,
        task_relevance_disposition=TASK_RELEVANT,
        chemistry_disposition=CHEMISTRY_POSITIVE,
        training_disposition=training_disposition,
        human_training_excluded=human_training_excluded,
        source_decision_schema=binding.schema_version,
        source_decision_sha256=binding.sha256,
        source_binding_path=binding.source_path,
    )


def _project_ffq_decision_mapping_v1(
    formal: Mapping[str, Any], binding: SourceBinding
) -> NormalizedDecisionSource:
    """Project already-bound FFQ semantics without reading role/family fields."""

    _validate_source_binding(binding)
    if (
        binding.schema_version != FFQ_FORMAL_DECISION_SCHEMA
        or binding.review_unit_id != FFQ_REVIEW_UNIT_ID
        or formal.get("schema_version") != binding.schema_version
        or formal.get("review_unit_id") != binding.review_unit_id
        or formal.get("decision_status")
        != "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION"
        or formal.get("human_review_decision_created") is not True
        or formal.get("human_approval_recorded") is not True
        or formal.get("ligand_component_id") != "FFQ"
    ):
        _fail("FFQ_FORMAL_DECISION_IDENTITY_INVALID")
    approval = _require_mapping(
        formal.get("human_approval"), "FFQ_HUMAN_APPROVAL_INVALID"
    )
    if approval.get("approval_recorded") is not True:
        _fail("FFQ_HUMAN_APPROVAL_INVALID")
    unit = _require_mapping(
        formal.get("unit_level_human_decisions"), "FFQ_UNIT_DECISION_INVALID"
    )
    if (
        unit.get("training_domain_relevance_decision")
        != "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
        or unit.get("chemistry_identity_decision")
        != "COVALENT_CHEMISTRY_SUPPORTED"
        or unit.get("chemistry_negative") is not False
        or unit.get("task_domain_negative") is not False
    ):
        _fail("FFQ_UNIT_DECISION_INVALID")
    events = _require_list(
        formal.get("event_level_human_decisions"), "FFQ_EVENTS_NOT_LIST"
    )
    if len(events) != 8:
        _fail("FFQ_EXACT8_EVENT_COUNT_INVALID")
    observed_ids: set[str] = set()
    pdb_counts: Counter[str] = Counter()
    facts: list[NormalizedCompletedDecisionFact] = []
    for raw_value in events:
        raw = _require_mapping(raw_value, "FFQ_EVENT_NOT_OBJECT")
        event_id = raw.get("canonical_event_id")
        pdb_id = raw.get("pdb_id")
        if type(event_id) is not str or not event_id:
            _fail("FFQ_EVENT_ID_INVALID")
        if event_id in observed_ids:
            _fail("FFQ_EVENT_ID_DUPLICATE")
        observed_ids.add(event_id)
        if pdb_id not in {"3VCY", "4R7U"}:
            _fail("FFQ_EVENT_PDB_INVALID")
        if f":{pdb_id}:" not in event_id or not event_id.endswith(":FFQ:C1"):
            _fail("FFQ_CANONICAL_EVENT_IDENTITY_INVALID")
        pdb_counts[str(pdb_id)] += 1
        if (
            raw.get("chemistry_identity") != "COVALENT_CHEMISTRY_SUPPORTED"
            or raw.get("negative_chemistry", False) is not False
            or raw.get("task_domain_negative", False) is not False
        ):
            _fail("FFQ_EVENT_CHEMISTRY_DISPOSITION_INVALID")
        excluded = pdb_id == "4R7U"
        training = TRAINING_EXCLUDE if excluded else TRAINING_INCLUDE
        if raw.get("event_training_use_decision") != training:
            _fail("FFQ_EVENT_TRAINING_DISPOSITION_INVALID")
        facts.append(
            _fact(
                event_id=event_id,
                binding=binding,
                training_disposition=training,
                human_training_excluded=excluded,
            )
        )
    if pdb_counts != Counter({"3VCY": 4, "4R7U": 4}):
        _fail("FFQ_EXACT4_BY_PDB_INVALID")
    return NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_ffq_formal_decision_v1(payload: bytes) -> NormalizedDecisionSource:
    """SHA-bind and project the published FFQ exact8 formal decision."""

    binding, formal = _verified_source_binding(
        payload,
        source_path=FFQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        expected_byte_count=FFQ_FORMAL_DECISION_BYTE_COUNT,
        expected_sha256=FFQ_FORMAL_DECISION_SHA256,
        expected_schema=FFQ_FORMAL_DECISION_SCHEMA,
        expected_review_unit_id=FFQ_REVIEW_UNIT_ID,
        label="FFQ_FORMAL_DECISION",
    )
    return _project_ffq_decision_mapping_v1(formal, binding)


def _project_poa_decision_mapping_v1(
    formal: Mapping[str, Any], binding: SourceBinding
) -> NormalizedDecisionSource:
    """Project already-bound POA semantics without consuming role/Exact5 fields."""

    _validate_source_binding(binding)
    if (
        binding.schema_version != POA_FORMAL_DECISION_SCHEMA
        or binding.review_unit_id != POA_REVIEW_UNIT_ID
        or formal.get("schema_version") != binding.schema_version
        or formal.get("review_unit_id") != binding.review_unit_id
        or formal.get("decision_status")
        != "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION"
        or formal.get("human_review_decision_created") is not True
        or formal.get("human_approval_recorded") is not True
        or formal.get("ligand_component_id") != "POA"
    ):
        _fail("POA_FORMAL_DECISION_IDENTITY_INVALID")
    approval = _require_mapping(
        formal.get("human_approval"), "POA_HUMAN_APPROVAL_INVALID"
    )
    if approval.get("approval_recorded") is not True:
        _fail("POA_HUMAN_APPROVAL_INVALID")
    transition = _require_mapping(
        formal.get("local_review_transition"), "POA_REVIEW_TRANSITION_INVALID"
    )
    if (
        transition.get("prior_review_state") != CURRENTLY_UNREVIEWED
        or transition.get("materialized_review_state") != "COMPLETED_HUMAN_REVIEW"
        or transition.get("local_completed_human_review_delta") != 16
    ):
        _fail("POA_REVIEW_TRANSITION_INVALID")
    unit = _require_mapping(
        formal.get("unit_level_human_decisions"), "POA_UNIT_DECISION_INVALID"
    )
    if (
        unit.get("exact_event_count") != 16
        or unit.get("completed_human_review_event_count") != 16
        or unit.get("chemistry_positive_event_count") != 16
        or unit.get("chemistry_negative_event_count") != 0
        or unit.get("human_training_excluded_positive_event_count") != 8
        or unit.get("subgroup_count") != 2
    ):
        _fail("POA_UNIT_DECISION_INVALID")
    groups = _require_list(
        formal.get("subgroup_human_decisions"), "POA_SUBGROUPS_NOT_LIST"
    )
    if len(groups) != 2:
        _fail("POA_EXACT2_SUBGROUP_COUNT_INVALID")
    by_pdb: dict[str, Mapping[str, Any]] = {}
    for raw_group in groups:
        group = _require_mapping(raw_group, "POA_SUBGROUP_NOT_OBJECT")
        pdb_id = group.get("pdb_id")
        if pdb_id not in {"4I3U", "4I3V"} or pdb_id in by_pdb:
            _fail("POA_SUBGROUP_IDENTITY_INVALID")
        by_pdb[str(pdb_id)] = group
    if set(by_pdb) != {"4I3U", "4I3V"}:
        _fail("POA_SUBGROUP_COVERAGE_INVALID")

    observed_ids: set[str] = set()
    facts: list[NormalizedCompletedDecisionFact] = []
    for pdb_id in ("4I3U", "4I3V"):
        group = by_pdb[pdb_id]
        excluded = pdb_id == "4I3V"
        training = TRAINING_EXCLUDE if excluded else TRAINING_INCLUDE
        if (
            group.get("CHEMISTRY_POSITIVE") is not True
            or group.get("chemistry_identity")
            != "COVALENT_CHEMISTRY_SUPPORTED"
            or group.get("negative_chemistry") is not False
            or group.get("TASK_RELEVANT_COVALENT_EVENT") is not True
            or group.get("task_domain_negative") is not False
            or group.get("event_training_use_decision") != training
            or group.get("human_training_excluded") is not excluded
            or group.get("ligand_component_id") != "POA"
            or group.get("ligand_reactive_atom_id") != "C2"
            or group.get("protein_component_id") != "CYS"
            or group.get("protein_reactive_atom_id") != "SG"
        ):
            _fail("POA_SUBGROUP_DISPOSITION_INVALID:" + pdb_id)
        expected_scope = TRAINING_EXCLUDE if excluded else "NONE"
        if group.get("training_exclusion_scope") != expected_scope:
            _fail("POA_SUBGROUP_TRAINING_EXCLUSION_INVALID:" + pdb_id)
        if excluded and group.get("training_exclusion_disposition") != (
            "HUMAN_EXCLUDE_FROM_TRAINING_ONLY"
        ):
            _fail("POA_SUBGROUP_TRAINING_EXCLUSION_INVALID:" + pdb_id)
        event_ids = _require_list(
            group.get("canonical_event_ids"), "POA_EVENT_IDS_NOT_LIST:" + pdb_id
        )
        if group.get("event_count") != 8 or len(event_ids) != 8:
            _fail("POA_EXACT8_SUBGROUP_EVENT_COUNT_INVALID:" + pdb_id)
        for event_id in event_ids:
            if type(event_id) is not str or not event_id:
                _fail("POA_EVENT_ID_INVALID")
            if event_id in observed_ids:
                _fail("POA_EVENT_ID_DUPLICATE")
            if f":{pdb_id}:" not in event_id or not event_id.endswith(":POA:C2"):
                _fail("POA_CANONICAL_EVENT_IDENTITY_INVALID")
            observed_ids.add(event_id)
            facts.append(
                _fact(
                    event_id=event_id,
                    binding=binding,
                    training_disposition=training,
                    human_training_excluded=excluded,
                )
            )
    if len(observed_ids) != 16:
        _fail("POA_EXACT16_EVENT_COVERAGE_INVALID")
    return NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_poa_formal_decision_v1(payload: bytes) -> NormalizedDecisionSource:
    """SHA-bind and project the frozen POA exact16 formal decision."""

    binding, formal = _verified_source_binding(
        payload,
        source_path=POA_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        path_namespace="repository_parent_relative",
        expected_byte_count=POA_FORMAL_DECISION_BYTE_COUNT,
        expected_sha256=POA_FORMAL_DECISION_SHA256,
        expected_schema=POA_FORMAL_DECISION_SCHEMA,
        expected_review_unit_id=POA_REVIEW_UNIT_ID,
        label="POA_FORMAL_DECISION",
    )
    return _project_poa_decision_mapping_v1(formal, binding)


def parse_historical_reconciliation_csv_v1(
    payload: bytes,
) -> tuple[dict[str, str], ...]:
    """Parse the frozen reconciliation schema without writing or regenerating it."""

    if type(payload) is not bytes:
        _fail("HISTORICAL_RECONCILIATION_NOT_BYTES")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CompletedDecisionReconciliationError(
            "HISTORICAL_RECONCILIATION_NOT_UTF8"
        ) from error
    if text.startswith("\ufeff") or "\x00" in text or "\r" in text:
        _fail("HISTORICAL_RECONCILIATION_TEXT_INVARIANT_INVALID")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != HISTORICAL_RECONCILIATION_HEADER:
        _fail("HISTORICAL_RECONCILIATION_HEADER_INVALID")
    try:
        rows = tuple(dict(row) for row in reader)
    except csv.Error as error:
        raise CompletedDecisionReconciliationError(
            "HISTORICAL_RECONCILIATION_CSV_INVALID"
        ) from error
    _validate_historical_rows(rows)
    return rows


def _parse_authority_sources(value: str, event_id: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise CompletedDecisionReconciliationError(
            "AUTHORITY_SOURCE_JSON_MALFORMED:" + event_id
        ) from error
    if (
        type(parsed) is not list
        or not parsed
        or any(type(item) is not str or not item for item in parsed)
        or len(parsed) != len(set(parsed))
    ):
        _fail("AUTHORITY_SOURCE_JSON_INVALID:" + event_id)
    return parsed


def _validate_historical_rows(
    rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    if not rows:
        _fail("HISTORICAL_RECONCILIATION_EMPTY")
    copied: list[dict[str, str]] = []
    seen_events: set[str] = set()
    unit_events: dict[str, set[str]] = defaultdict(set)
    unit_counts: dict[str, set[int]] = defaultdict(set)
    unit_ranks: dict[str, set[int]] = defaultdict(set)
    unit_statuses: dict[str, set[str]] = defaultdict(set)
    for raw in rows:
        if type(raw) is not dict or tuple(raw) != HISTORICAL_RECONCILIATION_HEADER:
            _fail("HISTORICAL_ROW_SCHEMA_INVALID")
        row = dict(raw)
        event_id = row["canonical_event_id"]
        unit_id = row["raw_review_unit_id"]
        if not event_id or event_id in seen_events:
            _fail("HISTORICAL_CANONICAL_EVENT_DUPLICATE_OR_EMPTY")
        if not unit_id:
            _fail("HISTORICAL_REVIEW_UNIT_EMPTY:" + event_id)
        seen_events.add(event_id)
        try:
            rank = int(row["raw_priority_rank"])
            raw_count = int(row["raw_unit_event_count"])
        except ValueError as error:
            raise CompletedDecisionReconciliationError(
                "HISTORICAL_NUMERIC_FIELD_INVALID:" + event_id
            ) from error
        if rank <= 0 or raw_count <= 0:
            _fail("HISTORICAL_NUMERIC_FIELD_INVALID:" + event_id)
        _parse_authority_sources(
            row["current_status_authority_sources_json"], event_id
        )
        status = row["current_review_status"]
        if status not in _HISTORICAL_REVIEW_STATUS_VALUES:
            _fail("HISTORICAL_REVIEW_STATUS_INVALID:" + event_id)
        expected_eligible = "true" if status == CURRENTLY_UNREVIEWED else "false"
        expected_reason = "" if status == CURRENTLY_UNREVIEWED else status
        if (
            row["calibration_eligible"] != expected_eligible
            or row["calibration_exclusion_reason"] != expected_reason
        ):
            _fail("HISTORICAL_RECONCILIATION_FIELD_INCONSISTENT:" + event_id)
        unit_events[unit_id].add(event_id)
        unit_counts[unit_id].add(raw_count)
        unit_ranks[unit_id].add(rank)
        unit_statuses[unit_id].add(status)
        copied.append(row)
    for unit_id, events in unit_events.items():
        if (
            len(unit_counts[unit_id]) != 1
            or next(iter(unit_counts[unit_id])) != len(events)
        ):
            _fail("RAW_UNIT_EVENT_COUNT_INCONSISTENT:" + unit_id)
        if len(unit_ranks[unit_id]) != 1:
            _fail("RAW_UNIT_PRIORITY_RANK_INCONSISTENT:" + unit_id)
        if len(unit_statuses[unit_id]) != 1:
            _fail("HISTORICAL_REVIEW_UNIT_STATUS_MIXED:" + unit_id)
    return tuple(copied)


def _validate_fact(
    fact: NormalizedCompletedDecisionFact, binding: SourceBinding
) -> None:
    if type(fact) is not NormalizedCompletedDecisionFact:
        _fail("NORMALIZED_FACT_TYPE_INVALID")
    if type(fact.canonical_event_id) is not str or not fact.canonical_event_id:
        _fail("NORMALIZED_EVENT_ID_INVALID")
    if fact.review_unit_id != binding.review_unit_id:
        _fail("FACT_SOURCE_REVIEW_UNIT_MISMATCH:" + fact.canonical_event_id)
    if fact.human_review_completed is not True:
        _fail("HUMAN_REVIEW_NOT_COMPLETED:" + fact.canonical_event_id)
    if fact.legacy_completed_review_status not in _LEGACY_COMPLETED_VALUES:
        _fail("LEGACY_COMPLETED_STATUS_INVALID:" + fact.canonical_event_id)
    if fact.task_relevance_disposition not in _TASK_RELEVANCE_VALUES:
        _fail("TASK_RELEVANCE_DISPOSITION_INVALID:" + fact.canonical_event_id)
    if fact.chemistry_disposition not in _CHEMISTRY_VALUES:
        _fail("CHEMISTRY_DISPOSITION_INVALID:" + fact.canonical_event_id)
    if fact.training_disposition not in _TRAINING_VALUES:
        _fail("TRAINING_DISPOSITION_INVALID:" + fact.canonical_event_id)
    if type(fact.human_training_excluded) is not bool:
        _fail("HUMAN_TRAINING_EXCLUDED_NOT_BOOLEAN:" + fact.canonical_event_id)
    if (fact.training_disposition == TRAINING_EXCLUDE) != (
        fact.human_training_excluded is True
    ):
        _fail("TRAINING_EXCLUSION_INCONSISTENT:" + fact.canonical_event_id)
    if (
        fact.source_decision_schema != binding.schema_version
        or fact.source_decision_sha256 != binding.sha256
        or fact.source_binding_path != binding.source_path
    ):
        _fail("FACT_SOURCE_PROVENANCE_MISMATCH:" + fact.canonical_event_id)

    if fact.task_relevance_disposition == TASK_NOT_RELEVANT:
        if (
            fact.legacy_completed_review_status != COMPLETED_HUMAN_NEGATIVE
            or fact.training_disposition != TRAINING_NOT_APPLICABLE
        ):
            _fail(
                "TASK_NOT_RELEVANT_DISPOSITION_INVALID:"
                + fact.canonical_event_id
            )
        return
    if fact.chemistry_disposition == CHEMISTRY_POSITIVE:
        if (
            fact.legacy_completed_review_status != COMPLETED_HUMAN_POSITIVE
            or fact.training_disposition
            not in {TRAINING_INCLUDE, TRAINING_EXCLUDE}
        ):
            _fail("POSITIVE_REVIEW_DISPOSITION_INVALID:" + fact.canonical_event_id)
        return
    if fact.chemistry_disposition == CHEMISTRY_NEGATIVE:
        if (
            fact.legacy_completed_review_status != COMPLETED_HUMAN_NEGATIVE
            or fact.training_disposition != TRAINING_NOT_APPLICABLE
        ):
            _fail("NEGATIVE_REVIEW_DISPOSITION_INVALID:" + fact.canonical_event_id)
        return
    _fail("RELEVANT_CHEMISTRY_NOT_ESTABLISHED:" + fact.canonical_event_id)


def _review_summary(rows: Sequence[Mapping[str, str]]) -> dict[str, int]:
    status_events: Counter[str] = Counter()
    status_units: dict[str, set[str]] = defaultdict(set)
    unit_statuses: dict[str, set[str]] = defaultdict(set)
    all_units: set[str] = set()
    for row in rows:
        status = row["current_review_status"]
        unit_id = row["raw_review_unit_id"]
        status_events[status] += 1
        status_units[status].add(unit_id)
        unit_statuses[unit_id].add(status)
        all_units.add(unit_id)
    mixed_units = [unit for unit, statuses in unit_statuses.items() if len(statuses) != 1]
    if mixed_units:
        _fail("RECONCILED_REVIEW_UNIT_STATUS_MIXED:" + sorted(mixed_units)[0])
    completed_units = (
        status_units[COMPLETED_HUMAN_POSITIVE]
        | status_units[COMPLETED_HUMAN_NEGATIVE]
    )
    return {
        "universe_event_count": len(rows),
        "universe_review_unit_count": len(all_units),
        "completed_positive_event_count": status_events[COMPLETED_HUMAN_POSITIVE],
        "completed_positive_unit_count": len(
            status_units[COMPLETED_HUMAN_POSITIVE]
        ),
        "completed_negative_event_count": status_events[COMPLETED_HUMAN_NEGATIVE],
        "completed_negative_unit_count": len(
            status_units[COMPLETED_HUMAN_NEGATIVE]
        ),
        "completed_total_event_count": (
            status_events[COMPLETED_HUMAN_POSITIVE]
            + status_events[COMPLETED_HUMAN_NEGATIVE]
        ),
        "completed_total_unit_count": len(completed_units),
        "in_progress_event_count": status_events[CURRENTLY_IN_PROGRESS],
        "in_progress_unit_count": len(status_units[CURRENTLY_IN_PROGRESS]),
        "unreviewed_event_count": status_events[CURRENTLY_UNREVIEWED],
        "unreviewed_unit_count": len(status_units[CURRENTLY_UNREVIEWED]),
    }


def reconcile_completed_human_decisions_v1(
    historical_rows: Sequence[Mapping[str, str]],
    sources: Sequence[NormalizedDecisionSource],
) -> ReconciliationResult:
    """Apply complete review-unit facts to historical rows, entirely in memory."""

    rows = [dict(row) for row in _validate_historical_rows(historical_rows)]
    by_event = {row["canonical_event_id"]: row for row in rows}
    unit_events: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        unit_events[row["raw_review_unit_id"]].add(row["canonical_event_id"])

    ordered_sources: list[NormalizedDecisionSource] = []
    seen_bindings: set[str] = set()
    for source in sources:
        if type(source) is not NormalizedDecisionSource:
            _fail("NORMALIZED_SOURCE_TYPE_INVALID")
        _validate_source_binding(source.binding)
        if source.binding.stable_identity in seen_bindings:
            _fail("SOURCE_BINDING_DUPLICATE:" + source.binding.stable_identity)
        seen_bindings.add(source.binding.stable_identity)
        ordered_sources.append(source)
    ordered_sources.sort(
        key=lambda source: (
            source.binding.path_namespace,
            source.binding.source_path,
            source.binding.sha256,
        )
    )

    supplied_events: dict[str, str] = {}
    ordered_facts: list[NormalizedCompletedDecisionFact] = []
    for source in ordered_sources:
        binding = source.binding
        if not source.facts:
            _fail("SOURCE_FACTS_EMPTY:" + binding.stable_identity)
        source_event_ids: set[str] = set()
        for fact in source.facts:
            _validate_fact(fact, binding)
            event_id = fact.canonical_event_id
            if event_id in source_event_ids:
                _fail("SOURCE_CANONICAL_EVENT_DUPLICATE:" + event_id)
            source_event_ids.add(event_id)
            if event_id not in by_event:
                _fail("EVENT_NOT_IN_HISTORICAL_UNIVERSE:" + event_id)
            if by_event[event_id]["raw_review_unit_id"] != fact.review_unit_id:
                _fail("FACT_HISTORICAL_REVIEW_UNIT_MISMATCH:" + event_id)
            if event_id in supplied_events:
                _fail("CROSS_SOURCE_EVENT_COLLISION:" + event_id)
            supplied_events[event_id] = binding.stable_identity
            ordered_facts.append(fact)
        if binding.review_unit_id not in unit_events:
            _fail("SOURCE_REVIEW_UNIT_NOT_IN_HISTORICAL_UNIVERSE")
        if source_event_ids != unit_events[binding.review_unit_id]:
            _fail("SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH:" + binding.review_unit_id)

    for fact in ordered_facts:
        row = by_event[fact.canonical_event_id]
        if row["current_review_status"] != CURRENTLY_UNREVIEWED:
            _fail("PRIOR_REVIEW_STATUS_NOT_UNREVIEWED:" + fact.canonical_event_id)

    for fact in sorted(ordered_facts, key=lambda item: item.canonical_event_id):
        row = by_event[fact.canonical_event_id]
        row["current_review_status"] = fact.legacy_completed_review_status
        row["current_status_authority_sources_json"] = _canonical_json(
            [fact.source_binding_path]
        )
        row["calibration_eligible"] = "false"
        row["calibration_exclusion_reason"] = fact.legacy_completed_review_status

    reconciled_rows = tuple(rows)
    _validate_historical_rows(reconciled_rows)
    bindings = tuple(source.binding for source in ordered_sources)
    facts = tuple(
        sorted(
            ordered_facts,
            key=lambda fact: (
                fact.canonical_event_id,
                fact.source_binding_path,
                fact.source_decision_sha256,
            ),
        )
    )
    return ReconciliationResult(
        reconciled_rows=reconciled_rows,
        source_bindings=bindings,
        normalized_facts=facts,
        review_summary=_review_summary(reconciled_rows),
    )


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        _fail("REAL_SOURCE_NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationError(
            "REAL_SOURCE_READ_FAILED:" + label
        ) from error


def load_real_historical_reconciliation_v1(
    repo_root: Path,
) -> tuple[dict[str, str], ...]:
    """Read and SHA-bind the committed historical CSV without modifying it."""

    payload = _read_regular_file(
        repo_root.resolve() / HISTORICAL_RECONCILIATION_RELATIVE,
        "HISTORICAL_RECONCILIATION",
    )
    if len(payload) != HISTORICAL_RECONCILIATION_BYTE_COUNT:
        _fail("HISTORICAL_RECONCILIATION_BYTE_COUNT_MISMATCH")
    if _sha256(payload) != HISTORICAL_RECONCILIATION_SHA256:
        _fail("HISTORICAL_RECONCILIATION_SHA256_MISMATCH")
    return parse_historical_reconciliation_csv_v1(payload)


def load_real_completed_decision_sources_v1(
    repo_root: Path, *, include_poa: bool = True
) -> tuple[NormalizedDecisionSource, ...]:
    """Read-only loader for the frozen FFQ and optional POA formal decisions."""

    root = repo_root.resolve()
    ffq_payload = _read_regular_file(
        root.parent / FFQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
        "FFQ_FORMAL_DECISION",
    )
    sources = [project_ffq_formal_decision_v1(ffq_payload)]
    if include_poa:
        poa_payload = _read_regular_file(
            root.parent / POA_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
            "POA_FORMAL_DECISION",
        )
        sources.append(project_poa_formal_decision_v1(poa_payload))
    return tuple(sources)


def reconcile_real_completed_human_decisions_v1(
    repo_root: Path, *, include_poa: bool = True
) -> ReconciliationResult:
    """Run the strict real-state reconciliation smoke entirely in memory."""

    rows = load_real_historical_reconciliation_v1(repo_root)
    sources = load_real_completed_decision_sources_v1(
        repo_root, include_poa=include_poa
    )
    return reconcile_completed_human_decisions_v1(rows, sources)
