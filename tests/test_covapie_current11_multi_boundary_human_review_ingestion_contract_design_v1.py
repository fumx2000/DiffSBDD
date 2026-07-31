from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

import pytest

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1
    as adapter,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10"
)
SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)


def _load_checker():
    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_ingestion_contract_design_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_ingestion_design_checker_for_tests", path,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


CHECKER = _load_checker()


@pytest.fixture(scope="session")
def synthetic_case() -> tuple[bytes, bytes, bytes, bytes]:
    return CHECKER._synthetic_case(REPO_ROOT)


@pytest.fixture(scope="session")
def fresh_response(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> dict[str, Any]:
    return CHECKER._evaluate(REPO_ROOT, synthetic_case)


@pytest.fixture(scope="session")
def expected_v1_context_sha256() -> str:
    context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            REPO_ROOT
        )
    )
    return context.context_record[
        "ingestion_authority_context_record_sha256"
    ]


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


def _mutated_submission_case(
    case: tuple[bytes, bytes, bytes, bytes],
    mutation: Callable[[dict[str, Any]], None],
    *,
    record_indices: tuple[int, ...] = (),
) -> tuple[bytes, bytes, bytes, bytes]:
    bundle = json.loads(case[0])
    mutation(bundle)
    for index in record_indices:
        record = bundle["submission_items"][index]
        record["multi_boundary_review_record_sha256"] = _canonical_sha(
            record, "multi_boundary_review_record_sha256",
        )
    bundle["multi_boundary_submission_bundle_sha256"] = _canonical_sha(
        bundle, "multi_boundary_submission_bundle_sha256",
    )
    submission = _ordered_bytes(bundle)
    response = (
        adapter
        .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            source_payload=submission,
        )
    )
    return submission, _ordered_bytes(response), case[2], case[3]


def _evaluate(case, existing=()):
    return CHECKER._evaluate(REPO_ROOT, case, existing=tuple(existing))


def _mutated_v1_execution_case(
    case: tuple[bytes, bytes, bytes, bytes],
    mutation: Callable[[dict[str, Any]], None],
    *,
    refresh_interface_digest: bool,
) -> tuple[bytes, bytes, bytes, bytes]:
    execution = json.loads(case[3])
    mutation(execution)
    if refresh_interface_digest:
        interface_response = {
            "interface_response_version":
                execution["ingestion_interface_response_version"],
            "authority_context_record_sha256":
                execution["authority_context_record_sha256"],
            "batch_passed": execution["batch_passed"],
            "ingestion_result_records":
                execution["ingestion_result_records"],
            "new_authority_records": execution["new_authority_records"],
            "interface_response_sha256":
                execution["ingestion_interface_response_sha256"],
        }
        execution["ingestion_interface_response_sha256"] = _canonical_sha(
            interface_response, "interface_response_sha256",
        )
    execution["ingestion_execution_bundle_sha256"] = _canonical_sha(
        execution, "ingestion_execution_bundle_sha256",
    )
    return case[0], case[1], case[2], _ordered_bytes(execution)


def _assert_atomic_failure(
    response: dict[str, Any],
    reason: str,
) -> None:
    assert response["batch_passed"] is False
    assert response["new_authority_records"] == ()
    assert len(response["ingestion_result_records"]) == 5
    assert [row["reason"] for row in response["ingestion_result_records"]].count(
        reason
    ) == 1
    assert [row["reason"] for row in response["ingestion_result_records"]].count(
        "BATCH_ATOMICITY_ABORTED"
    ) == 4


