from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import stat
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_real_human_review_ingestion_execution_bundle_v1
    as execution,
)
from covalent_ext import (
    covapie_current11_real_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1
    as public_adapter,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FIELDS = (
    "ingestion_execution_bundle_version",
    "source_submission_bundle_sha256",
    "source_canonical_bundle_sha256",
    "submission_batch_id",
    "submission_adapter_response_sha256",
    "ingestion_interface_response_version",
    "authority_context_record_sha256",
    "batch_passed",
    "ingestion_result_records",
    "new_authority_records",
    "ingestion_interface_response_sha256",
    "ingestion_execution_bundle_sha256",
)
EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)


def _load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


PREPARER = _load_script(
    "covapie_current11_workspace_preparer_for_execution_tests",
    REPO_ROOT
    / "scripts/"
    "prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "human_review_workspace_v1.py",
)
CLI = _load_script(
    "covapie_current11_ingestion_execution_cli_for_tests",
    REPO_ROOT
    / "scripts/"
    "execute_covapie_current11_real_human_review_ingestion_v1.py",
)


def _csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with io.StringIO(payload.decode("utf-8"), newline="") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _csv_bytes(
    fields: tuple[str, ...],
    rows: list[dict[str, str]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _synthetic_completed_submission(
    *,
    revise_positions: frozenset[int] = frozenset(),
) -> bytes:
    workspace = PREPARER.build_workspace_payloads(REPO_ROOT)
    fields, rows = _csv_rows(workspace["review_worklist.csv"])
    _, options = _csv_rows(workspace["eligible_candidate_options.csv"])
    first_option_by_sample: dict[str, dict[str, str]] = {}
    for option in options:
        first_option_by_sample.setdefault(
            option["sample_index_row_id"],
            option,
        )
    for position, row in enumerate(rows):
        row.update(
            {
                "reviewer_id": "unit-test-human-reviewer",
                "review_rationale": f"Unit-test human rationale {position}.",
                "review_notes": f"Unit-test preserved note {position}.",
                "reviewer_provenance_attested": "true",
                "reviewer_provenance_attestor_id": "unit-test-human-attestor",
                "submission_source_label": "execution-bundle-unit-test",
                "review_completed": "true",
            }
        )
        if position in revise_positions:
            option = first_option_by_sample[row["sample_index_row_id"]]
            row.update(
                {
                    "review_decision": "revise_atom_set_and_boundary",
                    "selected_bridge_candidate_index_0based": "",
                    "selected_bridge_candidate_record_sha256": "",
                    "reviewed_warhead_atom_ids_json":
                        option["warhead_side_atom_ids"],
                    "reviewed_warhead_attachment_atom_id":
                        option["warhead_attachment_atom_id"],
                    "reviewed_nonwarhead_boundary_atom_id":
                        option["nonwarhead_boundary_atom_id"],
                    "reviewed_attachment_boundary_bond_order":
                        option["boundary_bond_order"],
                    "reviewed_boundary_bond_id": option["boundary_bond_id"],
                }
            )
            continue
        if 5 <= position <= 9:
            row.update(
                {
                    "review_decision": "quarantine",
                    "selected_bridge_candidate_index_0based": "",
                    "selected_bridge_candidate_record_sha256": "",
                    "reviewed_warhead_atom_ids_json": "[]",
                    "reviewed_warhead_attachment_atom_id": "",
                    "reviewed_nonwarhead_boundary_atom_id": "",
                    "reviewed_attachment_boundary_bond_order": "",
                    "reviewed_boundary_bond_id": "",
                }
            )
            continue
        option = first_option_by_sample[row["sample_index_row_id"]]
        row.update(
            {
                "review_decision": "select_admitted_candidate",
                "selected_bridge_candidate_index_0based":
                    option["source_bridge_candidate_index_0based"],
                "selected_bridge_candidate_record_sha256":
                    option["source_bridge_candidate_record_sha256"],
                "reviewed_warhead_atom_ids_json":
                    option["warhead_side_atom_ids"],
                "reviewed_warhead_attachment_atom_id":
                    option["warhead_attachment_atom_id"],
                "reviewed_nonwarhead_boundary_atom_id":
                    option["nonwarhead_boundary_atom_id"],
                "reviewed_attachment_boundary_bond_order":
                    option["boundary_bond_order"],
                "reviewed_boundary_bond_id": option["boundary_bond_id"],
            }
        )
    package_root = REPO_ROOT / PREPARER.PACKAGE_ROOT
    return compiler.compile_covapie_current11_real_human_review_submission_bundle_v1(
        review_worklist_csv=_csv_bytes(fields, rows),
        eligible_candidate_options_csv=
            workspace["eligible_candidate_options.csv"],
        package_index_csv=(package_root / PREPARER.INDEX_FILE).read_bytes(),
        package_candidate_options_csv=
            (package_root / PREPARER.OPTIONS_FILE).read_bytes(),
        review_record_templates_csv=
            (package_root / PREPARER.TEMPLATES_FILE).read_bytes(),
        submission_batch_id=
            "covapie_current11_execution_bundle_unit_test_batch_v1",
    )


@pytest.fixture(scope="session")
def synthetic_submission() -> bytes:
    return _synthetic_completed_submission()


def _build(source: bytes) -> bytes:
    return (
        execution
        .build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
            source_submission_bundle=source,
            repo_root=REPO_ROOT,
        )
    )


def _rehash_interface(response: dict[str, object]) -> None:
    response["interface_response_sha256"] = (
        ingestion_interface.interface_response_sha256(response)
    )


def _rehash_authority_and_result(
    response: dict[str, object],
    position: int,
) -> None:
    authority = response["new_authority_records"][position]
    result = response["ingestion_result_records"][position]
    authority["authority_record_sha256"] = (
        ingestion_design.authority_record_sha256(authority)
    )
    result["authority_record_sha256"] = authority["authority_record_sha256"]
    result["authority_disposition"] = authority["authority_disposition"]
    result["ingestion_result_sha256"] = (
        ingestion_design.ingestion_result_sha256(result)
    )
    _rehash_interface(response)


def _mutated_evaluator(
    monkeypatch: pytest.MonkeyPatch,
    mutation,
) -> None:
    original = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1
    )

    def evaluator(**arguments):
        response = copy.deepcopy(original(**arguments))
        mutation(response)
        return response

    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        evaluator,
    )


