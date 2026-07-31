from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1
    as adapter,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPT = (
    adapter
    .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1
)
BUNDLE_DIGEST = "multi_boundary_submission_bundle_sha256"
RECORD_DIGEST = "multi_boundary_review_record_sha256"
RESPONSE_FIELDS = (
    "multi_boundary_submission_adapter_response_version",
    "source_payload_sha256",
    "canonical_source_bundle_sha256",
    "submission_batch_id",
    "adapter_passed",
    "reason",
    "adapter_result_records",
    "adapted_submissions",
    "multi_boundary_submission_adapter_response_sha256",
)
RESULT_FIELDS = (
    "multi_boundary_submission_adapter_result_version",
    "item_index_0based",
    "submission_batch_id",
    "sample_index_row_id",
    "outcome",
    "passed",
    "reason",
    "source_multi_boundary_review_record_sha256",
    "ingestion_envelope_sha256",
    "consumed_submission_item",
    "ready_for_ingestion",
    "multi_boundary_submission_adapter_result_sha256",
)
ENVELOPE_FIELDS = (
    "multi_boundary_ingestion_envelope_version",
    "submission_batch_id",
    "item_index_0based",
    "sample_index_row_id",
    "source_multi_boundary_submission_bundle_sha256",
    "source_multi_boundary_review_record_sha256",
    "review_record_payload",
    "reviewer_provenance_attested",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
    "ready_for_ingestion",
    "multi_boundary_ingestion_envelope_sha256",
)
RECORD_FIELDS = (
    "multi_boundary_review_record_version",
    "item_index_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_evidence_record_sha256",
    "source_v1_quarantine_authority_record_sha256",
    "source_review_record_sha256",
    "proposed_warhead_atom_ids",
    "proposed_boundary_records",
    "scope_caveat",
    "review_decision",
    "reviewed_warhead_atom_ids",
    "reviewed_boundary_records",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "reviewer_provenance_attested",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
    "review_completed",
    "multi_boundary_review_record_sha256",
)