def test_design_module_is_private_and_import_silent() -> None:
    assert design.__all__ == ()
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import "
            "covapie_current11_multi_boundary_human_review_"
            "ingestion_contract_design_v1",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_future_public_signature_is_frozen_but_not_exposed() -> None:
    assert design.FUTURE_PUBLIC_API_SIGNATURE.startswith(
        "def evaluate_covapie_current11_multi_boundary_human_review_"
        "ingestion_v1("
    )
    assert not hasattr(
        design,
        "evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1",
    )
    signature = inspect.signature(
        design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1
    )
    assert tuple(signature.parameters) == (
        "adapter_response_payload",
        "source_multi_boundary_submission_bundle",
        "source_v1_submission_bundle",
        "source_v1_ingestion_execution_bundle",
        "repo_root",
        "existing_multi_boundary_authority_records",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_exact10_authority_context(fresh_response: dict[str, Any]) -> None:
    assert len(design.MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_FIELDS) == 10
    assert design.MULTI_BOUNDARY_INGESTION_AUTHORITY_CONTEXT_FIELDS == (
        "multi_boundary_ingestion_authority_context_version",
        "committed_single_boundary_authority_context_sha256",
        "source_v1_submission_bundle_sha256",
        "source_v1_ingestion_execution_bundle_filesystem_sha256",
        "source_v1_ingestion_execution_bundle_sha256",
        "source_multi_boundary_submission_bundle_filesystem_sha256",
        "source_multi_boundary_submission_bundle_sha256",
        "source_adapter_response_filesystem_sha256",
        "source_adapter_response_sha256",
        "multi_boundary_ingestion_authority_context_record_sha256",
    )
    assert len(fresh_response["authority_context_record_sha256"]) == 64


def test_exact29_authority(fresh_response: dict[str, Any]) -> None:
    assert len(design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS) == 29
    for record in fresh_response["new_authority_records"]:
        assert tuple(record) == design.MULTI_BOUNDARY_AUTHORITY_RECORD_FIELDS
        design._validate_authority_record(record)


def test_exact18_result(fresh_response: dict[str, Any]) -> None:
    assert len(design.MULTI_BOUNDARY_INGESTION_RESULT_FIELDS) == 18
    for record in fresh_response["ingestion_result_records"]:
        assert tuple(record) == design.MULTI_BOUNDARY_INGESTION_RESULT_FIELDS
        design._validate_result_record(record)


def test_exact6_response_uses_tuples(
    fresh_response: dict[str, Any],
) -> None:
    assert tuple(fresh_response) == (
        design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS
    )
    assert type(fresh_response["ingestion_result_records"]) is tuple
    assert type(fresh_response["new_authority_records"]) is tuple
    design._validate_interface_response(fresh_response)


def test_fresh_410_profile_has_five_active_authorities(
    fresh_response: dict[str, Any],
) -> None:
    authorities = fresh_response["new_authority_records"]
    assert fresh_response["batch_passed"] is True
    assert len(fresh_response["ingestion_result_records"]) == 5
    assert len(authorities) == 5
    assert [row["review_decision"] for row in authorities].count(
        "accept_verified_two_boundary_proposal"
    ) == 4
    assert [row["review_decision"] for row in authorities].count(
        "revise_two_boundary_atom_set_and_boundaries"
    ) == 1
    assert all(row["authority_status"] == "active" for row in authorities)


def test_authority_result_and_response_digests(
    fresh_response: dict[str, Any],
) -> None:
    for record in fresh_response["new_authority_records"]:
        assert record["multi_boundary_authority_record_sha256"] == (
            _canonical_sha(
                record, "multi_boundary_authority_record_sha256",
            )
        )
    for result in fresh_response["ingestion_result_records"]:
        assert result["multi_boundary_ingestion_result_sha256"] == (
            _canonical_sha(
                result, "multi_boundary_ingestion_result_sha256",
            )
        )
    assert fresh_response[
        "multi_boundary_ingestion_interface_response_sha256"
    ] == _canonical_sha(
        fresh_response,
        "multi_boundary_ingestion_interface_response_sha256",
    )


def test_submission_adapter_source_linkage(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(synthetic_case[0])
    response = json.loads(synthetic_case[1])
    assert response["source_payload_sha256"] == hashlib.sha256(
        synthetic_case[0]
    ).hexdigest()
    assert response["canonical_source_bundle_sha256"] == bundle[
        "multi_boundary_submission_bundle_sha256"
    ]
    assert [
        envelope["review_record_payload"]
        for envelope in response["adapted_submissions"]
    ] == bundle["submission_items"]


def test_v1_execution_old_authority_linkage(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    execution = json.loads(synthetic_case[3])
    old = {
        row["sample_index_row_id"]: row
        for row in execution["new_authority_records"]
        if row["sample_index_row_id"] in SAMPLES
    }
    for authority in fresh_response["new_authority_records"]:
        predecessor = old[authority["sample_index_row_id"]]
        assert authority[
            "source_v1_quarantine_authority_record_sha256"
        ] == predecessor["authority_record_sha256"]
        assert authority["source_v1_review_record_sha256"] == predecessor[
            "source_review_record_sha256"
        ]


def test_all_five_v1_authorities_remain_quarantined(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    execution = json.loads(synthetic_case[3])
    old = [
        row for row in execution["new_authority_records"]
        if row["sample_index_row_id"] in SAMPLES
    ]
    assert len(old) == 5
    assert all(row["authority_status"] == "quarantined" for row in old)
    assert all(row["sample_quarantined"] is True for row in old)
    assert all(
        row["exact_one_attachment_boundary_authority_available"] is False
        for row in old
    )


def test_accept_graph_is_revalidated(
    fresh_response: dict[str, Any],
) -> None:
    accepts = [
        row for row in fresh_response["new_authority_records"]
        if row["review_decision"]
        == "accept_verified_two_boundary_proposal"
    ]
    assert len(accepts) == 4
    assert all(len(row["reviewed_boundary_records"]) == 2 for row in accepts)


def test_revise_graph_is_revalidated(
    fresh_response: dict[str, Any],
) -> None:
    revised = [
        row for row in fresh_response["new_authority_records"]
        if row["review_decision"]
        == "revise_two_boundary_atom_set_and_boundaries"
    ]
    assert len(revised) == 1
    assert len(revised[0]["reviewed_boundary_records"]) == 2


def test_disconnected_reviewed_set_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        item = bundle["submission_items"][0]
        atoms = ["C1", "C19", "C22", "C42", "O23"]
        item["proposed_warhead_atom_ids"] = atoms
        item["reviewed_warhead_atom_ids"] = atoms

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(0,),
    )
    _assert_atomic_failure(
        _evaluate(case), "REVIEWED_GRAPH_INVARIANT_INVALID",
    )


def test_local_reaction_center_cut_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        item = bundle["submission_items"][0]
        atoms = [
            atom for atom in item["proposed_warhead_atom_ids"]
            if atom != "O23"
        ]
        item["proposed_warhead_atom_ids"] = atoms
        item["reviewed_warhead_atom_ids"] = atoms

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(0,),
    )
    _assert_atomic_failure(
        _evaluate(case), "REVIEWED_GRAPH_INVARIANT_INVALID",
    )


def test_non_two_boundary_graph_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        item = bundle["submission_items"][0]
        atoms = ["C19", "C22", "C42", "O23"]
        item["proposed_warhead_atom_ids"] = atoms
        item["reviewed_warhead_atom_ids"] = atoms

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(0,),
    )
    _assert_atomic_failure(
        _evaluate(case), "REVIEWED_GRAPH_INVARIANT_INVALID",
    )


def test_boundary_order_and_bond_order_error_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        item = bundle["submission_items"][0]
        for field in ("proposed_boundary_records", "reviewed_boundary_records"):
            boundary = item[field][0]
            boundary["boundary_bond_order"] = "double"
            boundary["boundary_bond_id"] = "C16|N18|double"
            item[field].sort(key=lambda row: row["boundary_bond_id"])

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(0,),
    )
    _assert_atomic_failure(
        _evaluate(case), "REVIEWED_GRAPH_INVARIANT_INVALID",
    )


