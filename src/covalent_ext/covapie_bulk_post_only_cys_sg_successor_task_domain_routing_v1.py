"""Additive live task-domain routing for the CovaPIE post-only population.

This successor consumes the frozen legacy candidate population, the current
human-review overlay, and registered exact auto-negative gates.  It decides
only whether unit-level task-domain relevance still requires human review.  It
does not create chemistry, family, production, training, or event authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
import csv
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

from covalent_ext import covapie_bulk_post_only_cys_sg_human_review_v1 as review
from covalent_ext import covapie_post_only_auto_negative_ts_dump_exact_v1 as gate
from covalent_ext import (
    covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1
    as dtt_gate,
)


SCHEMA_VERSION = (
    "covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1"
)
STAGE = SCHEMA_VERSION
SNAPSHOT_SEMANTICS = (
    "CURRENT_HUMAN_BOUND_SUCCESSOR_TASK_DOMAIN_ROUTING_SNAPSHOT"
)
BASE_SUCCESSOR_COMMIT_ANCESTOR = (
    "57c59a40c29aec0c929b3c0848ce93c5af584f28"
)
BASE_SUCCESSOR_COMMIT_SUBJECT = (
    "fix CovaPIE TS dUMP shadow artifact descendant determinism v1"
)
DTT_GATE_PUBLICATION_COMMIT = "c49ee4e67318cd2cf09e8ef0cddd913ad2642772"
DTT_GATE_PUBLICATION_SUBJECT = (
    "add CovaPIE exact DTT crystallization reducing shadow gate v1"
)

HUMAN_NOT_RELEVANT_FINAL = "HUMAN_NOT_RELEVANT_FINAL"
HUMAN_RELEVANT_FINAL = "HUMAN_RELEVANT_FINAL"
AUTO_NEGATIVE_EXACT_FINAL = "AUTO_NEGATIVE_EXACT_FINAL"
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
HUMAN_REVIEW_REQUIRED_DEFERRED = "HUMAN_REVIEW_REQUIRED_DEFERRED"
HUMAN_REVIEW_REQUIRED_GATE_INVALID = "HUMAN_REVIEW_REQUIRED_GATE_INVALID"

ROUTE_STATUSES = (
    HUMAN_NOT_RELEVANT_FINAL,
    HUMAN_RELEVANT_FINAL,
    AUTO_NEGATIVE_EXACT_FINAL,
    HUMAN_REVIEW_REQUIRED,
    HUMAN_REVIEW_REQUIRED_DEFERRED,
    HUMAN_REVIEW_REQUIRED_GATE_INVALID,
)
HUMAN_RELEVANT_DECISION = "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
HUMAN_NOT_RELEVANT_DECISION = (
    "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
)
HUMAN_DEFERRED_DECISION = "DEFERRED_INSUFFICIENT_EVIDENCE"

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1"
)
MANIFEST = "covapie_successor_task_domain_routing_manifest_v1.json"
EVENT_INVENTORY = "covapie_successor_task_domain_event_routing_inventory_v1.csv"
UNIT_INVENTORY = "covapie_successor_task_domain_unit_routing_inventory_v1.csv"
SUMMARY = "covapie_successor_task_domain_routing_summary_v1.json"
OUTPUT_FILENAMES = (MANIFEST, EVENT_INVENTORY, UNIT_INVENTORY, SUMMARY)

HUMAN_PROGRESS_RELATIVE = review.OUTPUT_ROOT_RELATIVE / review.PROGRESS
GATE_MANIFEST_RELATIVE = gate.OUTPUT_ROOT_RELATIVE / gate.RULE_MANIFEST
GATE_INVENTORY_RELATIVE = gate.OUTPUT_ROOT_RELATIVE / gate.SHADOW_INVENTORY
GATE_SUMMARY_RELATIVE = gate.OUTPUT_ROOT_RELATIVE / gate.SUMMARY
DTT_GATE_MANIFEST_RELATIVE = dtt_gate.OUTPUT_ROOT_RELATIVE / dtt_gate.RULE_MANIFEST
DTT_GATE_INVENTORY_RELATIVE = (
    dtt_gate.OUTPUT_ROOT_RELATIVE / dtt_gate.SHADOW_INVENTORY
)
DTT_GATE_SUMMARY_RELATIVE = dtt_gate.OUTPUT_ROOT_RELATIVE / dtt_gate.SUMMARY
CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_dataset_expansion_pipeline_v1/"
    "6di9_gjj_approved_v1/reusable_authority_registry_v1.json"
)
CURRENT_PRODUCTION_AUTHORITY_PUBLICATION_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_dataset_expansion_pipeline_v1/"
    "6di9_gjj_approved_v1/pipeline_run_v1.json"
)
CURRENT_PRODUCTION_AUTHORITY_MODE = (
    "CURRENT_SHA_BOUND_REUSABLE_EXACT_CHEMISTRY_AUTHORITY_REGISTRY_"
    "WITH_FAIL_CLOSED_CANDIDATE_EVALUATION_COVERAGE"
)

LEGACY_INPUT_SHA256 = {
    gate.EVENT_INVENTORY_RELATIVE: (
        "a1e48d9efaa9b0f5f1b1d7d5988d9f54c07c22d7249b5a7b43dee31fd6efaa75"
    ),
    gate.REVIEW_PACKET_RELATIVE: (
        "39f8afd7b8f62531f9f8704163cc7a444c3b008ff8d4610744d90b4918053194"
    ),
    gate.UPSTREAM_OUTCOMES_RELATIVE: (
        "0270dd93a31427042d02f7751ab7b46679308c7f1ee5207a5560b199a6a94d57"
    ),
}
GATE_ARTIFACT_BINDINGS = {
    GATE_MANIFEST_RELATIVE: {
        "byte_count": 20844,
        "sha256": (
            "100b64fff8bbef56f9885a64607d25cff293bd9d98f93f25af71455dcf6bca42"
        ),
    },
    GATE_INVENTORY_RELATIVE: {
        "byte_count": 176462,
        "sha256": (
            "aaa8b4a974339e50e594de1bc51ab59fb1f5c25b14977aa0207eb79c6585d57e"
        ),
    },
    GATE_SUMMARY_RELATIVE: {
        "byte_count": 4662,
        "sha256": (
            "a5dc0e93c2a1c425371caf15c96813d25849cde130c1eddd58992b5fcd9676a7"
        ),
    },
}
DTT_GATE_ARTIFACT_BINDINGS = {
    DTT_GATE_MANIFEST_RELATIVE: {
        "byte_count": 34012,
        "sha256": (
            "9b41905df37beb80f73b3b5e02615439fcbe1f707dd5c1548bb71d0fb4976e45"
        ),
    },
    DTT_GATE_INVENTORY_RELATIVE: {
        "byte_count": 228071,
        "sha256": (
            "b8ecc5dc3ab392b3907bdfdaf6cba07f9a2038f28a7af5348f3cf4017dfc67ab"
        ),
    },
    DTT_GATE_SUMMARY_RELATIVE: {
        "byte_count": 2625,
        "sha256": (
            "10e5f45ec09f16506f88f137b5a5904d09c70aa563c31e81f6c9c156c7c9aa71"
        ),
    },
}

EVENT_HEADER = (
    "canonical_event_id",
    "review_unit_id",
    "pdb_id",
    "ligand_component_id",
    "human_workflow_status",
    "human_training_domain_relevance_decision",
    "rule_id",
    "gate_event_status",
    "gate_event_reason",
    "unit_final_task_domain_route",
    "unit_final_route_reason",
    "human_precedence_applied",
    "effective_auto_negative",
    "downstream_positive_chemistry_review_required",
)
UNIT_HEADER = (
    "review_unit_id",
    "event_count",
    "human_workflow_status",
    "human_training_domain_relevance_decision",
    "selected_auto_negative_rule_id",
    "selected_rule_matched_event_count",
    "selected_rule_all_events_match",
    "total_gate_invalid_evaluation_count",
    "per_rule_evidence_json",
    "final_task_domain_route",
    "final_route_reason",
    "effective_new_auto_negative",
    "downstream_chemistry_review_required",
    "human_overlay_mutated",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EVENT_STATUSES = frozenset(
    (gate.MATCHED_AUTO_NEGATIVE_EXACT, gate.NOT_MATCHED, gate.INVALID_EVIDENCE)
)


@dataclass(frozen=True)
class TaskDomainAutoNegativeEventEvaluation:
    """One event's result from one registered exact auto-negative rule."""

    canonical_event_id: str
    rule_id: str
    status: str
    reason: str


@dataclass(frozen=True)
class ExactAutoNegativeRuleRegistration:
    """Small ordered registry entry for an independently callable rule."""

    rule_id: str
    evaluator: Callable[..., gate.AutoNegativeEvaluationResult]


