from __future__ import annotations

import csv
import dataclasses
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from covalent_ext import (
    covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1
    as stage,
)
from covalent_ext.covapie_hermetic_git_lifecycle_harness_v1 import (
    exercise_hermetic_git_lifecycle_matrix,
)


ROOT = Path(__file__).resolve().parents[1]


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def result() -> stage.BuildResult:
    return stage.build_result(ROOT)


@pytest.fixture(scope="module")
def payloads() -> dict[str, bytes]:
    return stage.build_evidence_payloads(ROOT)


@pytest.fixture(scope="module")
def class_draft(result: stage.BuildResult) -> dict[str, object]:
    source = result.class_rows[0]
    return {
        "review_record_version": stage.REVIEW_RECORD_VERSION,
        "review_unit_type": "candidate_class",
        "warhead_type_candidate_class_index_0based":
            source["warhead_type_candidate_class_index_0based"],
        "warhead_type_candidate_class_id":
            source["warhead_type_candidate_class_id"],
        "reaction_family_id": source["reaction_family_id"],
        "reaction_family_semantic_name": source["reaction_family_semantic_name"],
        "canonical_reaction_family_signature_sha256":
            source["canonical_reaction_family_signature_sha256"],
        "warhead_rule_id": source["warhead_rule_id"],
        "warhead_type_candidate_semantic_name":
            source["warhead_type_candidate_semantic_name"],
        "canonical_local_graph_rule_sha256":
            source["canonical_local_graph_rule_sha256"],
        "reaction_family_identity_review_decision": "not_reviewed",
        "warhead_rule_topology_review_decision": "not_reviewed",
        "warhead_smarts_review_status": "not_materialized",
        "candidate_warhead_smarts": "",
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        # Synthetic draft-only source identity: no review package is materialized.
        "source_class_record_sha256": "c" * 64,
        "review_record_sha256": "",
    }


@pytest.fixture(scope="module")
def sample_draft(result: stage.BuildResult) -> dict[str, object]:
    source = result.sample_rows[0]
    assignment_sha = source["assignment_record_sha256"]
    return {
        "review_record_version": stage.REVIEW_RECORD_VERSION,
        "review_unit_type": "sample_assignment",
        "sample_index_row_id": source["sample_index_row_id"],
        "assignment_record_sha256": assignment_sha,
        "warhead_type_candidate_class_id":
            source["warhead_type_candidate_class_id"],
        "reaction_family_id": source["reaction_family_id"],
        "warhead_rule_id": source["warhead_rule_id"],
        "sample_assignment_review_decision": "not_reviewed",
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        "source_assignment_record_sha256": assignment_sha,
        "review_record_sha256": "",
    }


def test_fixed_interpreter_contract() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"


