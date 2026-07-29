"""Tests for the Current11 review-submission adapter design v1."""

from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import rdkit

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_design_v1
    as design,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


REPO_ROOT = Path(__file__).resolve().parents[1]


def git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    return result.stdout


def rows(name: str) -> list[dict[str, str]]:
    payload = (REPO_ROOT / design.OUTPUT_ROOT / name).read_bytes()
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def rehash_response(response: dict[str, object]) -> None:
    for result in response["adapter_result_records"]:
        result["submission_adapter_result_sha256"] = design._adapter_result_sha(
            result
        )
    response["submission_adapter_response_sha256"] = (
        design._adapter_response_sha(response)
    )


def assert_rehashed_response_rejected(
    response: dict[str, object],
    source_payload: object,
) -> None:
    rehash_response(response)
    with pytest.raises(
        ValueError,
        match="^ADAPTER_RESPONSE_INVARIANT_INVALID$",
    ):
        design._validate_reference_response(
            response,
            source_payload=source_payload,
        )


@pytest.fixture(scope="module")
def synthetic():
    return design._synthetic_payloads(REPO_ROOT)


def test_fixed_runtime_versions() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"


def test_formal_base_identity_and_exact10_source_sha() -> None:
    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", design.BASE_COMMIT,
    ).decode().splitlines()
    assert identity == [
        design.BASE_COMMIT,
        design.BASE_PARENT,
        design.BASE_TREE,
        design.BASE_SUBJECT,
    ]
    assert len(design.FROZEN_BASE_SHA256) == 10
    for path, expected in design.FROZEN_BASE_SHA256.items():
        payload = git("show", f"{design.BASE_COMMIT}:{path.as_posix()}")
        assert hashlib.sha256(payload).hexdigest() == expected


def test_interface_and_predecessor_state_is_fail_closed() -> None:
    payloads = design.load_frozen_sources(REPO_ROOT)
    design._validate_phase_a(payloads)
    manifest = json.loads(payloads[design.INTERFACE_MANIFEST])
    assert manifest["transaction_succeeded"] is True
    assert manifest["interface_implementation_completed"] is True
    assert manifest["ready_for_synthetic_interface_evaluation"] is True
    assert manifest["ready_for_real_review_ingestion_execution"] is False
    assert manifest["public_evaluator_design_source_integrity_required"] is True
    assert manifest["saved_context_cannot_bypass_design_source_integrity"] is True
    assert manifest["completed_review_record_count"] == 0
    assert manifest["human_provenance_envelope_count"] == 0
    assert manifest["actual_ingestion_result_count"] == 0
    assert manifest["actual_authority_record_count"] == 0
    assert (
        design.FROZEN_BASE_SHA256[design.INTERFACE_PRODUCTION]
        == "dad2bb9fffeecfd132b34f733be85ff45af089e8b8fbd2feb6a15eb924ac00b0"
    )
    assert (
        design.FROZEN_BASE_SHA256[design.DESIGN_PRODUCTION]
        == "cd726f7122edd8315079f0ac1df9d4bb24d4ee969f438ce2f41eda3fd0f7c410"
    )


def test_exact_schemas_versions_and_vocabularies() -> None:
    assert design.SUBMISSION_BUNDLE_FIELDS == (
        "submission_bundle_version", "submission_batch_id", "submission_items",
    )
    assert design.SUBMISSION_ITEM_FIELDS == (
        "submission_item_version", "review_record_payload",
        "reviewer_provenance_attested",
        "reviewer_provenance_attestor_id", "submission_source_label",
    )
    assert design.REVIEW_PAYLOAD_FIELDS == ingestion_design.REVIEW_RECORD_FIELDS[:-1]
    assert len(design.REVIEW_PAYLOAD_FIELDS) == 25
    assert len(design.ADAPTER_RESPONSE_FIELDS) == 9
    assert len(design.ADAPTER_RESULT_FIELDS) == 12
    assert len(design.ADAPTER_REASON_CODES) == 24
    assert len(set(design.ADAPTER_REASON_CODES)) == 24
    assert design.ADAPTER_REASON_PRECEDENCE == (
        "SOURCE_PAYLOAD_EXACT_TYPE_INVALID",
        "SOURCE_PAYLOAD_SIZE_INVALID",
        "SOURCE_PAYLOAD_UTF8_INVALID",
        "SOURCE_PAYLOAD_BOM_FORBIDDEN",
        "SOURCE_PAYLOAD_JSON_INVALID",
        "SOURCE_PAYLOAD_DUPLICATE_KEY",
        "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH",
        "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID",
        "SUBMISSION_BUNDLE_VERSION_MISMATCH",
        "SUBMISSION_BATCH_ID_NOT_MEANINGFUL",
        "SUBMISSION_ITEM_COUNT_INVALID",
        "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE",
        "DUPLICATE_SAMPLE_IN_BUNDLE",
        "ITEM_SPECIFIC_VALIDATION_REASON",
        "ADAPTER_ATOMICITY_ABORTED",
        "ADAPTER_RESPONSE_INVARIANT_INVALID",
    )
    assert len(design.ADAPTER_RESULT_EFFECTS) == 2
    assert design.COMPLETED_REVIEW_DECISIONS == (
        "select_admitted_candidate",
        "revise_atom_set_and_boundary",
        "quarantine",
    )


@pytest.mark.parametrize(
    ("payload", "expected"),
    (
        ("{}", "SOURCE_PAYLOAD_EXACT_TYPE_INVALID"),
        (bytearray(b"{}"), "SOURCE_PAYLOAD_EXACT_TYPE_INVALID"),
        (memoryview(b"{}"), "SOURCE_PAYLOAD_EXACT_TYPE_INVALID"),
        (b"", "SOURCE_PAYLOAD_SIZE_INVALID"),
        (b"x" * (design.MAX_SOURCE_PAYLOAD_BYTES + 1), "SOURCE_PAYLOAD_SIZE_INVALID"),
        (b"\xff", "SOURCE_PAYLOAD_UTF8_INVALID"),
        (b"\xef\xbb\xbf{}", "SOURCE_PAYLOAD_BOM_FORBIDDEN"),
        (b"{", "SOURCE_PAYLOAD_JSON_INVALID"),
        (b'{"a":1,"a":2}', "SOURCE_PAYLOAD_DUPLICATE_KEY"),
        (b'{"a":NaN}', "SOURCE_PAYLOAD_JSON_INVALID"),
        (b'{"a":Infinity}', "SOURCE_PAYLOAD_JSON_INVALID"),
        (b'{"a":-Infinity}', "SOURCE_PAYLOAD_JSON_INVALID"),
        (b'{"a":1}\\x00', "SOURCE_PAYLOAD_JSON_INVALID"),
        (b'{"a":1}{"b":2}', "SOURCE_PAYLOAD_JSON_INVALID"),
        (b'//comment\\n{}', "SOURCE_PAYLOAD_JSON_INVALID"),
        (b"{a:1}", "SOURCE_PAYLOAD_JSON_INVALID"),
    ),
)
def test_strict_source_rules(payload: object, expected: str) -> None:
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=payload,
    )
    assert response["reason"] == expected
    assert response["adapter_passed"] is False
    assert response["adapted_submissions"] == ()