def _canonical_sha(record: dict[str, Any], excluded: str) -> str:
    return hashlib.sha256(json.dumps(
        {key: value for key, value in record.items() if key != excluded},
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _load_compiler_checker():
    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_submission_bundle_compiler_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "adapter_test_compiler_checker", path,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def valid_payload() -> bytes:
    checker = _load_compiler_checker()
    workspace, submission, execution = checker._completed_workspace(REPO_ROOT)
    return (
        compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            verified_multi_boundary_evidence_csv=workspace["evidence"],
            multi_boundary_review_worklist_csv=workspace["worklist"],
            readme_md=workspace["readme"],
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=REPO_ROOT,
            submission_batch_id=
                "covapie_current11_multi_boundary_adapter_test_batch_v1",
        )
    )


def _mutated_payload(
    valid_payload: bytes,
    mutation: Callable[[dict[str, Any]], None],
    *,
    record_indices: tuple[int, ...] = (),
    refresh_bundle: bool = True,
) -> bytes:
    bundle = json.loads(valid_payload)
    mutation(bundle)
    for index in record_indices:
        record = bundle["submission_items"][index]
        record[RECORD_DIGEST] = _canonical_sha(record, RECORD_DIGEST)
    if refresh_bundle:
        bundle[BUNDLE_DIGEST] = _canonical_sha(bundle, BUNDLE_DIGEST)
    return _ordered_bytes(bundle)


def _assert_response_digest(response: dict[str, Any]) -> None:
    assert tuple(response) == RESPONSE_FIELDS
    assert response[
        "multi_boundary_submission_adapter_response_sha256"
    ] == _canonical_sha(
        response,
        "multi_boundary_submission_adapter_response_sha256",
    )


def _assert_failed(
    response: dict[str, Any],
    reason: str,
) -> None:
    _assert_response_digest(response)
    assert response["adapter_passed"] is False
    assert response["reason"] == reason
    assert response["adapter_result_records"] == ()
    assert response["adapted_submissions"] == ()


def test_public_api_signature_all_and_silent_import() -> None:
    assert adapter.__all__ == (
        "adapt_covapie_current11_multi_boundary_human_review_"
        "submission_bundle_v1",
    )
    signature = inspect.signature(ADAPT)
    assert tuple(signature.parameters) == ("source_payload",)
    parameter = signature.parameters["source_payload"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.annotation == "bytes"
    assert signature.return_annotation == "dict[str, Any]"

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext."
            "covapie_current11_multi_boundary_human_review_"
            "submission_adapter_v1",
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_valid_410_exact_response_results_envelopes_and_digests(
    valid_payload: bytes,
) -> None:
    response = ADAPT(source_payload=valid_payload)
    _assert_response_digest(response)
    assert response["adapter_passed"] is True
    assert response["reason"] == "PASSED"
    assert response["source_payload_sha256"] == hashlib.sha256(
        valid_payload
    ).hexdigest()
    bundle = json.loads(valid_payload)
    assert response["canonical_source_bundle_sha256"] == (
        bundle[BUNDLE_DIGEST]
    )
    results = response["adapter_result_records"]
    envelopes = response["adapted_submissions"]
    assert type(results) is tuple and len(results) == 5
    assert type(envelopes) is tuple and len(envelopes) == 5
    assert [
        envelope["review_record_payload"]["review_decision"]
        for envelope in envelopes
    ].count("accept_verified_two_boundary_proposal") == 4
    assert [
        envelope["review_record_payload"]["review_decision"]
        for envelope in envelopes
    ].count("revise_two_boundary_atom_set_and_boundaries") == 1

    envelope_shas = set()
    result_shas = set()
    for position, (source, result, envelope) in enumerate(zip(
        bundle["submission_items"], results, envelopes,
    )):
        assert tuple(result) == RESULT_FIELDS
        assert tuple(envelope) == ENVELOPE_FIELDS
        assert tuple(envelope["review_record_payload"]) == RECORD_FIELDS
        assert envelope["review_record_payload"] == source
        assert envelope["review_record_payload"] is not source
        assert result["item_index_0based"] == position
        assert result["outcome"] == "adapted"
        assert result["passed"] is True
        assert result["reason"] == "PASSED"
        assert result["consumed_submission_item"] is True
        assert result["ready_for_ingestion"] is True
        assert envelope["ready_for_ingestion"] is True
        assert envelope["reviewer_provenance_attested"] is True
        assert envelope["reviewer_provenance_attestor_id"] == (
            source["reviewer_provenance_attestor_id"]
        )
        assert envelope["submission_source_label"] == (
            source["submission_source_label"]
        )
        assert envelope["multi_boundary_ingestion_envelope_sha256"] == (
            _canonical_sha(
                envelope,
                "multi_boundary_ingestion_envelope_sha256",
            )
        )
        assert result[
            "multi_boundary_submission_adapter_result_sha256"
        ] == _canonical_sha(
            result,
            "multi_boundary_submission_adapter_result_sha256",
        )
        assert result["ingestion_envelope_sha256"] == (
            envelope["multi_boundary_ingestion_envelope_sha256"]
        )
        envelope_shas.add(result["ingestion_envelope_sha256"])
        result_shas.add(
            result["multi_boundary_submission_adapter_result_sha256"]
        )
    assert len(envelope_shas) == 5
    assert len(result_shas) == 5


def test_determinism_input_unchanged_and_deep_copy_isolation(
    valid_payload: bytes,
) -> None:
    snapshot = bytes(valid_payload)
    first = ADAPT(source_payload=valid_payload)
    second = ADAPT(source_payload=valid_payload)
    assert first == second
    assert valid_payload == snapshot
    original_atom = second["adapted_submissions"][0][
        "review_record_payload"
    ]["proposed_warhead_atom_ids"][0]
    first["adapted_submissions"][0]["review_record_payload"][
        "proposed_warhead_atom_ids"
    ][0] = "MUTATED"
    third = ADAPT(source_payload=valid_payload)
    assert second["adapted_submissions"][0]["review_record_payload"][
        "proposed_warhead_atom_ids"
    ][0] == original_atom
    assert third == second


@pytest.mark.parametrize(
    ("payload", "reason"),
    (
        (bytearray(b"{}"), "SOURCE_PAYLOAD_EXACT_TYPE_INVALID"),
        (b"", "SOURCE_PAYLOAD_SIZE_INVALID"),
        (b"x" * 1_048_576, "SOURCE_PAYLOAD_SIZE_INVALID"),
        (b"\xef\xbb\xbf{}", "SOURCE_PAYLOAD_BOM_FORBIDDEN"),
        (b'{"x":"\\u0000"}\x00', "SOURCE_PAYLOAD_NUL_FORBIDDEN"),
        (b"{}\n", "SOURCE_PAYLOAD_TRAILING_NEWLINE_FORBIDDEN"),
        (b'{"x":"\xff"}', "SOURCE_PAYLOAD_UTF8_INVALID"),
        (b"{", "SOURCE_PAYLOAD_JSON_INVALID"),
    ),
)
def test_source_byte_and_basic_json_failures(
    payload: object,
    reason: str,
) -> None:
    response = ADAPT(source_payload=payload)
    _assert_failed(response, reason)
    if type(payload) is bytes:
        assert response["source_payload_sha256"] == hashlib.sha256(
            payload
        ).hexdigest()
    else:
        assert response["source_payload_sha256"] == ""


def test_duplicate_keys_nonfinite_and_top_level_type(
    valid_payload: bytes,
) -> None:
    top_duplicate = b'{"x":1,"x":2,' + valid_payload[1:]
    nested_duplicate = valid_payload.replace(
        b'"item_index_0based":0',
        b'"item_index_0based":0,"item_index_0based":0',
        1,
    )
    for payload in (top_duplicate, nested_duplicate):
        _assert_failed(
            ADAPT(source_payload=payload),
            "SOURCE_PAYLOAD_DUPLICATE_KEY",
        )
    for constant in (b"NaN", b"Infinity", b"-Infinity"):
        _assert_failed(
            ADAPT(source_payload=b'{"value":' + constant + b"}"),
            "SOURCE_PAYLOAD_NONFINITE_INVALID",
        )
    _assert_failed(
        ADAPT(source_payload=b"[]"),
        "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID",
    )


def test_bundle_inventory_type_version_batch_count_and_digest(
    valid_payload: bytes,
) -> None:
    wrong_inventory = _mutated_payload(
        valid_payload,
        lambda bundle: bundle.__setitem__("unexpected", "value"),
        refresh_bundle=False,
    )
    _assert_failed(
        ADAPT(source_payload=wrong_inventory),
        "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH",
    )
    reordered = json.loads(valid_payload)
    first_key = next(iter(reordered))
    first_value = reordered.pop(first_key)
    reordered[first_key] = first_value
    _assert_failed(
        ADAPT(source_payload=_ordered_bytes(reordered)),
        "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH",
    )
    bad_sha = _mutated_payload(
        valid_payload,
        lambda bundle: bundle.__setitem__(
            "source_readme_sha256", "A" * 64,
        ),
        refresh_bundle=False,
    )
    _assert_failed(
        ADAPT(source_payload=bad_sha),
        "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID",
    )
    wrong_version = _mutated_payload(
        valid_payload,
        lambda bundle: bundle.__setitem__(
            "multi_boundary_submission_bundle_version", "wrong",
        ),
    )
    _assert_failed(
        ADAPT(source_payload=wrong_version),
        "SUBMISSION_BUNDLE_VERSION_MISMATCH",
    )
    for bad_batch in ("", " padded ", "\x00"):
        payload = _mutated_payload(
            valid_payload,
            lambda bundle, value=bad_batch: bundle.__setitem__(
                "submission_batch_id", value,
            ),
        )
        _assert_failed(
            ADAPT(source_payload=payload),
            "SUBMISSION_BATCH_ID_NOT_MEANINGFUL",
        )
    wrong_count = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"].pop(),
    )
    _assert_failed(
        ADAPT(source_payload=wrong_count),
        "SUBMISSION_ITEM_COUNT_INVALID",
    )
    wrong_digest = _mutated_payload(
        valid_payload,
        lambda bundle: bundle.__setitem__(BUNDLE_DIGEST, "0" * 64),
        refresh_bundle=False,
    )
    response = ADAPT(source_payload=wrong_digest)
    _assert_failed(response, "SUBMISSION_BUNDLE_DIGEST_INVALID")
    assert response["canonical_source_bundle_sha256"] == ""


def test_item_inventory_types_order_samples_and_uniqueness(
    valid_payload: bytes,
) -> None:
    def reorder_record(bundle: dict[str, Any]) -> None:
        record = bundle["submission_items"][0]
        value = record.pop("pdb_id")
        record["pdb_id"] = value

    inventory = _mutated_payload(
        valid_payload, reorder_record, refresh_bundle=True,
    )
    _assert_failed(
        ADAPT(source_payload=inventory),
        "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH",
    )
    bool_index = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            "item_index_0based", False,
        ),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=bool_index),
        "SUBMISSION_ITEM_EXACT_TYPE_INVALID",
    )
    wrong_order = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"].__setitem__(
            slice(0, 2),
            list(reversed(bundle["submission_items"][:2])),
        ),
    )
    _assert_failed(
        ADAPT(source_payload=wrong_order),
        "SUBMISSION_ITEM_ORDER_INVALID",
    )

    def swap_samples(bundle: dict[str, Any]) -> None:
        first, second = bundle["submission_items"][:2]
        first["sample_index_row_id"], second["sample_index_row_id"] = (
            second["sample_index_row_id"],
            first["sample_index_row_id"],
        )

    sample_order = _mutated_payload(
        valid_payload, swap_samples, record_indices=(0, 1),
    )
    _assert_failed(
        ADAPT(source_payload=sample_order),
        "SUBMISSION_SAMPLE_ORDER_INVALID",
    )
    duplicate_sample = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][1].__setitem__(
            "sample_index_row_id",
            bundle["submission_items"][0]["sample_index_row_id"],
        ),
        record_indices=(1,),
    )
    _assert_failed(
        ADAPT(source_payload=duplicate_sample),
        "DUPLICATE_SAMPLE_IN_BUNDLE",
    )