@dataclass(frozen=True)
class ExactRuleUnitEvidence:
    """Ordered immutable audit counts for one rule over one complete unit."""

    rule_id: str
    matched_event_count: int
    not_matched_event_count: int
    invalid_event_count: int
    all_events_match: bool


@dataclass(frozen=True)
class SuccessorTaskDomainRoutingResult:
    """Immutable unit-level task-domain route with explicit audit evidence."""

    review_unit_id: str
    route_status: str
    route_reason: str
    human_relevance_decision: str
    human_workflow_status: str
    auto_negative_rule_id: str
    auto_negative_event_match_count: int
    total_gate_invalid_evaluation_count: int
    gate_unit_all_events_match: bool
    rule_evidence: tuple[ExactRuleUnitEvidence, ...]
    event_count: int
    effective_new_auto_negative: bool
    human_precedence_applied: bool
    downstream_chemistry_review_required: bool


EXACT_AUTO_NEGATIVE_RULE_REGISTRY_V1 = (
    ExactAutoNegativeRuleRegistration(
        rule_id=gate.RULE_ID,
        evaluator=gate.evaluate_neg_v1_ts_dump_catalytic_adduct_exact,
    ),
    ExactAutoNegativeRuleRegistration(
        rule_id=dtt_gate.RULE_ID,
        evaluator=(
            dtt_gate.evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact
        ),
    ),
)
INTEGRATED_AUTO_NEGATIVE_RULE_IDS = tuple(
    registration.rule_id for registration in EXACT_AUTO_NEGATIVE_RULE_REGISTRY_V1
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=list(header),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(header):
            raise ValueError("CSV_ROW_SCHEMA_OR_ORDER_INVALID")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if type(value) is not dict:
        raise ValueError("JSON_ROOT_NOT_OBJECT:" + path.name)
    return value


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def verify_repository_binding_v1(repo_root: Path) -> dict[str, object]:
    """Require a synchronized main descendant without persisting runtime SHA."""

    repo_root = repo_root.resolve()
    branch = _git(repo_root, "branch", "--show-current")
    head = _git(repo_root, "rev-parse", "HEAD")
    origin = _git(repo_root, "rev-parse", "origin/main")
    ahead_text, behind_text = _git(
        repo_root,
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...origin/main",
    ).split()
    if branch != "main":
        raise ValueError("REPOSITORY_BRANCH_MISMATCH")
    if head != origin:
        raise ValueError("REPOSITORY_HEAD_ORIGIN_MISMATCH")
    if (ahead_text, behind_text) != ("0", "0"):
        raise ValueError("REPOSITORY_AHEAD_BEHIND_MISMATCH")
    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            BASE_SUCCESSOR_COMMIT_ANCESTOR,
            head,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if ancestor.returncode != 0:
        raise ValueError("BASE_SUCCESSOR_COMMIT_NOT_ANCESTOR")
    subject = _git(
        repo_root,
        "show",
        "-s",
        "--format=%s",
        BASE_SUCCESSOR_COMMIT_ANCESTOR,
    )
    if subject != BASE_SUCCESSOR_COMMIT_SUBJECT:
        raise ValueError("BASE_SUCCESSOR_COMMIT_SUBJECT_MISMATCH")
    for descendant, label in ((head, "HEAD"), (origin, "ORIGIN_MAIN")):
        dtt_ancestor = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                DTT_GATE_PUBLICATION_COMMIT,
                descendant,
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
        if dtt_ancestor.returncode != 0:
            raise ValueError("DTT_GATE_PUBLICATION_NOT_ANCESTOR_OF_" + label)
    dtt_subject = _git(
        repo_root,
        "show",
        "-s",
        "--format=%s",
        DTT_GATE_PUBLICATION_COMMIT,
    )
    if dtt_subject != DTT_GATE_PUBLICATION_SUBJECT:
        raise ValueError("DTT_GATE_PUBLICATION_SUBJECT_MISMATCH")
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "base_successor_commit_is_ancestor": True,
        "dtt_gate_publication_is_ancestor_of_head": True,
        "dtt_gate_publication_is_ancestor_of_origin_main": True,
    }


def _file_binding(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"byte_count": len(payload), "sha256": _sha(payload)}