def test_size_bounds_are_checked_before_json_semantics() -> None:
    one = design._reference_adapt_submission_bundle_v1(source_payload=b"x")
    upper = design._reference_adapt_submission_bundle_v1(
        source_payload=b" " * design.MAX_SOURCE_PAYLOAD_BYTES
    )
    assert one["reason"] == "SOURCE_PAYLOAD_JSON_INVALID"
    assert upper["reason"] == "SOURCE_PAYLOAD_JSON_INVALID"


def test_nul_and_parser_exceptions_fail_closed(synthetic) -> None:
    _, _, items = synthetic
    nul_item = copy.deepcopy(items[0])
    nul_item["review_record_payload"]["review_notes"] = "\x00"
    payloads = (
        b'{"x":"\x00"}',
        b'{"x":"\\u0000"}',
        b'{"x":{"nested":"\\u0000"}}',
        b'{"\\u0000":"value"}',
        b'{"\\u0000":"first","\\u0000":"second"}',
        design._bundle_bytes([nul_item], "escaped-nul-review-notes"),
        b"[" * 10_000 + b"0" + b"]" * 10_000,
        b'{"x":' * 10_000 + b"0" + b"}" * 10_000,
    )
    for payload in payloads:
        value, reason = design._strict_json_loads(payload)
        assert value is None
        assert reason == "SOURCE_PAYLOAD_JSON_INVALID"
        response = design._reference_adapt_submission_bundle_v1(
            source_payload=payload,
        )
        assert response["reason"] == "SOURCE_PAYLOAD_JSON_INVALID"
        assert response["adapter_passed"] is False
        assert response["adapted_submissions"] == ()


def test_pair_preserving_nul_globally_precedes_duplicate_key() -> None:
    nul_and_duplicate_payloads = (
        b'{"x":"\\u0000","x":"clean"}',
        b'{"x":"clean","x":"\\u0000"}',
        b'{"a":{"x":"\\u0000","x":"clean"}}',
        b'{"x":"clean","x":"clean","y":"\\u0000"}',
        b'{"\\u0000":"first","\\u0000":"second"}',
        b'{"a":[{"b":{"x":"\\u0000","x":"clean"}}]}',
    )
    for payload in nul_and_duplicate_payloads:
        snapshot = bytes(payload)
        value, reason = design._strict_json_loads(payload)
        assert value is None
        assert reason == "SOURCE_PAYLOAD_JSON_INVALID"
        analysis = design._analyze_submission_source_v1(payload)
        assert analysis.adapter_passed is False
        assert analysis.response_reason == "SOURCE_PAYLOAD_JSON_INVALID"
        assert analysis.ordered_result_reasons == ()
        response = design._reference_adapt_submission_bundle_v1(
            source_payload=payload,
        )
        assert response["reason"] == "SOURCE_PAYLOAD_JSON_INVALID"
        assert response["adapter_result_records"] == ()
        assert response["adapted_submissions"] == ()
        assert payload == snapshot

    preserved = json.loads(
        '{"x":"\\u0000","x":"clean"}',
        object_pairs_hook=design._preserve_json_object_pairs,
        parse_constant=design._reject_nonfinite,
    )
    assert type(preserved) is design._PreservedJsonObjectPairs
    assert preserved.pairs == (("x", "\x00"), ("x", "clean"))
    assert design._PreservedJsonObjectPairs.__dataclass_params__.frozen is True
    assert design._json_value_contains_nul(preserved) is True

    clean_duplicate = b'{"x":"clean","x":"clean"}'
    assert design._strict_json_loads(clean_duplicate) == (
        None,
        "SOURCE_PAYLOAD_DUPLICATE_KEY",
    )
    clean_response = design._reference_adapt_submission_bundle_v1(
        source_payload=clean_duplicate,
    )
    assert clean_response["reason"] == "SOURCE_PAYLOAD_DUPLICATE_KEY"

    literal_backslash = b'{"x":"\\\\u0000"}'
    literal_value, literal_reason = design._strict_json_loads(
        literal_backslash
    )
    assert literal_reason is None
    assert literal_value == {"x": "\\u0000"}
    literal_response = design._reference_adapt_submission_bundle_v1(
        source_payload=literal_backslash,
    )
    assert literal_response["reason"] == (
        "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH"
    )


def test_all_exact28_truth_cases_and_statistics(synthetic) -> None:
    context, _, items = synthetic
    cases = design._truth_cases(items)
    assert [case.name for case in cases] == [
        "valid_select",
        "valid_revise",
        "valid_quarantine",
        "valid_partial_two_sample_bundle",
        "source_payload_not_bytes",
        "source_payload_empty",
        "source_payload_too_large",
        "invalid_utf8",
        "utf8_bom_forbidden",
        "malformed_json",
        "duplicate_json_key",
        "top_level_not_object",
        "bundle_extra_field",
        "bundle_version_mismatch",
        "batch_id_empty",
        "submission_items_not_list",
        "item_count_zero",
        "item_count_twelve",
        "item_field_inventory_mismatch",
        "item_exact_type_invalid",
        "review_payload_field_inventory_mismatch",
        "review_payload_exact_type_invalid",
        "not_reviewed_decision",
        "provenance_attestation_false",
        "provenance_attestor_invalid",
        "submission_source_label_invalid",
        "duplicate_sample",
        "duplicate_derived_review_sha",
    ]
    responses = [
        design._reference_adapt_submission_bundle_v1(
            source_payload=case.source_payload,
        )
        for case in cases
    ]
    assert all(
        response["reason"] == case.expected_reason
        for response, case in zip(responses, cases)
    )
    assert sum(response["adapter_passed"] for response in responses) == 4
    assert sum(not response["adapter_passed"] for response in responses) == 24
    del context


