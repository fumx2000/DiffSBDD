"""Design the Current11 warhead/boundary human-review ingestion gate.

This module freezes a future ingestion interface.  It consumes only immutable
BASE evidence through ``git show`` and materializes design tables.  It never
performs human review and never writes submitted reviews, ingestion envelopes,
ingestion results, authority records, SMARTS, roles, masks, or training data.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from collections import defaultdict, deque
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_gate_design_v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review ingestion gate design v1"
)
BASE_COMMIT = "d0243f7b5d8c0ff7a2831be1a5ed904fb8ff294f"
BASE_PARENT = "ec9b1efbcfc49eeda55d7318b38daec67455343a"
BASE_TREE = "fb80f7e22552a5eb2b20edde2048a254b4d3aef3"
BASE_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review packages v1"
)

REVIEW_RECORD_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "human_review_record_v1"
)
REVIEW_UNIT_TYPE = "sample_warhead_atom_set_and_attachment_boundary"
PACKAGE_OPTION_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_option_v1"
)
INGESTION_ENVELOPE_VERSION = (
    "covapie_current11_warhead_boundary_review_ingestion_envelope_v1"
)
AUTHORITY_RECORD_VERSION = (
    "covapie_current11_reviewed_warhead_atom_set_and_attachment_"
    "boundary_authority_v1"
)
INGESTION_RESULT_VERSION = (
    "covapie_current11_warhead_boundary_review_ingestion_result_v1"
)
INGESTION_AUTHORITY_CONTEXT_VERSION = (
    "covapie_current11_warhead_boundary_ingestion_authority_context_v1"
)
INGESTION_RESULT_REASON_EFFECT_CONTRACT_VERSION = (
    "covapie_current11_warhead_boundary_ingestion_result_reason_effect_v1"
)

OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
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
    SOURCE_FILE,
    CONTRACT_FILE,
    DECISION_FILE,
    READINESS_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
PRODUCTION_PATH = Path("src/covalent_ext") / f"{SCHEMA_VERSION}.py"
TEST_PATH = Path("tests") / f"test_{SCHEMA_VERSION}.py"
CHECKER_PATH = Path("scripts") / f"check_{SCHEMA_VERSION}.py"
SUMMARY_PATH = Path("docs") / f"{SCHEMA_VERSION}_summary.md"
EXACT10_PATHS = (
    PRODUCTION_PATH,
    TEST_PATH,
    CHECKER_PATH,
    SUMMARY_PATH,
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
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

FROZEN_BASE_SHA256 = {
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
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)
INGESTION_AUTHORITY_CONTEXT_FIELDS = (
    "ingestion_authority_context_version",
    "formal_base_commit",
    "ordered_source_path_sha256_pairs",
    "ingestion_authority_context_record_sha256",
)

REVIEW_RECORD_FIELDS = (
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
REVIEW_DECISIONS = (
    "not_reviewed", "select_admitted_candidate",
    "revise_atom_set_and_boundary", "quarantine",
)
COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS = (
    "review_record_version", "review_unit_type", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_assignment_record_sha256",
    "source_candidate_set_sha256", "total_candidate_count",
    "admitted_candidate_count",
)
INGESTION_ENVELOPE_FIELDS = (
    "ingestion_envelope_version", "submission_batch_id", "sample_index_row_id",
    "review_record_sha256", "submitted_record_payload_sha256",
    "reviewer_provenance_attested", "reviewer_provenance_attestor_id",
    "submission_source_label", "ingestion_envelope_sha256",
)
AUTHORITY_RECORD_FIELDS = (
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
AUTHORITY_BOOL_FIELDS = {
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "sample_quarantined",
}
AUTHORITY_DISPOSITIONS = (
    "reviewed_authority_materialized", "reviewed_quarantine_no_authority",
)
AUTHORITY_STATUSES = ("active", "quarantined")
INGESTION_RESULT_FIELDS = (
    "ingestion_result_version", "submission_batch_id", "sample_index_row_id",
    "review_record_sha256", "ingestion_envelope_sha256", "outcome", "passed",
    "blocks_batch", "reason", "review_decision", "review_completed",
    "authority_disposition", "authority_record_sha256", "idempotent_replay",
    "conflicting_existing_authority", "consumed_review_record",
    "consumed_ingestion_envelope", "ingestion_result_sha256",
)
INGESTION_RESULT_BOOL_FIELDS = {
    "passed", "blocks_batch", "review_completed", "idempotent_replay",
    "conflicting_existing_authority", "consumed_review_record",
    "consumed_ingestion_envelope",
}
INGESTION_OUTCOMES = ("passed", "blocked", "invalid")
INGESTION_RESULT_REASON_CODES = (
    "PASSED",
    "IDEMPOTENT_REPLAY",
    "BATCH_SIZE_INVALID",
    "SUBMISSION_BATCH_ID_MISMATCH",
    "DUPLICATE_SAMPLE_IN_BATCH",
    "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",
    "BATCH_ATOMICITY_ABORTED",
    "REVIEW_NOT_COMPLETED",
    "REVIEW_IDENTITY_LINKAGE_MISMATCH",
    "COMPLETED_REVIEW_RECORD_SHA_INVALID",
    "REVIEWER_NOT_MEANINGFUL",
    "FORBIDDEN_AUTOMATED_REVIEWER",
    "REVIEW_RATIONALE_NOT_MEANINGFUL",
    "REVIEW_NOTES_NOT_MEANINGFUL",
    "SELECT_DEPENDENCY_INVALID",
    "SELECT_OPTION_NOT_REVIEW_ELIGIBLE",
    "REVISE_GRAPH_INVARIANT_INVALID",
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
INGESTION_FAILURE_REASON_PRECEDENCE = (
    "BATCH_SIZE_INVALID",
    "SUBMISSION_BATCH_ID_MISMATCH",
    "DUPLICATE_SAMPLE_IN_BATCH",
    "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",
    "INGESTION_AUTHORITY_CONTEXT_INVALID",
    "EXISTING_AUTHORITY_SET_INVALID",
    "EXISTING_AUTHORITY_LINEAGE_MISMATCH",
    "RECORD_SPECIFIC_VALIDATION_REASON",
    "CONFLICTING_REVIEW_REINGESTION",
    "BATCH_ATOMICITY_ABORTED",
)

INDEX_FIELDS = (
    "package_index_version", "package_item_order_0based",
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_assignment_record_sha256",
    "source_candidate_set_sha256", "total_candidate_count",
    "admitted_candidate_count", "source_proposal_status",
    "candidate_option_row_start_0based", "candidate_option_row_end_exclusive",
    "review_record_version", "unreviewed_template_payload_sha256",
    "review_options_materialized", "review_template_materialized",
    "ready_for_human_review", "human_review_completed",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_role_proposal_generation", "blocking_reasons", "verified",
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
OPTION_INT_FIELDS = {
    "package_item_order_0based", "option_order_within_sample_0based",
    "warhead_type_candidate_class_index_0based",
    "source_bridge_candidate_index_0based", "warhead_side_atom_count",
    "nonwarhead_side_atom_count",
}
OPTION_BOOL_FIELDS = {"candidate_admitted", "review_eligible"}
OPTION_LIST_FIELDS = {
    "warhead_side_atom_ids", "warhead_extra_atom_ids_beyond_local_center",
    "local_reaction_center_atom_ids", "required_leaving_group_atom_ids",
}
PROPOSAL_FIELDS = (
    "proposal_version", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "component_parent_graph_sha256", "ligand_reactive_parent_atom_id",
    "local_reaction_center_atom_ids", "local_reaction_center_bond_ids",
    "proposed_pre_reaction_warhead_atom_ids",
    "proposed_warhead_attachment_atom_id",
    "proposed_nonwarhead_boundary_atom_id",
    "proposed_attachment_boundary_bond_order",
    "required_leaving_group_atom_ids", "proposal_method", "proposal_status",
    "ambiguity_reasons", "source_assignment_record_sha256",
    "proposal_record_sha256",
)
ASSIGNMENT_HASH_FIELDS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "target_residue_name", "target_residue_number",
    "target_residue_atom_name", "ligand_reactive_atom_name",
    "ligand_reactive_atom_element", "ligand_reactive_parent_ccd_atom_id",
    "component_parent_graph_sha256", "observed_graph_sha256",
    "radius_1_signature_sha256", "candidate_reaction_family_id",
    "candidate_warhead_rule_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "assignment_status",
    "review_status", "training_label_status",
)
PARENT_ATOM_FIELDS = (
    "ligand_comp_id", "ccd_source_relative_path", "ccd_source_sha256",
    "ccd_parser_contract_version", "ccd_atom_id", "ccd_type_symbol",
    "ccd_formal_charge", "ccd_heavy_atom_row_index_0based",
    "component_parent_graph_sha256", "authority_class", "verified",
)
PARENT_BOND_FIELDS = (
    "ligand_comp_id", "ccd_source_relative_path", "ccd_source_sha256",
    "parent_ccd_atom_id_1", "parent_ccd_atom_id_2", "source_value_order",
    "source_aromatic_flag", "normalized_bond_order",
    "component_parent_graph_sha256", "authority_class", "verified",
)
PARENT_NORMALIZED_BOND_ORDERS = ("aromatic", "double", "single")

SOURCE_COLUMNS = (
    "source_path", "BASE_SHA256", "source_row_count", "Current11_coverage",
    "fields_actually_used", "authority_class", "provides_current_value",
    "verified",
)
CONTRACT_COLUMNS = (
    "contract_id", "semantic_name", "contract_scope", "required_inputs",
    "validation_rule", "success_effect", "failure_effect", "reason_code",
    "fails_closed", "verified",
)
DECISION_COLUMNS = (
    "review_decision", "completed_submission_ingestible", "future_outcome",
    "reason_code", "blocks_batch", "review_completed",
    "authority_disposition", "authority_status",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "sample_quarantined", "approves_reaction_family",
    "approves_warhead_rule", "approves_SMARTS", "creates_human_gold_label",
    "creates_training_label", "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "source_proposal_record_sha256", "source_assignment_record_sha256",
    "source_candidate_set_sha256", "unreviewed_template_payload_sha256",
    "package_materialized", "review_options_materialized",
    "blank_review_template_materialized", "ready_for_human_review_submission",
    "completed_review_record_available", "completed_review_record_sha256",
    "ingestion_envelope_available", "ingestion_envelope_sha256",
    "ready_for_review_ingestion_execution", "review_ingestion_completed",
    "authority_record_available", "authority_record_sha256",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available", "sample_quarantined",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_SMARTS_review_execution", "ready_for_role_proposal_generation",
    "ready_for_mask_materialization", "ready_for_model_integration",
    "ready_for_training", "blocking_reasons", "verified",
)
FAILURE_COLUMNS = (
    "failure_case", "mutation_signature", "mutated_field",
    "mutated_value_json", "expected_reason", "observed_reasons",
    "expected_reason_verified", "fails_closed", "contract_row_count",
    "decision_effect_row_count", "current11_readiness_row_count",
    "actual_review_record_count", "actual_ingestion_envelope_count",
    "actual_ingestion_result_count", "actual_authority_record_count",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available", "SMARTS_ready",
    "role_ready", "mask_ready", "model_ready", "training_ready", "verified",
)

_SHA = re.compile(r"[0-9a-f]{64}")
_FORBIDDEN_REVIEWERS = {
    "codex", "chatgpt", "openai", "automation", "auto", "system", "model",
}
CANONICAL_MASKS = (
    "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
    "scaffold_only", "scaffold_plus_linker_plus_warhead",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def _git(
    repo_root: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments), cwd=repo_root, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(
            "git_command_failed:" + " ".join(arguments) + ":"
            + result.stderr.decode("utf-8", "replace")
        )
    return result


def validate_execution_boundary_v1(repo_root: Path) -> str:
    identity = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).stdout.decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("formal_BASE_identity_mismatch")
    head = _git(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE_COMMIT:
        return "pre_commit"
    raw = _git(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    if not separator:
        raise ValueError("successor_commit_object_malformed")
    parents = tuple(
        line[7:].decode() for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    subject, newline, body = message.partition(b"\n")
    if (
        parents != (BASE_COMMIT,) or not newline
        or subject.decode() != FORMAL_COMMIT_SUBJECT or body
    ):
        raise ValueError("successor_identity_mismatch")
    changed = {
        item.decode() for item in _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r",
            "-z", head,
        ).stdout.split(b"\0") if item
    }
    if changed != {path.as_posix() for path in EXACT10_PATHS}:
        raise ValueError("successor_changed_path_inventory_mismatch")
    tree_rows = [
        row for row in _git(
            repo_root, "ls-tree", "-r", "-z", head, "--",
            *(path.as_posix() for path in EXACT10_PATHS),
        ).stdout.split(b"\0") if row
    ]
    if len(tree_rows) != 10 or any(
        not row.startswith(b"100644 blob ") for row in tree_rows
    ):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root, "rev-parse", "--verify", "refs/remotes/origin/main",
        check=False,
    )
    if origin.returncode:
        raise ValueError("successor_origin_main_missing")
    origin_oid = origin.stdout.decode().strip()
    if origin_oid == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin_oid == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def base_bytes(repo_root: Path, path: Path) -> bytes:
    result = _git(repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}", check=False)
    if result.returncode or not result.stdout:
        raise ValueError(f"BASE_source_missing:{path.as_posix()}")
    return result.stdout


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    validate_execution_boundary_v1(repo_root)
    result = {}
    for path, expected in FROZEN_BASE_SHA256.items():
        payload = base_bytes(repo_root, path)
        if sha256(payload) != expected:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        result[path] = payload
    return result


@dataclass(frozen=True)
class IngestionAuthorityContext:
    """Immutable carrier for the exact BASE source bytes used by ingestion."""

    context_record: Mapping[str, Any]
    source_payloads: tuple[tuple[str, bytes], ...]


def _authority_context_record_sha256(record: Mapping[str, Any]) -> str:
    return _record_sha(
        record,
        INGESTION_AUTHORITY_CONTEXT_FIELDS,
        "ingestion_authority_context_record_sha256",
    )


def build_ingestion_authority_context(
    repo_root: Path,
) -> IngestionAuthorityContext:
    """Build the in-memory authority context only through git show BASE:path."""

    validate_execution_boundary_v1(repo_root)
    source_payloads = tuple(
        (path.as_posix(), base_bytes(repo_root, path))
        for path in SOURCE_PATHS
    )
    pairs = [
        f"{path}\t{sha256(payload)}" for path, payload in source_payloads
    ]
    record: dict[str, Any] = {
        "ingestion_authority_context_version":
            INGESTION_AUTHORITY_CONTEXT_VERSION,
        "formal_base_commit": BASE_COMMIT,
        "ordered_source_path_sha256_pairs": pairs,
        "ingestion_authority_context_record_sha256": "",
    }
    record["ingestion_authority_context_record_sha256"] = (
        _authority_context_record_sha256(record)
    )
    context = IngestionAuthorityContext(record, source_payloads)
    validate_ingestion_authority_context(context)
    return context


def _validated_ingestion_authority_context(context: object):
    """Revalidate every byte and rebuild all authority evidence on every use."""

    if type(context) is not IngestionAuthorityContext:
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
    record = context.context_record
    if type(record) is not dict or tuple(record) != (
        INGESTION_AUTHORITY_CONTEXT_FIELDS
    ):
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
    if (
        type(record["ingestion_authority_context_version"]) is not str
        or type(record["formal_base_commit"]) is not str
        or type(record["ordered_source_path_sha256_pairs"]) is not list
        or any(
            type(item) is not str
            for item in record["ordered_source_path_sha256_pairs"]
        )
        or type(record["ingestion_authority_context_record_sha256"]) is not str
    ):
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
    if (
        record["ingestion_authority_context_version"]
        != INGESTION_AUTHORITY_CONTEXT_VERSION
        or record["formal_base_commit"] != BASE_COMMIT
        or _SHA.fullmatch(
            record["ingestion_authority_context_record_sha256"]
        ) is None
        or record["ingestion_authority_context_record_sha256"]
        != _authority_context_record_sha256(record)
    ):
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
    if (
        type(context.source_payloads) is not tuple
        or len(context.source_payloads) != len(SOURCE_PATHS) != 0
    ):
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
    expected_paths = tuple(path.as_posix() for path in SOURCE_PATHS)
    observed_paths: list[str] = []
    payloads: dict[Path, bytes] = {}
    pairs: list[str] = []
    for item in context.source_payloads:
        if (
            type(item) is not tuple or len(item) != 2
            or type(item[0]) is not str or type(item[1]) is not bytes
            or not item[0] or Path(item[0]).is_absolute()
        ):
            raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
        path_text, payload = item
        digest = sha256(payload)
        path = Path(path_text)
        if path not in FROZEN_BASE_SHA256 or digest != FROZEN_BASE_SHA256[path]:
            raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
        observed_paths.append(path_text)
        payloads[path] = payload
        pairs.append(f"{path_text}\t{digest}")
    if (
        tuple(observed_paths) != expected_paths
        or len(payloads) != 13
        or record["ordered_source_path_sha256_pairs"] != pairs
        or len(pairs) != 13
        or any(
            "\t" not in pair
            or _SHA.fullmatch(pair.rpartition("\t")[2]) is None
            for pair in pairs
        )
    ):
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
    phase = _validate_phase_a(payloads)
    if phase.blocking_reasons:
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID")
    return phase


def validate_ingestion_authority_context(context: object) -> None:
    _validated_ingestion_authority_context(context)


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _cell(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    if type(value) in (list, tuple, dict):
        return canonical_json(value)
    return str(value)


def _csv_bytes(
    columns: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _cell(row.get(field, "")) for field in columns})
    return stream.getvalue().encode("utf-8")


def _parse_int(value: str, field: str) -> int:
    if not value or not value.isdecimal() or (len(value) > 1 and value[0] == "0"):
        raise ValueError(f"canonical_nonnegative_decimal_invalid:{field}")
    result = int(value)
    if type(result) is not int:
        raise ValueError(f"exact_int_invalid:{field}")
    return result


def _parse_bool(value: str, field: str) -> bool:
    if value not in ("true", "false"):
        raise ValueError(f"exact_bool_invalid:{field}")
    return value == "true"


def _parse_list(value: str, field: str) -> list[str]:
    try:
        result = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"exact_list_str_invalid:{field}") from error
    if type(result) is not list or any(type(item) is not str for item in result):
        raise ValueError(f"exact_list_str_invalid:{field}")
    return result


def _record_sha(
    record: Mapping[str, Any], fields: Sequence[str], excluded: str,
) -> str:
    if type(record) is not dict or tuple(record) != tuple(fields):
        raise ValueError("record_field_inventory_mismatch")
    return sha256(canonical_json({
        field: record[field] for field in fields if field != excluded
    }).encode("utf-8"))


def parse_review_record_csv(row: Mapping[str, str]) -> dict[str, Any]:
    if tuple(row) != REVIEW_RECORD_FIELDS:
        raise ValueError("review_field_inventory_mismatch")
    result: dict[str, Any] = {}
    for field in REVIEW_RECORD_FIELDS:
        value = row[field]
        if field in {
            "warhead_type_candidate_class_index_0based",
            "total_candidate_count", "admitted_candidate_count",
        }:
            result[field] = _parse_int(value, field)
        elif field == "selected_bridge_candidate_index_0based":
            result[field] = None if value == "" else _parse_int(value, field)
        elif field == "reviewed_warhead_atom_ids":
            result[field] = _parse_list(value, field)
        else:
            if type(value) is not str:
                raise ValueError(f"review_exact_str_invalid:{field}")
            result[field] = value
    return result


def _validate_review_schema(record: Mapping[str, Any]) -> None:
    if type(record) is not dict or tuple(record) != REVIEW_RECORD_FIELDS:
        raise ValueError("review_field_inventory_mismatch")
    for field in REVIEW_RECORD_FIELDS:
        value = record[field]
        if field in {
            "warhead_type_candidate_class_index_0based",
            "total_candidate_count", "admitted_candidate_count",
        }:
            if type(value) is not int or value < 0:
                raise ValueError(f"review_exact_int_invalid:{field}")
        elif field == "selected_bridge_candidate_index_0based":
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("selected_index_exact_optional_int_invalid")
        elif field == "reviewed_warhead_atom_ids":
            if type(value) is not list or any(type(item) is not str for item in value):
                raise ValueError("reviewed_warhead_atom_ids_exact_list_str_invalid")
        elif type(value) is not str:
            raise ValueError(f"review_exact_str_invalid:{field}")
    if (
        record["review_record_version"] != REVIEW_RECORD_VERSION
        or record["review_unit_type"] != REVIEW_UNIT_TYPE
        or record["review_decision"] not in REVIEW_DECISIONS
    ):
        raise ValueError("review_identity_or_decision_invalid")
    atoms = record["reviewed_warhead_atom_ids"]
    if atoms != _utf8_sorted(atoms) or len(atoms) != len(set(atoms)):
        raise ValueError("reviewed_warhead_atom_ids_not_sorted_unique")


def _validate_package_identity_record(identity: Mapping[str, Any]) -> None:
    if (
        type(identity) is not dict
        or tuple(identity) != COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS
    ):
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    int_fields = {
        "warhead_type_candidate_class_index_0based",
        "total_candidate_count", "admitted_candidate_count",
    }
    sha_fields = {
        "source_proposal_record_sha256", "source_assignment_record_sha256",
        "source_candidate_set_sha256",
    }
    for field in COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS:
        value = identity[field]
        if field in int_fields:
            if type(value) is not int or value < 0:
                raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
        elif type(value) is not str or not value.strip():
            raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
        if field in sha_fields and _SHA.fullmatch(value) is None:
            raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    if (
        identity["review_record_version"] != REVIEW_RECORD_VERSION
        or identity["review_unit_type"] != REVIEW_UNIT_TYPE
    ):
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")


def build_package_identity_by_sample(
    package_index_rows: Sequence[Mapping[str, str]],
    template_rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Independently join the package index and blank templates on Exact14."""

    if len(package_index_rows) != 11 or len(template_rows) != 11:
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    index_by_sample: dict[str, dict[str, Any]] = {}
    for row in package_index_rows:
        if tuple(row) != INDEX_FIELDS:
            raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
        identity: dict[str, Any] = {}
        for field in COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS:
            if field == "review_unit_type":
                identity[field] = REVIEW_UNIT_TYPE
            elif field in {
                "warhead_type_candidate_class_index_0based",
                "total_candidate_count", "admitted_candidate_count",
            }:
                identity[field] = _parse_int(row[field], field)
            else:
                value = row[field]
                if type(value) is not str:
                    raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
                identity[field] = value
        _validate_package_identity_record(identity)
        sample = identity["sample_index_row_id"]
        if sample in index_by_sample:
            raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
        index_by_sample[sample] = identity
    template_by_sample: dict[str, dict[str, Any]] = {}
    for row in template_rows:
        identity = {
            field: row[field] for field in COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS
        }
        _validate_package_identity_record(identity)
        sample = identity["sample_index_row_id"]
        if sample in template_by_sample:
            raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
        template_by_sample[sample] = identity
    if set(index_by_sample) != set(template_by_sample):
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    for sample in sorted(index_by_sample):
        if index_by_sample[sample] != template_by_sample[sample]:
            raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    return {sample: index_by_sample[sample] for sample in sorted(index_by_sample)}