def _load_current_production_authority_registry_v1(
    repo_root: Path,
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    """Load the repository's current cumulative production exact authority."""

    from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk
    from covalent_ext import covapie_cys_sg_dataset_expansion_pipeline_v1 as pipeline

    if bulk.AUTHORITY_REGISTRY_RELATIVE != (
        CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE
    ):
        raise ValueError("CURRENT_PRODUCTION_AUTHORITY_OWNER_PATH_MISMATCH")
    registry_path = repo_root / CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE
    registry_payload = registry_path.read_bytes()
    registry_sha = _sha(registry_payload)
    if registry_sha != bulk.AUTHORITY_REGISTRY_SHA256:
        raise ValueError("CURRENT_PRODUCTION_AUTHORITY_OWNER_SHA256_MISMATCH")
    authorities = pipeline.load_reusable_authority_registry_v1(registry_path)
    if len(authorities) != 3 or any(
        authority.approved is not True
        or authority.approval_scope != "EXACT_CHEMISTRY_SIGNATURE_REUSABLE"
        for authority in authorities
    ):
        raise ValueError("CURRENT_PRODUCTION_AUTHORITY_REGISTRY_STATE_INVALID")

    publication_path = (
        repo_root / CURRENT_PRODUCTION_AUTHORITY_PUBLICATION_RELATIVE
    )
    publication = _read_json_object(publication_path)
    if (
        publication.get("pipeline_version") != pipeline.PIPELINE_VERSION
        or publication.get("execution_mode") != pipeline.MATERIALIZE_APPROVED
        or publication.get("successor_policy_id") != pipeline.SUCCESSOR_POLICY_ID
        or publication.get("reusable_authority_registry_sha256") != registry_sha
        or publication.get("dry_run") is not False
    ):
        raise ValueError("CURRENT_PRODUCTION_AUTHORITY_PUBLICATION_INVALID")
    binding = {
        "path": CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE.as_posix(),
        "schema": pipeline.REUSABLE_AUTHORITY_REGISTRY_SCHEMA_V1,
        "sha256": registry_sha,
        "byte_count": len(registry_payload),
        "authority_role": (
            "CURRENT_CUMULATIVE_HUMAN_APPROVED_REUSABLE_EXACT_CHEMISTRY_"
            "SIGNATURE_PRODUCTION_AUTHORITY"
        ),
        "authority_count": len(authorities),
        "successor_policy_id": pipeline.SUCCESSOR_POLICY_ID,
        "publication_evidence": {
            "path": CURRENT_PRODUCTION_AUTHORITY_PUBLICATION_RELATIVE.as_posix(),
            "schema": pipeline.PIPELINE_VERSION,
            **_file_binding(publication_path),
            "execution_mode": pipeline.MATERIALIZE_APPROVED,
        },
        "production_positive_authority_mode": CURRENT_PRODUCTION_AUTHORITY_MODE,
        "future_production_authority_change_requires_successor_rebuild": True,
    }
    return binding, authorities


def verify_predecessor_bindings_v1(repo_root: Path) -> dict[str, Any]:
    """Bind all frozen inputs and validate the live human snapshot."""

    repo_root = repo_root.resolve()
    legacy: dict[str, dict[str, object]] = {}
    for relative, expected_sha in LEGACY_INPUT_SHA256.items():
        observed = _file_binding(repo_root / relative)
        if observed["sha256"] != expected_sha:
            raise ValueError("LEGACY_INPUT_SHA256_MISMATCH:" + relative.as_posix())
        legacy[relative.as_posix()] = observed

    published_gate: dict[str, dict[str, object]] = {}
    for relative, expected in GATE_ARTIFACT_BINDINGS.items():
        observed = _file_binding(repo_root / relative)
        if observed != expected:
            raise ValueError("GATE_ARTIFACT_BINDING_MISMATCH:" + relative.as_posix())
        published_gate[relative.as_posix()] = observed

    published_dtt_gate: dict[str, dict[str, object]] = {}
    for relative, expected in DTT_GATE_ARTIFACT_BINDINGS.items():
        observed = _file_binding(repo_root / relative)
        if observed != expected:
            raise ValueError(
                "DTT_GATE_ARTIFACT_BINDING_MISMATCH:" + relative.as_posix()
            )
        published_dtt_gate[relative.as_posix()] = observed

    gate_manifest = _read_json_object(repo_root / GATE_MANIFEST_RELATIVE)
    gate_summary = _read_json_object(repo_root / GATE_SUMMARY_RELATIVE)
    required_gate_summary = {
        "artifact_semantics": "IMMUTABLE_CALIBRATION_SNAPSHOT_SHADOW_EVALUATION",
        "generalization_without_sibling_label_leakage": True,
        "target_family_generalization_authorized": True,
        "live_integration_ready": True,
        "observed_shadow_matched_event_count": 47,
        "observed_shadow_matched_unit_count": 2,
        "integration_into_live_triage_performed": False,
    }
    for field, expected in required_gate_summary.items():
        if gate_summary.get(field) != expected:
            raise ValueError("PUBLISHED_GATE_SUMMARY_STATE_MISMATCH:" + field)
    if (
        gate_manifest.get("rule_id") != gate.RULE_ID
        or gate_manifest.get("live_integration_ready") is not True
        or gate_manifest.get("target_family_generalization_authorized") is not True
        or not isinstance(gate_manifest.get("scientific_rule_context"), Mapping)
    ):
        raise ValueError("PUBLISHED_GATE_MANIFEST_STATE_INVALID")

    dtt_gate_manifest = _read_json_object(repo_root / DTT_GATE_MANIFEST_RELATIVE)
    dtt_gate_summary = _read_json_object(repo_root / DTT_GATE_SUMMARY_RELATIVE)
    required_dtt_gate_summary = {
        "rule_id": dtt_gate.RULE_ID,
        "artifact_semantics": (
            "IMMUTABLE_CALIBRATION_SNAPSHOT_SHADOW_EVALUATION"
        ),
        "readiness_mode": (
            "SAME_STRUCTURE_DTT_ENDPOINT_GENERALIZATION_PROVEN_WITHOUT_"
            "SHADOW_LABEL_LEAKAGE"
        ),
        "observed_shadow_matched_event_count": 2,
        "observed_shadow_matched_unit_count": 2,
        "human_calibration_matched_event_count": 1,
        "calibration_snapshot_unreviewed_shadow_auto_negative_event_count": 1,
        "calibration_snapshot_unreviewed_shadow_auto_negative_unit_count": 1,
        "DTT_endpoint_automorphism_proven": True,
        "generalization_without_sibling_label_leakage": True,
        "DTU_counterexample_match_count": 0,
        "cross_CCD_DTU_generalization_authorized": False,
        "cross_pdb_DTT_generalization_authorized": False,
        "invalid_evidence_count": 0,
        "live_integration_ready": True,
        "integration_into_live_successor_routing_performed": False,
    }
    for field, expected in required_dtt_gate_summary.items():
        if dtt_gate_summary.get(field) != expected:
            raise ValueError("PUBLISHED_DTT_GATE_SUMMARY_STATE_MISMATCH:" + field)
    if (
        dtt_gate_manifest.get("rule_id") != dtt_gate.RULE_ID
        or dtt_gate_manifest.get("artifact_semantics")
        != "IMMUTABLE_CALIBRATION_SNAPSHOT_SHADOW_EVALUATION"
        or dtt_gate_manifest.get("live_integration_ready") is not True
        or dtt_gate_manifest.get("cross_CCD_DTU_generalization_authorized")
        is not False
        or dtt_gate_manifest.get(
            "integration_into_live_successor_routing_performed"
        )
        is not False
        or not isinstance(
            dtt_gate_manifest.get("scientific_rule_context"), Mapping
        )
    ):
        raise ValueError("PUBLISHED_DTT_GATE_MANIFEST_STATE_INVALID")

    human_path = repo_root / gate.HUMAN_DECISIONS_RELATIVE
    progress_path = repo_root / HUMAN_PROGRESS_RELATIVE
    human_payload = human_path.read_bytes()
    human = json.loads(human_payload)
    if type(human) is not dict:
        raise ValueError("CURRENT_HUMAN_OVERLAY_ROOT_INVALID")
    derived_progress = review.validate_overlay_v1(repo_root, human)
    persisted_progress = _read_json_object(progress_path)
    if derived_progress != persisted_progress:
        raise ValueError("CURRENT_HUMAN_PROGRESS_NOT_DERIVED_FROM_OVERLAY")
    gate.validate_current_human_overlay_v1(human)
    if HUMAN_DEFERRED_DECISION not in review.RELEVANCE_DECISIONS:
        raise ValueError("OFFICIAL_HUMAN_DEFERRED_VOCABULARY_MISSING")
    human_snapshot = {
        "decisions": {
            "path": gate.HUMAN_DECISIONS_RELATIVE.as_posix(),
            **_file_binding(human_path),
        },
        "progress": {
            "path": HUMAN_PROGRESS_RELATIVE.as_posix(),
            **_file_binding(progress_path),
        },
    }
    production_binding, production_authorities = (
        _load_current_production_authority_registry_v1(repo_root)
    )
    return {
        "legacy": legacy,
        "published_gate": published_gate,
        "published_dtt_gate": published_dtt_gate,
        "gate_manifest": gate_manifest,
        "gate_summary": gate_summary,
        "dtt_gate_manifest": dtt_gate_manifest,
        "dtt_gate_summary": dtt_gate_summary,
        "current_human": human,
        "current_human_payload": human_payload,
        "current_human_progress": persisted_progress,
        "current_human_snapshot": human_snapshot,
        "current_production_authority_binding": production_binding,
        "current_production_authorities": production_authorities,
    }


def dispatch_exact_auto_negative_rules_v1(
    *,
    event: Mapping[str, Any],
    outcome: Mapping[str, Any],
    rule_context_by_id: Mapping[str, Mapping[str, Any]],
    override_context_by_id: Mapping[str, gate.RuntimePositiveOverrideContext],
    registry: Sequence[ExactAutoNegativeRuleRegistration] = (
        EXACT_AUTO_NEGATIVE_RULE_REGISTRY_V1
    ),
) -> tuple[TaskDomainAutoNegativeEventEvaluation, ...]:
    """Evaluate the ordered exact registry; base exceptions remain visible."""

    if not isinstance(registry, Sequence) or isinstance(registry, (str, bytes)):
        raise ValueError("EXACT_RULE_REGISTRY_NOT_SEQUENCE")
    registrations = tuple(registry)
    rule_ids = tuple(item.rule_id for item in registrations)
    if (
        not registrations
        or any(type(item) is not ExactAutoNegativeRuleRegistration for item in registrations)
        or any(not rule_id for rule_id in rule_ids)
        or len(set(rule_ids)) != len(rule_ids)
    ):
        raise ValueError("EXACT_RULE_REGISTRY_INVALID")
    event_id = event.get("canonical_event_id")
    if not isinstance(event_id, str) or not event_id:
        raise ValueError("DISPATCH_EVENT_ID_INVALID")
    results: list[TaskDomainAutoNegativeEventEvaluation] = []
    for registration in registrations:
        context = rule_context_by_id.get(registration.rule_id)
        override = override_context_by_id.get(registration.rule_id)
        raw = registration.evaluator(
            event=event,
            outcome=outcome,
            rule_context=context,
            override_context=override,
        )
        if (
            type(raw) is not gate.AutoNegativeEvaluationResult
            or raw.rule_id != registration.rule_id
        ):
            raise ValueError("EXACT_RULE_EVALUATOR_RESULT_TYPE_INVALID")
        results.append(
            TaskDomainAutoNegativeEventEvaluation(
                canonical_event_id=event_id,
                rule_id=raw.rule_id,
                status=raw.status,
                reason=raw.reason,
            )
        )
    return tuple(results)


def _relevant_downstream_complete(human_unit_state: Mapping[str, Any]) -> bool:
    if human_unit_state.get("workflow_status") != "COMPLETED":
        return False
    reactive = human_unit_state.get("reactive_atom_confirmation")
    family = human_unit_state.get("warhead_family_decision")
    warhead_atoms = human_unit_state.get("warhead_atom_ids")
    roles = human_unit_state.get("roles")
    events = human_unit_state.get("events")
    return bool(
        isinstance(reactive, Mapping)
        and reactive.get("status") == "CONFIRMED"
        and isinstance(family, Mapping)
        and isinstance(warhead_atoms, list)
        and warhead_atoms
        and isinstance(roles, Mapping)
        and isinstance(events, list)
        and events
        and all(
            isinstance(event, Mapping)
            and event.get("post_geometry_training_usable") in review.GEOMETRY_USABILITY
            and event.get("event_training_use_decision") in review.EVENT_USE_DECISIONS
            for event in events
        )
    )


def _invalid_route(
    *,
    unit_id: str,
    workflow: str,
    decision: str,
    event_count: int,
    reason: str,
) -> SuccessorTaskDomainRoutingResult:
    return SuccessorTaskDomainRoutingResult(
        review_unit_id=unit_id,
        route_status=HUMAN_REVIEW_REQUIRED_GATE_INVALID,
        route_reason=reason,
        human_relevance_decision=decision,
        human_workflow_status=workflow,
        auto_negative_rule_id="",
        auto_negative_event_match_count=0,
        total_gate_invalid_evaluation_count=event_count,
        gate_unit_all_events_match=False,
        rule_evidence=(),
        event_count=event_count,
        effective_new_auto_negative=False,
        human_precedence_applied=False,
        downstream_chemistry_review_required=False,
    )


def route_successor_task_domain_review_unit_v1(
    *,
    review_unit: Mapping[str, Any],
    event_evaluations: Sequence[TaskDomainAutoNegativeEventEvaluation],
    human_unit_state: Mapping[str, Any],
    registered_rule_ids: Sequence[str] = INTEGRATED_AUTO_NEGATIVE_RULE_IDS,
) -> SuccessorTaskDomainRoutingResult:
    """Route one in-memory unit with human precedence and fail-closed gates."""

    if not isinstance(review_unit, Mapping) or not isinstance(
        human_unit_state, Mapping
    ):
        raise ValueError("ROUTING_UNIT_INPUT_NOT_MAPPING")
    unit_id = review_unit.get("review_unit_id")
    human_unit_id = human_unit_state.get("review_unit_id")
    raw_event_ids = review_unit.get("canonical_event_ids")
    if not isinstance(unit_id, str) or not unit_id or human_unit_id != unit_id:
        raise ValueError("ROUTING_REVIEW_UNIT_ID_INVALID")
    if (
        not isinstance(raw_event_ids, list)
        or not raw_event_ids
        or any(not isinstance(item, str) or not item for item in raw_event_ids)
        or len(set(raw_event_ids)) != len(raw_event_ids)
    ):
        raise ValueError("ROUTING_REVIEW_UNIT_EVENTS_INVALID")
    event_ids = tuple(raw_event_ids)
    event_count = len(event_ids)
    if review_unit.get("event_count") != event_count:
        raise ValueError("ROUTING_REVIEW_UNIT_EVENT_COUNT_MISMATCH")
    workflow = human_unit_state.get("workflow_status")
    decision = human_unit_state.get("training_domain_relevance_decision")
    if workflow not in review.WORKFLOW_STATUSES or decision not in {
        "",
        HUMAN_RELEVANT_DECISION,
        HUMAN_NOT_RELEVANT_DECISION,
        HUMAN_DEFERRED_DECISION,
    }:
        return _invalid_route(
            unit_id=unit_id,
            workflow=str(workflow or ""),
            decision=str(decision or ""),
            event_count=event_count,
            reason="CURRENT_HUMAN_STATE_INVALID_FAIL_CLOSED",
        )

    rules = tuple(registered_rule_ids)
    if (
        not rules
        or any(not isinstance(rule_id, str) or not rule_id for rule_id in rules)
        or len(set(rules)) != len(rules)
    ):
        return _invalid_route(
            unit_id=unit_id,
            workflow=workflow,
            decision=decision,
            event_count=event_count,
            reason="EXACT_RULE_REGISTRY_INVALID_FAIL_CLOSED",
        )
    evaluations = tuple(event_evaluations)
    evaluation_by_key: dict[
        tuple[str, str], TaskDomainAutoNegativeEventEvaluation
    ] = {}
    evidence_error = ""
    for evaluation in evaluations:
        if type(evaluation) is not TaskDomainAutoNegativeEventEvaluation:
            evidence_error = "GATE_EVENT_EVALUATION_TYPE_INVALID"
            break
        key = (evaluation.rule_id, evaluation.canonical_event_id)
        if (
            evaluation.rule_id not in rules
            or evaluation.canonical_event_id not in event_ids
            or key in evaluation_by_key
            or evaluation.status not in _EVENT_STATUSES
            or not isinstance(evaluation.reason, str)
            or not evaluation.reason
        ):
            evidence_error = "GATE_EVENT_EVALUATION_SCHEMA_OR_COVERAGE_INVALID"
            break
        evaluation_by_key[key] = evaluation
    expected_keys = {(rule_id, event_id) for rule_id in rules for event_id in event_ids}
    if not evidence_error and set(evaluation_by_key) != expected_keys:
        evidence_error = "GATE_EVENT_EVALUATION_COVERAGE_INVALID"

    rule_evidence: tuple[ExactRuleUnitEvidence, ...] = ()
    if not evidence_error:
        evidence_items: list[ExactRuleUnitEvidence] = []
        for rule_id in rules:
            counts = Counter(
                evaluation_by_key[(rule_id, event_id)].status
                for event_id in event_ids
            )
            evidence_items.append(
                ExactRuleUnitEvidence(
                    rule_id=rule_id,
                    matched_event_count=counts[
                        gate.MATCHED_AUTO_NEGATIVE_EXACT
                    ],
                    not_matched_event_count=counts[gate.NOT_MATCHED],
                    invalid_event_count=counts[gate.INVALID_EVIDENCE],
                    all_events_match=(
                        counts[gate.MATCHED_AUTO_NEGATIVE_EXACT] == event_count
                    ),
                )
            )
        rule_evidence = tuple(evidence_items)
    total_invalid = sum(item.invalid_event_count for item in rule_evidence)

    def result(
        status: str,
        reason: str,
        *,
        auto_rule: str = "",
        effective_auto: bool = False,
        human_precedence: bool = False,
        downstream: bool = False,
    ) -> SuccessorTaskDomainRoutingResult:
        selected = next(
            (item for item in rule_evidence if item.rule_id == auto_rule), None
        )
        return SuccessorTaskDomainRoutingResult(
            review_unit_id=unit_id,
            route_status=status,
            route_reason=reason,
            human_relevance_decision=decision,
            human_workflow_status=workflow,
            auto_negative_rule_id=auto_rule,
            auto_negative_event_match_count=(
                selected.matched_event_count if selected is not None else 0
            ),
            total_gate_invalid_evaluation_count=total_invalid,
            gate_unit_all_events_match=(
                selected.all_events_match if selected is not None else False
            ),
            rule_evidence=rule_evidence,
            event_count=event_count,
            effective_new_auto_negative=effective_auto,
            human_precedence_applied=human_precedence,
            downstream_chemistry_review_required=downstream,
        )

    if decision == HUMAN_RELEVANT_DECISION:
        return result(
            HUMAN_RELEVANT_FINAL,
            "CURRENT_HUMAN_RELEVANT_DECISION_HAS_FIRST_PRECEDENCE",
            human_precedence=True,
            downstream=not _relevant_downstream_complete(human_unit_state),
        )
    if decision == HUMAN_NOT_RELEVANT_DECISION:
        return result(
            HUMAN_NOT_RELEVANT_FINAL,
            "CURRENT_HUMAN_NOT_RELEVANT_DECISION_HAS_SECOND_PRECEDENCE",
            human_precedence=True,
        )
    if decision == HUMAN_DEFERRED_DECISION or workflow == "DEFERRED":
        return result(
            HUMAN_REVIEW_REQUIRED_DEFERRED,
            "CURRENT_HUMAN_DEFERRED_STATE_REQUIRES_HUMAN_REVIEW",
            human_precedence=True,
        )
    if evidence_error:
        return result(
            HUMAN_REVIEW_REQUIRED_GATE_INVALID,
            "GATE_INVALID_FAIL_CLOSED:" + evidence_error,
        )
    if total_invalid:
        return result(
            HUMAN_REVIEW_REQUIRED_GATE_INVALID,
            "GATE_INVALID_FAIL_CLOSED:INVALID_EVALUATION_IN_REGISTERED_RULE",
        )
    fully_matched_rules = [
        item.rule_id for item in rule_evidence if item.all_events_match
    ]
    if len(fully_matched_rules) > 1:
        return result(
            HUMAN_REVIEW_REQUIRED_GATE_INVALID,
            "MULTIPLE_EXACT_RULES_FULL_MATCH_FAIL_CLOSED:"
            + ",".join(fully_matched_rules),
        )
    if len(fully_matched_rules) == 1:
        matched_rule = fully_matched_rules[0]
        return result(
            AUTO_NEGATIVE_EXACT_FINAL,
            "EVERY_EVENT_IN_UNIT_MATCHED_SAME_EXACT_RULE_WITHOUT_OVERRIDE",
            auto_rule=matched_rule,
            effective_auto=True,
        )
    return result(
        HUMAN_REVIEW_REQUIRED,
        "NO_SINGLE_EXACT_RULE_MATCHED_EVERY_EVENT;HUMAN_REVIEW_RETAINED",
    )


def _load_routing_inputs_v1(
    repo_root: Path, bindings: Mapping[str, Any]
) -> dict[str, Any]:
    with (repo_root / gate.EVENT_INVENTORY_RELATIVE).open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        candidate_rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("post_only_partition") == "POST_ONLY_V1_REVIEW_CANDIDATE"
        ]
    if len(candidate_rows) != 123:
        raise ValueError("LEGACY_CANDIDATE_EVENT_COUNT_MISMATCH")
    event_by_id = {
        row.get("canonical_event_id", ""): row for row in candidate_rows
    }
    if len(event_by_id) != 123 or "" in event_by_id:
        raise ValueError("LEGACY_CANDIDATE_EVENT_IDS_INVALID")

    packet = _read_json_object(repo_root / gate.REVIEW_PACKET_RELATIVE)
    units = packet.get("review_units")
    if not isinstance(units, list) or len(units) != 36:
        raise ValueError("LEGACY_REVIEW_UNIT_COUNT_MISMATCH")
    unit_by_id: dict[str, Mapping[str, Any]] = {}
    unit_by_event: dict[str, str] = {}
    for unit in units:
        if not isinstance(unit, Mapping):
            raise ValueError("LEGACY_REVIEW_UNIT_INVALID")
        unit_id = unit.get("review_unit_id")
        event_ids = unit.get("canonical_event_ids")
        if (
            not isinstance(unit_id, str)
            or not unit_id
            or unit_id in unit_by_id
            or not isinstance(event_ids, list)
            or not event_ids
            or unit.get("event_count") != len(event_ids)
        ):
            raise ValueError("LEGACY_REVIEW_UNIT_SCHEMA_INVALID")
        unit_by_id[unit_id] = unit
        for event_id in event_ids:
            if not isinstance(event_id, str) or event_id in unit_by_event:
                raise ValueError("LEGACY_REVIEW_EVENT_MEMBERSHIP_INVALID")
            unit_by_event[event_id] = unit_id
    if set(unit_by_event) != set(event_by_id):
        raise ValueError("LEGACY_REVIEW_EVENT_COVERAGE_MISMATCH")

    outcomes = _read_json_object(repo_root / gate.UPSTREAM_OUTCOMES_RELATIVE).get(
        "events"
    )
    if not isinstance(outcomes, list):
        raise ValueError("UPSTREAM_OUTCOMES_INVALID")
    outcome_by_id = {
        item.get("canonical_event_id", ""): item
        for item in outcomes
        if isinstance(item, Mapping)
    }
    if not set(event_by_id) <= set(outcome_by_id):
        raise ValueError("UPSTREAM_OUTCOME_COVERAGE_MISMATCH")

    current_human = bindings["current_human"]
    human_units = gate.validate_current_human_overlay_v1(current_human)
    if set(human_units) != set(unit_by_id):
        raise ValueError("CURRENT_HUMAN_UNIT_COVERAGE_MISMATCH")
    return {
        "event_by_id": event_by_id,
        "unit_by_id": unit_by_id,
        "unit_by_event": unit_by_event,
        "outcome_by_id": outcome_by_id,
        "human_unit_by_id": human_units,
    }


