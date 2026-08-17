from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1
    as published_review_packages,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_recovered7_direct_attachment_completed_review_submission_successor_v1
    as successor,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_REVIEW_OWNER = REPO_ROOT / (
    "src/covalent_ext/"
    "covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1.py"
)
PUBLISHED_REVIEW_OWNER_SHA256 = (
    "cfcf09c9d593c1a299192b4d455e05e45b1f916c792352479593459b3562c681"
)
PUBLISHED_EVIDENCE = REPO_ROOT / (
    "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1/"
    "covapie_recovered7_chemistry_review_package_evidence.json"
)


@pytest.fixture(scope="module")
def published_evidence() -> dict[str, object]:
    return json.loads(PUBLISHED_EVIDENCE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def k36_review_class(
    published_evidence: dict[str, object],
) -> dict[str, object]:
    matches = [
        review_class
        for review_class in published_evidence["review_classes"]
        if review_class["review_class_id"] == successor.K36_REVIEW_CLASS_ID_V1
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture(scope="module")
def k36_applicability(
    published_evidence: dict[str, object],
) -> list[dict[str, object]]:
    rows = [
        row
        for row in published_evidence["sample_applicability"]
        if row["review_class_id"] == successor.K36_REVIEW_CLASS_ID_V1
    ]
    assert len(rows) == 5
    return rows


def _retained(review_class: dict[str, object]) -> list[str]:
    return [
        row["atom_id"]
        for row in review_class["chemistry_review_signature"][
            "canonical_model_bound_ligand_heavy_atom_inventory"
        ]
    ]


def _valid_record(review_class: dict[str, object]) -> dict[str, object]:
    record = published_review_packages.make_blank_review_record_v1(review_class)
    active_warhead = list(successor.K36_ACTIVE_WARHEAD_ATOM_IDS_V1)
    record.update(
        {
            "review_status": "COMPLETED",
            "review_scope": "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
            "reviewed_reaction_family_authority_action": (
                "NEW_AUTHORITY_REQUIRED"
            ),
            "reviewed_warhead_rule_authority_action": (
                "NEW_AUTHORITY_REQUIRED"
            ),
            "reviewed_warhead_atom_ids": active_warhead,
            "reviewed_warhead_attachment_atom_id": "C21",
            "reviewed_nonwarhead_boundary_atom_id": "C20",
            "reviewed_attachment_boundary_bond_order": "single",
            "reviewed_scaffold_atom_ids": [
                atom
                for atom in _retained(review_class)
                if atom not in set(active_warhead)
            ],
            "reviewed_linker_atom_ids": [],
            "reviewed_warhead_role_atom_ids": active_warhead,
            "reviewed_minimal_seed_atom_ids": ["C20", "N19"],
            "reviewer_id": "TEST_REVIEWER_K36_DIRECT_V1",
            "review_rationale": (
                "Synthetic completed-record coverage of the approved K36 W1 "
                "direct-attachment scientific decision."
            ),
            "review_notes": "",
        }
    )
    _rehash(record)
    return record


def _rehash(record: dict[str, object]) -> None:
    record["review_record_sha256"] = ""
    record["review_record_sha256"] = (
        published_review_packages.review_record_sha256_v1(record)
    )


def _rehash_applicability(record: dict[str, object]) -> None:
    record["applicability_record_sha256"] = ""
    record["applicability_record_sha256"] = (
        published_review_packages.sample_applicability_record_sha256_v1(record)
    )


def _generic_direct_class_and_applicability(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    review_class = copy.deepcopy(k36_review_class)
    signature = review_class["chemistry_review_signature"]
    signature["ligand_component_id"] = "SYN"
    signature["explicit_covalent_event"]["ligand_component_id"] = "SYN"
    signature_sha256 = (
        published_review_packages.chemistry_review_signature_sha256_v1(
            signature
        )
    )
    review_class["chemistry_review_signature_sha256"] = signature_sha256
    review_class["review_class_id"] = (
        "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_" + signature_sha256.upper()
    )
    applicability = copy.deepcopy(k36_applicability)
    for row in applicability:
        row["review_class_id"] = review_class["review_class_id"]
        row["chemistry_review_signature_sha256"] = signature_sha256
        _rehash_applicability(row)
    return review_class, applicability


def _validate(
    record: dict[str, object],
    review_class: dict[str, object],
    applicability: object,
) -> None:
    successor.validate_completed_direct_attachment_review_record_v1(
        record,
        review_class,
        applicability_records_or_signatures=applicability,
    )


def test_historical_strict_validator_is_byte_unchanged_and_rejects_empty_linker(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    assert hashlib.sha256(PUBLISHED_REVIEW_OWNER.read_bytes()).hexdigest() == (
        PUBLISHED_REVIEW_OWNER_SHA256
    )
    record = _valid_record(k36_review_class)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="ROLE_PARTITION_INVALID:linker_empty",
    ):
        published_review_packages.validate_completed_review_record_v1(
            record,
            k36_review_class,
            applicability_signatures=[
                row["chemistry_review_signature_sha256"]
                for row in k36_applicability
            ],
        )


def test_k36_w1_completed_successor_and_submission_are_exact_and_deterministic(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    record_snapshot = copy.deepcopy(record)
    class_snapshot = copy.deepcopy(k36_review_class)
    applicability_snapshot = copy.deepcopy(k36_applicability)
    _validate(record, k36_review_class, k36_applicability)
    first = successor.compile_recovered7_direct_attachment_review_submission_v1(
        record, k36_review_class, k36_applicability
    )
    second = successor.compile_recovered7_direct_attachment_review_submission_v1(
        record, k36_review_class, k36_applicability
    )

    retained = _retained(k36_review_class)
    assert first == second
    assert record == record_snapshot
    assert k36_review_class == class_snapshot
    assert k36_applicability == applicability_snapshot
    assert tuple(first) == successor.SUBMISSION_FIELDS
    assert first["submission_schema_version"] == successor.SUBMISSION_SCHEMA_VERSION
    assert first["review_class_id"] == successor.K36_REVIEW_CLASS_ID_V1
    assert first["chemistry_review_signature_sha256"] == (
        successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1
    )
    assert tuple(first["review_class_member_identities"]) == (
        successor.K36_MEMBER_IDENTITIES_V1
    )
    assert first["reviewed_warhead_atom_ids"] == ["C21", "O22"]
    assert not set(first["reviewed_warhead_atom_ids"]) & set(
        successor.K36_MASKED_PRECURSOR_PROVENANCE_ATOM_IDS_V1
    )
    assert first["reviewed_scaffold_atom_ids"] == [
        atom for atom in retained if atom not in {"C21", "O22"}
    ]
    assert first["reviewed_linker_atom_ids"] == []
    assert first["reviewed_warhead_role_atom_ids"] == ["C21", "O22"]
    assert (
        len(first["reviewed_scaffold_atom_ids"]),
        len(first["reviewed_linker_atom_ids"]),
        len(first["reviewed_warhead_role_atom_ids"]),
    ) == (27, 0, 2)
    assert first["role_profile"] == (
        direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
    )
    assert first["direct_boundary_semantics"] == {
        "boundary_profile": "DIRECT_SCAFFOLD_WARHEAD_SINGLE_BOUNDARY_V1",
        "boundary_count": 1,
        "scaffold_side_atom_id": "C20",
        "warhead_side_atom_id": "C21",
        "bond_order": "single",
        "linker_present": False,
    }
    assert first["reviewed_minimal_seed_atom_ids"] == ["C20", "N19"]
    assert first["source_review_record_sha256"] == record["review_record_sha256"]
    assert first["reaction_family_authority_creation_required"] is True
    assert first["warhead_rule_authority_creation_required"] is True
    assert first["training_supervision_authority_complete"] is False


def test_k36_w2_precursor_expansion_cannot_replace_frozen_w1(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    record["reviewed_warhead_atom_ids"] = [
        "C21",
        "O1",
        "O2",
        "O22",
        "O3",
        "S1",
    ]
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="K36_W1_FROZEN_FIELD_MISMATCH:reviewed_warhead_atom_ids",
    ):
        _validate(record, k36_review_class, k36_applicability)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (
            lambda record: (
                record["reviewed_scaffold_atom_ids"].remove("C1"),
                record["reviewed_linker_atom_ids"].append("C1"),
            ),
            "K36_W1_FROZEN_FIELD_MISMATCH:reviewed_linker_atom_ids",
        ),
        (
            lambda record: record.update(
                reviewed_nonwarhead_boundary_atom_id="C24"
            ),
            "BOUNDARY_BOND_NOT_IN_GRAPH",
        ),
        (
            lambda record: record.update(
                reviewed_warhead_role_atom_ids=["O22"]
            ),
            "K36_W1_FROZEN_FIELD_MISMATCH:reviewed_warhead_role_atom_ids",
        ),
        (
            lambda record: record.update(
                reviewed_warhead_atom_ids=["C21", "O22", "ZZ"]
            ),
            "WARHEAD_ATOM_SET_OUTSIDE_TOPOLOGY",
        ),
    ),
)
def test_k36_role_and_warhead_mutations_fail_closed(
    mutation: object,
    expected: str,
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    mutation(record)
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match=expected,
    ):
        _validate(record, k36_review_class, k36_applicability)


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    (
        (
            lambda record: record.update(
                reviewed_warhead_atom_ids=["C20", "C21", "O22"],
                reviewed_scaffold_atom_ids=[
                    atom
                    for atom in record["reviewed_scaffold_atom_ids"]
                    if atom != "C20"
                ],
                reviewed_warhead_role_atom_ids=["C20", "C21", "O22"],
                reviewed_warhead_attachment_atom_id="C20",
                reviewed_nonwarhead_boundary_atom_id="C24",
                reviewed_minimal_seed_atom_ids=["C24", "C25"],
            ),
            "multiple_direct_boundaries_in_explicit_graph",
        ),
        (
            lambda record: record.update(
                reviewed_scaffold_atom_ids=[
                    *record["reviewed_scaffold_atom_ids"], "C21"
                ],
                reviewed_warhead_role_atom_ids=["O22"],
            ),
            "reactive_atom_outside_warhead",
        ),
        (
            lambda record: record.update(reviewed_minimal_seed_atom_ids=["C20"]),
            "seed_size_not_2_or_3",
        ),
        (
            lambda record: record.update(
                reviewed_minimal_seed_atom_ids=["C1", "C20", "N19", "O8"]
            ),
            "seed_size_not_2_or_3",
        ),
        (
            lambda record: record.update(
                reviewed_minimal_seed_atom_ids=["C1", "C20"]
            ),
            "seed_disconnected",
        ),
        (
            lambda record: record.update(
                reviewed_minimal_seed_atom_ids=["C17", "N19"]
            ),
            "seed_missing_primary_anchor",
        ),
    ),
)
def test_generic_direct_successor_delegates_boundary_and_seed_failures(
    mutation: object,
    expected_reason: str,
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    review_class, applicability = _generic_direct_class_and_applicability(
        k36_review_class, k36_applicability
    )
    record = _valid_record(review_class)
    mutation(record)
    record["reviewed_scaffold_atom_ids"] = sorted(
        set(record["reviewed_scaffold_atom_ids"]),
        key=lambda value: value.encode("utf-8"),
    )
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match=expected_reason,
    ):
        _validate(record, review_class, applicability)


def test_reusable_scope_requires_actual_complete_published_member_records(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="PUBLISHED_APPLICABILITY_RECORD_REQUIRED",
    ):
        _validate(
            record,
            k36_review_class,
            [successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1] * 5,
        )
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="REUSABLE_SCOPE_MEMBER_COUNT_INCOMPLETE",
    ):
        _validate(record, k36_review_class, k36_applicability[:-1])

    mismatched = copy.deepcopy(k36_applicability)
    mismatched[0]["sample_identity"] = "NOT_A_K36_MEMBER/K36"
    _rehash_applicability(mismatched[0])
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="REUSABLE_SCOPE_MEMBER_IDENTITY_MISMATCH",
    ):
        _validate(record, k36_review_class, mismatched)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    (
        (
            "chemistry_review_signature_sha256",
            "0" * 64,
            "APPLICABILITY_CHEMISTRY_SIGNATURE_MISMATCH",
        ),
        (
            "mechanical_closure_status",
            "MECHANICAL_CLOSURE_FAIL",
            "APPLICABILITY_REQUIRED_PASS_MISSING:mechanical_closure_status",
        ),
        (
            "event_mapping_status",
            "EVENT_MAPPING_FAIL",
            "APPLICABILITY_REQUIRED_PASS_MISSING:event_mapping_status",
        ),
        (
            "exact10_status",
            "EXACT10_FAIL",
            "APPLICABILITY_REQUIRED_PASS_MISSING:exact10_status",
        ),
        (
            "pocket_status",
            "POCKET_FAIL",
            "APPLICABILITY_REQUIRED_PASS_MISSING:pocket_status",
        ),
        (
            "sample_matches_review_class_signature",
            False,
            "APPLICABILITY_SIGNATURE_MATCH_NOT_PASS",
        ),
    ),
)
def test_each_reusable_applicability_pass_is_required(
    field: str,
    value: object,
    expected: str,
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    applicability = copy.deepcopy(k36_applicability)
    applicability[0][field] = value
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match=expected,
    ):
        _validate(record, k36_review_class, applicability)