def test_exact_types_no_coercion_and_optional_index(synthetic) -> None:
    _, payloads, items = synthetic
    assert design._review_payload_reason(payloads[0]) is None
    for field in (
        "warhead_type_candidate_class_index_0based",
        "total_candidate_count",
        "admitted_candidate_count",
    ):
        changed = copy.deepcopy(payloads[0])
        changed[field] = True
        assert (
            design._review_payload_reason(changed)
            == "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        )
    optional = copy.deepcopy(payloads[0])
    optional["selected_bridge_candidate_index_0based"] = None
    assert design._review_payload_reason(optional) is None
    optional["selected_bridge_candidate_index_0based"] = False
    assert (
        design._review_payload_reason(optional)
        == "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    )
    atoms = copy.deepcopy(payloads[0])
    atoms["reviewed_warhead_atom_ids"] = ("1",)
    assert (
        design._review_payload_reason(atoms)
        == "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    )
    atoms["reviewed_warhead_atom_ids"] = [1]
    assert (
        design._review_payload_reason(atoms)
        == "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    )
    assert design._item_reason(items[0]) is None


def test_no_normalization_or_input_mutation(synthetic) -> None:
    _, _, items = synthetic
    changed = copy.deepcopy(items[0])
    changed["reviewer_provenance_attestor_id"] += " "
    payload = design._bundle_bytes([changed])
    snapshot = bytes(payload)
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=payload,
    )
    assert response["reason"] == "PROVENANCE_ATTESTOR_INVALID"
    assert payload == snapshot
    changed = copy.deepcopy(items[0])
    changed["submission_source_label"] = changed["submission_source_label"].upper()
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes([changed]),
    )
    assert response["adapter_passed"] is True
    assert (
        response["adapted_submissions"][0][1]["submission_source_label"]
        == changed["submission_source_label"]
    )


def test_derived_review_payload_and_envelope_digests(synthetic) -> None:
    _, _, items = synthetic
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(items[:2], "digest-batch"),
    )
    assert response["adapter_passed"] is True
    assert len(response["adapted_submissions"]) == 2
    for source_item, (review, envelope), result in zip(
        items, response["adapted_submissions"], response["adapter_result_records"]
    ):
        assert {
            field: review[field] for field in design.REVIEW_PAYLOAD_FIELDS
        } == source_item["review_record_payload"]
        assert review["review_record_sha256"] == ingestion_design.review_record_sha256(review)
        assert envelope["submitted_record_payload_sha256"] == (
            ingestion_design.submitted_record_payload_sha256(review)
        )
        assert envelope["ingestion_envelope_sha256"] == (
            ingestion_design.ingestion_envelope_sha256(envelope)
        )
        assert tuple(envelope) == ingestion_design.INGESTION_ENVELOPE_FIELDS
        assert result["review_record_sha256"] == review["review_record_sha256"]
        assert result["ingestion_envelope_sha256"] == envelope["ingestion_envelope_sha256"]


def test_exact9_response_exact12_results_and_hashes(synthetic) -> None:
    _, _, items = synthetic
    source_payload = design._bundle_bytes(items[:2])
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=source_payload,
    )
    design._validate_reference_response(
        response,
        source_payload=source_payload,
    )
    assert tuple(response) == design.ADAPTER_RESPONSE_FIELDS
    assert response["submission_adapter_response_sha256"] == (
        design._adapter_response_sha(response)
    )
    assert all(
        tuple(result) == design.ADAPTER_RESULT_FIELDS
        and result["submission_adapter_result_sha256"]
        == design._adapter_result_sha(result)
        for result in response["adapter_result_records"]
    )
    broken = copy.deepcopy(response)
    broken["adapter_passed"] = False
    with pytest.raises(ValueError, match="ADAPTER_RESPONSE_INVARIANT_INVALID"):
        design._validate_reference_response(
            broken,
            source_payload=source_payload,
        )


def test_source_analysis_is_frozen_deterministic_and_input_preserving(
    synthetic,
) -> None:
    _, _, items = synthetic
    source_payload = design._bundle_bytes(items[:2], "analysis-plan")
    snapshot = bytes(source_payload)
    first = design._analyze_submission_source_v1(source_payload)
    second = design._analyze_submission_source_v1(source_payload)
    assert first == second
    assert source_payload == snapshot
    assert design.AdapterSourceAnalysis.__dataclass_params__.frozen is True
    assert first.adapter_passed is True
    assert first.response_reason == "PASSED"
    assert first.ordered_result_reasons == ("PASSED", "PASSED")
    assert first.expected_adapted_item_count == 2
    assert first.canonical_bundle_sha256 == design.sha256(
        design.canonical_json(json.loads(source_payload)).encode("utf-8")
    )


def test_review_atom_ids_inherit_exact26_canonical_structure(
    synthetic,
) -> None:
    _, _, items = synthetic
    source_item = next(
        item
        for item in items
        if len(item["review_record_payload"]["reviewed_warhead_atom_ids"])
        >= 2
    )
    sorted_source = design._bundle_bytes(
        [source_item],
        "canonical-atoms-sorted",
    )
    assert design._analyze_submission_source_v1(
        sorted_source
    ).adapter_passed is True

    unicode_item = copy.deepcopy(source_item)
    unicode_item["review_record_payload"]["reviewed_warhead_atom_ids"] = [
        "A",
        "\u00e9",
        "\u4e2d",
    ]
    unicode_source = design._bundle_bytes(
        [unicode_item],
        "canonical-atoms-unicode",
    )
    assert design._analyze_submission_source_v1(
        unicode_source
    ).adapter_passed is True
    unicode_item["review_record_payload"]["reviewed_warhead_atom_ids"] = [
        "\u00e9",
        "A",
        "\u4e2d",
    ]
    assert design._analyze_submission_source_v1(
        design._bundle_bytes(
            [unicode_item],
            "canonical-atoms-unicode-unsorted",
        )
    ).response_reason == "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"

    quarantine = next(
        item
        for item in items
        if item["review_record_payload"]["review_decision"] == "quarantine"
    )
    empty_item = copy.deepcopy(quarantine)
    empty_item["review_record_payload"]["reviewed_warhead_atom_ids"] = []
    assert design._analyze_submission_source_v1(
        design._bundle_bytes([empty_item], "canonical-atoms-empty")
    ).adapter_passed is True

    for name, mutate in (
        (
            "unsorted",
            lambda atoms: list(reversed(atoms)),
        ),
        (
            "duplicate",
            lambda atoms: [*atoms, atoms[0]],
        ),
    ):
        invalid_item = copy.deepcopy(source_item)
        atoms = invalid_item["review_record_payload"][
            "reviewed_warhead_atom_ids"
        ]
        invalid_item["review_record_payload"][
            "reviewed_warhead_atom_ids"
        ] = mutate(atoms)
        mixed_items = [copy.deepcopy(items[4]), invalid_item]
        source = design._bundle_bytes(
            mixed_items,
            f"canonical-atoms-{name}",
        )
        analysis = design._analyze_submission_source_v1(source)
        assert analysis.adapter_passed is False
        assert (
            analysis.response_reason
            == "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        )
        assert analysis.ordered_result_reasons == (
            "ADAPTER_ATOMICITY_ABORTED",
            "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID",
        )
        response = design._reference_adapt_submission_bundle_v1(
            source_payload=source,
        )
        assert response["reason"] == analysis.response_reason
        assert len(response["adapter_result_records"]) == len(mixed_items)
        assert tuple(
            result["reason"]
            for result in response["adapter_result_records"]
        ) == analysis.ordered_result_reasons


def test_derived_digest_helpers_delegate_formal_authorities(
    synthetic,
) -> None:
    _, _, items = synthetic
    payload = copy.deepcopy(items[0]["review_record_payload"])
    snapshot = copy.deepcopy(payload)
    provisional = copy.deepcopy(payload)
    provisional["review_record_sha256"] = ""
    expected_review_sha = ingestion_design.review_record_sha256(
        provisional
    )
    assert (
        design._derived_review_record_sha256_from_payload_v1(payload)
        == expected_review_sha
    )
    assert design._canonical_review_sha(payload) == expected_review_sha
    assert payload == snapshot
    assert (
        "ingestion_design.review_record_sha256(provisional)"
        in inspect.getsource(
            design._derived_review_record_sha256_from_payload_v1
        )
    )
    assert (
        "_derived_review_record_sha256_from_payload_v1(review)"
        in inspect.getsource(design._canonical_review_sha)
    )

    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(
            items[:1],
            "formal-derived-authorities",
        )
    )
    review, envelope = response["adapted_submissions"][0]
    assert design._submitted_record_payload_sha(review) == (
        ingestion_design.submitted_record_payload_sha256(review)
    )
    assert design._ingestion_envelope_sha(envelope) == (
        ingestion_design.ingestion_envelope_sha256(envelope)
    )
    assert (
        "ingestion_design.submitted_record_payload_sha256(review)"
        in inspect.getsource(design._submitted_record_payload_sha)
    )
    assert (
        "ingestion_design.ingestion_envelope_sha256(envelope)"
        in inspect.getsource(design._ingestion_envelope_sha)
    )
    assert (
        envelope["ingestion_envelope_version"]
        == ingestion_design.INGESTION_ENVELOPE_VERSION
    )


