#!/usr/bin/env python3
"""Independent checker for the Current11 review-ingestion gate design v1."""

from __future__ import annotations

import csv
import hashlib
import inspect
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest
import rdkit

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as gate,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "d0243f7b5d8c0ff7a2831be1a5ed904fb8ff294f"
BASE_IDENTITY = (
    BASE,
    "ec9b1efbcfc49eeda55d7318b38daec67455343a",
    "fb80f7e22552a5eb2b20edde2048a254b4d3aef3",
    "add CovaPIE Current11 warhead atom set and attachment boundary review packages v1",
)
SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review ingestion gate design v1"
)
SCHEMA = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_gate_design_v1"
)
OUTPUT = Path("data/derived/covalent_small") / SCHEMA
SOURCE_FILE = "covapie_review_ingestion_gate_source_inventory.csv"
CONTRACT_FILE = "covapie_review_ingestion_contract_registry.csv"
DECISION_FILE = "covapie_review_ingestion_decision_effect_matrix.csv"
READINESS_FILE = "covapie_current11_review_ingestion_readiness_matrix.csv"
FAILURE_FILE = "covapie_review_ingestion_gate_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_warhead_boundary_review_ingestion_"
    "gate_design_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE, CONTRACT_FILE, DECISION_FILE, READINESS_FILE, FAILURE_FILE,
    MANIFEST_FILE,
)
EXACT10 = (
    Path("src/covalent_ext") / f"{SCHEMA}.py",
    Path("tests") / f"test_{SCHEMA}.py",
    Path("scripts") / f"check_{SCHEMA}.py",
    Path("docs") / f"{SCHEMA}_summary.md",
    *(OUTPUT / name for name in OUTPUT_FILES),
)

PACKAGE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_v1"
)
PACKAGE_PRODUCTION = Path("src/covalent_ext") / (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_v1.py"
)
PACKAGE_MANIFEST = PACKAGE_ROOT / (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_manifest.json"
)
PACKAGE_INDEX = (
    PACKAGE_ROOT / "covapie_current11_warhead_boundary_review_package_index.csv"
)
PACKAGE_OPTIONS = (
    PACKAGE_ROOT
    / "covapie_current11_warhead_boundary_candidate_review_options.csv"
)
PACKAGE_TEMPLATES = (
    PACKAGE_ROOT / "covapie_current11_warhead_boundary_review_record_templates.csv"
)
PACKAGE_FAILURE = PACKAGE_ROOT / "covapie_warhead_boundary_review_package_failure_matrix.csv"
PROPOSAL_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals_v1"
)
PROPOSALS = PROPOSAL_ROOT / (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals.csv"
)
PROPOSAL_MANIFEST = PROPOSAL_ROOT / (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals_manifest.json"
)
ASSIGNMENTS = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/"
    "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
PARENT_ATOMS = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1/"
    "covapie_exact9_parent_heavy_atom_authority.csv"
)
PARENT_BONDS = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1/"
    "covapie_exact9_parent_heavy_bond_authority.csv"
)
ROLE_CONTRACT = Path("src/covalent_ext") / (
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
PARALLEL_REVIEW_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_"
    "review_packages_v1/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_"
    "review_packages_manifest.json"
)
EXPECTED_SHA = {
    PACKAGE_PRODUCTION:
        "7534a11b6c29f3d5d3268de34773e1d2ca5075624dbf05e30672705fa294e6c0",
    PACKAGE_MANIFEST:
        "5eff02e8ec764e35696e83136e61151c27a1d3101f811bcfbaa79278448015ea",
    PACKAGE_INDEX:
        "ead184e5bd092d6b10770ebdd3688cf2b8f72b7e30a29d1957aa5e4d06b7cd33",
    PACKAGE_OPTIONS:
        "bdac9a806043a81aff4310f2931d4431f1d8966e21437f150b15360f281f353d",
    PACKAGE_TEMPLATES:
        "62a98848db9fb44f0cc597f8b78755de3e981f1ffba6985853a29e9ed90088f8",
    PACKAGE_FAILURE:
        "706307754b4c1c2ead7422cd4648604d82468f283a6bce57665195161871522b",
    PROPOSALS:
        "7e72fc157bb52cc2d5cba0c3fd2a7ac88f92bc50a35d001cfff0c2bf3296b4b0",
    PROPOSAL_MANIFEST:
        "fed5f97d177b9a0f91ec7eebf8ea3081662731e50ca6a74f3898f3068a5e6b79",
    ASSIGNMENTS:
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    PARENT_ATOMS:
        "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BONDS:
        "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    ROLE_CONTRACT:
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    PARALLEL_REVIEW_MANIFEST:
        "677034c0b8822e0b1476e28d00bb8dda5c8e53f5f42fcda790d9c4a81fa8a90b",
}
CONTEXT_VERSION = (
    "covapie_current11_warhead_boundary_ingestion_authority_context_v1"
)
CONTEXT_FIELDS = (
    "ingestion_authority_context_version", "formal_base_commit",
    "ordered_source_path_sha256_pairs",
    "ingestion_authority_context_record_sha256",
)
RESULT_EFFECT_VERSION = (
    "covapie_current11_warhead_boundary_ingestion_result_reason_effect_v1"
)