def test_public_signature_and_all_contract() -> None:
    function = (
        execution
        .build_covapie_current11_real_human_review_ingestion_execution_bundle_v1
    )
    assert execution.__all__ == (
        "build_covapie_current11_real_human_review_ingestion_execution_bundle_v1",
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "source_submission_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.return_annotation in {bytes, "bytes"}


@pytest.mark.parametrize(
    ("source", "root"),
    (
        (bytearray(), REPO_ROOT),
        (memoryview(b"{}"), REPO_ROOT),
        ("{}", REPO_ROOT),
        (b"{}", str(REPO_ROOT)),
        (b"{}", None),
    ),
)
def test_exact_bytes_and_path_types_are_required(
    source: object,
    root: object,
) -> None:
    with pytest.raises(ValueError):
        execution.build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
            source_submission_bundle=source,
            repo_root=root,
        )


def test_malformed_submission_is_rejected_before_downstream_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_arguments, **_keyword_arguments):
        raise AssertionError("downstream ingestion must not run")

    monkeypatch.setattr(
        ingestion_interface,
        "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
        forbidden,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        forbidden,
    )
    with pytest.raises(ValueError, match="SUBMISSION_ADAPTER"):
        _build(b"{}")


def test_public_chain_is_called_once_with_empty_existing_authorities(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"adapter": 0, "context": 0, "evaluator": 0, "validator": 0}
    observed_existing: list[object] = []
    original_adapter = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1
    )
    original_context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    original_evaluator = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1
    )
    original_validator = (
        ingestion_interface
        .validate_current11_warhead_boundary_review_ingestion_interface_response_v1
    )

    def adapter(*, source_payload: bytes):
        calls["adapter"] += 1
        return original_adapter(source_payload=source_payload)

    def context(root: Path):
        calls["context"] += 1
        return original_context(root)

    def evaluator(**arguments):
        calls["evaluator"] += 1
        observed_existing.append(arguments["existing_authorities"])
        return original_evaluator(**arguments)

    def validator(*arguments, **keyword_arguments):
        calls["validator"] += 1
        return original_validator(*arguments, **keyword_arguments)

    monkeypatch.setattr(
        public_adapter,
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        adapter,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
        context,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        evaluator,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "validate_current11_warhead_boundary_review_ingestion_interface_response_v1",
        validator,
    )
    _build(synthetic_submission)
    assert calls == {
        "adapter": 1,
        "context": 1,
        "evaluator": 1,
        # Once inside the committed evaluator and once explicitly by builder.
        "validator": 2,
    }
    assert observed_existing == [()]