def test_wrong_committed_parent_graph_sha_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = sidecar._committed_sources
    calls = 0

    def changed(*arguments, **keywords):
        nonlocal calls
        calls += 1
        values = original(*arguments, **keywords)
        if calls != 2:
            return values
        packages, proposals, assignments, atoms, bonds = values
        changed_proposals = {
            key: copy.deepcopy(value) for key, value in proposals.items()
        }
        changed_proposals[SAMPLES[0]][
            "component_parent_graph_sha256"
        ] = "0" * 64
        return (
            packages,
            MappingProxyType(changed_proposals),
            assignments,
            atoms,
            bonds,
        )

    monkeypatch.setattr(sidecar, "_committed_sources", changed)
    _assert_atomic_failure(
        _evaluate(synthetic_case), "PARENT_GRAPH_LINEAGE_MISMATCH",
    )


def test_wrong_v1_authority_sha_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        bundle["submission_items"][0][
            "source_v1_quarantine_authority_record_sha256"
        ] = "0" * 64

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(0,),
    )
    _assert_atomic_failure(
        _evaluate(case),
        "V1_QUARANTINE_AUTHORITY_LINEAGE_MISMATCH",
    )


def test_wrong_evidence_and_review_lineage_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        item = bundle["submission_items"][1]
        item["source_evidence_record_sha256"] = "1" * 64

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(1,),
    )
    _assert_atomic_failure(
        _evaluate(case), "REVIEW_IDENTITY_LINKAGE_MISMATCH",
    )