def test_response_validator_only_accepts_raw_source_authority() -> None:
    signature = inspect.signature(design._validate_reference_response)
    assert tuple(signature.parameters) == ("response", "source_payload")
    assert signature.parameters["source_payload"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    assert "parsed_bundle" not in signature.parameters
    implementation = inspect.getsource(
        design._validate_reference_response_impl
    )
    assert "_analyze_submission_source_v1(source_payload)" in implementation
    implementation_signature = inspect.signature(
        design._validate_reference_response_impl
    )
    assert tuple(implementation_signature.parameters) == (
        "response",
        "source_payload",
    )


def test_eight_rehashed_derived_record_structure_attacks_fail_closed(
    synthetic,
) -> None:
    class StringSubclass(str):
        pass

    _, _, items = synthetic
    source = design._bundle_bytes(items[:2], "derived-structure-attacks")
    baseline = design._reference_adapt_submission_bundle_v1(
        source_payload=source,
    )
    attacks: list[tuple[str, dict[str, object]]] = []

    def envelope_digest_for_attack(envelope: dict[str, object]) -> str:
        return design.sha256(design.canonical_json({
            field: envelope[field]
            for field in ingestion_design.INGESTION_ENVELOPE_FIELDS
            if field != "ingestion_envelope_sha256"
        }).encode("utf-8"))

    def finish_envelope_attack(response: dict[str, object]) -> None:
        envelope = response["adapted_submissions"][0][1]
        envelope["ingestion_envelope_sha256"] = (
            envelope_digest_for_attack(envelope)
        )
        response["adapter_result_records"][0][
            "ingestion_envelope_sha256"
        ] = envelope["ingestion_envelope_sha256"]
        rehash_response(response)

    for name, version in (
        ("wrong_envelope_version", "forged-version"),
        ("empty_envelope_version", ""),
        (
            "other_formal_version",
            ingestion_design.REVIEW_RECORD_VERSION,
        ),
    ):
        malicious = copy.deepcopy(baseline)
        malicious["adapted_submissions"][0][1][
            "ingestion_envelope_version"
        ] = version
        finish_envelope_attack(malicious)
        attacks.append((name, malicious))

    reordered_envelope = copy.deepcopy(baseline)
    original_envelope = reordered_envelope["adapted_submissions"][0][1]
    reordered_envelope_submissions = list(
        reordered_envelope["adapted_submissions"]
    )
    reordered_envelope_submissions[0] = (
        reordered_envelope["adapted_submissions"][0][0],
        {
            field: original_envelope[field]
            for field in reversed(
                ingestion_design.INGESTION_ENVELOPE_FIELDS
            )
        },
    )
    reordered_envelope["adapted_submissions"] = tuple(
        reordered_envelope_submissions
    )
    finish_envelope_attack(reordered_envelope)
    attacks.append(("envelope_field_order", reordered_envelope))

    bool_as_int = copy.deepcopy(baseline)
    bool_as_int["adapted_submissions"][0][1][
        "reviewer_provenance_attested"
    ] = 1
    finish_envelope_attack(bool_as_int)
    attacks.append(("envelope_bool_as_int", bool_as_int))

    review_sha_subclass = copy.deepcopy(baseline)
    review_sha = review_sha_subclass["adapted_submissions"][0][0][
        "review_record_sha256"
    ]
    review_sha_subclass["adapted_submissions"][0][0][
        "review_record_sha256"
    ] = StringSubclass(review_sha)
    rehash_response(review_sha_subclass)
    attacks.append(("review_sha_str_subclass", review_sha_subclass))

    envelope_sha_subclass = copy.deepcopy(baseline)
    envelope_sha = envelope_sha_subclass["adapted_submissions"][0][1][
        "ingestion_envelope_sha256"
    ]
    envelope_sha_subclass["adapted_submissions"][0][1][
        "ingestion_envelope_sha256"
    ] = StringSubclass(envelope_sha)
    rehash_response(envelope_sha_subclass)
    attacks.append(("envelope_sha_str_subclass", envelope_sha_subclass))

    reordered_review = copy.deepcopy(baseline)
    original_review = reordered_review["adapted_submissions"][0][0]
    reordered_review_submissions = list(
        reordered_review["adapted_submissions"]
    )
    reordered_review_submissions[0] = (
        {
            field: original_review[field]
            for field in reversed(ingestion_design.REVIEW_RECORD_FIELDS)
        },
        reordered_review["adapted_submissions"][0][1],
    )
    reordered_review["adapted_submissions"] = tuple(
        reordered_review_submissions
    )
    rehash_response(reordered_review)
    attacks.append(("adapted_review_field_order", reordered_review))

    assert len(attacks) == 8
    for name, malicious in attacks:
        assert_rehashed_response_rejected(malicious, source)
        assert name


def test_twenty_rehashed_source_classification_attacks_fail_closed(
    synthetic,
) -> None:
    _, _, items = synthetic
    valid_payload = design._bundle_bytes(items[:2], "attack-valid")
    valid_response = design._reference_adapt_submission_bundle_v1(
        source_payload=valid_payload,
    )
    attacks: list[tuple[str, dict[str, object], object]] = []

    different_payload = design._bundle_bytes(items[2:4], "attack-bundle-b")
    bundle_b_response = design._reference_adapt_submission_bundle_v1(
        source_payload=different_payload,
    )
    bundle_b_response["source_payload_sha256"] = design.sha256(valid_payload)
    attacks.append(("source_a_bundle_b", bundle_b_response, valid_payload))

    for reason in (
        "SOURCE_PAYLOAD_JSON_INVALID",
        "SOURCE_PAYLOAD_SIZE_INVALID",
        "ADAPTER_RESPONSE_INVARIANT_INVALID",
    ):
        forged_failure = copy.deepcopy(valid_response)
        forged_failure.update({
            "adapter_passed": False,
            "reason": reason,
            "adapter_result_records": (),
            "adapted_submissions": (),
        })
        attacks.append((f"valid_as_{reason}", forged_failure, valid_payload))

    invalid_bundles: list[tuple[str, dict[str, object]]] = []
    mutation_specs = (
        ("wrong_bundle_version", lambda value: value.__setitem__(
            "submission_bundle_version", "wrong",
        )),
        ("whitespace_batch", lambda value: value.__setitem__(
            "submission_batch_id", " attack-valid ",
        )),
        ("wrong_item_version", lambda value: value["submission_items"][0].__setitem__(
            "submission_item_version", "wrong",
        )),
        ("provenance_false", lambda value: value["submission_items"][0].__setitem__(
            "reviewer_provenance_attested", False,
        )),
        ("blank_attestor", lambda value: value["submission_items"][0].__setitem__(
            "reviewer_provenance_attestor_id", " ",
        )),
        ("blank_source_label", lambda value: value["submission_items"][0].__setitem__(
            "submission_source_label", "",
        )),
        ("not_reviewed", lambda value: value["submission_items"][0][
            "review_record_payload"
        ].__setitem__("review_decision", "not_reviewed")),
        ("bool_as_int", lambda value: value["submission_items"][0][
            "review_record_payload"
        ].__setitem__("total_candidate_count", True)),
    )
    for name, mutate in mutation_specs:
        invalid_bundle = json.loads(valid_payload)
        mutate(invalid_bundle)
        invalid_bundles.append((name, invalid_bundle))

    duplicate_review = json.loads(valid_payload)
    duplicate_review["submission_items"][1] = copy.deepcopy(
        duplicate_review["submission_items"][0]
    )
    invalid_bundles.append(("duplicate_review", duplicate_review))
    duplicate_sample = json.loads(valid_payload)
    duplicate_sample["submission_items"][1]["review_record_payload"][
        "sample_index_row_id"
    ] = duplicate_sample["submission_items"][0]["review_record_payload"][
        "sample_index_row_id"
    ]
    invalid_bundles.append(("duplicate_sample", duplicate_sample))

    for name, invalid_bundle in invalid_bundles:
        invalid_source = design.canonical_json(invalid_bundle).encode("utf-8")
        analysis = design._analyze_submission_source_v1(invalid_source)
        assert analysis.adapter_passed is False
        forged_success = copy.deepcopy(valid_response)
        forged_success.update({
            "source_payload_sha256": analysis.source_payload_sha256,
            "canonical_bundle_sha256": analysis.canonical_bundle_sha256,
            "submission_batch_id": analysis.submission_batch_id,
        })
        attacks.append((f"{name}_as_success", forged_success, invalid_source))

    mixed_items = copy.deepcopy(items[:2])
    mixed_items[1]["reviewer_provenance_attested"] = False
    mixed_payload = design._bundle_bytes(mixed_items, "attack-mixed")
    mixed_response = design._reference_adapt_submission_bundle_v1(
        source_payload=mixed_payload,
    )
    wrong_response_reason = copy.deepcopy(mixed_response)
    wrong_response_reason["reason"] = "PROVENANCE_ATTESTOR_INVALID"
    attacks.append(("item_response_reason", wrong_response_reason, mixed_payload))
    wrong_atomic_reason = copy.deepcopy(mixed_response)
    wrong_atomic_reason["adapter_result_records"][0]["reason"] = (
        "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED"
    )
    attacks.append(("atomic_peer_reason", wrong_atomic_reason, mixed_payload))
    missing_results = copy.deepcopy(mixed_response)
    missing_results["adapter_result_records"] = ()
    attacks.append(("missing_item_results", missing_results, mixed_payload))

    source_failure = design._reference_adapt_submission_bundle_v1(
        source_payload=b"{",
    )
    source_failure["adapter_result_records"] = (
        design._new_result(
            item_index=0,
            batch_id="",
            sample="",
            outcome="invalid",
            passed=False,
            reason="SOURCE_PAYLOAD_JSON_INVALID",
        ),
    )
    attacks.append(("source_failure_item_results", source_failure, b"{"))

    duplicate_review_payload = design.canonical_json(
        duplicate_review
    ).encode("utf-8")
    duplicate_review_response = design._reference_adapt_submission_bundle_v1(
        source_payload=duplicate_review_payload,
    )
    duplicate_review_response["reason"] = "DUPLICATE_SAMPLE_IN_BUNDLE"
    for result in duplicate_review_response["adapter_result_records"]:
        result["reason"] = "DUPLICATE_SAMPLE_IN_BUNDLE"
    attacks.append((
        "duplicate_review_reason_swap",
        duplicate_review_response,
        duplicate_review_payload,
    ))

    duplicate_sample_payload = design.canonical_json(
        duplicate_sample
    ).encode("utf-8")
    duplicate_sample_response = design._reference_adapt_submission_bundle_v1(
        source_payload=duplicate_sample_payload,
    )
    duplicate_sample_response["reason"] = (
        "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE"
    )
    for result in duplicate_sample_response["adapter_result_records"]:
        result["reason"] = "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE"
    attacks.append((
        "duplicate_sample_reason_swap",
        duplicate_sample_response,
        duplicate_sample_payload,
    ))

    assert len(attacks) == 20
    for name, malicious, source_payload in attacks:
        assert_rehashed_response_rejected(malicious, source_payload)
        assert name


def test_exact2_result_effect_table(synthetic) -> None:
    _, _, items = synthetic
    assert design.ADAPTER_RESULT_EFFECTS == (
        {
            "outcome": "adapted",
            "passed": True,
            "reason": "PASSED",
            "consumed_submission_item": True,
            "ready_for_interface_evaluation": True,
            "review_record_sha256": "64_lowercase_hex",
            "ingestion_envelope_sha256": "64_lowercase_hex",
        },
        {
            "outcome": "invalid",
            "passed": False,
            "reason": "formal_failure_reason",
            "consumed_submission_item": False,
            "ready_for_interface_evaluation": False,
            "review_record_sha256": "",
            "ingestion_envelope_sha256": "",
        },
    )
    passed = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(items[:2]),
    )
    assert all(
        (
            result["outcome"],
            result["passed"],
            result["reason"],
            result["consumed_submission_item"],
            result["ready_for_interface_evaluation"],
            len(result["review_record_sha256"]),
            len(result["ingestion_envelope_sha256"]),
        ) == ("adapted", True, "PASSED", True, True, 64, 64)
        for result in passed["adapter_result_records"]
    )
    invalid_items = copy.deepcopy(items[:2])
    invalid_items[1]["reviewer_provenance_attested"] = False
    failed = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(invalid_items),
    )
    assert all(
        result["outcome"] == "invalid"
        and result["passed"] is False
        and result["reason"] != "PASSED"
        and result["consumed_submission_item"] is False
        and result["ready_for_interface_evaluation"] is False
        and result["review_record_sha256"] == ""
        and result["ingestion_envelope_sha256"] == ""
        for result in failed["adapter_result_records"]
    )