def test_builder_does_not_directly_call_design_batch_evaluator() -> None:
    source = inspect.getsource(
        execution
        .build_covapie_current11_real_human_review_ingestion_execution_bundle_v1
    )
    assert "ingest_review_batch" not in source


def test_adapter_response_identity_tamper_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1
    )

    def tampered(*, source_payload: bytes):
        response = copy.deepcopy(original(source_payload=source_payload))
        response["submission_batch_id"] = "tampered-batch"
        return response

    monkeypatch.setattr(
        public_adapter,
        "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        tampered,
    )
    with pytest.raises(ValueError, match="ADAPTER"):
        _build(synthetic_submission)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda response: response.__setitem__(
            "interface_response_sha256", "0" * 64
        ),
        lambda response: response.__setitem__(
            "ingestion_result_records",
            list(response["ingestion_result_records"]),
        ),
        lambda response: response.__setitem__(
            "authority_context_record_sha256", "1" * 64
        ),
    ),
)
def test_interface_field_type_hash_or_linkage_tamper_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
) -> None:
    _mutated_evaluator(monkeypatch, mutation)
    with pytest.raises(ValueError):
        _build(synthetic_submission)


def test_failed_batch_fails_closed_even_with_validator_replaced(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutation(response):
        response["batch_passed"] = False
        _rehash_interface(response)

    _mutated_evaluator(monkeypatch, mutation)
    monkeypatch.setattr(
        ingestion_interface,
        "validate_current11_warhead_boundary_review_ingestion_interface_response_v1",
        lambda *_arguments, **_keyword_arguments: None,
    )
    with pytest.raises(ValueError, match="BATCH_INVALID"):
        _build(synthetic_submission)


def test_result_count_mismatch_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutation(response):
        response["ingestion_result_records"] = (
            response["ingestion_result_records"][:-1]
        )
        _rehash_interface(response)

    _mutated_evaluator(monkeypatch, mutation)
    with pytest.raises(ValueError):
        _build(synthetic_submission)


def test_authority_count_or_linkage_mismatch_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutation(response):
        response["new_authority_records"] = (
            response["new_authority_records"][:-1]
        )
        _rehash_interface(response)

    _mutated_evaluator(monkeypatch, mutation)
    with pytest.raises(ValueError):
        _build(synthetic_submission)


def test_duplicate_authority_sha_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutation(response):
        authorities = list(response["new_authority_records"])
        authorities[1] = copy.deepcopy(authorities[0])
        response["new_authority_records"] = tuple(authorities)
        _rehash_interface(response)

    _mutated_evaluator(monkeypatch, mutation)
    with pytest.raises(ValueError):
        _build(synthetic_submission)


def test_selected_authority_effect_tamper_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutation(response):
        authority = response["new_authority_records"][0]
        authority["authority_status"] = "quarantined"
        _rehash_authority_and_result(response, 0)

    _mutated_evaluator(monkeypatch, mutation)
    with pytest.raises(ValueError):
        _build(synthetic_submission)


def test_quarantine_authority_effect_tamper_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutation(response):
        authority = response["new_authority_records"][5]
        authority["authority_disposition"] = "reviewed_authority_materialized"
        authority["authority_status"] = "active"
        authority["complete_warhead_atom_set_authority_available"] = True
        authority["exact_one_attachment_boundary_authority_available"] = True
        authority["sample_quarantined"] = False
        _rehash_authority_and_result(response, 5)

    _mutated_evaluator(monkeypatch, mutation)
    with pytest.raises(ValueError):
        _build(synthetic_submission)


@pytest.mark.parametrize("field", ("atoms", "boundary"))
def test_non_000011_active_authority_atom_or_boundary_drift_fails_linkage(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    def mutation(response):
        authority = response["new_authority_records"][0]
        if field == "atoms":
            authority["reviewed_warhead_atom_ids"].append("Z9")
        else:
            authority["reviewed_boundary_bond_id"] = "forged|boundary|single"
        _rehash_authority_and_result(response, 0)

    _mutated_evaluator(monkeypatch, mutation)
    monkeypatch.setattr(
        ingestion_interface,
        "validate_current11_warhead_boundary_review_ingestion_interface_response_v1",
        lambda *_arguments, **_keyword_arguments: None,
    )
    with pytest.raises(
        ValueError,
        match="^CURRENT11_AUTHORITY_REVIEW_LINKAGE_INVALID:0$",
    ):
        _build(synthetic_submission)


@pytest.mark.parametrize("field", ("reviewer_id", "pdb_id"))
def test_active_authority_reviewer_or_identity_drift_fails_linkage(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    def mutation(response):
        authority = response["new_authority_records"][0]
        authority[field] = (
            "different-human-reviewer"
            if field == "reviewer_id"
            else "ZZZZ"
        )
        _rehash_authority_and_result(response, 0)

    _mutated_evaluator(monkeypatch, mutation)
    monkeypatch.setattr(
        ingestion_interface,
        "validate_current11_warhead_boundary_review_ingestion_interface_response_v1",
        lambda *_arguments, **_keyword_arguments: None,
    )
    with pytest.raises(
        ValueError,
        match="^CURRENT11_AUTHORITY_REVIEW_LINKAGE_INVALID:0$",
    ):
        _build(synthetic_submission)


def test_current11_revise_profile_is_rejected_after_public_ingestion() -> None:
    submission = _synthetic_completed_submission(
        revise_positions=frozenset({0}),
    )
    adapted = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1(
            source_payload=submission,
        )
    )
    assert adapted["adapter_passed"] is True
    assert (
        adapted["adapted_submissions"][0][0]["review_decision"]
        == "revise_atom_set_and_boundary"
    )
    context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            REPO_ROOT
        )
    )
    response = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1(
            submissions=adapted["adapted_submissions"],
            authority_context=context,
            existing_authorities=(),
        )
    )
    assert response["batch_passed"] is True
    assert (
        response["new_authority_records"][0]["review_decision"]
        == "revise_atom_set_and_boundary"
    )
    with pytest.raises(
        ValueError,
        match="^CURRENT11_REVIEW_DECISION_PROFILE_INVALID$",
    ):
        _build(submission)