REVIEW_FIELDS = (
    "review_record_version", "review_unit_type", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_assignment_record_sha256",
    "source_candidate_set_sha256", "total_candidate_count",
    "admitted_candidate_count", "review_decision",
    "selected_bridge_candidate_index_0based",
    "selected_bridge_candidate_record_sha256", "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order", "reviewed_boundary_bond_id",
    "reviewer_id", "review_rationale", "review_notes",
    "review_record_sha256",
)
IDENTITY_FIELDS = (
    "review_record_version", "review_unit_type", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_assignment_record_sha256",
    "source_candidate_set_sha256", "total_candidate_count",
    "admitted_candidate_count",
)
ENVELOPE_FIELDS = (
    "ingestion_envelope_version", "submission_batch_id", "sample_index_row_id",
    "review_record_sha256", "submitted_record_payload_sha256",
    "reviewer_provenance_attested", "reviewer_provenance_attestor_id",
    "submission_source_label", "ingestion_envelope_sha256",
)
AUTHORITY_FIELDS = (
    "authority_record_version", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "warhead_type_candidate_class_id", "reaction_family_id",
    "warhead_rule_id", "source_assignment_record_sha256",
    "source_proposal_record_sha256", "source_candidate_set_sha256",
    "source_review_record_sha256", "source_ingestion_envelope_sha256",
    "review_decision", "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order", "reviewed_boundary_bond_id",
    "reviewer_id", "review_rationale_sha256", "authority_disposition",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available", "sample_quarantined",
    "supersedes_authority_record_sha256", "authority_status",
    "authority_record_sha256",
)
RESULT_FIELDS = (
    "ingestion_result_version", "submission_batch_id", "sample_index_row_id",
    "review_record_sha256", "ingestion_envelope_sha256", "outcome", "passed",
    "blocks_batch", "reason", "review_decision", "review_completed",
    "authority_disposition", "authority_record_sha256", "idempotent_replay",
    "conflicting_existing_authority", "consumed_review_record",
    "consumed_ingestion_envelope", "ingestion_result_sha256",
)
OPTION_FIELDS = (
    "package_option_version", "package_item_order_0based",
    "option_order_within_sample_0based", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_candidate_set_sha256",
    "source_bridge_candidate_index_0based",
    "source_bridge_candidate_record_sha256", "boundary_bond_id",
    "warhead_attachment_atom_id", "nonwarhead_boundary_atom_id",
    "boundary_bond_order", "warhead_side_atom_ids",
    "warhead_extra_atom_ids_beyond_local_center",
    "local_reaction_center_atom_ids", "required_leaving_group_atom_ids",
    "warhead_side_atom_count", "nonwarhead_side_atom_count",
    "candidate_admitted", "review_eligible", "blocking_reasons",
    "package_option_record_sha256",
)
OPTION_INT = {
    "package_item_order_0based", "option_order_within_sample_0based",
    "warhead_type_candidate_class_index_0based",
    "source_bridge_candidate_index_0based", "warhead_side_atom_count",
    "nonwarhead_side_atom_count",
}
OPTION_BOOL = {"candidate_admitted", "review_eligible"}
OPTION_LIST = {
    "warhead_side_atom_ids", "warhead_extra_atom_ids_beyond_local_center",
    "local_reaction_center_atom_ids", "required_leaving_group_atom_ids",
}
FAILURE_CASES = (
    "BASE source missing", "BASE source SHA mismatch",
    "review-package transaction not succeeded", "package count not 11",
    "option count not 200", "template count not 11",
    "candidate-set identity count not 11", "option record SHA mismatch",
    "unreviewed template payload SHA mismatch",
    "inherited review-field inventory mismatch",
    "ingestion-envelope field inventory mismatch",
    "ingestion-envelope exact type invalid",
    "ingestion-envelope SHA mismatch", "submitted review payload SHA mismatch",
    "envelope/sample/review linkage mismatch",
    "completed review-record SHA invalid",
    "not-reviewed submitted as completion", "reviewer not meaningful",
    "forbidden automated reviewer", "provenance attestation false",
    "provenance attestor invalid", "select decision dependency invalid",
    "select decision references ineligible option",
    "revise decision graph invariant invalid",
    "quarantine decision dependency invalid", "duplicate sample in batch",
    "duplicate review-record SHA in batch", "partial-batch policy mismatch",
    "batch atomicity disabled", "exact replay not idempotent",
    "conflicting re-ingestion accepted", "V1 supersession unexpectedly allowed",
    "authority source-lineage mismatch",
    "authority record field/type/hash invalid",
    "ingestion result field/type/hash invalid",
    "select/revise failed to open reviewed authority",
    "quarantine incorrectly opened authority",
    "family/rule/SMARTS/gold prematurely opened",
    "role/mask/model/training prematurely opened",
    "actual review/result/authority materialized during design",
    "completed review/package identity mismatch",
    "mixed submission batch IDs",
    "duplicate existing authority sample",
    "existing authority schema/type/hash invalid",
    "existing authority/package lineage mismatch",
    "public reason vocabulary or precedence invalid",
    "authority context source inventory mismatch",
    "authority context source SHA mismatch",
    "external caller-supplied authority maps accepted",
    "ingestion result reason/effect mismatch",
    "existing authority decision evidence invalid",
)
PUBLIC_REASONS = (
    "PASSED", "IDEMPOTENT_REPLAY", "BATCH_SIZE_INVALID",
    "SUBMISSION_BATCH_ID_MISMATCH", "DUPLICATE_SAMPLE_IN_BATCH",
    "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH", "BATCH_ATOMICITY_ABORTED",
    "REVIEW_NOT_COMPLETED", "REVIEW_IDENTITY_LINKAGE_MISMATCH",
    "COMPLETED_REVIEW_RECORD_SHA_INVALID", "REVIEWER_NOT_MEANINGFUL",
    "FORBIDDEN_AUTOMATED_REVIEWER", "REVIEW_RATIONALE_NOT_MEANINGFUL",
    "REVIEW_NOTES_NOT_MEANINGFUL", "SELECT_DEPENDENCY_INVALID",
    "SELECT_OPTION_NOT_REVIEW_ELIGIBLE", "REVISE_GRAPH_INVARIANT_INVALID",
    "QUARANTINE_DEPENDENCY_INVALID",
    "INGESTION_ENVELOPE_IDENTITY_INVALID",
    "INGESTION_ENVELOPE_EXACT_TYPE_INVALID",
    "INGESTION_ENVELOPE_SHA_INVALID",
    "SUBMISSION_BATCH_ID_NOT_MEANINGFUL",
    "HUMAN_PROVENANCE_ATTESTATION_REQUIRED",
    "PROVENANCE_ATTESTOR_INVALID",
    "SUBMISSION_SOURCE_LABEL_NOT_MEANINGFUL",
    "ENVELOPE_SAMPLE_REVIEW_LINKAGE_MISMATCH",
    "SUBMITTED_REVIEW_PAYLOAD_SHA_MISMATCH",
    "EXISTING_AUTHORITY_SET_INVALID",
    "EXISTING_AUTHORITY_LINEAGE_MISMATCH",
    "CONFLICTING_REVIEW_REINGESTION",
    "INGESTION_AUTHORITY_CONTEXT_INVALID",
)
REASON_PRECEDENCE = (
    "BATCH_SIZE_INVALID", "SUBMISSION_BATCH_ID_MISMATCH",
    "DUPLICATE_SAMPLE_IN_BATCH",
    "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",
    "INGESTION_AUTHORITY_CONTEXT_INVALID",
    "EXISTING_AUTHORITY_SET_INVALID",
    "EXISTING_AUTHORITY_LINEAGE_MISMATCH",
    "RECORD_SPECIFIC_VALIDATION_REASON",
    "CONFLICTING_REVIEW_REINGESTION", "BATCH_ATOMICITY_ABORTED",
)
SHA = re.compile(r"[0-9a-f]{64}")


