"""Safe execution workspace for CovaPIE post-only CYS-SG human review V1.

This module joins a mutable human-decision overlay to a SHA-bound, read-only
machine-evidence packet.  It never creates chemistry authority, materializes a
training sample, accesses the network, or modifies the frozen triage packet.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any


SCHEMA_VERSION = "covapie_bulk_post_only_cys_sg_human_review_v1"
OVERLAY_SCHEMA_VERSION = "covapie_post_only_human_review_decisions_v1"
DECISION_SCHEMA_VERSION = "covapie_post_only_human_review_decision_schema_v1"
EVIDENCE_BASELINE_COMMIT = "85073c3208633fefa63fc36e83f76215687d53dc"
# Backward-compatible display alias. Runtime gates must use the explicitly
# named evidence baseline and must not equate it with the current HEAD.
BASELINE_COMMIT = EVIDENCE_BASELINE_COMMIT
BASELINE_SUBJECT = "add CovaPIE post-only Cys-SG training candidate triage v1"

BASELINE_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_post_only_cys_sg_training_candidate_triage_v1"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_post_only_cys_sg_human_review_v1"
)

GUIDE = "README.md"
DECISION_SCHEMA = "covapie_post_only_human_review_decision_schema_v1.json"
WORKLIST = "covapie_post_only_human_review_worklist_v1.csv"
DECISIONS = "covapie_post_only_human_review_decisions_v1.json"
PROGRESS = "covapie_post_only_human_review_progress_v1.json"
OUTPUT_FILENAMES = (GUIDE, DECISION_SCHEMA, WORKLIST, DECISIONS, PROGRESS)
STATIC_OUTPUT_FILENAMES = (GUIDE, DECISION_SCHEMA, WORKLIST)
MUTABLE_OUTPUT_FILENAMES = (DECISIONS, PROGRESS)

BASELINE_ARTIFACT_SHA256 = {
    "README.md": "4caf6f5d789acfa74c20ac6baa98cb9f0633bb8470b6e3467e95e63dac947fa6",
    "covapie_bulk_post_only_training_candidate_event_inventory_v1.csv": (
        "a1e48d9efaa9b0f5f1b1d7d5988d9f54c07c22d7249b5a7b43dee31fd6efaa75"
    ),
    "covapie_bulk_post_only_training_review_unit_inventory_v1.csv": (
        "021cf3709c3e6172c592c1fe5cdf7254a87fb345cd23d6d80a5bfb515d8b9713"
    ),
    "covapie_bulk_post_only_training_domain_relevance_evidence_v1.csv": (
        "b33077c36804ebffeb5d15e8ac735f2a13cb4c9673fd6c0f079ff414b34522de"
    ),
    "covapie_bulk_post_only_training_candidate_summary_v1.json": (
        "1f8deb600137598786b3566c6fd35f0e044e150a306fe75da98f61c59dda07ac"
    ),
    "covapie_bulk_post_only_training_human_review_packet_v1.json": (
        "39f8afd7b8f62531f9f8704163cc7a444c3b008ff8d4610744d90b4918053194"
    ),
}
EVENT_INVENTORY = "covapie_bulk_post_only_training_candidate_event_inventory_v1.csv"
REVIEW_UNIT_INVENTORY = "covapie_bulk_post_only_training_review_unit_inventory_v1.csv"
REVIEW_PACKET = "covapie_bulk_post_only_training_human_review_packet_v1.json"
SUMMARY = "covapie_bulk_post_only_training_candidate_summary_v1.json"

# Registry inputs remain read-only.  The first four are repository-relative;
# the final three are relative to the repository parent (the covapie-state
# sibling).  No absolute machine path is emitted into an artifact.
AUTHORITY_SOURCE_BINDINGS = {
    "current11_reaction_family_design_registry": {
        "scope": "repository",
        "path": (
            "data/derived/covalent_small/"
            "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/"
            "covapie_cys_sg_reaction_family_registry.csv"
        ),
        "sha256": "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    },
    "current11_warhead_rule_design_registry": {
        "scope": "repository",
        "path": (
            "data/derived/covalent_small/"
            "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/"
            "covapie_cys_sg_warhead_rule_registry.csv"
        ),
        "sha256": "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    },
    "current11_family_rule_authority_registry": {
        "scope": "repository",
        "path": (
            "data/derived/covalent_small/"
            "covapie_current11_reaction_family_and_approved_warhead_rule_"
            "authority_binding_v1/"
            "covapie_family_and_warhead_rule_authority_registry.csv"
        ),
        "sha256": "4899d4664acf45d5ee90283e7977d62385b3a70fe41e082f4d060388be7e106b",
    },
    "role_semantics_registry": {
        "scope": "repository",
        "path": (
            "data/derived/covalent_small/"
            "covapie_role_annotation_input_authority_gap_resolution_v1/"
            "covapie_role_input_authority_semantics_registry.csv"
        ),
        "sha256": "6e08352146376bc3a4635b9c2a3155246e4a69dbc1a560c580573548a2479adb",
    },
    "current11_unified_effective_authority_view": {
        "scope": "repository_parent",
        "path": (
            "covapie-state/manual-review/"
            "covapie_current11_unified_effective_authority_view_v1.json"
        ),
        "sha256": "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774",
    },
    "approved_k36_reaction_family_authority": {
        "scope": "repository_parent",
        "path": (
            "covapie-state/manual-review/recovered7-targeted-chemistry-review-v1/"
            "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
            "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92/"
            "reaction_family_authority_v1.json"
        ),
        "sha256": "5eb39ac01770dbb8721a48d7ae6bf77fc6cb07493ca00a0eb5756ebf10921461",
    },
    "approved_k36_warhead_rule_authority": {
        "scope": "repository_parent",
        "path": (
            "covapie-state/manual-review/recovered7-targeted-chemistry-review-v1/"
            "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
            "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92/"
            "warhead_rule_authority_v1.json"
        ),
        "sha256": "1b8927693386aa8c72fed8677d59bdb3b5b56d4e89a09d88a908341fec0a19b2",
    },
}

APPROVED_REACTION_FAMILY_IDS = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_A06FD171EB8080D8",
)
APPROVED_WARHEAD_RULE_IDS = (
    "COVAPIE_CYS_SG_WARHEAD_RULE_855163C772D500C7",
)
NEW_FAMILY_REVIEW = "NEW_WARHEAD_FAMILY_REQUIRES_AUTHORITY_REVIEW"
EXISTING_FAMILY = "EXISTING_APPROVED_CANONICAL_REACTION_FAMILY"

WORKFLOW_STATUSES = ("UNREVIEWED", "IN_PROGRESS", "COMPLETED", "DEFERRED")
RELEVANCE_DECISIONS = (
    "RELEVANT_FOR_COVAPIE_POST_ONLY_V1",
    "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
    "DEFERRED_INSUFFICIENT_EVIDENCE",
)
REACTIVE_ATOM_STATUSES = ("CONFIRMED", "REJECTED", "DEFERRED")
GEOMETRY_USABILITY = ("YES", "NO", "DEFERRED")
EVENT_USE_DECISIONS = ("INCLUDE", "EXCLUDE", "DEFERRED")

MACHINE_SUPPORTED = "COVALENT_SMALL_MOLECULE_TASK_RELEVANCE_SUPPORTED"
MACHINE_NON_TARGET = "LIKELY_BIOCHEMICAL_OR_NON_TARGET_GENERATION_EVENT"
MACHINE_REVIEW = "TASK_RELEVANCE_HUMAN_REVIEW_REQUIRED"
MACHINE_INSUFFICIENT = "TASK_RELEVANCE_EVIDENCE_INSUFFICIENT"
MACHINE_STATUSES = frozenset(
    (MACHINE_SUPPORTED, MACHINE_NON_TARGET, MACHINE_REVIEW, MACHINE_INSUFFICIENT)
)

WORKLIST_HEADER = (
    "review_order",
    "priority",
    "review_unit_id",
    "event_count",
    "pdb_ids",
    "ligand_component_ids",
    "machine_status_distribution",
    "representative_event_id",
    "predicted_splits",
    "topology_availability",
    "decision_state",
)

UNIT_FIELDS = frozenset(
    (
        "review_unit_id",
        "workflow_status",
        "training_domain_relevance_decision",
        "reactive_atom_confirmation",
        "warhead_family_decision",
        "warhead_atom_ids",
        "roles",
        "reviewer_id",
        "reviewed_at_utc",
        "review_rationale",
        "events",
    )
)
EVENT_FIELDS = frozenset(
    (
        "canonical_event_id",
        "post_geometry_training_usable",
        "event_training_use_decision",
        "event_exclusion_reason",
    )
)
OVERLAY_FIELDS = frozenset(
    (
        "schema_version",
        "overlay_role",
        "baseline_bindings",
        "authority_vocabulary_bindings",
        "units",
        "decision_history",
        "production_authority_created",
        "production_materialization_performed",
        "training_materialization_performed",
        "authorized_population_changed",
    )
)
HISTORY_FIELDS = frozenset(
    (
        "sequence",
        "timestamp_utc",
        "reviewer_id",
        "target_kind",
        "review_unit_id",
        "canonical_event_id",
        "field",
        "old_value",
        "new_value",
        "previous_entry_sha256",
        "entry_sha256",
    )
)
UNIT_MUTABLE_FIELDS = frozenset(
    (
        "workflow_status",
        "training_domain_relevance_decision",
        "reactive_atom_confirmation",
        "warhead_family_decision",
        "warhead_atom_ids",
        "roles",
        "reviewer_id",
        "reviewed_at_utc",
        "review_rationale",
    )
)
EVENT_MUTABLE_FIELDS = frozenset(
    (
        "post_geometry_training_usable",
        "event_training_use_decision",
        "event_exclusion_reason",
    )
)


class HumanReviewValidationError(ValueError):
    """Raised whenever a human-review workspace gate fails closed."""


def _fail(reason: str) -> None:
    raise HumanReviewValidationError(reason)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise HumanReviewValidationError("CANONICAL_JSON_INVALID") from error
    return (text + "\n").encode("utf-8")


def _json_cell(value: object) -> str:
    return _json_bytes(value).decode("utf-8").rstrip("\n")


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=list(header), extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(header):
            _fail("CSV_ROW_SCHEMA_MISMATCH")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HumanReviewValidationError("JSON_READ_FAILED:" + path.name) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + path.name)
    return value


def _git(repo_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise HumanReviewValidationError("GIT_COMMAND_FAILED") from error
    return completed.stdout.strip()


def verify_execution_repository_state_v1(repo_root: Path) -> dict[str, object]:
    """Verify a synchronized main branch descending from the evidence baseline."""

    branch = _git(repo_root, "branch", "--show-current")
    head = _git(repo_root, "rev-parse", "HEAD")
    origin = _git(repo_root, "rev-parse", "origin/main")
    divergence = _git(
        repo_root, "rev-list", "--left-right", "--count", "HEAD...origin/main"
    )
    try:
        ahead_text, behind_text = divergence.split()
        ahead, behind = int(ahead_text), int(behind_text)
    except (TypeError, ValueError) as error:
        raise HumanReviewValidationError("GIT_DIVERGENCE_INVALID") from error
    if branch == "":
        _fail("EXECUTION_REPOSITORY_DETACHED_HEAD_REJECTED")
    if branch != "main":
        _fail("EXECUTION_REPOSITORY_WRONG_BRANCH_REJECTED")
    if head != origin:
        _fail("EXECUTION_REPOSITORY_HEAD_ORIGIN_MISMATCH")
    if (ahead, behind) != (0, 0):
        _fail("EXECUTION_REPOSITORY_DIVERGENCE_REJECTED")
    head_merge_base = _git(
        repo_root, "merge-base", EVIDENCE_BASELINE_COMMIT, head
    )
    origin_merge_base = _git(
        repo_root, "merge-base", EVIDENCE_BASELINE_COMMIT, origin
    )
    if head_merge_base != EVIDENCE_BASELINE_COMMIT:
        _fail("EVIDENCE_BASELINE_NOT_ANCESTOR_OF_HEAD")
    if origin_merge_base != EVIDENCE_BASELINE_COMMIT:
        _fail("EVIDENCE_BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "evidence_baseline_commit": EVIDENCE_BASELINE_COMMIT,
        "evidence_baseline_is_head_ancestor": True,
        "evidence_baseline_is_origin_main_ancestor": True,
    }


def verify_base_git_binding_v1(repo_root: Path) -> dict[str, object]:
    """Compatibility alias for the descendant-aware execution-state gate."""

    return verify_execution_repository_state_v1(repo_root)


def verify_starting_gate_v1(repo_root: Path) -> dict[str, object]:
    """Verify the stricter one-time clean-start gate named by the task."""

    binding = verify_execution_repository_state_v1(repo_root)
    if _git(repo_root, "status", "--porcelain=v1"):
        _fail("STARTING_WORKTREE_NOT_CLEAN")
    return binding


def _baseline_bindings() -> dict[str, object]:
    return {
        "baseline_commit": EVIDENCE_BASELINE_COMMIT,
        "baseline_packet_sha256": BASELINE_ARTIFACT_SHA256[REVIEW_PACKET],
        "baseline_review_unit_inventory_sha256": BASELINE_ARTIFACT_SHA256[
            REVIEW_UNIT_INVENTORY
        ],
        "baseline_event_inventory_sha256": BASELINE_ARTIFACT_SHA256[
            EVENT_INVENTORY
        ],
        "baseline_artifact_sha256": dict(BASELINE_ARTIFACT_SHA256),
    }


def _authority_bindings() -> dict[str, dict[str, str]]:
    return {
        name: {
            "scope": str(binding["scope"]),
            "path": str(binding["path"]),
            "sha256": str(binding["sha256"]),
        }
        for name, binding in AUTHORITY_SOURCE_BINDINGS.items()
    }


def verify_frozen_artifact_hashes_v1(repo_root: Path) -> dict[str, str]:
    root = repo_root / BASELINE_ROOT_RELATIVE
    observed: dict[str, str] = {}
    for filename, expected in BASELINE_ARTIFACT_SHA256.items():
        path = root / filename
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise HumanReviewValidationError(
                "FROZEN_BASELINE_READ_FAILED:" + filename
            ) from error
        digest = _sha(payload)
        if digest != expected:
            _fail("FROZEN_BASELINE_SHA256_MISMATCH:" + filename)
        observed[filename] = digest
    return observed


def _authority_path(repo_root: Path, binding: Mapping[str, object]) -> Path:
    scope = binding.get("scope")
    relative = Path(str(binding.get("path")))
    if relative.is_absolute():
        _fail("AUTHORITY_SOURCE_PATH_MUST_BE_RELATIVE")
    if scope == "repository":
        return repo_root / relative
    if scope == "repository_parent":
        return repo_root.parent / relative
    _fail("AUTHORITY_SOURCE_SCOPE_INVALID")


def verify_authority_vocabulary_sources_v1(repo_root: Path) -> dict[str, object]:
    """Bind approved authority separately from Current11 candidate registries."""

    payloads: dict[str, bytes] = {}
    for name, binding in AUTHORITY_SOURCE_BINDINGS.items():
        path = _authority_path(repo_root, binding)
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise HumanReviewValidationError(
                "AUTHORITY_SOURCE_READ_FAILED:" + name
            ) from error
        if _sha(payload) != binding["sha256"]:
            _fail("AUTHORITY_SOURCE_SHA256_MISMATCH:" + name)
        payloads[name] = payload

    try:
        family_rows = list(
            csv.DictReader(
                io.StringIO(
                    payloads["current11_reaction_family_design_registry"].decode(
                        "utf-8"
                    )
                )
            )
        )
        binding_rows = list(
            csv.DictReader(
                io.StringIO(
                    payloads["current11_family_rule_authority_registry"].decode(
                        "utf-8"
                    )
                )
            )
        )
        approved_family = json.loads(
            payloads["approved_k36_reaction_family_authority"]
        )
        approved_rule = json.loads(payloads["approved_k36_warhead_rule_authority"])
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HumanReviewValidationError("AUTHORITY_SOURCE_PARSE_FAILED") from error

    candidate_ids = sorted(row.get("reaction_family_id", "") for row in family_rows)
    if len(candidate_ids) != 7 or len(set(candidate_ids)) != 7:
        _fail("CURRENT11_CANDIDATE_FAMILY_REGISTRY_DRIFT")
    if any(row.get("approved") != "false" for row in family_rows):
        _fail("CURRENT11_CANDIDATE_FAMILY_APPROVAL_STATE_DRIFT")
    if any(
        row.get("reaction_family_authority_status") != "candidate_only"
        or row.get("approval_status") != "candidate_only"
        for row in binding_rows
    ):
        _fail("CURRENT11_FAMILY_RULE_BINDING_AUTHORITY_STATE_DRIFT")
    if approved_family.get("authority_id") not in APPROVED_REACTION_FAMILY_IDS:
        _fail("APPROVED_REACTION_FAMILY_ID_MISMATCH")
    if approved_family.get("authority_kind") != "reaction_family":
        _fail("APPROVED_REACTION_FAMILY_KIND_MISMATCH")
    if approved_rule.get("authority_id") not in APPROVED_WARHEAD_RULE_IDS:
        _fail("APPROVED_WARHEAD_RULE_ID_MISMATCH")
    if approved_rule.get("authority_kind") != "warhead_rule":
        _fail("APPROVED_WARHEAD_RULE_KIND_MISMATCH")
    signature = approved_rule.get("canonical_semantic_signature")
    if (
        type(signature) is not dict
        or signature.get("reaction_family_authority_id")
        != approved_family.get("authority_id")
    ):
        _fail("APPROVED_FAMILY_RULE_LINKAGE_MISMATCH")
    return {
        "approved_reaction_family_ids": list(APPROVED_REACTION_FAMILY_IDS),
        "approved_warhead_rule_ids": list(APPROVED_WARHEAD_RULE_IDS),
        "current11_candidate_only_reaction_family_ids": candidate_ids,
        "current11_candidate_ids_are_production_authority": False,
    }


def verify_frozen_evidence_baseline_v1(repo_root: Path) -> dict[str, object]:
    """Verify the immutable evidence commit and every bound evidence byte."""

    resolved_commit = _git(
        repo_root, "rev-parse", EVIDENCE_BASELINE_COMMIT + "^{commit}"
    )
    if resolved_commit != EVIDENCE_BASELINE_COMMIT:
        _fail("EVIDENCE_BASELINE_COMMIT_OBJECT_MISMATCH")
    subject = _git(
        repo_root,
        "show",
        "-s",
        "--format=%s",
        EVIDENCE_BASELINE_COMMIT,
    )
    if subject != BASELINE_SUBJECT:
        _fail("EVIDENCE_BASELINE_SUBJECT_MISMATCH")
    return {
        "evidence_baseline_commit": EVIDENCE_BASELINE_COMMIT,
        "evidence_baseline_subject": subject,
        "frozen_artifact_sha256": verify_frozen_artifact_hashes_v1(repo_root),
        "authority_vocabulary": verify_authority_vocabulary_sources_v1(repo_root),
    }


def verify_runtime_gates_v1(repo_root: Path) -> dict[str, object]:
    """Verify current execution state independently from immutable evidence."""

    return {
        "execution_repository_state": verify_execution_repository_state_v1(
            repo_root
        ),
        "frozen_evidence_baseline": verify_frozen_evidence_baseline_v1(
            repo_root
        ),
    }


def _packet(repo_root: Path) -> dict[str, Any]:
    return _read_json(repo_root / BASELINE_ROOT_RELATIVE / REVIEW_PACKET)


def _summary(repo_root: Path) -> dict[str, Any]:
    return _read_json(repo_root / BASELINE_ROOT_RELATIVE / SUMMARY)


def _machine_distribution(unit: Mapping[str, Any]) -> dict[str, int]:
    value = unit.get("training_domain_relevance_status_distribution")
    if type(value) is not dict or not value:
        _fail("MACHINE_STATUS_DISTRIBUTION_INVALID")
    result: dict[str, int] = {}
    for key, count in value.items():
        if key not in MACHINE_STATUSES or type(count) is not int or count <= 0:
            _fail("MACHINE_STATUS_DISTRIBUTION_INVALID")
        result[str(key)] = count
    return result


def priority_for_review_unit_v1(unit: Mapping[str, Any]) -> str:
    """Derive review ordering only; this function never makes a decision."""

    keys = set(_machine_distribution(unit))
    if keys == {MACHINE_SUPPORTED}:
        return "P0"
    if keys == {MACHINE_INSUFFICIENT}:
        return "P2"
    if keys == {MACHINE_NON_TARGET}:
        return "P3"
    if keys <= MACHINE_STATUSES:
        return "P1"
    _fail("MACHINE_STATUS_NOT_PRIORITY_COMPATIBLE")


def ordered_review_units_v1(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    units = packet.get("review_units")
    if type(units) is not list:
        _fail("REVIEW_UNITS_NOT_LIST")
    normalized: list[dict[str, Any]] = []
    for unit in units:
        if type(unit) is not dict:
            _fail("REVIEW_UNIT_NOT_OBJECT")
        priority_for_review_unit_v1(unit)
        normalized.append(unit)
    return sorted(
        normalized,
        key=lambda unit: (
            int(priority_for_review_unit_v1(unit)[1]),
            str(unit.get("review_unit_id", "")),
        ),
    )


def _event_topology_available(event: Mapping[str, Any]) -> bool:
    return (
        event.get("reactive_center_radius2_status")
        == "PUBLISHED_EVIDENCE_AVAILABLE"
        and bool(event.get("reactive_center_radius2_fingerprint"))
    )


def geometry_auxiliary_label_availability_v1(event: Mapping[str, Any]) -> str:
    if _event_topology_available(event):
        return "AVAILABLE_FOR_RADIUS2_DEPENDENT_LABELS"
    return "UNAVAILABLE_FOR_RADIUS2_DEPENDENT_LABELS"


def _topology_summary(unit: Mapping[str, Any]) -> str:
    events = unit.get("events_for_review")
    if type(events) is not list or not events:
        _fail("UNIT_EVENTS_INVALID")
    available = sum(_event_topology_available(event) for event in events)
    if available == len(events):
        return "ALL_EVENTS_RADIUS2_AVAILABLE"
    if available == 0:
        return "NO_EVENTS_RADIUS2_AVAILABLE"
    return "PARTIAL_EVENTS_RADIUS2_AVAILABLE"


def verify_frozen_baseline_facts_v1(repo_root: Path) -> dict[str, object]:
    """Re-derive the review population and evidence facts from frozen bytes."""

    hashes = verify_frozen_artifact_hashes_v1(repo_root)
    packet = _packet(repo_root)
    summary = _summary(repo_root)
    units = ordered_review_units_v1(packet)
    if len(units) != 36:
        _fail("REVIEW_UNIT_COUNT_MISMATCH")

    unit_ids: list[str] = []
    event_ids: list[str] = []
    events: list[dict[str, Any]] = []
    multi_units = 0
    multi_events = 0
    for unit in units:
        unit_id = unit.get("review_unit_id")
        if type(unit_id) is not str or not unit_id:
            _fail("REVIEW_UNIT_ID_INVALID")
        unit_ids.append(unit_id)
        unit_events = unit.get("events_for_review")
        if type(unit_events) is not list or not unit_events:
            _fail("UNIT_EVENTS_INVALID")
        if unit.get("event_count") != len(unit_events):
            _fail("UNIT_EVENT_COUNT_MISMATCH")
        if len(unit_events) > 1:
            multi_units += 1
            multi_events += len(unit_events)
        distribution = Counter(
            event.get("training_domain_machine_triage_status")
            for event in unit_events
        )
        if dict(sorted(distribution.items())) != dict(
            sorted(_machine_distribution(unit).items())
        ):
            _fail("UNIT_MACHINE_STATUS_DISTRIBUTION_MISMATCH")
        chemistry = unit.get("machine_chemistry_evidence")
        if type(chemistry) is not dict:
            _fail("MACHINE_CHEMISTRY_EVIDENCE_INVALID")
        if not chemistry.get("ccd_heavy_atom_inventory"):
            _fail("CCD_HEAVY_ATOM_INVENTORY_MISSING")
        if not chemistry.get("ccd_bond_inventory"):
            _fail("CCD_BOND_INVENTORY_MISSING")
        for field in (
            "review_status",
            "training_domain_relevance_decision",
            "warhead_family_decision",
            "warhead_atom_set_decision",
            "reactive_atom_confirmation",
            "scaffold_linker_warhead_role_decision",
            "reviewer_id",
            "review_rationale",
        ):
            if unit.get(field) != "":
                _fail("FROZEN_UNIT_HUMAN_FIELD_NOT_BLANK:" + field)
        for event in unit_events:
            if type(event) is not dict:
                _fail("EVENT_NOT_OBJECT")
            event_id = event.get("canonical_event_id")
            if type(event_id) is not str or not event_id:
                _fail("CANONICAL_EVENT_ID_INVALID")
            event_ids.append(event_id)
            events.append(event)
            for field in (
                "post_geometry_training_usable",
                "event_training_use_decision",
                "event_exclusion_reason",
            ):
                if event.get(field) != "":
                    _fail("FROZEN_EVENT_HUMAN_FIELD_NOT_BLANK:" + field)

    if len(set(unit_ids)) != 36:
        _fail("REVIEW_UNIT_DUPLICATE_OR_MISSING")
    if len(events) != 123 or len(set(event_ids)) != 123:
        _fail("EVENT_DUPLICATE_OR_MISSING")
    if (multi_units, multi_events) != (25, 112):
        _fail("MULTI_EVENT_WORKLOAD_MISMATCH")

    exact_identity = sum(
        event.get("exact_ccd_observed_heavy_atom_identity_coverage") is True
        for event in events
    )
    element_agreement = sum(
        event.get("exact_ccd_observed_heavy_atom_element_agreement") is True
        for event in events
    )
    reactive_exact = sum(
        event.get("reactive_ligand_atom_exact_coverage") is True for event in events
    )
    reactive_pair = sum(
        event.get("protein_reactive_atom") == "SG"
        and type(event.get("ligand_reactive_atom")) is str
        and bool(event.get("ligand_reactive_atom"))
        for event in events
    )
    post_distance = sum(
        type(event.get("post_distance_angstrom")) in (int, float)
        for event in events
    )
    ligand_coordinates = sum(
        event.get("full_ligand_coordinate_exact_coverage_status")
        == "EXACT_CCD_OBSERVED_HEAVY_ATOM_IDENTITY_AND_ELEMENT_COVERAGE"
        for event in events
    )
    pocket_coordinates = sum(
        event.get("pocket_coordinate_availability") is True for event in events
    )
    ccd_graph = sum(bool(event.get("ccd_component_graph_sha256")) for event in events)
    radius2 = sum(_event_topology_available(event) for event in events)
    observed = (
        exact_identity,
        element_agreement,
        reactive_exact,
        reactive_pair,
        post_distance,
        ligand_coordinates,
        pocket_coordinates,
        ccd_graph,
        radius2,
    )
    if observed != (123, 123, 123, 123, 123, 123, 123, 123, 115):
        _fail("FROZEN_EVIDENCE_COVERAGE_MISMATCH")
    if packet.get("accurate_experimental_pre_covalent_geometry_required") is not False:
        _fail("PRE_GEOMETRY_POLICY_DRIFT")
    if packet.get("pre_status_is_post_only_eligibility_hard_blocker") is not False:
        _fail("PRE_STATUS_POLICY_DRIFT")
    if packet.get("existing_production_chemistry_authority_semantics_changed") is not False:
        _fail("PRODUCTION_CHEMISTRY_SEMANTICS_DRIFT")

    post_readiness = summary.get("post_supervision_readiness")
    pre_policy = summary.get("pre_policy")
    if type(post_readiness) is not dict or type(pre_policy) is not dict:
        _fail("FROZEN_SUMMARY_CONTRACT_MISSING")
    if post_readiness.get("post_geometry_auxiliary_labels_derivable_count") != 115:
        _fail("POST_GEOMETRY_DERIVABILITY_MISMATCH")
    if pre_policy.get("accurate_pre_geometry_required_for_v1_training") is not False:
        _fail("SUMMARY_PRE_GEOMETRY_POLICY_DRIFT")
    if pre_policy.get("pre_status_is_post_only_training_hard_blocker") is not False:
        _fail("SUMMARY_PRE_STATUS_POLICY_DRIFT")
    if pre_policy.get("existing_production_chemistry_authority_semantics_changed") is not False:
        _fail("SUMMARY_CHEMISTRY_AUTHORITY_POLICY_DRIFT")

    unit_priority = Counter(priority_for_review_unit_v1(unit) for unit in units)
    event_priority = Counter()
    for unit in units:
        event_priority[priority_for_review_unit_v1(unit)] += int(unit["event_count"])
    if dict(unit_priority) != {"P0": 18, "P1": 4, "P2": 10, "P3": 4}:
        _fail("UNIT_PRIORITY_DISTRIBUTION_MISMATCH")
    if dict(event_priority) != {"P0": 39, "P1": 10, "P2": 37, "P3": 37}:
        _fail("EVENT_PRIORITY_DISTRIBUTION_MISMATCH")
    return {
        "artifact_sha256": hashes,
        "review_unit_count": len(units),
        "event_count": len(events),
        "multi_event_review_unit_count": multi_units,
        "event_count_inside_multi_event_units": multi_events,
        "exact_atom_identity_coverage_count": exact_identity,
        "element_agreement_count": element_agreement,
        "reactive_atom_exact_coverage_count": reactive_exact,
        "reactive_pair_count": reactive_pair,
        "post_distance_count": post_distance,
        "ligand_coordinate_count": ligand_coordinates,
        "pocket_coordinate_count": pocket_coordinates,
        "ccd_graph_count": ccd_graph,
        "radius2_topology_count": radius2,
        "post_geometry_mechanically_derivable_count": 115,
        "unit_priority_distribution": dict(sorted(unit_priority.items())),
        "event_priority_distribution": dict(sorted(event_priority.items())),
    }


def build_worklist_rows_v1(packet: Mapping[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for order, unit in enumerate(ordered_review_units_v1(packet), start=1):
        rows.append(
            {
                "review_order": order,
                "priority": priority_for_review_unit_v1(unit),
                "review_unit_id": unit["review_unit_id"],
                "event_count": unit["event_count"],
                "pdb_ids": _json_cell(unit["pdb_ids"]),
                "ligand_component_ids": _json_cell(unit["ligand_component_ids"]),
                "machine_status_distribution": _json_cell(
                    _machine_distribution(unit)
                ),
                "representative_event_id": unit[
                    "representative_canonical_event_id"
                ],
                "predicted_splits": _json_cell(unit["predicted_splits"]),
                "topology_availability": _topology_summary(unit),
                "decision_state": "UNREVIEWED",
            }
        )
    return rows


def _empty_event_decision(event_id: str) -> dict[str, object]:
    return {
        "canonical_event_id": event_id,
        "post_geometry_training_usable": "",
        "event_training_use_decision": "",
        "event_exclusion_reason": "",
    }


def _empty_unit_decision(unit: Mapping[str, Any]) -> dict[str, object]:
    events = sorted(
        (
            _empty_event_decision(str(event["canonical_event_id"]))
            for event in unit["events_for_review"]
        ),
        key=lambda event: str(event["canonical_event_id"]),
    )
    return {
        "review_unit_id": unit["review_unit_id"],
        "workflow_status": "UNREVIEWED",
        "training_domain_relevance_decision": "",
        "reactive_atom_confirmation": None,
        "warhead_family_decision": None,
        "warhead_atom_ids": [],
        "roles": {
            "scaffold_atom_ids": [],
            "linker_atom_ids": [],
            "warhead_atom_ids": [],
        },
        "reviewer_id": "",
        "reviewed_at_utc": "",
        "review_rationale": "",
        "events": events,
    }


def build_initial_overlay_v1(packet: Mapping[str, Any]) -> dict[str, object]:
    return {
        "schema_version": OVERLAY_SCHEMA_VERSION,
        "overlay_role": "HUMAN_REVIEW_DECISION_OVERLAY_NOT_PRODUCTION_AUTHORITY",
        "baseline_bindings": _baseline_bindings(),
        "authority_vocabulary_bindings": _authority_bindings(),
        "units": [
            _empty_unit_decision(unit) for unit in ordered_review_units_v1(packet)
        ],
        "decision_history": [],
        "production_authority_created": False,
        "production_materialization_performed": False,
        "training_materialization_performed": False,
        "authorized_population_changed": False,
    }


def build_decision_schema_v1(authority: Mapping[str, Any]) -> dict[str, object]:
    """Return the exact decision vocabulary and fail-closed cross-field contract."""

    return {
        "schema_version": DECISION_SCHEMA_VERSION,
        "decision_overlay_schema_version": OVERLAY_SCHEMA_VERSION,
        "schema_role": "VALIDATION_CONTRACT_NOT_PRODUCTION_CHEMISTRY_AUTHORITY",
        "frozen_machine_evidence_separate_from_human_decisions": True,
        "baseline_bindings": _baseline_bindings(),
        "authority_vocabulary_bindings": _authority_bindings(),
        "unit_workflow_status_allowed_values": list(WORKFLOW_STATUSES),
        "training_domain_relevance_decision_allowed_values": list(
            RELEVANCE_DECISIONS
        ),
        "reactive_atom_confirmation": {
            "allowed_status_values": list(REACTIVE_ATOM_STATUSES),
            "confirmed_atom_id_contract": (
                "CONFIRMED_REQUIRES_EXACT_FROZEN_LIGAND_REACTIVE_ATOM_ID"
            ),
            "correction_contract": (
                "REJECTED_REQUIRES_RATIONALE_AND_SEPARATE_CORRECTION_WORKFLOW"
            ),
        },
        "warhead_family_decision": {
            "allowed_decision_values": [EXISTING_FAMILY, NEW_FAMILY_REVIEW],
            "approved_existing_reaction_family_ids": list(
                authority["approved_reaction_family_ids"]
            ),
            "current11_candidate_only_reaction_family_ids": list(
                authority["current11_candidate_only_reaction_family_ids"]
            ),
            "candidate_only_ids_accepted_as_existing_approved_family": False,
            "new_family_requires_proposed_warhead_family_label": True,
            "proposal_creates_production_authority": False,
        },
        "warhead_atom_set": {
            "representation": "CANONICAL_LEXICOGRAPHIC_LIST_OF_CCD_HEAVY_ATOM_IDS",
            "nonempty_for_relevant_completed_unit": True,
            "unique": True,
            "explicit_hydrogen_forbidden": True,
            "confirmed_reactive_atom_required": True,
        },
        "roles": {
            "representation": {
                "scaffold_atom_ids": "CANONICAL_CCD_HEAVY_ATOM_ID_LIST",
                "linker_atom_ids": "CANONICAL_CCD_HEAVY_ATOM_ID_LIST",
                "warhead_atom_ids": "CANONICAL_CCD_HEAVY_ATOM_ID_LIST",
            },
            "sets_are_pairwise_disjoint": True,
            "union_equals_exact_ligand_heavy_atom_inventory": True,
            "warhead_role_equals_warhead_atom_set": True,
            "reactive_atom_in_warhead": True,
            "canonical_role_semantics": ["scaffold", "linker", "warhead"],
        },
        "event_level_decision": {
            "post_geometry_training_usable_allowed_values": list(
                GEOMETRY_USABILITY
            ),
            "event_training_use_decision_allowed_values": list(
                EVENT_USE_DECISIONS
            ),
            "include_requires_geometry_usable_yes": True,
            "exclude_requires_nonempty_reason": True,
            "events_are_independent": True,
            "radius2_unavailable_is_not_automatic_exclusion": True,
            "radius2_unavailable_auxiliary_status": (
                "UNAVAILABLE_FOR_RADIUS2_DEPENDENT_LABELS"
            ),
        },
        "reviewer_metadata": {
            "required_for_any_recorded_human_decision": [
                "reviewer_id",
                "reviewed_at_utc",
                "review_rationale",
            ],
            "initial_values_are_blank": True,
        },
        "cross_field_rules": [
            "NOT_RELEVANT_REQUIRES_BLANK_CHEMISTRY_AND_EVENT_FIELDS",
            "DEFERRED_RELEVANCE_REQUIRES_DEFERRED_WORKFLOW_STATUS",
            "RELEVANT_COMPLETED_REQUIRES_COMPLETE_CHEMISTRY_AND_EVERY_EVENT",
            "HUMAN_MACHINE_DISAGREEMENT_REQUIRES_RATIONALE",
            "NO_DECISION_CREATES_PRODUCTION_AUTHORITY_OR_TRAINING_MATERIALIZATION",
        ],
        "decision_history": {
            "mode": "APPEND_ONLY_HASH_CHAIN",
            "silent_overwrite_allowed": False,
            "history_replayed_against_empty_initial_overlay": True,
        },
    }


def _unit_by_id(
    overlay: Mapping[str, Any], unit_id: str
) -> dict[str, Any]:
    units = overlay.get("units")
    if type(units) is not list:
        _fail("OVERLAY_UNITS_NOT_LIST")
    matches = [unit for unit in units if unit.get("review_unit_id") == unit_id]
    if len(matches) != 1 or type(matches[0]) is not dict:
        _fail("OVERLAY_UNIT_ID_NOT_EXACT_ONE:" + unit_id)
    return matches[0]


def _event_by_id(unit: Mapping[str, Any], event_id: str) -> dict[str, Any]:
    events = unit.get("events")
    if type(events) is not list:
        _fail("OVERLAY_EVENTS_NOT_LIST")
    matches = [event for event in events if event.get("canonical_event_id") == event_id]
    if len(matches) != 1 or type(matches[0]) is not dict:
        _fail("OVERLAY_EVENT_ID_NOT_EXACT_ONE:" + event_id)
    return matches[0]


def _packet_unit_index(packet: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for unit in ordered_review_units_v1(packet):
        unit_id = str(unit["review_unit_id"])
        if unit_id in result:
            _fail("PACKET_UNIT_ID_DUPLICATE")
        result[unit_id] = unit
    return result


def _packet_event_index(unit: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for event in unit["events_for_review"]:
        event_id = str(event["canonical_event_id"])
        if event_id in result:
            _fail("PACKET_EVENT_ID_DUPLICATE")
        result[event_id] = event
    return result


def _is_canonical_atom_list(value: object) -> bool:
    return (
        type(value) is list
        and all(type(atom_id) is str and bool(atom_id) for atom_id in value)
        and len(set(value)) == len(value)
        and value == sorted(value)
    )


def _metadata_complete(unit: Mapping[str, Any]) -> bool:
    return all(
        type(unit.get(field)) is str and bool(str(unit[field]).strip())
        for field in ("reviewer_id", "reviewed_at_utc", "review_rationale")
    )


def _valid_utc_timestamp(value: object) -> bool:
    if type(value) is not str or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(None)


def _events_blank(unit: Mapping[str, Any]) -> bool:
    return all(
        event.get("post_geometry_training_usable") == ""
        and event.get("event_training_use_decision") == ""
        and event.get("event_exclusion_reason") == ""
        for event in unit["events"]
    )


def _chemistry_blank(unit: Mapping[str, Any]) -> bool:
    roles = unit.get("roles")
    return (
        unit.get("reactive_atom_confirmation") is None
        and unit.get("warhead_family_decision") is None
        and unit.get("warhead_atom_ids") == []
        and roles
        == {
            "scaffold_atom_ids": [],
            "linker_atom_ids": [],
            "warhead_atom_ids": [],
        }
    )


def _unit_has_human_content(unit: Mapping[str, Any]) -> bool:
    return not (
        unit.get("workflow_status") == "UNREVIEWED"
        and unit.get("training_domain_relevance_decision") == ""
        and _chemistry_blank(unit)
        and _events_blank(unit)
        and unit.get("reviewer_id") == ""
        and unit.get("reviewed_at_utc") == ""
        and unit.get("review_rationale") == ""
    )


def _validate_family_decision(value: object) -> bool:
    if type(value) is not dict or set(value) != {
        "decision",
        "canonical_reaction_family_id",
        "proposed_warhead_family_label",
    }:
        return False
    decision = value["decision"]
    family_id = value["canonical_reaction_family_id"]
    proposal = value["proposed_warhead_family_label"]
    if decision == EXISTING_FAMILY:
        return family_id in APPROVED_REACTION_FAMILY_IDS and proposal == ""
    if decision == NEW_FAMILY_REVIEW:
        return family_id == "" and type(proposal) is str and bool(proposal.strip())
    return False


def _validate_reactive_confirmation(
    value: object, packet_unit: Mapping[str, Any]
) -> bool:
    if type(value) is not dict or set(value) != {"status", "confirmed_atom_id"}:
        return False
    status = value["status"]
    atom_id = value["confirmed_atom_id"]
    if status not in REACTIVE_ATOM_STATUSES:
        return False
    if status == "CONFIRMED":
        return atom_id == packet_unit.get("ligand_reactive_atom")
    return atom_id == ""


def _validate_atom_and_role_sets(
    unit: Mapping[str, Any], packet_unit: Mapping[str, Any]
) -> bool:
    chemistry = packet_unit["machine_chemistry_evidence"]
    all_atoms = chemistry["ccd_atom_inventory"]
    heavy_atoms = chemistry["ccd_heavy_atom_inventory"]
    element_by_id = {atom["atom_id"]: atom["element"] for atom in all_atoms}
    heavy_ids = {atom["atom_id"] for atom in heavy_atoms}
    warhead = unit.get("warhead_atom_ids")
    if not _is_canonical_atom_list(warhead) or not warhead:
        return False
    for atom_id in warhead:
        if atom_id in element_by_id and str(element_by_id[atom_id]).upper() in {
            "H",
            "D",
            "T",
        }:
            _fail("EXPLICIT_HYDROGEN_ATOM_ID_REJECTED:" + atom_id)
        if atom_id not in heavy_ids:
            _fail("UNKNOWN_CCD_HEAVY_ATOM_ID_REJECTED:" + atom_id)
    confirmation = unit.get("reactive_atom_confirmation")
    if type(confirmation) is not dict:
        return False
    if confirmation.get("status") == "CONFIRMED":
        if confirmation.get("confirmed_atom_id") not in warhead:
            _fail("REACTIVE_ATOM_ABSENT_FROM_WARHEAD_SET")

    roles = unit.get("roles")
    if type(roles) is not dict or set(roles) != {
        "scaffold_atom_ids",
        "linker_atom_ids",
        "warhead_atom_ids",
    }:
        return False
    role_lists = [
        roles["scaffold_atom_ids"],
        roles["linker_atom_ids"],
        roles["warhead_atom_ids"],
    ]
    if not all(_is_canonical_atom_list(value) for value in role_lists):
        return False
    role_sets = [set(value) for value in role_lists]
    if any(role_sets[i] & role_sets[j] for i in range(3) for j in range(i + 1, 3)):
        _fail("ROLE_ATOM_SETS_OVERLAP")
    if set().union(*role_sets) != heavy_ids:
        _fail("ROLE_ATOM_SET_UNION_NOT_EXACT_HEAVY_ATOM_COVERAGE")
    if roles["warhead_atom_ids"] != warhead:
        _fail("ROLE_WARHEAD_SET_DIFFERS_FROM_WARHEAD_ATOM_SET")
    return True


def _validate_event_decision(
    event: Mapping[str, Any], packet_event: Mapping[str, Any]
) -> bool:
    geometry = event.get("post_geometry_training_usable")
    use = event.get("event_training_use_decision")
    reason = event.get("event_exclusion_reason")
    if geometry == "" and use == "" and reason == "":
        return False
    if geometry not in GEOMETRY_USABILITY or use not in EVENT_USE_DECISIONS:
        _fail("EVENT_DECISION_VOCABULARY_INVALID")
    if type(reason) is not str:
        _fail("EVENT_EXCLUSION_REASON_TYPE_INVALID")
    if use == "INCLUDE":
        if geometry != "YES":
            _fail("INCLUDE_REQUIRES_GEOMETRY_USABLE_YES")
        if reason != "":
            _fail("INCLUDE_REQUIRES_BLANK_EXCLUSION_REASON")
        include_evidence = (
            packet_event.get("exact_ccd_observed_heavy_atom_identity_coverage")
            is True
            and packet_event.get("exact_ccd_observed_heavy_atom_element_agreement")
            is True
            and packet_event.get("reactive_ligand_atom_exact_coverage") is True
            and packet_event.get("protein_reactive_atom") == "SG"
            and bool(packet_event.get("ligand_reactive_atom"))
            and packet_event.get("pocket_coordinate_availability") is True
            and packet_event.get("full_ligand_coordinate_exact_coverage_status")
            == "EXACT_CCD_OBSERVED_HEAVY_ATOM_IDENTITY_AND_ELEMENT_COVERAGE"
            and type(packet_event.get("protein_endpoint_coordinates")) is list
            and len(packet_event["protein_endpoint_coordinates"]) == 3
            and type(packet_event.get("ligand_endpoint_coordinates")) is list
            and len(packet_event["ligand_endpoint_coordinates"]) == 3
        )
        if not include_evidence:
            _fail("INCLUDE_FROZEN_EVIDENCE_PREREQUISITE_FAILED")
    elif use == "EXCLUDE":
        if not reason.strip():
            _fail("EXCLUDE_REQUIRES_NONEMPTY_REASON")
    elif reason != "":
        _fail("DEFERRED_EVENT_REQUIRES_BLANK_EXCLUSION_REASON")
    # Radius-2 absence is intentionally not an exclusion rule.  Downstream
    # consumers rejoin the packet and call the auxiliary availability helper.
    geometry_auxiliary_label_availability_v1(packet_event)
    return True


def _history_payload(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in entry.items() if key != "entry_sha256"}


def _history_entry_sha256(entry: Mapping[str, Any]) -> str:
    return _sha(_json_bytes(_history_payload(entry)))


def _history_target(
    overlay: Mapping[str, Any], entry: Mapping[str, Any]
) -> dict[str, Any]:
    unit = _unit_by_id(overlay, str(entry.get("review_unit_id", "")))
    if entry.get("target_kind") == "UNIT":
        if entry.get("canonical_event_id") != "":
            _fail("UNIT_HISTORY_EVENT_ID_MUST_BE_BLANK")
        if entry.get("field") not in UNIT_MUTABLE_FIELDS:
            _fail("UNIT_HISTORY_FIELD_NOT_MUTABLE")
        return unit
    if entry.get("target_kind") == "EVENT":
        if entry.get("field") not in EVENT_MUTABLE_FIELDS:
            _fail("EVENT_HISTORY_FIELD_NOT_MUTABLE")
        return _event_by_id(unit, str(entry.get("canonical_event_id", "")))
    _fail("HISTORY_TARGET_KIND_INVALID")


def _replay_history_v1(
    overlay: Mapping[str, Any], packet: Mapping[str, Any]
) -> None:
    history = overlay.get("decision_history")
    if type(history) is not list:
        _fail("DECISION_HISTORY_NOT_LIST")
    replay = build_initial_overlay_v1(packet)
    previous = ""
    for expected_sequence, entry in enumerate(history, start=1):
        if type(entry) is not dict or set(entry) != HISTORY_FIELDS:
            _fail("DECISION_HISTORY_ENTRY_SCHEMA_INVALID")
        if entry.get("sequence") != expected_sequence:
            _fail("DECISION_HISTORY_SEQUENCE_INVALID")
        if not _valid_utc_timestamp(entry.get("timestamp_utc")):
            _fail("DECISION_HISTORY_TIMESTAMP_INVALID")
        if type(entry.get("reviewer_id")) is not str or not entry[
            "reviewer_id"
        ].strip():
            _fail("DECISION_HISTORY_REVIEWER_INVALID")
        if entry.get("previous_entry_sha256") != previous:
            _fail("DECISION_HISTORY_CHAIN_PREDECESSOR_INVALID")
        digest = _history_entry_sha256(entry)
        if entry.get("entry_sha256") != digest:
            _fail("DECISION_HISTORY_ENTRY_SHA256_INVALID")
        target = _history_target(replay, entry)
        field = str(entry["field"])
        if target.get(field) != entry.get("old_value"):
            _fail("DECISION_HISTORY_OLD_VALUE_MISMATCH")
        if entry.get("old_value") == entry.get("new_value"):
            _fail("DECISION_HISTORY_NOOP_FORBIDDEN")
        target[field] = deepcopy(entry["new_value"])
        replay["decision_history"].append(deepcopy(entry))
        previous = digest
    if replay["units"] != overlay.get("units"):
        _fail("DECISION_STATE_NOT_DERIVABLE_FROM_APPEND_ONLY_HISTORY")


def _machine_human_disagreement(
    packet_unit: Mapping[str, Any], human_decision: str
) -> bool:
    statuses = set(_machine_distribution(packet_unit))
    if human_decision == "RELEVANT_FOR_COVAPIE_POST_ONLY_V1":
        return statuses == {MACHINE_NON_TARGET}
    if human_decision == "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK":
        return statuses == {MACHINE_SUPPORTED}
    return False


def _validate_unit_cross_fields(
    unit: Mapping[str, Any], packet_unit: Mapping[str, Any]
) -> None:
    if type(unit) is not dict or set(unit) != UNIT_FIELDS:
        _fail("OVERLAY_UNIT_SCHEMA_INVALID")
    if unit.get("workflow_status") not in WORKFLOW_STATUSES:
        _fail("WORKFLOW_STATUS_INVALID")
    relevance = unit.get("training_domain_relevance_decision")
    if relevance != "" and relevance not in RELEVANCE_DECISIONS:
        _fail("RELEVANCE_DECISION_INVALID")
    roles = unit.get("roles")
    if type(roles) is not dict or set(roles) != {
        "scaffold_atom_ids",
        "linker_atom_ids",
        "warhead_atom_ids",
    }:
        _fail("ROLE_SCHEMA_INVALID")
    events = unit.get("events")
    packet_events = _packet_event_index(packet_unit)
    if type(events) is not list or [
        event.get("canonical_event_id") for event in events
    ] != sorted(packet_events):
        _fail("OVERLAY_EVENT_ORDER_OR_COVERAGE_INVALID")
    for event in events:
        if type(event) is not dict or set(event) != EVENT_FIELDS:
            _fail("OVERLAY_EVENT_SCHEMA_INVALID")

    has_content = _unit_has_human_content(unit)
    metadata_fields = (
        unit.get("reviewer_id"),
        unit.get("reviewed_at_utc"),
        unit.get("review_rationale"),
    )
    if has_content:
        if not _metadata_complete(unit):
            if _machine_human_disagreement(packet_unit, str(relevance)):
                _fail("HUMAN_MACHINE_DISAGREEMENT_REQUIRES_RATIONALE")
            _fail("RECORDED_DECISION_REQUIRES_REVIEWER_METADATA")
        if not _valid_utc_timestamp(unit.get("reviewed_at_utc")):
            _fail("REVIEWED_AT_UTC_INVALID")
    elif metadata_fields != ("", "", ""):
        _fail("INITIAL_REVIEWER_METADATA_NOT_BLANK")

    if unit["workflow_status"] == "UNREVIEWED":
        if has_content:
            _fail("UNREVIEWED_UNIT_CONTAINS_HUMAN_DECISION")
        return

    if relevance == "":
        if not _chemistry_blank(unit) or not _events_blank(unit):
            _fail("CHEMISTRY_OR_EVENTS_RECORDED_BEFORE_RELEVANCE")
        if unit["workflow_status"] not in {"IN_PROGRESS", "DEFERRED"}:
            _fail("BLANK_RELEVANCE_WORKFLOW_STATUS_INVALID")
        return

    if _machine_human_disagreement(packet_unit, str(relevance)) and not str(
        unit.get("review_rationale", "")
    ).strip():
        _fail("HUMAN_MACHINE_DISAGREEMENT_REQUIRES_RATIONALE")

    if relevance == "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK":
        if not _chemistry_blank(unit) or not _events_blank(unit):
            _fail("NOT_RELEVANT_REQUIRES_BLANK_CHEMISTRY_AND_EVENTS")
        if unit["workflow_status"] not in {"IN_PROGRESS", "COMPLETED", "DEFERRED"}:
            _fail("NOT_RELEVANT_WORKFLOW_STATUS_INVALID")
        return

    if relevance == "DEFERRED_INSUFFICIENT_EVIDENCE":
        if unit["workflow_status"] != "DEFERRED":
            _fail("DEFERRED_RELEVANCE_REQUIRES_DEFERRED_WORKFLOW")
        if not _chemistry_blank(unit) or not _events_blank(unit):
            _fail("DEFERRED_RELEVANCE_REQUIRES_BLANK_CHEMISTRY_AND_EVENTS")
        return

    # Relevant units may be saved incrementally while IN_PROGRESS/DEFERRED.
    reactive = unit.get("reactive_atom_confirmation")
    if reactive is not None and not _validate_reactive_confirmation(
        reactive, packet_unit
    ):
        _fail("REACTIVE_ATOM_CONFIRMATION_INVALID")
    family = unit.get("warhead_family_decision")
    if family is not None and not _validate_family_decision(family):
        _fail("WARHEAD_FAMILY_DECISION_INVALID")
    atom_roles_present = bool(unit.get("warhead_atom_ids")) or any(
        bool(value) for value in roles.values()
    )
    atom_roles_valid = False
    if atom_roles_present:
        atom_roles_valid = _validate_atom_and_role_sets(unit, packet_unit)
    event_completion: list[bool] = []
    for event in events:
        event_completion.append(
            _validate_event_decision(
                event, packet_events[str(event["canonical_event_id"])]
            )
            if not (
                event["post_geometry_training_usable"] == ""
                and event["event_training_use_decision"] == ""
                and event["event_exclusion_reason"] == ""
            )
            else False
        )

    if unit["workflow_status"] == "COMPLETED":
        if not (
            type(reactive) is dict
            and reactive.get("status") == "CONFIRMED"
            and _validate_reactive_confirmation(reactive, packet_unit)
        ):
            _fail("RELEVANT_COMPLETION_REQUIRES_CONFIRMED_REACTIVE_ATOM")
        if family is None or not _validate_family_decision(family):
            _fail("RELEVANT_COMPLETION_REQUIRES_WARHEAD_FAMILY_DECISION")
        if not atom_roles_valid:
            _fail("RELEVANT_COMPLETION_REQUIRES_COMPLETE_ATOM_ROLES")
        if not all(event_completion):
            _fail("RELEVANT_COMPLETION_REQUIRES_EVERY_EVENT_DECISION")


def validate_overlay_v1(
    repo_root: Path,
    overlay: Mapping[str, Any],
    *,
    verify_sources: bool = True,
) -> dict[str, object]:
    """Validate IDs, hash bindings, history replay, and every cross-field rule."""

    if verify_sources:
        verify_runtime_gates_v1(repo_root)
        verify_frozen_baseline_facts_v1(repo_root)
    if type(overlay) is not dict or set(overlay) != OVERLAY_FIELDS:
        _fail("OVERLAY_TOP_LEVEL_SCHEMA_INVALID")
    if overlay.get("schema_version") != OVERLAY_SCHEMA_VERSION:
        _fail("OVERLAY_SCHEMA_VERSION_INVALID")
    if overlay.get("overlay_role") != (
        "HUMAN_REVIEW_DECISION_OVERLAY_NOT_PRODUCTION_AUTHORITY"
    ):
        _fail("OVERLAY_ROLE_INVALID")
    if overlay.get("baseline_bindings") != _baseline_bindings():
        _fail("OVERLAY_BASELINE_BINDING_MISMATCH")
    if overlay.get("authority_vocabulary_bindings") != _authority_bindings():
        _fail("OVERLAY_AUTHORITY_BINDING_MISMATCH")
    for field in (
        "production_authority_created",
        "production_materialization_performed",
        "training_materialization_performed",
        "authorized_population_changed",
    ):
        if overlay.get(field) is not False:
            _fail("OVERLAY_SAFETY_FLAG_MUST_REMAIN_FALSE:" + field)

    packet = _packet(repo_root)
    packet_units = _packet_unit_index(packet)
    units = overlay.get("units")
    expected_order = [
        unit["review_unit_id"] for unit in ordered_review_units_v1(packet)
    ]
    if type(units) is not list or [
        unit.get("review_unit_id") for unit in units
    ] != expected_order:
        _fail("OVERLAY_UNIT_ORDER_OR_COVERAGE_INVALID")
    _replay_history_v1(overlay, packet)
    for unit in units:
        unit_id = str(unit["review_unit_id"])
        _validate_unit_cross_fields(unit, packet_units[unit_id])
    return build_progress_v1(overlay, packet)


def _chemistry_complete_for_relevant(
    unit: Mapping[str, Any], packet_unit: Mapping[str, Any]
) -> bool:
    if unit.get("training_domain_relevance_decision") != (
        "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
    ):
        return False
    reactive = unit.get("reactive_atom_confirmation")
    family = unit.get("warhead_family_decision")
    if not (
        type(reactive) is dict
        and reactive.get("status") == "CONFIRMED"
        and _validate_reactive_confirmation(reactive, packet_unit)
        and family is not None
        and _validate_family_decision(family)
    ):
        return False
    try:
        return _validate_atom_and_role_sets(unit, packet_unit)
    except HumanReviewValidationError:
        return False


def build_progress_v1(
    overlay: Mapping[str, Any], packet: Mapping[str, Any]
) -> dict[str, object]:
    units = overlay.get("units")
    if type(units) is not list:
        _fail("PROGRESS_OVERLAY_UNITS_INVALID")
    packet_units = _packet_unit_index(packet)
    workflows = Counter(unit.get("workflow_status") for unit in units)
    relevance = Counter(
        unit.get("training_domain_relevance_decision") for unit in units
    )
    event_use: Counter[str] = Counter()
    geometry: Counter[str] = Counter()
    total_events = 0
    for unit in units:
        for event in unit["events"]:
            total_events += 1
            event_use[str(event["event_training_use_decision"])] += 1
            geometry[str(event["post_geometry_training_usable"])] += 1
    completed_events = sum(event_use[value] for value in EVENT_USE_DECISIONS)
    return {
        "schema_version": "covapie_post_only_human_review_progress_v1",
        "total_units": len(units),
        "reviewed_units": len(units) - workflows["UNREVIEWED"],
        "unreviewed_units": workflows["UNREVIEWED"],
        "in_progress_units": workflows["IN_PROGRESS"],
        "completed_units": workflows["COMPLETED"],
        "deferred_units": workflows["DEFERRED"],
        "relevant_units": relevance["RELEVANT_FOR_COVAPIE_POST_ONLY_V1"],
        "not_relevant_units": relevance[
            "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
        ],
        "total_events": total_events,
        "completed_event_decisions": completed_events,
        "included_events": event_use["INCLUDE"],
        "excluded_events": event_use["EXCLUDE"],
        "deferred_events": event_use["DEFERRED"],
        "unreviewed_events": total_events - completed_events,
        "geometry_usable_events": geometry["YES"],
        "geometry_not_usable_events": geometry["NO"],
        "completed_relevant_chemistry_units": sum(
            _chemistry_complete_for_relevant(
                unit, packet_units[str(unit["review_unit_id"])]
            )
            for unit in units
        ),
        "baseline_population_unchanged": True,
        "production_trainable_population_changed": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
    }


def _guide_bytes(facts: Mapping[str, Any]) -> bytes:
    unit_distribution = facts["unit_priority_distribution"]
    event_distribution = facts["event_priority_distribution"]
    text = f"""# CovaPIE post-only CYS-SG human-review workspace V1