def test_rehashed_malicious_response_mutations_all_fail(synthetic) -> None:
    _, _, items = synthetic
    valid_payload = design._bundle_bytes(items[:2], "malicious-response")
    valid_bundle = json.loads(valid_payload)
    valid = design._reference_adapt_submission_bundle_v1(
        source_payload=valid_payload,
    )
    invalid_items = copy.deepcopy(items[:2])
    invalid_items[1]["reviewer_provenance_attested"] = False
    invalid_payload = design._bundle_bytes(
        invalid_items, "malicious-invalid-response",
    )
    invalid_bundle = json.loads(invalid_payload)
    invalid = design._reference_adapt_submission_bundle_v1(
        source_payload=invalid_payload,
    )

    cases = []

    def add_valid(name, mutate):
        cases.append((name, valid, valid_payload, valid_bundle, mutate))

    add_valid("result_version", lambda value: value["adapter_result_records"][0].__setitem__(
        "submission_adapter_result_version", "wrong",
    ))
    add_valid("item_index_99", lambda value: value["adapter_result_records"][0].__setitem__(
        "item_index_0based", 99,
    ))
    add_valid("duplicate_item_index", lambda value: value["adapter_result_records"][1].__setitem__(
        "item_index_0based", 0,
    ))
    add_valid("result_batch", lambda value: value["adapter_result_records"][0].__setitem__(
        "submission_batch_id", "wrong",
    ))
    add_valid("result_sample", lambda value: value["adapter_result_records"][0].__setitem__(
        "sample_index_row_id", "wrong",
    ))
    add_valid("outcome", lambda value: value["adapter_result_records"][0].__setitem__(
        "outcome", "invalid",
    ))
    add_valid("passed", lambda value: value["adapter_result_records"][0].__setitem__(
        "passed", False,
    ))
    add_valid("reason", lambda value: value["adapter_result_records"][0].__setitem__(
        "reason", "ADAPTER_ATOMICITY_ABORTED",
    ))
    add_valid("consumed", lambda value: value["adapter_result_records"][0].__setitem__(
        "consumed_submission_item", False,
    ))
    add_valid("ready", lambda value: value["adapter_result_records"][0].__setitem__(
        "ready_for_interface_evaluation", False,
    ))
    add_valid("review_sha", lambda value: value["adapter_result_records"][0].__setitem__(
        "review_record_sha256", "f" * 64,
    ))
    add_valid("envelope_sha", lambda value: value["adapter_result_records"][0].__setitem__(
        "ingestion_envelope_sha256", "f" * 64,
    ))
    add_valid("result_order", lambda value: value.__setitem__(
        "adapter_result_records",
        tuple(reversed(value["adapter_result_records"])),
    ))
    add_valid("adapted_order", lambda value: value.__setitem__(
        "adapted_submissions",
        tuple(reversed(value["adapted_submissions"])),
    ))
    add_valid("adapted_review_field", lambda value: value["adapted_submissions"][0][0].__setitem__(
        "review_notes", "tampered",
    ))
    add_valid("adapted_review_digest", lambda value: value["adapted_submissions"][0][0].__setitem__(
        "review_record_sha256", "f" * 64,
    ))
    add_valid("envelope_linkage", lambda value: value["adapted_submissions"][0][1].__setitem__(
        "review_record_sha256", "f" * 64,
    ))
    add_valid("envelope_digest", lambda value: value["adapted_submissions"][0][1].__setitem__(
        "ingestion_envelope_sha256", "f" * 64,
    ))
    add_valid("source_sha", lambda value: value.__setitem__(
        "source_payload_sha256", "f" * 64,
    ))
    add_valid("bundle_sha", lambda value: value.__setitem__(
        "canonical_bundle_sha256", "f" * 64,
    ))
    add_valid("response_batch", lambda value: value.__setitem__(
        "submission_batch_id", "wrong",
    ))
    cases.append((
        "invalid_with_adapted",
        invalid,
        invalid_payload,
        invalid_bundle,
        lambda value: value.__setitem__(
            "adapted_submissions", valid["adapted_submissions"],
        ),
    ))
    cases.append((
        "invalid_nonblank_sha",
        invalid,
        invalid_payload,
        invalid_bundle,
        lambda value: value["adapter_result_records"][0].__setitem__(
            "review_record_sha256", "f" * 64,
        ),
    ))
    add_valid("success_atomicity_reason", lambda value: value.__setitem__(
        "reason", "ADAPTER_ATOMICITY_ABORTED",
    ))
    assert len(cases) == 24

    for name, baseline, source_payload, _bundle, mutate in cases:
        malicious = copy.deepcopy(baseline)
        mutate(malicious)
        rehash_response(malicious)
        with pytest.raises(
            ValueError, match="^ADAPTER_RESPONSE_INVARIANT_INVALID$",
        ):
            design._validate_reference_response(
                malicious,
                source_payload=source_payload,
            )
        assert name


