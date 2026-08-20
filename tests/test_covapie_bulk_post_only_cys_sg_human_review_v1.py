from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import inspect
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from covalent_ext import covapie_bulk_post_only_cys_sg_human_review_v1 as review


REPO_ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-08-20T12:00:00Z"
REVIEWER = "test-reviewer"
RATIONALE = "Human test rationale recorded for this bounded validation case."
STAMP_2 = "2026-08-20T13:00:00Z"
STAMP_3 = "2026-08-20T14:00:00Z"
STAMP_4 = "2026-08-20T15:00:00Z"


@pytest.fixture(scope="module")
def packet() -> dict:
    return json.loads(
        (REPO_ROOT / review.BASELINE_ROOT_RELATIVE / review.REVIEW_PACKET).read_text()
    )


@pytest.fixture()
def overlay(packet: dict) -> dict:
    return review.build_initial_overlay_v1(packet)


def _unit(packet: dict, *, multi: bool = False, topology_missing: bool = False) -> dict:
    for unit in review.ordered_review_units_v1(packet):
        events = unit["events_for_review"]
        if multi and len(events) < 2:
            continue
        if topology_missing and all(
            review.geometry_auxiliary_label_availability_v1(event)
            != "UNAVAILABLE_FOR_RADIUS2_DEPENDENT_LABELS"
            for event in events
        ):
            continue
        return unit
    raise AssertionError("required packet unit not found")


def _append(overlay: dict, changes: list[tuple[str, str, str, str, object]]) -> None:
    review._append_changes_v1(  # noqa: SLF001 - tests exercise history contract
        overlay, changes, reviewer_id=REVIEWER, timestamp_utc=STAMP
    )


def _metadata_changes(unit_id: str) -> list[tuple[str, str, str, str, object]]:
    return [
        ("UNIT", unit_id, "", "reviewer_id", REVIEWER),
        ("UNIT", unit_id, "", "reviewed_at_utc", STAMP),
        ("UNIT", unit_id, "", "review_rationale", RATIONALE),
    ]


def _valid_atom_roles(packet_unit: dict) -> tuple[list[str], dict]:
    heavy = sorted(
        atom["atom_id"]
        for atom in packet_unit["machine_chemistry_evidence"][
            "ccd_heavy_atom_inventory"
        ]
    )
    reactive = packet_unit["ligand_reactive_atom"]
    warhead = [reactive]
    roles = {
        "scaffold_atom_ids": [atom for atom in heavy if atom != reactive],
        "linker_atom_ids": [],
        "warhead_atom_ids": warhead,
    }
    return warhead, roles


def _relevant_overlay(packet: dict, *, multi: bool = False) -> tuple[dict, dict]:
    packet_unit = _unit(packet, multi=multi)
    unit_id = packet_unit["review_unit_id"]
    result = review.build_initial_overlay_v1(packet)
    warhead, roles = _valid_atom_roles(packet_unit)
    _append(
        result,
        _metadata_changes(unit_id)
        + [
            (
                "UNIT",
                unit_id,
                "",
                "training_domain_relevance_decision",
                "RELEVANT_FOR_COVAPIE_POST_ONLY_V1",
            ),
            (
                "UNIT",
                unit_id,
                "",
                "reactive_atom_confirmation",
                {
                    "status": "CONFIRMED",
                    "confirmed_atom_id": packet_unit["ligand_reactive_atom"],
                },
            ),
            (
                "UNIT",
                unit_id,
                "",
                "warhead_family_decision",
                {
                    "decision": review.NEW_FAMILY_REVIEW,
                    "canonical_reaction_family_id": "",
                    "proposed_warhead_family_label": "TEST_PROPOSAL_NOT_AUTHORITY",
                },
            ),
            ("UNIT", unit_id, "", "warhead_atom_ids", warhead),
            ("UNIT", unit_id, "", "roles", roles),
            ("UNIT", unit_id, "", "workflow_status", "IN_PROGRESS"),
        ],
    )
    review.validate_overlay_v1(REPO_ROOT, result, verify_sources=False)
    return result, packet_unit


def _event_changes(
    unit_id: str,
    event_id: str,
    *,
    geometry: str,
    use: str,
    reason: str = "",
) -> list[tuple[str, str, str, str, object]]:
    return [
        ("EVENT", unit_id, event_id, "post_geometry_training_usable", geometry),
        ("EVENT", unit_id, event_id, "event_training_use_decision", use),
        ("EVENT", unit_id, event_id, "event_exclusion_reason", reason),
    ]


