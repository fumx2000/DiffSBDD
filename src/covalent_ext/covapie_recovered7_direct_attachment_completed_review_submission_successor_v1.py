"""Validate and compile completed recovered7 direct-attachment reviews.

This additive successor preserves the published recovered7 review-record
schema, hashing convention, human-review requirements, and authority-action
semantics.  It replaces only the historical strict nonempty-linker role check
with the published direct-attachment optional-linker runtime.  It creates no
authority and performs no ingestion or state mutation.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1
    as published_review_packages,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)


__all__ = (
    "SUBMISSION_SCHEMA_VERSION",
    "SUBMISSION_FIELDS",
    "K36_REVIEW_CLASS_ID_V1",
    "K36_CHEMISTRY_SIGNATURE_SHA256_V1",
    "K36_MEMBER_IDENTITIES_V1",
    "K36_ACTIVE_WARHEAD_ATOM_IDS_V1",
    "K36_MASKED_PRECURSOR_PROVENANCE_ATOM_IDS_V1",
    "validate_completed_direct_attachment_review_record_v1",
    "compile_recovered7_direct_attachment_review_submission_v1",
)


SUBMISSION_SCHEMA_VERSION = (
    "covapie_recovered7_direct_attachment_review_submission_v1"
)

K36_CHEMISTRY_SIGNATURE_SHA256_V1 = (
    "83e9c7b9d43444d7e50fbfd7e6c3dafef5e0dc92cf1a7c571e3f4e3fe4e08d92"
)
K36_REVIEW_CLASS_ID_V1 = (
    "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
    + K36_CHEMISTRY_SIGNATURE_SHA256_V1.upper()
)
K36_MEMBER_IDENTITIES_V1 = (
    "4DCD/K36",
    "4F49/K36",
    "5WKJ/K36",
    "6L70/K36",
    "6WTT/K36",
)
K36_ACTIVE_WARHEAD_ATOM_IDS_V1 = ("C21", "O22")
K36_MASKED_PRECURSOR_PROVENANCE_ATOM_IDS_V1 = ("O1", "O2", "O3", "S1")

_K36_REVIEW_SCOPE_V1 = "EXACT_CHEMISTRY_SIGNATURE_REUSABLE"
_K36_WARHEAD_ATTACHMENT_ATOM_ID_V1 = "C21"
_K36_NONWARHEAD_BOUNDARY_ATOM_ID_V1 = "C20"
_K36_ATTACHMENT_BOUNDARY_BOND_ORDER_V1 = "single"
_K36_MINIMAL_SEED_ATOM_IDS_V1 = ("C20", "N19")

_CLASS_ID_PREFIX = "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
_REUSABLE_SCOPE = "EXACT_CHEMISTRY_SIGNATURE_REUSABLE"
_SAMPLE_BOUND_SCOPE = "SAMPLE_BOUND_ONLY"
_DIRECT_REVIEW_SCOPES = (_REUSABLE_SCOPE, _SAMPLE_BOUND_SCOPE)

_APPLICABILITY_REQUIRED_VALUES = {
    "event_mapping_status": "EXACT_EVENT_ENDPOINT_MAPPING_PASS",
    "exact10_status": "EXACT10_PASS",
    "pocket_status": "POCKET_PASS",
    "mechanical_closure_status": "MECHANICAL_CLOSURE_PASS",
    "applicability_status": (
        "EXACT_CHEMISTRY_SIGNATURE_MATCH_AND_MECHANICAL_CLOSURE_PASS"
    ),
}

SUBMISSION_FIELDS = (
    "submission_schema_version",
    "review_record_version",
    "review_class_id",
    "chemistry_review_signature_sha256",
    "review_class_member_count",
    "review_class_member_identities",
    "review_scope",
    "reviewed_sample_bound_member_identity",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "reviewed_reaction_family_authority_action",
    "reviewed_reaction_family_id",
    "reviewed_warhead_rule_authority_action",
    "reviewed_warhead_rule_id",
    "reaction_family_authority_creation_required",
    "warhead_rule_authority_creation_required",
    "training_supervision_authority_complete",
    "reviewed_warhead_atom_semantics",
    "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order",
    "role_profile",
    "reviewed_scaffold_atom_ids",
    "reviewed_linker_atom_ids",
    "reviewed_warhead_role_atom_ids",
    "reviewed_minimal_seed_atom_ids",
    "direct_boundary_semantics",
    "source_review_record_sha256",
)


ReviewPackageValidationError = (
    published_review_packages.ReviewPackageValidationError
)


def _fail(reason: str) -> None:
    raise ReviewPackageValidationError(reason)


def _meaningful(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _validate_review_class_v1(review_class: object) -> Mapping[str, Any]:
    if not isinstance(review_class, Mapping):
        _fail("REVIEW_CLASS_MAPPING_REQUIRED")
    required = (
        "review_class_id",
        "chemistry_review_signature_sha256",
        "chemistry_review_signature",
        "member_sample_count",
        "member_sample_identities",
    )
    if any(field not in review_class for field in required):
        _fail("REVIEW_CLASS_FIELD_MISSING")

    class_id = review_class["review_class_id"]
    declared_signature_sha256 = review_class[
        "chemistry_review_signature_sha256"
    ]
    member_count = review_class["member_sample_count"]
    member_identities = review_class["member_sample_identities"]
    if (
        type(class_id) is not str
        or type(declared_signature_sha256) is not str
        or type(member_count) is not int
        or member_count < 1
        or type(member_identities) is not list
        or any(type(identity) is not str for identity in member_identities)
        or member_identities
        != sorted(member_identities, key=lambda value: value.encode("utf-8"))
        or len(member_identities) != len(set(member_identities))
        or len(member_identities) != member_count
    ):
        _fail("REVIEW_CLASS_IDENTITY_FIELDS_INVALID")
    if class_id != _CLASS_ID_PREFIX + declared_signature_sha256.upper():
        _fail("REVIEW_CLASS_ID_NOT_SIGNATURE_BOUND")

    try:
        actual_signature_sha256 = (
            published_review_packages.chemistry_review_signature_sha256_v1(
                review_class["chemistry_review_signature"]
            )
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ReviewPackageValidationError(
            "CHEMISTRY_REVIEW_SIGNATURE_CONTENT_INVALID"
        ) from error
    if actual_signature_sha256 != declared_signature_sha256:
        _fail("CHEMISTRY_REVIEW_SIGNATURE_CONTENT_SHA256_MISMATCH")
    return review_class


def _validate_one_applicability_record_v1(
    applicability: object,
    *,
    review_class_id: str,
    chemistry_signature_sha256: str,
) -> str:
    if not isinstance(applicability, Mapping):
        _fail("PUBLISHED_APPLICABILITY_RECORD_REQUIRED")
    required = (
        "sample_identity",
        "review_class_id",
        "chemistry_review_signature_sha256",
        "sample_matches_review_class_signature",
        "event_mapping_status",
        "exact10_status",
        "pocket_status",
        "mechanical_closure_status",
        "applicability_status",
        "applicability_record_sha256",
    )
    if any(field not in applicability for field in required):
        _fail("APPLICABILITY_RECORD_FIELD_MISSING")
    identity = applicability["sample_identity"]
    if not _meaningful(identity):
        _fail("APPLICABILITY_SAMPLE_IDENTITY_INVALID")
    if applicability["review_class_id"] != review_class_id:
        _fail("APPLICABILITY_REVIEW_CLASS_ID_MISMATCH")
    if (
        applicability["chemistry_review_signature_sha256"]
        != chemistry_signature_sha256
    ):
        _fail("APPLICABILITY_CHEMISTRY_SIGNATURE_MISMATCH")
    if applicability["sample_matches_review_class_signature"] is not True:
        _fail("APPLICABILITY_SIGNATURE_MATCH_NOT_PASS")
    for field, required_value in _APPLICABILITY_REQUIRED_VALUES.items():
        if applicability[field] != required_value:
            _fail(f"APPLICABILITY_REQUIRED_PASS_MISSING:{field}")
    declared_sha256 = applicability["applicability_record_sha256"]
    if not _meaningful(declared_sha256):
        _fail("APPLICABILITY_RECORD_SHA256_REQUIRED")
    try:
        actual_sha256 = (
            published_review_packages.sample_applicability_record_sha256_v1(
                applicability
            )
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ReviewPackageValidationError(
            "APPLICABILITY_RECORD_SHA256_INVALID"
        ) from error
    if declared_sha256 != actual_sha256:
        _fail("APPLICABILITY_RECORD_SHA256_MISMATCH")
    return identity


def _validate_applicability_boundary_v1(
    record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    applicability_records_or_signatures: object,
) -> tuple[str, ...]:
    if type(applicability_records_or_signatures) not in (tuple, list):
        _fail("APPLICABILITY_RECORD_SEQUENCE_REQUIRED")
    applicability = tuple(applicability_records_or_signatures)
    review_class_id = review_class["review_class_id"]
    signature_sha256 = review_class["chemistry_review_signature_sha256"]

    if record["review_scope"] == _REUSABLE_SCOPE:
        if not applicability:
            _fail("REUSABLE_SCOPE_APPLICABILITY_RECORDS_REQUIRED")
        identities = tuple(
            _validate_one_applicability_record_v1(
                item,
                review_class_id=review_class_id,
                chemistry_signature_sha256=signature_sha256,
            )
            for item in applicability
        )
        expected_identities = tuple(record["review_class_member_identities"])
        if len(identities) != len(expected_identities):
            _fail("REUSABLE_SCOPE_MEMBER_COUNT_INCOMPLETE")
        if len(identities) != len(set(identities)):
            _fail("REUSABLE_SCOPE_MEMBER_IDENTITY_DUPLICATE")
        if set(identities) != set(expected_identities):
            _fail("REUSABLE_SCOPE_MEMBER_IDENTITY_MISMATCH")
        return tuple(signature_sha256 for _ in identities)

    selected_identity = record["reviewed_sample_bound_member_identity"]
    if selected_identity not in record["review_class_member_identities"]:
        _fail("SAMPLE_BOUND_MEMBER_INVALID")
    if not applicability:
        return ()
    if len(applicability) != 1:
        _fail("SAMPLE_BOUND_CROSS_SAMPLE_PROPAGATION_FORBIDDEN")
    identity = _validate_one_applicability_record_v1(
        applicability[0],
        review_class_id=review_class_id,
        chemistry_signature_sha256=signature_sha256,
    )
    if identity != selected_identity:
        _fail("SAMPLE_BOUND_APPLICABILITY_IDENTITY_MISMATCH")
    return ()


def _validate_active_warhead_v1(
    record: Mapping[str, Any], review_class: Mapping[str, Any]
) -> None:
    signature = review_class["chemistry_review_signature"]
    try:
        topology_atoms = tuple(
            row["atom_id"] for row in signature["topology_heavy_atom_inventory"]
        )
        bonds = signature[
            "canonical_internal_heavy_heavy_bond_graph_with_bond_orders"
        ]
        reactive_atom = signature["reactive_ligand_atom"]
    except (KeyError, TypeError) as error:
        raise ReviewPackageValidationError(
            "CHEMISTRY_REVIEW_SIGNATURE_TOPOLOGY_INVALID"
        ) from error
    topology_set = set(topology_atoms)
    warhead_atoms = record["reviewed_warhead_atom_ids"]
    if not warhead_atoms or not set(warhead_atoms) <= topology_set:
        _fail("WARHEAD_ATOM_SET_OUTSIDE_TOPOLOGY")
    if reactive_atom not in warhead_atoms:
        _fail("REACTIVE_ATOM_OUTSIDE_WARHEAD_ATOM_SET")

    attachment = record["reviewed_warhead_attachment_atom_id"]
    nonwarhead = record["reviewed_nonwarhead_boundary_atom_id"]
    order = record["reviewed_attachment_boundary_bond_order"]
    if attachment not in topology_set or nonwarhead not in topology_set:
        _fail("BOUNDARY_ATOM_NOT_IN_GRAPH")
    if attachment not in warhead_atoms:
        _fail("WARHEAD_ATTACHMENT_OUTSIDE_WARHEAD_SET")
    if nonwarhead in warhead_atoms or attachment == nonwarhead:
        _fail("NONWARHEAD_BOUNDARY_IN_WARHEAD_SET")
    boundary = published_review_packages._canonical_bond(
        attachment, nonwarhead, order
    )
    if boundary not in bonds:
        _fail("BOUNDARY_BOND_NOT_IN_GRAPH")


def _validate_frozen_k36_w1_v1(
    record: Mapping[str, Any], review_class: Mapping[str, Any]
) -> None:
    class_id = review_class["review_class_id"]
    signature_sha256 = review_class["chemistry_review_signature_sha256"]
    if (
        class_id != K36_REVIEW_CLASS_ID_V1
        and signature_sha256 != K36_CHEMISTRY_SIGNATURE_SHA256_V1
    ):
        return
    if (
        class_id != K36_REVIEW_CLASS_ID_V1
        or signature_sha256 != K36_CHEMISTRY_SIGNATURE_SHA256_V1
    ):
        _fail("K36_REVIEW_CLASS_IDENTITY_MISMATCH")
    if tuple(review_class["member_sample_identities"]) != K36_MEMBER_IDENTITIES_V1:
        _fail("K36_REUSABLE_MEMBER_IDENTITIES_MISMATCH")
    expected_values = {
        "review_scope": _K36_REVIEW_SCOPE_V1,
        "reviewed_warhead_atom_ids": list(K36_ACTIVE_WARHEAD_ATOM_IDS_V1),
        "reviewed_warhead_attachment_atom_id": (
            _K36_WARHEAD_ATTACHMENT_ATOM_ID_V1
        ),
        "reviewed_nonwarhead_boundary_atom_id": (
            _K36_NONWARHEAD_BOUNDARY_ATOM_ID_V1
        ),
        "reviewed_attachment_boundary_bond_order": (
            _K36_ATTACHMENT_BOUNDARY_BOND_ORDER_V1
        ),
        "reviewed_linker_atom_ids": [],
        "reviewed_warhead_role_atom_ids": list(
            K36_ACTIVE_WARHEAD_ATOM_IDS_V1
        ),
        "reviewed_minimal_seed_atom_ids": list(_K36_MINIMAL_SEED_ATOM_IDS_V1),
        "reviewed_reaction_family_authority_action": "NEW_AUTHORITY_REQUIRED",
        "reviewed_reaction_family_id": "",
        "reviewed_warhead_rule_authority_action": "NEW_AUTHORITY_REQUIRED",
        "reviewed_warhead_rule_id": "",
    }
    for field, expected in expected_values.items():
        if record[field] != expected:
            _fail(f"K36_W1_FROZEN_FIELD_MISMATCH:{field}")
    if set(record["reviewed_warhead_atom_ids"]) & set(
        K36_MASKED_PRECURSOR_PROVENANCE_ATOM_IDS_V1
    ):
        _fail("K36_MASKED_PRECURSOR_IN_ACTIVE_WARHEAD")
    retained = [
        row["atom_id"]
        for row in review_class["chemistry_review_signature"][
            "canonical_model_bound_ligand_heavy_atom_inventory"
        ]
    ]
    expected_scaffold = [
        atom
        for atom in retained
        if atom not in set(K36_ACTIVE_WARHEAD_ATOM_IDS_V1)
    ]
    if record["reviewed_scaffold_atom_ids"] != expected_scaffold:
        _fail("K36_W1_SCAFFOLD_NOT_EXACT_RETAINED_COMPLEMENT")


def validate_completed_direct_attachment_review_record_v1(
    record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    *,
    applicability_records_or_signatures: object,
) -> None:
    """Fail closed unless a completed direct-attachment record is valid.

    Reusable scope requires complete SHA-bound published applicability records;
    a caller-supplied sequence of repeated signature strings is insufficient.
    """

    published_review_packages.validate_review_record_schema_v1(record)
    validated_class = _validate_review_class_v1(review_class)
    if record["review_status"] != "COMPLETED":
        _fail("COMPLETED_REVIEW_STATUS_REQUIRED")
    if record["review_scope"] not in _DIRECT_REVIEW_SCOPES:
        _fail("COMPLETED_DIRECT_REVIEW_SCOPE_REQUIRED")

    class_bindings = (
        ("review_class_id", "review_class_id"),
        (
            "chemistry_review_signature_sha256",
            "chemistry_review_signature_sha256",
        ),
        ("review_class_member_count", "member_sample_count"),
        ("review_class_member_identities", "member_sample_identities"),
    )
    for record_field, class_field in class_bindings:
        if record[record_field] != validated_class[class_field]:
            _fail(f"REVIEW_CLASS_BINDING_MISMATCH:{record_field}")

    if not _meaningful(record["reviewer_id"]):
        _fail("REVIEWER_ID_REQUIRED")
    if (
        record["reviewer_id"].strip().casefold()
        in published_review_packages._FORBIDDEN_REVIEWER_IDS
    ):
        _fail("FORBIDDEN_REVIEWER_ID")
    if not _meaningful(record["review_rationale"]):
        _fail("REVIEW_RATIONALE_REQUIRED")
    if record["review_notes"] and not _meaningful(record["review_notes"]):
        _fail("REVIEW_NOTES_NOT_MEANINGFUL")

    if record["review_scope"] == _REUSABLE_SCOPE:
        if record["reviewed_sample_bound_member_identity"]:
            _fail("REUSABLE_SCOPE_SAMPLE_BINDING_FORBIDDEN")
    elif (
        record["reviewed_sample_bound_member_identity"]
        not in record["review_class_member_identities"]
    ):
        _fail("SAMPLE_BOUND_MEMBER_INVALID")

    published_review_packages._validate_authority_action(
        record,
        "reviewed_reaction_family_authority_action",
        "reviewed_reaction_family_id",
    )
    published_review_packages._validate_authority_action(
        record,
        "reviewed_warhead_rule_authority_action",
        "reviewed_warhead_rule_id",
    )
    _validate_active_warhead_v1(record, validated_class)
    _validate_frozen_k36_w1_v1(record, validated_class)

    applicability_signatures = _validate_applicability_boundary_v1(
        record,
        validated_class,
        applicability_records_or_signatures,
    )
    role_validation = (
        direct_runtime.validate_direct_attachment_review_role_payload_v1(
            review_record=record,
            chemistry_review_signature=validated_class[
                "chemistry_review_signature"
            ],
            expected_review_signature_sha256=validated_class[
                "chemistry_review_signature_sha256"
            ],
            applicability_signatures=applicability_signatures,
        )
    )
    if not role_validation.valid:
        _fail("DIRECT_REVIEW_ROLE_PAYLOAD_INVALID:" + ";".join(role_validation.reasons))

    if not record["review_record_sha256"]:
        _fail("COMPLETED_REVIEW_SHA_REQUIRED")
    if (
        record["review_record_sha256"]
        != published_review_packages.review_record_sha256_v1(record)
    ):
        _fail("COMPLETED_REVIEW_SHA_MISMATCH")


def compile_recovered7_direct_attachment_review_submission_v1(
    record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    sample_applicability: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compile one valid decision into a deterministic plain-data carrier."""

    validate_completed_direct_attachment_review_record_v1(
        record,
        review_class,
        applicability_records_or_signatures=sample_applicability,
    )
    reaction_family_creation_required = (
        record["reviewed_reaction_family_authority_action"]
        == "NEW_AUTHORITY_REQUIRED"
    )
    warhead_rule_creation_required = (
        record["reviewed_warhead_rule_authority_action"]
        == "NEW_AUTHORITY_REQUIRED"
    )
    submission = {
        "submission_schema_version": SUBMISSION_SCHEMA_VERSION,
        "review_record_version": record["review_record_version"],
        "review_class_id": record["review_class_id"],
        "chemistry_review_signature_sha256": record[
            "chemistry_review_signature_sha256"
        ],
        "review_class_member_count": record["review_class_member_count"],
        "review_class_member_identities": list(
            record["review_class_member_identities"]
        ),
        "review_scope": record["review_scope"],
        "reviewed_sample_bound_member_identity": record[
            "reviewed_sample_bound_member_identity"
        ],
        "reviewer_id": record["reviewer_id"],
        "review_rationale": record["review_rationale"],
        "review_notes": record["review_notes"],
        "reviewed_reaction_family_authority_action": record[
            "reviewed_reaction_family_authority_action"
        ],
        "reviewed_reaction_family_id": record[
            "reviewed_reaction_family_id"
        ],
        "reviewed_warhead_rule_authority_action": record[
            "reviewed_warhead_rule_authority_action"
        ],
        "reviewed_warhead_rule_id": record["reviewed_warhead_rule_id"],
        "reaction_family_authority_creation_required": (
            reaction_family_creation_required
        ),
        "warhead_rule_authority_creation_required": (
            warhead_rule_creation_required
        ),
        # Submission compilation never proves effective training-supervision
        # authority completeness; that belongs to a later creation/ingestion owner.
        "training_supervision_authority_complete": False,
        "reviewed_warhead_atom_semantics": (
            "REACTION_COMPETENT_ACTIVE_WARHEAD_V1"
        ),
        "reviewed_warhead_atom_ids": list(record["reviewed_warhead_atom_ids"]),
        "reviewed_warhead_attachment_atom_id": record[
            "reviewed_warhead_attachment_atom_id"
        ],
        "reviewed_nonwarhead_boundary_atom_id": record[
            "reviewed_nonwarhead_boundary_atom_id"
        ],
        "reviewed_attachment_boundary_bond_order": record[
            "reviewed_attachment_boundary_bond_order"
        ],
        "role_profile": direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "reviewed_scaffold_atom_ids": list(record["reviewed_scaffold_atom_ids"]),
        "reviewed_linker_atom_ids": list(record["reviewed_linker_atom_ids"]),
        "reviewed_warhead_role_atom_ids": list(
            record["reviewed_warhead_role_atom_ids"]
        ),
        "reviewed_minimal_seed_atom_ids": list(
            record["reviewed_minimal_seed_atom_ids"]
        ),
        "direct_boundary_semantics": {
            "boundary_profile": "DIRECT_SCAFFOLD_WARHEAD_SINGLE_BOUNDARY_V1",
            "boundary_count": 1,
            "scaffold_side_atom_id": record[
                "reviewed_nonwarhead_boundary_atom_id"
            ],
            "warhead_side_atom_id": record[
                "reviewed_warhead_attachment_atom_id"
            ],
            "bond_order": record["reviewed_attachment_boundary_bond_order"],
            "linker_present": False,
        },
        "source_review_record_sha256": record["review_record_sha256"],
    }
    if tuple(submission) != SUBMISSION_FIELDS:
        _fail("SUBMISSION_FIELD_INVENTORY_INVALID")
    return submission