def test_record_digest_invalid_and_duplicate(
    valid_payload: bytes,
) -> None:
    wrong = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            RECORD_DIGEST, "0" * 64,
        ),
    )
    _assert_failed(
        ADAPT(source_payload=wrong),
        "REVIEW_RECORD_DIGEST_INVALID",
    )
    duplicate = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][1].__setitem__(
            RECORD_DIGEST,
            bundle["submission_items"][0][RECORD_DIGEST],
        ),
    )
    _assert_failed(
        ADAPT(source_payload=duplicate),
        "DUPLICATE_REVIEW_DIGEST_IN_BUNDLE",
    )


def test_decision_completion_and_provenance_fail_closed(
    valid_payload: bytes,
) -> None:
    invalid_decision = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            "review_decision", "unknown",
        ),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=invalid_decision),
        "REVIEW_DECISION_INVALID",
    )
    incomplete = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            "review_completed", False,
        ),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=incomplete),
        "REVIEW_COMPLETION_INVALID",
    )
    unattested = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            "reviewer_provenance_attested", False,
        ),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=unattested),
        "REVIEWER_PROVENANCE_INVALID",
    )
    for field in (
        "reviewer_id",
        "review_rationale",
        "review_notes",
        "reviewer_provenance_attestor_id",
        "submission_source_label",
    ):
        missing = _mutated_payload(
            valid_payload,
            lambda bundle, name=field: bundle[
                "submission_items"
            ][0].__setitem__(name, ""),
            record_indices=(0,),
        )
        response = ADAPT(source_payload=missing)
        _assert_failed(response, "REVIEWER_PROVENANCE_INVALID")