def _mock_execution_git(
    monkeypatch: pytest.MonkeyPatch,
    *,
    branch: str = "main",
    head: str,
    origin: str,
    divergence: str = "0\t0",
    merge_base: str = review.EVIDENCE_BASELINE_COMMIT,
) -> None:
    def fake_git(_repo_root: Path, *arguments: str) -> str:
        if arguments == ("branch", "--show-current"):
            return branch
        if arguments == ("rev-parse", "HEAD"):
            return head
        if arguments == ("rev-parse", "origin/main"):
            return origin
        if arguments == (
            "rev-parse",
            review.EVIDENCE_BASELINE_COMMIT + "^{commit}",
        ):
            return review.EVIDENCE_BASELINE_COMMIT
        if arguments == (
            "show",
            "-s",
            "--format=%s",
            review.EVIDENCE_BASELINE_COMMIT,
        ):
            return review.BASELINE_SUBJECT
        if arguments == (
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...origin/main",
        ):
            return divergence
        if arguments in {
            ("merge-base", review.EVIDENCE_BASELINE_COMMIT, head),
            ("merge-base", review.EVIDENCE_BASELINE_COMMIT, origin),
        }:
            return merge_base
        raise AssertionError("unexpected git query: " + repr(arguments))

    monkeypatch.setattr(review, "_git", fake_git)


def _prepare_relevant_workspace_with_downstream(
    tmp_path: Path, packet: dict
) -> tuple[Path, dict, str]:
    output = tmp_path / "workspace"
    review.materialize_v1(REPO_ROOT, output)
    packet_unit = _unit(packet)
    unit_id = packet_unit["review_unit_id"]
    event_id = packet_unit["events_for_review"][0]["canonical_event_id"]
    review.record_unit_relevance_v1(
        REPO_ROOT,
        output,
        unit_id=unit_id,
        relevance_decision="RELEVANT_FOR_COVAPIE_POST_ONLY_V1",
        workflow_status="IN_PROGRESS",
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP,
        review_rationale=RATIONALE,
    )
    warhead, roles = _valid_atom_roles(packet_unit)
    review.record_unit_chemistry_v1(
        REPO_ROOT,
        output,
        unit_id=unit_id,
        reactive_atom_status="CONFIRMED",
        confirmed_atom_id=packet_unit["ligand_reactive_atom"],
        family_decision=review.NEW_FAMILY_REVIEW,
        canonical_reaction_family_id="",
        proposed_warhead_family_label="TEST_CORRECTION_PROPOSAL_NOT_AUTHORITY",
        warhead_atom_ids=warhead,
        scaffold_atom_ids=roles["scaffold_atom_ids"],
        linker_atom_ids=roles["linker_atom_ids"],
        warhead_role_atom_ids=roles["warhead_atom_ids"],
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP_2,
        review_rationale=RATIONALE + " Chemistry recorded.",
    )
    review.record_event_decision_v1(
        REPO_ROOT,
        output,
        unit_id=unit_id,
        event_id=event_id,
        post_geometry_training_usable="YES",
        event_training_use_decision="INCLUDE",
        event_exclusion_reason="",
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP_3,
        review_rationale=RATIONALE + " Event recorded.",
    )
    return output, packet_unit, event_id


def test_current_repository_state_descends_from_evidence_baseline() -> None:
    state = review.verify_execution_repository_state_v1(REPO_ROOT)
    assert state["branch"] == "main"
    assert state["head"] == state["origin_main"]
    assert (state["ahead"], state["behind"]) == (0, 0)
    assert state["evidence_baseline_commit"] == review.EVIDENCE_BASELINE_COMMIT
    assert state["evidence_baseline_is_head_ancestor"] is True
    assert state["evidence_baseline_is_origin_main_ancestor"] is True


def test_simulated_published_descendant_execution_state_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    successor = "9" * 40
    _mock_execution_git(monkeypatch, head=successor, origin=successor)
    state = review.verify_execution_repository_state_v1(REPO_ROOT)
    assert state["head"] == successor
    assert state["origin_main"] == successor
    assert state["evidence_baseline_commit"] == review.EVIDENCE_BASELINE_COMMIT


def test_simulated_published_descendant_checker_show_and_record_operational(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, packet: dict
) -> None:
    successor = "9" * 40
    _mock_execution_git(monkeypatch, head=successor, origin=successor)
    output = tmp_path / "workspace"
    initialized = review.materialize_v1(REPO_ROOT, output)
    assert initialized["already_initialized"] is False
    assert review.check_workspace_v1(REPO_ROOT, output, require_initial=True)[
        "workspace_valid"
    ] is True
    unit_id = review.next_review_unit_id_v1(REPO_ROOT, output)
    assert unit_id == "COVAPIE_BULK_REVIEW_UNIT_07BD3B72031BD7CC"
    assert "MACHINE TRIAGE ONLY" in review.render_review_card_v1(
        REPO_ROOT, unit_id, output
    )
    review.record_unit_relevance_v1(
        REPO_ROOT,
        output,
        unit_id=unit_id,
        relevance_decision="DEFERRED_INSUFFICIENT_EVIDENCE",
        workflow_status="DEFERRED",
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP,
        review_rationale=RATIONALE,
    )
    assert review.check_workspace_v1(REPO_ROOT, output)["progress"][
        "deferred_units"
    ] == 1