def build_current_production_positive_context_v1(
    *,
    bindings: Mapping[str, Any],
    event_by_id: Mapping[str, Mapping[str, Any]],
    outcome_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Derive candidate-positive IDs against the bound current registry."""

    authorities = tuple(bindings["current_production_authorities"])
    expected = tuple(
        (
            authority.authority_id,
            authority.authority_version,
            authority.chemistry_signature_sha256,
        )
        for authority in authorities
    )
    if not expected:
        raise ValueError("CURRENT_PRODUCTION_AUTHORITY_REGISTRY_EMPTY")
    positive_event_ids: list[str] = []
    normalized_outcomes: dict[str, dict[str, Any]] = {}
    for event_id in sorted(event_by_id):
        outcome = outcome_by_id.get(event_id)
        if not isinstance(outcome, Mapping):
            raise ValueError("CURRENT_PRODUCTION_EVENT_OUTCOME_MISSING:" + event_id)
        evaluations = outcome.get("authority_match_evaluation")
        if not isinstance(evaluations, list):
            raise ValueError(
                "CURRENT_PRODUCTION_AUTHORITY_EVALUATION_INVALID:" + event_id
            )
        observed: list[tuple[str, str, str]] = []
        matched_authorities: list[str] = []
        for evaluation in evaluations:
            if not isinstance(evaluation, Mapping):
                raise ValueError(
                    "CURRENT_PRODUCTION_AUTHORITY_EVALUATION_INVALID:" + event_id
                )
            key = (
                evaluation.get("authority_id"),
                evaluation.get("authority_version"),
                evaluation.get("authority_chemistry_signature_sha256"),
            )
            if any(not isinstance(value, str) or not value for value in key):
                raise ValueError(
                    "CURRENT_PRODUCTION_AUTHORITY_EVALUATION_INVALID:" + event_id
                )
            observed.append(key)  # type: ignore[arg-type]
            if evaluation.get("candidate_match_result") == "EXACT_SIGNATURE_MATCH":
                if evaluation.get("candidate_chemistry_signature_sha256") != key[2]:
                    raise ValueError(
                        "CURRENT_PRODUCTION_EXACT_MATCH_SIGNATURE_INVALID:"
                        + event_id
                    )
                matched_authorities.append(key[0])
        if tuple(observed) != expected:
            raise ValueError(
                "CURRENT_PRODUCTION_AUTHORITY_EVALUATION_COVERAGE_STALE:"
                + event_id
            )
        if len(matched_authorities) > 1:
            raise ValueError(
                "CURRENT_PRODUCTION_MULTIPLE_EXACT_AUTHORITY_MATCHES:" + event_id
            )
        derived_match = bool(matched_authorities)
        if outcome.get("existing_exact_authority_match") is not derived_match:
            raise ValueError(
                "CURRENT_PRODUCTION_EXACT_AUTHORITY_BOOLEAN_MISMATCH:" + event_id
            )
        if derived_match:
            positive_event_ids.append(event_id)
        normalized = dict(outcome)
        normalized["existing_exact_authority_match"] = derived_match
        normalized_outcomes[event_id] = normalized
    return {
        "positive_event_ids": tuple(positive_event_ids),
        "outcome_by_id": normalized_outcomes,
        "audit": {
            "candidate_event_count": len(event_by_id),
            "authority_count": len(expected),
            "rule_event_authority_evaluation_count": len(event_by_id)
            * len(expected),
            "current_production_exact_positive_authority_event_count": len(
                positive_event_ids
            ),
            "current_production_exact_positive_authority_event_ids": list(
                positive_event_ids
            ),
            "candidate_evaluation_source": {
                "path": gate.UPSTREAM_OUTCOMES_RELATIVE.as_posix(),
                "sha256": LEGACY_INPUT_SHA256[gate.UPSTREAM_OUTCOMES_RELATIVE],
                "role": (
                    "SHA_BOUND_CANDIDATE_EVENT_EVALUATION_WITH_COMPLETE_"
                    "CURRENT_REGISTRY_AUTHORITY_COVERAGE"
                ),
            },
            "registry_coverage_complete": True,
            "current_production_positive_integration_safe": True,
        },
    }


def _rule_evidence_json(result: SuccessorTaskDomainRoutingResult) -> str:
    return json.dumps(
        [
            {
                "rule_id": item.rule_id,
                "matched_event_count": item.matched_event_count,
                "not_matched_event_count": item.not_matched_event_count,
                "invalid_event_count": item.invalid_event_count,
                "all_events_match": item.all_events_match,
            }
            for item in result.rule_evidence
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _build_manifest_v1(
    *,
    bindings: Mapping[str, Any],
    production_audit: Mapping[str, Any],
    integrated_rule_ids: Sequence[str],
    event_payload: bytes,
    unit_payload: bytes,
) -> dict[str, Any]:
    production_binding = {
        **bindings["current_production_authority_binding"],
        **production_audit,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "snapshot_semantics": SNAPSHOT_SEMANTICS,
        "base_successor_commit_ancestor": BASE_SUCCESSOR_COMMIT_ANCESTOR,
        "dtt_gate_publication": {
            "commit": DTT_GATE_PUBLICATION_COMMIT,
            "subject": DTT_GATE_PUBLICATION_SUBJECT,
            "required_as_ancestor_of_synchronized_head_and_origin_main": True,
        },
        "legacy_candidate_input_bindings": bindings["legacy"],
        "current_human_snapshot_binding": bindings["current_human_snapshot"],
        "current_production_exact_positive_authority_binding": (
            production_binding
        ),
        "published_ts_dump_gate_artifact_bindings": bindings["published_gate"],
        "published_dtt_gate_artifact_bindings": bindings[
            "published_dtt_gate"
        ],
        "integrated_scientific_rule_context_sources": {
            gate.RULE_ID: {
                "source": "PUBLISHED_SHA_BOUND_TS_DUMP_GATE_MANIFEST",
                "path": GATE_MANIFEST_RELATIVE.as_posix(),
                "sha256": GATE_ARTIFACT_BINDINGS[GATE_MANIFEST_RELATIVE][
                    "sha256"
                ],
            },
            dtt_gate.RULE_ID: {
                "source": "PUBLISHED_SHA_BOUND_DTT_GATE_MANIFEST",
                "path": DTT_GATE_MANIFEST_RELATIVE.as_posix(),
                "sha256": DTT_GATE_ARTIFACT_BINDINGS[
                    DTT_GATE_MANIFEST_RELATIVE
                ]["sha256"],
                "external_cache_reconstruction_used": False,
            },
        },
        "integrated_auto_negative_rule_ids": list(integrated_rule_ids),
        "integrated_rule_registry_order_is_semantic": True,
        "routing_precedence": [
            "CURRENT_HUMAN_RELEVANT",
            "CURRENT_HUMAN_NOT_RELEVANT",
            "CURRENT_HUMAN_DEFERRED",
            "UNDECIDED_SINGLE_EXACT_RULE_ALL_EVENTS_MATCH",
            "UNDECIDED_HUMAN_REVIEW_FAIL_CLOSED",
        ],
        "human_vocabulary": {
            "workflow_statuses": list(review.WORKFLOW_STATUSES),
            "training_domain_relevance_decisions": list(
                review.RELEVANCE_DECISIONS
            ),
            "blank_decision_means": "UNDECIDED",
        },
        "public_route_statuses": list(ROUTE_STATUSES),
        "gate_invalid_fail_closed_policy": (
            "INVALID_MALFORMED_MISSING_PARTIAL_OR_CONTRADICTORY_EXACT_GATE_"
            "EVIDENCE_NEVER_AUTO_NEGATIVES; INVALID_EVIDENCE_USES_"
            "HUMAN_REVIEW_REQUIRED_GATE_INVALID"
        ),
        "unit_aggregation_policy": (
            "EVERY_EVENT_MUST_INDEPENDENTLY_MATCH_THE_SAME_SINGLE_EXACT_RULE;"
            "ONE_FULL_RULE_PLUS_NONMATCHING_RULES_MAY_AUTO_NEGATIVE;ANY_INVALID_"
            "REGISTERED_RULE_OR_MULTIPLE_FULL_RULES_FAILS_CLOSED"
        ),
        "routing_result_convenience_field_semantics": {
            "auto_negative_rule_id": "UNIQUE_SELECTED_FULL_MATCH_RULE_OR_BLANK",
            "auto_negative_event_match_count": (
                "SELECTED_EFFECTIVE_RULE_MATCHED_EVENT_COUNT_OR_ZERO"
            ),
            "gate_unit_all_events_match": (
                "SELECTED_EFFECTIVE_RULE_ALL_EVENTS_MATCH_OR_FALSE"
            ),
            "total_gate_invalid_evaluation_count": (
                "SUM_ACROSS_ALL_REGISTERED_RULE_EVENT_EVALUATIONS"
            ),
            "rule_evidence": "ORDERED_EXACT_REGISTRY_PER_RULE_UNIT_AUDIT",
        },
        "routing_scope": (
            "UNIT_LEVEL_HUMAN_TASK_DOMAIN_RELEVANCE_REVIEW_REQUIREMENT_ONLY"
        ),
        "legacy_raw_gate_metric_semantics": (
            "raw_gate_matched_events/raw_gate_matched_units/"
            "raw_gate_invalid_events retain TS_DUMP_RULE_ONLY semantics"
        ),
        "dtt_live_integration_semantics": {
            "shadow_artifact_remains_immutable": True,
            "live_integration_occurs_only_in_successor_routing": True,
            "cross_pdb_dtt_propagation_authorized": False,
            "cross_ccd_dtu_generalization_authorized": False,
            "chemistry_family_or_training_authority_created": False,
        },
        "not_authority_for": [
            "warhead_family",
            "warhead_atoms",
            "reactive_atom",
            "scaffold_linker_warhead_roles",
            "event_geometry_inclusion",
            "training_admission",
            "production_chemistry",
            "cross_pdb_dtt_propagation",
            "cross_ccd_dtu_generalization",
        ],
        "output_sha256_excluding_manifest_and_summary": {
            EVENT_INVENTORY: _sha(event_payload),
            UNIT_INVENTORY: _sha(unit_payload),
        },
        "current_human_overlay_mutated": False,
        "legacy_triage_modified": False,
        "gate_artifacts_modified": False,
        "ts_dump_shadow_artifacts_modified": False,
        "dtt_shadow_artifacts_modified": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
        "future_production_authority_change_requires_successor_rebuild": True,
        "current_production_positive_integration_safe": True,
        "live_routing_ready": True,
    }


def build_artifacts_v1(
    *,
    repo_root: Path,
    registry: Sequence[ExactAutoNegativeRuleRegistration] | None = None,
    rule_context_by_id: Mapping[str, Mapping[str, Any]] | None = None,
    override_context_by_id: Mapping[str, Any] | None = None,
) -> dict[str, bytes]:
    """Build the four deterministic current-human-bound artifacts in memory."""

    repo_root = repo_root.resolve()
    verify_repository_binding_v1(repo_root)
    bindings_before = verify_predecessor_bindings_v1(repo_root)
    inputs = _load_routing_inputs_v1(repo_root, bindings_before)
    registrations = tuple(
        EXACT_AUTO_NEGATIVE_RULE_REGISTRY_V1 if registry is None else registry
    )
    if (
        not registrations
        or any(
            type(item) is not ExactAutoNegativeRuleRegistration
            for item in registrations
        )
    ):
        raise ValueError("EXACT_RULE_REGISTRY_INVALID")
    rule_ids = tuple(item.rule_id for item in registrations)
    if any(not rule_id for rule_id in rule_ids) or len(set(rule_ids)) != len(
        rule_ids
    ):
        raise ValueError("EXACT_RULE_REGISTRY_INVALID")

    production_context = build_current_production_positive_context_v1(
        bindings=bindings_before,
        event_by_id=inputs["event_by_id"],
        outcome_by_id=inputs["outcome_by_id"],
    )
    current_human_sha = bindings_before["current_human_snapshot"]["decisions"][
        "sha256"
    ]
    override = gate.build_runtime_positive_override_context_v1(
        current_human_overlay=bindings_before["current_human"],
        current_human_overlay_sha256=current_human_sha,
        outcome_by_id=production_context["outcome_by_id"],
    )
    ts_dump_rule_context = bindings_before["gate_manifest"][
        "scientific_rule_context"
    ]
    dtt_rule_context = bindings_before["dtt_gate_manifest"][
        "scientific_rule_context"
    ]
    if rule_context_by_id is None:
        if rule_ids != INTEGRATED_AUTO_NEGATIVE_RULE_IDS:
            raise ValueError("CUSTOM_RULE_REGISTRY_CONTEXT_REQUIRED")
        effective_rule_context_by_id: Mapping[str, Mapping[str, Any]] = {
            gate.RULE_ID: ts_dump_rule_context,
            dtt_gate.RULE_ID: dtt_rule_context,
        }
    else:
        effective_rule_context_by_id = rule_context_by_id
    if override_context_by_id is None:
        if rule_ids != INTEGRATED_AUTO_NEGATIVE_RULE_IDS:
            raise ValueError("CUSTOM_RULE_REGISTRY_OVERRIDE_CONTEXT_REQUIRED")
        effective_override_context_by_id: Mapping[str, Any] = {
            gate.RULE_ID: override,
            dtt_gate.RULE_ID: override,
        }
    else:
        effective_override_context_by_id = override_context_by_id
    if set(effective_rule_context_by_id) != set(rule_ids) or set(
        effective_override_context_by_id
    ) != set(rule_ids):
        raise ValueError("EXACT_RULE_RUNTIME_CONTEXT_COVERAGE_INVALID")

    event_evaluation_by_key: dict[
        tuple[str, str], TaskDomainAutoNegativeEventEvaluation
    ] = {}
    evaluations_by_unit: dict[
        str, list[TaskDomainAutoNegativeEventEvaluation]
    ] = defaultdict(list)
    for event_id in sorted(inputs["event_by_id"]):
        evaluations = dispatch_exact_auto_negative_rules_v1(
            event=inputs["event_by_id"][event_id],
            outcome=production_context["outcome_by_id"][event_id],
            rule_context_by_id=effective_rule_context_by_id,
            override_context_by_id=effective_override_context_by_id,
            registry=registrations,
        )
        if tuple(item.rule_id for item in evaluations) != rule_ids:
            raise ValueError("EXACT_RULE_DISPATCH_ORDER_OR_COVERAGE_MISMATCH")
        for evaluation in evaluations:
            event_evaluation_by_key[(event_id, evaluation.rule_id)] = evaluation
            evaluations_by_unit[inputs["unit_by_event"][event_id]].append(
                evaluation
            )

    routes: dict[str, SuccessorTaskDomainRoutingResult] = {}
    for unit_id in sorted(inputs["unit_by_id"]):
        routes[unit_id] = route_successor_task_domain_review_unit_v1(
            review_unit=inputs["unit_by_id"][unit_id],
            event_evaluations=evaluations_by_unit[unit_id],
            human_unit_state=inputs["human_unit_by_id"][unit_id],
            registered_rule_ids=rule_ids,
        )

    event_rows: list[dict[str, object]] = []
    for event_id in sorted(inputs["event_by_id"]):
        event = inputs["event_by_id"][event_id]
        unit_id = inputs["unit_by_event"][event_id]
        human = inputs["human_unit_by_id"][unit_id]
        route = routes[unit_id]
        for rule_id in rule_ids:
            evaluation = event_evaluation_by_key[(event_id, rule_id)]
            event_rows.append(
                {
                    "canonical_event_id": event_id,
                    "review_unit_id": unit_id,
                    "pdb_id": event["pdb_id"],
                    "ligand_component_id": event["ligand_component_id"],
                    "human_workflow_status": human["workflow_status"],
                    "human_training_domain_relevance_decision": human[
                        "training_domain_relevance_decision"
                    ],
                    "rule_id": evaluation.rule_id,
                    "gate_event_status": evaluation.status,
                    "gate_event_reason": evaluation.reason,
                    "unit_final_task_domain_route": route.route_status,
                    "unit_final_route_reason": route.route_reason,
                    "human_precedence_applied": str(
                        route.human_precedence_applied
                    ).lower(),
                    "effective_auto_negative": str(
                        route.effective_new_auto_negative
                    ).lower(),
                    "downstream_positive_chemistry_review_required": str(
                        route.downstream_chemistry_review_required
                    ).lower(),
                }
            )

    unit_rows: list[dict[str, object]] = []
    for unit_id in sorted(routes):
        route = routes[unit_id]
        unit_rows.append(
            {
                "review_unit_id": unit_id,
                "event_count": route.event_count,
                "human_workflow_status": route.human_workflow_status,
                "human_training_domain_relevance_decision": (
                    route.human_relevance_decision
                ),
                "selected_auto_negative_rule_id": route.auto_negative_rule_id,
                "selected_rule_matched_event_count": (
                    route.auto_negative_event_match_count
                ),
                "selected_rule_all_events_match": str(
                    route.gate_unit_all_events_match
                ).lower(),
                "total_gate_invalid_evaluation_count": (
                    route.total_gate_invalid_evaluation_count
                ),
                "per_rule_evidence_json": _rule_evidence_json(route),
                "final_task_domain_route": route.route_status,
                "final_route_reason": route.route_reason,
                "effective_new_auto_negative": str(
                    route.effective_new_auto_negative
                ).lower(),
                "downstream_chemistry_review_required": str(
                    route.downstream_chemistry_review_required
                ).lower(),
                "human_overlay_mutated": "false",
            }
        )

    event_payload = _csv_bytes(EVENT_HEADER, event_rows)
    unit_payload = _csv_bytes(UNIT_HEADER, unit_rows)
    manifest = _build_manifest_v1(
        bindings=bindings_before,
        production_audit=production_context["audit"],
        integrated_rule_ids=rule_ids,
        event_payload=event_payload,
        unit_payload=unit_payload,
    )
    manifest_payload = _json_bytes(manifest)

    route_units = Counter(route.route_status for route in routes.values())
    route_events = Counter()
    for route in routes.values():
        route_events[route.route_status] += route.event_count
    ts_dump_evaluations = [
        item
        for (event_id, rule_id), item in event_evaluation_by_key.items()
        if rule_id == gate.RULE_ID
    ]
    raw_matched_events = sum(
        item.status == gate.MATCHED_AUTO_NEGATIVE_EXACT
        for item in ts_dump_evaluations
    )
    raw_matched_units = sum(
        item.all_events_match
        for route in routes.values()
        for item in route.rule_evidence
        if item.rule_id == gate.RULE_ID
    )
    raw_invalid_events = sum(
        item.status == gate.INVALID_EVIDENCE for item in ts_dump_evaluations
    )
    raw_rule_metrics_by_rule: dict[str, dict[str, int]] = {}
    effective_auto_negative_metrics_by_rule: dict[str, dict[str, int]] = {}
    for rule_id in rule_ids:
        rule_evaluations = [
            item
            for (_event_id, observed_rule_id), item in event_evaluation_by_key.items()
            if observed_rule_id == rule_id
        ]
        raw_rule_metrics_by_rule[rule_id] = {
            "matched_events": sum(
                item.status == gate.MATCHED_AUTO_NEGATIVE_EXACT
                for item in rule_evaluations
            ),
            "fully_matched_units": sum(
                item.all_events_match
                for route in routes.values()
                for item in route.rule_evidence
                if item.rule_id == rule_id
            ),
            "invalid_events": sum(
                item.status == gate.INVALID_EVIDENCE
                for item in rule_evaluations
            ),
        }
        selected_routes = [
            route
            for route in routes.values()
            if route.route_status == AUTO_NEGATIVE_EXACT_FINAL
            and route.auto_negative_rule_id == rule_id
        ]
        effective_auto_negative_metrics_by_rule[rule_id] = {
            "events": sum(route.event_count for route in selected_routes),
            "units": len(selected_routes),
        }
    matched_rule_event_evaluations = sum(
        item.status == gate.MATCHED_AUTO_NEGATIVE_EXACT
        for item in event_evaluation_by_key.values()
    )
    invalid_rule_event_evaluations = sum(
        item.status == gate.INVALID_EVIDENCE
        for item in event_evaluation_by_key.values()
    )
    fully_matched_rule_unit_pairs = sum(
        item.all_events_match
        for route in routes.values()
        for item in route.rule_evidence
    )
    multiple_full_match_conflict_units = sum(
        sum(item.all_events_match for item in route.rule_evidence) > 1
        for route in routes.values()
    )
    auto_units = route_units[AUTO_NEGATIVE_EXACT_FINAL]
    auto_events = route_events[AUTO_NEGATIVE_EXACT_FINAL]
    human_progress = bindings_before["current_human_progress"]
    resolved_units = (
        route_units[HUMAN_NOT_RELEVANT_FINAL]
        + route_units[HUMAN_RELEVANT_FINAL]
        + auto_units
    )
    required_statuses = {
        HUMAN_REVIEW_REQUIRED,
        HUMAN_REVIEW_REQUIRED_DEFERRED,
        HUMAN_REVIEW_REQUIRED_GATE_INVALID,
    }
    required_units = sum(route_units[status] for status in required_statuses)
    required_events = sum(route_events[status] for status in required_statuses)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "snapshot_semantics": SNAPSHOT_SEMANTICS,
        "candidate_events": len(inputs["event_by_id"]),
        "candidate_units": len(unit_rows),
        "legacy_frozen_candidate_population": {
            "candidate_events": len(inputs["event_by_id"]),
            "candidate_units": len(unit_rows),
        },
        "current_human_overlay": {
            "reviewed_units": human_progress["reviewed_units"],
            "unreviewed_units": human_progress["unreviewed_units"],
            "not_relevant_units": human_progress["not_relevant_units"],
            "relevant_units": human_progress["relevant_units"],
            "deferred_units": human_progress["deferred_units"],
        },
        "human_overlay_reviewed_units": human_progress["reviewed_units"],
        "human_overlay_unreviewed_units": human_progress["unreviewed_units"],
        "human_not_relevant_final_units": route_units[
            HUMAN_NOT_RELEVANT_FINAL
        ],
        "human_relevant_final_units": route_units[HUMAN_RELEVANT_FINAL],
        "auto_negative_exact_final_units": auto_units,
        "human_review_required_units": route_units[HUMAN_REVIEW_REQUIRED],
        "human_review_required_deferred_units": route_units[
            HUMAN_REVIEW_REQUIRED_DEFERRED
        ],
        "gate_invalid_units": route_units[HUMAN_REVIEW_REQUIRED_GATE_INVALID],
        "unit_route_counts": {
            status: route_units[status] for status in ROUTE_STATUSES
        },
        "event_route_counts": {
            status: route_events[status] for status in ROUTE_STATUSES
        },
        "raw_gate_matched_events": raw_matched_events,
        "raw_gate_matched_units": raw_matched_units,
        "raw_gate_invalid_events": raw_invalid_events,
        "raw_gate_metric_semantics": "LEGACY_TS_DUMP_RULE_ONLY",
        "raw_rule_metrics_by_rule": raw_rule_metrics_by_rule,
        "total_rule_event_evaluation_count": len(event_evaluation_by_key),
        "matched_rule_event_evaluation_count": (
            matched_rule_event_evaluations
        ),
        "invalid_rule_event_evaluation_count": (
            invalid_rule_event_evaluations
        ),
        "fully_matched_rule_unit_pairs": fully_matched_rule_unit_pairs,
        "multiple_full_match_conflict_units": multiple_full_match_conflict_units,
        "effective_new_auto_negative_events": auto_events,
        "effective_new_auto_negative_units": auto_units,
        "effective_auto_negative_metrics_by_rule": (
            effective_auto_negative_metrics_by_rule
        ),
        "ts_dump_effective_auto_negative_events": (
            effective_auto_negative_metrics_by_rule.get(
                gate.RULE_ID, {"events": 0}
            )["events"]
        ),
        "ts_dump_effective_auto_negative_units": (
            effective_auto_negative_metrics_by_rule.get(
                gate.RULE_ID, {"units": 0}
            )["units"]
        ),
        "dtt_incremental_effective_auto_negative_events": (
            effective_auto_negative_metrics_by_rule.get(
                dtt_gate.RULE_ID, {"events": 0}
            )["events"]
        ),
        "dtt_incremental_effective_auto_negative_units": (
            effective_auto_negative_metrics_by_rule.get(
                dtt_gate.RULE_ID, {"units": 0}
            )["units"]
        ),
        "new_machine_resolved_events": auto_events,
        "new_machine_resolved_units": auto_units,
        "effective_task_domain_resolved_units": resolved_units,
        "effective_task_domain_human_review_required_units": required_units,
        "effective_task_domain_human_review_required_events": required_events,
        "integrated_auto_negative_rule_count": len(rule_ids),
        "integrated_auto_negative_rule_ids": list(rule_ids),
        "current_production_exact_positive_authority_source": (
            CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE.as_posix()
        ),
        "current_production_exact_positive_authority_event_count": len(
            production_context["positive_event_ids"]
        ),
        "current_production_positive_integration_safe": True,
        "future_production_authority_change_requires_successor_rebuild": True,
        "human_overlay_modified": False,
        "legacy_triage_modified": False,
        "gate_artifacts_modified": False,
        "ts_dump_shadow_artifacts_modified": False,
        "dtt_shadow_artifacts_modified": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
        "production_materialization_performed": False,
        "live_routing_ready": invalid_rule_event_evaluations == 0
        and route_units[HUMAN_REVIEW_REQUIRED_GATE_INVALID] == 0,
        "ready_for_gpt_review": invalid_rule_event_evaluations == 0
        and route_units[HUMAN_REVIEW_REQUIRED_GATE_INVALID] == 0,
        "recommended_next_step_exactly": (
            "gpt_audit_DTT_successor_integration_then_commit_push_two_rule_"
            "successor_snapshot"
        ),
        "output_sha256_excluding_summary": {
            MANIFEST: _sha(manifest_payload),
            EVENT_INVENTORY: _sha(event_payload),
            UNIT_INVENTORY: _sha(unit_payload),
        },
    }
    summary_payload = _json_bytes(summary)
    artifacts = {
        MANIFEST: manifest_payload,
        EVENT_INVENTORY: event_payload,
        UNIT_INVENTORY: unit_payload,
        SUMMARY: summary_payload,
    }

    bindings_after = verify_predecessor_bindings_v1(repo_root)
    for field in (
        "legacy",
        "published_gate",
        "published_dtt_gate",
        "current_human_snapshot",
        "current_production_authority_binding",
    ):
        if bindings_after[field] != bindings_before[field]:
            raise ValueError("SOURCE_INPUTS_MODIFIED_DURING_BUILD:" + field)
    return {name: artifacts[name] for name in OUTPUT_FILENAMES}


def verify_human_snapshot_payload_binding_v1(
    manifest: Mapping[str, Any], current_human_overlay_payload: bytes
) -> bool:
    """Raise stale-input evidence when current human content SHA changes."""

    try:
        expected = manifest["current_human_snapshot_binding"]["decisions"][
            "sha256"
        ]
    except (KeyError, TypeError) as error:
        raise ValueError("SNAPSHOT_HUMAN_BINDING_MISSING") from error
    if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
        raise ValueError("SNAPSHOT_HUMAN_BINDING_INVALID")
    if _sha(current_human_overlay_payload) != expected:
        raise ValueError("CURRENT_HUMAN_ROUTING_SNAPSHOT_STALE")
    return True


def verify_current_production_positive_snapshot_binding_v1(
    manifest: Mapping[str, Any], current_authority_registry_payload: bytes
) -> bool:
    """Raise stale-input evidence when current production authority changes."""

    try:
        expected = manifest[
            "current_production_exact_positive_authority_binding"
        ]["sha256"]
    except (KeyError, TypeError) as error:
        raise ValueError("SNAPSHOT_PRODUCTION_AUTHORITY_BINDING_MISSING") from error
    if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
        raise ValueError("SNAPSHOT_PRODUCTION_AUTHORITY_BINDING_INVALID")
    if _sha(current_authority_registry_payload) != expected:
        raise ValueError("CURRENT_PRODUCTION_POSITIVE_ROUTING_SNAPSHOT_STALE")
    return True


def _verify_published_gate_snapshot_payload_bindings_v1(
    *,
    manifest: Mapping[str, Any],
    manifest_field: str,
    current_payload_by_path: Mapping[str, bytes],
    error_prefix: str,
) -> bool:
    try:
        bindings = manifest[manifest_field]
    except (KeyError, TypeError) as error:
        raise ValueError(error_prefix + "_SNAPSHOT_BINDING_MISSING") from error
    if not isinstance(bindings, Mapping) or set(bindings) != set(
        current_payload_by_path
    ):
        raise ValueError(error_prefix + "_SNAPSHOT_BINDING_INVALID")
    for path, payload in current_payload_by_path.items():
        expected = bindings.get(path)
        if (
            not isinstance(expected, Mapping)
            or not isinstance(expected.get("byte_count"), int)
            or not isinstance(expected.get("sha256"), str)
            or not _SHA256_RE.fullmatch(expected["sha256"])
        ):
            raise ValueError(error_prefix + "_SNAPSHOT_BINDING_INVALID")
        if (
            len(payload) != expected["byte_count"]
            or _sha(payload) != expected["sha256"]
        ):
            raise ValueError(error_prefix + "_ROUTING_SNAPSHOT_STALE")
    return True


def verify_published_ts_dump_gate_snapshot_payload_bindings_v1(
    manifest: Mapping[str, Any], current_payload_by_path: Mapping[str, bytes]
) -> bool:
    """Fail when any published TS/dUMP gate artifact differs from the snapshot."""

    return _verify_published_gate_snapshot_payload_bindings_v1(
        manifest=manifest,
        manifest_field="published_ts_dump_gate_artifact_bindings",
        current_payload_by_path=current_payload_by_path,
        error_prefix="PUBLISHED_TS_DUMP_GATE",
    )


def verify_published_dtt_gate_snapshot_payload_bindings_v1(
    manifest: Mapping[str, Any], current_payload_by_path: Mapping[str, bytes]
) -> bool:
    """Fail when any immutable published DTT gate artifact drifts."""

    return _verify_published_gate_snapshot_payload_bindings_v1(
        manifest=manifest,
        manifest_field="published_dtt_gate_artifact_bindings",
        current_payload_by_path=current_payload_by_path,
        error_prefix="PUBLISHED_DTT_GATE",
    )


def verify_current_snapshot_v1(repo_root: Path) -> bool:
    manifest = _read_json_object(repo_root / OUTPUT_ROOT_RELATIVE / MANIFEST)
    human_payload = (repo_root / gate.HUMAN_DECISIONS_RELATIVE).read_bytes()
    production_payload = (
        repo_root / CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE
    ).read_bytes()
    ts_dump_payloads = {
        path.as_posix(): (repo_root / path).read_bytes()
        for path in GATE_ARTIFACT_BINDINGS
    }
    dtt_payloads = {
        path.as_posix(): (repo_root / path).read_bytes()
        for path in DTT_GATE_ARTIFACT_BINDINGS
    }
    return bool(
        verify_human_snapshot_payload_binding_v1(manifest, human_payload)
        and verify_current_production_positive_snapshot_binding_v1(
            manifest, production_payload
        )
        and verify_published_ts_dump_gate_snapshot_payload_bindings_v1(
            manifest, ts_dump_payloads
        )
        and verify_published_dtt_gate_snapshot_payload_bindings_v1(
            manifest, dtt_payloads
        )
    )


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_v1(
    *, repo_root: Path, output_root: Path | None = None
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = (
        output_root.resolve()
        if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    authorized = repo_root / OUTPUT_ROOT_RELATIVE
    if target != authorized:
        try:
            target.relative_to(Path(tempfile.gettempdir()).resolve())
        except ValueError as error:
            raise ValueError("OUTPUT_ROOT_OUTSIDE_AUTHORIZED_PATH") from error
    artifacts = build_artifacts_v1(repo_root=repo_root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(target / name, artifacts[name])
    return json.loads(artifacts[SUMMARY])


def verify_deterministic_replay_v1(repo_root: Path) -> dict[str, str]:
    output_root = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    expected = build_artifacts_v1(repo_root=repo_root)
    result: dict[str, str] = {}
    for name in OUTPUT_FILENAMES:
        observed = (output_root / name).read_bytes()
        if observed != expected[name]:
            raise ValueError("OUTPUT_NOT_BYTE_IDENTICAL_ON_REPLAY:" + name)
        result[name] = _sha(observed)
    return result