def test_formal_base_identity_and_current_lifecycle() -> None:
    shown = subprocess.run(
        (
            "git", "show", "-s", "--format=%H%n%P%n%T%n%s",
            stage.BASE_COMMIT,
        ),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert shown.stdout.decode().splitlines() == [
        stage.BASE_COMMIT,
        stage.BASE_PARENT,
        stage.BASE_TREE,
        stage.BASE_SUBJECT,
    ]
    assert stage.validate_execution_boundary_v1(ROOT) in {
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    }


def test_exact12_sources_are_base_read_and_sha_frozen(
    result: stage.BuildResult,
) -> None:
    assert len(stage.SOURCE_PATHS) == len(stage.FROZEN_BASE_SHA256) == 12
    assert len(result.source_rows) == 12
    for row, path in zip(result.source_rows, stage.SOURCE_PATHS):
        payload = subprocess.run(
            ("git", "show", f"{stage.BASE_COMMIT}:{path.as_posix()}"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout
        assert hashlib.sha256(payload).hexdigest() == stage.FROZEN_BASE_SHA256[path]
        assert row["source_path"] == path.as_posix()
        assert row["BASE_SHA256"] == stage.FROZEN_BASE_SHA256[path]
        assert row["Current11_coverage"] == "11/11"
        assert row["fields_actually_used"]
        assert row["authority_class"]
        assert row["verified"] is True


def test_phase_a_reconstructs_exact7_exact11_and_record_sha(
    result: stage.BuildResult,
) -> None:
    assert result.transaction_succeeded
    assert not result.blocking_reasons
    assert len(result.class_rows) == 7
    assert len(result.sample_rows) == 11
    assignments = csv_rows(stage.base_bytes(ROOT, stage.ASSIGNMENT_AUTHORITY))
    assert len(assignments) == 11
    assert all(
        stage._assignment_hash(row) == row["assignment_record_sha256"]
        for row in assignments
    )
    assert {
        row["assignment_record_sha256"] for row in result.sample_rows
    } == {
        row["assignment_record_sha256"] for row in assignments
    }


def test_sample_class_rule_family_links_are_exact_one(
    result: stage.BuildResult,
) -> None:
    classes = {
        row["warhead_type_candidate_class_id"]: row for row in result.class_rows
    }
    assert len(classes) == 7
    for sample in result.sample_rows:
        linked = classes[sample["warhead_type_candidate_class_id"]]
        assert sample["warhead_type_candidate_class_index_0based"] == (
            linked["warhead_type_candidate_class_index_0based"]
        )
        assert sample["reaction_family_id"] == linked["reaction_family_id"]
        assert sample["warhead_rule_id"] == linked["warhead_rule_id"]


def test_review_and_smarts_vocabularies_are_closed() -> None:
    assert stage.HUMAN_REVIEW_DECISIONS == (
        "not_reviewed", "approve", "revise", "quarantine"
    )
    assert stage.SMARTS_REVIEW_STATUSES == (
        "not_materialized",
        "candidate_not_reviewed",
        "approved",
        "revised",
        "quarantined",
    )
    assert stage.SMARTS_UNREVIEWED_STATUSES == (
        "not_materialized",
        "candidate_not_reviewed",
    )
    assert stage.SMARTS_HUMAN_REVIEWED_STATUSES == (
        "approved",
        "revised",
        "quarantined",
    )


def test_meaningful_text_requires_exact_nonblank_string() -> None:
    assert stage._is_meaningful_text("human-reviewer")
    assert stage._is_meaningful_text("  human-reviewer  ")
    for value in ("", " ", "   ", "\t", "\n", "\r\n", True, 1, object()):
        assert not stage._is_meaningful_text(value)


def test_lower_sha256_requires_exact_lowercase_64_hex_string() -> None:
    for value in ("a" * 64, "0123456789abcdef" * 4):
        result = stage._is_lower_sha256(value)
        assert result is True
        assert type(result) is bool
    for value in (
        "",
        "abc",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        " " + "a" * 64,
        "a" * 64 + " ",
        True,
        1,
        1.0,
        object(),
    ):
        result = stage._is_lower_sha256(value)
        assert result is False
        assert type(result) is bool


def test_exact_scalar_type_helpers_exclude_python_equality_aliases() -> None:
    assert stage._is_exact_bool(True) is True
    assert stage._is_exact_bool(False) is True
    assert stage._is_exact_bool(1) is False
    assert stage._is_exact_bool(object()) is False
    assert stage._is_exact_int(1) is True
    assert stage._is_exact_int(0) is True
    assert stage._is_exact_int(True) is False
    assert stage._is_exact_int(1.0) is False
    assert all(
        type(result) is bool
        for result in (
            stage._is_exact_bool(True),
            stage._is_exact_bool(1),
            stage._is_exact_int(1),
            stage._is_exact_int(True),
        )
    )


def test_exact12_policy_registry_is_semantically_frozen(
    result: stage.BuildResult,
) -> None:
    assert len(result.policy_rows) == 12
    assert [row["policy_id"] for row in result.policy_rows] == [
        f"REVIEW_POLICY_{index:03d}" for index in range(1, 13)
    ]
    assert [row["semantic_name"] for row in result.policy_rows] == [
        definition[0] for definition in stage.POLICY_DEFINITIONS
    ]
    assert all(row["fails_closed"] and row["verified"] for row in result.policy_rows)
    assert "topology rule approval is separate from SMARTS approval" in {
        row["semantic_name"] for row in result.policy_rows
    }


def test_exact7_class_packages_are_ready_but_unreviewed(
    result: stage.BuildResult,
) -> None:
    assert [row["warhead_type_candidate_class_index_0based"]
            for row in result.class_rows] == list(range(7))
    for row in result.class_rows:
        assert row["class_review_package_ready"] is True
        assert row["ready_for_sample_assignment_review"] is True
        assert row["family_identity_evidence_complete"] is True
        assert row["rule_topology_evidence_complete"] is True
        assert row["assignment_support_complete"] is True
        assert row["class_identity_verified"] is True
        assert row["reaction_family_identity_review_decision"] == "not_reviewed"
        assert row["warhead_rule_topology_review_decision"] == "not_reviewed"
        assert row["warhead_smarts_review_status"] == "not_materialized"
        assert row["candidate_warhead_smarts"] == ""
        assert row["reviewer_id"] == row["review_rationale"] == row["review_notes"] == ""
        assert row["family_identity_review_completed"] is False
        assert row["rule_topology_review_completed"] is False
        assert row["warhead_rule_topology_review_passed"] is False
        assert row["approved_reaction_family_available"] is False
        assert row["approved_warhead_rule_available"] is False
        assert row["ready_for_role_proposal_generation"] is False
        assert row["ready_for_training"] is False


def test_exact11_sample_packages_are_ready_but_every_gate_closed(
    result: stage.BuildResult,
) -> None:
    assert len({row["sample_index_row_id"] for row in result.sample_rows}) == 11
    for row in result.sample_rows:
        assert row["class_review_package_ready"] is True
        assert row["sample_assignment_evidence_complete"] is True
        assert row["sample_assignment_identity_verified"] is True
        assert row["sample_review_package_ready"] is True
        assert row["sample_assignment_review_decision"] == "not_reviewed"
        assert row["reviewer_id"] == row["review_rationale"] == row["review_notes"] == ""
        for field in (
            "sample_review_completed",
            "approved_reaction_family_available",
            "approved_warhead_rule_available",
            "human_gold_review_completed",
            "training_label_approved",
            "ready_for_role_proposal_generation",
            "ready_for_minimal_seed_proposal_generation",
            "ready_for_mask_materialization",
            "ready_for_tensorization",
            "ready_for_model_integration",
            "ready_for_training",
        ):
            assert row[field] is False


def test_family_approval_requires_decision_reviewer_rationale_and_identity() -> None:
    arguments = {
        "decision": "approve",
        "reviewer_id": "reviewer",
        "review_rationale": "evidence checked",
        "canonical_identity_sha256": "a" * 64,
        "source_identity_sha256": "a" * 64,
    }
    assert stage.approved_reaction_family_available(**arguments)
    for key, value in (
        ("decision", "revise"),
        ("reviewer_id", ""),
        ("reviewer_id", "   "),
        ("reviewer_id", True),
        ("review_rationale", ""),
        ("review_rationale", "\t"),
        ("review_rationale", 1),
        ("source_identity_sha256", "b" * 64),
    ):
        mutated = dict(arguments)
        mutated[key] = value
        assert not stage.approved_reaction_family_available(**mutated)


def test_topology_approval_is_not_approved_smarts_or_rule() -> None:
    arguments = {
        "family_available": True,
        "topology_decision": "approve",
        "approved_smarts": "",
        "smarts_review_status": "not_materialized",
        "smarts_match_count": 0,
        "smarts_includes_reactive_atom": False,
        "warhead_atom_count": 0,
        "attachment_boundary_count": 0,
        "reviewer_id": "reviewer",
        "review_rationale": "topology only",
        "identities_unchanged": True,
    }
    assert not stage.approved_warhead_rule_available(**arguments)


def test_approved_rule_requires_all_smarts_and_identity_conditions() -> None:
    arguments = {
        "family_available": True,
        "topology_decision": "approve",
        "approved_smarts": "[C:1]",
        "smarts_review_status": "approved",
        "smarts_match_count": 1,
        "smarts_includes_reactive_atom": True,
        "warhead_atom_count": 1,
        "attachment_boundary_count": 1,
        "reviewer_id": "reviewer",
        "review_rationale": "all evidence checked",
        "identities_unchanged": True,
    }
    assert stage.approved_warhead_rule_available(**arguments)
    mutations = (
        ("family_available", False),
        ("topology_decision", "revise"),
        ("approved_smarts", ""),
        ("approved_smarts", "   "),
        ("approved_smarts", "\t"),
        ("smarts_review_status", "candidate_not_reviewed"),
        ("smarts_match_count", 0),
        ("smarts_match_count", 2),
        ("smarts_includes_reactive_atom", False),
        ("warhead_atom_count", 0),
        ("attachment_boundary_count", 0),
        ("attachment_boundary_count", 2),
        ("reviewer_id", ""),
        ("reviewer_id", "   "),
        ("reviewer_id", True),
        ("review_rationale", ""),
        ("review_rationale", "\n"),
        ("review_rationale", 1),
        ("identities_unchanged", False),
    )
    for key, value in mutations:
        mutated = dict(arguments)
        mutated[key] = value
        assert not stage.approved_warhead_rule_available(**mutated)


def test_gold_and_role_dependencies_fail_closed() -> None:
    arguments = {
        "sample_decision": "approve",
        "family_available": True,
        "rule_available": True,
        "assignment_record_sha256": "a" * 64,
        "source_assignment_record_sha256": "a" * 64,
        "reviewer_id": "reviewer",
        "review_rationale": "assignment checked",
    }
    assert stage.human_gold_review_completed(**arguments)
    for key, value in (
        ("sample_decision", "quarantine"),
        ("family_available", False),
        ("rule_available", False),
        ("source_assignment_record_sha256", "b" * 64),
        ("reviewer_id", ""),
        ("reviewer_id", "   "),
        ("reviewer_id", True),
        ("review_rationale", ""),
        ("review_rationale", "\t"),
        ("review_rationale", 1),
    ):
        mutated = dict(arguments)
        mutated[key] = value
        assert not stage.human_gold_review_completed(**mutated)
    assert stage.ready_for_role_proposal_generation(True, True, True)
    assert not stage.ready_for_role_proposal_generation(True, True, False)
    assert not stage.ready_for_role_proposal_generation(True, False, True)
    assert not stage.ready_for_role_proposal_generation(False, True, True)


def test_family_approval_exact_scalar_and_sha_gate_cases() -> None:
    class StringSubclass(str):
        pass

    valid = {
        "decision": "approve",
        "reviewer_id": "human-reviewer",
        "review_rationale": "family identity checked",
        "canonical_identity_sha256": "a" * 64,
        "source_identity_sha256": "a" * 64,
    }
    result = stage.approved_reaction_family_available(**valid)
    assert result is True
    assert type(result) is bool
    mutations = (
        ("canonical_identity_sha256", 1, "source_identity_sha256", True),
        ("canonical_identity_sha256", True, "source_identity_sha256", 1),
        ("canonical_identity_sha256", "abc", "source_identity_sha256", "abc"),
        (
            "canonical_identity_sha256",
            "A" * 64,
            "source_identity_sha256",
            "A" * 64,
        ),
        (
            "canonical_identity_sha256",
            " " + "a" * 64,
            "source_identity_sha256",
            " " + "a" * 64,
        ),
        (
            "canonical_identity_sha256",
            "a" * 64 + " ",
            "source_identity_sha256",
            "a" * 64 + " ",
        ),
        (
            "canonical_identity_sha256",
            "a" * 64,
            "source_identity_sha256",
            "b" * 64,
        ),
        ("decision", StringSubclass("approve"), "reviewer_id", "human-reviewer"),
        ("reviewer_id", "   ", "review_rationale", "family identity checked"),
        ("reviewer_id", object(), "review_rationale", "family identity checked"),
        ("review_rationale", "\t", "reviewer_id", "human-reviewer"),
        ("review_rationale", 1, "reviewer_id", "human-reviewer"),
    )
    for first_key, first_value, second_key, second_value in mutations:
        arguments = dict(valid)
        arguments[first_key] = first_value
        arguments[second_key] = second_value
        result = stage.approved_reaction_family_available(**arguments)
        assert result is False
        assert type(result) is bool


def test_rule_approval_exact_scalar_gate_cases() -> None:
    class StringSubclass(str):
        pass

    valid = {
        "family_available": True,
        "topology_decision": "approve",
        "approved_smarts": "[C:1]",
        "smarts_review_status": "approved",
        "smarts_match_count": 1,
        "smarts_includes_reactive_atom": True,
        "warhead_atom_count": 1,
        "attachment_boundary_count": 1,
        "reviewer_id": "human-reviewer",
        "review_rationale": "rule and SMARTS checked",
        "identities_unchanged": True,
    }
    result = stage.approved_warhead_rule_available(**valid)
    assert result is True
    assert type(result) is bool
    mutations = (
        ("family_available", 1),
        ("family_available", object()),
        ("smarts_match_count", True),
        ("smarts_match_count", 1.0),
        ("smarts_match_count", "1"),
        ("smarts_includes_reactive_atom", 1),
        ("smarts_includes_reactive_atom", object()),
        ("warhead_atom_count", True),
        ("warhead_atom_count", 1.0),
        ("warhead_atom_count", "1"),
        ("attachment_boundary_count", True),
        ("attachment_boundary_count", 1.0),
        ("identities_unchanged", 1),
        ("identities_unchanged", object()),
        ("topology_decision", StringSubclass("approve")),
        ("smarts_review_status", StringSubclass("approved")),
        ("approved_smarts", "   "),
        ("approved_smarts", object()),
        ("reviewer_id", "\t"),
        ("reviewer_id", object()),
        ("review_rationale", "\n"),
        ("review_rationale", 1),
    )
    for key, value in mutations:
        arguments = dict(valid)
        arguments[key] = value
        result = stage.approved_warhead_rule_available(**arguments)
        assert result is False
        assert type(result) is bool


def test_gold_review_exact_scalar_and_sha_gate_cases() -> None:
    class StringSubclass(str):
        pass

    valid = {
        "sample_decision": "approve",
        "family_available": True,
        "rule_available": True,
        "assignment_record_sha256": "a" * 64,
        "source_assignment_record_sha256": "a" * 64,
        "reviewer_id": "human-reviewer",
        "review_rationale": "sample assignment checked",
    }
    result = stage.human_gold_review_completed(**valid)
    assert result is True
    assert type(result) is bool
    mutations = (
        ("family_available", 1, "rule_available", True),
        ("family_available", object(), "rule_available", True),
        ("rule_available", 1, "family_available", True),
        ("rule_available", object(), "family_available", True),
        (
            "assignment_record_sha256",
            1,
            "source_assignment_record_sha256",
            True,
        ),
        (
            "assignment_record_sha256",
            "abc",
            "source_assignment_record_sha256",
            "abc",
        ),
        (
            "assignment_record_sha256",
            "A" * 64,
            "source_assignment_record_sha256",
            "A" * 64,
        ),
        (
            "assignment_record_sha256",
            " " + "a" * 64,
            "source_assignment_record_sha256",
            " " + "a" * 64,
        ),
        (
            "assignment_record_sha256",
            "a" * 64 + " ",
            "source_assignment_record_sha256",
            "a" * 64 + " ",
        ),
        (
            "assignment_record_sha256",
            "a" * 64,
            "source_assignment_record_sha256",
            "b" * 64,
        ),
        ("sample_decision", StringSubclass("approve"), "reviewer_id", "human"),
        ("reviewer_id", "   ", "review_rationale", "sample checked"),
        ("reviewer_id", object(), "review_rationale", "sample checked"),
        ("review_rationale", "\t", "reviewer_id", "human-reviewer"),
        ("review_rationale", 1, "reviewer_id", "human-reviewer"),
    )
    for first_key, first_value, second_key, second_value in mutations:
        arguments = dict(valid)
        arguments[first_key] = first_value
        arguments[second_key] = second_value
        result = stage.human_gold_review_completed(**arguments)
        assert result is False
        assert type(result) is bool


def test_role_proposal_gate_requires_three_exact_true_values() -> None:
    result = stage.ready_for_role_proposal_generation(True, True, True)
    assert result is True
    assert type(result) is bool
    for arguments in (
        (1, True, True),
        (object(), True, True),
        ("yes", True, True),
        (True, 1, True),
        (True, object(), True),
        (True, "yes", True),
        (True, True, 1),
        (True, True, object()),
        (True, True, "yes"),
    ):
        result = stage.ready_for_role_proposal_generation(*arguments)
        assert result is False
        assert type(result) is bool


def test_complete_class_draft_is_valid(
    class_draft: dict[str, object],
) -> None:
    assert stage.REVIEW_RECORD_VERSION == "covapie_cys_sg_human_review_record_v1"
    assert stage.REVIEW_UNIT_TYPES == ("candidate_class", "sample_assignment")
    assert stage.CLASS_REVIEW_RECORD_FIELDS[-1] == "review_record_sha256"
    assert stage.SAMPLE_REVIEW_RECORD_FIELDS[-1] == "review_record_sha256"
    assert set(class_draft) == set(stage.CLASS_REVIEW_RECORD_FIELDS)
    assert stage.validate_review_record_schema(class_draft) == "candidate_class"
    assert set(stage.review_record_hash_input(class_draft)) == (
        set(stage.CLASS_REVIEW_RECORD_FIELDS) - {"review_record_sha256"}
    )
    assert "/" not in stage.REVIEW_RECORD_VERSION


def test_complete_sample_draft_is_valid(
    sample_draft: dict[str, object],
) -> None:
    assert set(sample_draft) == set(stage.SAMPLE_REVIEW_RECORD_FIELDS)
    assert stage.validate_review_record_schema(sample_draft) == "sample_assignment"
    assert sample_draft["source_assignment_record_sha256"] == (
        sample_draft["assignment_record_sha256"]
    )
    assert set(stage.review_record_hash_input(sample_draft)) == (
        set(stage.SAMPLE_REVIEW_RECORD_FIELDS) - {"review_record_sha256"}
    )


def test_review_record_requires_exact_dict_container(
    sample_draft: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError, match="^review_record_container_not_exact_dict$"
    ):
        stage.validate_review_record_schema(MappingProxyType(sample_draft))


@pytest.mark.parametrize("unit_type", ["sample", "class", "review", "record", ""])
def test_review_unit_type_closed_set_rejects_ambiguous_values(
    class_draft: dict[str, object], unit_type: str,
) -> None:
    record = dict(class_draft)
    record["review_unit_type"] = unit_type
    with pytest.raises(ValueError, match="^review_unit_type_invalid$"):
        stage.validate_review_record_schema(record)


def test_wrong_review_record_version_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["review_record_version"] = "covapie_cys_sg_human_review_record_v0"
    with pytest.raises(ValueError, match="^review_record_version_mismatch$"):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize("field", ["review_notes", "source_class_record_sha256"])
def test_missing_class_field_is_rejected(
    class_draft: dict[str, object], field: str,
) -> None:
    record = dict(class_draft)
    del record[field]
    with pytest.raises(
        ValueError, match="^class_review_record_field_inventory_mismatch$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize("field", ["created_at", "timestamp", "absolute_path"])
def test_extra_class_metadata_is_rejected(
    class_draft: dict[str, object], field: str,
) -> None:
    record = dict(class_draft)
    record[field] = "/not/allowed" if field == "absolute_path" else "now"
    with pytest.raises(
        ValueError, match="^class_review_record_field_inventory_mismatch$"
    ):
        stage.validate_review_record_schema(record)


def test_missing_sample_field_is_rejected(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    del record["source_assignment_record_sha256"]
    with pytest.raises(
        ValueError, match="^sample_review_record_field_inventory_mismatch$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize("field", ["updated_at", "source_path", "absolute_path"])
def test_extra_sample_metadata_is_rejected(
    sample_draft: dict[str, object], field: str,
) -> None:
    record = dict(sample_draft)
    record[field] = "/not/allowed"
    with pytest.raises(
        ValueError, match="^sample_review_record_field_inventory_mismatch$"
    ):
        stage.validate_review_record_schema(record)


def test_class_index_bool_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_type_candidate_class_index_0based"] = True
    with pytest.raises(
        ValueError,
        match=(
            "^review_record_field_type_invalid:"
            "warhead_type_candidate_class_index_0based$"
        ),
    ):
        stage.validate_review_record_schema(record)


def test_class_index_negative_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_type_candidate_class_index_0based"] = -1
    with pytest.raises(
        ValueError,
        match=(
            "^review_record_integer_negative:"
            "warhead_type_candidate_class_index_0based$"
        ),
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize(
    "field",
    [
        "canonical_reaction_family_signature_sha256",
        "canonical_local_graph_rule_sha256",
        "source_class_record_sha256",
    ],
)
def test_malformed_class_sha_is_rejected(
    class_draft: dict[str, object], field: str,
) -> None:
    record = dict(class_draft)
    record[field] = "ABC123"
    with pytest.raises(
        ValueError, match=f"^review_record_SHA_invalid:{field}$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize(
    "field", ["assignment_record_sha256", "source_assignment_record_sha256"]
)
def test_malformed_sample_sha_is_rejected(
    sample_draft: dict[str, object], field: str,
) -> None:
    record = dict(sample_draft)
    record[field] = "f" * 63
    with pytest.raises(
        ValueError, match=f"^review_record_SHA_invalid:{field}$"
    ):
        stage.validate_review_record_schema(record)


def test_malformed_review_record_sha_is_rejected(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    record["review_record_sha256"] = "A" * 64
    with pytest.raises(
        ValueError, match="^review_record_SHA_invalid:review_record_sha256$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize(
    ("fixture_name", "field"),
    [
        ("class_draft", "warhead_type_candidate_class_id"),
        ("class_draft", "reviewer_id"),
        ("sample_draft", "sample_index_row_id"),
        ("sample_draft", "review_record_sha256"),
    ],
)
def test_exact_string_field_types_are_enforced(
    request: pytest.FixtureRequest, fixture_name: str, field: str,
) -> None:
    record = dict(request.getfixturevalue(fixture_name))
    record[field] = False
    with pytest.raises(
        ValueError, match=f"^review_record_field_type_invalid:{field}$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize(
    ("fixture_name", "field"),
    [
        ("class_draft", "reaction_family_identity_review_decision"),
        ("class_draft", "warhead_rule_topology_review_decision"),
        ("sample_draft", "sample_assignment_review_decision"),
    ],
)
def test_invalid_human_decision_is_rejected(
    request: pytest.FixtureRequest, fixture_name: str, field: str,
) -> None:
    record = dict(request.getfixturevalue(fixture_name))
    record[field] = "approved"
    with pytest.raises(
        ValueError, match=f"^review_record_decision_invalid:{field}$"
    ):
        stage.validate_review_record_schema(record)


def test_invalid_smarts_status_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "approve"
    with pytest.raises(
        ValueError, match="^review_record_SMARTS_status_invalid$"
    ):
        stage.validate_review_record_schema(record)


def test_not_reviewed_with_reviewer_is_rejected(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    record["reviewer_id"] = "human-reviewer"
    with pytest.raises(
        ValueError, match="^not_reviewed_review_metadata_present$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize(
    ("field", "value"),
    [("reviewer_id", "   "), ("review_rationale", "\t")],
)
def test_not_reviewed_with_whitespace_metadata_is_rejected(
    sample_draft: dict[str, object], field: str, value: str,
) -> None:
    record = dict(sample_draft)
    record[field] = value
    with pytest.raises(
        ValueError, match="^not_reviewed_review_metadata_present$"
    ):
        stage.validate_review_record_schema(record)


def test_non_not_reviewed_without_reviewer_is_rejected(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    record["sample_assignment_review_decision"] = "approve"
    record["review_rationale"] = "checked"
    with pytest.raises(
        ValueError, match="^review_decision_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_non_not_reviewed_without_rationale_is_rejected(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    record["sample_assignment_review_decision"] = "revise"
    record["reviewer_id"] = "human-reviewer"
    with pytest.raises(
        ValueError, match="^review_decision_requires_rationale$"
    ):
        stage.validate_review_record_schema(record)


def test_sample_approval_with_whitespace_reviewer_is_rejected(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    record["sample_assignment_review_decision"] = "approve"
    record["reviewer_id"] = "   "
    record["review_rationale"] = "Sample assignment reviewed"
    with pytest.raises(
        ValueError, match="^review_decision_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_sample_approval_with_whitespace_rationale_is_rejected(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    record["sample_assignment_review_decision"] = "approve"
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "\t"
    with pytest.raises(
        ValueError, match="^review_decision_requires_rationale$"
    ):
        stage.validate_review_record_schema(record)


def test_family_approval_with_whitespace_reviewer_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["reaction_family_identity_review_decision"] = "approve"
    record["reviewer_id"] = " \t "
    record["review_rationale"] = "Reaction family reviewed"
    with pytest.raises(
        ValueError, match="^review_decision_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_topology_approval_with_whitespace_rationale_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_rule_topology_review_decision"] = "approve"
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "\t"
    with pytest.raises(
        ValueError, match="^review_decision_requires_rationale$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize(
    "reviewer_id",
    [
        "CODEX",
        "ChatGPT",
        "AUTO",
        "System",
        "SYNTHETIC",
        "Placeholder",
        "UNKNOWN",
        "None",
        " Codex ",
        "\tChatGPT\n",
        " SYSTEM ",
    ],
)
def test_forbidden_reviewer_id_is_rejected_case_insensitively(
    sample_draft: dict[str, object], reviewer_id: str,
) -> None:
    record = dict(sample_draft)
    record["sample_assignment_review_decision"] = "quarantine"
    record["reviewer_id"] = reviewer_id
    record["review_rationale"] = "checked"
    with pytest.raises(ValueError, match="^reviewer_identity_forbidden$"):
        stage.validate_review_record_schema(record)


def test_not_materialized_smarts_must_be_empty(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["candidate_warhead_smarts"] = "[C:1]"
    with pytest.raises(
        ValueError, match="^SMARTS_not_materialized_but_value_present$"
    ):
        stage.validate_review_record_schema(record)


def test_candidate_not_reviewed_with_candidate_and_empty_metadata_is_valid(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "candidate_not_reviewed"
    record["candidate_warhead_smarts"] = "[C:1]"
    assert stage.validate_review_record_schema(record) == "candidate_class"


@pytest.mark.parametrize("status", ["approved", "revised"])
def test_human_reviewed_smarts_status_requires_nonempty_candidate(
    class_draft: dict[str, object], status: str,
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = status
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "SMARTS candidate reviewed"
    with pytest.raises(
        ValueError, match="^SMARTS_status_requires_nonempty_candidate$"
    ):
        stage.validate_review_record_schema(record)


def test_candidate_not_reviewed_without_candidate_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "candidate_not_reviewed"
    with pytest.raises(
        ValueError, match="^SMARTS_status_requires_nonempty_candidate$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize(
    ("status", "candidate_smarts"),
    [
        ("candidate_not_reviewed", "   "),
        ("candidate_not_reviewed", "\t"),
        ("approved", "   "),
        ("revised", "\n"),
    ],
)
def test_candidate_smarts_must_be_meaningful_text(
    class_draft: dict[str, object], status: str, candidate_smarts: str,
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = status
    record["candidate_warhead_smarts"] = candidate_smarts
    if status in {"approved", "revised"}:
        record["reviewer_id"] = "human-reviewer"
        record["review_rationale"] = "SMARTS candidate reviewed"
    with pytest.raises(
        ValueError, match="^SMARTS_status_requires_nonempty_candidate$"
    ):
        stage.validate_review_record_schema(record)


def test_smarts_approved_without_reviewer_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "approved"
    record["candidate_warhead_smarts"] = "[C:1]"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_smarts_approved_with_whitespace_reviewer_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "approved"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "   "
    record["review_rationale"] = "SMARTS candidate approved after review"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_smarts_approved_without_rationale_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "approved"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "human-reviewer"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_rationale$"
    ):
        stage.validate_review_record_schema(record)


def test_smarts_revised_with_whitespace_rationale_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "revised"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "\n"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_rationale$"
    ):
        stage.validate_review_record_schema(record)


def test_smarts_revised_without_reviewer_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "revised"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["review_rationale"] = "SMARTS candidate revised after review"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_smarts_revised_with_human_metadata_is_valid(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "revised"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "SMARTS candidate revised after review"
    assert stage.validate_review_record_schema(record) == "candidate_class"


@pytest.mark.parametrize("candidate_smarts", ["", "[C:1]"])
def test_quarantined_smarts_without_reviewer_is_rejected(
    class_draft: dict[str, object], candidate_smarts: str,
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "quarantined"
    record["candidate_warhead_smarts"] = candidate_smarts
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_quarantined_smarts_with_whitespace_reviewer_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "quarantined"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "\t"
    record["review_rationale"] = "SMARTS candidate quarantined after review"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


@pytest.mark.parametrize("candidate_smarts", ["", "[C:1]"])
def test_quarantined_smarts_with_human_metadata_is_valid(
    class_draft: dict[str, object], candidate_smarts: str,
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "quarantined"
    record["candidate_warhead_smarts"] = candidate_smarts
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "SMARTS candidate quarantined after review"
    assert stage.validate_review_record_schema(record) == "candidate_class"


@pytest.mark.parametrize("candidate_smarts", ["   ", "\t", "\r\n"])
def test_quarantined_whitespace_only_smarts_is_rejected(
    class_draft: dict[str, object], candidate_smarts: str,
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "quarantined"
    record["candidate_warhead_smarts"] = candidate_smarts
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "SMARTS candidate quarantined after review"
    with pytest.raises(
        ValueError, match="^SMARTS_candidate_whitespace_only$"
    ):
        stage.validate_review_record_schema(record)


def test_candidate_not_reviewed_with_metadata_is_rejected(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "candidate_not_reviewed"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "not yet reviewed"
    with pytest.raises(
        ValueError, match="^not_reviewed_review_metadata_present$"
    ):
        stage.validate_review_record_schema(record)


def test_smarts_only_approved_state_requires_metadata(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    assert record["reaction_family_identity_review_decision"] == "not_reviewed"
    assert record["warhead_rule_topology_review_decision"] == "not_reviewed"
    record["warhead_smarts_review_status"] = "approved"
    record["candidate_warhead_smarts"] = "[C:1]"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_reviewer$"
    ):
        stage.validate_review_record_schema(record)


def test_family_approval_with_not_materialized_smarts_uses_decision_metadata(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["reaction_family_identity_review_decision"] = "approve"
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "Reaction family identity approved"
    assert stage.validate_review_record_schema(record) == "candidate_class"


def test_forbidden_reviewer_blocks_smarts_only_approved_state(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "approved"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "ChatGPT"
    record["review_rationale"] = "synthetic"
    with pytest.raises(ValueError, match="^reviewer_identity_forbidden$"):
        stage.validate_review_record_schema(record)


def test_hash_rejects_invalid_smarts_review_metadata(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "approved"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "   "
    record["review_rationale"] = "SMARTS candidate reviewed"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_reviewer$"
    ):
        stage.review_record_sha256(record)


def test_identity_verification_rejects_invalid_smarts_review_metadata(
    class_draft: dict[str, object],
) -> None:
    record = dict(class_draft)
    record["warhead_smarts_review_status"] = "quarantined"
    record["candidate_warhead_smarts"] = "[C:1]"
    record["reviewer_id"] = "human-reviewer"
    record["review_rationale"] = "\n"
    with pytest.raises(
        ValueError, match="^SMARTS_review_status_requires_rationale$"
    ):
        stage.review_record_identity_verified(record)


def test_source_assignment_identity_must_copy_assignment_identity(
    sample_draft: dict[str, object],
) -> None:
    record = dict(sample_draft)
    record["source_assignment_record_sha256"] = "d" * 64
    with pytest.raises(
        ValueError, match="^source_assignment_record_SHA_mismatch$"
    ):
        stage.validate_review_record_schema(record)


def test_canonical_hash_is_input_order_independent_and_does_not_mutate(
    class_draft: dict[str, object],
) -> None:
    original = dict(class_draft)
    reversed_record = dict(reversed(tuple(class_draft.items())))
    digest = stage.review_record_sha256(class_draft)
    assert digest == stage.review_record_sha256(reversed_record)
    assert class_draft == original


def test_digest_self_field_is_the_only_excluded_field(
    sample_draft: dict[str, object],
) -> None:
    digest = stage.review_record_sha256(sample_draft)
    with_populated_digest = dict(sample_draft)
    with_populated_digest["review_record_sha256"] = "0" * 64
    assert stage.review_record_sha256(with_populated_digest) == digest
    assert "review_record_sha256" not in stage.review_record_hash_input(
        with_populated_digest
    )
    assert set(stage.review_record_hash_input(with_populated_digest)) == (
        set(sample_draft) - {"review_record_sha256"}
    )


def test_any_other_formal_field_change_changes_digest(
    sample_draft: dict[str, object],
) -> None:
    digest = stage.review_record_sha256(sample_draft)
    changed = dict(sample_draft)
    changed["review_notes"] = "contract-only synthetic note"
    assert stage.review_record_sha256(changed) != digest


def test_review_record_identity_verification(
    class_draft: dict[str, object],
) -> None:
    assert stage.review_record_identity_verified(class_draft) is False
    populated = dict(class_draft)
    populated["review_record_sha256"] = stage.review_record_sha256(populated)
    assert stage.review_record_identity_verified(populated) is True
    wrong = dict(populated)
    wrong["review_record_sha256"] = "0" * 64
    assert stage.review_record_identity_verified(wrong) is False


def test_public_hash_and_identity_functions_fail_closed_on_invalid_schema(
    class_draft: dict[str, object],
) -> None:
    missing = dict(class_draft)
    del missing["review_notes"]
    with pytest.raises(
        ValueError, match="^class_review_record_field_inventory_mismatch$"
    ):
        stage.review_record_hash_input(missing)
    extra = dict(class_draft)
    extra["timestamp"] = "forbidden"
    with pytest.raises(
        ValueError, match="^class_review_record_field_inventory_mismatch$"
    ):
        stage.review_record_sha256(extra)
    wrong_version = dict(class_draft)
    wrong_version["review_record_version"] = "v0"
    with pytest.raises(ValueError, match="^review_record_version_mismatch$"):
        stage.review_record_identity_verified(wrong_version)


def test_transaction_failure_makes_all_three_core_tables_header_only(
    result: stage.BuildResult,
) -> None:
    policies, classes, samples = stage.transaction_tables(
        ("synthetic_blocker",),
        result.policy_rows,
        result.class_rows,
        result.sample_rows,
    )
    assert policies == classes == samples == ()
    payloads = (
        stage._csv_bytes(stage.POLICY_COLUMNS, policies),
        stage._csv_bytes(stage.CLASS_COLUMNS, classes),
        stage._csv_bytes(stage.SAMPLE_COLUMNS, samples),
    )
    assert all(len(csv_rows(payload)) == 0 for payload in payloads)


def test_exact30_failure_matrix_is_typed_unique_and_fail_closed(
    result: stage.BuildResult,
) -> None:
    baseline = stage.ReviewGateScenario()
    assert len(stage.FAILURE_MUTATIONS) == len(result.failure_rows) == 30
    assert len({row["mutation_signature"] for row in result.failure_rows}) == 30
    for mutation, row in zip(stage.FAILURE_MUTATIONS, result.failure_rows):
        case, field, value, expected = mutation
        assert field in baseline.__dataclass_fields__
        assert type(value) is type(getattr(baseline, field))
        assert value != getattr(baseline, field)
        observed = stage.observe_failure_scenario(
            dataclasses.replace(baseline, **{field: value})
        )
        assert expected in observed
        assert row["failure_case"] == case
        assert row["expected_reason"] == expected
        assert row["expected_reason_verified"] is True
        assert row["fails_closed"] is True
        assert row["review_policy_registry_row_count"] == 0
        assert row["candidate_class_review_readiness_row_count"] == 0
        assert row["sample_assignment_review_readiness_row_count"] == 0
        assert row["role_proposal_generation_ready"] is False
        assert row["mask_materialization_ready"] is False
        assert row["model_integration_ready"] is False
        assert row["training_ready"] is False
        assert row["verified"] is True


def test_manifest_is_truthful_closed_and_has_no_machine_metadata(
    payloads: dict[str, bytes],
) -> None:
    manifest = json.loads(payloads[stage.MANIFEST_FILE])
    expected = {
        "source_count": 12,
        "review_policy_count": 12,
        "candidate_class_count": 7,
        "current11_sample_count": 11,
        "class_review_package_ready_count": 7,
        "sample_review_package_ready_count": 11,
        "family_identity_review_completed_count": 0,
        "rule_topology_review_completed_count": 0,
        "sample_review_completed_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "approved_warhead_smarts_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "failure_mutation_count": 30,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
    }
    for key, value in expected.items():
        assert manifest[key] == value
    assert manifest["review_gate_design_completed"] is True
    assert manifest["ready_for_review_package_materialization"] is True
    for key in (
        "review_package_materialized",
        "human_review_execution_completed",
        "ready_for_human_review_execution",
        "ready_for_role_proposal_generation",
        "ready_for_mask_materialization",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
        "warhead_type_model_head_integrated",
        "warhead_type_loss_integrated",
        "role_annotation_materialized",
        "minimal_seed_materialized",
        "mask_materialized",
        "tensor_materialized",
        "model_changed",
        "training_used",
    ):
        assert manifest[key] is False
    text = payloads[stage.MANIFEST_FILE].decode()
    assert "timestamp" not in text.lower()
    assert str(ROOT) not in text
    assert stage.MANIFEST_FILE not in manifest["output_sha256"]


def test_builder_is_byte_deterministic_and_matches_materialized_exact6(
    payloads: dict[str, bytes],
) -> None:
    assert payloads == stage.build_evidence_payloads(ROOT)
    assert tuple(payloads) == stage.OUTPUT_FILES
    for name, payload in payloads.items():
        assert (ROOT / stage.OUTPUT_ROOT / name).read_bytes() == payload


def test_no_reviewers_decisions_smarts_tensors_heads_losses_or_training(
    payloads: dict[str, bytes],
) -> None:
    class_rows = csv_rows(payloads[stage.CLASS_FILE])
    sample_rows = csv_rows(payloads[stage.SAMPLE_FILE])
    assert all(row["reviewer_id"] == row["review_rationale"] == "" for row in class_rows)
    assert all(row["reviewer_id"] == row["review_rationale"] == "" for row in sample_rows)
    assert all(row["candidate_warhead_smarts"] == "" for row in class_rows)
    assert all(
        row["reaction_family_identity_review_decision"] == "not_reviewed"
        and row["warhead_rule_topology_review_decision"] == "not_reviewed"
        for row in class_rows
    )
    assert all(row["sample_assignment_review_decision"] == "not_reviewed"
               for row in sample_rows)
    manifest = json.loads(payloads[stage.MANIFEST_FILE])
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["training_used"] is False


def test_independent_checker_reconstructs_authorities() -> None:
    path = (
        ROOT / "scripts/"
        "check_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
        "gate_design_v1.py"
    )
    spec = importlib.util.spec_from_file_location("review_gate_checker", path)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    report = checker.check(ROOT, run_lifecycle_matrix=False)
    assert report["source_count"] == 12
    assert report["policy_count"] == 12
    assert report["class_count"] == 7
    assert report["sample_count"] == 11
    assert report["failure_count"] == 30
    assert report["ready_for_training"] is False


def test_exact10_paths_are_safe_unstaged_and_only_authorized_inventory() -> None:
    assert len(stage.EXACT10_PATHS) == len(set(stage.EXACT10_PATHS)) == 10
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    for relative in stage.EXACT10_PATHS:
        target = ROOT / relative
        assert target.exists() and target.is_file() and not target.is_symlink()
        mode = stat.S_IMODE(target.stat(follow_symlinks=False).st_mode)
        assert mode in {0o644, 0o664}
        assert mode & 0o111 == 0
        assert relative.suffix.lower() not in forbidden
        probe = subprocess.run(
            ("git", "cat-file", "-e",
             f"{stage.BASE_COMMIT}:{relative.as_posix()}"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert probe.returncode != 0
    assert subprocess.run(
        ("git", "diff", "--cached", "--name-only"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout == b""
    if stage.validate_execution_boundary_v1(ROOT) == "pre_commit":
        status = subprocess.run(
            ("git", "status", "--short", "--untracked-files=all"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode().splitlines()
        assert set(status) == {f"?? {path.as_posix()}" for path in stage.EXACT10_PATHS}


def test_shared_hermetic_lifecycle_exact4(tmp_path: Path) -> None:
    report = exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=stage.BASE_COMMIT,
        formal_commit_subject=stage.FORMAL_COMMIT_SUBJECT,
        exact_paths=stage.EXACT10_PATHS,
    )
    assert report.cleanup_verified
    assert report.candidate_parent == stage.BASE_COMMIT
    assert report.candidate_subject == stage.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert (
        report.pre_commit.lifecycle,
        report.detached_candidate_post_commit.lifecycle,
        report.formal_main_post_commit_unpushed.lifecycle,
        report.formal_main_post_push.lifecycle,
    ) == (
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    )


def test_isolated_import_has_no_output_or_file_side_effects(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext."
            "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
            "gate_design_v1",
        ),
        cwd=tmp_path,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""
    assert tuple(tmp_path.iterdir()) == ()
