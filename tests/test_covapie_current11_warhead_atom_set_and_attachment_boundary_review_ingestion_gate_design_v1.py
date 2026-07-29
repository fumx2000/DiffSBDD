from __future__ import annotations

import csv
import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import rdkit

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as gate,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


ROOT = Path(__file__).resolve().parents[1]
PYTEST_VERSION = "9.1.0"
RDKIT_VERSION = "2022.03.2"
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
}


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def payloads():
    return gate.load_frozen_sources(ROOT)


@pytest.fixture(scope="module")
def result():
    value = gate.build_result(ROOT)
    assert value.transaction_succeeded and not value.blocking_reasons
    return value


def _sample_options(result, sample: str):
    return [
        row for row in result.option_rows
        if row["sample_index_row_id"] == sample
    ]


def _human_record(result, decision: str, sample_offset: int = 0):
    template = dict(result.template_rows[sample_offset])
    sample = template["sample_index_row_id"]
    options = _sample_options(result, sample)
    if decision in {"select_admitted_candidate", "revise_atom_set_and_boundary"}:
        option = next(row for row in options if row["review_eligible"])
        template.update({
            "reviewed_warhead_atom_ids": list(option["warhead_side_atom_ids"]),
            "reviewed_warhead_attachment_atom_id":
                option["warhead_attachment_atom_id"],
            "reviewed_nonwarhead_boundary_atom_id":
                option["nonwarhead_boundary_atom_id"],
            "reviewed_attachment_boundary_bond_order":
                option["boundary_bond_order"],
            "reviewed_boundary_bond_id": option["boundary_bond_id"],
        })
        if decision == "select_admitted_candidate":
            template.update({
                "selected_bridge_candidate_index_0based":
                    option["source_bridge_candidate_index_0based"],
                "selected_bridge_candidate_record_sha256":
                    option["source_bridge_candidate_record_sha256"],
            })
    template.update({
        "review_decision": decision,
        "reviewer_id": f"human-reviewer-{sample_offset + 1:02d}",
        "review_rationale": "The named human reviewer inspected the package evidence.",
        "review_notes": "",
    })
    template["review_record_sha256"] = gate.review_record_sha256(template)
    return template


def _envelope(record, batch: str = "human-batch-0001"):
    envelope = {
        "ingestion_envelope_version": gate.INGESTION_ENVELOPE_VERSION,
        "submission_batch_id": batch,
        "sample_index_row_id": record["sample_index_row_id"],
        "review_record_sha256": record["review_record_sha256"],
        "submitted_record_payload_sha256":
            gate.submitted_record_payload_sha256(record),
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "human-attestor-01",
        "submission_source_label": "controlled-human-review-transfer",
        "ingestion_envelope_sha256": "",
    }
    envelope["ingestion_envelope_sha256"] = (
        gate.ingestion_envelope_sha256(envelope)
    )
    return envelope


def _unchecked_rehash_review(record):
    record["review_record_sha256"] = gate.sha256(gate.canonical_json({
        field: record[field] for field in gate.REVIEW_RECORD_FIELDS
        if field != "review_record_sha256"
    }).encode("utf-8"))
    return record


def _unchecked_envelope(record, batch: str):
    envelope = {
        "ingestion_envelope_version": gate.INGESTION_ENVELOPE_VERSION,
        "submission_batch_id": batch,
        "sample_index_row_id": record["sample_index_row_id"],
        "review_record_sha256": record["review_record_sha256"],
        "submitted_record_payload_sha256": gate.sha256(
            gate.canonical_json({
                field: record[field] for field in gate.REVIEW_RECORD_FIELDS
            }).encode("utf-8")
        ),
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "human-attestor-identity-test",
        "submission_source_label": "identity-hardening-test",
        "ingestion_envelope_sha256": "",
    }
    envelope["ingestion_envelope_sha256"] = gate.ingestion_envelope_sha256(
        envelope
    )
    return envelope


def _context(result):
    proposals = {
        row["sample_index_row_id"]: row for row in result.proposal_rows
    }
    atom_ids = {}
    for row in result.parent_atom_rows:
        atom_ids.setdefault(row["ligand_comp_id"], []).append(row["ccd_atom_id"])
    bonds = {}
    for row in result.parent_bond_rows:
        bonds.setdefault(row["ligand_comp_id"], []).append(row)
    return proposals, atom_ids, bonds, result.package_identity_by_sample


def _ingest(result, submissions, existing=()):
    return gate.ingest_review_batch(
        submissions, authority_context=result.authority_context,
        existing_authorities=existing,
    )


def _authority_for(result, decision="quarantine", offset=0):
    review = _human_record(result, decision, offset)
    batch = _ingest(
        result, [(review, _envelope(review, f"authority-{offset}"))],
    )
    assert batch.passed and len(batch.new_authority_records) == 1
    return review, dict(batch.new_authority_records[0])


def test_formal_python_pytest_rdkit_environment():
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == (3, 10, 4)
    assert pytest.__version__ == PYTEST_VERSION
    assert rdkit.__version__ == RDKIT_VERSION


def test_base_identity_and_actual_lifecycle():
    identity = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%P%n%T%n%s", gate.BASE_COMMIT),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode().splitlines()
    assert identity == [
        gate.BASE_COMMIT, gate.BASE_PARENT, gate.BASE_TREE, gate.BASE_SUBJECT,
    ]
    assert gate.validate_execution_boundary_v1(ROOT) in lifecycle.LIFECYCLES


def test_exact13_git_show_sources_and_sha(payloads):
    assert len(payloads) == len(gate.FROZEN_BASE_SHA256) == 13
    for path, expected in gate.FROZEN_BASE_SHA256.items():
        assert hashlib.sha256(payloads[path]).hexdigest() == expected
        assert subprocess.run(
            ("git", "cat-file", "-e", f"{gate.BASE_COMMIT}:{path.as_posix()}"),
            cwd=ROOT, check=False,
        ).returncode == 0


def _rehash_context_record(record):
    record["ingestion_authority_context_record_sha256"] = gate.sha256(
        gate.canonical_json({
            field: record[field]
            for field in gate.INGESTION_AUTHORITY_CONTEXT_FIELDS
            if field != "ingestion_authority_context_record_sha256"
        }).encode("utf-8")
    )


