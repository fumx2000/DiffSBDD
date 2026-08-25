"""Add frozen G3H decisions to the published generic reconciliation V1.

This metadata-only successor owns only the G3H source binding and normalized
projection.  The predecessor remains the sole owner of historical parsing,
FFQ/POA projection, source ordering, collision and review-unit coverage checks,
and the in-memory reconciliation algorithm.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from . import covapie_completed_human_decision_reconciliation_v1 as predecessor


__all__ = (
    "CompletedDecisionReconciliationWithG3HError",
    "project_g3h_formal_decision_v1",
    "load_real_completed_decision_sources_with_g3h_v1",
    "reconcile_real_completed_human_decisions_with_g3h_v1",
)


_G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "G3H_COVAPIE_BULK_REVIEW_UNIT_5C788252BB9BA078/"
    "formal-human-decision-v1/g3h_formal_human_decision_v1.json"
)
_G3H_FORMAL_DECISION_BYTE_COUNT = 22456
_G3H_FORMAL_DECISION_SHA256 = (
    "872ac01500180f752928aeb2fb44287b7fa9cad7070e1b17a45f0d19b25d5203"
)
_G3H_FORMAL_DECISION_SCHEMA = "covapie_g3h_formal_human_decision_v1"
_G3H_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_5C788252BB9BA078"
_G3H_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:A:CYS:291-:SG:I:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:B:CYS:291-:SG:K:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:C:CYS:291-:SG:M:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:D:CYS:291-:SG:O:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:E:CYS:291-:SG:Q:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:F:CYS:291-:SG:S:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:G:CYS:291-:SG:U:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:H:CYS:291-:SG:W:G3H:C1",
)


class CompletedDecisionReconciliationWithG3HError(ValueError):
    """Raised when the G3H-specific successor contract cannot be proven."""


def _fail(token: str) -> None:
    raise CompletedDecisionReconciliationWithG3HError(token)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("G3H_JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    _fail("G3H_JSON_NONFINITE_CONSTANT:" + value)


def _strict_json_object(payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CompletedDecisionReconciliationWithG3HError(
            "G3H_SOURCE_NOT_UTF8"
        ) from error
    if text.startswith("\ufeff") or "\x00" in text:
        _fail("G3H_SOURCE_TEXT_INVARIANT_INVALID")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as error:
        raise CompletedDecisionReconciliationWithG3HError(
            "G3H_SOURCE_JSON_PARSE_FAILED"
        ) from error
    if type(value) is not dict:
        _fail("G3H_SOURCE_JSON_ROOT_NOT_OBJECT")
    return value


def _require_mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _require_list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _validate_g3h_binding(binding: predecessor.SourceBinding) -> None:
    if type(binding) is not predecessor.SourceBinding:
        _fail("G3H_SOURCE_BINDING_TYPE_INVALID")
    if (
        binding.source_path
        != _G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        or binding.path_namespace != "repository_parent_relative"
        or binding.byte_count != _G3H_FORMAL_DECISION_BYTE_COUNT
        or binding.sha256 != _G3H_FORMAL_DECISION_SHA256
        or binding.schema_version != _G3H_FORMAL_DECISION_SCHEMA
        or binding.review_unit_id != _G3H_REVIEW_UNIT_ID
    ):
        _fail("G3H_SOURCE_BINDING_INVALID")


def _project_g3h_decision_mapping_v1(
    formal: Mapping[str, Any], binding: predecessor.SourceBinding
) -> predecessor.NormalizedDecisionSource:
    """Project already-bound G3H review facts without reading role/pair fields."""

    _validate_g3h_binding(binding)
    if (
        formal.get("schema_version") != _G3H_FORMAL_DECISION_SCHEMA
        or formal.get("decision_status")
        != "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION"
        or formal.get("review_unit_id") != _G3H_REVIEW_UNIT_ID
        or formal.get("pdb_id") != "4I3W"
        or formal.get("ligand_component_id") != "G3H"
        or formal.get("exact_event_count") != 8
        or formal.get("human_review_completed") is not True
        or formal.get("human_decision_created") is not True
        or formal.get("human_review_decision_created") is not True
        or formal.get("human_approval_recorded") is not True
        or formal.get("formal_authority_created") is not True
    ):
        _fail("G3H_FORMAL_DECISION_IDENTITY_INVALID")

    approval = _require_mapping(
        formal.get("human_approval"), "G3H_HUMAN_APPROVAL_INVALID"
    )
    if approval.get("approval_recorded") is not True:
        _fail("G3H_HUMAN_APPROVAL_INVALID")

    unit = _require_mapping(
        formal.get("unit_level_human_decisions"),
        "G3H_UNIT_DECISION_INVALID",
    )
    expected_unit_values = {
        "exact_event_count": 8,
        "completed_human_review_event_count": 8,
        "task_relevance_decision": predecessor.TASK_RELEVANT,
        "task_relevant_event_count": 8,
        "chemistry_support_disposition": predecessor.CHEMISTRY_POSITIVE,
        "chemistry_positive_event_count": 8,
        "chemistry_negative_event_count": 0,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "human_training_excluded_positive_event_count": 8,
        "training_admission_created": False,
        "training_dataset_changed": False,
    }
    if any(
        type(unit.get(key)) is not type(value) or unit.get(key) != value
        for key, value in expected_unit_values.items()
    ):
        _fail("G3H_UNIT_DECISION_INVALID")

    canonical_ids = _require_list(
        formal.get("canonical_event_ids"), "G3H_CANONICAL_IDS_NOT_LIST"
    )
    if len(canonical_ids) != 8:
        _fail("G3H_CANONICAL_EXACT8_COUNT_INVALID")
    if any(type(event_id) is not str or not event_id for event_id in canonical_ids):
        _fail("G3H_CANONICAL_EVENT_ID_INVALID")
    if len(set(canonical_ids)) != 8:
        _fail("G3H_CANONICAL_EVENT_ID_DUPLICATE")
    if set(canonical_ids) != set(_G3H_EVENT_IDS):
        _fail("G3H_CANONICAL_EVENT_COVERAGE_INVALID")

    events = _require_list(
        formal.get("event_level_human_decisions"), "G3H_EVENTS_NOT_LIST"
    )
    if len(events) != 8:
        _fail("G3H_EXACT8_EVENT_COUNT_INVALID")

    facts: list[predecessor.NormalizedCompletedDecisionFact] = []
    observed_ids: set[str] = set()
    for raw_value in events:
        raw = _require_mapping(raw_value, "G3H_EVENT_NOT_OBJECT")
        event_id = raw.get("canonical_event_id")
        if type(event_id) is not str or not event_id:
            _fail("G3H_EVENT_ID_INVALID")
        if event_id in observed_ids:
            _fail("G3H_EVENT_ID_DUPLICATE")
        observed_ids.add(event_id)
        if event_id not in _G3H_EVENT_IDS:
            _fail("G3H_EVENT_ID_UNEXPECTED")
        if raw.get("pdb_id") != "4I3W":
            _fail("G3H_EVENT_PDB_INVALID:" + event_id)
        if raw.get("human_task_relevance_decision") != predecessor.TASK_RELEVANT:
            _fail("G3H_EVENT_TASK_RELEVANCE_INVALID:" + event_id)
        if (
            raw.get("human_chemistry_support_disposition")
            != predecessor.CHEMISTRY_POSITIVE
            or raw.get("negative_chemistry") is not False
            or raw.get("task_domain_negative") is not False
        ):
            _fail("G3H_EVENT_CHEMISTRY_DISPOSITION_INVALID:" + event_id)
        if (
            raw.get("human_event_training_use_disposition")
            != predecessor.TRAINING_EXCLUDE
            or raw.get("human_training_excluded") is not True
            or raw.get("training_admitted") is not False
        ):
            _fail("G3H_EVENT_TRAINING_DISPOSITION_INVALID:" + event_id)
        if raw.get("decision_finalized") is not True:
            _fail("G3H_EVENT_DECISION_NOT_FINALIZED:" + event_id)
        facts.append(
            predecessor.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=binding.review_unit_id,
                human_review_completed=True,
                legacy_completed_review_status=(
                    predecessor.COMPLETED_HUMAN_POSITIVE
                ),
                task_relevance_disposition=predecessor.TASK_RELEVANT,
                chemistry_disposition=predecessor.CHEMISTRY_POSITIVE,
                training_disposition=predecessor.TRAINING_EXCLUDE,
                human_training_excluded=True,
                source_decision_schema=binding.schema_version,
                source_decision_sha256=binding.sha256,
                source_binding_path=binding.source_path,
            )
        )
    if observed_ids != set(_G3H_EVENT_IDS):
        _fail("G3H_EXACT8_EVENT_COVERAGE_INVALID")
    return predecessor.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(sorted(facts, key=lambda fact: fact.canonical_event_id)),
    )


def project_g3h_formal_decision_v1(
    payload: bytes,
) -> predecessor.NormalizedDecisionSource:
    """SHA-bind and project the frozen G3H Exact8 formal human decision."""

    if type(payload) is not bytes:
        _fail("G3H_SOURCE_PAYLOAD_NOT_BYTES")
    if len(payload) != _G3H_FORMAL_DECISION_BYTE_COUNT:
        _fail("G3H_SOURCE_BYTE_COUNT_MISMATCH")
    observed_sha256 = _sha256(payload)
    if observed_sha256 != _G3H_FORMAL_DECISION_SHA256:
        _fail("G3H_SOURCE_SHA256_MISMATCH")
    formal = _strict_json_object(payload)
    binding = predecessor.SourceBinding(
        source_path=(
            _G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=len(payload),
        sha256=observed_sha256,
        schema_version=_G3H_FORMAL_DECISION_SCHEMA,
        review_unit_id=_G3H_REVIEW_UNIT_ID,
    )
    return _project_g3h_decision_mapping_v1(formal, binding)


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        _fail("REAL_SOURCE_NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWithG3HError(
            "REAL_SOURCE_READ_FAILED:" + label
        ) from error


def load_real_completed_decision_sources_with_g3h_v1(
    repo_root: Path,
) -> tuple[predecessor.NormalizedDecisionSource, ...]:
    """Load the frozen FFQ, POA, and G3H formal decisions read-only."""

    root = repo_root.resolve()
    parent = root.parent
    ffq = predecessor.project_ffq_formal_decision_v1(
        _read_regular_file(
            parent / predecessor.FFQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
            "FFQ_FORMAL_DECISION",
        )
    )
    poa = predecessor.project_poa_formal_decision_v1(
        _read_regular_file(
            parent / predecessor.POA_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
            "POA_FORMAL_DECISION",
        )
    )
    g3h = project_g3h_formal_decision_v1(
        _read_regular_file(
            parent / _G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
            "G3H_FORMAL_DECISION",
        )
    )
    sources = (ffq, poa, g3h)
    if len({source.binding.review_unit_id for source in sources}) != 3:
        _fail("REAL_SOURCE_REVIEW_UNIT_IDENTITIES_NOT_EXACT3")
    if len({source.binding.stable_identity for source in sources}) != 3:
        _fail("REAL_SOURCE_STABLE_IDENTITIES_NOT_EXACT3")
    return sources


def reconcile_real_completed_human_decisions_with_g3h_v1(
    repo_root: Path,
) -> predecessor.ReconciliationResult:
    """Reconcile historical plus FFQ, POA, and G3H facts entirely in memory."""

    historical_rows = predecessor.load_real_historical_reconciliation_v1(repo_root)
    sources = load_real_completed_decision_sources_with_g3h_v1(repo_root)
    return predecessor.reconcile_completed_human_decisions_v1(
        historical_rows,
        sources,
    )