def test_incomplete_review_is_rejected_before_ingestion(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    case = _mutated_submission_case(
        synthetic_case,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            "review_completed", False,
        ),
        record_indices=(0,),
    )
    response = _evaluate(case)
    assert response["batch_passed"] is False
    assert response["ingestion_result_records"] == ()


def test_invalid_provenance_is_rejected_before_ingestion(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    case = _mutated_submission_case(
        synthetic_case,
        lambda bundle: bundle["submission_items"][0].__setitem__(
            "reviewer_provenance_attested", False,
        ),
        record_indices=(0,),
    )
    response = _evaluate(case)
    assert response["batch_passed"] is False
    assert response["ingestion_result_records"] == ()


def test_failed_adapter_response_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    failed = (
        adapter
        .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            source_payload=b"{}",
        )
    )
    case = (
        synthetic_case[0],
        _ordered_bytes(failed),
        synthetic_case[2],
        synthetic_case[3],
    )
    response = _evaluate(case)
    assert response["batch_passed"] is False
    assert response["ingestion_result_records"] == ()


def test_adapter_response_digest_error_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    response = json.loads(synthetic_case[1])
    response[
        "multi_boundary_submission_adapter_response_sha256"
    ] = "0" * 64
    case = (
        synthetic_case[0],
        _ordered_bytes(response),
        synthetic_case[2],
        synthetic_case[3],
    )
    _assert_atomic_failure(
        _evaluate(case), "ADAPTER_RESPONSE_INVALID",
    )


def test_envelope_digest_error_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    response = json.loads(synthetic_case[1])
    response["adapted_submissions"][0][
        "multi_boundary_ingestion_envelope_sha256"
    ] = "0" * 64
    response[
        "multi_boundary_submission_adapter_response_sha256"
    ] = _canonical_sha(
        response,
        "multi_boundary_submission_adapter_response_sha256",
    )
    case = (
        synthetic_case[0],
        _ordered_bytes(response),
        synthetic_case[2],
        synthetic_case[3],
    )
    _assert_atomic_failure(
        _evaluate(case), "INGESTION_ENVELOPE_DIGEST_INVALID",
    )


def test_review_record_digest_error_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(synthetic_case[0])
    bundle["submission_items"][0][
        "multi_boundary_review_record_sha256"
    ] = "0" * 64
    bundle["multi_boundary_submission_bundle_sha256"] = _canonical_sha(
        bundle, "multi_boundary_submission_bundle_sha256",
    )
    case = (
        _ordered_bytes(bundle),
        synthetic_case[1],
        synthetic_case[2],
        synthetic_case[3],
    )
    _assert_atomic_failure(
        _evaluate(case), "REVIEW_RECORD_DIGEST_INVALID",
    )


def test_duplicate_sample_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        bundle["submission_items"][1]["sample_index_row_id"] = (
            bundle["submission_items"][0]["sample_index_row_id"]
        )

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(1,),
    )
    assert _evaluate(case)["batch_passed"] is False


def test_duplicate_review_sha_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    bundle = json.loads(synthetic_case[0])
    bundle["submission_items"][1][
        "multi_boundary_review_record_sha256"
    ] = bundle["submission_items"][0][
        "multi_boundary_review_record_sha256"
    ]
    bundle["multi_boundary_submission_bundle_sha256"] = _canonical_sha(
        bundle, "multi_boundary_submission_bundle_sha256",
    )
    case = (
        _ordered_bytes(bundle),
        synthetic_case[1],
        synthetic_case[2],
        synthetic_case[3],
    )
    assert _evaluate(case)["batch_passed"] is False


def test_valid_quarantine_semantics(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        item = bundle["submission_items"][4]
        item["review_decision"] = "quarantine"
        item["reviewed_warhead_atom_ids"] = []
        item["reviewed_boundary_records"] = []

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(4,),
    )
    response = _evaluate(case)
    assert response["batch_passed"] is True
    authority = response["new_authority_records"][4]
    assert authority["authority_status"] == "quarantined"
    assert authority["sample_quarantined"] is True
    assert authority["reviewed_warhead_atom_ids"] == []
    assert authority["reviewed_boundary_records"] == []


def test_nonempty_quarantine_is_rejected(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        bundle["submission_items"][4]["review_decision"] = "quarantine"

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(4,),
    )
    response = _evaluate(case)
    assert response["batch_passed"] is False
    assert response["ingestion_result_records"] == ()