def test_actual_class_signature_content_is_sha_bound(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    mutated_class = copy.deepcopy(k36_review_class)
    mutated_class["chemistry_review_signature"]["semantic_topology_sha256"] = (
        "0" * 64
    )
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="CHEMISTRY_REVIEW_SIGNATURE_CONTENT_SHA256_MISMATCH",
    ):
        _validate(record, mutated_class, k36_applicability)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    (
        ("reviewer_id", "", "REVIEWER_ID_REQUIRED"),
        ("reviewer_id", "Codex", "FORBIDDEN_REVIEWER_ID"),
        ("review_rationale", "", "REVIEW_RATIONALE_REQUIRED"),
        ("review_notes", "   ", "REVIEW_NOTES_NOT_MEANINGFUL"),
    ),
)
def test_human_identity_rationale_and_notes_remain_mandatory(
    field: str,
    value: str,
    expected: str,
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    record[field] = value
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match=expected,
    ):
        _validate(record, k36_review_class, k36_applicability)


def test_completed_record_sha_is_required_exact_and_mutation_sensitive(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    record["review_record_sha256"] = ""
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="COMPLETED_REVIEW_SHA_REQUIRED",
    ):
        _validate(record, k36_review_class, k36_applicability)

    record = _valid_record(k36_review_class)
    record["review_record_sha256"] = "0" * 64
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="COMPLETED_REVIEW_SHA_MISMATCH",
    ):
        _validate(record, k36_review_class, k36_applicability)

    record = _valid_record(k36_review_class)
    record["review_rationale"] += " Mutated after canonical hashing."
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="COMPLETED_REVIEW_SHA_MISMATCH",
    ):
        _validate(record, k36_review_class, k36_applicability)


