from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

import pytest

from covalent_ext import (
    covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1
    as published_review_packages,
)
from covalent_ext import (
    covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1
    as authority_creator,
)
from covalent_ext import (
    covapie_k36_w1_recovered7_authority_ingestion_and_effective_supervision_successor_v1
    as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = REPO_ROOT.parent / "covapie-state"
K36_STATE = STATE_ROOT / (
    "manual-review/recovered7-targeted-chemistry-review-v1/"
    "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
    "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92"
)
COMPLETED_REVIEW_PATH = K36_STATE / "completed_review_record.csv"
COMPILED_SUBMISSION_PATH = (
    K36_STATE / "compiled_direct_attachment_review_submission_v1.json"
)
REACTION_FAMILY_AUTHORITY_PATH = (
    K36_STATE / "reaction_family_authority_v1.json"
)
WARHEAD_RULE_AUTHORITY_PATH = K36_STATE / "warhead_rule_authority_v1.json"
PUBLISHED_EVIDENCE_PATH = REPO_ROOT / (
    "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1/"
    "covapie_recovered7_chemistry_review_package_evidence.json"
)
CREATOR_PATH = REPO_ROOT / (
    "src/covalent_ext/"
    "covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1.py"
)

EXPECTED_MEMBERS = (
    "4DCD/K36",
    "4F49/K36",
    "5WKJ/K36",
    "6L70/K36",
    "6WTT/K36",
)
EXPECTED_REVIEW_CLASS_ID = (
    "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
    "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92"
)
EXPECTED_CHEMISTRY_SIGNATURE = (
    "83e9c7b9d43444d7e50fbfd7e6c3dafef5e0dc92cf1a7c571e3f4e3fe4e08d92"
)
EXPECTED_FILE_SHA256 = {
    COMPLETED_REVIEW_PATH: (
        "4e64742c6bfc585e4ef9dd662a31ee7f35df9bf2cd3d305452647bb86392956b"
    ),
    COMPILED_SUBMISSION_PATH: (
        "0fff58cdd0fdaa12c8e41376de76e0edf76b72c8bd43a08045a04681dc6ea73c"
    ),
    REACTION_FAMILY_AUTHORITY_PATH: (
        "5eb39ac01770dbb8721a48d7ae6bf77fc6cb07493ca00a0eb5756ebf10921461"
    ),
    WARHEAD_RULE_AUTHORITY_PATH: (
        "1b8927693386aa8c72fed8677d59bdb3b5b56d4e89a09d88a908341fec0a19b2"
    ),
    CREATOR_PATH: (
        "7c0f68d298fd80d6427126cf6148af7593c18a5163f2aa8a7b3fa5fe1c8789e0"
    ),
}
_JSON_LIST_FIELDS = (
    "review_class_member_identities",
    "reviewed_warhead_atom_ids",
    "reviewed_scaffold_atom_ids",
    "reviewed_linker_atom_ids",
    "reviewed_warhead_role_atom_ids",
    "reviewed_minimal_seed_atom_ids",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def completed_review_record() -> dict[str, Any]:
    with COMPLETED_REVIEW_PATH.open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        record: dict[str, Any] = dict(next(csv.DictReader(stream)))
    for field in _JSON_LIST_FIELDS:
        record[field] = json.loads(record[field])
    record["review_class_member_count"] = int(
        record["review_class_member_count"]
    )
    return record


@pytest.fixture(scope="module")
def published_evidence() -> dict[str, Any]:
    return json.loads(PUBLISHED_EVIDENCE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def review_class(published_evidence: dict[str, Any]) -> dict[str, Any]:
    matches = [
        value
        for value in published_evidence["review_classes"]
        if value["review_class_id"] == EXPECTED_REVIEW_CLASS_ID
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture(scope="module")
def sample_applicability(
    published_evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    matches = [
        value
        for value in published_evidence["sample_applicability"]
        if value["review_class_id"] == EXPECTED_REVIEW_CLASS_ID
    ]
    assert len(matches) == 5
    return matches


@pytest.fixture(scope="module")
def compiled_submission() -> dict[str, Any]:
    return json.loads(COMPILED_SUBMISSION_PATH.read_text(encoding="utf-8"))


def _real_baseline_source_payloads() -> dict[str, bytes]:
    payloads = {}
    for source in authority_creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1:
        path = REPO_ROOT.parent / source["source_path"]
        if source["source_path"].startswith("data/"):
            path = REPO_ROOT / source["source_path"]
        payloads[source["source_path"]] = path.read_bytes()
    return payloads


def _authority_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _reverse_mapping_order(value: Any) -> Any:
    if type(value) is dict:
        return {
            key: _reverse_mapping_order(item)
            for key, item in reversed(tuple(value.items()))
        }
    if type(value) is list:
        return [_reverse_mapping_order(item) for item in value]
    return value


def _build(
    completed_review_record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    sample_applicability: list[dict[str, Any]],
    compiled_submission: Mapping[str, Any],
    *,
    reaction_family_authority: bytes | None = None,
    warhead_rule_authority: bytes | None = None,
    baseline_source_payloads: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    if reaction_family_authority is None:
        reaction_family_authority = REACTION_FAMILY_AUTHORITY_PATH.read_bytes()
    if warhead_rule_authority is None:
        warhead_rule_authority = WARHEAD_RULE_AUTHORITY_PATH.read_bytes()
    if baseline_source_payloads is None:
        baseline_source_payloads = _real_baseline_source_payloads()
    return owner.build_covapie_k36_w1_recovered7_effective_supervision_v1(
        completed_review_record=completed_review_record,
        review_class=review_class,
        sample_applicability=sample_applicability,
        compiled_submission=compiled_submission,
        reaction_family_authority=reaction_family_authority,
        warhead_rule_authority=warhead_rule_authority,
        existing_approved_authority_baseline_source_payloads=(
            baseline_source_payloads
        ),
    )


@pytest.fixture(scope="module")
def real_result(
    completed_review_record: dict[str, Any],
    review_class: dict[str, Any],
    sample_applicability: list[dict[str, Any]],
    compiled_submission: dict[str, Any],
) -> dict[str, Any]:
    return _build(
        completed_review_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )


def _rehash_applicability(record: dict[str, Any]) -> None:
    record["applicability_record_sha256"] = (
        published_review_packages.sample_applicability_record_sha256_v1(
            record
        )
    )


def _rehash_completed_review(record: dict[str, Any]) -> None:
    record["review_record_sha256"] = ""
    record["review_record_sha256"] = (
        published_review_packages.review_record_sha256_v1(record)
    )


def test_actual_formal_sources_build_exact5_effective_supervision(
    completed_review_record: dict[str, Any],
    review_class: dict[str, Any],
    sample_applicability: list[dict[str, Any]],
    compiled_submission: dict[str, Any],
    real_result: dict[str, Any],
) -> None:
    assert {path: _sha256(path) for path in EXPECTED_FILE_SHA256} == (
        EXPECTED_FILE_SHA256
    )
    state_inventory_before = tuple(sorted(path.name for path in K36_STATE.iterdir()))
    state_bytes_before = {
        path: path.read_bytes()
        for path in (
            COMPLETED_REVIEW_PATH,
            COMPILED_SUBMISSION_PATH,
            REACTION_FAMILY_AUTHORITY_PATH,
            WARHEAD_RULE_AUTHORITY_PATH,
        )
    }
    assert _build(
        completed_review_record,
        review_class,
        sample_applicability,
        compiled_submission,
    ) == real_result
    assert state_inventory_before == tuple(
        sorted(path.name for path in K36_STATE.iterdir())
    )
    assert state_bytes_before == {
        path: path.read_bytes() for path in state_bytes_before
    }
    assert completed_review_record["review_record_sha256"] == (
        authority_creator.K36_SOURCE_REVIEW_RECORD_SHA256_V1
    )
    assert completed_review_record["reviewer_id"] == "fmx"
    assert completed_review_record["review_status"] == "COMPLETED"

    parsed_family = owner.strict_parse_authority_json_v1(
        REACTION_FAMILY_AUTHORITY_PATH.read_bytes()
    )
    parsed_rule = owner.strict_parse_authority_json_v1(
        WARHEAD_RULE_AUTHORITY_PATH.read_bytes()
    )
    build_authorities = getattr(
        authority_creator,
        "build_covapie_k36_w1_reaction_family_and_warhead_rule_authority_v1",
    )
    validate_authorities = getattr(
        authority_creator,
        "validate_covapie_k36_w1_reaction_family_and_warhead_rule_"
        "authority_payload_v1",
    )
    fresh = build_authorities(
        completed_review_record=completed_review_record,
        review_class=review_class,
        sample_applicability=sample_applicability,
        compiled_submission=compiled_submission,
        existing_approved_authority_baseline_source_payloads=(
            _real_baseline_source_payloads()
        ),
    )
    validate_authorities(fresh)
    assert parsed_family == fresh["reaction_family_authority"]
    assert parsed_rule == fresh["warhead_rule_authority"]

    owner.validate_covapie_k36_w1_recovered7_effective_supervision_v1(
        real_result
    )
    records = real_result["effective_supervision_records"]
    assert len(records) == 5
    assert tuple(record["sample_identity"] for record in records) == (
        EXPECTED_MEMBERS
    )
    assert all(
        record["review_class_id"] == EXPECTED_REVIEW_CLASS_ID
        and record["chemistry_review_signature_sha256"]
        == EXPECTED_CHEMISTRY_SIGNATURE
        and record["reaction_family_authority_id"]
        == owner.REACTION_FAMILY_AUTHORITY_ID
        and record["warhead_rule_authority_id"]
        == owner.WARHEAD_RULE_AUTHORITY_ID
        and record["role_profile"]
        == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        and record["retained_heavy_atom_count"] == 29
        and record["reviewed_scaffold_atom_count"] == 27
        and record["reviewed_linker_atom_count"] == 0
        and record["reviewed_warhead_role_atom_count"] == 2
        and record["valid_task_ids"] == [0, 3, 4]
        and record["not_applicable_task_ids"] == [1, 2]
        and record["exact10_status"] == "EXACT10_PASS"
        and record["pocket_status"] == "POCKET_PASS"
        and record["mechanical_closure_status"]
        == "MECHANICAL_CLOSURE_PASS"
        and record["PRE_geometry_supervision_authority_status"]
        == "NOT_ESTABLISHED"
        and record["effective_supervision_record_sha256"]
        == owner.effective_supervision_record_sha256_v1(record)
        for record in records
    )

    summary = real_result["ingestion_effective_authority_summary"]
    assert summary["disk_authorities_equal_fresh_creator_output"] is True
    assert summary["k36_effective_authority_linkage_complete"] is True
    assert (
        summary["k36_non_geometry_training_supervision_authority_complete"]
        is True
    )
    assert summary["k36_PRE_geometry_supervision_authority_complete"] is False
    assert summary["training_supervision_authority_complete"] is False
    assert summary["ready_for_expanded_tensorizer_integration"] is True
    assert summary["expanded_tensorizer_integration_pending"] is True
    assert summary["ready_for_training"] is False


def test_sorted_disk_and_reversed_authority_key_orders_are_semantically_equal(
    completed_review_record: dict[str, Any],
    review_class: dict[str, Any],
    sample_applicability: list[dict[str, Any]],
    compiled_submission: dict[str, Any],
    real_result: dict[str, Any],
) -> None:
    sorted_family = owner.strict_parse_authority_json_v1(
        REACTION_FAMILY_AUTHORITY_PATH.read_bytes()
    )
    sorted_rule = owner.strict_parse_authority_json_v1(
        WARHEAD_RULE_AUTHORITY_PATH.read_bytes()
    )
    reversed_family = _reverse_mapping_order(sorted_family)
    reversed_rule = _reverse_mapping_order(sorted_rule)
    assert tuple(reversed_family) == tuple(reversed(tuple(sorted_family)))
    assert tuple(reversed_rule) == tuple(reversed(tuple(sorted_rule)))

    reversed_result = _build(
        completed_review_record,
        review_class,
        sample_applicability,
        compiled_submission,
        reaction_family_authority=_authority_bytes(reversed_family),
        warhead_rule_authority=_authority_bytes(reversed_rule),
    )
    assert reversed_result == real_result
    assert owner.strict_parse_authority_json_v1(
        _authority_bytes(reversed_family)
    ) == owner.strict_parse_authority_json_v1(
        REACTION_FAMILY_AUTHORITY_PATH.read_bytes()
    )
    provenance = reversed_result["source_authority_provenance"]
    assert provenance["reaction_family_authority_id"] == (
        owner.REACTION_FAMILY_AUTHORITY_ID
    )
    assert provenance["reaction_family_semantic_signature_sha256"] == (
        owner.REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256
    )
    assert provenance["warhead_rule_authority_id"] == (
        owner.WARHEAD_RULE_AUTHORITY_ID
    )
    assert provenance["warhead_rule_semantic_signature_sha256"] == (
        owner.WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256
    )


@pytest.mark.parametrize(
    ("payload", "match"),
    (
        (b'{"authority_id":"one","authority_id":"two"}', "DUPLICATE_KEY"),
        (b"\xef\xbb\xbf{}", "BOM_FORBIDDEN"),
        (b'{"x":"a\x00b"}', "NUL_FORBIDDEN"),
        (b"\xff", "UTF8_REQUIRED"),
        (b'{"x":NaN}', "NONFINITE_NUMBER_REJECTED"),
        (b'{"x":Infinity}', "NONFINITE_NUMBER_REJECTED"),
        (b'{"x":1e999}', "NONFINITE_NUMBER_REJECTED"),
        (b"[]", "TOP_LEVEL_OBJECT_REQUIRED"),
    ),
)
def test_strict_authority_json_parser_fails_closed(
    payload: bytes, match: str
) -> None:
    with pytest.raises(owner.EffectiveSupervisionValidationError, match=match):
        owner.strict_parse_authority_json_v1(payload)


def test_strict_authority_json_parser_requires_exact_bytes() -> None:
    with pytest.raises(
        owner.EffectiveSupervisionValidationError, match="BYTES_REQUIRED"
    ):
        owner.strict_parse_authority_json_v1("{}")  # type: ignore[arg-type]


AuthorityMutation = Callable[[dict[str, Any], dict[str, Any]], None]


def _extra_top_level(family: dict[str, Any], rule: dict[str, Any]) -> None:
    family["extra"] = "forbidden"


def _missing_top_level(family: dict[str, Any], rule: dict[str, Any]) -> None:
    del rule["semantic_name"]


def _wrong_authority_id(family: dict[str, Any], rule: dict[str, Any]) -> None:
    family["authority_id"] = (
        "COVAPIE_CYS_SG_REACTION_FAMILY_0000000000000000"
    )


def _wrong_semantic_sha(family: dict[str, Any], rule: dict[str, Any]) -> None:
    rule["canonical_semantic_signature_sha256"] = "0" * 64


def _wrong_family_rule_linkage(
    family: dict[str, Any], rule: dict[str, Any]
) -> None:
    rule["canonical_semantic_signature"][
        "reaction_family_authority_id"
    ] = "COVAPIE_CYS_SG_REACTION_FAMILY_0000000000000000"


def _wrong_human_provenance(
    family: dict[str, Any], rule: dict[str, Any]
) -> None:
    family["source_human_review_provenance"]["source_reviewer_id"] = "gpt"


def _w2_active_warhead_mutation(
    family: dict[str, Any], rule: dict[str, Any]
) -> None:
    rule["canonical_semantic_signature"]["active_warhead_atom_contract"][1][
        "atom_id"
    ] = "W2"


def _positive_formed_bond_order(
    family: dict[str, Any], rule: dict[str, Any]
) -> None:
    rule["canonical_semantic_signature"]["formed_protein_ligand_event"][
        "formed_bond_order"
    ] = "single"


def _wrong_component_boundary(
    family: dict[str, Any], rule: dict[str, Any]
) -> None:
    rule["canonical_semantic_signature"]["retained_framework_boundary"][
        "scaffold_side_atom_id"
    ] = "C19"


def _pre_authority_established(
    family: dict[str, Any], rule: dict[str, Any]
) -> None:
    rule["canonical_semantic_signature"][
        "pre_reaction_graph_authority_status"
    ] = "ESTABLISHED"


@pytest.mark.parametrize(
    "mutation",
    (
        _extra_top_level,
        _missing_top_level,
        _wrong_authority_id,
        _wrong_semantic_sha,
        _wrong_family_rule_linkage,
        _wrong_human_provenance,
        _w2_active_warhead_mutation,
        _positive_formed_bond_order,
        _wrong_component_boundary,
        _pre_authority_established,
    ),
)
def test_authority_payload_mutations_fail_closed(
    mutation: AuthorityMutation,
    completed_review_record: dict[str, Any],
    review_class: dict[str, Any],
    sample_applicability: list[dict[str, Any]],
    compiled_submission: dict[str, Any],
) -> None:
    family = owner.strict_parse_authority_json_v1(
        REACTION_FAMILY_AUTHORITY_PATH.read_bytes()
    )
    rule = owner.strict_parse_authority_json_v1(
        WARHEAD_RULE_AUTHORITY_PATH.read_bytes()
    )
    mutation(family, rule)
    with pytest.raises(owner.EffectiveSupervisionValidationError):
        _build(
            completed_review_record,
            review_class,
            sample_applicability,
            compiled_submission,
            reaction_family_authority=_authority_bytes(family),
            warhead_rule_authority=_authority_bytes(rule),
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "completed_review_sha",
        "wrong_reviewer",
        "wrong_review_class",
        "missing_applicability",
        "duplicate_member",
        "wrong_applicability_sha",
        "wrong_applicability_signature",
        "signature_match_failure",
        "event_mapping_failure",
        "exact10_failure",
        "pocket_failure",
        "mechanical_failure",
        "applicability_status_failure",
        "baseline_sha_drift",
    ),
)
def test_source_and_applicability_mutations_fail_closed(
    mutation: str,
    completed_review_record: dict[str, Any],
    review_class: dict[str, Any],
    sample_applicability: list[dict[str, Any]],
    compiled_submission: dict[str, Any],
) -> None:
    completed = copy.deepcopy(completed_review_record)
    reviewed_class = copy.deepcopy(review_class)
    applicability = copy.deepcopy(sample_applicability)
    baseline = _real_baseline_source_payloads()
    if mutation == "completed_review_sha":
        completed["review_record_sha256"] = "0" * 64
    elif mutation == "wrong_reviewer":
        completed["reviewer_id"] = "different-human"
        _rehash_completed_review(completed)
    elif mutation == "wrong_review_class":
        reviewed_class["review_class_id"] = (
            "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_" + "0" * 64
        )
    elif mutation == "missing_applicability":
        applicability.pop()
    elif mutation == "duplicate_member":
        applicability[-1] = copy.deepcopy(applicability[0])
    elif mutation == "wrong_applicability_sha":
        applicability[0]["applicability_record_sha256"] = "0" * 64
    elif mutation == "wrong_applicability_signature":
        applicability[0]["chemistry_review_signature_sha256"] = "0" * 64
        _rehash_applicability(applicability[0])
    elif mutation == "signature_match_failure":
        applicability[0]["sample_matches_review_class_signature"] = False
        _rehash_applicability(applicability[0])
    elif mutation == "event_mapping_failure":
        applicability[0]["event_mapping_status"] = "FAIL"
        _rehash_applicability(applicability[0])
    elif mutation == "exact10_failure":
        applicability[0]["exact10_status"] = "EXACT10_FAIL"
        _rehash_applicability(applicability[0])
    elif mutation == "pocket_failure":
        applicability[0]["pocket_status"] = "POCKET_FAIL"
        _rehash_applicability(applicability[0])
    elif mutation == "mechanical_failure":
        applicability[0]["mechanical_closure_status"] = (
            "MECHANICAL_CLOSURE_FAIL"
        )
        _rehash_applicability(applicability[0])
    elif mutation == "applicability_status_failure":
        applicability[0]["applicability_status"] = "FAIL"
        _rehash_applicability(applicability[0])
    elif mutation == "baseline_sha_drift":
        first_path = next(iter(baseline))
        baseline[first_path] = baseline[first_path] + b"\n"
    else:  # pragma: no cover - the parametrization is exhaustive
        raise AssertionError(mutation)
    with pytest.raises(owner.EffectiveSupervisionValidationError):
        _build(
            completed,
            reviewed_class,
            applicability,
            compiled_submission,
            baseline_source_payloads=baseline,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "family_id",
        "rule_id",
        "active_warhead",
        "nonempty_linker",
        "role_profile",
        "valid_tasks_include_B",
        "valid_tasks_missing_C",
        "minimal_seed",
        "direct_boundary",
        "PRE_geometry_established",
    ),
)
def test_generated_effective_record_mutations_fail_closed(
    mutation: str, real_result: dict[str, Any]
) -> None:
    result = copy.deepcopy(real_result)
    record = result["effective_supervision_records"][0]
    if mutation == "family_id":
        record["reaction_family_authority_id"] = (
            "COVAPIE_CYS_SG_REACTION_FAMILY_0000000000000000"
        )
    elif mutation == "rule_id":
        record["warhead_rule_authority_id"] = (
            "COVAPIE_CYS_SG_WARHEAD_RULE_0000000000000000"
        )
    elif mutation == "active_warhead":
        record["reviewed_active_warhead_atom_ids"] = ["C21", "W2"]
    elif mutation == "nonempty_linker":
        record["reviewed_linker_atom_ids"] = ["N19"]
    elif mutation == "role_profile":
        record["role_profile"] = "STRICT_LINKER_PRESENT_V1"
    elif mutation == "valid_tasks_include_B":
        record["valid_task_ids"] = [0, 1, 3, 4]
    elif mutation == "valid_tasks_missing_C":
        record["valid_task_ids"] = [0, 3]
    elif mutation == "minimal_seed":
        record["minimal_seed_atom_ids"] = ["C20", "C19"]
    elif mutation == "direct_boundary":
        record["direct_boundary_semantics"]["scaffold_side_atom_id"] = "C19"
    elif mutation == "PRE_geometry_established":
        record["PRE_geometry_supervision_authority_status"] = "ESTABLISHED"
    else:  # pragma: no cover - the parametrization is exhaustive
        raise AssertionError(mutation)
    record["effective_supervision_record_sha256"] = (
        owner.effective_supervision_record_sha256_v1(record)
    )
    with pytest.raises(
        owner.EffectiveSupervisionValidationError,
        match="EFFECTIVE_SUPERVISION_RECORD_INVALID",
    ):
        owner.validate_covapie_k36_w1_recovered7_effective_supervision_v1(
            result
        )


def test_repeated_and_reordered_builds_are_deterministic_and_do_not_mutate_inputs(
    completed_review_record: dict[str, Any],
    review_class: dict[str, Any],
    sample_applicability: list[dict[str, Any]],
    compiled_submission: dict[str, Any],
    real_result: dict[str, Any],
) -> None:
    family = owner.strict_parse_authority_json_v1(
        REACTION_FAMILY_AUTHORITY_PATH.read_bytes()
    )
    rule = owner.strict_parse_authority_json_v1(
        WARHEAD_RULE_AUTHORITY_PATH.read_bytes()
    )
    completed = copy.deepcopy(completed_review_record)
    reviewed_class = copy.deepcopy(review_class)
    applicability = copy.deepcopy(sample_applicability)
    submission = dict(reversed(tuple(compiled_submission.items())))
    baseline = dict(
        reversed(tuple(_real_baseline_source_payloads().items()))
    )
    snapshot = copy.deepcopy(
        (completed, reviewed_class, applicability, submission, baseline)
    )
    reordered = _build(
        completed,
        reviewed_class,
        list(reversed(applicability)),
        submission,
        reaction_family_authority=_authority_bytes(
            _reverse_mapping_order(family)
        ),
        warhead_rule_authority=_authority_bytes(_reverse_mapping_order(rule)),
        baseline_source_payloads=baseline,
    )
    repeated = _build(
        completed,
        reviewed_class,
        applicability,
        submission,
        baseline_source_payloads=baseline,
    )
    assert reordered == repeated == real_result
    assert snapshot == (
        completed,
        reviewed_class,
        applicability,
        submission,
        baseline,
    )
    assert json.dumps(
        reordered, sort_keys=True, separators=(",", ":")
    ) == json.dumps(real_result, sort_keys=True, separators=(",", ":"))


def test_summary_keeps_authority_role_mechanical_and_pre_geometry_layers_separate(
    real_result: dict[str, Any],
) -> None:
    summary = real_result["ingestion_effective_authority_summary"]
    assert summary["reaction_family_authority_established"] is True
    assert summary["warhead_rule_authority_established"] is True
    assert (
        summary["k36_non_geometry_training_supervision_authority_complete"]
        is True
    )
    assert summary["k36_PRE_geometry_supervision_authority_complete"] is False
    assert summary["training_supervision_authority_complete"] is False
    assert summary["ready_for_training"] is False
    for record in real_result["effective_supervision_records"]:
        assert record["reaction_family_authority_established"] is True
        assert record["warhead_rule_authority_established"] is True
        assert record["exact10_status"] == "EXACT10_PASS"
        assert record["pocket_status"] == "POCKET_PASS"
        assert record["mechanical_closure_status"] == (
            "MECHANICAL_CLOSURE_PASS"
        )
        assert record["PRE_geometry_supervision_authority_status"] == (
            "NOT_ESTABLISHED"
        )