def test_atom_set_validation(
    valid_payload: bytes,
) -> None:
    mutations = (
        lambda atoms: atoms.reverse(),
        lambda atoms: atoms.append(atoms[0]),
        lambda atoms: atoms.__setitem__(0, " padded "),
        lambda atoms: atoms.__setitem__(0, 7),
    )
    for mutate_atoms in mutations:
        def mutation(
            bundle: dict[str, Any],
            operation=mutate_atoms,
        ) -> None:
            operation(
                bundle["submission_items"][0][
                    "proposed_warhead_atom_ids"
                ]
            )

        payload = _mutated_payload(
            valid_payload, mutation, record_indices=(0,),
        )
        _assert_failed(ADAPT(source_payload=payload), "ATOM_SET_INVALID")


def test_boundary_record_validation_and_count(
    valid_payload: bytes,
) -> None:
    malformed = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            "proposed_boundary_records", [1, 2],
        ),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=malformed),
        "BOUNDARY_RECORDS_INVALID",
    )

    def reverse_boundary_fields(bundle: dict[str, Any]) -> None:
        records = bundle["submission_items"][0][
            "proposed_boundary_records"
        ]
        records[0] = dict(reversed(tuple(records[0].items())))

    wrong_fields = _mutated_payload(
        valid_payload, reverse_boundary_fields, record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=wrong_fields),
        "BOUNDARY_RECORDS_INVALID",
    )
    wrong_id = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0][
            "proposed_boundary_records"
        ][0].__setitem__("boundary_bond_id", "not-canonical"),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=wrong_id),
        "BOUNDARY_RECORDS_INVALID",
    )

    def duplicate_boundary(bundle: dict[str, Any]) -> None:
        records = bundle["submission_items"][0][
            "proposed_boundary_records"
        ]
        records[1] = copy.deepcopy(records[0])

    duplicate = _mutated_payload(
        valid_payload, duplicate_boundary, record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=duplicate),
        "BOUNDARY_RECORDS_INVALID",
    )

    def unsort_boundaries(bundle: dict[str, Any]) -> None:
        bundle["submission_items"][0][
            "proposed_boundary_records"
        ].reverse()

    unsorted = _mutated_payload(
        valid_payload, unsort_boundaries, record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=unsorted),
        "BOUNDARY_RECORDS_INVALID",
    )
    wrong_count = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0][
            "proposed_boundary_records"
        ].pop(),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=wrong_count),
        "ACCEPT_SEMANTICS_INVALID",
    )