def test_evidence_baseline_not_ancestor_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    successor = "8" * 40
    _mock_execution_git(
        monkeypatch,
        head=successor,
        origin=successor,
        merge_base="7" * 40,
    )
    with pytest.raises(review.HumanReviewValidationError, match="NOT_ANCESTOR"):
        review.verify_execution_repository_state_v1(REPO_ROOT)


def test_head_origin_divergence_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_execution_git(monkeypatch, head="8" * 40, origin="9" * 40)
    with pytest.raises(review.HumanReviewValidationError, match="HEAD_ORIGIN"):
        review.verify_execution_repository_state_v1(REPO_ROOT)


@pytest.mark.parametrize("branch", ["feature/review", ""])
def test_wrong_branch_or_detached_head_rejected(
    monkeypatch: pytest.MonkeyPatch, branch: str
) -> None:
    successor = "9" * 40
    _mock_execution_git(
        monkeypatch, branch=branch, head=successor, origin=successor
    )
    with pytest.raises(
        review.HumanReviewValidationError, match="WRONG_BRANCH|DETACHED_HEAD"
    ):
        review.verify_execution_repository_state_v1(REPO_ROOT)


def test_frozen_evidence_drift_rejected_even_with_valid_execution_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    successor = "9" * 40
    _mock_execution_git(monkeypatch, head=successor, origin=successor)
    target = REPO_ROOT / review.BASELINE_ROOT_RELATIVE / review.REVIEW_PACKET
    original_read_bytes = Path.read_bytes

    def drift_one_file(path: Path) -> bytes:
        payload = original_read_bytes(path)
        return payload + b"drift" if path == target else payload

    monkeypatch.setattr(Path, "read_bytes", drift_one_file)
    with pytest.raises(review.HumanReviewValidationError, match="SHA256_MISMATCH"):
        review.verify_runtime_gates_v1(REPO_ROOT)


def test_six_frozen_artifact_sha_bindings_and_real_facts() -> None:
    facts = review.verify_frozen_baseline_facts_v1(REPO_ROOT)
    assert facts["artifact_sha256"] == review.BASELINE_ARTIFACT_SHA256
    assert facts["review_unit_count"] == 36
    assert facts["event_count"] == 123
    assert facts["multi_event_review_unit_count"] == 25
    assert facts["event_count_inside_multi_event_units"] == 112
    assert facts["radius2_topology_count"] == 115
    assert facts["post_geometry_mechanically_derivable_count"] == 115


def test_36_units_and_123_events_exactly_once(packet: dict) -> None:
    units = review.ordered_review_units_v1(packet)
    unit_ids = [unit["review_unit_id"] for unit in units]
    event_ids = [
        event["canonical_event_id"]
        for unit in units
        for event in unit["events_for_review"]
    ]
    assert len(unit_ids) == len(set(unit_ids)) == 36
    assert len(event_ids) == len(set(event_ids)) == 123


def test_worklist_deterministic_priority_and_first_ten(packet: dict) -> None:
    rows = review.build_worklist_rows_v1(packet)
    assert [row["review_order"] for row in rows] == list(range(1, 37))
    assert [row["priority"] for row in rows].count("P0") == 18
    assert [row["priority"] for row in rows].count("P1") == 4
    assert [row["priority"] for row in rows].count("P2") == 10
    assert [row["priority"] for row in rows].count("P3") == 4
    assert [row["review_unit_id"] for row in rows[:10]] == [
        "COVAPIE_BULK_REVIEW_UNIT_07BD3B72031BD7CC",
        "COVAPIE_BULK_REVIEW_UNIT_164B59C21643F70A",
        "COVAPIE_BULK_REVIEW_UNIT_53F40FB515D7D1DF",
        "COVAPIE_BULK_REVIEW_UNIT_5662273FCD38234C",
        "COVAPIE_BULK_REVIEW_UNIT_59100AAB78E957D9",
        "COVAPIE_BULK_REVIEW_UNIT_5FFACB7F4984AD92",
        "COVAPIE_BULK_REVIEW_UNIT_6F93A0730570186F",
        "COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295",
        "COVAPIE_BULK_REVIEW_UNIT_AAB4DCC7D3073222",
        "COVAPIE_BULK_REVIEW_UNIT_B4F514DC9BD2350E",
    ]
    assert review.build_worklist_rows_v1(packet) == rows