def test_bundle_atomicity_and_input_order(synthetic) -> None:
    _, _, items = synthetic
    mixed = copy.deepcopy(items[:2])
    mixed[1]["reviewer_provenance_attested"] = False
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(mixed),
    )
    assert response["adapter_passed"] is False
    assert response["adapted_submissions"] == ()
    assert [record["reason"] for record in response["adapter_result_records"]] == [
        "ADAPTER_ATOMICITY_ABORTED",
        "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED",
    ]
    passed = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(items[:3]),
    )
    assert [
        review["sample_index_row_id"]
        for review, _ in passed["adapted_submissions"]
    ] == [
        item["review_record_payload"]["sample_index_row_id"]
        for item in items[:3]
    ]


def test_reachable_duplicate_precedence_and_invalid_item_priority(synthetic) -> None:
    _, _, items = synthetic
    exact_duplicates = [copy.deepcopy(items[0]), copy.deepcopy(items[0])]
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(exact_duplicates),
    )
    assert response["reason"] == "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE"

    same_sample = [copy.deepcopy(items[0]), copy.deepcopy(items[1])]
    same_sample[1]["review_record_payload"]["sample_index_row_id"] = (
        same_sample[0]["review_record_payload"]["sample_index_row_id"]
    )
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(same_sample),
    )
    assert response["reason"] == "DUPLICATE_SAMPLE_IN_BUNDLE"

    invalid_provenance = copy.deepcopy(same_sample)
    invalid_provenance[1]["reviewer_provenance_attested"] = False
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(invalid_provenance),
    )
    assert response["reason"] == "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED"
    assert [row["reason"] for row in response["adapter_result_records"]] == [
        "ADAPTER_ATOMICITY_ABORTED",
        "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED",
    ]

    invalid_review = copy.deepcopy(same_sample)
    invalid_review[1]["review_record_payload"]["total_candidate_count"] = True
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=design._bundle_bytes(invalid_review),
    )
    assert response["reason"] == "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    assert [row["reason"] for row in response["adapter_result_records"]] == [
        "ADAPTER_ATOMICITY_ABORTED",
        "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID",
    ]


def test_interface_public_builder_evaluator_compatibility(synthetic) -> None:
    context, _, items = synthetic
    cases = design._truth_cases(items)[:4]
    assert (
        "build_result"
        not in inspect.getsource(
            ingestion_interface.
            evaluate_current11_warhead_boundary_review_ingestion_v1
        )
    )
    for case in cases:
        adapted = design._reference_adapt_submission_bundle_v1(
            source_payload=case.source_payload,
        )
        response = (
            ingestion_interface.
            evaluate_current11_warhead_boundary_review_ingestion_v1(
                submissions=adapted["adapted_submissions"],
                authority_context=context,
            )
        )
        ingestion_interface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
            response,
            submissions=adapted["adapted_submissions"],
            authority_context=context,
        )
        assert response["batch_passed"] is True