def test_authority_action_semantics_are_preserved(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    record["reviewed_reaction_family_id"] = "MUST_NOT_EXIST_YET"
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="NEW_AUTHORITY_ID_MUST_BE_BLANK:reviewed_reaction_family_id",
    ):
        _validate(record, k36_review_class, k36_applicability)

    review_class, applicability = _generic_direct_class_and_applicability(
        k36_review_class, k36_applicability
    )
    record = _valid_record(review_class)
    record["reviewed_reaction_family_authority_action"] = (
        "USE_EXISTING_REVIEWED_ID"
    )
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="EXISTING_AUTHORITY_ID_REQUIRED:reviewed_reaction_family_id",
    ):
        _validate(record, review_class, applicability)

    record["reviewed_reaction_family_id"] = "SYNTHETIC_FAMILY_V1"
    record["reviewed_warhead_rule_authority_action"] = (
        "USE_EXISTING_REVIEWED_ID"
    )
    record["reviewed_warhead_rule_id"] = "SYNTHETIC_RULE_V1"
    _rehash(record)
    _validate(record, review_class, applicability)
    submission = successor.compile_recovered7_direct_attachment_review_submission_v1(
        record, review_class, applicability
    )
    assert submission["reaction_family_authority_creation_required"] is False
    assert submission["warhead_rule_authority_creation_required"] is False
    assert submission["training_supervision_authority_complete"] is False