def test_full_fresh_authority_output_order(
    fresh_response: dict[str, Any],
) -> None:
    assert tuple(
        row["sample_index_row_id"]
        for row in fresh_response["new_authority_records"]
    ) == SAMPLES
    assert len({
        row["multi_boundary_authority_record_sha256"]
        for row in fresh_response["new_authority_records"]
    }) == 5


def test_full_idempotent_replay(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    replay = _evaluate(
        synthetic_case, fresh_response["new_authority_records"],
    )
    assert replay["batch_passed"] is True
    assert replay["new_authority_records"] == ()
    assert all(
        row["reason"] == "IDEMPOTENT_REPLAY"
        and row["idempotent_replay"] is True
        for row in replay["ingestion_result_records"]
    )


def test_mixed_fresh_and_replay(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    replay = _evaluate(
        synthetic_case, fresh_response["new_authority_records"][:2],
    )
    assert replay["batch_passed"] is True
    assert [row["reason"] for row in replay["ingestion_result_records"]] == [
        "IDEMPOTENT_REPLAY",
        "IDEMPOTENT_REPLAY",
        "PASSED",
        "PASSED",
        "PASSED",
    ]
    assert len(replay["new_authority_records"]) == 3


def test_conflicting_reingestion_fails_atomically(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    conflict = copy.deepcopy(fresh_response["new_authority_records"][0])
    conflict["review_notes_sha256"] = "f" * 64
    conflict["multi_boundary_authority_record_sha256"] = _canonical_sha(
        conflict, "multi_boundary_authority_record_sha256",
    )
    response = _evaluate(synthetic_case, (conflict,))
    _assert_atomic_failure(
        response, "CONFLICTING_REVIEW_REINGESTION",
    )
    assert response["ingestion_result_records"][0][
        "conflicting_existing_authority"
    ] is True


def test_malformed_existing_authority_set_fails_closed(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    response = _evaluate(
        synthetic_case,
        ({"authority_record_version": "legacy_exact_one_v1"},),
    )
    _assert_atomic_failure(response, "EXISTING_AUTHORITY_SET_INVALID")


def test_batch_atomicity_discards_other_candidates(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    def mutation(bundle):
        item = bundle["submission_items"][2]
        atoms = item["reviewed_warhead_atom_ids"][:-1]
        item["reviewed_warhead_atom_ids"] = atoms

    case = _mutated_submission_case(
        synthetic_case, mutation, record_indices=(2,),
    )
    response = _evaluate(case)
    assert response["batch_passed"] is False
    assert response["new_authority_records"] == ()
    assert len(response["ingestion_result_records"]) == 5


def test_evaluation_is_deterministic(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    assert _evaluate(synthetic_case) == _evaluate(synthetic_case)


def test_all_exact_byte_inputs_are_unchanged(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    before = tuple(bytes(value) for value in synthetic_case)
    _evaluate(synthetic_case)
    assert synthetic_case == before


def test_call_budget_and_zero_filesystem_writes() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            str(PYTHON),
            "-B",
            "scripts/check_covapie_current11_multi_boundary_"
            "human_review_ingestion_contract_design_v1.py",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    expected_lines = (
        "sidecar_builder_calls_per_evaluation=1",
        "authority_context_builder_calls_per_evaluation=2",
        "compiler_calls_per_evaluation=0",
        "adapter_calls_per_evaluation=0",
        "predecessor_ingestion_evaluator_calls_per_evaluation=0",
        "files_written=false",
        "durable_authority_created=false",
        "v1_authority_modified=false",
    )
    assert all(line in completed.stdout for line in expected_lines)


def test_v1_authority_objects_and_source_bytes_are_unchanged(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
) -> None:
    before_execution = copy.deepcopy(json.loads(synthetic_case[3]))
    before_sources = tuple(bytes(value) for value in synthetic_case)
    _evaluate(synthetic_case)
    assert json.loads(synthetic_case[3]) == before_execution
    assert synthetic_case == before_sources


def test_reason_vocabulary_is_exact() -> None:
    assert len(design.INGESTION_REASON_VOCABULARY) == 25
    assert design.INGESTION_REASON_VOCABULARY[0] == "PASSED"
    assert design.INGESTION_REASON_VOCABULARY[-1] == (
        "INGESTION_RESPONSE_INVARIANT_INVALID"
    )
    assert design.INGESTION_FAILURE_REASON_PRECEDENCE == (
        "adapter_response_and_source_bytes",
        "batch_identity_count_and_duplicates",
        "authority_context",
        "existing_authority_set",
        "v1_predecessor_lineage",
        "envelope_record_digest_and_identity",
        "completion_provenance_and_decision",
        "committed_graph",
        "conflict",
        "batch_atomicity",
        "response_invariant",
    )


def test_legacy_coexistence_contract_is_frozen() -> None:
    assert design.LEGACY_V1_COEXISTENCE == (
        "legacy_v1_authority_namespace=exact_one_boundary_v1",
        "new_authority_namespace=exact_two_boundaries_multi_boundary_v1",
        "legacy_v1_authority_records_are_immutable=true",
        "new_multi_boundary_ingestion_does_not_edit_or_delete_v1=true",
        "parallel_authority_namespaces_allowed=true",
        "future_unified_gold_view_precedence_not_implemented=true",
    )


def test_mutated_v1_authority_context_sha_fails_lineage(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    expected_v1_context_sha256: str,
) -> None:
    case = _mutated_v1_execution_case(
        synthetic_case,
        lambda execution: execution.__setitem__(
            "authority_context_record_sha256", "0" * 64,
        ),
        refresh_interface_digest=True,
    )
    with pytest.raises(design._ContractFailure) as captured:
        design._decode_v1_execution(
            case[3],
            source_v1_submission_bundle=case[2],
            expected_authority_context_record_sha256=
                expected_v1_context_sha256,
        )
    assert captured.value.reason == "SOURCE_V1_LINEAGE_MISMATCH"
    _assert_atomic_failure(
        _evaluate(case), "SOURCE_V1_LINEAGE_MISMATCH",
    )


def test_mutated_v1_interface_response_sha_fails_lineage(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    expected_v1_context_sha256: str,
) -> None:
    case = _mutated_v1_execution_case(
        synthetic_case,
        lambda execution: execution.__setitem__(
            "ingestion_interface_response_sha256", "0" * 64,
        ),
        refresh_interface_digest=False,
    )
    with pytest.raises(design._ContractFailure) as captured:
        design._decode_v1_execution(
            case[3],
            source_v1_submission_bundle=case[2],
            expected_authority_context_record_sha256=
                expected_v1_context_sha256,
        )
    assert captured.value.reason == "SOURCE_V1_LINEAGE_MISMATCH"
    _assert_atomic_failure(
        _evaluate(case), "SOURCE_V1_LINEAGE_MISMATCH",
    )


def test_v1_nested_result_batch_id_mismatch_fails_lineage(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    expected_v1_context_sha256: str,
) -> None:
    def mutation(execution):
        result = execution["ingestion_result_records"][0]
        result["submission_batch_id"] = "different_nested_batch"
        result["ingestion_result_sha256"] = _canonical_sha(
            result, "ingestion_result_sha256",
        )

    case = _mutated_v1_execution_case(
        synthetic_case,
        mutation,
        refresh_interface_digest=True,
    )
    with pytest.raises(design._ContractFailure) as captured:
        design._decode_v1_execution(
            case[3],
            source_v1_submission_bundle=case[2],
            expected_authority_context_record_sha256=
                expected_v1_context_sha256,
        )
    assert captured.value.reason == "SOURCE_V1_LINEAGE_MISMATCH"
    _assert_atomic_failure(
        _evaluate(case), "SOURCE_V1_LINEAGE_MISMATCH",
    )


def test_existing_authority_invalid_source_sha_is_not_conflict(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    existing = copy.deepcopy(fresh_response["new_authority_records"][0])
    existing["source_evidence_record_sha256"] = "not-a-sha"
    existing["multi_boundary_authority_record_sha256"] = _canonical_sha(
        existing, "multi_boundary_authority_record_sha256",
    )
    _assert_atomic_failure(
        _evaluate(synthetic_case, (existing,)),
        "EXISTING_AUTHORITY_SET_INVALID",
    )


def test_existing_authority_invalid_atom_order_is_not_conflict(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    existing = copy.deepcopy(fresh_response["new_authority_records"][0])
    existing["reviewed_warhead_atom_ids"].reverse()
    existing["multi_boundary_authority_record_sha256"] = _canonical_sha(
        existing, "multi_boundary_authority_record_sha256",
    )
    _assert_atomic_failure(
        _evaluate(synthetic_case, (existing,)),
        "EXISTING_AUTHORITY_SET_INVALID",
    )


def test_existing_authority_invalid_canonical_boundary_is_not_conflict(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    existing = copy.deepcopy(fresh_response["new_authority_records"][0])
    existing["reviewed_boundary_records"][0][
        "boundary_bond_id"
    ] = "forged|boundary|single"
    existing["multi_boundary_authority_record_sha256"] = _canonical_sha(
        existing, "multi_boundary_authority_record_sha256",
    )
    _assert_atomic_failure(
        _evaluate(synthetic_case, (existing,)),
        "EXISTING_AUTHORITY_SET_INVALID",
    )


def test_existing_authority_nonmeaningful_provenance_is_not_conflict(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    existing = copy.deepcopy(fresh_response["new_authority_records"][0])
    existing["reviewer_provenance_attestor_id"] = " attestor "
    existing["multi_boundary_authority_record_sha256"] = _canonical_sha(
        existing, "multi_boundary_authority_record_sha256",
    )
    _assert_atomic_failure(
        _evaluate(synthetic_case, (existing,)),
        "EXISTING_AUTHORITY_SET_INVALID",
    )


def test_v1_canonical_submission_digest_mismatch_fails_lineage(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    expected_v1_context_sha256: str,
) -> None:
    case = _mutated_v1_execution_case(
        synthetic_case,
        lambda execution: execution.__setitem__(
            "source_canonical_bundle_sha256", "0" * 64,
        ),
        refresh_interface_digest=False,
    )
    with pytest.raises(design._ContractFailure) as captured:
        design._decode_v1_execution(
            case[3],
            source_v1_submission_bundle=case[2],
            expected_authority_context_record_sha256=
                expected_v1_context_sha256,
        )
    assert captured.value.reason == "SOURCE_V1_LINEAGE_MISMATCH"
    _assert_atomic_failure(
        _evaluate(case), "SOURCE_V1_LINEAGE_MISMATCH",
    )


def test_existing_authority_attachment_outside_reviewed_set_is_invalid(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    existing = copy.deepcopy(fresh_response["new_authority_records"][0])
    boundary = existing["reviewed_boundary_records"][0]
    boundary["warhead_attachment_atom_id"] = "ZZ_OUTSIDE_REVIEWED_SET"
    low, high = sorted(
        (
            boundary["warhead_attachment_atom_id"],
            boundary["nonwarhead_boundary_atom_id"],
        ),
        key=lambda value: value.encode("utf-8"),
    )
    boundary["boundary_bond_id"] = (
        f"{low}|{high}|{boundary['boundary_bond_order']}"
    )
    existing["reviewed_boundary_records"].sort(
        key=lambda row: row["boundary_bond_id"].encode("utf-8")
    )
    existing["multi_boundary_authority_record_sha256"] = _canonical_sha(
        existing, "multi_boundary_authority_record_sha256",
    )
    _assert_atomic_failure(
        _evaluate(synthetic_case, (existing,)),
        "EXISTING_AUTHORITY_SET_INVALID",
    )


def test_existing_authority_nonwarhead_inside_reviewed_set_is_invalid(
    synthetic_case: tuple[bytes, bytes, bytes, bytes],
    fresh_response: dict[str, Any],
) -> None:
    existing = copy.deepcopy(fresh_response["new_authority_records"][0])
    boundary = existing["reviewed_boundary_records"][0]
    boundary["nonwarhead_boundary_atom_id"] = next(
        atom for atom in existing["reviewed_warhead_atom_ids"]
        if atom != boundary["warhead_attachment_atom_id"]
    )
    low, high = sorted(
        (
            boundary["warhead_attachment_atom_id"],
            boundary["nonwarhead_boundary_atom_id"],
        ),
        key=lambda value: value.encode("utf-8"),
    )
    boundary["boundary_bond_id"] = (
        f"{low}|{high}|{boundary['boundary_bond_order']}"
    )
    existing["reviewed_boundary_records"].sort(
        key=lambda row: row["boundary_bond_id"].encode("utf-8")
    )
    existing["multi_boundary_authority_record_sha256"] = _canonical_sha(
        existing, "multi_boundary_authority_record_sha256",
    )
    _assert_atomic_failure(
        _evaluate(synthetic_case, (existing,)),
        "EXISTING_AUTHORITY_SET_INVALID",
    )