def test_deep_nested_malformed_json_is_value_error_before_ingestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"context": 0, "evaluator": 0}

    def context(*_arguments, **_keyword_arguments):
        calls["context"] += 1
        raise AssertionError("context builder must not run")

    def evaluator(*_arguments, **_keyword_arguments):
        calls["evaluator"] += 1
        raise AssertionError("evaluator must not run")

    monkeypatch.setattr(
        ingestion_interface,
        "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
        context,
    )
    monkeypatch.setattr(
        ingestion_interface,
        "evaluate_current11_warhead_boundary_review_ingestion_v1",
        evaluator,
    )
    deeply_nested = b"[" * 2000 + b"0" + b"]" * 2000
    with pytest.raises(ValueError):
        _build(deeply_nested)
    assert calls == {"context": 0, "evaluator": 0}


@pytest.mark.parametrize("field", ("atoms", "boundary"))
def test_sample_000011_atom_or_boundary_drift_fails_closed(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    def mutation(response):
        authority = response["new_authority_records"][10]
        if field == "atoms":
            authority["reviewed_warhead_atom_ids"].append("Z9")
        else:
            authority["reviewed_boundary_bond_id"] = "N1|Z9|single"
        _rehash_authority_and_result(response, 10)

    _mutated_evaluator(monkeypatch, mutation)
    with pytest.raises(
        ValueError,
        match="CURRENT11_AUTHORITY_REVIEW_LINKAGE_INVALID:10|000011",
    ):
        _build(synthetic_submission)


def test_valid_mixed_execution_bundle_schema_and_semantics(
    synthetic_submission: bytes,
) -> None:
    payload = _build(synthetic_submission)
    bundle = json.loads(payload)
    adapted = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1(
            source_payload=synthetic_submission,
        )
    )
    assert tuple(bundle) == EXPECTED_FIELDS
    assert bundle["ingestion_execution_bundle_version"] == (
        "covapie_current11_real_human_review_ingestion_execution_bundle_v1"
    )
    assert type(bundle["batch_passed"]) is bool
    assert type(bundle["ingestion_result_records"]) is list
    assert type(bundle["new_authority_records"]) is list
    assert len(bundle["ingestion_result_records"]) == 11
    assert len(bundle["new_authority_records"]) == 11
    assert all(
        tuple(record) == tuple(ingestion_design.INGESTION_RESULT_FIELDS)
        for record in bundle["ingestion_result_records"]
    )
    assert all(
        tuple(record) == tuple(ingestion_design.AUTHORITY_RECORD_FIELDS)
        for record in bundle["new_authority_records"]
    )
    assert tuple(
        record["sample_index_row_id"]
        for record in bundle["ingestion_result_records"]
    ) == EXPECTED_SAMPLES
    assert tuple(
        record["sample_index_row_id"]
        for record in bundle["new_authority_records"]
    ) == EXPECTED_SAMPLES
    assert all(
        record["authority_status"] == "quarantined"
        and record["sample_quarantined"] is True
        for record in bundle["new_authority_records"][5:10]
    )
    authority_000011 = bundle["new_authority_records"][10]
    assert authority_000011["reviewed_warhead_atom_ids"] == [
        "C2", "C4", "C5", "C6", "F5", "N1", "N3", "O2", "O4",
    ]
    assert authority_000011["reviewed_boundary_bond_id"] == "C1'|N1|single"
    direct_fields = (
        "sample_index_row_id",
        "pdb_id",
        "ligand_comp_id",
        "warhead_type_candidate_class_id",
        "reaction_family_id",
        "warhead_rule_id",
        "source_assignment_record_sha256",
        "source_proposal_record_sha256",
        "source_candidate_set_sha256",
        "review_decision",
        "reviewed_warhead_atom_ids",
        "reviewed_warhead_attachment_atom_id",
        "reviewed_nonwarhead_boundary_atom_id",
        "reviewed_attachment_boundary_bond_order",
        "reviewed_boundary_bond_id",
        "reviewer_id",
    )
    for position, (authority, submission) in enumerate(zip(
        bundle["new_authority_records"],
        adapted["adapted_submissions"],
    )):
        review, envelope = submission
        assert all(
            authority[field] == review[field] for field in direct_fields
        )
        assert authority["source_review_record_sha256"] == (
            review["review_record_sha256"]
        )
        assert authority["source_ingestion_envelope_sha256"] == (
            envelope["ingestion_envelope_sha256"]
        )
        assert authority["review_rationale_sha256"] == hashlib.sha256(
            review["review_rationale"].encode("utf-8")
        ).hexdigest()
        assert authority["supersedes_authority_record_sha256"] == ""
        assert authority["review_decision"] == (
            "select_admitted_candidate"
            if position in {0, 1, 2, 3, 4, 10}
            else "quarantine"
        )
    hash_payload = {
        field: bundle[field]
        for field in EXPECTED_FIELDS
        if field != "ingestion_execution_bundle_sha256"
    }
    expected_sha = hashlib.sha256(json.dumps(
        hash_payload,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    assert bundle["ingestion_execution_bundle_sha256"] == expected_sha
    assert len(payload) < 1024 * 1024
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in payload
    assert b"\n" not in payload


def test_input_is_unchanged_and_output_is_byte_deterministic(
    synthetic_submission: bytes,
) -> None:
    snapshot = copy.copy(synthetic_submission)
    first = _build(synthetic_submission)
    second = _build(synthetic_submission)
    assert synthetic_submission == snapshot
    assert first == second
    assert type(first) is bytes


def test_production_builder_performs_no_file_writes(
    synthetic_submission: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_arguments, **_keyword_arguments):
        raise AssertionError("production builder attempted a file write")

    for method in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, method, forbidden)
    assert json.loads(_build(synthetic_submission))["batch_passed"] is True


def test_cli_rejects_repository_internal_output(
    tmp_path: Path,
    synthetic_submission: bytes,
) -> None:
    source = tmp_path / "submission.json"
    source.write_bytes(synthetic_submission)
    destination = REPO_ROOT / "forbidden-ingestion-execution-output.json"
    with pytest.raises(ValueError, match="outside the Git repository"):
        CLI.execute_submission_to_file(
            repo_root=REPO_ROOT,
            submission_file=source,
            output_file=destination,
        )
    assert not destination.exists()


def test_cli_rejects_existing_output_and_symlink(
    tmp_path: Path,
    synthetic_submission: bytes,
) -> None:
    source = tmp_path / "submission.json"
    source.write_bytes(synthetic_submission)
    existing = tmp_path / "existing.json"
    existing.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        CLI.execute_submission_to_file(
            repo_root=REPO_ROOT,
            submission_file=source,
            output_file=existing,
        )
    symlink = tmp_path / "symlink.json"
    symlink.symlink_to(tmp_path / "missing.json")
    with pytest.raises(FileExistsError, match="must not be a symlink"):
        CLI.execute_submission_to_file(
            repo_root=REPO_ROOT,
            submission_file=source,
            output_file=symlink,
        )
    assert existing.read_text(encoding="utf-8") == "preserve"
    assert symlink.is_symlink()


def test_cli_rejects_submission_symlink(
    tmp_path: Path,
    synthetic_submission: bytes,
) -> None:
    real_source = tmp_path / "real-submission.json"
    real_source.write_bytes(synthetic_submission)
    source = tmp_path / "submission-link.json"
    source.symlink_to(real_source)
    with pytest.raises(ValueError, match="regular file"):
        CLI.execute_submission_to_file(
            repo_root=REPO_ROOT,
            submission_file=source,
            output_file=tmp_path / "output.json",
        )


def test_cli_success_creates_one_0644_json_without_modifying_source(
    tmp_path: Path,
    synthetic_submission: bytes,
) -> None:
    source = tmp_path / "submission.json"
    source.write_bytes(synthetic_submission)
    source_snapshot = source.read_bytes()
    output_parent = tmp_path / "output"
    output_parent.mkdir()
    destination = output_parent / "execution.json"
    result = CLI.execute_submission_to_file(
        repo_root=REPO_ROOT,
        submission_file=source,
        output_file=destination,
    )
    assert tuple(path.name for path in output_parent.iterdir()) == (
        "execution.json",
    )
    assert stat.S_IMODE(destination.stat().st_mode) == 0o644
    bundle = json.loads(destination.read_bytes())
    assert result["ingestion_execution_bundle_sha256"] == (
        bundle["ingestion_execution_bundle_sha256"]
    )
    assert result["result_count"] == 11
    assert result["authority_count"] == 11
    assert result["active_authority_count"] == 6
    assert result["quarantined_authority_count"] == 5
    assert source.read_bytes() == source_snapshot


def test_cli_pre_link_and_post_link_failures_leave_no_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_destination = tmp_path / "first.json"

    def failed_link(*_arguments, **_keyword_arguments):
        raise OSError("synthetic link failure")

    monkeypatch.setattr(os, "link", failed_link)
    with pytest.raises(OSError, match="synthetic link failure"):
        CLI._atomic_create_external_file(first_destination, b"{}")
    assert list(tmp_path.iterdir()) == []

    monkeypatch.undo()
    second_destination = tmp_path / "second.json"
    real_link = os.link

    def link_then_fail(*arguments, **keyword_arguments):
        real_link(*arguments, **keyword_arguments)
        raise OSError("synthetic post-link failure")

    monkeypatch.setattr(os, "link", link_then_fail)
    with pytest.raises(OSError, match="synthetic post-link failure"):
        CLI._atomic_create_external_file(second_destination, b"{}")
    assert list(tmp_path.iterdir()) == []


def test_cli_main_prints_only_exact_summary_fields(
    tmp_path: Path,
    synthetic_submission: bytes,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "submission.json"
    source.write_bytes(synthetic_submission)
    destination = tmp_path / "execution.json"
    assert CLI.main((
        "--repo-root", str(REPO_ROOT),
        "--submission-file", str(source),
        "--output-file", str(destination),
    )) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert tuple(
        line.split("=", 1)[0] for line in captured.out.splitlines()
    ) == (
        "output_path",
        "source_submission_bundle_sha256",
        "ingestion_execution_bundle_sha256",
        "submission_batch_id",
        "result_count",
        "authority_count",
        "active_authority_count",
        "quarantined_authority_count",
        "batch_passed",
    )