def run_git(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *args), cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def base_payload(path: Path) -> bytes:
    payload = run_git("show", f"{BASE}:{path.as_posix()}")
    assert payload and digest(payload) == EXPECTED_SHA[path]
    assert subprocess.run(
        ("git", "cat-file", "-e", f"{BASE}:{path.as_posix()}"),
        cwd=ROOT, check=False, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    return payload


def parse_int(value: str) -> int:
    assert value and value.isdecimal() and (value == "0" or not value.startswith("0"))
    return int(value)


def parse_bool(value: str) -> bool:
    assert value in ("true", "false")
    return value == "true"


def parse_list(value: str) -> list[str]:
    result = json.loads(value)
    assert type(result) is list and all(type(item) is str for item in result)
    return result


def typed_review(row: Mapping[str, str]) -> dict[str, Any]:
    assert tuple(row) == REVIEW_FIELDS
    result: dict[str, Any] = {}
    for field in REVIEW_FIELDS:
        if field in {
            "warhead_type_candidate_class_index_0based",
            "total_candidate_count", "admitted_candidate_count",
        }:
            result[field] = parse_int(row[field])
        elif field == "selected_bridge_candidate_index_0based":
            result[field] = None if row[field] == "" else parse_int(row[field])
        elif field == "reviewed_warhead_atom_ids":
            result[field] = parse_list(row[field])
        else:
            result[field] = row[field]
    return result


def independent_package_identities(
    index_rows: Sequence[Mapping[str, str]],
    template_rows: Sequence[Mapping[str, str]],
) -> dict[str, dict[str, Any]]:
    assert len(index_rows) == len(template_rows) == 11
    from_index: dict[str, dict[str, Any]] = {}
    for row in index_rows:
        identity: dict[str, Any] = {}
        for field in IDENTITY_FIELDS:
            if field == "review_unit_type":
                identity[field] = "sample_warhead_atom_set_and_attachment_boundary"
            elif field in {
                "warhead_type_candidate_class_index_0based",
                "total_candidate_count", "admitted_candidate_count",
            }:
                identity[field] = parse_int(row[field])
            else:
                identity[field] = row[field]
        sample = identity["sample_index_row_id"]
        assert sample not in from_index
        from_index[sample] = identity
    from_templates: dict[str, dict[str, Any]] = {}
    for raw in template_rows:
        typed = typed_review(raw)
        identity = {field: typed[field] for field in IDENTITY_FIELDS}
        sample = identity["sample_index_row_id"]
        assert sample not in from_templates
        from_templates[sample] = identity
    assert set(from_index) == set(from_templates)
    for sample, identity in from_index.items():
        assert identity == from_templates[sample]
        for field, value in identity.items():
            if field in {
                "warhead_type_candidate_class_index_0based",
                "total_candidate_count", "admitted_candidate_count",
            }:
                assert type(value) is int and value >= 0
            else:
                assert type(value) is str and value.strip()
        for field in (
            "source_proposal_record_sha256",
            "source_assignment_record_sha256",
            "source_candidate_set_sha256",
        ):
            assert SHA.fullmatch(identity[field])
    return {sample: from_index[sample] for sample in sorted(from_index)}


def independent_review_identity_matches(
    review: Mapping[str, Any],
    identities: Mapping[str, Mapping[str, Any]],
) -> bool:
    sample = review.get("sample_index_row_id")
    if type(sample) is not str or sample not in identities:
        return False
    try:
        observed = {field: review[field] for field in IDENTITY_FIELDS}
    except KeyError:
        return False
    return observed == identities[sample]


def typed_option(row: Mapping[str, str]) -> dict[str, Any]:
    assert tuple(row) == OPTION_FIELDS
    result: dict[str, Any] = {}
    for field in OPTION_FIELDS:
        if field in OPTION_INT:
            result[field] = parse_int(row[field])
        elif field in OPTION_BOOL:
            result[field] = parse_bool(row[field])
        elif field in OPTION_LIST:
            result[field] = parse_list(row[field])
        else:
            result[field] = row[field]
    expected = digest(canonical({
        field: result[field] for field in OPTION_FIELDS
        if field != "package_option_record_sha256"
    }).encode())
    assert result["package_option_record_sha256"] == expected
    return result


def hash_excluding(
    record: Mapping[str, Any], fields: Sequence[str], excluded: str,
) -> str:
    assert tuple(record) == tuple(fields)
    return digest(canonical({
        field: record[field] for field in fields if field != excluded
    }).encode())


def independent_context(
    frozen: Mapping[Path, bytes],
) -> tuple[dict[str, Any], tuple[tuple[str, bytes], ...]]:
    payloads = tuple(
        (path.as_posix(), frozen[path]) for path in EXPECTED_SHA
    )
    record: dict[str, Any] = {
        "ingestion_authority_context_version": CONTEXT_VERSION,
        "formal_base_commit": BASE,
        "ordered_source_path_sha256_pairs": [
            f"{path}\t{digest(payload)}" for path, payload in payloads
        ],
        "ingestion_authority_context_record_sha256": "",
    }
    record["ingestion_authority_context_record_sha256"] = hash_excluding(
        record, CONTEXT_FIELDS,
        "ingestion_authority_context_record_sha256",
    )
    return record, payloads


def independent_context_valid(
    record: object, payloads: object,
) -> bool:
    try:
        assert type(record) is dict and tuple(record) == CONTEXT_FIELDS
        assert record["ingestion_authority_context_version"] == CONTEXT_VERSION
        assert record["formal_base_commit"] == BASE
        assert type(record["ordered_source_path_sha256_pairs"]) is list
        assert all(
            type(item) is str
            for item in record["ordered_source_path_sha256_pairs"]
        )
        assert record["ingestion_authority_context_record_sha256"] == (
            hash_excluding(
                record, CONTEXT_FIELDS,
                "ingestion_authority_context_record_sha256",
            )
        )
        assert type(payloads) is tuple and len(payloads) == len(EXPECTED_SHA) == 13
        expected_paths = [path.as_posix() for path in EXPECTED_SHA]
        observed_paths = []
        observed_pairs = []
        for item, expected_path in zip(payloads, EXPECTED_SHA):
            assert (
                type(item) is tuple and len(item) == 2
                and type(item[0]) is str and type(item[1]) is bytes
                and item[0] and not Path(item[0]).is_absolute()
            )
            path, payload = item
            observed_paths.append(path)
            observed_pairs.append(f"{path}\t{digest(payload)}")
            assert path == expected_path.as_posix()
            assert digest(payload) == EXPECTED_SHA[expected_path]
        assert observed_paths == expected_paths
        assert record["ordered_source_path_sha256_pairs"] == observed_pairs
        return True
    except (AssertionError, KeyError, TypeError, ValueError):
        return False


def independent_result_effect_valid(record: Mapping[str, Any]) -> bool:
    try:
        assert type(record) is dict and tuple(record) == RESULT_FIELDS
        assert record["reason"] in PUBLIC_REASONS
        assert record["outcome"] in {"passed", "blocked", "invalid"}
        assert record["ingestion_result_sha256"] == hash_excluding(
            record, RESULT_FIELDS, "ingestion_result_sha256",
        )
        passed_reasons = {"PASSED", "IDEMPOTENT_REPLAY"}
        blocked_reasons = {
            "REVIEW_NOT_COMPLETED", "CONFLICTING_REVIEW_REINGESTION",
            "BATCH_ATOMICITY_ABORTED",
        }
        if record["outcome"] == "passed":
            expected_disposition = (
                "reviewed_quarantine_no_authority"
                if record["review_decision"] == "quarantine"
                else "reviewed_authority_materialized"
                if record["review_decision"] in {
                    "select_admitted_candidate",
                    "revise_atom_set_and_boundary",
                }
                else None
            )
            return (
                record["reason"] in passed_reasons
                and record["passed"] is True
                and record["blocks_batch"] is False
                and record["review_completed"] is True
                and record["authority_disposition"] == expected_disposition
                and SHA.fullmatch(record["authority_record_sha256"]) is not None
                and record["idempotent_replay"]
                is (record["reason"] == "IDEMPOTENT_REPLAY")
                and record["conflicting_existing_authority"] is False
                and record["consumed_review_record"] is True
                and record["consumed_ingestion_envelope"] is True
            )
        if record["outcome"] == "blocked":
            return (
                record["reason"] in blocked_reasons
                and record["passed"] is False
                and record["blocks_batch"] is True
                and record["review_completed"] is False
                and record["authority_disposition"] == ""
                and record["authority_record_sha256"] == ""
                and record["idempotent_replay"] is False
                and record["conflicting_existing_authority"]
                is (record["reason"] == "CONFLICTING_REVIEW_REINGESTION")
                and record["consumed_review_record"] is False
                and record["consumed_ingestion_envelope"] is False
            )
        return (
            record["reason"] not in passed_reasons | blocked_reasons
            and record["passed"] is False
            and record["blocks_batch"] is True
            and record["review_completed"] is False
            and record["authority_disposition"] == ""
            and record["authority_record_sha256"] == ""
            and record["idempotent_replay"] is False
            and record["conflicting_existing_authority"] is False
            and record["consumed_review_record"] is False
            and record["consumed_ingestion_envelope"] is False
        )
    except (AssertionError, KeyError, TypeError, ValueError):
        return False


def independent_decision_evidence_valid(
    authority: Mapping[str, Any],
    options: Sequence[Mapping[str, Any]],
    proposal_by_sample: Mapping[str, Mapping[str, str]],
    atoms_by_ligand: Mapping[str, Sequence[Mapping[str, str]]],
    bonds_by_ligand: Mapping[str, Sequence[Mapping[str, str]]],
) -> bool:
    try:
        reviewer = authority["reviewer_id"]
        assert (
            type(reviewer) is str and reviewer.strip()
            and reviewer.strip().casefold()
            not in {"codex", "chatgpt", "openai", "automation", "auto",
                    "system", "model"}
        )
        decision = authority["review_decision"]
        evidence = (
            authority["reviewed_warhead_atom_ids"],
            authority["reviewed_warhead_attachment_atom_id"],
            authority["reviewed_nonwarhead_boundary_atom_id"],
            authority["reviewed_attachment_boundary_bond_order"],
            authority["reviewed_boundary_bond_id"],
        )
        if decision == "quarantine":
            return evidence == ([], "", "", "", "")
        if decision == "select_admitted_candidate":
            matches = [
                option for option in options
                if option["sample_index_row_id"]
                == authority["sample_index_row_id"]
                and option["source_candidate_set_sha256"]
                == authority["source_candidate_set_sha256"]
                and option["review_eligible"] is True
                and (
                    option["warhead_side_atom_ids"],
                    option["warhead_attachment_atom_id"],
                    option["nonwarhead_boundary_atom_id"],
                    option["boundary_bond_order"],
                    option["boundary_bond_id"],
                ) == evidence
            ]
            return len(matches) == 1
        assert decision == "revise_atom_set_and_boundary"
        proposal = proposal_by_sample[authority["sample_index_row_id"]]
        atom_ids = {
            row["ccd_atom_id"]
            for row in atoms_by_ligand[authority["ligand_comp_id"]]
        }
        selected = set(authority["reviewed_warhead_atom_ids"])
        local = set(json.loads(proposal["local_reaction_center_atom_ids"]))
        leaving = set(json.loads(proposal["required_leaving_group_atom_ids"]))
        assert selected and local <= selected and leaving <= selected
        assert selected < atom_ids
        adjacency = {atom: set() for atom in selected}
        boundary = []
        for bond in bonds_by_ligand[authority["ligand_comp_id"]]:
            left = bond["parent_ccd_atom_id_1"]
            right = bond["parent_ccd_atom_id_2"]
            order = bond["normalized_bond_order"]
            if left in selected and right in selected:
                adjacency[left].add(right)
                adjacency[right].add(left)
            elif (left in selected) != (right in selected):
                boundary.append((left, right, order))
        reached = set()
        pending = [next(iter(selected))]
        while pending:
            atom = pending.pop()
            if atom not in reached:
                reached.add(atom)
                pending.extend(adjacency[atom] - reached)
        assert reached == selected and len(boundary) == 1
        left, right, order = boundary[0]
        attachment = left if left in selected else right
        nonwarhead = right if attachment == left else left
        low, high = sorted((left, right), key=lambda value: value.encode())
        return evidence[1:] == (
            attachment, nonwarhead, order, f"{low}|{high}|{order}",
        )
    except (AssertionError, KeyError, TypeError, ValueError):
        return False


def actual_lifecycle() -> str:
    assert tuple(
        run_git("show", "-s", "--format=%H%n%P%n%T%n%s", BASE)
        .decode().splitlines()
    ) == BASE_IDENTITY
    head = run_git("rev-parse", "HEAD").decode().strip()
    if head == BASE:
        return "pre_commit"
    raw = run_git("cat-file", "commit", head)
    headers, separator, message = raw.partition(b"\n\n")
    assert separator
    parents = tuple(
        line[7:].decode() for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    subject, newline, body = message.partition(b"\n")
    assert parents == (BASE,) and newline and subject.decode() == SUBJECT and not body
    changed = {
        item.decode() for item in run_git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head,
        ).split(b"\0") if item
    }
    assert changed == {path.as_posix() for path in EXACT10}
    branch = subprocess.run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"), cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    assert branch.stdout.decode().strip() == "main"
    origin = run_git("rev-parse", "refs/remotes/origin/main").decode().strip()
    if origin == BASE:
        return "formal_main_post_commit_unpushed"
    assert origin == head
    return "formal_main_post_push"


def check_synthetic_schemas(
    template: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    review = typed_review(template)
    review.update({
        "review_decision": "quarantine",
        "reviewer_id": "human-reviewer-independent",
        "review_rationale": "Independent synthetic schema evidence.",
    })
    review["review_record_sha256"] = hash_excluding(
        review, REVIEW_FIELDS, "review_record_sha256",
    )
    assert SHA.fullmatch(review["review_record_sha256"])
    payload_sha = digest(canonical(review).encode())
    envelope: dict[str, Any] = {
        "ingestion_envelope_version":
            "covapie_current11_warhead_boundary_review_ingestion_envelope_v1",
        "submission_batch_id": "independent-synthetic-batch",
        "sample_index_row_id": review["sample_index_row_id"],
        "review_record_sha256": review["review_record_sha256"],
        "submitted_record_payload_sha256": payload_sha,
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "human-attestor-independent",
        "submission_source_label": "independent-in-memory-test",
        "ingestion_envelope_sha256": "",
    }
    envelope["ingestion_envelope_sha256"] = hash_excluding(
        envelope, ENVELOPE_FIELDS, "ingestion_envelope_sha256",
    )
    assert tuple(envelope) == ENVELOPE_FIELDS
    authority: dict[str, Any] = {
        "authority_record_version":
            "covapie_current11_reviewed_warhead_atom_set_and_attachment_boundary_authority_v1",
        "sample_index_row_id": review["sample_index_row_id"],
        "pdb_id": review["pdb_id"], "ligand_comp_id": review["ligand_comp_id"],
        "warhead_type_candidate_class_id":
            review["warhead_type_candidate_class_id"],
        "reaction_family_id": review["reaction_family_id"],
        "warhead_rule_id": review["warhead_rule_id"],
        "source_assignment_record_sha256":
            review["source_assignment_record_sha256"],
        "source_proposal_record_sha256":
            review["source_proposal_record_sha256"],
        "source_candidate_set_sha256": review["source_candidate_set_sha256"],
        "source_review_record_sha256": review["review_record_sha256"],
        "source_ingestion_envelope_sha256":
            envelope["ingestion_envelope_sha256"],
        "review_decision": "quarantine", "reviewed_warhead_atom_ids": [],
        "reviewed_warhead_attachment_atom_id": "",
        "reviewed_nonwarhead_boundary_atom_id": "",
        "reviewed_attachment_boundary_bond_order": "",
        "reviewed_boundary_bond_id": "", "reviewer_id": review["reviewer_id"],
        "review_rationale_sha256":
            digest(review["review_rationale"].encode()),
        "authority_disposition": "reviewed_quarantine_no_authority",
        "complete_warhead_atom_set_authority_available": False,
        "exact_one_attachment_boundary_authority_available": False,
        "sample_quarantined": True, "supersedes_authority_record_sha256": "",
        "authority_status": "quarantined", "authority_record_sha256": "",
    }
    authority["authority_record_sha256"] = hash_excluding(
        authority, AUTHORITY_FIELDS, "authority_record_sha256",
    )
    result: dict[str, Any] = {
        "ingestion_result_version":
            "covapie_current11_warhead_boundary_review_ingestion_result_v1",
        "submission_batch_id": envelope["submission_batch_id"],
        "sample_index_row_id": review["sample_index_row_id"],
        "review_record_sha256": review["review_record_sha256"],
        "ingestion_envelope_sha256": envelope["ingestion_envelope_sha256"],
        "outcome": "passed", "passed": True, "blocks_batch": False,
        "reason": "PASSED", "review_decision": "quarantine",
        "review_completed": True,
        "authority_disposition": authority["authority_disposition"],
        "authority_record_sha256": authority["authority_record_sha256"],
        "idempotent_replay": False, "conflicting_existing_authority": False,
        "consumed_review_record": True, "consumed_ingestion_envelope": True,
        "ingestion_result_sha256": "",
    }
    result["ingestion_result_sha256"] = hash_excluding(
        result, RESULT_FIELDS, "ingestion_result_sha256",
    )
    assert tuple(authority) == AUTHORITY_FIELDS and len(authority) == 27
    assert tuple(result) == RESULT_FIELDS and len(result) == 18
    assert authority["supersedes_authority_record_sha256"] == ""
    assert not authority["complete_warhead_atom_set_authority_available"]
    assert authority["sample_quarantined"] and result["passed"]
    return review, envelope, authority


def independent_existing_authority_reason(
    authorities: Sequence[Mapping[str, Any]],
    identities: Mapping[str, Mapping[str, Any]],
) -> str | None:
    bool_fields = {
        "complete_warhead_atom_set_authority_available",
        "exact_one_attachment_boundary_authority_available",
        "sample_quarantined",
    }
    try:
        for authority in authorities:
            assert type(authority) is dict and tuple(authority) == AUTHORITY_FIELDS
            for field in AUTHORITY_FIELDS:
                value = authority[field]
                if field in bool_fields:
                    assert type(value) is bool
                elif field == "reviewed_warhead_atom_ids":
                    assert type(value) is list
                    assert all(type(item) is str for item in value)
                else:
                    assert type(value) is str
            assert authority["supersedes_authority_record_sha256"] == ""
            assert authority["authority_record_sha256"] == hash_excluding(
                authority, AUTHORITY_FIELDS, "authority_record_sha256",
            )
            quarantine = authority["review_decision"] == "quarantine"
            assert authority["authority_disposition"] == (
                "reviewed_quarantine_no_authority"
                if quarantine else "reviewed_authority_materialized"
            )
            assert authority["authority_status"] == (
                "quarantined" if quarantine else "active"
            )
            assert authority[
                "complete_warhead_atom_set_authority_available"
            ] is (not quarantine)
            assert authority[
                "exact_one_attachment_boundary_authority_available"
            ] is (not quarantine)
            assert authority["sample_quarantined"] is quarantine
    except (AssertionError, KeyError, TypeError, ValueError):
        return "EXISTING_AUTHORITY_SET_INVALID"
    samples = [row["sample_index_row_id"] for row in authorities]
    digests = [row["authority_record_sha256"] for row in authorities]
    if len(samples) != len(set(samples)) or len(digests) != len(set(digests)):
        return "EXISTING_AUTHORITY_SET_INVALID"
    joins = {
        "sample_index_row_id": "sample_index_row_id",
        "pdb_id": "pdb_id", "ligand_comp_id": "ligand_comp_id",
        "warhead_type_candidate_class_id": "warhead_type_candidate_class_id",
        "reaction_family_id": "reaction_family_id",
        "warhead_rule_id": "warhead_rule_id",
        "source_assignment_record_sha256": "source_assignment_record_sha256",
        "source_proposal_record_sha256": "source_proposal_record_sha256",
        "source_candidate_set_sha256": "source_candidate_set_sha256",
    }
    for authority in authorities:
        sample = authority["sample_index_row_id"]
        if sample not in identities:
            return "EXISTING_AUTHORITY_LINEAGE_MISMATCH"
        if any(
            authority[authority_field] != identities[sample][identity_field]
            for authority_field, identity_field in joins.items()
        ):
            return "EXISTING_AUTHORITY_LINEAGE_MISMATCH"
    return None


def independent_replay_semantics_match(
    authority: Mapping[str, Any],
    review: Mapping[str, Any],
) -> bool:
    return (
        authority["source_review_record_sha256"]
        == review["review_record_sha256"]
        and authority["review_decision"] == review["review_decision"]
        and authority["reviewed_warhead_atom_ids"]
        == review["reviewed_warhead_atom_ids"]
        and authority["reviewed_warhead_attachment_atom_id"]
        == review["reviewed_warhead_attachment_atom_id"]
        and authority["reviewed_nonwarhead_boundary_atom_id"]
        == review["reviewed_nonwarhead_boundary_atom_id"]
        and authority["reviewed_attachment_boundary_bond_order"]
        == review["reviewed_attachment_boundary_bond_order"]
        and authority["reviewed_boundary_bond_id"]
        == review["reviewed_boundary_bond_id"]
        and authority["reviewer_id"] == review["reviewer_id"]
        and authority["review_rationale_sha256"]
        == digest(review["review_rationale"].encode())
    )


def check_batch_duplicate_replay_contracts() -> None:
    """Independently exercise the frozen V1 transaction state machine."""

    def simulate(
        submitted: Sequence[tuple[str, str, str, str]],
        existing: Mapping[str, str] | None = None,
    ) -> tuple[bool, tuple[str, ...], int]:
        # Each tuple is (sample_id, review_sha, batch_id, validation_state).
        existing = {} if existing is None else dict(existing)
        if not 1 <= len(submitted) <= 11:
            return False, ("BATCH_SIZE_INVALID",), 0
        samples = [sample for sample, _, _, _ in submitted]
        review_shas = [review_sha for _, review_sha, _, _ in submitted]
        batch_ids = [batch_id for _, _, batch_id, _ in submitted]
        if any(batch_id != batch_ids[0] for batch_id in batch_ids[1:]):
            return False, tuple(
                "SUBMISSION_BATCH_ID_MISMATCH" for _ in submitted
            ), 0
        if len(samples) != len(set(samples)):
            return False, ("DUPLICATE_SAMPLE_IN_BATCH",), 0
        if len(review_shas) != len(set(review_shas)):
            return False, ("DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",), 0
        reasons = []
        new_authority_count = 0
        for sample, review_sha, _, state in submitted:
            if state != "valid":
                reasons.append(state)
                continue
            if sample in existing:
                reasons.append(
                    "IDEMPOTENT_REPLAY"
                    if existing[sample] == review_sha
                    else "CONFLICTING_REVIEW_REINGESTION"
                )
            else:
                reasons.append("PASSED")
                new_authority_count += 1
        if any(reason not in {"PASSED", "IDEMPOTENT_REPLAY"} for reason in reasons):
            return False, tuple(reasons), 0
        return True, tuple(reasons), new_authority_count

    first = "1" * 64
    second = "2" * 64
    assert simulate((("S1", first, "batch", "valid"),)) == (
        True, ("PASSED",), 1,
    )
    assert simulate((
        ("S1", first, "batch", "valid"),
        ("S2", second, "batch", "valid"),
    )) == (True, ("PASSED", "PASSED"), 2)
    assert simulate((
        ("S1", first, "batch", "valid"),
        ("S1", second, "batch", "valid"),
    )) == (False, ("DUPLICATE_SAMPLE_IN_BATCH",), 0)
    assert simulate((
        ("S1", first, "batch", "valid"),
        ("S2", first, "batch", "valid"),
    )) == (False, ("DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",), 0)
    assert simulate((
        ("S1", first, "batch", "valid"),
        ("S2", second, "batch", "REVIEW_NOT_COMPLETED"),
    )) == (False, ("PASSED", "REVIEW_NOT_COMPLETED"), 0)
    assert simulate((
        ("S1", first, "batch-A", "valid"),
        ("S2", second, "batch-B", "valid"),
    )) == (
        False,
        ("SUBMISSION_BATCH_ID_MISMATCH", "SUBMISSION_BATCH_ID_MISMATCH"),
        0,
    )
    assert simulate(
        (("S1", first, "batch", "valid"),), {"S1": first},
    ) == (True, ("IDEMPOTENT_REPLAY",), 0)
    assert simulate(
        (("S1", second, "batch", "valid"),), {"S1": first},
    ) == (False, ("CONFLICTING_REVIEW_REINGESTION",), 0)


def synthetic_submission(
    template: Mapping[str, str],
    options: Sequence[Mapping[str, Any]],
    decision: str,
    batch: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    review = typed_review(template)
    if decision in {
        "select_admitted_candidate", "revise_atom_set_and_boundary",
    }:
        option = next(
            row for row in options
            if row["sample_index_row_id"] == review["sample_index_row_id"]
            and row["review_eligible"]
        )
        review.update({
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
            review["selected_bridge_candidate_index_0based"] = (
                option["source_bridge_candidate_index_0based"]
            )
            review["selected_bridge_candidate_record_sha256"] = (
                option["source_bridge_candidate_record_sha256"]
            )
    review.update({
        "review_decision": decision,
        "reviewer_id": "human-reviewer-independent",
        "review_rationale": "Independent decision-evidence check.",
        "review_notes": "",
    })
    review["review_record_sha256"] = hash_excluding(
        review, REVIEW_FIELDS, "review_record_sha256",
    )
    envelope: dict[str, Any] = {
        "ingestion_envelope_version":
            "covapie_current11_warhead_boundary_review_ingestion_envelope_v1",
        "submission_batch_id": batch,
        "sample_index_row_id": review["sample_index_row_id"],
        "review_record_sha256": review["review_record_sha256"],
        "submitted_record_payload_sha256": digest(canonical(review).encode()),
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "human-attestor-independent",
        "submission_source_label": "independent-in-memory-test",
        "ingestion_envelope_sha256": "",
    }
    envelope["ingestion_envelope_sha256"] = hash_excluding(
        envelope, ENVELOPE_FIELDS, "ingestion_envelope_sha256",
    )
    return review, envelope


def main() -> int:
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"
    assert rdkit.__version__ == "2022.03.2"
    current = actual_lifecycle()
    frozen = {path: base_payload(path) for path in EXPECTED_SHA}
    context_record, context_payloads = independent_context(frozen)
    assert independent_context_valid(context_record, context_payloads)
    assert len(context_record) == len(CONTEXT_FIELDS) == 4
    assert len(context_payloads) == 13
    forged_payloads = list(context_payloads)
    forged_path, forged_payload = forged_payloads[2]
    forged_payloads[2] = (
        forged_path, forged_payload[:-1] + bytes([forged_payload[-1] ^ 1]),
    )
    forged_context_record = dict(context_record)
    forged_context_record["ordered_source_path_sha256_pairs"] = list(
        forged_context_record["ordered_source_path_sha256_pairs"]
    )
    forged_context_record["ordered_source_path_sha256_pairs"][2] = (
        f"{forged_path}\t{digest(forged_payloads[2][1])}"
    )
    forged_context_record[
        "ingestion_authority_context_record_sha256"
    ] = hash_excluding(
        forged_context_record, CONTEXT_FIELDS,
        "ingestion_authority_context_record_sha256",
    )
    assert not independent_context_valid(
        forged_context_record, tuple(forged_payloads),
    )
    parameters = inspect.signature(gate.ingest_review_batch).parameters
    assert tuple(parameters) == (
        "submissions", "authority_context", "existing_authorities",
    )
    assert not {
        "package_identity_by_sample", "options", "proposals_by_sample",
        "parent_atom_ids_by_ligand", "parent_bonds_by_ligand",
        "valid_sample_ids",
    } & set(parameters)
    package_manifest = json.loads(frozen[PACKAGE_MANIFEST])
    index = rows(frozen[PACKAGE_INDEX])
    options = [typed_option(row) for row in rows(frozen[PACKAGE_OPTIONS])]
    templates = rows(frozen[PACKAGE_TEMPLATES])
    proposals = rows(frozen[PROPOSALS])
    assignments = rows(frozen[ASSIGNMENTS])
    atoms = rows(frozen[PARENT_ATOMS])
    bonds = rows(frozen[PARENT_BONDS])
    assert package_manifest["transaction_succeeded"] is True
    assert (len(index), len(options), len(templates)) == (11, 200, 11)
    assert sum(row["review_eligible"] for row in options) == 185
    assert sum(not row["review_eligible"] for row in options) == 15
    assert len({row["source_candidate_set_sha256"] for row in index}) == 11
    assert len(proposals) == len(assignments) == 11 and atoms and bonds
    identities = independent_package_identities(index, templates)
    assert len(IDENTITY_FIELDS) == 14 and len(identities) == 11
    proposal_by_sample = {row["sample_index_row_id"]: row for row in proposals}
    assignment_by_sample = {
        row["sample_index_row_id"]: row for row in assignments
    }
    for sample, identity in identities.items():
        proposal = proposal_by_sample[sample]
        assignment = assignment_by_sample[sample]
        assert proposal["pdb_id"] == identity["pdb_id"]
        assert proposal["ligand_comp_id"] == identity["ligand_comp_id"]
        assert parse_int(
            proposal["warhead_type_candidate_class_index_0based"]
        ) == identity["warhead_type_candidate_class_index_0based"]
        assert proposal["warhead_type_candidate_class_id"] == identity[
            "warhead_type_candidate_class_id"
        ]
        assert proposal["reaction_family_id"] == identity["reaction_family_id"]
        assert proposal["warhead_rule_id"] == identity["warhead_rule_id"]
        assert proposal["proposal_record_sha256"] == identity[
            "source_proposal_record_sha256"
        ]
        assert proposal["source_assignment_record_sha256"] == identity[
            "source_assignment_record_sha256"
        ]
        assert assignment["assignment_record_sha256"] == identity[
            "source_assignment_record_sha256"
        ]
    for source, template in zip(index, templates):
        typed = typed_review(template)
        assert typed["review_decision"] == "not_reviewed"
        assert not typed["review_record_sha256"]
        assert hash_excluding(
            typed, REVIEW_FIELDS, "review_record_sha256",
        ) == source["unreviewed_template_payload_sha256"]
    assert len(REVIEW_FIELDS) == 26
    assert len(ENVELOPE_FIELDS) == 9
    assert len(AUTHORITY_FIELDS) == 27
    assert len(RESULT_FIELDS) == 18
    synthetic_review, _, synthetic_authority = check_synthetic_schemas(
        templates[0]
    )
    formal_context = gate.build_ingestion_authority_context(ROOT)
    forged_context = gate.IngestionAuthorityContext(
        forged_context_record, tuple(forged_payloads),
    )
    forged_review, forged_envelope = synthetic_submission(
        templates[0], options, "quarantine", "forged-context-checker",
    )
    forged_batch = gate.ingest_review_batch(
        [(forged_review, forged_envelope)], authority_context=forged_context,
    )
    assert (
        not forged_batch.passed
        and not forged_batch.new_authority_records
        and forged_batch.result_records[0]["reason"]
        == "INGESTION_AUTHORITY_CONTEXT_INVALID"
    )
    try:
        gate.ingest_review_batch(
            [(forged_review, forged_envelope)],
            authority_context=formal_context,
            options=options,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("external_authority_map_injection_accepted")
    assert independent_review_identity_matches(synthetic_review, identities)
    forged_review = dict(synthetic_review)
    forged_review.update({
        "pdb_id": "FORGED_PDB", "ligand_comp_id": "FORGED_LIGAND",
        "warhead_type_candidate_class_id": "FORGED_CLASS",
        "reaction_family_id": "FORGED_FAMILY",
        "warhead_rule_id": "FORGED_RULE",
        "source_proposal_record_sha256": "1" * 64,
        "source_assignment_record_sha256": "2" * 64,
        "source_candidate_set_sha256": "3" * 64,
    })
    forged_review["review_record_sha256"] = hash_excluding(
        forged_review, REVIEW_FIELDS, "review_record_sha256",
    )
    assert not independent_review_identity_matches(forged_review, identities)
    assert independent_existing_authority_reason(
        (synthetic_authority,), identities,
    ) is None
    assert independent_replay_semantics_match(
        synthetic_authority, synthetic_review,
    )
    duplicate_authority = dict(synthetic_authority)
    duplicate_authority["source_ingestion_envelope_sha256"] = "9" * 64
    duplicate_authority["authority_record_sha256"] = hash_excluding(
        duplicate_authority, AUTHORITY_FIELDS, "authority_record_sha256",
    )
    assert independent_existing_authority_reason(
        (synthetic_authority, duplicate_authority), identities,
    ) == "EXISTING_AUTHORITY_SET_INVALID"
    bad_hash = dict(synthetic_authority)
    bad_hash["authority_record_sha256"] = "0" * 64
    assert independent_existing_authority_reason(
        (bad_hash,), identities,
    ) == "EXISTING_AUTHORITY_SET_INVALID"
    forged_authority = dict(synthetic_authority)
    forged_authority["pdb_id"] = "FORGED_PDB"
    forged_authority["authority_record_sha256"] = hash_excluding(
        forged_authority, AUTHORITY_FIELDS, "authority_record_sha256",
    )
    assert independent_existing_authority_reason(
        (forged_authority,), identities,
    ) == "EXISTING_AUTHORITY_LINEAGE_MISMATCH"
    semantic_mismatch = dict(synthetic_authority)
    semantic_mismatch["reviewer_id"] = "different-human-reviewer"
    semantic_mismatch["authority_record_sha256"] = hash_excluding(
        semantic_mismatch, AUTHORITY_FIELDS, "authority_record_sha256",
    )
    assert independent_existing_authority_reason(
        (semantic_mismatch,), identities,
    ) is None
    assert not independent_replay_semantics_match(
        semantic_mismatch, synthetic_review,
    )
    atoms_by_ligand: dict[str, list[Mapping[str, str]]] = {}
    bonds_by_ligand: dict[str, list[Mapping[str, str]]] = {}
    for row in atoms:
        atoms_by_ligand.setdefault(row["ligand_comp_id"], []).append(row)
    for row in bonds:
        bonds_by_ligand.setdefault(row["ligand_comp_id"], []).append(row)
    generated: dict[str, tuple[
        dict[str, Any], dict[str, Any], Mapping[str, Any], Mapping[str, Any]
    ]] = {}
    for offset, decision in enumerate((
        "select_admitted_candidate", "revise_atom_set_and_boundary",
        "quarantine",
    )):
        review, envelope = synthetic_submission(
            templates[offset], options, decision, f"evidence-{decision}",
        )
        batch = gate.ingest_review_batch(
            [(review, envelope)], authority_context=formal_context,
        )
        assert batch.passed and len(batch.new_authority_records) == 1
        authority = batch.new_authority_records[0]
        assert independent_decision_evidence_valid(
            authority, options, proposal_by_sample,
            atoms_by_ligand, bonds_by_ligand,
        )
        assert independent_result_effect_valid(batch.result_records[0])
        generated[decision] = (
            review, envelope, authority, batch.result_records[0],
        )
    invalid_existing = []
    for decision, field, value in (
        ("select_admitted_candidate", "reviewed_boundary_bond_id",
         "FORGED|BOUNDARY|single"),
        ("revise_atom_set_and_boundary", "reviewed_warhead_atom_ids", []),
        ("quarantine", "reviewer_id", "codex"),
    ):
        review, envelope, authority, _ = generated[decision]
        mutated = dict(authority)
        mutated[field] = value
        mutated["authority_record_sha256"] = hash_excluding(
            mutated, AUTHORITY_FIELDS, "authority_record_sha256",
        )
        assert not independent_decision_evidence_valid(
            mutated, options, proposal_by_sample,
            atoms_by_ligand, bonds_by_ligand,
        )
        blocked = gate.ingest_review_batch(
            [(review, envelope)], authority_context=formal_context,
            existing_authorities=(mutated,),
        )
        assert (
            not blocked.passed
            and blocked.result_records[0]["reason"]
            == "EXISTING_AUTHORITY_SET_INVALID"
        )
        invalid_existing.append(mutated)
    select_review, _, select_authority, select_result = generated[
        "select_admitted_candidate"
    ]
    replay_review, replay_envelope = synthetic_submission(
        templates[0], options, "select_admitted_candidate", "result-replay",
    )
    replay = gate.ingest_review_batch(
        [(replay_review, replay_envelope)], authority_context=formal_context,
        existing_authorities=(select_authority,),
    )
    assert replay.passed and independent_result_effect_valid(
        replay.result_records[0]
    )
    conflicting_review, conflicting_envelope = synthetic_submission(
        templates[0], options, "quarantine", "result-conflict",
    )
    conflict = gate.ingest_review_batch(
        [(conflicting_review, conflicting_envelope)],
        authority_context=formal_context,
        existing_authorities=(select_authority,),
    )
    assert not conflict.passed and independent_result_effect_valid(
        conflict.result_records[0]
    )
    invalid_context_result = forged_batch.result_records[0]
    assert independent_result_effect_valid(invalid_context_result)
    blocked_result = dict(invalid_context_result)
    blocked_result.update({
        "outcome": "blocked", "reason": "REVIEW_NOT_COMPLETED",
    })
    blocked_result["ingestion_result_sha256"] = hash_excluding(
        blocked_result, RESULT_FIELDS, "ingestion_result_sha256",
    )
    assert independent_result_effect_valid(blocked_result)
    gate.validate_ingestion_result(blocked_result)
    malicious_inputs = (
        (select_result, {"reason": "REVIEW_NOT_COMPLETED"}),
        (select_result, {"reason": "CONFLICTING_REVIEW_REINGESTION"}),
        (blocked_result, {"reason": "PASSED"}),
        (invalid_context_result, {"reason": "BATCH_ATOMICITY_ABORTED"}),
        (replay.result_records[0], {"idempotent_replay": False}),
        (select_result, {"idempotent_replay": True}),
        (
            conflict.result_records[0],
            {"conflicting_existing_authority": False},
        ),
        (
            invalid_context_result,
            {"conflicting_existing_authority": True},
        ),
        (
            generated["quarantine"][3],
            {"authority_disposition": "reviewed_authority_materialized"},
        ),
        (
            select_result,
            {"authority_disposition": "reviewed_quarantine_no_authority"},
        ),
    )
    for source, changes in malicious_inputs:
        malicious = dict(source)
        malicious.update(changes)
        malicious["ingestion_result_sha256"] = hash_excluding(
            malicious, RESULT_FIELDS, "ingestion_result_sha256",
        )
        assert not independent_result_effect_valid(malicious)
        try:
            gate.validate_ingestion_result(malicious)
        except ValueError:
            pass
        else:
            raise AssertionError("malicious_result_reason_effect_accepted")
    check_batch_duplicate_replay_contracts()
    assert len(PUBLIC_REASONS) == len(set(PUBLIC_REASONS)) == 31
    assert REASON_PRECEDENCE == (
        "BATCH_SIZE_INVALID", "SUBMISSION_BATCH_ID_MISMATCH",
        "DUPLICATE_SAMPLE_IN_BATCH",
        "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",
        "INGESTION_AUTHORITY_CONTEXT_INVALID",
        "EXISTING_AUTHORITY_SET_INVALID",
        "EXISTING_AUTHORITY_LINEAGE_MISMATCH",
        "RECORD_SPECIFIC_VALIDATION_REASON",
        "CONFLICTING_REVIEW_REINGESTION", "BATCH_ATOMICITY_ABORTED",
    )

    source_rows = rows((ROOT / OUTPUT / SOURCE_FILE).read_bytes())
    contracts = rows((ROOT / OUTPUT / CONTRACT_FILE).read_bytes())
    decisions = rows((ROOT / OUTPUT / DECISION_FILE).read_bytes())
    readiness = rows((ROOT / OUTPUT / READINESS_FILE).read_bytes())
    failures = rows((ROOT / OUTPUT / FAILURE_FILE).read_bytes())
    manifest = json.loads((ROOT / OUTPUT / MANIFEST_FILE).read_bytes())
    assert len(source_rows) == 13
    for row in source_rows:
        path = Path(row["source_path"])
        assert row["BASE_SHA256"] == EXPECTED_SHA[path]
        assert row["verified"] == "true"
    assert [row["contract_id"] for row in contracts] == [
        f"INGEST_{index:03d}" for index in range(1, 21)
    ]
    assert all(row["fails_closed"] == row["verified"] == "true" for row in contracts)
    contract_by_id = {row["contract_id"]: row for row in contracts}
    assert "Exact14" in contract_by_id["INGEST_004"]["semantic_name"]
    assert "exact-one meaningful batch ID" in contract_by_id[
        "INGEST_011"
    ]["validation_rule"]
    assert "reason" in contract_by_id["INGEST_012"]["required_inputs"]
    assert "review semantics" in contract_by_id["INGEST_013"]["validation_rule"]
    assert "existing authority" in contract_by_id["INGEST_016"]["required_inputs"]
    assert [row["review_decision"] for row in decisions] == [
        "not_reviewed", "select_admitted_candidate",
        "revise_atom_set_and_boundary", "quarantine",
    ]
    assert decisions[0]["future_outcome"] == "blocked"
    assert decisions[1]["future_outcome"] == decisions[2]["future_outcome"] == "passed"
    assert decisions[3]["authority_disposition"] == "reviewed_quarantine_no_authority"
    assert all(
        row[field] == "false" for row in decisions
        for field in (
            "approves_reaction_family", "approves_warhead_rule",
            "approves_SMARTS", "creates_human_gold_label",
            "creates_training_label",
        )
    )
    assert len(readiness) == 11
    assert [row["sample_index_row_id"] for row in readiness] == sorted(
        row["sample_index_row_id"] for row in readiness
    )
    assert all(
        row["ready_for_human_review_submission"] == "true"
        and row["completed_review_record_available"] == "false"
        and row["completed_review_record_sha256"] == ""
        and row["ingestion_envelope_available"] == "false"
        and row["ready_for_review_ingestion_execution"] == "false"
        and row["review_ingestion_completed"] == "false"
        and row["authority_record_available"] == "false"
        and row["complete_warhead_atom_set_authority_available"] == "false"
        and row["exact_one_attachment_boundary_authority_available"] == "false"
        and row["sample_quarantined"] == "false"
        and row["ready_for_training"] == "false"
        for row in readiness
    )
    assert [row["failure_case"] for row in failures] == list(FAILURE_CASES)
    assert len(failures) == 51
    assert len({row["mutation_signature"] for row in failures}) == 51
    assert all(
        row["expected_reason_verified"] == row["fails_closed"]
        == row["verified"] == "true"
        and row["contract_row_count"] == "0"
        and row["decision_effect_row_count"] == "0"
        and row["current11_readiness_row_count"] == "0"
        and row["actual_review_record_count"] == "0"
        and row["actual_ingestion_envelope_count"] == "0"
        and row["actual_ingestion_result_count"] == "0"
        and row["actual_authority_record_count"] == "0"
        and row["SMARTS_ready"] == row["training_ready"] == "false"
        for row in failures
    )
    assert manifest["source_count"] == 13
    assert manifest["ingestion_authority_context_version"] == CONTEXT_VERSION
    assert manifest["ingestion_authority_context_field_count"] == 4
    assert manifest["ingestion_authority_context_fields"] == list(
        CONTEXT_FIELDS
    )
    assert manifest["ingestion_authority_context_source_count"] == 13
    assert manifest["ingestion_authority_context_built_from_formal_base"] is True
    assert manifest["ingestion_authority_context_validation_required"] is True
    assert manifest["external_authority_maps_allowed"] is False
    assert manifest["contract_count"] == 20
    assert manifest["decision_effect_row_count"] == 4
    assert manifest["current11_readiness_row_count"] == 11
    assert manifest["completed_review_record_count"] == 0
    assert manifest["ingestion_envelope_count"] == 0
    assert manifest["ingestion_result_count"] == 0
    assert manifest["authority_record_count"] == 0
    assert manifest["completed_review_package_identity_field_count"] == 14
    assert manifest["completed_review_package_identity_fields"] == list(
        IDENTITY_FIELDS
    )
    assert manifest["single_submission_batch_id_required"] is True
    assert manifest["existing_authority_validation_required"] is True
    assert manifest["existing_authority_unique_sample_required"] is True
    assert manifest["existing_authority_package_lineage_required"] is True
    assert manifest["existing_authority_decision_evidence_required"] is True
    assert manifest["ingestion_result_reason_effect_contract_version"] == (
        RESULT_EFFECT_VERSION
    )
    assert manifest["ingestion_result_reason_effect_invariants_frozen"] is True
    assert manifest["ingestion_result_reason_codes"] == list(PUBLIC_REASONS)
    assert manifest["ingestion_result_reason_code_count"] == 31
    assert manifest["ingestion_failure_reason_precedence"] == list(
        REASON_PRECEDENCE
    )
    assert manifest["public_reason_vocabulary_frozen"] is True
    assert manifest["deterministic_failure_precedence"] is True
    assert manifest["failure_mutation_count"] == 51
    assert manifest["ready_for_review_ingestion_interface_implementation"] is True
    assert manifest["ready_for_review_ingestion_execution"] is False
    assert manifest["supersession_available_v1"] is False
    assert manifest["batch_atomicity_required"] is True
    assert manifest["exact_replay_idempotent"] is True
    assert manifest["conflicting_reingestion_forbidden"] is True
    assert manifest["canonical_masks"] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert MANIFEST_FILE not in manifest["output_sha256"]
    for name, expected in manifest["output_sha256"].items():
        assert digest((ROOT / OUTPUT / name).read_bytes()) == expected
    assert all((ROOT / path).is_file() and not (ROOT / path).is_symlink() for path in EXACT10)
    assert {
        path.name for path in (ROOT / OUTPUT).iterdir()
    } == set(OUTPUT_FILES)

    with tempfile.TemporaryDirectory(prefix="covapie-checker-") as temporary:
        workspace = Path(temporary) / "workspace"
        workspace.mkdir()
        report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
            ROOT, workspace, base_commit=BASE, formal_commit_subject=SUBJECT,
            exact_paths=EXACT10,
        )
        assert report.cleanup_verified and report.exact_path_count == 10
        assert tuple(
            state.lifecycle for state in (
                report.pre_commit, report.detached_candidate_post_commit,
                report.formal_main_post_commit_unpushed,
                report.formal_main_post_push,
            )
        ) == lifecycle.LIFECYCLES
        candidate = report.candidate_commit
    print("checker=passed")
    print("sources=13 contracts=20 decisions=4 samples=11")
    print(
        "identity_fields=14 authority_context_fields=4 immutable_context=true"
    )
    print("public_reasons=31 reason_precedence=10 result_effects=true")
    print("completed_reviews=0 envelopes=0 results=0 authorities=0")
    print("interface_ready=true execution_ready=false")
    print("failure_mutations=51 all_fail_closed=true")
    print(f"current_lifecycle={current}")
    print(
        "hermetic_lifecycle="
        "pre_commit,detached_candidate_post_commit,"
        "formal_main_post_commit_unpushed,formal_main_post_push"
    )
    print(f"candidate_commit={candidate}")
    print(
        "recommended_next_step="
        "implement_covapie_current11_warhead_atom_set_and_attachment_"
        "boundary_review_ingestion_interface_v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