This is an additive human-review execution workspace for the 36 SHA-bound
review units and 123 events in the frozen post-only triage packet. It is not a
production chemistry authority, an authorized-population update, or a training
sample materializer.

## Frozen machine evidence and mutable decisions

The machine evidence remains byte-identical under `{BASELINE_ROOT_RELATIVE}`.
The decision overlay stores only `review_unit_id` / `canonical_event_id`
references plus human-entered fields and an append-only hash-chained history.
Do not edit the frozen packet. Use the record-decision CLI for all overlay
changes so prior values remain auditable.

Initial state: all 36 units are `UNREVIEWED`; every chemistry, relevance,
reviewer, geometry, and event-use decision is blank.

## Review ordering only

Priority is derived only from the frozen unit-level machine-status
distribution. It is not a scientific outcome or approval recommendation.

- P0: {unit_distribution['P0']} units / {event_distribution['P0']} events
- P1: {unit_distribution['P1']} units / {event_distribution['P1']} events
- P2: {unit_distribution['P2']} units / {event_distribution['P2']} events
- P3: {unit_distribution['P3']} units / {event_distribution['P3']} events

Every priority retains all of its units. P0 is not approved; P3 is not
rejected.

## Commands

```bash
python scripts/build_covapie_bulk_post_only_cys_sg_human_review_v1.py
python scripts/show_covapie_bulk_post_only_cys_sg_review_unit_v1.py --next
python scripts/show_covapie_bulk_post_only_cys_sg_review_unit_v1.py --unit-id UNIT_ID
python scripts/record_covapie_bulk_post_only_cys_sg_review_decision_v1.py --help
python scripts/check_covapie_bulk_post_only_cys_sg_human_review_v1.py
```