def test_exact4_immutable_authority_context_from_base_and_deterministic(
    result, monkeypatch,
):
    context = result.authority_context
    assert type(context) is gate.IngestionAuthorityContext
    assert context.__dataclass_params__.frozen is True
    assert tuple(context.context_record) == (
        gate.INGESTION_AUTHORITY_CONTEXT_FIELDS
    )
    assert len(context.context_record) == 4
    assert context.context_record["formal_base_commit"] == gate.BASE_COMMIT
    assert len(context.source_payloads) == 13
    assert [path for path, _ in context.source_payloads] == [
        path.as_posix() for path in gate.SOURCE_PATHS
    ]
    gate.validate_ingestion_authority_context(context)
    observed = []
    original = gate.base_bytes

    def recording_base_bytes(repo_root, path):
        observed.append(path)
        return original(repo_root, path)

    monkeypatch.setattr(gate, "base_bytes", recording_base_bytes)
    first = gate.build_ingestion_authority_context(ROOT)
    second = gate.build_ingestion_authority_context(ROOT)
    assert observed == list(gate.SOURCE_PATHS) * 2
    assert first == second == context
    assert "read_bytes" not in inspect.getsource(
        gate.build_ingestion_authority_context
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "source_order", "source_deleted", "source_added", "payload_byte",
        "source_sha", "formal_base", "context_digest",
    ),
)
def test_authority_context_mutations_fail_closed(result, mutation):
    context = result.authority_context
    payloads = list(context.source_payloads)
    record = dict(context.context_record)
    record["ordered_source_path_sha256_pairs"] = list(
        record["ordered_source_path_sha256_pairs"]
    )
    if mutation == "source_order":
        payloads[0], payloads[1] = payloads[1], payloads[0]
        record["ordered_source_path_sha256_pairs"][0:2] = (
            record["ordered_source_path_sha256_pairs"][1::-1]
        )
        _rehash_context_record(record)
    elif mutation == "source_deleted":
        payloads.pop()
        record["ordered_source_path_sha256_pairs"].pop()
        _rehash_context_record(record)
    elif mutation == "source_added":
        payloads.append(payloads[0])
        record["ordered_source_path_sha256_pairs"].append(
            record["ordered_source_path_sha256_pairs"][0]
        )
        _rehash_context_record(record)
    elif mutation == "payload_byte":
        path, payload = payloads[2]
        payloads[2] = (path, payload[:-1] + bytes([payload[-1] ^ 1]))
        digest = gate.sha256(payloads[2][1])
        record["ordered_source_path_sha256_pairs"][2] = f"{path}\t{digest}"
        _rehash_context_record(record)
    elif mutation == "source_sha":
        path = payloads[3][0]
        record["ordered_source_path_sha256_pairs"][3] = f"{path}\t{'0' * 64}"
        _rehash_context_record(record)
    elif mutation == "formal_base":
        record["formal_base_commit"] = "0" * 40
        _rehash_context_record(record)
    else:
        record["ingestion_authority_context_record_sha256"] = "0" * 64
    forged = gate.IngestionAuthorityContext(record, tuple(payloads))
    review = _human_record(result, "quarantine")
    batch = gate.ingest_review_batch(
        [(review, _envelope(review, f"context-{mutation}"))],
        authority_context=forged,
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == (
        "INGESTION_AUTHORITY_CONTEXT_INVALID"
    )
    assert not batch.result_records[0]["consumed_review_record"]
    assert not batch.result_records[0]["consumed_ingestion_envelope"]


def test_external_authority_maps_removed_and_forged_context_blocked(result):
    parameters = inspect.signature(gate.ingest_review_batch).parameters
    assert tuple(parameters) == (
        "submissions", "authority_context", "existing_authorities",
    )
    for forbidden in (
        "package_identity_by_sample", "options", "proposals_by_sample",
        "parent_atom_ids_by_ligand", "parent_bonds_by_ligand",
        "valid_sample_ids",
    ):
        assert forbidden not in parameters
    review = _human_record(result, "quarantine")
    with pytest.raises(TypeError):
        gate.ingest_review_batch(
            [(review, _envelope(review))],
            authority_context=result.authority_context,
            package_identity_by_sample=result.package_identity_by_sample,
        )
    payloads = list(result.authority_context.source_payloads)
    target = next(
        index for index, (path, _) in enumerate(payloads)
        if path == gate.PACKAGE_INDEX.as_posix()
    )
    path, payload = payloads[target]
    forged_payload = payload.replace(
        b"CYS_SG_SAMPLE_INDEX_000001", b"FORGED_SAMPLE_INDEX_000001", 1,
    ).replace(b"6BV6", b"FORGED_PDB", 1).replace(
        b"JUG", b"FORGED_LIGAND", 1,
    )
    payloads[target] = (path, forged_payload)
    record = dict(result.authority_context.context_record)
    record["ordered_source_path_sha256_pairs"] = list(
        record["ordered_source_path_sha256_pairs"]
    )
    record["ordered_source_path_sha256_pairs"][target] = (
        f"{path}\t{gate.sha256(forged_payload)}"
    )
    _rehash_context_record(record)
    forged_context = gate.IngestionAuthorityContext(record, tuple(payloads))
    batch = gate.ingest_review_batch(
        [(review, _envelope(review, "forged-context"))],
        authority_context=forged_context,
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == (
        "INGESTION_AUTHORITY_CONTEXT_INVALID"
    )


def test_phase_a_package_counts_and_current_zero_state(result):
    assert len(result.option_rows) == 200
    assert sum(row["review_eligible"] for row in result.option_rows) == 185
    assert sum(not row["review_eligible"] for row in result.option_rows) == 15
    assert len(result.template_rows) == 11
    assert all(row["review_decision"] == "not_reviewed" for row in result.template_rows)
    assert all(not row["review_record_sha256"] for row in result.template_rows)


def test_source_inventory_exact13_current_value_flag(result):
    assert tuple(result.source_rows[0]) == gate.SOURCE_COLUMNS
    assert len(result.source_rows) == 13
    assert all(row["verified"] is True for row in result.source_rows)
    assert any(row["provides_current_value"] is False for row in result.source_rows)


def test_inherited_exact26_and_blank_payload_digest(result):
    assert len(gate.REVIEW_RECORD_FIELDS) == 26
    for row in result.template_rows:
        assert tuple(row) == gate.REVIEW_RECORD_FIELDS
        gate.validate_review_record(row)
        assert row["review_record_sha256"] == ""
        assert gate.review_record_sha256(row)


def test_review_csv_typed_optional_index(payloads):
    row = _rows(payloads[gate.PACKAGE_TEMPLATES])[0]
    parsed = gate.parse_review_record_csv(row)
    assert parsed["selected_bridge_candidate_index_0based"] is None
    bad = dict(row)
    bad["selected_bridge_candidate_index_0based"] = "01"
    with pytest.raises(ValueError, match="canonical_nonnegative"):
        gate.parse_review_record_csv(bad)


def test_exact14_package_identity_rebuilt_from_index_and_templates(result):
    assert gate.COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS == (
        "review_record_version", "review_unit_type", "sample_index_row_id",
        "pdb_id", "ligand_comp_id",
        "warhead_type_candidate_class_index_0based",
        "warhead_type_candidate_class_id", "reaction_family_id",
        "warhead_rule_id", "source_proposal_record_sha256",
        "source_assignment_record_sha256", "source_candidate_set_sha256",
        "total_candidate_count", "admitted_candidate_count",
    )
    rebuilt = gate.build_package_identity_by_sample(
        result.package_index_rows, result.template_rows,
    )
    assert rebuilt == result.package_identity_by_sample
    assert len(rebuilt) == 11
    review = _human_record(result, "quarantine")
    gate.validate_completed_review_package_identity(
        review, package_identity_by_sample=rebuilt,
    )
    bad = dict(review)
    bad["warhead_type_candidate_class_index_0based"] = True
    with pytest.raises(ValueError, match="REVIEW_IDENTITY_LINKAGE_MISMATCH"):
        gate.validate_completed_review_package_identity(
            bad, package_identity_by_sample=rebuilt,
        )


@pytest.mark.parametrize(
    "field",
    (
        "pdb_id", "ligand_comp_id",
        "warhead_type_candidate_class_index_0based",
        "warhead_type_candidate_class_id", "reaction_family_id",
        "warhead_rule_id", "source_proposal_record_sha256",
        "source_assignment_record_sha256", "source_candidate_set_sha256",
        "total_candidate_count", "admitted_candidate_count",
        "review_record_version", "review_unit_type",
    ),
)
def test_completed_quarantine_exact14_field_forgery_is_blocked(result, field):
    review = _human_record(result, "quarantine")
    if field in {
        "warhead_type_candidate_class_index_0based",
        "total_candidate_count", "admitted_candidate_count",
    }:
        review[field] += 1
    elif field.startswith("source_"):
        review[field] = "f" * 64
    else:
        review[field] = "FORGED_" + field.upper()
    _unchecked_rehash_review(review)
    batch = _ingest(
        result,
        [(review, _unchecked_envelope(review, "identity-forgery-batch"))],
    )
    assert batch.passed is False
    assert batch.new_authority_records == ()
    assert [row["reason"] for row in batch.result_records] == [
        "REVIEW_IDENTITY_LINKAGE_MISMATCH"
    ]


def test_manual_forged_quarantine_reproduction_is_now_blocked(result):
    review = _human_record(result, "quarantine")
    review.update({
        "pdb_id": "FORGED_PDB",
        "ligand_comp_id": "FORGED_LIGAND",
        "warhead_type_candidate_class_id": "FORGED_CLASS",
        "reaction_family_id": "FORGED_FAMILY",
        "warhead_rule_id": "FORGED_RULE",
        "source_proposal_record_sha256": "1" * 64,
        "source_assignment_record_sha256": "2" * 64,
        "source_candidate_set_sha256": "3" * 64,
    })
    _unchecked_rehash_review(review)
    batch = _ingest(
        result, [(review, _unchecked_envelope(review, "forged-quarantine"))],
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == (
        "REVIEW_IDENTITY_LINKAGE_MISMATCH"
    )


@pytest.mark.parametrize(
    "field",
    (
        "pdb_id", "reaction_family_id", "warhead_rule_id",
        "source_proposal_record_sha256", "source_assignment_record_sha256",
    ),
)
def test_select_candidate_identity_cannot_bypass_package_join(result, field):
    review = _human_record(result, "select_admitted_candidate")
    review[field] = "e" * 64 if field.startswith("source_") else "FORGED_" + field
    _unchecked_rehash_review(review)
    batch = _ingest(
        result, [(review, _unchecked_envelope(review, "select-forgery"))],
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == (
        "REVIEW_IDENTITY_LINKAGE_MISMATCH"
    )


def test_revise_uses_authoritative_package_ligand_and_proposal_lineage(result):
    review = _human_record(result, "revise_atom_set_and_boundary")
    review["ligand_comp_id"] = "FORGED_LIGAND"
    review["source_proposal_record_sha256"] = "d" * 64
    _unchecked_rehash_review(review)
    batch = _ingest(
        result, [(review, _unchecked_envelope(review, "revise-forgery"))],
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == (
        "REVIEW_IDENTITY_LINKAGE_MISMATCH"
    )


def test_exact9_envelope_schema_type_hash_and_full_payload(result):
    review = _human_record(result, "select_admitted_candidate")
    envelope = _envelope(review)
    assert len(gate.INGESTION_ENVELOPE_FIELDS) == 9
    gate.validate_ingestion_envelope(
        envelope, review_record=review,
        valid_sample_ids={review["sample_index_row_id"]},
    )
    digest = gate.submitted_record_payload_sha256(review)
    changed = dict(review)
    changed["review_record_sha256"] = "0" * 64
    assert gate.submitted_record_payload_sha256(changed) != digest
    bad = dict(envelope)
    bad["reviewer_provenance_attested"] = 1
    with pytest.raises(ValueError, match="EXACT_TYPE_INVALID"):
        gate.validate_ingestion_envelope(bad)


@pytest.mark.parametrize("attestor", ["codex", " ChatGPT ", "OPENAI", "system"])
def test_provenance_attestation_and_forbidden_attestor(result, attestor):
    review = _human_record(result, "quarantine")
    envelope = _envelope(review)
    envelope["reviewer_provenance_attestor_id"] = attestor
    envelope["ingestion_envelope_sha256"] = gate.ingestion_envelope_sha256(envelope)
    with pytest.raises(ValueError, match="PROVENANCE_ATTESTOR_INVALID"):
        gate.validate_ingestion_envelope(envelope, review_record=review)
    envelope["reviewer_provenance_attestor_id"] = "human-attestor"
    envelope["reviewer_provenance_attested"] = False
    envelope["ingestion_envelope_sha256"] = gate.ingestion_envelope_sha256(envelope)
    with pytest.raises(ValueError, match="ATTESTATION_REQUIRED"):
        gate.validate_ingestion_envelope(envelope, review_record=review)


def test_valid_select_exact27_authority_and_exact18_result(result):
    review = _human_record(result, "select_admitted_candidate")
    envelope = _envelope(review)
    batch = _ingest(result, [(review, envelope)])
    assert batch.passed and len(batch.new_authority_records) == 1
    authority = batch.new_authority_records[0]
    assert tuple(authority) == gate.AUTHORITY_RECORD_FIELDS
    assert len(gate.AUTHORITY_RECORD_FIELDS) == 27
    gate.validate_authority_record(authority)
    assert authority["complete_warhead_atom_set_authority_available"] is True
    assert authority["exact_one_attachment_boundary_authority_available"] is True
    assert authority["sample_quarantined"] is False
    result_record = batch.result_records[0]
    assert len(gate.INGESTION_RESULT_FIELDS) == 18
    gate.validate_ingestion_result(result_record)
    assert result_record["outcome"] == "passed"


def test_valid_revise_parent_graph_invariants_and_authority(result):
    review = _human_record(result, "revise_atom_set_and_boundary")
    envelope = _envelope(review, "human-batch-revise")
    batch = _ingest(result, [(review, envelope)])
    assert batch.passed and len(batch.new_authority_records) == 1
    assert batch.new_authority_records[0]["authority_status"] == "active"
    bad = dict(review)
    bad["reviewed_warhead_atom_ids"] = []
    bad["review_record_sha256"] = gate.review_record_sha256(bad)
    with pytest.raises(ValueError, match="REVISE_GRAPH_INVARIANT_INVALID"):
        proposals, atoms, bonds, _ = _context(result)
        gate.validate_review_record(
            bad, proposal=proposals[bad["sample_index_row_id"]],
            parent_atom_ids=atoms[bad["ligand_comp_id"]],
            parent_bonds=bonds[bad["ligand_comp_id"]],
            completed_submission=True,
        )


def test_valid_quarantine_disposition_has_no_boundary_authority(result):
    review = _human_record(result, "quarantine")
    envelope = _envelope(review, "human-batch-quarantine")
    batch = _ingest(result, [(review, envelope)])
    authority = batch.new_authority_records[0]
    assert authority["authority_disposition"] == "reviewed_quarantine_no_authority"
    assert authority["authority_status"] == "quarantined"
    assert authority["complete_warhead_atom_set_authority_available"] is False
    assert authority["exact_one_attachment_boundary_authority_available"] is False
    assert authority["sample_quarantined"] is True


def test_select_ineligible_option_is_rejected(result):
    option = next(row for row in result.option_rows if not row["review_eligible"])
    sample_offset = next(
        index for index, row in enumerate(result.template_rows)
        if row["sample_index_row_id"] == option["sample_index_row_id"]
    )
    review = _human_record(result, "quarantine", sample_offset)
    review.update({
        "review_decision": "select_admitted_candidate",
        "selected_bridge_candidate_index_0based":
            option["source_bridge_candidate_index_0based"],
        "selected_bridge_candidate_record_sha256":
            option["source_bridge_candidate_record_sha256"],
        "reviewed_warhead_atom_ids": list(option["warhead_side_atom_ids"]),
        "reviewed_warhead_attachment_atom_id":
            option["warhead_attachment_atom_id"],
        "reviewed_nonwarhead_boundary_atom_id":
            option["nonwarhead_boundary_atom_id"],
        "reviewed_attachment_boundary_bond_order": option["boundary_bond_order"],
        "reviewed_boundary_bond_id": option["boundary_bond_id"],
    })
    review["review_record_sha256"] = gate.review_record_sha256(review)
    with pytest.raises(ValueError, match="NOT_REVIEW_ELIGIBLE"):
        gate.validate_review_record(
            review, options=result.option_rows, completed_submission=True,
        )


def test_not_reviewed_submission_blocks_and_creates_no_authority(result):
    review = dict(result.template_rows[0])
    envelope = {
        "ingestion_envelope_version": gate.INGESTION_ENVELOPE_VERSION,
        "submission_batch_id": "human-batch-blank",
        "sample_index_row_id": review["sample_index_row_id"],
        "review_record_sha256": "0" * 64,
        "submitted_record_payload_sha256": "0" * 64,
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "human-attestor",
        "submission_source_label": "test-only",
        "ingestion_envelope_sha256": "0" * 64,
    }
    batch = _ingest(result, [(review, envelope)])
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == "REVIEW_NOT_COMPLETED"
    assert batch.result_records[0]["blocks_batch"] is True


def test_partial_two_record_batch_atomicity(result):
    first = _human_record(result, "select_admitted_candidate", 0)
    second = _human_record(result, "quarantine", 1)
    passed = _ingest(
        result,
        [(first, _envelope(first, "partial-two")),
         (second, _envelope(second, "partial-two"))],
    )
    assert passed.passed and len(passed.new_authority_records) == 2
    blank = dict(result.template_rows[1])
    invalid = _ingest(
        result,
        [(first, _envelope(first, "atomic-fail")),
         (blank, {
             "ingestion_envelope_version": gate.INGESTION_ENVELOPE_VERSION,
             "submission_batch_id": "atomic-fail",
             "sample_index_row_id": blank["sample_index_row_id"],
             "review_record_sha256": "0" * 64,
             "submitted_record_payload_sha256": "0" * 64,
             "reviewer_provenance_attested": True,
             "reviewer_provenance_attestor_id": "human-attestor",
             "submission_source_label": "test-only",
             "ingestion_envelope_sha256": "0" * 64,
         })],
    )
    assert not invalid.passed and invalid.new_authority_records == ()
    assert {row["reason"] for row in invalid.result_records} == {
        "BATCH_ATOMICITY_ABORTED", "REVIEW_NOT_COMPLETED",
    }


def test_single_submission_batch_id_required_and_mixed_ids_fail_all(result):
    first = _human_record(result, "select_admitted_candidate", 0)
    second = _human_record(result, "quarantine", 1)
    mixed = _ingest(
        result,
        [(first, _envelope(first, "batch-A")),
         (second, _envelope(second, "batch-B"))],
    )
    assert mixed.passed is False and mixed.new_authority_records == ()
    assert [row["sample_index_row_id"] for row in mixed.result_records] == [
        first["sample_index_row_id"], second["sample_index_row_id"],
    ]
    assert all(
        row["outcome"] == "invalid"
        and row["reason"] == "SUBMISSION_BATCH_ID_MISMATCH"
        and not row["consumed_review_record"]
        and not row["consumed_ingestion_envelope"]
        for row in mixed.result_records
    )
    same = _ingest(
        result,
        [(first, _envelope(first, "batch-same")),
         (second, _envelope(second, "batch-same"))],
    )
    assert same.passed and len(same.new_authority_records) == 2
    padded = _ingest(
        result,
        [(first, _envelope(first, "batch-same")),
         (second, _envelope(second, " batch-same "))],
    )
    assert not padded.passed and all(
        row["reason"] == "SUBMISSION_BATCH_ID_MISMATCH"
        for row in padded.result_records
    )


def test_duplicate_constraints_idempotent_replay_and_conflict(result):
    review = _human_record(result, "select_admitted_candidate")
    envelope = _envelope(review, "initial")
    initial = _ingest(result, [(review, envelope)])
    authority = initial.new_authority_records[0]
    replay = _ingest(
        result, [(review, _envelope(review, "replay"))], existing=(authority,),
    )
    assert replay.passed and replay.new_authority_records == ()
    assert replay.result_records[0]["idempotent_replay"] is True
    conflicting = _human_record(result, "quarantine")
    conflict = _ingest(
        result, [(conflicting, _envelope(conflicting, "conflict"))],
        existing=(authority,),
    )
    assert not conflict.passed and conflict.new_authority_records == ()
    assert conflict.result_records[0]["reason"] == "CONFLICTING_REVIEW_REINGESTION"
    duplicate = _ingest(result, [(review, envelope), (review, envelope)])
    assert not duplicate.passed and duplicate.new_authority_records == ()


def test_existing_authority_duplicate_sample_and_sha_fail_closed(result):
    review, authority = _authority_for(result)
    second = dict(authority)
    second["source_ingestion_envelope_sha256"] = "9" * 64
    second["authority_record_sha256"] = gate.authority_record_sha256(second)
    duplicate_sample = _ingest(
        result, [(review, _envelope(review, "existing-duplicate-sample"))],
        existing=(authority, second),
    )
    assert not duplicate_sample.passed
    assert duplicate_sample.new_authority_records == ()
    assert {
        row["reason"] for row in duplicate_sample.result_records
    } == {"EXISTING_AUTHORITY_SET_INVALID"}
    duplicate_sha = _ingest(
        result, [(review, _envelope(review, "existing-duplicate-sha"))],
        existing=(authority, dict(authority)),
    )
    assert not duplicate_sha.passed
    assert duplicate_sha.result_records[0]["reason"] == (
        "EXISTING_AUTHORITY_SET_INVALID"
    )


@pytest.mark.parametrize("mutation", ("invalid_hash", "nonempty_supersedes"))
def test_existing_authority_schema_hash_and_supersession_are_validated(
    result, mutation,
):
    review, authority = _authority_for(result)
    if mutation == "invalid_hash":
        authority["authority_record_sha256"] = "0" * 64
    else:
        authority["supersedes_authority_record_sha256"] = "1" * 64
        authority["authority_record_sha256"] = gate.authority_record_sha256(
            authority
        )
    batch = _ingest(
        result, [(review, _envelope(review, f"existing-{mutation}"))],
        existing=(authority,),
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == "EXISTING_AUTHORITY_SET_INVALID"


@pytest.mark.parametrize("mutation", ("forged_lineage", "unknown_sample"))
def test_existing_authority_package_lineage_is_validated(result, mutation):
    review, authority = _authority_for(result)
    if mutation == "forged_lineage":
        authority["pdb_id"] = "FORGED_PDB"
    else:
        authority["sample_index_row_id"] = "UNKNOWN_SAMPLE"
    authority["authority_record_sha256"] = gate.authority_record_sha256(
        authority
    )
    batch = _ingest(
        result, [(review, _envelope(review, f"existing-{mutation}"))],
        existing=(authority,),
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == (
        "EXISTING_AUTHORITY_LINEAGE_MISMATCH"
    )


@pytest.mark.parametrize(
    "decision",
    ("select_admitted_candidate", "revise_atom_set_and_boundary", "quarantine"),
)
def test_existing_authority_valid_decision_evidence(result, decision):
    review, authority = _authority_for(result, decision)
    batch = _ingest(
        result, [(review, _envelope(review, f"valid-existing-{decision}"))],
        existing=(authority,),
    )
    assert batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == "IDEMPOTENT_REPLAY"


@pytest.mark.parametrize(
    "decision,mutation",
    (
        ("select_admitted_candidate", "unknown_boundary"),
        ("select_admitted_candidate", "ineligible_mismatch"),
        ("revise_atom_set_and_boundary", "disconnected"),
        ("revise_atom_set_and_boundary", "missing_local_center"),
        ("revise_atom_set_and_boundary", "non_exact_one_boundary"),
        ("quarantine", "empty_reviewer"),
        ("quarantine", "automated_reviewer"),
    ),
)
def test_existing_authority_decision_evidence_fail_closed(
    result, decision, mutation,
):
    offset = 0
    if mutation == "ineligible_mismatch":
        ineligible_sample = next(
            row["sample_index_row_id"] for row in result.option_rows
            if not row["review_eligible"]
        )
        offset = next(
            index for index, row in enumerate(result.template_rows)
            if row["sample_index_row_id"] == ineligible_sample
        )
    review, authority = _authority_for(result, decision, offset)
    if mutation == "unknown_boundary":
        authority["reviewed_warhead_atom_ids"] = ["FORGED_ATOM"]
        authority["reviewed_warhead_attachment_atom_id"] = "FORGED_ATOM"
        authority["reviewed_nonwarhead_boundary_atom_id"] = "FORGED_NEIGHBOR"
        authority["reviewed_boundary_bond_id"] = (
            "FORGED_ATOM|FORGED_NEIGHBOR|single"
        )
    elif mutation == "ineligible_mismatch":
        option = next(
            row for row in result.option_rows
            if row["sample_index_row_id"] == authority["sample_index_row_id"]
            and not row["review_eligible"]
        )
        authority["reviewed_warhead_atom_ids"] = list(
            option["warhead_side_atom_ids"]
        )
        authority["reviewed_warhead_attachment_atom_id"] = (
            option["warhead_attachment_atom_id"]
        )
        authority["reviewed_nonwarhead_boundary_atom_id"] = (
            option["nonwarhead_boundary_atom_id"]
        )
        authority["reviewed_attachment_boundary_bond_order"] = (
            option["boundary_bond_order"]
        )
        authority["reviewed_boundary_bond_id"] = option["boundary_bond_id"]
    elif mutation in {
        "disconnected", "missing_local_center", "non_exact_one_boundary",
    }:
        proposal = next(
            row for row in result.proposal_rows
            if row["sample_index_row_id"] == authority["sample_index_row_id"]
        )
        local = list(proposal["local_reaction_center_atom_ids"])
        if mutation == "missing_local_center":
            authority["reviewed_warhead_atom_ids"] = local[1:]
        elif mutation == "non_exact_one_boundary":
            authority["reviewed_warhead_atom_ids"] = local
        else:
            _, atom_ids, bonds, _ = _context(result)
            ligand = authority["ligand_comp_id"]
            adjacency = {atom: set() for atom in atom_ids[ligand]}
            for bond in bonds[ligand]:
                left = bond["parent_ccd_atom_id_1"]
                right = bond["parent_ccd_atom_id_2"]
                adjacency[left].add(right)
                adjacency[right].add(left)
            detached = next(
                atom for atom in atom_ids[ligand]
                if atom not in set(local)
                and not adjacency[atom] & set(local)
            )
            authority["reviewed_warhead_atom_ids"] = sorted(
                [*local, detached], key=lambda value: value.encode("utf-8"),
            )
    elif mutation == "empty_reviewer":
        authority["reviewer_id"] = ""
    else:
        authority["reviewer_id"] = "codex"
    authority["authority_record_sha256"] = gate.authority_record_sha256(
        authority
    )
    batch = _ingest(
        result,
        [(review, _envelope(review, f"invalid-existing-{mutation}"))],
        existing=(authority,),
    )
    assert not batch.passed and batch.new_authority_records == ()
    assert batch.result_records[0]["reason"] == "EXISTING_AUTHORITY_SET_INVALID"


def test_exact_replay_requires_semantic_equivalence(result):
    review, authority = _authority_for(
        result, "select_admitted_candidate",
    )
    valid = _ingest(
        result, [(review, _envelope(review, "semantic-replay-valid"))],
        existing=(authority,),
    )
    assert valid.passed and valid.new_authority_records == ()
    assert valid.result_records[0]["idempotent_replay"] is True
    forged = dict(authority)
    forged["reviewer_id"] = "different-human-reviewer"
    forged["authority_record_sha256"] = gate.authority_record_sha256(forged)
    invalid = _ingest(
        result, [(review, _envelope(review, "semantic-replay-invalid"))],
        existing=(forged,),
    )
    assert not invalid.passed and invalid.new_authority_records == ()
    assert invalid.result_records[0]["reason"] == (
        "EXISTING_AUTHORITY_LINEAGE_MISMATCH"
    )
    conflicting = _human_record(result, "quarantine")
    conflict = _ingest(
        result,
        [(conflicting, _envelope(conflicting, "different-review-conflict"))],
        existing=(authority,),
    )
    assert not conflict.passed
    assert conflict.result_records[0]["reason"] == (
        "CONFLICTING_REVIEW_REINGESTION"
    )


def test_existing_authority_order_does_not_change_results(result):
    _, first = _authority_for(result, "quarantine", 0)
    _, second = _authority_for(result, "quarantine", 1)
    review = _human_record(result, "quarantine", 2)
    submission = [(review, _envelope(review, "existing-order"))]
    forward = _ingest(result, submission, existing=(first, second))
    reverse = _ingest(result, submission, existing=(second, first))
    assert forward == reverse


def test_v1_supersession_is_rejected(result):
    review = _human_record(result, "quarantine")
    authority = gate.materialize_authority_record(
        review, _envelope(review),
        package_identity=result.package_identity_by_sample[
            review["sample_index_row_id"]
        ],
    )
    authority["supersedes_authority_record_sha256"] = "0" * 64
    authority["authority_record_sha256"] = gate.authority_record_sha256(authority)
    with pytest.raises(ValueError, match="SUPERSESSION_UNAVAILABLE"):
        gate.validate_authority_record(authority)


def test_public_reason_vocabulary_and_no_internal_exception_leak(result):
    assert len(gate.INGESTION_RESULT_REASON_CODES) == 31
    assert len(set(gate.INGESTION_RESULT_REASON_CODES)) == 31
    review = _human_record(result, "quarantine")
    envelope = _envelope(review, "exact-type-public-reason")
    envelope["reviewer_provenance_attested"] = 1
    batch = _ingest(result, [(review, envelope)])
    assert not batch.passed
    reason = batch.result_records[0]["reason"]
    assert reason == "INGESTION_ENVELOPE_EXACT_TYPE_INVALID"
    assert reason in gate.INGESTION_RESULT_REASON_CODES
    assert ":" not in reason and "exact_bool_invalid" not in reason
    assert all(
        row["reason"] in gate.INGESTION_RESULT_REASON_CODES
        for row in batch.result_records
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "passed_review_not_completed", "passed_conflict", "blocked_passed",
        "invalid_atomic", "replay_flag_false", "passed_flag_true",
        "conflict_flag_false", "nonconflict_flag_true",
        "quarantine_active_disposition", "select_quarantine_disposition",
    ),
)
def test_ingestion_result_reason_effect_forbidden_combinations(result, mutation):
    select = _human_record(result, "select_admitted_candidate")
    select_passed = _ingest(
        result, [(select, _envelope(select, "result-select"))],
    )
    select_authority = select_passed.new_authority_records[0]
    replay = _ingest(
        result, [(select, _envelope(select, "result-replay"))],
        existing=(select_authority,),
    )
    quarantine = _human_record(result, "quarantine", 1)
    quarantine_passed = _ingest(
        result, [(quarantine, _envelope(quarantine, "result-quarantine"))],
    )
    blank = dict(result.template_rows[2])
    blocked = _ingest(
        result, [(blank, {
            "ingestion_envelope_version": gate.INGESTION_ENVELOPE_VERSION,
            "submission_batch_id": "result-blocked",
            "sample_index_row_id": blank["sample_index_row_id"],
            "review_record_sha256": "0" * 64,
            "submitted_record_payload_sha256": "0" * 64,
            "reviewer_provenance_attested": True,
            "reviewer_provenance_attestor_id": "human-attestor",
            "submission_source_label": "test",
            "ingestion_envelope_sha256": "0" * 64,
        })],
    )
    invalid = gate.ingest_review_batch(
        [(select, _envelope(select, "result-invalid"))],
        authority_context=None,
    )
    conflicting_review = _human_record(result, "quarantine")
    conflict = _ingest(
        result,
        [(conflicting_review, _envelope(conflicting_review, "result-conflict"))],
        existing=(select_authority,),
    )
    valid_rows = (
        select_passed.result_records[0], replay.result_records[0],
        quarantine_passed.result_records[0], blocked.result_records[0],
        invalid.result_records[0], conflict.result_records[0],
    )
    for valid in valid_rows:
        gate.validate_ingestion_result(valid)
    source, changes = {
        "passed_review_not_completed": (
            select_passed.result_records[0],
            {"reason": "REVIEW_NOT_COMPLETED"},
        ),
        "passed_conflict": (
            select_passed.result_records[0],
            {"reason": "CONFLICTING_REVIEW_REINGESTION"},
        ),
        "blocked_passed": (
            blocked.result_records[0], {"reason": "PASSED"},
        ),
        "invalid_atomic": (
            invalid.result_records[0], {"reason": "BATCH_ATOMICITY_ABORTED"},
        ),
        "replay_flag_false": (
            replay.result_records[0], {"idempotent_replay": False},
        ),
        "passed_flag_true": (
            select_passed.result_records[0], {"idempotent_replay": True},
        ),
        "conflict_flag_false": (
            conflict.result_records[0],
            {"conflicting_existing_authority": False},
        ),
        "nonconflict_flag_true": (
            invalid.result_records[0],
            {"conflicting_existing_authority": True},
        ),
        "quarantine_active_disposition": (
            quarantine_passed.result_records[0],
            {"authority_disposition": "reviewed_authority_materialized"},
        ),
        "select_quarantine_disposition": (
            select_passed.result_records[0],
            {"authority_disposition": "reviewed_quarantine_no_authority"},
        ),
    }[mutation]
    malicious = dict(source)
    malicious.update(changes)
    malicious["ingestion_result_sha256"] = gate.ingestion_result_sha256(
        malicious
    )
    with pytest.raises(ValueError, match="REASON_EFFECT_INVALID"):
        gate.validate_ingestion_result(malicious)


def test_deterministic_reason_precedence_and_input_order(result):
    assert gate.INGESTION_FAILURE_REASON_PRECEDENCE == (
        "BATCH_SIZE_INVALID", "SUBMISSION_BATCH_ID_MISMATCH",
        "DUPLICATE_SAMPLE_IN_BATCH",
        "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",
        "INGESTION_AUTHORITY_CONTEXT_INVALID",
        "EXISTING_AUTHORITY_SET_INVALID",
        "EXISTING_AUTHORITY_LINEAGE_MISMATCH",
        "RECORD_SPECIFIC_VALIDATION_REASON",
        "CONFLICTING_REVIEW_REINGESTION", "BATCH_ATOMICITY_ABORTED",
    )
    first = _human_record(result, "quarantine", 0)
    second = _human_record(result, "quarantine", 1)
    mixed_and_duplicate = _ingest(
        result,
        [(first, _envelope(first, "batch-A")),
         (first, _envelope(first, "batch-B"))],
    )
    assert all(
        row["reason"] == "SUBMISSION_BATCH_ID_MISMATCH"
        for row in mixed_and_duplicate.result_records
    )
    forged = dict(first)
    forged["pdb_id"] = "FORGED_PDB"
    _unchecked_rehash_review(forged)
    forward_submissions = [
        (forged, _unchecked_envelope(forged, "record-precedence")),
        (second, _envelope(second, "record-precedence")),
    ]
    reverse_submissions = list(reversed(forward_submissions))
    forward = _ingest(result, forward_submissions)
    reverse = _ingest(result, reverse_submissions)
    forward_by_sample = {
        row["sample_index_row_id"]: row["reason"]
        for row in forward.result_records
    }
    reverse_by_sample = {
        row["sample_index_row_id"]: row["reason"]
        for row in reverse.result_records
    }
    assert forward_by_sample == reverse_by_sample == {
        first["sample_index_row_id"]: "REVIEW_IDENTITY_LINKAGE_MISMATCH",
        second["sample_index_row_id"]: "BATCH_ATOMICITY_ABORTED",
    }
    assert [
        row["sample_index_row_id"] for row in reverse.result_records
    ] == [second["sample_index_row_id"], first["sample_index_row_id"]]
    repeated = _ingest(result, forward_submissions)
    assert gate.canonical_json(forward.result_records) == gate.canonical_json(
        repeated.result_records
    )


def test_exact4_decision_effect_matrix(result):
    assert tuple(result.decision_rows[0]) == gate.DECISION_COLUMNS
    assert [row["review_decision"] for row in result.decision_rows] == list(
        gate.REVIEW_DECISIONS
    )
    blank, select, revise, quarantine = result.decision_rows
    assert blank["future_outcome"] == "blocked" and blank["blocks_batch"]
    assert select["complete_warhead_atom_set_authority_available"]
    assert revise["exact_one_attachment_boundary_authority_available"]
    assert quarantine["sample_quarantined"]
    assert all(
        not row["approves_reaction_family"]
        and not row["approves_warhead_rule"]
        and not row["approves_SMARTS"]
        and not row["creates_human_gold_label"]
        and not row["creates_training_label"]
        for row in result.decision_rows
    )


def test_exact20_registry_and_exact11_readiness(result):
    assert [row["contract_id"] for row in result.contract_rows] == [
        f"INGEST_{index:03d}" for index in range(1, 21)
    ]
    assert all(row["fails_closed"] and row["verified"] for row in result.contract_rows)
    by_id = {row["contract_id"]: row for row in result.contract_rows}
    assert "Exact14" in by_id["INGEST_004"]["semantic_name"]
    assert "exact-one meaningful batch ID" in by_id["INGEST_011"]["validation_rule"]
    assert "reason" in by_id["INGEST_012"]["required_inputs"]
    assert "review semantics" in by_id["INGEST_013"]["validation_rule"]
    assert "existing authority" in by_id["INGEST_016"]["required_inputs"]
    assert len(result.readiness_rows) == 11
    assert [row["sample_index_row_id"] for row in result.readiness_rows] == sorted(
        row["sample_index_row_id"] for row in result.readiness_rows
    )
    for row in result.readiness_rows:
        assert row["ready_for_human_review_submission"] is True
        assert row["completed_review_record_available"] is False
        assert row["completed_review_record_sha256"] == ""
        assert row["ingestion_envelope_available"] is False
        assert row["ready_for_review_ingestion_execution"] is False
        assert row["authority_record_available"] is False
        assert row["sample_quarantined"] is False
        assert all(reason in row["blocking_reasons"] for reason in (
            "completed_human_review_record_missing",
            "human_provenance_attestation_missing",
            "ingestion_envelope_missing",
            "review_ingestion_not_executed",
        ))


def test_exact51_typed_unique_fail_closed(result):
    assert len(gate.FAILURE_MUTATIONS) == len(result.failure_rows) == 51
    assert len({row["mutation_signature"] for row in result.failure_rows}) == 51
    baseline = gate.IngestionGateScenario()
    for _, field, value, reason in gate.FAILURE_MUTATIONS:
        assert type(getattr(baseline, field)) is type(value)
        assert getattr(baseline, field) != value
        scenario = replace(baseline, **{field: value})
        assert reason in gate.observe_failure_scenario(scenario)
        assert gate.transaction_tables(scenario) == ((), (), ())
    assert all(
        row["expected_reason_verified"] and row["fails_closed"]
        and row["contract_row_count"] == 0
        and row["decision_effect_row_count"] == 0
        and row["current11_readiness_row_count"] == 0
        and row["actual_review_record_count"] == 0
        and row["actual_ingestion_envelope_count"] == 0
        and row["actual_ingestion_result_count"] == 0
        and row["actual_authority_record_count"] == 0
        and not row["SMARTS_ready"] and not row["training_ready"]
        for row in result.failure_rows
    )


def test_manifest_truth_interface_ready_execution_closed():
    manifest = json.loads((ROOT / gate.OUTPUT_ROOT / gate.MANIFEST_FILE).read_bytes())
    assert manifest["transaction_succeeded"] is True
    assert manifest["review_ingestion_gate_design_completed"] is True
    assert manifest["ready_for_review_ingestion_interface_implementation"] is True
    assert manifest["ready_for_review_ingestion_execution"] is False
    assert manifest["completed_review_record_count"] == 0
    assert manifest["ingestion_envelope_count"] == 0
    assert manifest["ingestion_result_count"] == 0
    assert manifest["authority_record_count"] == 0
    assert manifest["human_provenance_attestation_required"] is True
    assert manifest["human_provenance_cryptographically_verified"] is False
    assert manifest["completed_review_package_identity_field_count"] == 14
    assert manifest["completed_review_package_identity_fields"] == list(
        gate.COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS
    )
    assert manifest["single_submission_batch_id_required"] is True
    assert manifest["existing_authority_validation_required"] is True
    assert manifest["existing_authority_unique_sample_required"] is True
    assert manifest["existing_authority_package_lineage_required"] is True
    assert manifest["existing_authority_decision_evidence_required"] is True
    assert manifest["ingestion_authority_context_version"] == (
        gate.INGESTION_AUTHORITY_CONTEXT_VERSION
    )
    assert manifest["ingestion_authority_context_field_count"] == 4
    assert manifest["ingestion_authority_context_fields"] == list(
        gate.INGESTION_AUTHORITY_CONTEXT_FIELDS
    )
    assert manifest["ingestion_authority_context_source_count"] == 13
    assert manifest["ingestion_authority_context_built_from_formal_base"] is True
    assert manifest["ingestion_authority_context_validation_required"] is True
    assert manifest["external_authority_maps_allowed"] is False
    assert manifest["ingestion_result_reason_effect_contract_version"] == (
        gate.INGESTION_RESULT_REASON_EFFECT_CONTRACT_VERSION
    )
    assert manifest["ingestion_result_reason_effect_invariants_frozen"] is True
    assert manifest["ingestion_result_reason_codes"] == list(
        gate.INGESTION_RESULT_REASON_CODES
    )
    assert manifest["ingestion_result_reason_code_count"] == 31
    assert manifest["ingestion_failure_reason_precedence"] == list(
        gate.INGESTION_FAILURE_REASON_PRECEDENCE
    )
    assert manifest["public_reason_vocabulary_frozen"] is True
    assert manifest["deterministic_failure_precedence"] is True
    assert manifest["failure_mutation_count"] == 51
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["canonical_masks"] == list(gate.CANONICAL_MASKS)
    assert gate.MANIFEST_FILE not in manifest["output_sha256"]
    text = json.dumps(manifest)
    assert "/cpfs" not in text and "timestamp" not in text.casefold()


def test_design_materializes_no_lifecycle_or_downstream_artifact():
    names = {path.name for path in (ROOT / gate.OUTPUT_ROOT).iterdir()}
    assert names == set(gate.OUTPUT_FILES)
    assert not any(
        token in name for name in names
        for token in ("completed_review", "ingestion_envelope",
                      "ingestion_result", "authority_record", "smarts")
    )


def test_materialization_byte_determinism():
    first = gate.build_evidence_payloads(ROOT)
    second = gate.build_evidence_payloads(ROOT)
    assert first == second
    assert set(first) == set(gate.OUTPUT_FILES)


def test_isolated_import_silent_and_side_effect_free(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "import covalent_ext."
            "covapie_current11_warhead_atom_set_and_attachment_boundary_"
            "review_ingestion_gate_design_v1",
        ),
        cwd=tmp_path, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert before == after


def test_exact10_filesystem_safety():
    assert len(gate.EXACT10_PATHS) == len(set(gate.EXACT10_PATHS)) == 10
    for relative in gate.EXACT10_PATHS:
        path = ROOT / relative
        assert path.is_file() and not path.is_symlink()
        assert stat.S_IMODE(path.stat(follow_symlinks=False).st_mode) in {
            0o644, 0o664,
        }
        assert path.stat().st_size < 5 * 1024 * 1024
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES


def test_shared_hermetic_lifecycle_exact4_and_cleanup(tmp_path):
    workspace = tmp_path / "lifecycle"
    workspace.mkdir()
    before = subprocess.run(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT, workspace, base_commit=gate.BASE_COMMIT,
        formal_commit_subject=gate.FORMAL_COMMIT_SUBJECT,
        exact_paths=gate.EXACT10_PATHS,
    )
    after = subprocess.run(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout
    states = (
        report.pre_commit, report.detached_candidate_post_commit,
        report.formal_main_post_commit_unpushed, report.formal_main_post_push,
    )
    assert tuple(state.lifecycle for state in states) == lifecycle.LIFECYCLES
    assert report.candidate_parent == gate.BASE_COMMIT
    assert report.candidate_subject == gate.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10 and report.cleanup_verified
    assert before == after and tuple(workspace.iterdir()) == ()