def test_accept_revision_and_quarantine_semantics(
    valid_payload: bytes,
) -> None:
    accept_mismatch = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][0][
            "reviewed_warhead_atom_ids"
        ].pop(),
        record_indices=(0,),
    )
    _assert_failed(
        ADAPT(source_payload=accept_mismatch),
        "ACCEPT_SEMANTICS_INVALID",
    )

    def unchanged_revision(bundle: dict[str, Any]) -> None:
        item = bundle["submission_items"][2]
        item["reviewed_warhead_atom_ids"] = copy.deepcopy(
            item["proposed_warhead_atom_ids"]
        )
        item["reviewed_boundary_records"] = copy.deepcopy(
            item["proposed_boundary_records"]
        )

    revision = _mutated_payload(
        valid_payload, unchanged_revision, record_indices=(2,),
    )
    _assert_failed(
        ADAPT(source_payload=revision),
        "REVISION_SEMANTICS_INVALID",
    )
    valid_revision = ADAPT(source_payload=valid_payload)
    assert valid_revision["adapter_passed"] is True
    assert valid_revision["adapted_submissions"][2][
        "review_record_payload"
    ]["review_decision"] == (
        "revise_two_boundary_atom_set_and_boundaries"
    )

    def invalid_quarantine(bundle: dict[str, Any]) -> None:
        bundle["submission_items"][4]["review_decision"] = "quarantine"

    nonempty = _mutated_payload(
        valid_payload, invalid_quarantine, record_indices=(4,),
    )
    _assert_failed(
        ADAPT(source_payload=nonempty),
        "QUARANTINE_SEMANTICS_INVALID",
    )

    def completed_quarantine(bundle: dict[str, Any]) -> None:
        item = bundle["submission_items"][4]
        item["review_decision"] = "quarantine"
        item["reviewed_warhead_atom_ids"] = []
        item["reviewed_boundary_records"] = []

    empty = _mutated_payload(
        valid_payload, completed_quarantine, record_indices=(4,),
    )
    response = ADAPT(source_payload=empty)
    assert response["adapter_passed"] is True
    assert len(response["adapted_submissions"]) == 5
    assert response["adapted_submissions"][4]["review_record_payload"][
        "review_decision"
    ] == "quarantine"


def test_any_item_failure_is_atomic_and_failure_digest_is_valid(
    valid_payload: bytes,
) -> None:
    payload = _mutated_payload(
        valid_payload,
        lambda bundle: bundle["submission_items"][4].__setitem__(
            "review_completed", False,
        ),
        record_indices=(4,),
    )
    response = ADAPT(source_payload=payload)
    _assert_failed(response, "REVIEW_COMPLETION_INVALID")
    assert response["submission_batch_id"] == json.loads(
        valid_payload
    )["submission_batch_id"]
    assert response["canonical_source_bundle_sha256"] == json.loads(
        payload
    )[BUNDLE_DIGEST]


def test_public_call_has_no_predecessor_evaluator_or_write_effects(
    valid_payload: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {
        "compiler": 0,
        "sidecar": 0,
        "context": 0,
        "evaluator": 0,
        "writes": 0,
    }

    def forbidden(name: str):
        def fail(*_args, **_kwargs):
            calls[name] += 1
            raise AssertionError(f"{name} called")

        return fail

    monkeypatch.setattr(
        compiler,
        "compile_covapie_current11_multi_boundary_human_review_"
        "submission_bundle_v1",
        forbidden("compiler"),
    )
    monkeypatch.setattr(
        sidecar,
        "build_covapie_current11_multi_boundary_human_review_sidecar_v1",
        forbidden("sidecar"),
    )
    monkeypatch.setattr(
        ingestion_interface,
        "build_current11_warhead_boundary_review_ingestion_"
        "authority_context_v1",
        forbidden("context"),
    )
    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        forbidden("evaluator"),
    )
    for name in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, name, forbidden("writes"))

    response = ADAPT(source_payload=valid_payload)
    assert response["adapter_passed"] is True
    assert calls == {
        "compiler": 0,
        "sidecar": 0,
        "context": 0,
        "evaluator": 0,
        "writes": 0,
    }