def test_compilation_does_not_imply_ingestion_or_effective_authority_closure(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    review_class, applicability = _generic_direct_class_and_applicability(
        k36_review_class, k36_applicability
    )
    record = _valid_record(review_class)
    record["reviewed_reaction_family_authority_action"] = (
        "USE_EXISTING_REVIEWED_ID"
    )
    record["reviewed_reaction_family_id"] = "SYNTHETIC_FAMILY_V1"
    record["reviewed_warhead_rule_authority_action"] = (
        "USE_EXISTING_REVIEWED_ID"
    )
    record["reviewed_warhead_rule_id"] = "SYNTHETIC_RULE_V1"
    _rehash(record)

    submission = successor.compile_recovered7_direct_attachment_review_submission_v1(
        record, review_class, applicability
    )
    assert submission["reaction_family_authority_creation_required"] is False
    assert submission["warhead_rule_authority_creation_required"] is False
    assert submission["training_supervision_authority_complete"] is False


def test_sample_bound_scope_is_member_bound_and_cannot_propagate(
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    review_class, applicability = _generic_direct_class_and_applicability(
        k36_review_class, k36_applicability
    )
    record = _valid_record(review_class)
    selected = review_class["member_sample_identities"][0]
    record["review_scope"] = "SAMPLE_BOUND_ONLY"
    record["reviewed_sample_bound_member_identity"] = selected
    selected_applicability = [
        row for row in applicability if row["sample_identity"] == selected
    ]
    _rehash(record)
    _validate(record, review_class, selected_applicability)

    record["reviewed_sample_bound_member_identity"] = "NOT_A_MEMBER/SYN"
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="SAMPLE_BOUND_MEMBER_INVALID",
    ):
        _validate(record, review_class, selected_applicability)

    record["reviewed_sample_bound_member_identity"] = selected
    _rehash(record)
    with pytest.raises(
        published_review_packages.ReviewPackageValidationError,
        match="SAMPLE_BOUND_CROSS_SAMPLE_PROPAGATION_FORBIDDEN",
    ):
        _validate(record, review_class, applicability)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record: record.update(reviewer_id=""),
        lambda record: record.update(reviewed_linker_atom_ids=["C1"]),
        lambda record: record.update(review_record_sha256="0" * 64),
    ),
)
def test_submission_compiler_refuses_invalid_completed_records(
    mutation: object,
    k36_review_class: dict[str, object],
    k36_applicability: list[dict[str, object]],
) -> None:
    record = _valid_record(k36_review_class)
    mutation(record)
    if record["review_record_sha256"] != "0" * 64:
        _rehash(record)
    with pytest.raises(published_review_packages.ReviewPackageValidationError):
        successor.compile_recovered7_direct_attachment_review_submission_v1(
            record, k36_review_class, k36_applicability
        )