def test_contract_truth_readiness_and_failure_tables() -> None:
    contracts = rows(design.CONTRACT_FILE)
    truth = rows(design.TRUTH_FILE)
    readiness = rows(design.READINESS_FILE)
    failures = rows(design.FAILURE_FILE)
    assert [row["contract_id"] for row in contracts] == [
        f"ADAPTER_{index:03d}" for index in range(1, 15)
    ]
    assert len(truth) == 28
    assert sum(row["expected_outcome"] == "adapted" for row in truth) == 4
    assert sum(row["expected_outcome"] == "invalid" for row in truth) == 24
    assert all(row["verified"] == "true" for row in truth)
    assert len(readiness) == 11
    assert [row["sample_index_row_id"] for row in readiness] == sorted(
        row["sample_index_row_id"] for row in readiness
    )
    required_blockers = {
        "completed_human_review_record_missing",
        "human_provenance_attestation_missing",
        "submission_payload_missing",
        "submission_adapter_not_implemented",
        "real_ingestion_not_executed",
    }
    for row in readiness:
        assert row["submission_adapter_design_completed"] == "true"
        assert row["ready_for_submission_adapter_implementation"] == "true"
        assert required_blockers <= set(row["blocking_reasons"].split(";"))
        assert row["ready_for_real_ingestion_execution"] == "false"
        assert row["ready_for_training"] == "false"
    assert len(failures) == 47
    assert len({row["mutation_signature"] for row in failures}) == 47
    assert [
        (
            row["failure_case_id"],
            row["mutated_field"],
            row["expected_reason"],
        )
        for row in failures[-10:]
    ] == [
        (
            "FAILURE_038",
            "source_payload_bundle_binding_valid",
            "ADAPTER_SOURCE_PAYLOAD_BUNDLE_BINDING_INVALID",
        ),
        (
            "FAILURE_039",
            "successful_response_requires_valid_source_analysis",
            "ADAPTER_SUCCESS_CLASSIFICATION_INVALID",
        ),
        (
            "FAILURE_040",
            "failed_response_reason_matches_source_analysis",
            "ADAPTER_FAILURE_CLASSIFICATION_INVALID",
        ),
        (
            "FAILURE_041",
            "result_reason_plan_matches_source_analysis",
            "ADAPTER_RESULT_REASON_PLAN_INVALID",
        ),
        (
            "FAILURE_042",
            "checker_source_response_classification_verified",
            "CHECKER_SOURCE_RESPONSE_CLASSIFICATION_NOT_VERIFIED",
        ),
        (
            "FAILURE_043",
            "review_atom_ids_canonical_structure_required",
            "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID",
        ),
        (
            "FAILURE_044",
            "ingestion_envelope_version_exact",
            "ADAPTER_RESPONSE_INVARIANT_INVALID",
        ),
        (
            "FAILURE_045",
            "checker_derived_record_structure_verified",
            "CHECKER_DERIVED_RECORD_STRUCTURE_NOT_VERIFIED",
        ),
        (
            "FAILURE_046",
            "nul_precedence_over_duplicate_key_global",
            "SOURCE_PAYLOAD_JSON_INVALID",
        ),
        (
            "FAILURE_047",
            "checker_nul_duplicate_precedence_verified",
            "CHECKER_NUL_DUPLICATE_PRECEDENCE_NOT_VERIFIED",
        ),
    ]
    assert all(
        row["expected_reason_verified"] == "true"
        and row["fails_closed"] == "true"
        and row["contract_row_count"] == "0"
        and row["truth_row_count"] == "0"
        and row["current11_readiness_row_count"] == "0"
        and row["actual_completed_review_count"] == "0"
        and row["actual_ingestion_envelope_count"] == "0"
        and row["actual_ingestion_result_count"] == "0"
        and row["actual_authority_record_count"] == "0"
        and row["smarts_ready"] == "false"
        and row["training_ready"] == "false"
        for row in failures
    )


def test_failure_dataclass_mutations_are_exact_typed_and_fail_closed() -> None:
    baseline = design.AdapterDesignScenario()
    names = {field.name: field for field in baseline.__dataclass_fields__.values()}
    for _, field, value, expected in design.FAILURE_MUTATIONS:
        assert field in names
        assert type(value) is type(getattr(baseline, field))
        assert value != getattr(baseline, field)
        scenario = design.replace(baseline, **{field: value})
        assert design.observe_failure_scenario(scenario) == (expected,)
        assert design.transaction_tables(scenario) == ((), (), ())


def test_manifest_exact_counts_and_closed_lifecycle() -> None:
    manifest = json.loads(
        (REPO_ROOT / design.OUTPUT_ROOT / design.MANIFEST_FILE).read_bytes()
    )
    assert manifest["transaction_succeeded"] is True
    assert manifest["blocking_reasons"] == []
    assert manifest["source_count"] == 10
    assert manifest["submission_bundle_field_count"] == 3
    assert manifest["submission_item_field_count"] == 5
    assert manifest["review_payload_field_count"] == 25
    assert manifest["submission_adapter_response_field_count"] == 9
    assert manifest["submission_adapter_result_field_count"] == 12
    assert manifest["adapter_reason_count"] == 24
    assert manifest["adapter_reason_precedence_count"] == 16
    assert manifest["contract_count"] == 14
    assert manifest["truth_case_count"] == 28
    assert manifest["current11_readiness_row_count"] == 11
    assert manifest["failure_mutation_count"] == 47
    assert manifest["nul_allowed"] is False
    assert manifest["nul_rejected_after_json_unescape"] is True
    assert manifest["json_parser_exceptions_fail_closed"] is True
    assert (
        manifest["json_parser_internal_exception_public_reason"]
        == "SOURCE_PAYLOAD_JSON_INVALID"
    )
    assert manifest["adapter_reason_precedence"] == list(
        design.ADAPTER_REASON_PRECEDENCE
    )
    assert manifest["adapter_result_effect_row_count"] == 2
    assert manifest["adapter_result_effects_frozen"] is True
    assert manifest["adapter_response_cross_record_linkage_required"] is True
    assert manifest["adapter_response_rehash_does_not_bypass_semantics"] is True
    for field in (
        "source_analysis_plan_frozen",
        "source_analysis_is_single_classification_authority",
        "response_validator_reparses_source_payload",
        "source_payload_to_bundle_binding_required",
        "response_passed_matches_source_analysis",
        "response_reason_matches_source_analysis",
        "result_reasons_match_source_analysis",
        "duplicate_reason_matches_source_analysis",
        "atomic_peer_reasons_match_source_analysis",
        "successful_response_requires_valid_source_analysis",
        "failed_response_must_match_source_analysis",
        "valid_source_cannot_be_reported_as_arbitrary_failure",
        "invalid_source_cannot_be_reported_as_success",
        "checker_source_response_classification_verified",
        "review_payload_inherits_exact26_structural_domain",
        "reviewed_warhead_atom_ids_utf8_sorted_required",
        "reviewed_warhead_atom_ids_unique_required",
        "review_record_digest_uses_ingestion_design_authority",
        "submitted_record_payload_digest_uses_ingestion_design_authority",
        "ingestion_envelope_digest_uses_ingestion_design_authority",
        "ingestion_envelope_version_exact",
        "response_validator_checks_envelope_version",
        "checker_derived_record_structure_verified",
        "nul_scan_preserves_all_object_pairs",
        "nul_scan_runs_before_duplicate_key_rejection",
        "nul_precedence_over_duplicate_key_global",
        "escaped_nul_in_overwritten_duplicate_value_rejected",
        "nested_escaped_nul_in_overwritten_duplicate_value_rejected",
        "literal_backslash_u0000_allowed",
        "checker_nul_duplicate_precedence_verified",
    ):
        assert manifest[field] is True
    assert manifest["review_atom_ids_existence_checked_by_adapter"] is False
    assert manifest["review_atom_ids_chemistry_checked_by_adapter"] is False
    assert manifest["ingestion_envelope_expected_version"] == (
        ingestion_design.INGESTION_ENVELOPE_VERSION
    )
    assert manifest["source_analysis_has_filesystem_effects"] is False
    assert manifest["response_validator_accepts_external_parsed_bundle"] is False
    assert manifest["checker_external_parsed_bundle_trusted"] is False
    assert manifest["adapter_result_indices_contiguous"] is True
    assert manifest["checker_hermetic_lifecycle_executed"] is True
    assert manifest["checker_candidate_commit_from_hermetic_report"] is True
    assert manifest["submission_adapter_design_completed"] is True
    assert manifest["ready_for_submission_adapter_implementation"] is True
    assert manifest["ready_for_real_submission_adaptation"] is False
    assert manifest["ready_for_real_review_ingestion_execution"] is False
    for field in (
        "actual_submission_payload_count",
        "completed_review_record_count",
        "human_provenance_envelope_count",
        "adapted_submission_count",
        "actual_ingestion_result_count",
        "actual_authority_record_count",
    ):
        assert manifest[field] == 0
    assert manifest["canonical_masks"] == list(design.CANONICAL_MASKS)
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert manifest["formal_training_prerequisite"] == "feature-semantics audit"
    assert manifest["Step12D_scope"] == "smoke legality check only"
    assert design.MANIFEST_FILE not in manifest["output_sha256"]


