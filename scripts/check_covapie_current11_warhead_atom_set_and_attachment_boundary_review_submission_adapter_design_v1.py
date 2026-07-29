"""Independent checker for the Current11 submission-adapter design v1."""

from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

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
    as production,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


class DuplicateKey(ValueError):
    pass


@dataclass(frozen=True)
class IndependentPreservedObjectPairs:
    pairs: tuple[tuple[str, Any], ...]


def preserve_pairs(
    pairs: list[tuple[str, Any]],
) -> IndependentPreservedObjectPairs:
    return IndependentPreservedObjectPairs(tuple(pairs))


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def git(repo_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKey(key)
        value[key] = item
    return value


def nonfinite(value: str) -> None:
    raise ValueError(value)


def meaningful(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def contains_nul(value: Any) -> bool:
    stack = [value]
    while stack:
        current = stack.pop()
        if type(current) is str and "\x00" in current:
            return True
        if type(current) is list:
            stack.extend(current)
        elif type(current) is IndependentPreservedObjectPairs:
            for key, item in current.pairs:
                if "\x00" in key:
                    return True
                stack.append(item)
        elif type(current) is dict:
            for key, item in current.items():
                if "\x00" in key:
                    return True
                stack.append(item)
    return False


def independent_review_reason(review: object) -> str | None:
    if type(review) is not dict or tuple(review) != production.REVIEW_PAYLOAD_FIELDS:
        return "REVIEW_RECORD_PAYLOAD_FIELD_INVENTORY_MISMATCH"
    ints = {
        "warhead_type_candidate_class_index_0based",
        "total_candidate_count",
        "admitted_candidate_count",
    }
    for field in production.REVIEW_PAYLOAD_FIELDS:
        value = review[field]
        if field in ints:
            if type(value) is not int or value < 0:
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        elif field == "selected_bridge_candidate_index_0based":
            if value is not None and (type(value) is not int or value < 0):
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        elif field == "reviewed_warhead_atom_ids":
            if type(value) is not list or any(type(item) is not str for item in value):
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
            try:
                ordered = sorted(
                    value,
                    key=lambda item: item.encode("utf-8"),
                )
            except UnicodeEncodeError:
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
            if value != ordered or len(value) != len(set(value)):
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        elif type(value) is not str:
            return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    if (
        review["review_record_version"] != ingestion_design.REVIEW_RECORD_VERSION
        or review["review_unit_type"] != ingestion_design.REVIEW_UNIT_TYPE
    ):
        return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    if review["review_decision"] not in production.COMPLETED_REVIEW_DECISIONS:
        return "REVIEW_DECISION_NOT_COMPLETED"
    return None


def independent_item_reason(item: object) -> str | None:
    if type(item) is not dict or tuple(item) != production.SUBMISSION_ITEM_FIELDS:
        return "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH"
    if (
        type(item["submission_item_version"]) is not str
        or type(item["review_record_payload"]) is not dict
        or type(item["reviewer_provenance_attested"]) is not bool
        or type(item["reviewer_provenance_attestor_id"]) is not str
        or type(item["submission_source_label"]) is not str
        or item["submission_item_version"] != production.SUBMISSION_ITEM_VERSION
    ):
        return "SUBMISSION_ITEM_EXACT_TYPE_INVALID"
    reason = independent_review_reason(item["review_record_payload"])
    if reason:
        return reason
    if item["reviewer_provenance_attested"] is not True:
        return "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED"
    if not meaningful(item["reviewer_provenance_attestor_id"]):
        return "PROVENANCE_ATTESTOR_INVALID"
    if not meaningful(item["submission_source_label"]):
        return "SUBMISSION_SOURCE_LABEL_NOT_MEANINGFUL"
    return None


def independent_review_sha(review_payload: Mapping[str, Any]) -> str:
    provisional = {
        field: copy.deepcopy(review_payload[field])
        for field in production.REVIEW_PAYLOAD_FIELDS
    }
    provisional["review_record_sha256"] = ""
    formal = ingestion_design.review_record_sha256(provisional)
    manual = digest(canonical({
        field: provisional[field]
        for field in production.REVIEW_PAYLOAD_FIELDS
    }))
    if formal != manual:
        raise ValueError("independent review digest authority mismatch")
    return formal


def independent_submitted_payload_sha(review: Mapping[str, Any]) -> str:
    formal = ingestion_design.submitted_record_payload_sha256(review)
    manual = digest(canonical({
        field: review[field]
        for field in ingestion_design.REVIEW_RECORD_FIELDS
    }))
    if formal != manual:
        raise ValueError("independent submitted-payload authority mismatch")
    return formal


def independent_envelope_sha(envelope: Mapping[str, Any]) -> str:
    formal = ingestion_design.ingestion_envelope_sha256(envelope)
    manual = digest(canonical({
        field: envelope[field]
        for field in ingestion_design.INGESTION_ENVELOPE_FIELDS
        if field != "ingestion_envelope_sha256"
    }))
    if formal != manual:
        raise ValueError("independent envelope authority mismatch")
    return formal


@dataclass(frozen=True)
class IndependentSourceAnalysis:
    source_payload_sha256: str
    canonical_bundle_sha256: str
    submission_batch_id: str
    submission_items: tuple[object, ...]
    adapter_passed: bool
    response_reason: str
    ordered_result_reasons: tuple[str, ...]
    adapted_submissions: tuple[
        tuple[dict[str, Any], dict[str, Any]], ...
    ]


def independent_analyze_source(
    source_payload: object,
) -> IndependentSourceAnalysis:
    """Independently parse and classify raw source without production oracles."""

    source_sha = digest(source_payload) if type(source_payload) is bytes else ""

    def classified(
        reason: str,
        *,
        bundle_sha: str = "",
        batch_id: str = "",
        items: tuple[object, ...] = (),
        result_reasons: tuple[str, ...] = (),
        passed: bool = False,
        submissions: tuple[
            tuple[dict[str, Any], dict[str, Any]], ...
        ] = (),
    ) -> IndependentSourceAnalysis:
        return IndependentSourceAnalysis(
            source_payload_sha256=source_sha,
            canonical_bundle_sha256=bundle_sha,
            submission_batch_id=batch_id,
            submission_items=items,
            adapter_passed=passed,
            response_reason=reason,
            ordered_result_reasons=result_reasons,
            adapted_submissions=submissions,
        )

    if type(source_payload) is not bytes:
        return classified("SOURCE_PAYLOAD_EXACT_TYPE_INVALID")
    if not 1 <= len(source_payload) <= production.MAX_SOURCE_PAYLOAD_BYTES:
        return classified("SOURCE_PAYLOAD_SIZE_INVALID")
    try:
        text = source_payload.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return classified("SOURCE_PAYLOAD_UTF8_INVALID")
    if text.startswith("\ufeff"):
        return classified("SOURCE_PAYLOAD_BOM_FORBIDDEN")
    if "\x00" in text:
        return classified("SOURCE_PAYLOAD_JSON_INVALID")
    try:
        syntax_value = json.loads(
            text,
            object_pairs_hook=preserve_pairs,
            parse_constant=nonfinite,
        )
    except (json.JSONDecodeError, ValueError, RecursionError, OverflowError):
        return classified("SOURCE_PAYLOAD_JSON_INVALID")
    if contains_nul(syntax_value):
        return classified("SOURCE_PAYLOAD_JSON_INVALID")
    try:
        bundle = json.loads(
            text, object_pairs_hook=pairs_hook, parse_constant=nonfinite,
        )
    except DuplicateKey:
        return classified("SOURCE_PAYLOAD_DUPLICATE_KEY")
    except (json.JSONDecodeError, ValueError, RecursionError, OverflowError):
        return classified("SOURCE_PAYLOAD_JSON_INVALID")
    if contains_nul(bundle):
        return classified("SOURCE_PAYLOAD_JSON_INVALID")
    try:
        bundle_sha = digest(canonical(bundle))
    except (TypeError, ValueError, RecursionError, OverflowError):
        return classified("SOURCE_PAYLOAD_JSON_INVALID")
    batch_id = (
        bundle.get("submission_batch_id", "")
        if type(bundle) is dict
        and type(bundle.get("submission_batch_id")) is str
        else ""
    )
    if type(bundle) is not dict or tuple(bundle) != production.SUBMISSION_BUNDLE_FIELDS:
        return classified(
            "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH",
            bundle_sha=bundle_sha,
            batch_id=batch_id,
        )
    if (
        type(bundle["submission_bundle_version"]) is not str
        or type(bundle["submission_batch_id"]) is not str
        or type(bundle["submission_items"]) is not list
    ):
        return classified(
            "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID",
            bundle_sha=bundle_sha,
            batch_id=batch_id,
        )
    if bundle["submission_bundle_version"] != production.SUBMISSION_BUNDLE_VERSION:
        return classified(
            "SUBMISSION_BUNDLE_VERSION_MISMATCH",
            bundle_sha=bundle_sha,
            batch_id=batch_id,
        )
    if not meaningful(batch_id):
        return classified(
            "SUBMISSION_BATCH_ID_NOT_MEANINGFUL",
            bundle_sha=bundle_sha,
            batch_id=batch_id,
        )
    items = bundle["submission_items"]
    if not 1 <= len(items) <= 11:
        return classified(
            "SUBMISSION_ITEM_COUNT_INVALID",
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=tuple(items),
        )
    item_reasons = [independent_item_reason(item) for item in items]
    if any(reason is not None for reason in item_reasons):
        first_reason = next(
            reason for reason in item_reasons if reason is not None
        )
        return classified(
            first_reason,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=tuple(items),
            result_reasons=tuple(
                reason
                if reason is not None
                else "ADAPTER_ATOMICITY_ABORTED"
                for reason in item_reasons
            ),
        )
    safe_reviews = [item["review_record_payload"] for item in items]
    shas = []
    authority_reasons: list[str | None] = []
    for review in safe_reviews:
        try:
            shas.append(independent_review_sha(review))
            authority_reasons.append(None)
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeEncodeError,
            RecursionError,
            OverflowError,
        ):
            shas.append("")
            authority_reasons.append(
                "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
            )
    if any(reason is not None for reason in authority_reasons):
        first_reason = next(
            reason for reason in authority_reasons if reason is not None
        )
        return classified(
            first_reason,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=tuple(items),
            result_reasons=tuple(
                reason
                if reason is not None
                else "ADAPTER_ATOMICITY_ABORTED"
                for reason in authority_reasons
            ),
        )
    samples = [
        review["sample_index_row_id"]
        for review in safe_reviews
    ]
    duplicate_sha = len(shas) != len(set(shas))
    duplicate_sample = len(samples) != len(set(samples))
    if duplicate_sha:
        reason = "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE"
        return classified(
            reason,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=tuple(items),
            result_reasons=(reason,) * len(items),
        )
    if duplicate_sample:
        reason = "DUPLICATE_SAMPLE_IN_BUNDLE"
        return classified(
            reason,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=tuple(items),
            result_reasons=(reason,) * len(items),
        )
    adapted = []
    for item, review_payload in zip(items, safe_reviews):
        review = copy.deepcopy(review_payload)
        review["review_record_sha256"] = independent_review_sha(review)
        envelope: dict[str, Any] = {
            "ingestion_envelope_version": ingestion_design.INGESTION_ENVELOPE_VERSION,
            "submission_batch_id": bundle["submission_batch_id"],
            "sample_index_row_id": review["sample_index_row_id"],
            "review_record_sha256": review["review_record_sha256"],
            "submitted_record_payload_sha256":
                independent_submitted_payload_sha(review),
            "reviewer_provenance_attested": item["reviewer_provenance_attested"],
            "reviewer_provenance_attestor_id": item["reviewer_provenance_attestor_id"],
            "submission_source_label": item["submission_source_label"],
            "ingestion_envelope_sha256": "",
        }
        envelope["ingestion_envelope_sha256"] = independent_envelope_sha(
            envelope
        )
        adapted.append((review, envelope))
    return classified(
        "PASSED",
        bundle_sha=bundle_sha,
        batch_id=batch_id,
        items=tuple(items),
        result_reasons=("PASSED",) * len(items),
        passed=True,
        submissions=tuple(adapted),
    )


def independent_evaluate(
    source_payload: object,
) -> tuple[
    str,
    tuple[tuple[dict[str, Any], dict[str, Any]], ...],
]:
    analysis = independent_analyze_source(source_payload)
    return analysis.response_reason, analysis.adapted_submissions


def independent_response_valid(
    response: object,
    *,
    source_payload: object,
) -> bool:
    try:
        analysis = independent_analyze_source(source_payload)
        assert type(response) is dict
        assert tuple(response) == production.ADAPTER_RESPONSE_FIELDS
        assert response["submission_adapter_response_version"] == (
            production.SUBMISSION_ADAPTER_RESPONSE_VERSION
        )
        assert type(response["adapter_passed"]) is bool
        assert response["reason"] in production.ADAPTER_REASON_CODES
        assert response["source_payload_sha256"] == analysis.source_payload_sha256
        assert response["canonical_bundle_sha256"] == (
            analysis.canonical_bundle_sha256
        )
        assert response["submission_batch_id"] == analysis.submission_batch_id
        assert response["adapter_passed"] is analysis.adapter_passed
        assert response["reason"] == analysis.response_reason
        assert response["submission_adapter_response_sha256"] == digest(
            canonical({
                field: response[field]
                for field in production.ADAPTER_RESPONSE_FIELDS
                if field != "submission_adapter_response_sha256"
            })
        )
        results = response["adapter_result_records"]
        assert type(results) is tuple
        assert type(response["adapted_submissions"]) is tuple
        assert len(results) == len(analysis.ordered_result_reasons)
        assert response["adapted_submissions"] == analysis.adapted_submissions
        result_shas = set()
        for index, result in enumerate(results):
            assert type(result) is dict
            assert tuple(result) == production.ADAPTER_RESULT_FIELDS
            assert result["submission_adapter_result_version"] == (
                production.SUBMISSION_ADAPTER_RESULT_VERSION
            )
            assert type(result["item_index_0based"]) is int
            assert result["item_index_0based"] == index
            assert result["submission_batch_id"] == response["submission_batch_id"]
            assert result["reason"] in production.ADAPTER_REASON_CODES
            assert result["reason"] == analysis.ordered_result_reasons[index]
            assert result["sample_index_row_id"] == (
                analysis.submission_items[index]["review_record_payload"].get(
                    "sample_index_row_id", ""
                )
                if type(analysis.submission_items[index]) is dict
                and type(
                    analysis.submission_items[index].get(
                        "review_record_payload"
                    )
                ) is dict
                else ""
            )
            assert result["submission_adapter_result_sha256"] == digest(
                canonical({
                    field: result[field]
                    for field in production.ADAPTER_RESULT_FIELDS
                    if field != "submission_adapter_result_sha256"
                })
            )
            assert result["submission_adapter_result_sha256"] not in result_shas
            result_shas.add(result["submission_adapter_result_sha256"])
            if result["outcome"] == "adapted":
                assert (
                    result["passed"],
                    result["reason"],
                    result["consumed_submission_item"],
                    result["ready_for_interface_evaluation"],
                ) == (True, "PASSED", True, True)
                assert len(result["review_record_sha256"]) == 64
                assert len(result["ingestion_envelope_sha256"]) == 64
            else:
                assert result["outcome"] == "invalid"
                assert (
                    result["passed"],
                    result["consumed_submission_item"],
                    result["ready_for_interface_evaluation"],
                    result["review_record_sha256"],
                    result["ingestion_envelope_sha256"],
                ) == (False, False, False, "", "")
                assert result["reason"] != "PASSED"
        if response["adapter_passed"]:
            items = analysis.submission_items
            assert response["reason"] == "PASSED"
            assert len(results) == len(items) == len(response["adapted_submissions"])
            assert items
            for index, (submission, item, result) in enumerate(
                zip(response["adapted_submissions"], items, results)
            ):
                assert type(submission) is tuple and len(submission) == 2
                review, envelope = submission
                assert type(review) is dict
                assert type(envelope) is dict
                assert tuple(review) == ingestion_design.REVIEW_RECORD_FIELDS
                assert tuple(envelope) == ingestion_design.INGESTION_ENVELOPE_FIELDS
                assert envelope["ingestion_envelope_version"] == (
                    ingestion_design.INGESTION_ENVELOPE_VERSION
                )
                assert {
                    field: review[field]
                    for field in production.REVIEW_PAYLOAD_FIELDS
                } == item["review_record_payload"]
                assert review["review_record_sha256"] == (
                    ingestion_design.review_record_sha256(review)
                )
                assert envelope["submitted_record_payload_sha256"] == (
                    independent_submitted_payload_sha(review)
                )
                assert envelope["ingestion_envelope_sha256"] == (
                    independent_envelope_sha(envelope)
                )
                assert result["sample_index_row_id"] == review["sample_index_row_id"]
                assert result["review_record_sha256"] == review["review_record_sha256"]
                assert result["ingestion_envelope_sha256"] == (
                    envelope["ingestion_envelope_sha256"]
                )
                assert envelope["sample_index_row_id"] == review["sample_index_row_id"]
                assert envelope["review_record_sha256"] == review["review_record_sha256"]
                assert envelope["submission_batch_id"] == response["submission_batch_id"]
                assert result["item_index_0based"] == index
        else:
            assert response["reason"] != "PASSED"
            assert response["adapted_submissions"] == ()
            assert all(result["outcome"] == "invalid" for result in results)
    except (
        AssertionError,
        KeyError,
        TypeError,
        ValueError,
        RecursionError,
    ):
        return False
    return True


def rehash_response(response: dict[str, Any]) -> None:
    for result in response["adapter_result_records"]:
        result["submission_adapter_result_sha256"] = digest(canonical({
            field: result[field]
            for field in production.ADAPTER_RESULT_FIELDS
            if field != "submission_adapter_result_sha256"
        }))
    response["submission_adapter_response_sha256"] = digest(canonical({
        field: response[field]
        for field in production.ADAPTER_RESPONSE_FIELDS
        if field != "submission_adapter_response_sha256"
    }))


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"

    identity = git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s",
        production.BASE_COMMIT,
    ).decode().splitlines()
    assert identity == [
        production.BASE_COMMIT,
        production.BASE_PARENT,
        production.BASE_TREE,
        production.BASE_SUBJECT,
    ]
    for path, expected in production.FROZEN_BASE_SHA256.items():
        payload = git(
            repo_root, "show",
            f"{production.BASE_COMMIT}:{path.as_posix()}",
        )
        assert digest(payload) == expected

    manifest_path = repo_root / production.OUTPUT_ROOT / production.MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["transaction_succeeded"] is True
    assert manifest["source_count"] == 10
    assert manifest["contract_count"] == 14
    assert manifest["truth_case_count"] == 28
    assert manifest["truth_adapted_case_count"] == 4
    assert manifest["truth_invalid_case_count"] == 24
    assert manifest["current11_readiness_row_count"] == 11
    assert manifest["failure_mutation_count"] == 47
    assert manifest["nul_allowed"] is False
    assert manifest["nul_rejected_after_json_unescape"] is True
    assert manifest["json_parser_exceptions_fail_closed"] is True
    assert manifest["adapter_reason_precedence"] == list(
        production.ADAPTER_REASON_PRECEDENCE
    )
    assert manifest["adapter_result_effect_row_count"] == 2
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
    assert manifest["source_analysis_has_filesystem_effects"] is False
    assert manifest["response_validator_accepts_external_parsed_bundle"] is False
    assert manifest["checker_external_parsed_bundle_trusted"] is False
    assert manifest["review_atom_ids_existence_checked_by_adapter"] is False
    assert manifest["review_atom_ids_chemistry_checked_by_adapter"] is False
    assert manifest["ingestion_envelope_expected_version"] == (
        ingestion_design.INGESTION_ENVELOPE_VERSION
    )
    assert manifest["checker_hermetic_lifecycle_executed"] is True
    assert manifest["actual_submission_payload_count"] == 0
    assert manifest["completed_review_record_count"] == 0
    assert manifest["human_provenance_envelope_count"] == 0
    assert manifest["adapted_submission_count"] == 0
    assert manifest["actual_ingestion_result_count"] == 0
    assert manifest["actual_authority_record_count"] == 0
    assert manifest["canonical_masks"] == list(production.CANONICAL_MASKS)
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["ready_for_training"] is False

    expected_payloads = production.build_evidence_payloads(repo_root)
    for name, expected in expected_payloads.items():
        assert (repo_root / production.OUTPUT_ROOT / name).read_bytes() == expected

    context, _, items = production._synthetic_payloads(repo_root)
    truth_cases = production._truth_cases(items)
    assert len(truth_cases) == 28
    adapted_count = 0
    invalid_count = 0
    compatibility_count = 0
    for case in truth_cases:
        independent_reason, independent_submissions = independent_evaluate(
            case.source_payload
        )
        response = production._reference_adapt_submission_bundle_v1(
            source_payload=case.source_payload,
        )
        assert independent_reason == case.expected_reason == response["reason"]
        assert independent_submissions == response["adapted_submissions"]
        if independent_reason == "PASSED":
            adapted_count += 1
        else:
            invalid_count += 1
            assert response["adapted_submissions"] == ()
        if case.interface_compatibility:
            interface_response = (
                ingestion_interface.
                evaluate_current11_warhead_boundary_review_ingestion_v1(
                    submissions=independent_submissions,
                    authority_context=context,
                )
            )
            ingestion_interface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
                interface_response,
                submissions=independent_submissions,
                authority_context=context,
            )
            assert interface_response["batch_passed"] is True
            compatibility_count += 1
    assert (adapted_count, invalid_count, compatibility_count) == (4, 24, 4)
    assert production.ADAPTER_REASON_PRECEDENCE[11:13] == (
        "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE",
        "DUPLICATE_SAMPLE_IN_BUNDLE",
    )
    nul_payloads = (
        b'{"x":"\\u0000"}',
        b'{"\\u0000":"x"}',
        b'{"x":{"y":"\\u0000"}}',
        b'{"x":"\x00"}',
        b'{"\\u0000":"first","\\u0000":"second"}',
        b'{"x":"\\u0000","x":"clean"}',
        b'{"x":"clean","x":"\\u0000"}',
        b'{"a":{"x":"\\u0000","x":"clean"}}',
        b'{"x":"clean","x":"clean","y":"\\u0000"}',
        b'{"a":[{"b":{"x":"\\u0000","x":"clean"}}]}',
    )
    for payload in nul_payloads:
        assert independent_evaluate(payload)[0] == "SOURCE_PAYLOAD_JSON_INVALID"
        assert production._reference_adapt_submission_bundle_v1(
            source_payload=payload,
        )["reason"] == "SOURCE_PAYLOAD_JSON_INVALID"
    preserved = json.loads(
        '{"x":"\\u0000","x":"clean"}',
        object_pairs_hook=preserve_pairs,
        parse_constant=nonfinite,
    )
    assert type(preserved) is IndependentPreservedObjectPairs
    assert preserved.pairs == (("x", "\x00"), ("x", "clean"))
    assert contains_nul(preserved) is True
    clean_duplicate = b'{"x":"clean","x":"clean"}'
    assert independent_evaluate(clean_duplicate)[0] == (
        "SOURCE_PAYLOAD_DUPLICATE_KEY"
    )
    assert production._reference_adapt_submission_bundle_v1(
        source_payload=clean_duplicate,
    )["reason"] == "SOURCE_PAYLOAD_DUPLICATE_KEY"
    literal_backslash = b'{"x":"\\\\u0000"}'
    assert independent_evaluate(literal_backslash)[0] == (
        "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH"
    )
    assert production._reference_adapt_submission_bundle_v1(
        source_payload=literal_backslash,
    )["reason"] == "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH"
    for deep in (
        b"[" * 10_000 + b"0" + b"]" * 10_000,
        b'{"x":' * 10_000 + b"0" + b"}" * 10_000,
    ):
        assert independent_evaluate(deep)[0] == "SOURCE_PAYLOAD_JSON_INVALID"
        response = production._reference_adapt_submission_bundle_v1(
            source_payload=deep,
        )
        assert response["reason"] == "SOURCE_PAYLOAD_JSON_INVALID"
        assert response["adapted_submissions"] == ()

    valid_payload = production._bundle_bytes(items[:2], "checker-linkage")
    valid_response = production._reference_adapt_submission_bundle_v1(
        source_payload=valid_payload,
    )
    assert independent_response_valid(
        valid_response, source_payload=valid_payload,
    )
    invalid_items = copy.deepcopy(items[:2])
    invalid_items[1]["reviewer_provenance_attested"] = False
    invalid_payload = production._bundle_bytes(
        invalid_items, "checker-invalid-effects",
    )
    invalid_response = production._reference_adapt_submission_bundle_v1(
        source_payload=invalid_payload,
    )
    assert independent_response_valid(
        invalid_response,
        source_payload=invalid_payload,
    )

    canonical_item = next(
        item
        for item in items
        if len(item["review_record_payload"]["reviewed_warhead_atom_ids"])
        >= 2
    )
    for name, mutate_atoms in (
        ("unsorted", lambda atoms: list(reversed(atoms))),
        ("duplicate", lambda atoms: [*atoms, atoms[0]]),
    ):
        structural_item = copy.deepcopy(canonical_item)
        atoms = structural_item["review_record_payload"][
            "reviewed_warhead_atom_ids"
        ]
        structural_item["review_record_payload"][
            "reviewed_warhead_atom_ids"
        ] = mutate_atoms(atoms)
        structural_source = production._bundle_bytes(
            [structural_item],
            f"checker-{name}-atom-list",
        )
        independent_structural = independent_analyze_source(
            structural_source
        )
        assert independent_structural.adapter_passed is False
        assert independent_structural.response_reason == (
            "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        )
        structural_response = (
            production._reference_adapt_submission_bundle_v1(
                source_payload=structural_source,
            )
        )
        assert structural_response["reason"] == (
            "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        )
        assert independent_response_valid(
            structural_response,
            source_payload=structural_source,
        )

    first_review, first_envelope = valid_response[
        "adapted_submissions"
    ][0]
    assert first_review["review_record_sha256"] == (
        independent_review_sha({
            field: first_review[field]
            for field in production.REVIEW_PAYLOAD_FIELDS
        })
    )
    assert first_envelope["submitted_record_payload_sha256"] == (
        independent_submitted_payload_sha(first_review)
    )
    assert first_envelope["ingestion_envelope_version"] == (
        ingestion_design.INGESTION_ENVELOPE_VERSION
    )
    assert first_envelope["ingestion_envelope_sha256"] == (
        independent_envelope_sha(first_envelope)
    )

    wrong_envelope_version = copy.deepcopy(valid_response)
    forged_envelope = wrong_envelope_version[
        "adapted_submissions"
    ][0][1]
    forged_envelope["ingestion_envelope_version"] = "forged-version"
    forged_envelope["ingestion_envelope_sha256"] = (
        independent_envelope_sha(forged_envelope)
    )
    forged_result = wrong_envelope_version[
        "adapter_result_records"
    ][0]
    forged_result["ingestion_envelope_sha256"] = (
        forged_envelope["ingestion_envelope_sha256"]
    )
    rehash_response(wrong_envelope_version)
    assert not independent_response_valid(
        wrong_envelope_version,
        source_payload=valid_payload,
    )
    try:
        production._validate_reference_response(
            wrong_envelope_version,
            source_payload=valid_payload,
        )
    except ValueError as error:
        assert str(error) == "ADAPTER_RESPONSE_INVARIANT_INVALID"
    else:
        raise AssertionError("wrong envelope version was accepted")

    def assert_classification_attack_rejected(
        malicious: dict[str, Any],
        source: object,
    ) -> None:
        rehash_response(malicious)
        assert not independent_response_valid(
            malicious,
            source_payload=source,
        )
        try:
            production._validate_reference_response(
                malicious,
                source_payload=source,
            )
        except ValueError as error:
            assert str(error) == "ADAPTER_RESPONSE_INVARIANT_INVALID"
        else:
            raise AssertionError("classification attack was accepted")

    different_payload = production._bundle_bytes(
        items[2:4], "checker-different-bundle",
    )
    substituted = production._reference_adapt_submission_bundle_v1(
        source_payload=different_payload,
    )
    substituted["source_payload_sha256"] = digest(valid_payload)
    assert_classification_attack_rejected(substituted, valid_payload)

    for forged_reason in (
        "SOURCE_PAYLOAD_JSON_INVALID",
        "SOURCE_PAYLOAD_SIZE_INVALID",
    ):
        forged_failure = copy.deepcopy(valid_response)
        forged_failure.update({
            "adapter_passed": False,
            "reason": forged_reason,
            "adapter_result_records": (),
            "adapted_submissions": (),
        })
        assert_classification_attack_rejected(
            forged_failure,
            valid_payload,
        )

    invalid_bundles: list[dict[str, Any]] = []
    for mutate in (
        lambda value: value.__setitem__(
            "submission_bundle_version", "wrong",
        ),
        lambda value: value.__setitem__(
            "submission_batch_id", " checker-whitespace ",
        ),
        lambda value: value["submission_items"][0].__setitem__(
            "submission_item_version", "wrong",
        ),
        lambda value: value["submission_items"][0].__setitem__(
            "reviewer_provenance_attested", False,
        ),
        lambda value: value["submission_items"][0].__setitem__(
            "reviewer_provenance_attestor_id", " ",
        ),
        lambda value: value["submission_items"][0].__setitem__(
            "submission_source_label", "",
        ),
        lambda value: value["submission_items"][0][
            "review_record_payload"
        ].__setitem__("review_decision", "not_reviewed"),
        lambda value: value["submission_items"][0][
            "review_record_payload"
        ].__setitem__("total_candidate_count", True),
    ):
        invalid_bundle = json.loads(valid_payload)
        mutate(invalid_bundle)
        invalid_bundles.append(invalid_bundle)
    for invalid_bundle in invalid_bundles:
        invalid_source = canonical(invalid_bundle)
        source_analysis = independent_analyze_source(invalid_source)
        assert source_analysis.adapter_passed is False
        forged_success = copy.deepcopy(valid_response)
        forged_success.update({
            "source_payload_sha256":
                source_analysis.source_payload_sha256,
            "canonical_bundle_sha256":
                source_analysis.canonical_bundle_sha256,
            "submission_batch_id":
                source_analysis.submission_batch_id,
        })
        assert_classification_attack_rejected(
            forged_success,
            invalid_source,
        )

    mutations = (
        lambda value: value["adapter_result_records"][0].__setitem__(
            "submission_adapter_result_version", "wrong",
        ),
        lambda value: value["adapter_result_records"][0].__setitem__(
            "item_index_0based", 99,
        ),
        lambda value: value["adapter_result_records"][0].__setitem__(
            "submission_batch_id", "wrong",
        ),
        lambda value: value["adapter_result_records"][0].__setitem__(
            "sample_index_row_id", "wrong",
        ),
        lambda value: value["adapter_result_records"][0].__setitem__(
            "outcome", "invalid",
        ),
        lambda value: value["adapter_result_records"][0].__setitem__(
            "review_record_sha256", "f" * 64,
        ),
        lambda value: value["adapted_submissions"][0][0].__setitem__(
            "review_notes", "tampered",
        ),
        lambda value: value["adapted_submissions"][0][1].__setitem__(
            "submission_batch_id", "wrong",
        ),
    )
    for mutate in mutations:
        malicious = copy.deepcopy(valid_response)
        mutate(malicious)
        rehash_response(malicious)
        assert not independent_response_valid(
            malicious, source_payload=valid_payload,
        )
        try:
            production._validate_reference_response(
                malicious,
                source_payload=valid_payload,
            )
        except ValueError as error:
            assert str(error) == "ADAPTER_RESPONSE_INVARIANT_INVALID"
        else:
            raise AssertionError("malicious response mutation was accepted")

    source = inspect.getsource(production._reference_adapt_submission_bundle_v1)
    assert "Path(" not in source
    assert "open(" not in source
    assert "read_" not in source
    assert "write_" not in source
    assert (
        "adapt_current11_warhead_boundary_review_submission_bundle_v1"
        not in vars(production)
    )
    complete_source = (repo_root / production.PRODUCTION_PATH).read_text("utf-8")
    assert "ingestion_interface.build_result(" not in complete_source

    contracts = csv_rows(
        (repo_root / production.OUTPUT_ROOT / production.CONTRACT_FILE).read_bytes()
    )
    truth = csv_rows(
        (repo_root / production.OUTPUT_ROOT / production.TRUTH_FILE).read_bytes()
    )
    readiness = csv_rows(
        (repo_root / production.OUTPUT_ROOT / production.READINESS_FILE).read_bytes()
    )
    failures = csv_rows(
        (repo_root / production.OUTPUT_ROOT / production.FAILURE_FILE).read_bytes()
    )
    assert [row["contract_id"] for row in contracts] == [
        f"ADAPTER_{index:03d}" for index in range(1, 15)
    ]
    assert [row["truth_case_name"] for row in truth] == [
        case.name for case in truth_cases
    ]
    assert len(readiness) == 11
    assert [row["sample_index_row_id"] for row in readiness] == sorted(
        row["sample_index_row_id"] for row in readiness
    )
    assert len(failures) == 47
    assert all(
        row["fails_closed"] == "true"
        and row["verified"] == "true"
        and row["contract_row_count"] == "0"
        and row["truth_row_count"] == "0"
        and row["current11_readiness_row_count"] == "0"
        for row in failures
    )

    current_lifecycle = production.validate_execution_boundary_v1(repo_root)
    with tempfile.TemporaryDirectory(
        prefix="covapie-adapter-checker-",
    ) as temporary:
        isolated_workspace = Path(temporary)
        report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
            repo_root,
            isolated_workspace,
            base_commit=production.BASE_COMMIT,
            formal_commit_subject=production.FORMAL_COMMIT_SUBJECT,
            exact_paths=production.EXACT10_PATHS,
        )
        assert report.base_commit == production.BASE_COMMIT
        assert report.candidate_parent == production.BASE_COMMIT
        assert report.candidate_subject == production.FORMAL_COMMIT_SUBJECT
        assert report.exact_path_count == 10
        assert report.cleanup_verified is True
        observed_lifecycles = (
            report.pre_commit.lifecycle,
            report.detached_candidate_post_commit.lifecycle,
            report.formal_main_post_commit_unpushed.lifecycle,
            report.formal_main_post_push.lifecycle,
        )
        assert observed_lifecycles == lifecycle.LIFECYCLES
        assert tuple(isolated_workspace.iterdir()) == ()
        candidate_commit = report.candidate_commit
    print("checker=passed")
    print("sources=10 contracts=14 truth_cases=28 samples=11")
    print("truth_outcomes=adapted:4,invalid:24")
    print("schemas=bundle:3,item:5,review_payload:25,response:9,result:12")
    print(
        "strict_json=true duplicate_keys=false nul=false "
        "parser_exceptions_fail_closed=true coercion=false"
    )
    print("nul_duplicate_precedence=true")
    print("reason_precedence=16 precedence_consistent=true")
    print("response_result_invariants=true")
    print("interface_compatibility_cases=4 all_passed=true")
    print("actual_payloads=0 reviews=0 envelopes=0 results=0 authorities=0")
    print("adapter_design_completed=true implementation_ready=true execution_ready=false")
    print("source_response_binding=true")
    print("classification_reason_binding=true")
    print("external_parsed_bundle_trusted=false")
    print("review_atom_ids_canonical=true")
    print("derived_record_authority=true")
    print("envelope_version_exact=true")
    print("failure_mutations=47 all_fail_closed=true")
    print(f"current_lifecycle={current_lifecycle}")
    print("hermetic_lifecycle=" + ",".join(observed_lifecycles))
    print(f"candidate_commit={candidate_commit}")
    print(
        "recommended_next_step=implement_covapie_current11_warhead_atom_set_"
        "and_attachment_boundary_review_submission_adapter_v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