def test_all_initial_human_fields_blank_and_progress_zero(packet: dict, overlay: dict) -> None:
    progress = review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)
    assert not overlay["decision_history"]
    assert all(unit["workflow_status"] == "UNREVIEWED" for unit in overlay["units"])
    assert all(not review._unit_has_human_content(unit) for unit in overlay["units"])
    assert progress["reviewed_units"] == 0
    assert progress["completed_event_decisions"] == 0
    assert progress["unreviewed_events"] == 123


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("training_domain_relevance_decision", "relevant", "RELEVANCE_DECISION_INVALID"),
        ("workflow_status", "DONE", "WORKFLOW_STATUS_INVALID"),
    ],
)
def test_invalid_unit_vocabularies_rejected(
    packet: dict, overlay: dict, field: str, value: str, match: str
) -> None:
    unit_id = _unit(packet)["review_unit_id"]
    _append(overlay, _metadata_changes(unit_id) + [("UNIT", unit_id, "", field, value)])
    with pytest.raises(review.HumanReviewValidationError, match=match):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_warhead_unknown_atom_id_rejected(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    unit_id = packet_unit["review_unit_id"]
    decision = review._unit_by_id(overlay, unit_id)
    roles = deepcopy(decision["roles"])
    roles["warhead_atom_ids"] = ["UNKNOWN"]
    _append(
        overlay,
        [
            ("UNIT", unit_id, "", "warhead_atom_ids", ["UNKNOWN"]),
            ("UNIT", unit_id, "", "roles", roles),
        ],
    )
    with pytest.raises(review.HumanReviewValidationError, match="UNKNOWN_CCD"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_warhead_explicit_hydrogen_rejected(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    unit_id = packet_unit["review_unit_id"]
    hydrogen = next(
        atom["atom_id"]
        for atom in packet_unit["machine_chemistry_evidence"]["ccd_atom_inventory"]
        if atom["element"] == "H"
    )
    reactive = packet_unit["ligand_reactive_atom"]
    decision = review._unit_by_id(overlay, unit_id)
    roles = deepcopy(decision["roles"])
    roles["warhead_atom_ids"] = sorted([reactive, hydrogen])
    _append(
        overlay,
        [
            ("UNIT", unit_id, "", "warhead_atom_ids", sorted([reactive, hydrogen])),
            ("UNIT", unit_id, "", "roles", roles),
        ],
    )
    with pytest.raises(review.HumanReviewValidationError, match="EXPLICIT_HYDROGEN"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_reactive_atom_absent_from_warhead_rejected(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    unit_id = packet_unit["review_unit_id"]
    reactive = packet_unit["ligand_reactive_atom"]
    heavy = sorted(
        atom["atom_id"]
        for atom in packet_unit["machine_chemistry_evidence"]["ccd_heavy_atom_inventory"]
    )
    alternative = next(atom for atom in heavy if atom != reactive)
    roles = {
        "scaffold_atom_ids": [atom for atom in heavy if atom != alternative],
        "linker_atom_ids": [],
        "warhead_atom_ids": [alternative],
    }
    _append(
        overlay,
        [
            ("UNIT", unit_id, "", "warhead_atom_ids", [alternative]),
            ("UNIT", unit_id, "", "roles", roles),
        ],
    )
    with pytest.raises(review.HumanReviewValidationError, match="REACTIVE_ATOM_ABSENT"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_role_overlap_rejected(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    unit_id = packet_unit["review_unit_id"]
    decision = review._unit_by_id(overlay, unit_id)
    roles = deepcopy(decision["roles"])
    roles["scaffold_atom_ids"] = sorted(
        roles["scaffold_atom_ids"] + roles["warhead_atom_ids"]
    )
    _append(overlay, [("UNIT", unit_id, "", "roles", roles)])
    with pytest.raises(review.HumanReviewValidationError, match="ROLE_ATOM_SETS_OVERLAP"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_role_incomplete_union_rejected(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    unit_id = packet_unit["review_unit_id"]
    decision = review._unit_by_id(overlay, unit_id)
    roles = deepcopy(decision["roles"])
    assert roles["scaffold_atom_ids"]
    roles["scaffold_atom_ids"] = roles["scaffold_atom_ids"][1:]
    _append(overlay, [("UNIT", unit_id, "", "roles", roles)])
    with pytest.raises(review.HumanReviewValidationError, match="UNION_NOT_EXACT"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_role_union_exact_heavy_atom_coverage_accepted(packet: dict) -> None:
    overlay, _ = _relevant_overlay(packet)
    progress = review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)
    assert progress["completed_relevant_chemistry_units"] == 1


def test_not_relevant_early_stop_requires_blank_chemistry_and_events(
    packet: dict, overlay: dict
) -> None:
    unit_id = _unit(packet)["review_unit_id"]
    _append(
        overlay,
        _metadata_changes(unit_id)
        + [
            (
                "UNIT",
                unit_id,
                "",
                "training_domain_relevance_decision",
                "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
            ),
            ("UNIT", unit_id, "", "workflow_status", "COMPLETED"),
        ],
    )
    progress = review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)
    assert progress["not_relevant_units"] == 1
    assert progress["completed_units"] == 1
    assert progress["completed_event_decisions"] == 0


def test_relevant_incomplete_chemistry_cannot_complete(packet: dict, overlay: dict) -> None:
    unit_id = _unit(packet)["review_unit_id"]
    _append(
        overlay,
        _metadata_changes(unit_id)
        + [
            (
                "UNIT",
                unit_id,
                "",
                "training_domain_relevance_decision",
                "RELEVANT_FOR_COVAPIE_POST_ONLY_V1",
            ),
            ("UNIT", unit_id, "", "workflow_status", "COMPLETED"),
        ],
    )
    with pytest.raises(review.HumanReviewValidationError, match="CONFIRMED_REACTIVE"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_relevant_incomplete_events_cannot_complete(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    unit_id = packet_unit["review_unit_id"]
    _append(overlay, [("UNIT", unit_id, "", "workflow_status", "COMPLETED")])
    with pytest.raises(review.HumanReviewValidationError, match="EVERY_EVENT_DECISION"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_include_requires_geometry_usable_yes(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    event_id = packet_unit["events_for_review"][0]["canonical_event_id"]
    _append(
        overlay,
        _event_changes(packet_unit["review_unit_id"], event_id, geometry="NO", use="INCLUDE"),
    )
    with pytest.raises(review.HumanReviewValidationError, match="INCLUDE_REQUIRES"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_exclude_requires_reason(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    event_id = packet_unit["events_for_review"][0]["canonical_event_id"]
    _append(
        overlay,
        _event_changes(packet_unit["review_unit_id"], event_id, geometry="NO", use="EXCLUDE"),
    )
    with pytest.raises(review.HumanReviewValidationError, match="EXCLUDE_REQUIRES"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_machine_human_disagreement_requires_rationale(packet: dict, overlay: dict) -> None:
    packet_unit = next(
        unit
        for unit in review.ordered_review_units_v1(packet)
        if review.priority_for_review_unit_v1(unit) == "P0"
    )
    unit_id = packet_unit["review_unit_id"]
    _append(
        overlay,
        [
            ("UNIT", unit_id, "", "reviewer_id", REVIEWER),
            ("UNIT", unit_id, "", "reviewed_at_utc", STAMP),
            (
                "UNIT",
                unit_id,
                "",
                "training_domain_relevance_decision",
                "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
            ),
            ("UNIT", unit_id, "", "workflow_status", "COMPLETED"),
        ],
    )
    with pytest.raises(review.HumanReviewValidationError, match="DISAGREEMENT"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_event_decision_does_not_propagate_to_other_event(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet, multi=True)
    unit_id = packet_unit["review_unit_id"]
    first, second = [event["canonical_event_id"] for event in packet_unit["events_for_review"][:2]]
    _append(overlay, _event_changes(unit_id, first, geometry="YES", use="INCLUDE"))
    review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)
    decision = review._unit_by_id(overlay, unit_id)
    assert review._event_by_id(decision, first)["event_training_use_decision"] == "INCLUDE"
    assert review._event_by_id(decision, second)["event_training_use_decision"] == ""


def test_multi_event_unit_accepts_independent_geometry_decisions(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet, multi=True)
    unit_id = packet_unit["review_unit_id"]
    first, second = [event["canonical_event_id"] for event in packet_unit["events_for_review"][:2]]
    _append(
        overlay,
        _event_changes(unit_id, first, geometry="YES", use="INCLUDE")
        + _event_changes(
            unit_id,
            second,
            geometry="NO",
            use="EXCLUDE",
            reason="Post geometry judged unusable for this crystal event.",
        ),
    )
    progress = review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)
    assert progress["included_events"] == 1
    assert progress["excluded_events"] == 1


def test_radius2_unavailable_event_can_still_be_included(packet: dict) -> None:
    packet_unit = _unit(packet, topology_missing=True)
    overlay = review.build_initial_overlay_v1(packet)
    # Reuse the chemistry helper's construction for this exact unit.
    unit_id = packet_unit["review_unit_id"]
    warhead, roles = _valid_atom_roles(packet_unit)
    _append(
        overlay,
        _metadata_changes(unit_id)
        + [
            (
                "UNIT",
                unit_id,
                "",
                "training_domain_relevance_decision",
                "RELEVANT_FOR_COVAPIE_POST_ONLY_V1",
            ),
            (
                "UNIT",
                unit_id,
                "",
                "reactive_atom_confirmation",
                {"status": "CONFIRMED", "confirmed_atom_id": packet_unit["ligand_reactive_atom"]},
            ),
            (
                "UNIT",
                unit_id,
                "",
                "warhead_family_decision",
                {
                    "decision": review.NEW_FAMILY_REVIEW,
                    "canonical_reaction_family_id": "",
                    "proposed_warhead_family_label": "TEST_TOPOLOGY_MISSING_PROPOSAL",
                },
            ),
            ("UNIT", unit_id, "", "warhead_atom_ids", warhead),
            ("UNIT", unit_id, "", "roles", roles),
            ("UNIT", unit_id, "", "workflow_status", "IN_PROGRESS"),
        ],
    )
    event = next(
        event
        for event in packet_unit["events_for_review"]
        if review.geometry_auxiliary_label_availability_v1(event)
        == "UNAVAILABLE_FOR_RADIUS2_DEPENDENT_LABELS"
    )
    _append(
        overlay,
        _event_changes(unit_id, event["canonical_event_id"], geometry="YES", use="INCLUDE"),
    )
    review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)
    assert review.geometry_auxiliary_label_availability_v1(event) == (
        "UNAVAILABLE_FOR_RADIUS2_DEPENDENT_LABELS"
    )


def test_candidate_only_family_id_is_not_accepted_as_approved(packet: dict) -> None:
    overlay, packet_unit = _relevant_overlay(packet)
    unit_id = packet_unit["review_unit_id"]
    invalid = {
        "decision": review.EXISTING_FAMILY,
        "canonical_reaction_family_id": "COVAPIE_CYS_SG_REACTION_FAMILY_6A5C7B2B614B5F52",
        "proposed_warhead_family_label": "",
    }
    _append(overlay, [("UNIT", unit_id, "", "warhead_family_decision", invalid)])
    with pytest.raises(review.HumanReviewValidationError, match="WARHEAD_FAMILY"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_append_only_history_detects_tamper(packet: dict) -> None:
    overlay, _ = _relevant_overlay(packet)
    overlay["decision_history"][0]["new_value"] = "silent-overwrite"
    with pytest.raises(review.HumanReviewValidationError, match="SHA256"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_progress_summary_is_deterministic(packet: dict) -> None:
    overlay, _ = _relevant_overlay(packet)
    first = review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)
    second = review.build_progress_v1(overlay, packet)
    assert first == second
    assert review._json_bytes(first) == review._json_bytes(second)


def test_invalid_baseline_sha_fails_closed(overlay: dict) -> None:
    overlay["baseline_bindings"]["baseline_packet_sha256"] = "0" * 64
    with pytest.raises(review.HumanReviewValidationError, match="BASELINE_BINDING"):
        review.validate_overlay_v1(REPO_ROOT, overlay, verify_sources=False)


def test_no_production_approval_or_materialization_in_artifacts() -> None:
    artifacts = review.build_artifacts_v1(REPO_ROOT)
    overlay = json.loads(artifacts[review.DECISIONS])
    assert overlay["production_authority_created"] is False
    assert overlay["production_materialization_performed"] is False
    assert overlay["training_materialization_performed"] is False
    assert set(artifacts) == set(review.OUTPUT_FILENAMES)


def test_materialize_fresh_then_exact_initial_rerun_is_byte_idempotent(
    tmp_path: Path,
) -> None:
    output = tmp_path / "workspace"
    first = review.materialize_v1(REPO_ROOT, output)
    assert first["already_initialized"] is False
    before = {
        name: (output / name).read_bytes() for name in review.OUTPUT_FILENAMES
    }
    second = review.materialize_v1(REPO_ROOT, output)
    assert second["already_initialized"] is True
    assert {
        name: (output / name).read_bytes() for name in review.OUTPUT_FILENAMES
    } == before


def test_materialize_refuses_post_decision_reinitialization_without_byte_change(
    tmp_path: Path, packet: dict
) -> None:
    output = tmp_path / "workspace"
    review.materialize_v1(REPO_ROOT, output)
    unit_id = _unit(packet)["review_unit_id"]
    review.record_unit_relevance_v1(
        REPO_ROOT,
        output,
        unit_id=unit_id,
        relevance_decision="NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
        workflow_status="COMPLETED",
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP,
        review_rationale=RATIONALE,
    )
    decisions_before = (output / review.DECISIONS).read_bytes()
    progress_before = (output / review.PROGRESS).read_bytes()
    history_before = json.loads(decisions_before)["decision_history"]
    with pytest.raises(
        review.HumanReviewValidationError,
        match="ALREADY_CONTAINS_HUMAN_DECISIONS",
    ):
        review.materialize_v1(REPO_ROOT, output)
    assert (output / review.DECISIONS).read_bytes() == decisions_before
    assert (output / review.PROGRESS).read_bytes() == progress_before
    assert json.loads((output / review.DECISIONS).read_bytes())[
        "decision_history"
    ] == history_before


def test_materialize_partial_workspace_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "workspace"
    output.mkdir()
    (output / review.GUIDE).write_text("partial", encoding="utf-8")
    with pytest.raises(review.HumanReviewValidationError, match="PARTIAL_OR_FILE_SET"):
        review.materialize_v1(REPO_ROOT, output)
    assert (output / review.GUIDE).read_text(encoding="utf-8") == "partial"


def test_materialize_static_drift_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "workspace"
    review.materialize_v1(REPO_ROOT, output)
    decisions_before = (output / review.DECISIONS).read_bytes()
    progress_before = (output / review.PROGRESS).read_bytes()
    (output / review.GUIDE).write_bytes(
        (output / review.GUIDE).read_bytes() + b"static drift"
    )
    with pytest.raises(review.HumanReviewValidationError, match="STATIC_ARTIFACT_DRIFT"):
        review.materialize_v1(REPO_ROOT, output)
    assert (output / review.DECISIONS).read_bytes() == decisions_before
    assert (output / review.PROGRESS).read_bytes() == progress_before


def test_materialize_progress_drift_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "workspace"
    review.materialize_v1(REPO_ROOT, output)
    decisions_before = (output / review.DECISIONS).read_bytes()
    progress = json.loads((output / review.PROGRESS).read_bytes())
    progress["unreviewed_units"] = 35
    (output / review.PROGRESS).write_text(
        json.dumps(progress, sort_keys=True) + "\n", encoding="utf-8"
    )
    drifted_progress = (output / review.PROGRESS).read_bytes()
    with pytest.raises(review.HumanReviewValidationError, match="PROGRESS_NOT_EXACT"):
        review.materialize_v1(REPO_ROOT, output)
    assert (output / review.DECISIONS).read_bytes() == decisions_before
    assert (output / review.PROGRESS).read_bytes() == drifted_progress


def test_no_force_reset_path_exists() -> None:
    assert "force" not in inspect.signature(review.materialize_v1).parameters
    completed = subprocess.run(
        [
            sys.executable,
            str(
                REPO_ROOT
                / "scripts/build_covapie_bulk_post_only_cys_sg_human_review_v1.py"
            ),
            "--help",
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        check=True,
        capture_output=True,
        text=True,
    )
    assert "force-reset" not in completed.stdout
    assert "--force" not in completed.stdout


def test_downward_relevance_correction_without_explicit_clear_is_rejected(
    tmp_path: Path, packet: dict
) -> None:
    output, packet_unit, _ = _prepare_relevant_workspace_with_downstream(
        tmp_path, packet
    )
    decisions_before = (output / review.DECISIONS).read_bytes()
    progress_before = (output / review.PROGRESS).read_bytes()
    packet_before = (
        REPO_ROOT / review.BASELINE_ROOT_RELATIVE / review.REVIEW_PACKET
    ).read_bytes()
    with pytest.raises(
        review.HumanReviewValidationError,
        match="DOWNSTREAM_DECISIONS_EXIST_EXPLICIT_CLEAR_REQUIRED",
    ):
        review.record_unit_relevance_v1(
            REPO_ROOT,
            output,
            unit_id=packet_unit["review_unit_id"],
            relevance_decision="NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
            workflow_status="COMPLETED",
            reviewer_id=REVIEWER,
            reviewed_at_utc=STAMP_4,
            review_rationale=RATIONALE + " Corrected downward.",
        )
    assert (output / review.DECISIONS).read_bytes() == decisions_before
    assert (output / review.PROGRESS).read_bytes() == progress_before
    assert (
        REPO_ROOT / review.BASELINE_ROOT_RELATIVE / review.REVIEW_PACKET
    ).read_bytes() == packet_before


def test_explicit_downstream_clear_is_append_only_and_replay_exact(
    tmp_path: Path, packet: dict
) -> None:
    output, packet_unit, event_id = _prepare_relevant_workspace_with_downstream(
        tmp_path, packet
    )
    before = json.loads((output / review.DECISIONS).read_bytes())
    old_history = deepcopy(before["decision_history"])
    result = review.record_unit_relevance_v1(
        REPO_ROOT,
        output,
        unit_id=packet_unit["review_unit_id"],
        relevance_decision="NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
        workflow_status="COMPLETED",
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP_4,
        review_rationale=RATIONALE + " Explicitly invalidated downstream review.",
        clear_downstream=True,
    )
    after = json.loads((output / review.DECISIONS).read_bytes())
    unit = review._unit_by_id(after, packet_unit["review_unit_id"])
    assert review._chemistry_blank(unit)
    assert review._events_blank(unit)
    assert unit["training_domain_relevance_decision"] == (
        "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
    )
    assert after["decision_history"][: len(old_history)] == old_history
    assert len(after["decision_history"]) > len(old_history)
    appended = after["decision_history"][len(old_history) :]
    assert any(
        entry["field"] == "warhead_atom_ids"
        and entry["old_value"]
        and entry["new_value"] == []
        for entry in appended
    )
    assert any(
        entry["canonical_event_id"] == event_id
        and entry["field"] == "event_training_use_decision"
        and entry["old_value"] == "INCLUDE"
        and entry["new_value"] == ""
        for entry in appended
    )
    progress = review.validate_overlay_v1(
        REPO_ROOT, after, verify_sources=False
    )
    assert progress == result["progress"]
    assert progress["not_relevant_units"] == 1
    assert progress["completed_event_decisions"] == 0


def test_explicit_downstream_clear_supports_deferred_relevance(
    tmp_path: Path, packet: dict
) -> None:
    output, packet_unit, _ = _prepare_relevant_workspace_with_downstream(
        tmp_path, packet
    )
    before = json.loads((output / review.DECISIONS).read_bytes())
    result = review.record_unit_relevance_v1(
        REPO_ROOT,
        output,
        unit_id=packet_unit["review_unit_id"],
        relevance_decision="DEFERRED_INSUFFICIENT_EVIDENCE",
        workflow_status="DEFERRED",
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP_4,
        review_rationale=RATIONALE + " Deferred after audited invalidation.",
        clear_downstream=True,
    )
    after = json.loads((output / review.DECISIONS).read_bytes())
    unit = review._unit_by_id(after, packet_unit["review_unit_id"])
    assert unit["workflow_status"] == "DEFERRED"
    assert unit["training_domain_relevance_decision"] == (
        "DEFERRED_INSUFFICIENT_EVIDENCE"
    )
    assert review._chemistry_blank(unit) and review._events_blank(unit)
    assert after["decision_history"][: len(before["decision_history"])] == before[
        "decision_history"
    ]
    assert result["progress"]["deferred_units"] == 1


def test_record_cli_mutates_only_temp_overlay_progress_and_preserves_sources(
    tmp_path: Path, packet: dict
) -> None:
    output = tmp_path / "workspace"
    review.materialize_v1(REPO_ROOT, output)
    frozen_paths = [
        REPO_ROOT / review.BASELINE_ROOT_RELATIVE / name
        for name in review.BASELINE_ARTIFACT_SHA256
    ]
    registry_paths = [
        review._authority_path(REPO_ROOT, binding)  # noqa: SLF001
        for binding in review.AUTHORITY_SOURCE_BINDINGS.values()
    ]
    protected = frozen_paths + registry_paths
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    static_before = {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in (review.GUIDE, review.DECISION_SCHEMA, review.WORKLIST)
    }
    unit_id = _unit(packet)["review_unit_id"]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    completed = subprocess.run(
        [
            sys.executable,
            str(
                REPO_ROOT
                / "scripts/record_covapie_bulk_post_only_cys_sg_review_decision_v1.py"
            ),
            "--repo-root",
            str(REPO_ROOT),
            "--output-root",
            str(output),
            "unit-relevance",
            "--unit-id",
            unit_id,
            "--reviewer-id",
            REVIEWER,
            "--reviewed-at-utc",
            STAMP,
            "--review-rationale",
            RATIONALE,
            "--decision",
            "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
            "--workflow-status",
            "COMPLETED",
        ],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["history_entry_count"] == 5
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected} == before
    assert {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in static_before
    } == static_before
    checked = review.check_workspace_v1(REPO_ROOT, output)
    assert checked["progress"]["not_relevant_units"] == 1
    assert checked["progress"]["completed_event_decisions"] == 0


def test_record_path_does_not_use_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, packet: dict) -> None:
    output = tmp_path / "workspace"
    review.materialize_v1(REPO_ROOT, output)

    def forbidden_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("network access forbidden")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    unit_id = _unit(packet)["review_unit_id"]
    result = review.record_unit_relevance_v1(
        REPO_ROOT,
        output,
        unit_id=unit_id,
        relevance_decision="DEFERRED_INSUFFICIENT_EVIDENCE",
        workflow_status="DEFERRED",
        reviewer_id=REVIEWER,
        reviewed_at_utc=STAMP,
        review_rationale=RATIONALE,
    )
    assert result["production_authority_created"] is False


def test_show_card_is_machine_only_and_contains_no_approval_advice(
    tmp_path: Path, packet: dict
) -> None:
    output = tmp_path / "workspace"
    review.materialize_v1(REPO_ROOT, output)
    unit_id = review.next_review_unit_id_v1(REPO_ROOT, output)
    card = review.render_review_card_v1(REPO_ROOT, unit_id, output)
    assert "MACHINE TRIAGE ONLY" in card
    assert "SUPPORTING" in card
    assert "underlying_events:" in card
    assert "you should approve" not in card.lower()


def test_deterministic_double_materialization() -> None:
    assert review.verify_deterministic_replay_v1(REPO_ROOT) == (
        review.verify_deterministic_replay_v1(REPO_ROOT)
    )