The build command initializes the workspace only when it is absent, or
idempotently verifies an exact initial empty workspace. **DO NOT use the build
command to reset human decisions.** It has no force-reset mode and refuses to
reinitialize any workspace containing human decisions or history. Missing,
partial, drifted, or internally inconsistent workspaces also fail closed and
must use a separate explicit administrative recovery workflow.

The record CLI supports separate `unit-relevance`, `unit-chemistry`, `event`,
and `unit-status` operations. It verifies every baseline and authority SHA
before writing, writes the overlay atomically, rebuilds progress from the
validated overlay, and never modifies a registry or frozen baseline artifact.
Changing a relevant unit that already has chemistry/event content to
not-relevant or deferred fails unless `unit-relevance --clear-downstream` is
explicitly supplied. That flag appends every actual downstream clear to the
history hash chain before recording the corrected relevance; it never deletes
the earlier decisions or history.

For a relevant completed unit, the exact CCD heavy atoms must be partitioned
into mutually exclusive scaffold/linker/warhead sets. The warhead set must
contain the frozen reactive atom. Event decisions remain independent even
inside a multi-event unit. Radius-2 topology absence does not force exclusion;
it remains unavailable for radius2-dependent auxiliary labels.

Current11 candidate-only family IDs are not accepted as existing approved
authority. A reviewer who cannot map safely to the SHA-bound approved family
must use `{NEW_FAMILY_REVIEW}` and provide a proposal label. The proposal is
not reusable production authority.
"""
    return text.encode("utf-8")


def build_artifacts_v1(repo_root: Path) -> dict[str, bytes]:
    runtime = verify_runtime_gates_v1(repo_root)
    facts = verify_frozen_baseline_facts_v1(repo_root)
    authority = runtime["frozen_evidence_baseline"]["authority_vocabulary"]
    packet = _packet(repo_root)
    overlay = build_initial_overlay_v1(packet)
    validate_overlay_v1(repo_root, overlay, verify_sources=False)
    progress = build_progress_v1(overlay, packet)
    expected_initial_progress = {
        "total_units": 36,
        "reviewed_units": 0,
        "unreviewed_units": 36,
        "in_progress_units": 0,
        "completed_units": 0,
        "deferred_units": 0,
        "relevant_units": 0,
        "not_relevant_units": 0,
        "total_events": 123,
        "completed_event_decisions": 0,
        "included_events": 0,
        "excluded_events": 0,
        "deferred_events": 0,
        "unreviewed_events": 123,
        "geometry_usable_events": 0,
        "geometry_not_usable_events": 0,
        "completed_relevant_chemistry_units": 0,
    }
    for field, expected in expected_initial_progress.items():
        if progress.get(field) != expected:
            _fail("INITIAL_PROGRESS_MISMATCH:" + field)
    return {
        GUIDE: _guide_bytes(facts),
        DECISION_SCHEMA: _json_bytes(build_decision_schema_v1(authority)),
        WORKLIST: _csv_bytes(WORKLIST_HEADER, build_worklist_rows_v1(packet)),
        DECISIONS: _json_bytes(overlay),
        PROGRESS: _json_bytes(progress),
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix="." + path.name + ".atomic-",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def materialize_v1(
    repo_root: Path, output_root: Path | None = None
) -> dict[str, object]:
    """Initialize an absent workspace or verify an exact empty one.

    This function deliberately has no reset or force path. Once any human
    decision/history exists, reinitialization fails before writing any byte.
    """

    if output_root is None:
        output_root = repo_root / OUTPUT_ROOT_RELATIVE
    artifacts = build_artifacts_v1(repo_root)
    file_metadata = {
        filename: {"sha256": _sha(payload), "bytes": len(payload)}
        for filename, payload in artifacts.items()
    }
    if output_root.exists():
        if not output_root.is_dir():
            _fail("WORKSPACE_OUTPUT_PATH_EXISTS_BUT_IS_NOT_DIRECTORY")
        entries = list(output_root.iterdir())
        if {entry.name for entry in entries} != set(OUTPUT_FILENAMES) or not all(
            entry.is_file() for entry in entries
        ):
            _fail("WORKSPACE_PARTIAL_OR_FILE_SET_MISMATCH")
        for filename in STATIC_OUTPUT_FILENAMES:
            try:
                observed_static = (output_root / filename).read_bytes()
            except OSError as error:
                raise HumanReviewValidationError(
                    "WORKSPACE_STATIC_ARTIFACT_READ_FAILED:" + filename
                ) from error
            if observed_static != artifacts[filename]:
                _fail("WORKSPACE_STATIC_ARTIFACT_DRIFT_REFUSE_REINITIALIZATION")

        try:
            decisions_payload = (output_root / DECISIONS).read_bytes()
            progress_payload = (output_root / PROGRESS).read_bytes()
        except OSError as error:
            raise HumanReviewValidationError(
                "WORKSPACE_MUTABLE_ARTIFACT_READ_FAILED"
            ) from error
        overlay = _read_json(output_root / DECISIONS)
        packet = _packet(repo_root)
        derived_progress = validate_overlay_v1(
            repo_root, overlay, verify_sources=False
        )
        if progress_payload != _json_bytes(derived_progress):
            _fail("WORKSPACE_PROGRESS_NOT_EXACT_DERIVATION_OF_OVERLAY")
        initial_overlay = build_initial_overlay_v1(packet)
        if overlay != initial_overlay or overlay.get("decision_history") != []:
            _fail(
                "WORKSPACE_ALREADY_CONTAINS_HUMAN_DECISIONS_"
                "REFUSE_REINITIALIZATION"
            )
        if decisions_payload != artifacts[DECISIONS]:
            _fail("WORKSPACE_INITIAL_DECISION_BYTES_DRIFT")
        if progress_payload != artifacts[PROGRESS]:
            _fail("WORKSPACE_INITIAL_PROGRESS_BYTES_DRIFT")
        return {"already_initialized": True, "files": file_metadata}

    for filename, payload in artifacts.items():
        _atomic_write(output_root / filename, payload)
    return {"already_initialized": False, "files": file_metadata}


def verify_deterministic_replay_v1(repo_root: Path) -> dict[str, str]:
    first = build_artifacts_v1(repo_root)
    second = build_artifacts_v1(repo_root)
    if first != second:
        _fail("DETERMINISTIC_REPLAY_MISMATCH")
    return {filename: _sha(payload) for filename, payload in first.items()}


def check_workspace_v1(
    repo_root: Path,
    output_root: Path | None = None,
    *,
    require_initial: bool = False,
) -> dict[str, object]:
    if output_root is None:
        output_root = repo_root / OUTPUT_ROOT_RELATIVE
    runtime = verify_runtime_gates_v1(repo_root)
    facts = verify_frozen_baseline_facts_v1(repo_root)
    authority = runtime["frozen_evidence_baseline"]["authority_vocabulary"]
    packet = _packet(repo_root)
    expected_static = {
        GUIDE: _guide_bytes(facts),
        DECISION_SCHEMA: _json_bytes(build_decision_schema_v1(authority)),
        WORKLIST: _csv_bytes(WORKLIST_HEADER, build_worklist_rows_v1(packet)),
    }
    for filename, expected in expected_static.items():
        try:
            observed = (output_root / filename).read_bytes()
        except OSError as error:
            raise HumanReviewValidationError(
                "WORKSPACE_STATIC_ARTIFACT_READ_FAILED:" + filename
            ) from error
        if observed != expected:
            _fail("WORKSPACE_STATIC_ARTIFACT_MISMATCH:" + filename)
    overlay = _read_json(output_root / DECISIONS)
    progress = validate_overlay_v1(repo_root, overlay, verify_sources=False)
    if require_initial and overlay != build_initial_overlay_v1(packet):
        _fail("WORKSPACE_NOT_IN_INITIAL_EMPTY_DECISION_STATE")
    try:
        progress_payload = (output_root / PROGRESS).read_bytes()
    except OSError as error:
        raise HumanReviewValidationError("WORKSPACE_PROGRESS_READ_FAILED") from error
    if progress_payload != _json_bytes(progress):
        _fail("WORKSPACE_PROGRESS_NOT_EXACT_DERIVATION_OF_OVERLAY")
    return {
        "schema_version": SCHEMA_VERSION,
        "workspace_valid": True,
        "initial_state_required": require_initial,
        "review_unit_count": facts["review_unit_count"],
        "event_count": facts["event_count"],
        "progress": progress,
        "frozen_baseline_modified": False,
        "production_authority_created": False,
        "production_materialization_performed": False,
        "training_materialization_performed": False,
    }


def _canonical_atom_argument(
    value: Sequence[str], *, allow_empty: bool = False
) -> list[str]:
    atoms = list(value)
    if (not atoms and not allow_empty) or any(
        type(atom) is not str or not atom for atom in atoms
    ):
        _fail("ATOM_ID_ARGUMENT_INVALID")
    if len(set(atoms)) != len(atoms):
        _fail("ATOM_ID_ARGUMENT_DUPLICATE")
    return sorted(atoms)


def _append_changes_v1(
    overlay: dict[str, Any],
    changes: Sequence[tuple[str, str, str, str, object]],
    *,
    reviewer_id: str,
    timestamp_utc: str,
) -> None:
    if type(reviewer_id) is not str or not reviewer_id.strip():
        _fail("RECORD_REVIEWER_ID_REQUIRED")
    if not _valid_utc_timestamp(timestamp_utc):
        _fail("RECORD_TIMESTAMP_UTC_INVALID")
    history = overlay.get("decision_history")
    if type(history) is not list:
        _fail("RECORD_HISTORY_INVALID")
    previous = str(history[-1]["entry_sha256"]) if history else ""
    for target_kind, unit_id, event_id, field, new_value in changes:
        probe = {
            "target_kind": target_kind,
            "review_unit_id": unit_id,
            "canonical_event_id": event_id,
            "field": field,
        }
        target = _history_target(overlay, probe)
        old_value = deepcopy(target[field])
        if old_value == new_value:
            continue
        entry: dict[str, Any] = {
            "sequence": len(history) + 1,
            "timestamp_utc": timestamp_utc,
            "reviewer_id": reviewer_id,
            "target_kind": target_kind,
            "review_unit_id": unit_id,
            "canonical_event_id": event_id,
            "field": field,
            "old_value": old_value,
            "new_value": deepcopy(new_value),
            "previous_entry_sha256": previous,
            "entry_sha256": "",
        }
        entry["entry_sha256"] = _history_entry_sha256(entry)
        target[field] = deepcopy(new_value)
        history.append(entry)
        previous = str(entry["entry_sha256"])


def _record_and_write_v1(
    repo_root: Path,
    output_root: Path,
    changes: (
        Sequence[tuple[str, str, str, str, object]]
        | Callable[
            [dict[str, Any]], Sequence[tuple[str, str, str, str, object]]
        ]
    ),
    *,
    reviewer_id: str,
    timestamp_utc: str,
) -> dict[str, object]:
    # Every source SHA is rechecked before the mutable overlay is opened.
    verify_runtime_gates_v1(repo_root)
    verify_frozen_baseline_facts_v1(repo_root)
    overlay_path = output_root / DECISIONS
    overlay = _read_json(overlay_path)
    validate_overlay_v1(repo_root, overlay, verify_sources=False)
    updated = deepcopy(overlay)
    resolved_changes = changes(updated) if callable(changes) else changes
    _append_changes_v1(
        updated,
        resolved_changes,
        reviewer_id=reviewer_id,
        timestamp_utc=timestamp_utc,
    )
    if updated == overlay:
        _fail("RECORD_OPERATION_CONTAINS_NO_CHANGE")
    progress = validate_overlay_v1(repo_root, updated, verify_sources=False)
    # The authority-bearing overlay is replaced atomically. Progress is a
    # deterministic, non-authoritative projection and can always be rebuilt.
    _atomic_write(overlay_path, _json_bytes(updated))
    _atomic_write(output_root / PROGRESS, _json_bytes(progress))
    reloaded = _read_json(overlay_path)
    validate_overlay_v1(repo_root, reloaded, verify_sources=False)
    return {
        "overlay_sha256": _sha(_json_bytes(reloaded)),
        "history_entry_count": len(reloaded["decision_history"]),
        "progress": progress,
        "frozen_baseline_modified": False,
        "registry_modified": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
    }


def _downstream_clear_changes_v1(
    unit: Mapping[str, Any]
) -> list[tuple[str, str, str, str, object]]:
    unit_id = str(unit["review_unit_id"])
    changes: list[tuple[str, str, str, str, object]] = [
        ("UNIT", unit_id, "", "reactive_atom_confirmation", None),
        ("UNIT", unit_id, "", "warhead_family_decision", None),
        ("UNIT", unit_id, "", "warhead_atom_ids", []),
        (
            "UNIT",
            unit_id,
            "",
            "roles",
            {
                "scaffold_atom_ids": [],
                "linker_atom_ids": [],
                "warhead_atom_ids": [],
            },
        ),
    ]
    for event in unit["events"]:
        event_id = str(event["canonical_event_id"])
        changes.extend(
            (
                (
                    "EVENT",
                    unit_id,
                    event_id,
                    "post_geometry_training_usable",
                    "",
                ),
                (
                    "EVENT",
                    unit_id,
                    event_id,
                    "event_training_use_decision",
                    "",
                ),
                (
                    "EVENT",
                    unit_id,
                    event_id,
                    "event_exclusion_reason",
                    "",
                ),
            )
        )
    return changes


def record_unit_relevance_v1(
    repo_root: Path,
    output_root: Path,
    *,
    unit_id: str,
    relevance_decision: str,
    workflow_status: str,
    reviewer_id: str,
    reviewed_at_utc: str,
    review_rationale: str,
    clear_downstream: bool = False,
) -> dict[str, object]:
    if relevance_decision not in RELEVANCE_DECISIONS:
        _fail("RECORD_RELEVANCE_DECISION_INVALID")
    if workflow_status not in WORKFLOW_STATUSES or workflow_status == "UNREVIEWED":
        _fail("RECORD_WORKFLOW_STATUS_INVALID")
    if relevance_decision == "DEFERRED_INSUFFICIENT_EVIDENCE" and (
        workflow_status != "DEFERRED"
    ):
        _fail("RECORD_DEFERRED_RELEVANCE_REQUIRES_DEFERRED_STATUS")
    if type(review_rationale) is not str or not review_rationale.strip():
        _fail("RECORD_REVIEW_RATIONALE_REQUIRED")
    if type(clear_downstream) is not bool:
        _fail("RECORD_CLEAR_DOWNSTREAM_FLAG_INVALID")
    if clear_downstream and relevance_decision == (
        "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
    ):
        _fail("CLEAR_DOWNSTREAM_NOT_ALLOWED_FOR_RELEVANT_DECISION")

    def changes(updated: dict[str, Any]) -> list[tuple[str, str, str, str, object]]:
        unit = _unit_by_id(updated, unit_id)
        downstream_exists = not _chemistry_blank(unit) or not _events_blank(unit)
        downward_target = relevance_decision in {
            "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
            "DEFERRED_INSUFFICIENT_EVIDENCE",
        }
        if downward_target and downstream_exists and not clear_downstream:
            _fail("DOWNSTREAM_DECISIONS_EXIST_EXPLICIT_CLEAR_REQUIRED")
        result = (
            _downstream_clear_changes_v1(unit)
            if downward_target and clear_downstream
            else []
        )
        result.extend(
            (
                (
                    "UNIT",
                    unit_id,
                    "",
                    "training_domain_relevance_decision",
                    relevance_decision,
                ),
                ("UNIT", unit_id, "", "workflow_status", workflow_status),
                ("UNIT", unit_id, "", "reviewer_id", reviewer_id),
                ("UNIT", unit_id, "", "reviewed_at_utc", reviewed_at_utc),
                ("UNIT", unit_id, "", "review_rationale", review_rationale),
            )
        )
        return result

    return _record_and_write_v1(
        repo_root,
        output_root,
        changes,
        reviewer_id=reviewer_id,
        timestamp_utc=reviewed_at_utc,
    )


def record_unit_chemistry_v1(
    repo_root: Path,
    output_root: Path,
    *,
    unit_id: str,
    reactive_atom_status: str,
    confirmed_atom_id: str,
    family_decision: str,
    canonical_reaction_family_id: str,
    proposed_warhead_family_label: str,
    warhead_atom_ids: Sequence[str],
    scaffold_atom_ids: Sequence[str],
    linker_atom_ids: Sequence[str],
    warhead_role_atom_ids: Sequence[str],
    reviewer_id: str,
    reviewed_at_utc: str,
    review_rationale: str,
) -> dict[str, object]:
    if reactive_atom_status not in REACTIVE_ATOM_STATUSES:
        _fail("RECORD_REACTIVE_ATOM_STATUS_INVALID")
    if reactive_atom_status != "CONFIRMED" and confirmed_atom_id != "":
        _fail("RECORD_NONCONFIRMED_ATOM_ID_MUST_BE_BLANK")
    if family_decision not in {EXISTING_FAMILY, NEW_FAMILY_REVIEW}:
        _fail("RECORD_FAMILY_DECISION_INVALID")
    family = {
        "decision": family_decision,
        "canonical_reaction_family_id": canonical_reaction_family_id,
        "proposed_warhead_family_label": proposed_warhead_family_label,
    }
    if not _validate_family_decision(family):
        _fail("RECORD_FAMILY_DECISION_FIELDS_INVALID")
    if type(review_rationale) is not str or not review_rationale.strip():
        _fail("RECORD_REVIEW_RATIONALE_REQUIRED")
    roles = {
        "scaffold_atom_ids": _canonical_atom_argument(
            scaffold_atom_ids, allow_empty=True
        ),
        "linker_atom_ids": _canonical_atom_argument(
            linker_atom_ids, allow_empty=True
        ),
        "warhead_atom_ids": _canonical_atom_argument(warhead_role_atom_ids),
    }
    changes = (
        ("UNIT", unit_id, "", "reviewer_id", reviewer_id),
        ("UNIT", unit_id, "", "reviewed_at_utc", reviewed_at_utc),
        ("UNIT", unit_id, "", "review_rationale", review_rationale),
        (
            "UNIT",
            unit_id,
            "",
            "reactive_atom_confirmation",
            {
                "status": reactive_atom_status,
                "confirmed_atom_id": confirmed_atom_id,
            },
        ),
        ("UNIT", unit_id, "", "warhead_family_decision", family),
        (
            "UNIT",
            unit_id,
            "",
            "warhead_atom_ids",
            _canonical_atom_argument(warhead_atom_ids),
        ),
        ("UNIT", unit_id, "", "roles", roles),
    )
    return _record_and_write_v1(
        repo_root,
        output_root,
        changes,
        reviewer_id=reviewer_id,
        timestamp_utc=reviewed_at_utc,
    )


def record_event_decision_v1(
    repo_root: Path,
    output_root: Path,
    *,
    unit_id: str,
    event_id: str,
    post_geometry_training_usable: str,
    event_training_use_decision: str,
    event_exclusion_reason: str,
    reviewer_id: str,
    reviewed_at_utc: str,
    review_rationale: str,
) -> dict[str, object]:
    if post_geometry_training_usable not in GEOMETRY_USABILITY:
        _fail("RECORD_GEOMETRY_USABILITY_INVALID")
    if event_training_use_decision not in EVENT_USE_DECISIONS:
        _fail("RECORD_EVENT_USE_DECISION_INVALID")
    if type(review_rationale) is not str or not review_rationale.strip():
        _fail("RECORD_REVIEW_RATIONALE_REQUIRED")
    changes = (
        ("UNIT", unit_id, "", "reviewer_id", reviewer_id),
        ("UNIT", unit_id, "", "reviewed_at_utc", reviewed_at_utc),
        ("UNIT", unit_id, "", "review_rationale", review_rationale),
        (
            "EVENT",
            unit_id,
            event_id,
            "post_geometry_training_usable",
            post_geometry_training_usable,
        ),
        (
            "EVENT",
            unit_id,
            event_id,
            "event_training_use_decision",
            event_training_use_decision,
        ),
        (
            "EVENT",
            unit_id,
            event_id,
            "event_exclusion_reason",
            event_exclusion_reason,
        ),
    )
    return _record_and_write_v1(
        repo_root,
        output_root,
        changes,
        reviewer_id=reviewer_id,
        timestamp_utc=reviewed_at_utc,
    )


def record_unit_status_v1(
    repo_root: Path,
    output_root: Path,
    *,
    unit_id: str,
    workflow_status: str,
    reviewer_id: str,
    reviewed_at_utc: str,
    review_rationale: str,
) -> dict[str, object]:
    if workflow_status not in WORKFLOW_STATUSES or workflow_status == "UNREVIEWED":
        _fail("RECORD_WORKFLOW_STATUS_INVALID")
    if type(review_rationale) is not str or not review_rationale.strip():
        _fail("RECORD_REVIEW_RATIONALE_REQUIRED")
    changes = (
        ("UNIT", unit_id, "", "reviewer_id", reviewer_id),
        ("UNIT", unit_id, "", "reviewed_at_utc", reviewed_at_utc),
        ("UNIT", unit_id, "", "review_rationale", review_rationale),
        ("UNIT", unit_id, "", "workflow_status", workflow_status),
    )
    return _record_and_write_v1(
        repo_root,
        output_root,
        changes,
        reviewer_id=reviewer_id,
        timestamp_utc=reviewed_at_utc,
    )


def next_review_unit_id_v1(
    repo_root: Path, output_root: Path | None = None
) -> str:
    if output_root is None:
        output_root = repo_root / OUTPUT_ROOT_RELATIVE
    overlay = _read_json(output_root / DECISIONS)
    validate_overlay_v1(repo_root, overlay)
    for unit in overlay["units"]:
        if unit["workflow_status"] == "UNREVIEWED":
            return str(unit["review_unit_id"])
    _fail("NO_UNREVIEWED_UNIT_REMAINS")


def _coordinate_summary(unit: Mapping[str, Any]) -> str:
    coordinates = unit["machine_chemistry_evidence"].get(
        "representative_observed_ligand_atom_coordinates"
    )
    if type(coordinates) is not list or not coordinates:
        return "unavailable"
    xyz = [(float(atom["x"]), float(atom["y"]), float(atom["z"])) for atom in coordinates]
    centroid = tuple(sum(point[i] for point in xyz) / len(xyz) for i in range(3))
    minimum = tuple(min(point[i] for point in xyz) for i in range(3))
    maximum = tuple(max(point[i] for point in xyz) for i in range(3))
    return (
        f"count={len(xyz)} centroid=({centroid[0]:.3f},{centroid[1]:.3f},"
        f"{centroid[2]:.3f}) bounds=({minimum[0]:.3f},{minimum[1]:.3f},"
        f"{minimum[2]:.3f})..({maximum[0]:.3f},{maximum[1]:.3f},"
        f"{maximum[2]:.3f})"
    )


def render_review_card_v1(
    repo_root: Path,
    unit_id: str,
    output_root: Path | None = None,
) -> str:
    if output_root is None:
        output_root = repo_root / OUTPUT_ROOT_RELATIVE
    packet = _packet(repo_root)
    overlay = _read_json(output_root / DECISIONS)
    validate_overlay_v1(repo_root, overlay)
    packet_units = _packet_unit_index(packet)
    if unit_id not in packet_units:
        _fail("SHOW_UNIT_ID_UNKNOWN")
    machine = packet_units[unit_id]
    decision = _unit_by_id(overlay, unit_id)
    worklist = build_worklist_rows_v1(packet)
    work = next(row for row in worklist if row["review_unit_id"] == unit_id)
    chemistry = machine["machine_chemistry_evidence"]
    reactive = chemistry["reactive_atom_evidence"]
    atoms = ", ".join(
        f"{atom['atom_id']}:{atom['element']}"
        for atom in chemistry["ccd_heavy_atom_inventory"]
    )
    neighbors = ", ".join(
        f"{item['neighbor_atom']['atom_id']}:{item['neighbor_atom']['element']}"
        f"({item['bond_order']})"
        for item in reactive["reactive_atom_immediate_neighbors"]
    )
    bonds = ", ".join(
        f"{bond['atom_id_1']}-{bond['atom_id_2']}({bond['bond_order']})"
        for bond in chemistry["ccd_bond_inventory"]
    )
    lines = [
        "MACHINE TRIAGE ONLY — SUPPORTING EVIDENCE, NOT HUMAN TRUTH",
        f"review_order={work['review_order']} priority={work['priority']}",
        f"review_unit_id={unit_id}",
        f"event_count={machine['event_count']}",
        f"pdb_ids={_json_cell(machine['pdb_ids'])}",
        f"ligand_component_ids={_json_cell(machine['ligand_component_ids'])}",
        "machine_relevance_status_distribution="
        + _json_cell(_machine_distribution(machine)),
        f"source_annotations_SUPPORTING_ONLY={_json_cell(machine['source_annotations'])}",
        f"reactive_atom={machine['ligand_reactive_atom']}",
        f"reactive_atom_neighbors={neighbors}",
        f"ccd_heavy_atoms={atoms}",
        f"ccd_bond_graph={bonds}",
        f"representative_coordinates={_coordinate_summary(machine)}",
        f"post_distance_range_angstrom={machine['post_distance_min_angstrom']:.5f}.."
        f"{machine['post_distance_max_angstrom']:.5f}",
        f"altloc_state={machine['altloc_status']}",
        f"topology_status={_topology_summary(machine)}",
        f"predicted_splits={_json_cell(machine['predicted_splits'])}",
        "underlying_events:",
    ]
    decision_events = {
        event["canonical_event_id"]: event for event in decision["events"]
    }
    for event in machine["events_for_review"]:
        event_id = event["canonical_event_id"]
        current = decision_events[event_id]
        lines.append(
            "  - "
            f"event_id={event_id} target_cys={event['target_cys_identity']} "
            f"post_distance={event['post_distance_angstrom']:.5f} "
            f"altloc=protein:{event['protein_altloc'] or '-'}"
            f"/ligand:{event['ligand_altloc'] or '-'} "
            f"topology={geometry_auxiliary_label_availability_v1(event)} "
            f"machine_status={event['training_domain_machine_triage_status']} "
            f"human_geometry={current['post_geometry_training_usable'] or '<blank>'} "
            f"human_use={current['event_training_use_decision'] or '<blank>'}"
        )
    lines.extend(
        (
            "current_overlay:",
            f"  workflow_status={decision['workflow_status']}",
            "  relevance_decision="
            + (decision["training_domain_relevance_decision"] or "<blank>"),
            "  chemistry_decision_populated="
            + ("true" if not _chemistry_blank(decision) else "false"),
            f"  history_entries={len(overlay['decision_history'])}",
        )
    )
    return "\n".join(lines) + "\n"