def test_builder_is_deterministic_and_six_data_artifacts_match() -> None:
    first = design.build_evidence_payloads(REPO_ROOT)
    second = design.build_evidence_payloads(REPO_ROOT)
    assert first == second
    assert tuple(first) == design.OUTPUT_FILES
    assert len(first) == 6
    for name, payload in first.items():
        assert (REPO_ROOT / design.OUTPUT_ROOT / name).read_bytes() == payload


def test_design_does_not_implement_future_public_adapter_or_use_interface_build_result() -> None:
    future = "adapt_current11_warhead_boundary_review_submission_bundle_v1"
    assert future not in vars(design)
    signature = inspect.signature(design._reference_adapt_submission_bundle_v1)
    assert tuple(signature.parameters) == ("source_payload",)
    assert signature.parameters["source_payload"].kind is inspect.Parameter.KEYWORD_ONLY
    reference_source = inspect.getsource(design._reference_adapt_submission_bundle_v1)
    assert "Path(" not in reference_source
    assert "open(" not in reference_source
    source = (REPO_ROOT / design.PRODUCTION_PATH).read_text("utf-8")
    assert "ingestion_interface.build_result(" not in source
    checker_source = (REPO_ROOT / design.CHECKER_PATH).read_text("utf-8")
    assert "exercise_hermetic_git_lifecycle_matrix(" in checker_source
    assert "candidate_commit = report.candidate_commit" in checker_source
    assert "def independent_analyze_source(" in checker_source
    assert "class IndependentPreservedObjectPairs:" in checker_source
    assert "def preserve_pairs(" in checker_source
    assert "def independent_review_sha(" in checker_source
    assert "def independent_submitted_payload_sha(" in checker_source
    assert "def independent_envelope_sha(" in checker_source
    assert 'print("review_atom_ids_canonical=true")' in checker_source
    assert 'print("derived_record_authority=true")' in checker_source
    assert 'print("envelope_version_exact=true")' in checker_source
    assert 'print("nul_duplicate_precedence=true")' in checker_source
    assert (
        "def independent_response_valid(\n"
        "    response: object,\n"
        "    *,\n"
        "    source_payload: object,\n"
        ")"
    ) in checker_source
    assert "bundle: object" not in checker_source
    assert "production._analyze_submission_source_v1" not in checker_source
    assert 'git(repo_root, "rev-parse", "HEAD")' not in checker_source


@pytest.mark.parametrize("module_path", (design.PRODUCTION_PATH, design.CHECKER_PATH))
def test_isolated_import_has_no_output_or_side_effects(module_path: Path) -> None:
    before = {
        path.relative_to(REPO_ROOT).as_posix(): path.stat().st_mtime_ns
        for path in (REPO_ROOT / design.OUTPUT_ROOT).iterdir()
    }
    code = (
        "import importlib.util, pathlib, sys;"
        f"p=pathlib.Path({str(REPO_ROOT / module_path)!r});"
        "s=importlib.util.spec_from_file_location('isolated_adapter_design',p);"
        "m=importlib.util.module_from_spec(s);"
        "sys.modules[s.name]=m;"
        "s.loader.exec_module(m)"
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=REPO_ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
    after = {
        path.relative_to(REPO_ROOT).as_posix(): path.stat().st_mtime_ns
        for path in (REPO_ROOT / design.OUTPUT_ROOT).iterdir()
    }
    assert after == before


def test_exact10_filesystem_safety_and_current_lifecycle() -> None:
    existing = [path for path in design.EXACT10_PATHS if (REPO_ROOT / path).exists()]
    assert len(existing) == 10
    for path in existing:
        target = REPO_ROOT / path
        mode = target.stat().st_mode
        assert stat.S_ISREG(mode)
        assert not target.is_symlink()
        assert not mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        assert target.stat().st_size < 5 * 1024 * 1024
    assert design.validate_execution_boundary_v1(REPO_ROOT) in (
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    )


def test_shared_hermetic_lifecycle_exact4_and_cleanup(tmp_path: Path) -> None:
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        REPO_ROOT,
        tmp_path,
        base_commit=design.BASE_COMMIT,
        formal_commit_subject=design.FORMAL_COMMIT_SUBJECT,
        exact_paths=design.EXACT10_PATHS,
    )
    assert report.base_commit == design.BASE_COMMIT
    assert report.candidate_parent == design.BASE_COMMIT
    assert report.candidate_subject == design.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert (
        report.pre_commit.lifecycle,
        report.detached_candidate_post_commit.lifecycle,
        report.formal_main_post_commit_unpushed.lifecycle,
        report.formal_main_post_push.lifecycle,
    ) == lifecycle.LIFECYCLES
    assert tuple(tmp_path.iterdir()) == ()