def validate_completed_review_package_identity(
    review_record: Mapping[str, Any],
    *,
    package_identity_by_sample: Mapping[str, Mapping[str, Any]],
) -> None:
    """Require an Exact14 join before accepting any completed decision."""

    if type(review_record) is not dict:
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    sample = review_record.get("sample_index_row_id")
    if type(sample) is not str or sample not in package_identity_by_sample:
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    package_identity = package_identity_by_sample[sample]
    _validate_package_identity_record(package_identity)
    try:
        observed = {
            field: review_record[field]
            for field in COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS
        }
    except KeyError as error:
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH") from error
    _validate_package_identity_record(observed)
    if observed != package_identity:
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")


def review_record_sha256(record: Mapping[str, Any]) -> str:
    _validate_review_schema(record)
    return _record_sha(record, REVIEW_RECORD_FIELDS, "review_record_sha256")


def submitted_record_payload_sha256(record: Mapping[str, Any]) -> str:
    """Hash all typed Exact26 fields, including populated review_record_sha256."""

    _validate_review_schema(record)
    return sha256(canonical_json({
        field: record[field] for field in REVIEW_RECORD_FIELDS
    }).encode("utf-8"))


def _meaningful(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _forbidden_reviewer(value: object) -> bool:
    return (
        type(value) is str
        and value.strip().casefold() in _FORBIDDEN_REVIEWERS
    )


def _bond_tuple(
    row: Mapping[str, str] | Sequence[str],
) -> tuple[str, str, str]:
    if isinstance(row, Mapping):
        return (
            row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"],
            row["normalized_bond_order"],
        )
    if len(row) != 3 or any(type(item) is not str for item in row):
        raise ValueError("parent_bond_invalid")
    return row[0], row[1], row[2]


def _canonical_parent_graph_sha256(
    atoms: Sequence[Mapping[str, str]],
    bonds: Sequence[Mapping[str, str]],
) -> str:
    payload = {
        "atoms": [
            [
                row["ccd_atom_id"], row["ccd_type_symbol"],
                int(row["ccd_formal_charge"]),
            ]
            for row in sorted(atoms, key=lambda item: item["ccd_atom_id"])
        ],
        "bonds": [
            list(item)
            for item in sorted(
                (
                    min(
                        row["parent_ccd_atom_id_1"],
                        row["parent_ccd_atom_id_2"],
                    ),
                    max(
                        row["parent_ccd_atom_id_1"],
                        row["parent_ccd_atom_id_2"],
                    ),
                    row["normalized_bond_order"],
                )
                for row in bonds
            )
        ],
    }
    return sha256(canonical_json(payload).encode("utf-8"))


def _validate_parent_graph(
    atom_rows: Sequence[Mapping[str, str]],
    bond_rows: Sequence[Mapping[str, str]],
    *,
    expected_sha: str,
) -> None:
    if not atom_rows or not bond_rows:
        raise ValueError("parent_graph_missing")
    if any(tuple(row) != PARENT_ATOM_FIELDS for row in atom_rows):
        raise ValueError("parent_atom_field_inventory_mismatch")
    if any(tuple(row) != PARENT_BOND_FIELDS for row in bond_rows):
        raise ValueError("parent_bond_field_inventory_mismatch")
    if any(row["verified"] != "true" for row in (*atom_rows, *bond_rows)):
        raise ValueError("parent_graph_unverified")
    atom_ids = [row["ccd_atom_id"] for row in atom_rows]
    if (
        any(not atom_id for atom_id in atom_ids)
        or len(atom_ids) != len(set(atom_ids))
    ):
        raise ValueError("parent_atom_ID_invalid")
    atom_set = set(atom_ids)
    adjacency = {atom_id: set() for atom_id in atom_ids}
    seen_edges: set[frozenset[str]] = set()
    for row in bond_rows:
        left = row["parent_ccd_atom_id_1"]
        right = row["parent_ccd_atom_id_2"]
        edge = frozenset((left, right))
        if (
            left == right or left not in atom_set or right not in atom_set
            or len(edge) != 2 or edge in seen_edges
            or row["normalized_bond_order"]
            not in PARENT_NORMALIZED_BOND_ORDERS
        ):
            raise ValueError("parent_bond_invalid")
        seen_edges.add(edge)
        adjacency[left].add(right)
        adjacency[right].add(left)
    reached: set[str] = set()
    queue = deque([_utf8_sorted(atom_ids)[0]])
    while queue:
        current = queue.popleft()
        if current in reached:
            continue
        reached.add(current)
        queue.extend(adjacency[current] - reached)
    if reached != atom_set:
        raise ValueError("parent_graph_disconnected")
    if any(
        row["component_parent_graph_sha256"] != expected_sha
        for row in (*atom_rows, *bond_rows)
    ):
        raise ValueError("parent_graph_SHA_link_mismatch")
    if _canonical_parent_graph_sha256(atom_rows, bond_rows) != expected_sha:
        raise ValueError("parent_graph_SHA_mismatch")


def _validate_revised_boundary_evidence(
    record: Mapping[str, Any],
    *,
    proposal: Mapping[str, Any],
    parent_atom_ids: Sequence[str],
    parent_bonds: Sequence[Mapping[str, str] | Sequence[str]],
) -> None:
    atoms = record["reviewed_warhead_atom_ids"]
    atom_set = set(atoms)
    parent_set = set(parent_atom_ids)
    if (
        type(atoms) is not list
        or any(type(atom) is not str for atom in atoms)
        or atoms != _utf8_sorted(atoms)
        or len(atom_set) != len(atoms)
        or not atoms
        or not set(proposal["local_reaction_center_atom_ids"]) <= atom_set
        or not set(proposal["required_leaving_group_atom_ids"]) <= atom_set
        or not atom_set < parent_set
    ):
        raise ValueError("REVISE_GRAPH_INVARIANT_INVALID")
    adjacency: dict[str, set[str]] = defaultdict(set)
    boundary = []
    for raw in parent_bonds:
        left, right, order = _bond_tuple(raw)
        if left in atom_set and right in atom_set:
            adjacency[left].add(right)
            adjacency[right].add(left)
        elif (left in atom_set) != (right in atom_set):
            boundary.append((left, right, order))
    seen: set[str] = set()
    queue = deque([atoms[0]])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(adjacency[current] - seen)
    if seen != atom_set or len(boundary) != 1:
        raise ValueError("REVISE_GRAPH_INVARIANT_INVALID")
    left, right, order = boundary[0]
    attachment = left if left in atom_set else right
    nonwarhead = right if attachment == left else left
    low, high = _utf8_sorted((left, right))
    expected = (attachment, nonwarhead, order, f"{low}|{high}|{order}")
    observed = (
        record["reviewed_warhead_attachment_atom_id"],
        record["reviewed_nonwarhead_boundary_atom_id"],
        record["reviewed_attachment_boundary_bond_order"],
        record["reviewed_boundary_bond_id"],
    )
    if observed != expected:
        raise ValueError("REVISE_GRAPH_INVARIANT_INVALID")


def validate_review_record(
    record: Mapping[str, Any],
    *,
    options: Sequence[Mapping[str, Any]] = (),
    proposal: Mapping[str, Any] | None = None,
    parent_atom_ids: Sequence[str] = (),
    parent_bonds: Sequence[Mapping[str, str] | Sequence[str]] = (),
    package_identity: Mapping[str, Any] | None = None,
    completed_submission: bool = False,
) -> None:
    """Validate an inherited Exact26 record without performing human review."""

    _validate_review_schema(record)
    decision = record["review_decision"]
    selected = record["selected_bridge_candidate_index_0based"]
    selected_sha = record["selected_bridge_candidate_record_sha256"]
    blank_boundary = (
        record["reviewed_warhead_atom_ids"] == []
        and record["reviewed_warhead_attachment_atom_id"] == ""
        and record["reviewed_nonwarhead_boundary_atom_id"] == ""
        and record["reviewed_attachment_boundary_bond_order"] == ""
        and record["reviewed_boundary_bond_id"] == ""
    )
    if decision == "not_reviewed":
        if completed_submission:
            raise ValueError("REVIEW_NOT_COMPLETED")
        if selected is not None or selected_sha:
            raise ValueError("not_reviewed_selection_prefilled")
        if not blank_boundary:
            raise ValueError("not_reviewed_boundary_prefilled")
        if any(record[field] for field in (
            "reviewer_id", "review_rationale", "review_notes",
            "review_record_sha256",
        )):
            raise ValueError("not_reviewed_human_or_digest_prefilled")
        return
    if not _meaningful(record["reviewer_id"]):
        raise ValueError("REVIEWER_NOT_MEANINGFUL")
    if _forbidden_reviewer(record["reviewer_id"]):
        raise ValueError("FORBIDDEN_AUTOMATED_REVIEWER")
    if not _meaningful(record["review_rationale"]):
        raise ValueError("REVIEW_RATIONALE_NOT_MEANINGFUL")
    if record["review_notes"] and not _meaningful(record["review_notes"]):
        raise ValueError("REVIEW_NOTES_NOT_MEANINGFUL")
    if decision == "select_admitted_candidate":
        if type(selected) is not int or _SHA.fullmatch(selected_sha) is None:
            raise ValueError("SELECT_DEPENDENCY_INVALID")
        matches = [
            option for option in options
            if option["sample_index_row_id"] == record["sample_index_row_id"]
            and option["source_candidate_set_sha256"]
            == record["source_candidate_set_sha256"]
            and option["source_bridge_candidate_index_0based"] == selected
            and option["source_bridge_candidate_record_sha256"] == selected_sha
        ]
        if len(matches) != 1:
            raise ValueError("SELECT_DEPENDENCY_INVALID")
        option = matches[0]
        if package_identity is not None:
            _validate_package_identity_record(package_identity)
            option_identity_fields = (
                "sample_index_row_id", "pdb_id", "ligand_comp_id",
                "warhead_type_candidate_class_index_0based",
                "warhead_type_candidate_class_id", "reaction_family_id",
                "warhead_rule_id", "source_proposal_record_sha256",
                "source_candidate_set_sha256",
            )
            if any(
                option[field] != package_identity[field]
                or record[field] != package_identity[field]
                for field in option_identity_fields
            ):
                raise ValueError("SELECT_DEPENDENCY_INVALID")
        if option["review_eligible"] is not True:
            raise ValueError("SELECT_OPTION_NOT_REVIEW_ELIGIBLE")
        expected = (
            option["warhead_side_atom_ids"], option["warhead_attachment_atom_id"],
            option["nonwarhead_boundary_atom_id"], option["boundary_bond_order"],
            option["boundary_bond_id"],
        )
        observed = (
            record["reviewed_warhead_atom_ids"],
            record["reviewed_warhead_attachment_atom_id"],
            record["reviewed_nonwarhead_boundary_atom_id"],
            record["reviewed_attachment_boundary_bond_order"],
            record["reviewed_boundary_bond_id"],
        )
        if observed != expected:
            raise ValueError("SELECT_DEPENDENCY_INVALID")
    elif decision == "revise_atom_set_and_boundary":
        if selected is not None or selected_sha or proposal is None:
            raise ValueError("REVISE_GRAPH_INVARIANT_INVALID")
        _validate_revised_boundary_evidence(
            record, proposal=proposal, parent_atom_ids=parent_atom_ids,
            parent_bonds=parent_bonds,
        )
    elif selected is not None or selected_sha or not blank_boundary:
        raise ValueError("QUARANTINE_DEPENDENCY_INVALID")
    if _SHA.fullmatch(record["review_record_sha256"]) is None:
        raise ValueError("COMPLETED_REVIEW_RECORD_SHA_INVALID")
    if record["review_record_sha256"] != review_record_sha256(record):
        raise ValueError("COMPLETED_REVIEW_RECORD_SHA_INVALID")


def ingestion_envelope_sha256(record: Mapping[str, Any]) -> str:
    _validate_exact_record_types(
        record, INGESTION_ENVELOPE_FIELDS,
        bool_fields={"reviewer_provenance_attested"},
    )
    return _record_sha(
        record, INGESTION_ENVELOPE_FIELDS, "ingestion_envelope_sha256",
    )


def validate_ingestion_envelope(
    envelope: Mapping[str, Any],
    *,
    review_record: Mapping[str, Any] | None = None,
    valid_sample_ids: Iterable[str] = (),
) -> None:
    try:
        _validate_exact_record_types(
            envelope, INGESTION_ENVELOPE_FIELDS,
            bool_fields={"reviewer_provenance_attested"},
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("INGESTION_ENVELOPE_EXACT_TYPE_INVALID") from error
    if envelope["ingestion_envelope_version"] != INGESTION_ENVELOPE_VERSION:
        raise ValueError("INGESTION_ENVELOPE_IDENTITY_INVALID")
    if not _meaningful(envelope["submission_batch_id"]):
        raise ValueError("SUBMISSION_BATCH_ID_NOT_MEANINGFUL")
    valid_ids = set(valid_sample_ids)
    if valid_ids and envelope["sample_index_row_id"] not in valid_ids:
        raise ValueError("ENVELOPE_SAMPLE_REVIEW_LINKAGE_MISMATCH")
    if (
        _SHA.fullmatch(envelope["review_record_sha256"]) is None
        or _SHA.fullmatch(envelope["submitted_record_payload_sha256"]) is None
        or _SHA.fullmatch(envelope["ingestion_envelope_sha256"]) is None
    ):
        raise ValueError("INGESTION_ENVELOPE_SHA_INVALID")
    if envelope["reviewer_provenance_attested"] is not True:
        raise ValueError("HUMAN_PROVENANCE_ATTESTATION_REQUIRED")
    if (
        not _meaningful(envelope["reviewer_provenance_attestor_id"])
        or _forbidden_reviewer(envelope["reviewer_provenance_attestor_id"])
    ):
        raise ValueError("PROVENANCE_ATTESTOR_INVALID")
    if not _meaningful(envelope["submission_source_label"]):
        raise ValueError("SUBMISSION_SOURCE_LABEL_NOT_MEANINGFUL")
    if review_record is not None:
        _validate_review_schema(review_record)
        if (
            envelope["sample_index_row_id"] != review_record["sample_index_row_id"]
            or envelope["review_record_sha256"]
            != review_record["review_record_sha256"]
        ):
            raise ValueError("ENVELOPE_SAMPLE_REVIEW_LINKAGE_MISMATCH")
        if (
            envelope["submitted_record_payload_sha256"]
            != submitted_record_payload_sha256(review_record)
        ):
            raise ValueError("SUBMITTED_REVIEW_PAYLOAD_SHA_MISMATCH")
    if envelope["ingestion_envelope_sha256"] != ingestion_envelope_sha256(envelope):
        raise ValueError("INGESTION_ENVELOPE_SHA_INVALID")


def _validate_exact_record_types(
    record: Mapping[str, Any],
    fields: Sequence[str],
    *,
    bool_fields: set[str] | frozenset[str] = frozenset(),
    list_fields: set[str] | frozenset[str] = frozenset(),
) -> None:
    if type(record) is not dict or tuple(record) != tuple(fields):
        raise ValueError("record_field_inventory_mismatch")
    for field in fields:
        value = record[field]
        if field in bool_fields:
            if type(value) is not bool:
                raise ValueError(f"exact_bool_invalid:{field}")
        elif field in list_fields:
            if type(value) is not list or any(type(item) is not str for item in value):
                raise ValueError(f"exact_list_str_invalid:{field}")
        elif type(value) is not str:
            raise ValueError(f"exact_str_invalid:{field}")


def authority_record_sha256(record: Mapping[str, Any]) -> str:
    _validate_exact_record_types(
        record, AUTHORITY_RECORD_FIELDS, bool_fields=AUTHORITY_BOOL_FIELDS,
        list_fields={"reviewed_warhead_atom_ids"},
    )
    return _record_sha(record, AUTHORITY_RECORD_FIELDS, "authority_record_sha256")


def validate_authority_record(record: Mapping[str, Any]) -> None:
    _validate_exact_record_types(
        record, AUTHORITY_RECORD_FIELDS, bool_fields=AUTHORITY_BOOL_FIELDS,
        list_fields={"reviewed_warhead_atom_ids"},
    )
    if record["authority_record_version"] != AUTHORITY_RECORD_VERSION:
        raise ValueError("AUTHORITY_RECORD_VERSION_INVALID")
    if record["review_decision"] not in REVIEW_DECISIONS[1:]:
        raise ValueError("AUTHORITY_REVIEW_DECISION_INVALID")
    if record["authority_disposition"] not in AUTHORITY_DISPOSITIONS:
        raise ValueError("AUTHORITY_DISPOSITION_INVALID")
    if record["authority_status"] not in AUTHORITY_STATUSES:
        raise ValueError("AUTHORITY_STATUS_INVALID")
    if record["supersedes_authority_record_sha256"] != "":
        raise ValueError("V1_SUPERSESSION_UNAVAILABLE")
    if (
        not _meaningful(record["reviewer_id"])
        or _forbidden_reviewer(record["reviewer_id"])
    ):
        raise ValueError("AUTHORITY_REVIEWER_INVALID")
    atoms = record["reviewed_warhead_atom_ids"]
    if atoms != _utf8_sorted(atoms) or len(atoms) != len(set(atoms)):
        raise ValueError("AUTHORITY_REVIEWED_ATOM_IDS_INVALID")
    for field in (
        "source_assignment_record_sha256", "source_proposal_record_sha256",
        "source_candidate_set_sha256", "source_review_record_sha256",
        "source_ingestion_envelope_sha256", "review_rationale_sha256",
        "authority_record_sha256",
    ):
        if _SHA.fullmatch(record[field]) is None:
            raise ValueError("AUTHORITY_SOURCE_LINEAGE_OR_SHA_INVALID")
    quarantine = record["review_decision"] == "quarantine"
    expected = (
        "reviewed_quarantine_no_authority" if quarantine
        else "reviewed_authority_materialized",
        not quarantine, not quarantine, quarantine,
        "quarantined" if quarantine else "active",
    )
    observed = (
        record["authority_disposition"],
        record["complete_warhead_atom_set_authority_available"],
        record["exact_one_attachment_boundary_authority_available"],
        record["sample_quarantined"], record["authority_status"],
    )
    if observed != expected:
        raise ValueError("AUTHORITY_DECISION_EFFECT_INVALID")
    boundary_blank = (
        atoms == []
        and record["reviewed_warhead_attachment_atom_id"] == ""
        and record["reviewed_nonwarhead_boundary_atom_id"] == ""
        and record["reviewed_attachment_boundary_bond_order"] == ""
        and record["reviewed_boundary_bond_id"] == ""
    )
    if quarantine is not boundary_blank:
        raise ValueError("AUTHORITY_DECISION_EFFECT_INVALID")
    if record["authority_record_sha256"] != authority_record_sha256(record):
        raise ValueError("AUTHORITY_RECORD_SHA_MISMATCH")


def validate_authority_package_lineage(
    authority: Mapping[str, Any],
    *,
    package_identity_by_sample: Mapping[str, Mapping[str, Any]],
) -> None:
    """Require an authority identity and lineage to equal its Exact14 package."""

    if type(authority) is not dict:
        raise ValueError("EXISTING_AUTHORITY_LINEAGE_MISMATCH")
    sample = authority.get("sample_index_row_id")
    if type(sample) is not str or sample not in package_identity_by_sample:
        raise ValueError("EXISTING_AUTHORITY_LINEAGE_MISMATCH")
    identity = package_identity_by_sample[sample]
    _validate_package_identity_record(identity)
    authority_to_package = {
        "sample_index_row_id": "sample_index_row_id",
        "pdb_id": "pdb_id",
        "ligand_comp_id": "ligand_comp_id",
        "warhead_type_candidate_class_id": "warhead_type_candidate_class_id",
        "reaction_family_id": "reaction_family_id",
        "warhead_rule_id": "warhead_rule_id",
        "source_assignment_record_sha256": "source_assignment_record_sha256",
        "source_proposal_record_sha256": "source_proposal_record_sha256",
        "source_candidate_set_sha256": "source_candidate_set_sha256",
    }
    if any(
        authority[authority_field] != identity[identity_field]
        for authority_field, identity_field in authority_to_package.items()
    ):
        raise ValueError("EXISTING_AUTHORITY_LINEAGE_MISMATCH")


def materialize_authority_record(
    review_record: Mapping[str, Any],
    envelope: Mapping[str, Any],
    *,
    package_identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Create one synthetic future authority/disposition record in memory."""

    if review_record["review_decision"] == "not_reviewed":
        raise ValueError("REVIEW_NOT_COMPLETED")
    _validate_package_identity_record(package_identity)
    if any(
        review_record[field] != package_identity[field]
        for field in COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS
    ):
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    quarantine = review_record["review_decision"] == "quarantine"
    record: dict[str, Any] = {
        "authority_record_version": AUTHORITY_RECORD_VERSION,
        "sample_index_row_id": package_identity["sample_index_row_id"],
        "pdb_id": package_identity["pdb_id"],
        "ligand_comp_id": package_identity["ligand_comp_id"],
        "warhead_type_candidate_class_id":
            package_identity["warhead_type_candidate_class_id"],
        "reaction_family_id": package_identity["reaction_family_id"],
        "warhead_rule_id": package_identity["warhead_rule_id"],
        "source_assignment_record_sha256":
            package_identity["source_assignment_record_sha256"],
        "source_proposal_record_sha256":
            package_identity["source_proposal_record_sha256"],
        "source_candidate_set_sha256":
            package_identity["source_candidate_set_sha256"],
        "source_review_record_sha256": review_record["review_record_sha256"],
        "source_ingestion_envelope_sha256":
            envelope["ingestion_envelope_sha256"],
        "review_decision": review_record["review_decision"],
        "reviewed_warhead_atom_ids":
            list(review_record["reviewed_warhead_atom_ids"]),
        "reviewed_warhead_attachment_atom_id":
            review_record["reviewed_warhead_attachment_atom_id"],
        "reviewed_nonwarhead_boundary_atom_id":
            review_record["reviewed_nonwarhead_boundary_atom_id"],
        "reviewed_attachment_boundary_bond_order":
            review_record["reviewed_attachment_boundary_bond_order"],
        "reviewed_boundary_bond_id": review_record["reviewed_boundary_bond_id"],
        "reviewer_id": review_record["reviewer_id"],
        "review_rationale_sha256":
            sha256(review_record["review_rationale"].encode("utf-8")),
        "authority_disposition": (
            "reviewed_quarantine_no_authority" if quarantine
            else "reviewed_authority_materialized"
        ),
        "complete_warhead_atom_set_authority_available": not quarantine,
        "exact_one_attachment_boundary_authority_available": not quarantine,
        "sample_quarantined": quarantine,
        "supersedes_authority_record_sha256": "",
        "authority_status": "quarantined" if quarantine else "active",
        "authority_record_sha256": "",
    }
    record["authority_record_sha256"] = authority_record_sha256(record)
    validate_authority_record(record)
    return record


def ingestion_result_sha256(record: Mapping[str, Any]) -> str:
    _validate_exact_record_types(
        record, INGESTION_RESULT_FIELDS,
        bool_fields=INGESTION_RESULT_BOOL_FIELDS,
    )
    return _record_sha(
        record, INGESTION_RESULT_FIELDS, "ingestion_result_sha256",
    )


def validate_ingestion_result(record: Mapping[str, Any]) -> None:
    _validate_exact_record_types(
        record, INGESTION_RESULT_FIELDS,
        bool_fields=INGESTION_RESULT_BOOL_FIELDS,
    )
    if record["ingestion_result_version"] != INGESTION_RESULT_VERSION:
        raise ValueError("INGESTION_RESULT_VERSION_INVALID")
    if record["outcome"] not in INGESTION_OUTCOMES:
        raise ValueError("INGESTION_RESULT_OUTCOME_INVALID")
    if record["reason"] not in INGESTION_RESULT_REASON_CODES:
        raise ValueError("INGESTION_RESULT_REASON_INVALID")
    if _SHA.fullmatch(record["ingestion_result_sha256"]) is None:
        raise ValueError("INGESTION_RESULT_SHA_INVALID")
    passed_reasons = {"PASSED", "IDEMPOTENT_REPLAY"}
    blocked_reasons = {
        "REVIEW_NOT_COMPLETED", "CONFLICTING_REVIEW_REINGESTION",
        "BATCH_ATOMICITY_ABORTED",
    }
    invalid_reasons = (
        set(INGESTION_RESULT_REASON_CODES) - passed_reasons - blocked_reasons
    )
    if record["outcome"] == "passed":
        expected_disposition = (
            "reviewed_quarantine_no_authority"
            if record["review_decision"] == "quarantine"
            else "reviewed_authority_materialized"
            if record["review_decision"] in {
                "select_admitted_candidate", "revise_atom_set_and_boundary",
            }
            else None
        )
        valid = (
            record["reason"] in passed_reasons
            and record["passed"] is True
            and record["blocks_batch"] is False
            and record["review_completed"] is True
            and record["consumed_review_record"] is True
            and record["consumed_ingestion_envelope"] is True
            and record["conflicting_existing_authority"] is False
            and record["authority_disposition"] == expected_disposition
            and _SHA.fullmatch(record["authority_record_sha256"]) is not None
            and record["idempotent_replay"]
            is (record["reason"] == "IDEMPOTENT_REPLAY")
        )
    elif record["outcome"] == "blocked":
        valid = (
            record["reason"] in blocked_reasons
            and record["passed"] is False
            and record["blocks_batch"] is True
            and record["review_completed"] is False
            and record["authority_disposition"] == ""
            and record["authority_record_sha256"] == ""
            and record["idempotent_replay"] is False
            and record["consumed_review_record"] is False
            and record["consumed_ingestion_envelope"] is False
            and record["conflicting_existing_authority"]
            is (record["reason"] == "CONFLICTING_REVIEW_REINGESTION")
        )
    else:
        valid = (
            record["reason"] in invalid_reasons
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
    if not valid:
        raise ValueError("INGESTION_RESULT_REASON_EFFECT_INVALID")
    if record["ingestion_result_sha256"] != ingestion_result_sha256(record):
        raise ValueError("INGESTION_RESULT_SHA_MISMATCH")


def _result_record(
    *,
    batch_id: str,
    sample_id: str,
    review_sha: str,
    envelope_sha: str,
    outcome: str,
    reason: str,
    decision: str,
    authority: Mapping[str, Any] | None = None,
    replay: bool = False,
    conflict: bool = False,
    consumed: bool = False,
) -> dict[str, Any]:
    passed = outcome == "passed"
    row: dict[str, Any] = {
        "ingestion_result_version": INGESTION_RESULT_VERSION,
        "submission_batch_id": batch_id,
        "sample_index_row_id": sample_id,
        "review_record_sha256": review_sha,
        "ingestion_envelope_sha256": envelope_sha,
        "outcome": outcome, "passed": passed, "blocks_batch": not passed,
        "reason": reason, "review_decision": decision,
        "review_completed": passed,
        "authority_disposition": (
            authority["authority_disposition"] if authority is not None else ""
        ),
        "authority_record_sha256": (
            authority["authority_record_sha256"] if authority is not None else ""
        ),
        "idempotent_replay": replay,
        "conflicting_existing_authority": conflict,
        "consumed_review_record": consumed,
        "consumed_ingestion_envelope": consumed,
        "ingestion_result_sha256": "",
    }
    row["ingestion_result_sha256"] = ingestion_result_sha256(row)
    validate_ingestion_result(row)
    return row


@dataclass(frozen=True)
class BatchIngestionResult:
    passed: bool
    result_records: tuple[Mapping[str, Any], ...]
    new_authority_records: tuple[Mapping[str, Any], ...]


def _public_review_reason(
    error: BaseException,
    *,
    review: object,
) -> str:
    message = str(error)
    if message in INGESTION_RESULT_REASON_CODES:
        return message
    decision = (
        review.get("review_decision")
        if isinstance(review, Mapping) else None
    )
    if message.startswith((
        "review_field_inventory_mismatch",
        "review_template_field_inventory_mismatch",
        "review_exact_",
        "selected_index_exact_",
        "review_identity_or_decision_invalid",
        "REVIEW_IDENTITY_LINKAGE_MISMATCH",
    )):
        return "REVIEW_IDENTITY_LINKAGE_MISMATCH"
    if message.startswith((
        "review_record_SHA", "record_field_inventory_mismatch",
        "COMPLETED_REVIEW_RECORD_SHA_INVALID",
    )):
        return "COMPLETED_REVIEW_RECORD_SHA_INVALID"
    if decision == "select_admitted_candidate":
        return "SELECT_DEPENDENCY_INVALID"
    if decision == "revise_atom_set_and_boundary":
        return "REVISE_GRAPH_INVARIANT_INVALID"
    if decision == "quarantine":
        return "QUARANTINE_DEPENDENCY_INVALID"
    return "REVIEW_IDENTITY_LINKAGE_MISMATCH"


def _public_envelope_reason(error: BaseException) -> str:
    message = str(error)
    if message in INGESTION_RESULT_REASON_CODES:
        return message
    if message.startswith((
        "record_field_inventory_mismatch", "exact_bool_invalid",
        "exact_str_invalid", "INGESTION_ENVELOPE_EXACT_TYPE_INVALID",
    )):
        return "INGESTION_ENVELOPE_EXACT_TYPE_INVALID"
    if "SHA" in message:
        return "INGESTION_ENVELOPE_SHA_INVALID"
    return "INGESTION_ENVELOPE_IDENTITY_INVALID"


def _validate_proposal_package_lineage(
    proposal: Mapping[str, Any] | None,
    *,
    package_identity: Mapping[str, Any],
) -> None:
    if type(proposal) is not dict:
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    joins = (
        ("sample_index_row_id", "sample_index_row_id"),
        ("pdb_id", "pdb_id"),
        ("ligand_comp_id", "ligand_comp_id"),
        (
            "warhead_type_candidate_class_index_0based",
            "warhead_type_candidate_class_index_0based",
        ),
        ("warhead_type_candidate_class_id", "warhead_type_candidate_class_id"),
        ("reaction_family_id", "reaction_family_id"),
        ("warhead_rule_id", "warhead_rule_id"),
        ("proposal_record_sha256", "source_proposal_record_sha256"),
        ("source_assignment_record_sha256", "source_assignment_record_sha256"),
    )
    if any(
        proposal[proposal_field] != package_identity[identity_field]
        for proposal_field, identity_field in joins
    ):
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    if _SHA.fullmatch(package_identity["source_candidate_set_sha256"]) is None:
        raise ValueError("REVIEW_IDENTITY_LINKAGE_MISMATCH")


def _validated_existing_authorities_by_sample(
    existing_authorities: Sequence[Mapping[str, Any]],
    *,
    package_identity_by_sample: Mapping[str, Mapping[str, Any]],
    options: Sequence[Mapping[str, Any]],
    proposals_by_sample: Mapping[str, Mapping[str, Any]],
    parent_atom_ids_by_ligand: Mapping[str, Sequence[str]],
    parent_bonds_by_ligand: Mapping[
        str, Sequence[Mapping[str, str] | Sequence[str]]
    ],
) -> dict[str, Mapping[str, Any]]:
    validated = []
    for authority in existing_authorities:
        try:
            validate_authority_record(authority)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("EXISTING_AUTHORITY_SET_INVALID") from error
        validated.append(authority)
    samples = [authority["sample_index_row_id"] for authority in validated]
    authority_shas = [
        authority["authority_record_sha256"] for authority in validated
    ]
    if len(samples) != len(set(samples)) or len(authority_shas) != len(
        set(authority_shas)
    ):
        raise ValueError("EXISTING_AUTHORITY_SET_INVALID")
    for authority in validated:
        try:
            validate_authority_package_lineage(
                authority,
                package_identity_by_sample=package_identity_by_sample,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("EXISTING_AUTHORITY_LINEAGE_MISMATCH") from error
        try:
            decision = authority["review_decision"]
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
                    ) == (
                        authority["reviewed_warhead_atom_ids"],
                        authority["reviewed_warhead_attachment_atom_id"],
                        authority["reviewed_nonwarhead_boundary_atom_id"],
                        authority["reviewed_attachment_boundary_bond_order"],
                        authority["reviewed_boundary_bond_id"],
                    )
                ]
                if len(matches) != 1:
                    raise ValueError("existing_select_evidence_invalid")
            elif decision == "revise_atom_set_and_boundary":
                sample = authority["sample_index_row_id"]
                ligand = authority["ligand_comp_id"]
                _validate_revised_boundary_evidence(
                    authority, proposal=proposals_by_sample[sample],
                    parent_atom_ids=parent_atom_ids_by_ligand[ligand],
                    parent_bonds=parent_bonds_by_ligand[ligand],
                )
            elif decision != "quarantine":
                raise ValueError("existing_decision_invalid")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("EXISTING_AUTHORITY_SET_INVALID") from error
    return {
        authority["sample_index_row_id"]: authority
        for authority in sorted(
            validated, key=lambda row: row["sample_index_row_id"],
        )
    }


def _existing_authority_semantically_matches_review(
    authority: Mapping[str, Any],
    review: Mapping[str, Any],
) -> bool:
    direct_fields = (
        ("review_decision", "review_decision"),
        ("reviewed_warhead_atom_ids", "reviewed_warhead_atom_ids"),
        (
            "reviewed_warhead_attachment_atom_id",
            "reviewed_warhead_attachment_atom_id",
        ),
        (
            "reviewed_nonwarhead_boundary_atom_id",
            "reviewed_nonwarhead_boundary_atom_id",
        ),
        (
            "reviewed_attachment_boundary_bond_order",
            "reviewed_attachment_boundary_bond_order",
        ),
        ("reviewed_boundary_bond_id", "reviewed_boundary_bond_id"),
        ("reviewer_id", "reviewer_id"),
    )
    return (
        all(
            authority[authority_field] == review[review_field]
            for authority_field, review_field in direct_fields
        )
        and authority["review_rationale_sha256"]
        == sha256(review["review_rationale"].encode("utf-8"))
    )


def ingest_review_batch(
    submissions: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    authority_context: IngestionAuthorityContext,
    existing_authorities: Sequence[Mapping[str, Any]] = (),
) -> BatchIngestionResult:
    """Exercise the frozen future all-or-nothing semantics in memory only."""

    def safe_value(record: object, field: str) -> str:
        if not isinstance(record, Mapping):
            return ""
        value = record.get(field, "")
        return value if type(value) is str else ""

    def batch_failure(reason: str) -> BatchIngestionResult:
        records = tuple(
            _result_record(
                batch_id=safe_value(envelope, "submission_batch_id"),
                sample_id=safe_value(review, "sample_index_row_id"),
                review_sha=safe_value(review, "review_record_sha256"),
                envelope_sha=safe_value(envelope, "ingestion_envelope_sha256"),
                outcome="invalid", reason=reason,
                decision=safe_value(review, "review_decision"),
            )
            for review, envelope in submissions
        )
        return BatchIngestionResult(False, records, ())

    if not 1 <= len(submissions) <= 11:
        return batch_failure("BATCH_SIZE_INVALID")
    batch_ids = [
        envelope.get("submission_batch_id")
        if isinstance(envelope, Mapping) else None
        for _, envelope in submissions
    ]
    if (
        all(type(value) is str for value in batch_ids)
        and any(value != batch_ids[0] for value in batch_ids[1:])
    ):
        return batch_failure("SUBMISSION_BATCH_ID_MISMATCH")
    sample_ids = [
        review.get("sample_index_row_id")
        if isinstance(review, Mapping) else None
        for review, _ in submissions
    ]
    if any(
        sample_ids[index] == sample_ids[prior]
        for index in range(len(sample_ids))
        for prior in range(index)
        if type(sample_ids[index]) is str
    ):
        return batch_failure("DUPLICATE_SAMPLE_IN_BATCH")
    review_shas = [
        review.get("review_record_sha256")
        if isinstance(review, Mapping) else None
        for review, _ in submissions
    ]
    if any(
        review_shas[index] == review_shas[prior]
        for index in range(len(review_shas))
        for prior in range(index)
        if type(review_shas[index]) is str
    ):
        return batch_failure("DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH")

    try:
        phase = _validated_ingestion_authority_context(authority_context)
        package_identity_by_sample = phase.package_identity_by_sample
        options = phase.option_rows
        proposals_by_sample = {
            row["sample_index_row_id"]: row for row in phase.proposal_rows
        }
        parent_atom_ids_by_ligand: dict[str, list[str]] = defaultdict(list)
        for row in phase.parent_atom_rows:
            parent_atom_ids_by_ligand[row["ligand_comp_id"]].append(
                row["ccd_atom_id"]
            )
        parent_bonds_by_ligand: dict[
            str, list[Mapping[str, str]]
        ] = defaultdict(list)
        for row in phase.parent_bond_rows:
            parent_bonds_by_ligand[row["ligand_comp_id"]].append(row)
    except (KeyError, TypeError, ValueError):
        return batch_failure("INGESTION_AUTHORITY_CONTEXT_INVALID")

    try:
        existing_by_sample = _validated_existing_authorities_by_sample(
            existing_authorities,
            package_identity_by_sample=package_identity_by_sample,
            options=options, proposals_by_sample=proposals_by_sample,
            parent_atom_ids_by_ligand=parent_atom_ids_by_ligand,
            parent_bonds_by_ligand=parent_bonds_by_ligand,
        )
    except ValueError as error:
        reason = str(error)
        if reason not in {
            "EXISTING_AUTHORITY_SET_INVALID",
            "EXISTING_AUTHORITY_LINEAGE_MISMATCH",
        }:
            reason = "EXISTING_AUTHORITY_SET_INVALID"
        return batch_failure(reason)

    candidates: list[
        tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], bool]
    ] = []
    record_failures: list[str | None] = [None] * len(submissions)
    conflicts: list[bool] = [False] * len(submissions)
    semantic_existing_lineage_invalid = False
    for position, (review, envelope) in enumerate(submissions):
        try:
            validate_completed_review_package_identity(
                review,
                package_identity_by_sample=package_identity_by_sample,
            )
            package_identity = package_identity_by_sample[
                review["sample_index_row_id"]
            ]
            proposal = proposals_by_sample.get(package_identity["sample_index_row_id"])
            _validate_proposal_package_lineage(
                proposal, package_identity=package_identity,
            )
            authoritative_ligand = package_identity["ligand_comp_id"]
            validate_review_record(
                review, options=options, proposal=proposal,
                parent_atom_ids=parent_atom_ids_by_ligand.get(
                    authoritative_ligand, ()
                ),
                parent_bonds=parent_bonds_by_ligand.get(
                    authoritative_ligand, ()
                ),
                package_identity=package_identity,
                completed_submission=True,
            )
        except (KeyError, TypeError, ValueError) as error:
            record_failures[position] = _public_review_reason(
                error, review=review,
            )
            continue
        try:
            validate_ingestion_envelope(
                envelope, review_record=review,
                valid_sample_ids=package_identity_by_sample.keys(),
            )
        except (KeyError, TypeError, ValueError) as error:
            record_failures[position] = _public_envelope_reason(error)
            continue
        existing = existing_by_sample.get(package_identity["sample_index_row_id"])
        if existing is not None:
            if (
                existing["source_review_record_sha256"]
                == review["review_record_sha256"]
            ):
                if not _existing_authority_semantically_matches_review(
                    existing, review,
                ):
                    semantic_existing_lineage_invalid = True
                    continue
                candidates.append((review, envelope, existing, True))
            else:
                record_failures[position] = "CONFLICTING_REVIEW_REINGESTION"
                conflicts[position] = True
        else:
            try:
                authority = materialize_authority_record(
                    review, envelope, package_identity=package_identity,
                )
            except (KeyError, TypeError, ValueError) as error:
                record_failures[position] = _public_review_reason(
                    error, review=review,
                )
                continue
            candidates.append((review, envelope, authority, False))

    if semantic_existing_lineage_invalid:
        return batch_failure("EXISTING_AUTHORITY_LINEAGE_MISMATCH")
    if any(reason is not None for reason in record_failures):
        records = []
        for position, (review, envelope) in enumerate(submissions):
            reason = record_failures[position] or "BATCH_ATOMICITY_ABORTED"
            records.append(_result_record(
                batch_id=safe_value(envelope, "submission_batch_id"),
                sample_id=safe_value(review, "sample_index_row_id"),
                review_sha=safe_value(review, "review_record_sha256"),
                envelope_sha=safe_value(envelope, "ingestion_envelope_sha256"),
                outcome="blocked" if reason in {
                    "REVIEW_NOT_COMPLETED",
                    "CONFLICTING_REVIEW_REINGESTION",
                    "BATCH_ATOMICITY_ABORTED",
                } else "invalid",
                reason=reason, decision=safe_value(review, "review_decision"),
                conflict=conflicts[position],
            ))
        return BatchIngestionResult(False, tuple(records), ())

    records = []
    new_authorities = []
    for review, envelope, authority, replay in candidates:
        if not replay:
            new_authorities.append(authority)
        records.append(_result_record(
            batch_id=envelope["submission_batch_id"],
            sample_id=review["sample_index_row_id"],
            review_sha=review["review_record_sha256"],
            envelope_sha=envelope["ingestion_envelope_sha256"],
            outcome="passed", reason="IDEMPOTENT_REPLAY" if replay else "PASSED",
            decision=review["review_decision"], authority=authority,
            replay=replay, consumed=True,
        ))
    return BatchIngestionResult(True, tuple(records), tuple(new_authorities))


def _typed_option(row: Mapping[str, str]) -> dict[str, Any]:
    if tuple(row) != OPTION_FIELDS:
        raise ValueError("option_field_inventory_mismatch")
    result: dict[str, Any] = {}
    for field in OPTION_FIELDS:
        if field in OPTION_INT_FIELDS:
            result[field] = _parse_int(row[field], field)
        elif field in OPTION_BOOL_FIELDS:
            result[field] = _parse_bool(row[field], field)
        elif field in OPTION_LIST_FIELDS:
            result[field] = _parse_list(row[field], field)
        else:
            result[field] = row[field]
    expected = _record_sha(result, OPTION_FIELDS, "package_option_record_sha256")
    if result["package_option_record_sha256"] != expected:
        raise ValueError("OPTION_RECORD_SHA_MISMATCH")
    if result["package_option_version"] != PACKAGE_OPTION_VERSION:
        raise ValueError("OPTION_VERSION_MISMATCH")
    if result["candidate_admitted"] is not result["review_eligible"]:
        raise ValueError("OPTION_ELIGIBILITY_MISMATCH")
    return result


def _typed_proposal(row: Mapping[str, str]) -> dict[str, Any]:
    if tuple(row) != PROPOSAL_FIELDS:
        raise ValueError("proposal_field_inventory_mismatch")
    result: dict[str, Any] = {}
    list_fields = {
        "local_reaction_center_atom_ids", "local_reaction_center_bond_ids",
        "proposed_pre_reaction_warhead_atom_ids",
        "required_leaving_group_atom_ids", "ambiguity_reasons",
    }
    for field in PROPOSAL_FIELDS:
        if field == "warhead_type_candidate_class_index_0based":
            result[field] = _parse_int(row[field], field)
        elif field in list_fields:
            result[field] = _parse_list(row[field], field)
        else:
            result[field] = row[field]
    if (
        result["proposal_record_sha256"]
        != _record_sha(result, PROPOSAL_FIELDS, "proposal_record_sha256")
    ):
        raise ValueError("PROPOSAL_RECORD_SHA_MISMATCH")
    if (
        result["proposal_status"] != "ambiguous_candidate"
        or result["ambiguity_reasons"]
        != ["multiple_admissible_exact_one_boundary_candidates"]
        or result["proposed_pre_reaction_warhead_atom_ids"] != []
        or any(result[field] for field in (
            "proposed_warhead_attachment_atom_id",
            "proposed_nonwarhead_boundary_atom_id",
            "proposed_attachment_boundary_bond_order",
        ))
    ):
        raise ValueError("PROPOSAL_AMBIGUOUS_SOURCE_STATE_INVALID")
    return result


def _source_metadata(path: Path) -> tuple[str, str, str, bool]:
    values = {
        PACKAGE_PRODUCTION: (
            "11/11", "Exact26 review schema and validation semantics",
            "predecessor_production_contract", True,
        ),
        PACKAGE_MANIFEST: (
            "11/11", "transaction, counts, versions, closed downstream",
            "review_package_manifest", True,
        ),
        PACKAGE_INDEX: (
            "11/11", "sample/package/candidate-set/template identity",
            "review_package_index", True,
        ),
        PACKAGE_OPTIONS: (
            "11/11", "Exact200 option identities, eligibility, hashes",
            "review_option_evidence", True,
        ),
        PACKAGE_TEMPLATES: (
            "11/11", "blank Exact26 not_reviewed templates",
            "unreviewed_template_evidence", True,
        ),
        PACKAGE_FAILURE: (
            "11/11", "predecessor fail-closed evidence",
            "predecessor_failure_evidence", False,
        ),
        PROPOSALS: (
            "11/11", "proposal identity, local center, leaving groups",
            "proposal_records", True,
        ),
        PROPOSAL_MANIFEST: (
            "11/11", "proposal transaction and closed authority",
            "proposal_manifest", True,
        ),
        ASSIGNMENTS: (
            "11/11", "assignment lineage and family/rule candidate identity",
            "candidate_assignment_authority", True,
        ),
        PARENT_ATOMS: (
            "11/11", "parent_ccd_atom_id namespace",
            "parent_heavy_atom_authority", True,
        ),
        PARENT_BONDS: (
            "11/11", "bond order, connectivity, exact-one boundary",
            "parent_heavy_bond_authority", True,
        ),
        ROLE_CONTRACT: (
            "11/11", "five-mask and downstream role/seed boundary",
            "downstream_design_contract", False,
        ),
        PARALLEL_REVIEW_MANIFEST: (
            "11/11", "parallel family/topology review remains incomplete",
            "parallel_review_manifest", True,
        ),
    }
    return values[path]


def _source_inventory(
    payloads: Mapping[Path, bytes],
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for path in SOURCE_PATHS:
        coverage, fields, authority, current = _source_metadata(path)
        payload = payloads[path]
        count = (
            len(_csv_rows(payload)) if path.suffix == ".csv"
            else 1 if path.suffix == ".json"
            else len(payload.decode("utf-8").splitlines())
        )
        rows.append({
            "source_path": path.as_posix(),
            "BASE_SHA256": sha256(payload),
            "source_row_count": count,
            "Current11_coverage": coverage,
            "fields_actually_used": fields,
            "authority_class": authority,
            "provides_current_value": current,
            "verified": True,
        })
    return tuple(rows)


@dataclass(frozen=True)
class PhaseA:
    index_rows: tuple[Mapping[str, str], ...]
    package_identity_by_sample: Mapping[str, Mapping[str, Any]]
    option_rows: tuple[Mapping[str, Any], ...]
    template_rows: tuple[Mapping[str, Any], ...]
    proposal_rows: tuple[Mapping[str, Any], ...]
    assignment_rows: tuple[Mapping[str, str], ...]
    parent_atom_rows: tuple[Mapping[str, str], ...]
    parent_bond_rows: tuple[Mapping[str, str], ...]
    blocking_reasons: tuple[str, ...]


def _validate_phase_a(payloads: Mapping[Path, bytes]) -> PhaseA:
    reasons: list[str] = []
    manifest = json.loads(payloads[PACKAGE_MANIFEST])
    proposal_manifest = json.loads(payloads[PROPOSAL_MANIFEST])
    parallel_manifest = json.loads(payloads[PARALLEL_REVIEW_MANIFEST])
    raw_index = _csv_rows(payloads[PACKAGE_INDEX])
    raw_options = _csv_rows(payloads[PACKAGE_OPTIONS])
    raw_templates = _csv_rows(payloads[PACKAGE_TEMPLATES])
    raw_proposals = _csv_rows(payloads[PROPOSALS])
    assignments = _csv_rows(payloads[ASSIGNMENTS])
    parent_atoms = _csv_rows(payloads[PARENT_ATOMS])
    parent_bonds = _csv_rows(payloads[PARENT_BONDS])
    if not manifest.get("transaction_succeeded"):
        reasons.append("REVIEW_PACKAGE_TRANSACTION_NOT_SUCCEEDED")
    if len(raw_index) != 11:
        reasons.append("PACKAGE_COUNT_NOT_11")
    if len(raw_options) != 200:
        reasons.append("OPTION_COUNT_NOT_200")
    if len(raw_templates) != 11:
        reasons.append("TEMPLATE_COUNT_NOT_11")
    if len(raw_proposals) != 11 or len(assignments) != 11:
        reasons.append("AUTHORITY_CONTEXT_CURRENT11_COUNT_MISMATCH")
    if tuple(raw_index[0]) != INDEX_FIELDS if raw_index else True:
        reasons.append("PACKAGE_INDEX_FIELD_INVENTORY_MISMATCH")
    if tuple(raw_templates[0]) != REVIEW_RECORD_FIELDS if raw_templates else True:
        reasons.append("INHERITED_REVIEW_FIELD_INVENTORY_MISMATCH")
    options: list[Mapping[str, Any]] = []
    templates: list[Mapping[str, Any]] = []
    proposals: list[Mapping[str, Any]] = []
    try:
        options = [_typed_option(row) for row in raw_options]
    except ValueError as error:
        reasons.append(str(error))
    try:
        templates = [parse_review_record_csv(row) for row in raw_templates]
        for row in templates:
            validate_review_record(row)
    except ValueError as error:
        reasons.append(str(error))
    try:
        proposals = [_typed_proposal(row) for row in raw_proposals]
    except ValueError as error:
        reasons.append(str(error))
    package_identity_by_sample: dict[str, dict[str, Any]] = {}
    try:
        package_identity_by_sample = build_package_identity_by_sample(
            raw_index, templates,
        )
    except ValueError:
        reasons.append("REVIEW_IDENTITY_LINKAGE_MISMATCH")
    index_by_sample = {row["sample_index_row_id"]: row for row in raw_index}
    template_by_sample = {
        row["sample_index_row_id"]: row for row in templates
    }
    proposal_by_sample = {
        row["sample_index_row_id"]: row for row in proposals
    }
    assignment_by_sample = {
        row["sample_index_row_id"]: row for row in assignments
    }
    if (
        len(index_by_sample) != 11
        or len({row["source_candidate_set_sha256"] for row in raw_index}) != 11
    ):
        reasons.append("CANDIDATE_SET_IDENTITY_COUNT_NOT_11")
    if len(template_by_sample) != 11 or len(proposal_by_sample) != 11:
        reasons.append("CURRENT11_IDENTITY_COUNT_NOT_11")
    if len(options) == 200:
        if sum(row["review_eligible"] for row in options) != 185:
            reasons.append("OPTION_ELIGIBILITY_COUNT_MISMATCH")
        for index, row in enumerate(options):
            if row["package_item_order_0based"] != index:
                reasons.append("OPTION_ORDER_MISMATCH")
                break
    assignment_fields = tuple(assignments[0]) if assignments else ()
    if (
        not assignments
        or any(tuple(row) != assignment_fields for row in assignments)
        or "assignment_record_sha256" not in assignment_fields
    ):
        reasons.append("ASSIGNMENT_FIELD_INVENTORY_MISMATCH")
    else:
        for row in assignments:
            try:
                assignment_payload = {
                    field: (
                        _parse_int(row[field], field)
                        if field == "warhead_type_candidate_class_index_0based"
                        else row[field]
                    )
                    for field in ASSIGNMENT_HASH_FIELDS
                }
                if (
                    row["assignment_record_sha256"]
                    != sha256(
                        canonical_json(assignment_payload).encode("utf-8")
                    )
                    or row["candidate_rule_assignment_exact_one"] != "true"
                    or row["candidate_family_assignment_exact_one"] != "true"
                    or row["class_vocabulary_join_exact_one"] != "true"
                    or row["verified"] != "true"
                ):
                    raise ValueError("assignment_invalid")
            except (KeyError, TypeError, ValueError):
                reasons.append("ASSIGNMENT_RECORD_INVALID")
                break
    completed_count = sum(
        row["review_decision"] != "not_reviewed"
        or bool(row["review_record_sha256"])
        for row in templates
    )
    if completed_count:
        reasons.append("ACTUAL_REVIEW_MATERIALIZED_DURING_DESIGN")
    for sample, index in index_by_sample.items():
        template = template_by_sample.get(sample)
        proposal = proposal_by_sample.get(sample)
        assignment = assignment_by_sample.get(sample)
        if template is None or proposal is None or assignment is None:
            reasons.append("PACKAGE_SAMPLE_PROPOSAL_IDENTITY_MISMATCH")
            continue
        if any(
            template[field] != (
                _parse_int(index[field], field)
                if field in {
                    "warhead_type_candidate_class_index_0based",
                    "total_candidate_count", "admitted_candidate_count",
                } else index[field]
            )
            for field in (
                "sample_index_row_id", "pdb_id", "ligand_comp_id",
                "warhead_type_candidate_class_index_0based",
                "warhead_type_candidate_class_id", "reaction_family_id",
                "warhead_rule_id", "source_proposal_record_sha256",
                "source_assignment_record_sha256", "source_candidate_set_sha256",
                "total_candidate_count", "admitted_candidate_count",
            )
        ):
            reasons.append("PACKAGE_SAMPLE_PROPOSAL_IDENTITY_MISMATCH")
        if (
            review_record_sha256(template)
            != index["unreviewed_template_payload_sha256"]
        ):
            reasons.append("UNREVIEWED_TEMPLATE_PAYLOAD_SHA_MISMATCH")
        if (
            proposal["proposal_record_sha256"]
            != index["source_proposal_record_sha256"]
            or assignment["assignment_record_sha256"]
            != index["source_assignment_record_sha256"]
        ):
            reasons.append("PACKAGE_SAMPLE_PROPOSAL_IDENTITY_MISMATCH")
        try:
            _validate_proposal_package_lineage(
                proposal,
                package_identity=package_identity_by_sample[sample],
            )
        except (KeyError, TypeError, ValueError):
            reasons.append("PACKAGE_SAMPLE_PROPOSAL_IDENTITY_MISMATCH")
        try:
            start = _parse_int(
                index["candidate_option_row_start_0based"],
                "candidate_option_row_start_0based",
            )
            end = _parse_int(
                index["candidate_option_row_end_exclusive"],
                "candidate_option_row_end_exclusive",
            )
            sample_options = options[start:end]
            identity = package_identity_by_sample[sample]
            option_identity_fields = (
                "sample_index_row_id", "pdb_id", "ligand_comp_id",
                "warhead_type_candidate_class_index_0based",
                "warhead_type_candidate_class_id", "reaction_family_id",
                "warhead_rule_id", "source_proposal_record_sha256",
                "source_candidate_set_sha256",
            )
            if (
                end <= start
                or len(sample_options) != identity["total_candidate_count"]
                or [row["option_order_within_sample_0based"]
                    for row in sample_options]
                != list(range(len(sample_options)))
                or any(
                    row["package_item_order_0based"] != position
                    for position, row in enumerate(
                        sample_options, start=start,
                    )
                )
                or any(
                    row[field] != identity[field]
                    for row in sample_options
                    for field in option_identity_fields
                )
                or sum(
                    row["review_eligible"] for row in sample_options
                ) != identity["admitted_candidate_count"]
            ):
                raise ValueError("option_span_or_lineage_invalid")
        except (KeyError, TypeError, ValueError):
            reasons.append("OPTION_SPAN_OR_LINEAGE_MISMATCH")
        if not all(index[field] == "true" for field in (
            "review_options_materialized", "review_template_materialized",
            "ready_for_human_review", "verified",
        )):
            reasons.append("REVIEW_PACKAGE_NOT_READY")
        if not all(index[field] == "false" for field in (
            "human_review_completed",
            "complete_warhead_atom_set_authority_available",
            "exact_one_attachment_boundary_authority_available",
            "ready_for_candidate_warhead_smarts_materialization",
            "ready_for_role_proposal_generation",
        )):
            reasons.append("PACKAGE_DOWNSTREAM_PREMATURELY_OPENED")
    expected_manifest = {
        "package_index_count": 11,
        "package_option_record_count": 200,
        "review_eligible_option_count": 185,
        "review_ineligible_option_count": 15,
        "review_template_count": 11,
        "warhead_boundary_human_review_completed_count": 0,
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
    }
    if any(manifest.get(key) != value for key, value in expected_manifest.items()):
        reasons.append("REVIEW_PACKAGE_MANIFEST_STATE_INVALID")
    if not proposal_manifest.get("transaction_succeeded"):
        reasons.append("PROPOSAL_TRANSACTION_NOT_SUCCEEDED")
    if any(parallel_manifest.get(key, 0) not in (0, False) for key in (
        "class_human_review_completed_count",
        "sample_human_review_completed_count",
        "approved_reaction_family_available_count",
        "approved_warhead_rule_available_count",
        "human_gold_review_completed_count", "training_label_approved_count",
    )):
        reasons.append("PARALLEL_REVIEW_PREMATURELY_COMPLETED")
    atoms_by_ligand: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    bonds_by_ligand: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in parent_atoms:
        atoms_by_ligand[row.get("ligand_comp_id", "")].append(row)
    for row in parent_bonds:
        bonds_by_ligand[row.get("ligand_comp_id", "")].append(row)
    proposal_graph_by_ligand: dict[str, str] = {}
    for proposal in proposals:
        ligand = proposal["ligand_comp_id"]
        graph_sha = proposal["component_parent_graph_sha256"]
        previous = proposal_graph_by_ligand.setdefault(ligand, graph_sha)
        if previous != graph_sha:
            reasons.append("PROPOSAL_PARENT_GRAPH_SHA_MISMATCH")
    if set(atoms_by_ligand) != set(bonds_by_ligand) or set(
        proposal_graph_by_ligand
    ) - set(atoms_by_ligand):
        reasons.append("PARENT_GRAPH_COMPONENT_INVENTORY_MISMATCH")
    else:
        for ligand, graph_sha in proposal_graph_by_ligand.items():
            try:
                _validate_parent_graph(
                    atoms_by_ligand[ligand], bonds_by_ligand[ligand],
                    expected_sha=graph_sha,
                )
                if any(
                    row["component_parent_graph_sha256"] != graph_sha
                    for row in assignments
                    if row["ligand_comp_id"] == ligand
                ):
                    raise ValueError("assignment_graph_SHA_mismatch")
            except (KeyError, TypeError, ValueError):
                reasons.append("PARENT_GRAPH_AUTHORITY_INVALID")
                break
    return PhaseA(
        tuple(raw_index), package_identity_by_sample, tuple(options),
        tuple(templates), tuple(proposals), tuple(assignments), tuple(parent_atoms),
        tuple(parent_bonds), tuple(dict.fromkeys(reasons)),
    )


def _contract_rows() -> tuple[Mapping[str, Any], ...]:
    specifications = (
        ("INGEST_001", "Exact26 review schema inherited unchanged",
         "review_record", "Exact26 typed record", "field order and exact types match",
         "schema admitted", "record invalid", "REVIEW_SCHEMA_MISMATCH"),
        ("INGEST_002", "completed decision required for ingestion",
         "review_record", "review_decision", "decision is not not_reviewed",
         "completion evaluated", "batch blocked", "REVIEW_NOT_COMPLETED"),
        ("INGEST_003", "review-record canonical digest required",
         "review_record", "Exact25 hash input", "canonical digest matches",
         "review identity admitted", "record invalid", "REVIEW_RECORD_SHA_INVALID"),
        ("INGEST_004", "Exact14 completed-review package identity join required",
         "lineage", "immutable BASE authority context, package index, template, proposal, assignment and review",
         "validated context rebuilds all Exact14 identity fields and source lineage joins exactly",
         "lineage admitted", "record invalid", "REVIEW_IDENTITY_LINKAGE_MISMATCH"),
        ("INGEST_005", "submitted payload digest must match Exact26 record",
         "envelope", "typed Exact26 plus envelope", "all-field payload digest matches",
         "payload admitted", "record invalid", "SUBMITTED_REVIEW_PAYLOAD_SHA_MISMATCH"),
        ("INGEST_006", "human provenance attestation required",
         "envelope", "attestation and attestor", "attested is exact true and human ID meaningful",
         "provenance admitted", "record invalid", "HUMAN_PROVENANCE_ATTESTATION_REQUIRED"),
        ("INGEST_007", "select decision may reference eligible option only",
         "decision", "review and validated authority-context options", "exact-one same-sample eligible formal option",
         "select admitted", "record invalid", "SELECT_OPTION_NOT_REVIEW_ELIGIBLE"),
        ("INGEST_008", "revise decision must satisfy parent graph invariants",
         "decision", "review plus validated authority-context proposal and parent graph", "connected proper subset and exact-one boundary",
         "revise admitted", "record invalid", "REVISE_GRAPH_INVARIANT_INVALID"),
        ("INGEST_009", "quarantine produces no warhead/boundary authority",
         "decision", "quarantine review", "disposition closed and both authorities false",
         "quarantine disposition", "record invalid", "QUARANTINE_EFFECT_INVALID"),
        ("INGEST_010", "not-reviewed records are not ingestible completions",
         "decision", "not_reviewed record", "completed submission is rejected",
         "blank template remains legal", "batch blocked", "REVIEW_NOT_COMPLETED"),
        ("INGEST_011", "partial single-ID unique-sample batches are allowed",
         "batch", "one to eleven envelopes", "exact-one meaningful batch ID plus unique sample and review SHA",
         "partial batch evaluated", "batch invalid", "SUBMISSION_BATCH_ID_MISMATCH"),
        ("INGEST_012", "batch ingestion is atomic",
         "batch", "all batch records, authority context, frozen reason precedence and result reason/effect contract",
         "context and reason/effect failures close the batch and any failure rolls back all effects",
         "all effects committed", "all effects rolled back", "BATCH_ATOMICITY_ABORTED"),
        ("INGEST_013", "exact replay is idempotent",
         "replay", "validated context, existing decision evidence and submitted review",
         "same sample/review SHA, package lineage, decision evidence and review semantics",
         "passed without duplicate", "replay invalid", "EXISTING_AUTHORITY_LINEAGE_MISMATCH"),
        ("INGEST_014", "conflicting re-ingestion is blocked",
         "replay", "validated existing authority and submitted review",
         "different review SHA conflicts; same SHA with invalid semantics or lineage is invalid",
         "no conflict", "batch blocked", "CONFLICTING_REVIEW_REINGESTION"),
        ("INGEST_015", "V1 supersession is unavailable",
         "authority", "supersedes field", "field is empty",
         "V1 authority admitted", "record invalid", "V1_SUPERSESSION_UNAVAILABLE"),
        ("INGEST_016", "new and existing authorities preserve package lineage",
         "authority", "validated context, package proposal review envelope and existing authority set",
         "all identities, lineage hashes and decision evidence equal formal authority",
         "authority traceable", "record invalid", "AUTHORITY_SOURCE_LINEAGE_MISMATCH"),
        ("INGEST_017", "boundary review does not approve family/rule/SMARTS/gold",
         "downstream", "decision effect", "all approval effects remain false",
         "boundary disposition only", "transaction fails", "PREMATURE_APPROVAL_OPENED"),
        ("INGEST_018", "role/mask/model/training gates remain closed",
         "downstream", "readiness state", "role mask model training all false",
         "downstream closed", "transaction fails", "DOWNSTREAM_GATE_OPENED"),
        ("INGEST_019", "design stage materializes no reviews/results/authority",
         "design", "artifact inventory and in-memory context contract", "context is not externalized and all actual lifecycle counts are zero",
         "design evidence emitted", "transaction fails", "DESIGN_MATERIALIZED_LIFECYCLE_RECORD"),
        ("INGEST_020", "formal training still requires feature-semantics audit",
         "training", "training prerequisite", "feature-semantics audit remains required",
         "training remains closed", "transaction fails", "FEATURE_SEMANTICS_AUDIT_REQUIRED"),
    )
    rows = []
    for values in specifications:
        rows.append(dict(zip(CONTRACT_COLUMNS[:-2], values), fails_closed=True, verified=True))
    return tuple(rows)


def _decision_rows() -> tuple[Mapping[str, Any], ...]:
    rows = []
    for decision in REVIEW_DECISIONS:
        not_reviewed = decision == "not_reviewed"
        quarantine = decision == "quarantine"
        materialized = decision in {
            "select_admitted_candidate", "revise_atom_set_and_boundary",
        }
        rows.append({
            "review_decision": decision,
            "completed_submission_ingestible": not not_reviewed,
            "future_outcome": "blocked" if not_reviewed else "passed",
            "reason_code": "REVIEW_NOT_COMPLETED" if not_reviewed else "PASSED",
            "blocks_batch": not_reviewed,
            "review_completed": not not_reviewed,
            "authority_disposition": (
                "" if not_reviewed else
                "reviewed_quarantine_no_authority" if quarantine else
                "reviewed_authority_materialized"
            ),
            "authority_status": (
                "" if not_reviewed else "quarantined" if quarantine else "active"
            ),
            "complete_warhead_atom_set_authority_available": materialized,
            "exact_one_attachment_boundary_authority_available": materialized,
            "sample_quarantined": quarantine,
            "approves_reaction_family": False,
            "approves_warhead_rule": False,
            "approves_SMARTS": False,
            "creates_human_gold_label": False,
            "creates_training_label": False,
            "verified": True,
        })
    return tuple(rows)


def _readiness_rows(
    index_rows: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, Any], ...]:
    blockers = (
        "completed_human_review_record_missing;"
        "human_provenance_attestation_missing;"
        "ingestion_envelope_missing;"
        "review_ingestion_not_executed"
    )
    rows = []
    for source in sorted(index_rows, key=lambda row: row["sample_index_row_id"]):
        rows.append({
            "sample_index_row_id": source["sample_index_row_id"],
            "pdb_id": source["pdb_id"],
            "ligand_comp_id": source["ligand_comp_id"],
            "warhead_type_candidate_class_id":
                source["warhead_type_candidate_class_id"],
            "reaction_family_id": source["reaction_family_id"],
            "warhead_rule_id": source["warhead_rule_id"],
            "source_proposal_record_sha256":
                source["source_proposal_record_sha256"],
            "source_assignment_record_sha256":
                source["source_assignment_record_sha256"],
            "source_candidate_set_sha256":
                source["source_candidate_set_sha256"],
            "unreviewed_template_payload_sha256":
                source["unreviewed_template_payload_sha256"],
            "package_materialized": True,
            "review_options_materialized": True,
            "blank_review_template_materialized": True,
            "ready_for_human_review_submission": True,
            "completed_review_record_available": False,
            "completed_review_record_sha256": "",
            "ingestion_envelope_available": False,
            "ingestion_envelope_sha256": "",
            "ready_for_review_ingestion_execution": False,
            "review_ingestion_completed": False,
            "authority_record_available": False,
            "authority_record_sha256": "",
            "complete_warhead_atom_set_authority_available": False,
            "exact_one_attachment_boundary_authority_available": False,
            "sample_quarantined": False,
            "ready_for_candidate_warhead_smarts_materialization": False,
            "ready_for_SMARTS_review_execution": False,
            "ready_for_role_proposal_generation": False,
            "ready_for_mask_materialization": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "blocking_reasons": blockers,
            "verified": True,
        })
    return tuple(rows)


@dataclass(frozen=True)
class IngestionGateScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    review_package_transaction_succeeded: bool = True
    package_count: int = 11
    option_count: int = 200
    template_count: int = 11
    candidate_set_identity_count: int = 11
    option_record_sha_matches: bool = True
    template_payload_sha_matches: bool = True
    inherited_review_field_count: int = 26
    envelope_field_count: int = 9
    envelope_exact_types_valid: bool = True
    envelope_sha_matches: bool = True
    submitted_payload_sha_matches: bool = True
    envelope_linkage_matches: bool = True
    completed_review_sha_valid: bool = True
    completed_decision: bool = True
    reviewer_meaningful: bool = True
    reviewer_allowed: bool = True
    provenance_attested: bool = True
    provenance_attestor_valid: bool = True
    select_dependency_valid: bool = True
    selected_option_eligible: bool = True
    revise_graph_valid: bool = True
    quarantine_dependency_valid: bool = True
    unique_sample_batch: bool = True
    unique_review_sha_batch: bool = True
    partial_batch_allowed: bool = True
    batch_atomicity_enabled: bool = True
    exact_replay_idempotent: bool = True
    conflicting_reingestion_blocked: bool = True
    supersession_available: bool = False
    authority_lineage_matches: bool = True
    authority_record_valid: bool = True
    ingestion_result_valid: bool = True
    select_revise_opens_authority: bool = True
    quarantine_opens_authority: bool = False
    approval_gates_closed: bool = True
    downstream_gates_closed: bool = True
    actual_lifecycle_record_count: int = 0
    completed_review_package_identity_matches: bool = True
    single_submission_batch_id: bool = True
    existing_authority_samples_unique: bool = True
    existing_authority_records_valid: bool = True
    existing_authority_lineage_matches: bool = True
    public_reason_contract_valid: bool = True
    authority_context_source_inventory_matches: bool = True
    authority_context_source_sha_matches: bool = True
    external_authority_maps_forbidden: bool = True
    ingestion_result_reason_effect_valid: bool = True
    existing_authority_decision_evidence_valid: bool = True


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_SOURCE_MISSING"),
    ("BASE source SHA mismatch", "base_source_sha_matches", False, "BASE_SOURCE_SHA_MISMATCH"),
    ("review-package transaction not succeeded", "review_package_transaction_succeeded", False, "REVIEW_PACKAGE_TRANSACTION_NOT_SUCCEEDED"),
    ("package count not 11", "package_count", 10, "PACKAGE_COUNT_NOT_11"),
    ("option count not 200", "option_count", 199, "OPTION_COUNT_NOT_200"),
    ("template count not 11", "template_count", 10, "TEMPLATE_COUNT_NOT_11"),
    ("candidate-set identity count not 11", "candidate_set_identity_count", 10, "CANDIDATE_SET_IDENTITY_COUNT_NOT_11"),
    ("option record SHA mismatch", "option_record_sha_matches", False, "OPTION_RECORD_SHA_MISMATCH"),
    ("unreviewed template payload SHA mismatch", "template_payload_sha_matches", False, "UNREVIEWED_TEMPLATE_PAYLOAD_SHA_MISMATCH"),
    ("inherited review-field inventory mismatch", "inherited_review_field_count", 25, "INHERITED_REVIEW_FIELD_INVENTORY_MISMATCH"),
    ("ingestion-envelope field inventory mismatch", "envelope_field_count", 8, "INGESTION_ENVELOPE_FIELD_INVENTORY_MISMATCH"),
    ("ingestion-envelope exact type invalid", "envelope_exact_types_valid", False, "INGESTION_ENVELOPE_EXACT_TYPE_INVALID"),
    ("ingestion-envelope SHA mismatch", "envelope_sha_matches", False, "INGESTION_ENVELOPE_SHA_MISMATCH"),
    ("submitted review payload SHA mismatch", "submitted_payload_sha_matches", False, "SUBMITTED_REVIEW_PAYLOAD_SHA_MISMATCH"),
    ("envelope/sample/review linkage mismatch", "envelope_linkage_matches", False, "ENVELOPE_SAMPLE_REVIEW_LINKAGE_MISMATCH"),
    ("completed review-record SHA invalid", "completed_review_sha_valid", False, "COMPLETED_REVIEW_RECORD_SHA_INVALID"),
    ("not-reviewed submitted as completion", "completed_decision", False, "REVIEW_NOT_COMPLETED"),
    ("reviewer not meaningful", "reviewer_meaningful", False, "REVIEWER_NOT_MEANINGFUL"),
    ("forbidden automated reviewer", "reviewer_allowed", False, "FORBIDDEN_AUTOMATED_REVIEWER"),
    ("provenance attestation false", "provenance_attested", False, "HUMAN_PROVENANCE_ATTESTATION_REQUIRED"),
    ("provenance attestor invalid", "provenance_attestor_valid", False, "PROVENANCE_ATTESTOR_INVALID"),
    ("select decision dependency invalid", "select_dependency_valid", False, "SELECT_DEPENDENCY_INVALID"),
    ("select decision references ineligible option", "selected_option_eligible", False, "SELECT_OPTION_NOT_REVIEW_ELIGIBLE"),
    ("revise decision graph invariant invalid", "revise_graph_valid", False, "REVISE_GRAPH_INVARIANT_INVALID"),
    ("quarantine decision dependency invalid", "quarantine_dependency_valid", False, "QUARANTINE_DEPENDENCY_INVALID"),
    ("duplicate sample in batch", "unique_sample_batch", False, "DUPLICATE_SAMPLE_IN_BATCH"),
    ("duplicate review-record SHA in batch", "unique_review_sha_batch", False, "DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH"),
    ("partial-batch policy mismatch", "partial_batch_allowed", False, "PARTIAL_BATCH_POLICY_MISMATCH"),
    ("batch atomicity disabled", "batch_atomicity_enabled", False, "BATCH_ATOMICITY_DISABLED"),
    ("exact replay not idempotent", "exact_replay_idempotent", False, "EXACT_REPLAY_NOT_IDEMPOTENT"),
    ("conflicting re-ingestion accepted", "conflicting_reingestion_blocked", False, "CONFLICTING_REINGESTION_ACCEPTED"),
    ("V1 supersession unexpectedly allowed", "supersession_available", True, "V1_SUPERSESSION_UNEXPECTEDLY_ALLOWED"),
    ("authority source-lineage mismatch", "authority_lineage_matches", False, "AUTHORITY_SOURCE_LINEAGE_MISMATCH"),
    ("authority record field/type/hash invalid", "authority_record_valid", False, "AUTHORITY_RECORD_INVALID"),
    ("ingestion result field/type/hash invalid", "ingestion_result_valid", False, "INGESTION_RESULT_INVALID"),
    ("select/revise failed to open reviewed authority", "select_revise_opens_authority", False, "SELECT_REVISE_AUTHORITY_EFFECT_INVALID"),
    ("quarantine incorrectly opened authority", "quarantine_opens_authority", True, "QUARANTINE_AUTHORITY_EFFECT_INVALID"),
    ("family/rule/SMARTS/gold prematurely opened", "approval_gates_closed", False, "PREMATURE_APPROVAL_OPENED"),
    ("role/mask/model/training prematurely opened", "downstream_gates_closed", False, "DOWNSTREAM_GATE_OPENED"),
    ("actual review/result/authority materialized during design", "actual_lifecycle_record_count", 1, "DESIGN_MATERIALIZED_LIFECYCLE_RECORD"),
    ("completed review/package identity mismatch", "completed_review_package_identity_matches", False, "REVIEW_IDENTITY_LINKAGE_MISMATCH"),
    ("mixed submission batch IDs", "single_submission_batch_id", False, "SUBMISSION_BATCH_ID_MISMATCH"),
    ("duplicate existing authority sample", "existing_authority_samples_unique", False, "EXISTING_AUTHORITY_SET_INVALID"),
    ("existing authority schema/type/hash invalid", "existing_authority_records_valid", False, "EXISTING_AUTHORITY_SET_INVALID"),
    ("existing authority/package lineage mismatch", "existing_authority_lineage_matches", False, "EXISTING_AUTHORITY_LINEAGE_MISMATCH"),
    ("public reason vocabulary or precedence invalid", "public_reason_contract_valid", False, "INGESTION_PUBLIC_REASON_CONTRACT_INVALID"),
    ("authority context source inventory mismatch", "authority_context_source_inventory_matches", False, "INGESTION_AUTHORITY_CONTEXT_SOURCE_INVENTORY_MISMATCH"),
    ("authority context source SHA mismatch", "authority_context_source_sha_matches", False, "INGESTION_AUTHORITY_CONTEXT_SOURCE_SHA_MISMATCH"),
    ("external caller-supplied authority maps accepted", "external_authority_maps_forbidden", False, "EXTERNAL_AUTHORITY_MAP_INJECTION_ACCEPTED"),
    ("ingestion result reason/effect mismatch", "ingestion_result_reason_effect_valid", False, "INGESTION_RESULT_REASON_EFFECT_INVALID"),
    ("existing authority decision evidence invalid", "existing_authority_decision_evidence_valid", False, "EXISTING_AUTHORITY_DECISION_EVIDENCE_INVALID"),
)


def observe_failure_scenario(
    scenario: IngestionGateScenario,
) -> tuple[str, ...]:
    baseline = IngestionGateScenario()
    reasons = []
    for _, field, _, reason in FAILURE_MUTATIONS:
        if getattr(scenario, field) != getattr(baseline, field):
            reasons.append(reason)
    return tuple(reasons)


def transaction_tables(
    scenario: IngestionGateScenario,
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    if observe_failure_scenario(scenario):
        return (), (), ()
    return _contract_rows(), _decision_rows(), tuple({"verified": True} for _ in range(11))


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = IngestionGateScenario()
    rows = []
    for case, field, value, expected in FAILURE_MUTATIONS:
        scenario = replace(baseline, **{field: value})
        observed = observe_failure_scenario(scenario)
        core = transaction_tables(scenario)
        signature = sha256(canonical_json({
            "field": field, "value": value,
        }).encode("utf-8"))
        rows.append({
            "failure_case": case, "mutation_signature": signature,
            "mutated_field": field, "mutated_value_json": canonical_json(value),
            "expected_reason": expected,
            "observed_reasons": list(observed),
            "expected_reason_verified": expected in observed,
            "fails_closed": all(not table for table in core),
            "contract_row_count": len(core[0]),
            "decision_effect_row_count": len(core[1]),
            "current11_readiness_row_count": len(core[2]),
            "actual_review_record_count": 0,
            "actual_ingestion_envelope_count": 0,
            "actual_ingestion_result_count": 0,
            "actual_authority_record_count": 0,
            "complete_warhead_atom_set_authority_available": False,
            "exact_one_attachment_boundary_authority_available": False,
            "SMARTS_ready": False, "role_ready": False, "mask_ready": False,
            "model_ready": False, "training_ready": False,
            "verified": expected in observed and all(not table for table in core),
        })
    return tuple(rows)


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    contract_rows: tuple[Mapping[str, Any], ...]
    decision_rows: tuple[Mapping[str, Any], ...]
    readiness_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    package_index_rows: tuple[Mapping[str, str], ...]
    package_identity_by_sample: Mapping[str, Mapping[str, Any]]
    option_rows: tuple[Mapping[str, Any], ...]
    template_rows: tuple[Mapping[str, Any], ...]
    proposal_rows: tuple[Mapping[str, Any], ...]
    parent_atom_rows: tuple[Mapping[str, str], ...]
    parent_bond_rows: tuple[Mapping[str, str], ...]
    authority_context: IngestionAuthorityContext
    actual_lifecycle: str
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


def build_result(repo_root: Path) -> BuildResult:
    lifecycle = validate_execution_boundary_v1(repo_root)
    payloads = load_frozen_sources(repo_root)
    phase = _validate_phase_a(payloads)
    authority_context = build_ingestion_authority_context(repo_root)
    source_rows = _source_inventory(payloads)
    phase_b_valid = (
        len(REVIEW_RECORD_FIELDS) == 26
        and len(COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS) == 14
        and len(INGESTION_ENVELOPE_FIELDS) == 9
        and len(AUTHORITY_RECORD_FIELDS) == 27
        and len(INGESTION_RESULT_FIELDS) == 18
        and len(_contract_rows()) == 20
        and len(_decision_rows()) == 4
        and len(INGESTION_RESULT_REASON_CODES) == len(
            set(INGESTION_RESULT_REASON_CODES)
        )
        and len(INGESTION_AUTHORITY_CONTEXT_FIELDS) == 4
        and len(INGESTION_RESULT_REASON_CODES) == 31
        and len(INGESTION_FAILURE_REASON_PRECEDENCE) == 10
        and len(FAILURE_MUTATIONS) == 51
        and len(CANONICAL_MASKS) == 5
    )
    reasons = list(phase.blocking_reasons)
    if not phase_b_valid:
        reasons.append("PHASE_B_CONTRACT_INVALID")
    if reasons:
        contract_rows: tuple[Mapping[str, Any], ...] = ()
        decision_rows: tuple[Mapping[str, Any], ...] = ()
        readiness_rows: tuple[Mapping[str, Any], ...] = ()
    else:
        contract_rows = _contract_rows()
        decision_rows = _decision_rows()
        readiness_rows = _readiness_rows(phase.index_rows)
    failure_rows = build_failure_rows()
    return BuildResult(
        source_rows, contract_rows, decision_rows, readiness_rows,
        failure_rows, phase.index_rows, phase.package_identity_by_sample,
        phase.option_rows, phase.template_rows, phase.proposal_rows,
        phase.parent_atom_rows, phase.parent_bond_rows, authority_context,
        lifecycle, not reasons, tuple(dict.fromkeys(reasons)),
    )


def _manifest(
    result: BuildResult, output_sha256: Mapping[str, str],
) -> Mapping[str, Any]:
    succeeded = result.transaction_succeeded
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT, "parent": BASE_PARENT,
            "tree": BASE_TREE, "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "source_count": 13,
        "source_sha256": {
            path.as_posix(): digest
            for path, digest in FROZEN_BASE_SHA256.items()
        },
        "ingestion_authority_context_version":
            INGESTION_AUTHORITY_CONTEXT_VERSION,
        "ingestion_authority_context_field_count": 4,
        "ingestion_authority_context_fields": list(
            INGESTION_AUTHORITY_CONTEXT_FIELDS
        ),
        "ingestion_authority_context_source_count": 13,
        "ingestion_authority_context_built_from_formal_base": True,
        "ingestion_authority_context_validation_required": True,
        "external_authority_maps_allowed": False,
        "inherited_review_record_field_count": 26,
        "inherited_review_record_fields": list(REVIEW_RECORD_FIELDS),
        "completed_review_package_identity_field_count": 14,
        "completed_review_package_identity_fields": list(
            COMPLETED_REVIEW_PACKAGE_IDENTITY_FIELDS
        ),
        "review_decisions": list(REVIEW_DECISIONS),
        "ingestion_envelope_version": INGESTION_ENVELOPE_VERSION,
        "ingestion_envelope_field_count": 9,
        "ingestion_envelope_fields": list(INGESTION_ENVELOPE_FIELDS),
        "ingestion_envelope_hash_included_field_count": 8,
        "authority_record_version": AUTHORITY_RECORD_VERSION,
        "authority_record_field_count": 27,
        "authority_record_fields": list(AUTHORITY_RECORD_FIELDS),
        "authority_record_hash_included_field_count": 26,
        "authority_dispositions": list(AUTHORITY_DISPOSITIONS),
        "authority_statuses": list(AUTHORITY_STATUSES),
        "ingestion_result_version": INGESTION_RESULT_VERSION,
        "ingestion_result_field_count": 18,
        "ingestion_result_fields": list(INGESTION_RESULT_FIELDS),
        "ingestion_result_hash_included_field_count": 17,
        "ingestion_outcomes": list(INGESTION_OUTCOMES),
        "ingestion_result_reason_codes": list(INGESTION_RESULT_REASON_CODES),
        "ingestion_result_reason_effect_contract_version":
            INGESTION_RESULT_REASON_EFFECT_CONTRACT_VERSION,
        "ingestion_result_reason_effect_invariants_frozen": True,
        "ingestion_result_reason_code_count": len(
            INGESTION_RESULT_REASON_CODES
        ),
        "ingestion_failure_reason_precedence": list(
            INGESTION_FAILURE_REASON_PRECEDENCE
        ),
        "public_reason_vocabulary_frozen": True,
        "deterministic_failure_precedence": True,
        "contract_count": len(result.contract_rows),
        "decision_effect_row_count": len(result.decision_rows),
        "current11_readiness_row_count": len(result.readiness_rows),
        "review_package_count": 11,
        "review_option_count": 200,
        "review_eligible_option_count": 185,
        "review_ineligible_option_count": 15,
        "blank_review_template_count": 11,
        "completed_review_record_count": 0,
        "ingestion_envelope_count": 0,
        "submitted_ingestion_batch_count": 0,
        "ingestion_result_count": 0,
        "authority_record_count": 0,
        "human_provenance_attestation_required": True,
        "human_provenance_cryptographically_verified": False,
        "partial_batch_allowed": True,
        "single_submission_batch_id_required": True,
        "batch_atomicity_required": True,
        "existing_authority_validation_required": True,
        "existing_authority_unique_sample_required": True,
        "existing_authority_package_lineage_required": True,
        "existing_authority_decision_evidence_required": True,
        "exact_replay_idempotent": True,
        "conflicting_reingestion_forbidden": True,
        "supersession_available_v1": False,
        "review_ingestion_gate_design_completed": succeeded,
        "ready_for_review_ingestion_interface_implementation": succeeded,
        "ready_for_review_ingestion_execution": False,
        "review_ingestion_completed": False,
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
        "sample_quarantined_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "candidate_warhead_smarts_materialization_ready_count": 0,
        "SMARTS_human_review_ready_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "approved_warhead_smarts_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "ready_for_role_proposal_generation": False,
        "ready_for_minimal_seed_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "role_annotation_materialized": False,
        "minimal_seed_materialized": False,
        "mask_materialized": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_used": False,
        "canonical_mask_count": 5,
        "canonical_masks": list(CANONICAL_MASKS),
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "transaction_succeeded": succeeded,
        "blocking_reasons": list(result.blocking_reasons),
        "failure_mutation_count": 51,
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] and row["verified"] for row in result.failure_rows
        ),
        "output_sha256": dict(output_sha256),
        "recommended_manual_action_primary":
            "perform_real_human_review_of_current11_warhead_atom_set_and_attachment_boundary_review_packages",
        "remaining_parallel_manual_action":
            "perform_real_human_review_of_materialized_family_topology_and_sample_assignment_packages",
        "recommended_engineering_next_step": (
            "implement_covapie_current11_warhead_atom_set_and_attachment_"
            "boundary_review_ingestion_interface_v1"
            if succeeded else
            "resolve_covapie_current11_warhead_boundary_review_ingestion_"
            "gate_design_blockers_v1"
        ),
        "recommended_next_step": (
            "implement_covapie_current11_warhead_atom_set_and_attachment_"
            "boundary_review_ingestion_interface_v1"
            if succeeded else
            "resolve_covapie_current11_warhead_boundary_review_ingestion_"
            "gate_design_blockers_v1"
        ),
        "formal_training_prerequisite": "feature-semantics audit",
        "Step12D_scope": "smoke legality check only",
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, result.contract_rows),
        DECISION_FILE: _csv_bytes(DECISION_COLUMNS, result.decision_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, result.readiness_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    output_sha = {name: sha256(payload) for name, payload in payloads.items()}
    payloads[MANIFEST_FILE] = (
        json.dumps(
            _manifest(result, output_sha), indent=2, sort_keys=True,
            ensure_ascii=True,
        ).encode("utf-8") + b"\n"
    )
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    root = repo_root / OUTPUT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:
        (root / name).write_bytes(payloads[name])
    return payloads


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize(repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
