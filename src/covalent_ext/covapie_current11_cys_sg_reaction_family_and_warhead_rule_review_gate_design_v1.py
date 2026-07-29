"""Design the Current11 Cys-SG reaction-family and warhead-rule review gate.

This stage freezes review schemas, policies, dependencies, and readiness only.
It never performs review, invents reviewers or SMARTS, approves labels, assigns
ligand roles, materializes masks/tensors, changes models, or performs training.
"""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASE_COMMIT = "0c8d1d10260a028360357b8c309f22676fc81645"
BASE_PARENT = "dc1222503dcec83220a28df2abdae898a0855864"
BASE_TREE = "5d1ddb25404e55858001267135536450428dfb25"
BASE_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule assignments v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review gate "
    "design v1"
)
SCHEMA_VERSION = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1"
)
REVIEW_RECORD_VERSION = "covapie_cys_sg_human_review_record_v1"
REVIEW_UNIT_TYPES = ("candidate_class", "sample_assignment")
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION

HUMAN_REVIEW_DECISIONS = ("not_reviewed", "approve", "revise", "quarantine")
SMARTS_REVIEW_STATUSES = (
    "not_materialized",
    "candidate_not_reviewed",
    "approved",
    "revised",
    "quarantined",
)
SMARTS_UNREVIEWED_STATUSES = ("not_materialized", "candidate_not_reviewed")
SMARTS_HUMAN_REVIEWED_STATUSES = ("approved", "revised", "quarantined")
DESIGN_DECISION = "not_reviewed"
DESIGN_SMARTS_STATUS = "not_materialized"

ASSIGNMENT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
)
ASSIGNMENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1"
)
CLASS_VOCABULARY = (
    ASSIGNMENT_ROOT / "covapie_cys_sg_warhead_type_candidate_class_vocabulary.csv"
)
ASSIGNMENT_AUTHORITY = (
    ASSIGNMENT_ROOT / "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
ASSIGNMENT_READINESS = (
    ASSIGNMENT_ROOT / "covapie_current11_cys_sg_assignment_review_readiness_matrix.csv"
)
ASSIGNMENT_MANIFEST = (
    ASSIGNMENT_ROOT
    / "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_manifest.json"
)
REGISTRY_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1"
)
FAMILY_REGISTRY = REGISTRY_ROOT / "covapie_cys_sg_reaction_family_registry.csv"
RULE_REGISTRY = REGISTRY_ROOT / "covapie_cys_sg_warhead_rule_registry.csv"
DESIGN_MATRIX = (
    REGISTRY_ROOT / "covapie_current11_reaction_family_and_warhead_rule_design_matrix.csv"
)
REGISTRY_MANIFEST = (
    REGISTRY_ROOT
    / "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_manifest.json"
)
ROLE_CONTRACT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
ATOM_MAPPING = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)

FROZEN_BASE_SHA256 = {
    ASSIGNMENT_SOURCE:
        "fe6c67940efef89290b2f276f9fb4c39245468181d52b219951a6f9ca7f454aa",
    CLASS_VOCABULARY:
        "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    ASSIGNMENT_AUTHORITY:
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    ASSIGNMENT_READINESS:
        "3405eb96ae610315a0a6f607267a2c2522fb2c1debec5f492c787d4e11e4d474",
    ASSIGNMENT_MANIFEST:
        "5e5acefc9051fc07d3243917292f073fc09fb432a0eb0325fa8d344d37c0e265",
    FAMILY_REGISTRY:
        "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    RULE_REGISTRY:
        "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    DESIGN_MATRIX:
        "24ae0fbd2dc1454574d9ed17145ba71d3b3132ffecfb84a1a831eceb77efab03",
    REGISTRY_MANIFEST:
        "4603d124e2f90616ebf7d28975e0eeb77e3d4c90133688d87df2e30c9ac54ef9",
    ROLE_CONTRACT_SOURCE:
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    ATOM_MAPPING:
        "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    FINAL_INDEX:
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
}
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)

SOURCE_FILE = "covapie_review_gate_design_source_inventory.csv"
POLICY_FILE = "covapie_reaction_family_and_warhead_rule_review_policy_registry.csv"
CLASS_FILE = "covapie_cys_sg_candidate_class_review_readiness_matrix.csv"
SAMPLE_FILE = "covapie_current11_candidate_assignment_review_readiness_matrix.csv"
FAILURE_FILE = "covapie_reaction_family_and_warhead_rule_review_gate_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
    "design_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    POLICY_FILE,
    CLASS_FILE,
    SAMPLE_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
EXACT10_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
        "design_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
        "gate_design_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
        "gate_design_v1.py"
    ),
    Path(
        "docs/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
        "design_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)

SOURCE_COLUMNS = (
    "source_path",
    "BASE_SHA256",
    "source_row_count",
    "Current11_coverage",
    "fields_actually_used",
    "authority_class",
    "verified",
)
POLICY_COLUMNS = (
    "policy_id",
    "semantic_name",
    "review_scope",
    "preconditions",
    "approval_effect",
    "failure_effect",
    "reason_code",
    "fails_closed",
    "verified",
)
CLASS_COLUMNS = (
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "warhead_type_candidate_semantic_name",
    "reaction_family_id",
    "reaction_family_semantic_name",
    "canonical_reaction_family_signature_sha256",
    "warhead_rule_id",
    "canonical_local_graph_rule_sha256",
    "selected_signature_radius",
    "Current11_match_count",
    "Current11_unique_component_count",
    "representative_sample_ids",
    "representative_component_ids",
    "family_identity_evidence_complete",
    "rule_topology_evidence_complete",
    "assignment_support_complete",
    "class_identity_verified",
    "reaction_family_identity_review_decision",
    "warhead_rule_topology_review_decision",
    "warhead_smarts_review_status",
    "candidate_warhead_smarts",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "class_review_package_ready",
    "family_identity_review_completed",
    "rule_topology_review_completed",
    "warhead_rule_topology_review_passed",
    "approved_reaction_family_available",
    "approved_warhead_rule_available",
    "ready_for_sample_assignment_review",
    "ready_for_role_proposal_generation",
    "ready_for_training",
    "blocking_reasons",
    "verified",
)
SAMPLE_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "assignment_record_sha256",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "target_residue_name",
    "target_residue_number",
    "target_residue_atom_name",
    "ligand_reactive_atom_name",
    "component_parent_graph_sha256",
    "observed_graph_sha256",
    "radius_1_signature_sha256",
    "class_review_package_ready",
    "sample_assignment_evidence_complete",
    "sample_assignment_identity_verified",
    "sample_assignment_review_decision",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "sample_review_package_ready",
    "sample_review_completed",
    "approved_reaction_family_available",
    "approved_warhead_rule_available",
    "human_gold_review_completed",
    "training_label_approved",
    "ready_for_role_proposal_generation",
    "ready_for_minimal_seed_proposal_generation",
    "ready_for_mask_materialization",
    "ready_for_tensorization",
    "ready_for_model_integration",
    "ready_for_training",
    "blocking_reasons",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case",
    "mutation_signature",
    "mutated_field",
    "mutated_value_json",
    "expected_reason",
    "observed_reasons",
    "expected_reason_verified",
    "fails_closed",
    "review_policy_registry_row_count",
    "candidate_class_review_readiness_row_count",
    "sample_assignment_review_readiness_row_count",
    "role_proposal_generation_ready",
    "mask_materialization_ready",
    "model_integration_ready",
    "training_ready",
    "verified",
)

CLASS_REVIEW_RECORD_FIELDS = (
    "review_record_version",
    "review_unit_type",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "reaction_family_semantic_name",
    "canonical_reaction_family_signature_sha256",
    "warhead_rule_id",
    "warhead_type_candidate_semantic_name",
    "canonical_local_graph_rule_sha256",
    "reaction_family_identity_review_decision",
    "warhead_rule_topology_review_decision",
    "warhead_smarts_review_status",
    "candidate_warhead_smarts",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "source_class_record_sha256",
    "review_record_sha256",
)
SAMPLE_REVIEW_RECORD_FIELDS = (
    "review_record_version",
    "review_unit_type",
    "sample_index_row_id",
    "assignment_record_sha256",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "sample_assignment_review_decision",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "source_assignment_record_sha256",
    "review_record_sha256",
)

# ``source_class_record_sha256`` is the identity of the frozen class-package
# record that a future review-package materialization stage will construct.  At
# this design stage only its field presence, exact type, SHA format, and review
# record hash behavior are frozen; no source class identities are invented.
_LOWER_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_FORBIDDEN_REVIEWER_IDS = frozenset(
    {
        "codex",
        "chatgpt",
        "auto",
        "system",
        "synthetic",
        "placeholder",
        "unknown",
        "none",
    }
)
_CLASS_SHA_FIELDS = (
    "canonical_reaction_family_signature_sha256",
    "canonical_local_graph_rule_sha256",
    "source_class_record_sha256",
)
_SAMPLE_SHA_FIELDS = (
    "assignment_record_sha256",
    "source_assignment_record_sha256",
)

POLICY_DEFINITIONS = (
    ("candidate identity is not approval", "class_and_sample",
     "candidate identity verified", "review package may open",
     "all approval readiness remains closed", "candidate_identity_is_not_approval"),
    ("family identity requires explicit human approval", "family",
     "identity unchanged; reviewer and rationale present; decision approve",
     "approved reaction family becomes available",
     "family availability remains false", "family_human_approval_missing"),
    ("topology rule approval is separate from SMARTS approval", "rule_topology",
     "topology decision approve", "topology pass may be recorded only",
     "approved warhead rule remains false", "topology_is_not_SMARTS_approval"),
    ("approved warhead rule requires approved SMARTS", "warhead_rule",
     "family and topology approved; approved SMARTS passes all checks",
     "approved warhead rule becomes available",
     "rule availability remains false", "approved_SMARTS_missing"),
    ("SMARTS must match exact-one atom set", "warhead_SMARTS",
     "SMARTS match count equals one", "SMARTS match-count condition passes",
     "rule availability remains false", "SMARTS_match_not_exact_one"),
    ("SMARTS must include known reactive ligand atom", "warhead_SMARTS",
     "unique match contains known reactive ligand atom",
     "reactive-atom condition passes", "rule availability remains false",
     "SMARTS_excludes_reactive_atom"),
    ("warhead attachment boundary must be exact-one", "warhead_SMARTS",
     "nonempty warhead atom set has exactly one attachment boundary",
     "boundary condition passes", "rule availability remains false",
     "warhead_attachment_boundary_not_exact_one"),
    ("sample assignment requires independent sample review", "sample",
     "sample decision approve; reviewer and rationale present",
     "sample review may complete", "sample gold remains false",
     "sample_independent_review_missing"),
    ("quarantine overrides downstream readiness", "class_and_sample",
     "no linked class/rule/sample is quarantined",
     "dependency evaluation may continue",
     "all downstream readiness closes", "quarantine_overrides_readiness"),
    ("gold requires approved family rule and sample assignment", "sample_gold",
     "family and rule available; sample approved; assignment identity unchanged",
     "human gold review completes", "human gold remains false",
     "gold_dependencies_incomplete"),
    ("role proposal requires approved family rule and gold sample", "role",
     "family available; rule available; human gold complete",
     "role proposal generation becomes ready",
     "role proposal generation remains false", "role_dependencies_incomplete"),
    ("training approval remains a separate future gate", "training",
     "independent future training-label gate approves",
     "training label may become approved in a later stage",
     "training label and training readiness remain false",
     "independent_training_gate_missing"),
)

ASSIGNMENT_HASH_FIELDS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "target_residue_name",
    "target_residue_number",
    "target_residue_atom_name",
    "ligand_reactive_atom_name",
    "ligand_reactive_atom_element",
    "ligand_reactive_parent_ccd_atom_id",
    "component_parent_graph_sha256",
    "observed_graph_sha256",
    "radius_1_signature_sha256",
    "candidate_reaction_family_id",
    "candidate_warhead_rule_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "assignment_status",
    "review_status",
    "training_label_status",
)

CLASS_BLOCKERS = (
    "reaction_family_identity_review_not_completed",
    "warhead_rule_topology_review_not_completed",
    "approved_warhead_smarts_missing",
    "sample_human_gold_review_missing",
)
SAMPLE_BLOCKERS = (
    "sample_assignment_review_not_completed",
    "approved_reaction_family_missing",
    "approved_warhead_rule_missing",
    "approved_warhead_smarts_missing",
    "human_gold_review_missing",
    "independent_training_label_gate_missing",
)


@dataclass(frozen=True)
class ReviewGateScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    assignment_transaction_succeeded: bool = True
    candidate_class_count: int = 7
    class_indices_contiguous: bool = True
    assignment_count: int = 11
    duplicate_class_identity: bool = False
    duplicate_sample_identity: bool = False
    links_match: bool = True
    assignment_record_sha_matches: bool = True
    class_review_package_complete: bool = True
    sample_review_package_complete: bool = True
    review_decision_valid: bool = True
    non_not_reviewed_has_reviewer: bool = True
    non_not_reviewed_has_rationale: bool = True
    family_approval_dependency_valid: bool = True
    topology_family_dependency_valid: bool = True
    approved_rule_has_smarts: bool = True
    smarts_approved_nonempty: bool = True
    smarts_match_count: int = 1
    smarts_includes_reactive_atom: bool = True
    warhead_attachment_boundary_count: int = 1
    sample_approval_class_not_quarantined: bool = True
    sample_approval_rule_approved: bool = True
    gold_dependency_valid: bool = True
    training_gold_dependency_valid: bool = True
    role_dependency_valid: bool = True
    partial_materialization_attempted: bool = False
    execution_boundary_crossed: bool = False


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    policy_rows: tuple[Mapping[str, Any], ...]
    class_rows: tuple[Mapping[str, Any], ...]
    sample_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_source_missing"),
    ("BASE source SHA mismatch", "base_source_sha_matches", False,
     "BASE_source_SHA_mismatch"),
    ("assignment transaction not succeeded", "assignment_transaction_succeeded",
     False, "assignment_transaction_not_succeeded"),
    ("candidate class count not 7", "candidate_class_count", 6,
     "candidate_class_count_not_7"),
    ("class index non-contiguous", "class_indices_contiguous", False,
     "class_index_non_contiguous"),
    ("Current11 assignment count not 11", "assignment_count", 10,
     "Current11_assignment_count_not_11"),
    ("duplicate class identity", "duplicate_class_identity", True,
     "duplicate_class_identity"),
    ("duplicate sample identity", "duplicate_sample_identity", True,
     "duplicate_sample_identity"),
    ("sample-rule-family-class link mismatch", "links_match", False,
     "sample_rule_family_class_link_mismatch"),
    ("assignment record SHA mismatch", "assignment_record_sha_matches", False,
     "assignment_record_SHA_mismatch"),
    ("class review package incomplete", "class_review_package_complete", False,
     "class_review_package_incomplete"),
    ("sample review package incomplete", "sample_review_package_complete", False,
     "sample_review_package_incomplete"),
    ("review decision outside vocabulary", "review_decision_valid", False,
     "review_decision_outside_vocabulary"),
    ("non-not-reviewed decision without reviewer",
     "non_not_reviewed_has_reviewer", False,
     "non_not_reviewed_decision_without_reviewer"),
    ("non-not-reviewed decision without rationale",
     "non_not_reviewed_has_rationale", False,
     "non_not_reviewed_decision_without_rationale"),
    ("family approved while identity decision not approve",
     "family_approval_dependency_valid", False,
     "family_approved_without_identity_approval"),
    ("rule topology approved while family not approved",
     "topology_family_dependency_valid", False,
     "topology_approved_without_family_approval"),
    ("warhead rule approved without SMARTS", "approved_rule_has_smarts", False,
     "approved_warhead_rule_without_SMARTS"),
    ("SMARTS approved but empty", "smarts_approved_nonempty", False,
     "SMARTS_approved_but_empty"),
    ("SMARTS match count zero", "smarts_match_count", 0,
     "SMARTS_match_count_zero"),
    ("SMARTS match count multiple", "smarts_match_count", 2,
     "SMARTS_match_count_multiple"),
    ("SMARTS excludes reactive atom", "smarts_includes_reactive_atom", False,
     "SMARTS_excludes_reactive_atom"),
    ("warhead attachment boundary not exact-one",
     "warhead_attachment_boundary_count", 2,
     "warhead_attachment_boundary_not_exact_one"),
    ("sample assignment approved while class quarantined",
     "sample_approval_class_not_quarantined", False,
     "sample_approved_while_class_quarantined"),
    ("sample assignment approved while rule not approved",
     "sample_approval_rule_approved", False,
     "sample_approved_while_rule_not_approved"),
    ("gold marked without complete human review", "gold_dependency_valid", False,
     "gold_marked_without_complete_human_review"),
    ("training label approved without gold", "training_gold_dependency_valid",
     False, "training_label_approved_without_gold"),
    ("role readiness opened without approved family/rule/SMARTS",
     "role_dependency_valid", False,
     "role_readiness_opened_without_approved_family_rule_SMARTS"),
    ("partial materialization attempted", "partial_materialization_attempted",
     True, "partial_materialization_attempted"),
    ("execution boundary crossed", "execution_boundary_crossed", True,
     "execution_boundary_crossed"),
)


def _git(
    repo_root: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            "git_command_failed:"
            + " ".join(arguments)
            + ":"
            + result.stderr.decode("utf-8", "replace")
        )
    return result


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _is_meaningful_text(value: object) -> bool:
    """Return whether value is an exact string with non-whitespace content."""

    return type(value) is str and bool(value.strip())


def _is_lower_sha256(value: object) -> bool:
    """Return whether value is an exact lowercase SHA256 string."""

    return (
        type(value) is str
        and _LOWER_SHA256_PATTERN.fullmatch(value) is not None
    )


def _is_exact_bool(value: object) -> bool:
    """Return whether value has the exact bool type."""

    return type(value) is bool


def _is_exact_int(value: object) -> bool:
    """Return whether value has the exact int type, excluding bool."""

    return type(value) is int


def _review_record_field_type(
    record: dict[str, Any], field: str, expected_type: type[Any]
) -> None:
    if type(record[field]) is not expected_type:
        raise ValueError(f"review_record_field_type_invalid:{field}")


def _review_record_sha_field(
    record: dict[str, Any], field: str, *, allow_empty: bool = False
) -> None:
    _review_record_field_type(record, field, str)
    value = record[field]
    if (allow_empty and value == "") or _LOWER_SHA256_PATTERN.fullmatch(value):
        return
    raise ValueError(f"review_record_SHA_invalid:{field}")


def validate_review_record_schema(record: Mapping[str, Any]) -> str:
    """Validate one exact class or sample review-record schema.

    The validator deliberately rejects mapping subclasses, missing or extra
    metadata, bool-as-int values, invented reviewers, and internally
    inconsistent decision/SMARTS states.  It returns the valid review unit
    type and never mutates ``record``.
    """

    if type(record) is not dict:
        raise ValueError("review_record_container_not_exact_dict")
    exact_record = record
    if exact_record.get("review_record_version") != REVIEW_RECORD_VERSION:
        raise ValueError("review_record_version_mismatch")
    unit_type = exact_record.get("review_unit_type")
    if unit_type not in REVIEW_UNIT_TYPES or type(unit_type) is not str:
        raise ValueError("review_unit_type_invalid")
    expected_fields = (
        CLASS_REVIEW_RECORD_FIELDS
        if unit_type == "candidate_class"
        else SAMPLE_REVIEW_RECORD_FIELDS
    )
    if set(exact_record) != set(expected_fields):
        reason = (
            "class_review_record_field_inventory_mismatch"
            if unit_type == "candidate_class"
            else "sample_review_record_field_inventory_mismatch"
        )
        raise ValueError(reason)

    for field in expected_fields:
        if field != "warhead_type_candidate_class_index_0based":
            _review_record_field_type(exact_record, field, str)
    if unit_type == "candidate_class":
        index_field = "warhead_type_candidate_class_index_0based"
        _review_record_field_type(exact_record, index_field, int)
        if exact_record[index_field] < 0:
            raise ValueError(f"review_record_integer_negative:{index_field}")
        for field in _CLASS_SHA_FIELDS:
            _review_record_sha_field(exact_record, field)
        human_decision_fields = (
            "reaction_family_identity_review_decision",
            "warhead_rule_topology_review_decision",
        )
        for field in human_decision_fields:
            if exact_record[field] not in HUMAN_REVIEW_DECISIONS:
                raise ValueError(f"review_record_decision_invalid:{field}")
        if exact_record["warhead_smarts_review_status"] not in SMARTS_REVIEW_STATUSES:
            raise ValueError("review_record_SMARTS_status_invalid")
    else:
        for field in _SAMPLE_SHA_FIELDS:
            _review_record_sha_field(exact_record, field)
        decision_field = "sample_assignment_review_decision"
        if exact_record[decision_field] not in HUMAN_REVIEW_DECISIONS:
            raise ValueError(f"review_record_decision_invalid:{decision_field}")
        human_decision_fields = (decision_field,)
        # A future sample review record copies the predecessor assignment
        # identity; it does not define a second sample-assignment identity.
        if (
            exact_record["source_assignment_record_sha256"]
            != exact_record["assignment_record_sha256"]
        ):
            raise ValueError("source_assignment_record_SHA_mismatch")
    _review_record_sha_field(
        exact_record, "review_record_sha256", allow_empty=True
    )

    reviewer_id = exact_record["reviewer_id"]
    review_rationale = exact_record["review_rationale"]
    if reviewer_id and reviewer_id.strip().casefold() in _FORBIDDEN_REVIEWER_IDS:
        raise ValueError("reviewer_identity_forbidden")
    human_decision_requires_metadata = any(
        exact_record[field] != "not_reviewed" for field in human_decision_fields
    )
    smarts_review_requires_metadata = (
        unit_type == "candidate_class"
        and exact_record["warhead_smarts_review_status"]
        in SMARTS_HUMAN_REVIEWED_STATUSES
    )
    if human_decision_requires_metadata:
        if not _is_meaningful_text(reviewer_id):
            raise ValueError("review_decision_requires_reviewer")
        if not _is_meaningful_text(review_rationale):
            raise ValueError("review_decision_requires_rationale")
    elif smarts_review_requires_metadata:
        if not _is_meaningful_text(reviewer_id):
            raise ValueError("SMARTS_review_status_requires_reviewer")
        if not _is_meaningful_text(review_rationale):
            raise ValueError("SMARTS_review_status_requires_rationale")
    elif reviewer_id or review_rationale:
        raise ValueError("not_reviewed_review_metadata_present")

    if unit_type == "candidate_class":
        smarts_status = exact_record["warhead_smarts_review_status"]
        candidate_smarts = exact_record["candidate_warhead_smarts"]
        if smarts_status == "not_materialized" and candidate_smarts:
            raise ValueError("SMARTS_not_materialized_but_value_present")
        if (
            smarts_status in {"candidate_not_reviewed", "approved", "revised"}
            and not _is_meaningful_text(candidate_smarts)
        ):
            raise ValueError("SMARTS_status_requires_nonempty_candidate")
        if (
            smarts_status == "quarantined"
            and candidate_smarts != ""
            and not _is_meaningful_text(candidate_smarts)
        ):
            raise ValueError("SMARTS_candidate_whitespace_only")
    return unit_type


def review_record_hash_input(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact validated record identity excluding only its digest."""

    unit_type = validate_review_record_schema(record)
    fields = (
        CLASS_REVIEW_RECORD_FIELDS
        if unit_type == "candidate_class"
        else SAMPLE_REVIEW_RECORD_FIELDS
    )
    return {
        field: record[field]
        for field in fields
        if field != "review_record_sha256"
    }


def review_record_sha256(record: Mapping[str, Any]) -> str:
    """Hash one exact, validated review record with self-digest exclusion."""

    return sha256(
        canonical_json(review_record_hash_input(record)).encode("utf-8")
    )


def review_record_identity_verified(record: Mapping[str, Any]) -> bool:
    """Fail closed on invalid schema and verify a populated canonical digest."""

    validate_review_record_schema(record)
    digest = record["review_record_sha256"]
    if digest == "":
        return False
    return digest == review_record_sha256(record)


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bytes(
    columns: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _cell(row.get(column, "")) for column in columns})
    return stream.getvalue().encode("utf-8")


def _cell(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    return str(value)


def validate_execution_boundary_v1(repo_root: Path) -> str:
    """Accept exactly pre-commit and the three exact-successor lifecycle states."""

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
        line[7:].decode()
        for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    if parents != (BASE_COMMIT,):
        raise ValueError("successor_parent_not_exact_BASE")
    subject, newline, body = message.partition(b"\n")
    if not newline or subject.decode() != FORMAL_COMMIT_SUBJECT:
        raise ValueError("successor_subject_mismatch")
    if body:
        raise ValueError("successor_commit_body_nonempty")
    changed = {
        item.decode()
        for item in _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).stdout.split(b"\0")
        if item
    }
    expected = {path.as_posix() for path in EXACT10_PATHS}
    if changed != expected:
        raise ValueError("successor_changed_path_inventory_mismatch")
    modes = [
        row.partition(b"\t")[0]
        for row in _git(
            repo_root, "ls-tree", "-r", "-z", head, "--", *sorted(expected)
        ).stdout.split(b"\0")
        if row
    ]
    if len(modes) != 10 or any(not mode.startswith(b"100644 blob ") for mode in modes):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root, "rev-parse", "--verify", "refs/remotes/origin/main", check=False
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
    """Read one immutable predecessor source exclusively from formal BASE."""

    result = _git(
        repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}", check=False
    )
    if result.returncode or not result.stdout:
        raise ValueError(f"BASE_source_missing:{path.as_posix()}")
    return result.stdout


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    validate_execution_boundary_v1(repo_root)
    payloads = {}
    for path, expected in FROZEN_BASE_SHA256.items():
        payload = base_bytes(repo_root, path)
        if sha256(payload) != expected:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        payloads[path] = payload
    return payloads


def _source_metadata(path: Path) -> tuple[str, str, str]:
    values = {
        ASSIGNMENT_SOURCE: (
            "11/11", "BASE/lifecycle and assignment record hash contract",
            "predecessor_assignment_production_contract"),
        CLASS_VOCABULARY: (
            "11/11", "Exact7 stable class/family/rule identities and counts",
            "candidate_class_vocabulary_authority"),
        ASSIGNMENT_AUTHORITY: (
            "11/11", "sample identities; graph SHA; class/rule/family links; record SHA",
            "Current11_candidate_assignment_authority"),
        ASSIGNMENT_READINESS: (
            "11/11", "assignment identity and predecessor review-package readiness",
            "predecessor_assignment_readiness_authority"),
        ASSIGNMENT_MANIFEST: (
            "11/11", "successful predecessor transaction and output identities",
            "predecessor_assignment_manifest"),
        FAMILY_REGISTRY: (
            "11/11", "family semantic identity and canonical family JSON/SHA",
            "candidate_reaction_family_registry"),
        RULE_REGISTRY: (
            "11/11", "local-graph topology JSON/SHA and family linkage",
            "candidate_warhead_rule_registry"),
        DESIGN_MATRIX: (
            "11/11", "radius-1 signature and candidate assignment support",
            "Current11_reaction_family_rule_design_matrix"),
        REGISTRY_MANIFEST: (
            "11/11", "registry transaction, counts, and candidate-only boundary",
            "registry_design_manifest"),
        ROLE_CONTRACT_SOURCE: (
            "11/11", "approved family/rule prerequisite for downstream role proposals",
            "downstream_role_and_seed_contract"),
        ATOM_MAPPING: (
            "11/11", "reactive atom plus parent/observed graph identity",
            "observed_to_parent_atom_mapping_authority"),
        FINAL_INDEX: (
            "11/11", "sample/PDB/component/CYS-SG target identity",
            "Current11_sample_index_authority"),
    }
    return values[path]


def _source_inventory(
    payloads: Mapping[Path, bytes],
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for path in SOURCE_PATHS:
        payload = payloads[path]
        coverage, fields, authority = _source_metadata(path)
        count = (
            len(_csv_rows(payload))
            if path.suffix == ".csv"
            else 1
            if path.suffix == ".json"
            else len(payload.decode("utf-8").splitlines())
        )
        rows.append(
            {
                "source_path": path.as_posix(),
                "BASE_SHA256": sha256(payload),
                "source_row_count": count,
                "Current11_coverage": coverage,
                "fields_actually_used": fields,
                "authority_class": authority,
                "verified": True,
            }
        )
    return tuple(rows)


def _require(condition: bool, reason: str, reasons: list[str]) -> None:
    if not condition:
        reasons.append(reason)


def _assignment_hash(row: Mapping[str, Any]) -> str:
    value = {field: row[field] for field in ASSIGNMENT_HASH_FIELDS}
    value["warhead_type_candidate_class_index_0based"] = int(
        value["warhead_type_candidate_class_index_0based"]
    )
    return sha256(canonical_json(value).encode("utf-8"))


def approved_reaction_family_available(
    *,
    decision: str,
    reviewer_id: str,
    review_rationale: str,
    canonical_identity_sha256: str,
    source_identity_sha256: str,
) -> bool:
    return (
        type(decision) is str
        and decision == "approve"
        and _is_meaningful_text(reviewer_id)
        and _is_meaningful_text(review_rationale)
        and _is_lower_sha256(canonical_identity_sha256)
        and _is_lower_sha256(source_identity_sha256)
        and canonical_identity_sha256 == source_identity_sha256
    )


def approved_warhead_rule_available(
    *,
    family_available: bool,
    topology_decision: str,
    approved_smarts: str,
    smarts_review_status: str,
    smarts_match_count: int,
    smarts_includes_reactive_atom: bool,
    warhead_atom_count: int,
    attachment_boundary_count: int,
    reviewer_id: str,
    review_rationale: str,
    identities_unchanged: bool,
) -> bool:
    return (
        family_available is True
        and type(topology_decision) is str
        and topology_decision == "approve"
        and _is_meaningful_text(approved_smarts)
        and type(smarts_review_status) is str
        and smarts_review_status == "approved"
        and _is_exact_int(smarts_match_count)
        and smarts_match_count == 1
        and smarts_includes_reactive_atom is True
        and _is_exact_int(warhead_atom_count)
        and warhead_atom_count > 0
        and _is_exact_int(attachment_boundary_count)
        and attachment_boundary_count == 1
        and _is_meaningful_text(reviewer_id)
        and _is_meaningful_text(review_rationale)
        and identities_unchanged is True
    )


def human_gold_review_completed(
    *,
    sample_decision: str,
    family_available: bool,
    rule_available: bool,
    assignment_record_sha256: str,
    source_assignment_record_sha256: str,
    reviewer_id: str,
    review_rationale: str,
) -> bool:
    return (
        type(sample_decision) is str
        and sample_decision == "approve"
        and family_available is True
        and rule_available is True
        and _is_lower_sha256(assignment_record_sha256)
        and _is_lower_sha256(source_assignment_record_sha256)
        and assignment_record_sha256 == source_assignment_record_sha256
        and _is_meaningful_text(reviewer_id)
        and _is_meaningful_text(review_rationale)
    )


def ready_for_role_proposal_generation(
    family_available: bool, rule_available: bool, gold_completed: bool
) -> bool:
    return (
        family_available is True
        and rule_available is True
        and gold_completed is True
    )


def _validate_phase_a(
    payloads: Mapping[Path, bytes],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[str],
]:
    reasons: list[str] = []
    classes = _csv_rows(payloads[CLASS_VOCABULARY])
    assignments = _csv_rows(payloads[ASSIGNMENT_AUTHORITY])
    predecessor_readiness = _csv_rows(payloads[ASSIGNMENT_READINESS])
    assignment_manifest = json.loads(payloads[ASSIGNMENT_MANIFEST])
    families = _csv_rows(payloads[FAMILY_REGISTRY])
    rules = _csv_rows(payloads[RULE_REGISTRY])
    design = _csv_rows(payloads[DESIGN_MATRIX])
    registry_manifest = json.loads(payloads[REGISTRY_MANIFEST])

    _require(
        assignment_manifest.get("transaction_succeeded") is True,
        "assignment_transaction_not_succeeded", reasons)
    _require(
        assignment_manifest.get("candidate_class_count") == 7
        and assignment_manifest.get("current11_sample_count") == 11,
        "assignment_transaction_not_succeeded", reasons)
    _require(
        registry_manifest.get("transaction_succeeded") is True,
        "registry_transaction_not_succeeded", reasons)
    _require(len(classes) == 7, "candidate_class_count_not_7", reasons)
    _require(len(assignments) == 11, "Current11_assignment_count_not_11", reasons)
    _require(len(predecessor_readiness) == 11,
             "sample_review_package_incomplete", reasons)
    _require(len(design) == 11, "Current11_design_count_not_11", reasons)
    indices = [int(row["warhead_type_candidate_class_index_0based"]) for row in classes]
    _require(indices == list(range(7)), "class_index_non_contiguous", reasons)

    classes_by_id = {
        row["warhead_type_candidate_class_id"]: row for row in classes
    }
    families_by_id = {row["reaction_family_id"]: row for row in families}
    rules_by_id = {row["warhead_rule_id"]: row for row in rules}
    _require(len(classes_by_id) == 7, "duplicate_class_identity", reasons)
    _require(len(families_by_id) == 7, "duplicate_family_identity", reasons)
    _require(len(rules_by_id) == 7, "duplicate_rule_identity", reasons)
    _require(
        len({row["sample_index_row_id"] for row in assignments}) == 11,
        "duplicate_sample_identity", reasons)
    _require(
        len({row["assignment_record_sha256"] for row in assignments}) == 11,
        "duplicate_assignment_record_SHA", reasons)

    for family in families:
        try:
            digest = sha256(
                canonical_json(
                    json.loads(family["canonical_reaction_family_signature_json"])
                ).encode("utf-8")
            )
        except (KeyError, json.JSONDecodeError):
            digest = ""
        _require(
            digest == family.get("canonical_reaction_family_signature_sha256"),
            "family_identity_SHA_mismatch", reasons)
    for rule in rules:
        try:
            digest = sha256(
                canonical_json(
                    json.loads(rule["canonical_local_graph_rule_json"])
                ).encode("utf-8")
            )
        except (KeyError, json.JSONDecodeError):
            digest = ""
        _require(
            digest == rule.get("canonical_local_graph_rule_sha256"),
            "rule_topology_SHA_mismatch", reasons)
        _require(
            rule.get("reaction_family_id") in families_by_id,
            "sample_rule_family_class_link_mismatch", reasons)
        _require(
            rule.get("approved_warhead_smarts", "") == ""
            and rule.get("approved") == "false",
            "candidate_identity_prematurely_approved", reasons)

    for row in assignments:
        class_row = classes_by_id.get(row["warhead_type_candidate_class_id"])
        rule = rules_by_id.get(row["candidate_warhead_rule_id"])
        linked = (
            class_row is not None
            and rule is not None
            and class_row["warhead_rule_id"] == row["candidate_warhead_rule_id"]
            and class_row["reaction_family_id"]
            == row["candidate_reaction_family_id"]
            and rule["reaction_family_id"] == row["candidate_reaction_family_id"]
            and int(class_row["warhead_type_candidate_class_index_0based"])
            == int(row["warhead_type_candidate_class_index_0based"])
        )
        _require(linked, "sample_rule_family_class_link_mismatch", reasons)
        _require(
            _assignment_hash(row) == row["assignment_record_sha256"],
            "assignment_record_SHA_mismatch", reasons)
        _require(
            row["ready_for_assignment_human_review"] == "true"
            and row["approved_warhead_rule_available"] == "false"
            and row["human_gold_review_completed"] == "false",
            "predecessor_assignment_readiness_invalid", reasons)

    role_text = payloads[ROLE_CONTRACT_SOURCE].decode("utf-8")
    _require(
        "approved_reaction_family_warhead_rule" in role_text
        and "approved_warhead_rule_present" in role_text,
        "role_contract_prerequisite_identity_missing", reasons)
    return classes, assignments, rules, reasons


def _policy_rows() -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {
            "policy_id": f"REVIEW_POLICY_{index:03d}",
            "semantic_name": definition[0],
            "review_scope": definition[1],
            "preconditions": definition[2],
            "approval_effect": definition[3],
            "failure_effect": definition[4],
            "reason_code": definition[5],
            "fails_closed": True,
            "verified": True,
        }
        for index, definition in enumerate(POLICY_DEFINITIONS, 1)
    )


def _class_rows(
    classes: Sequence[Mapping[str, str]],
    assignments: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, Any], ...]:
    by_class: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in assignments:
        by_class[row["warhead_type_candidate_class_id"]].append(row)
    blockers = ";".join(CLASS_BLOCKERS)
    rows = []
    for source in sorted(
        classes, key=lambda row: int(row["warhead_type_candidate_class_index_0based"])
    ):
        support = by_class[source["warhead_type_candidate_class_id"]]
        samples = sorted(row["sample_index_row_id"] for row in support)
        components = sorted({row["ligand_comp_id"] for row in support})
        rows.append(
            {
                "warhead_type_candidate_class_index_0based":
                    int(source["warhead_type_candidate_class_index_0based"]),
                "warhead_type_candidate_class_id":
                    source["warhead_type_candidate_class_id"],
                "warhead_type_candidate_semantic_name":
                    source["warhead_type_candidate_semantic_name"],
                "reaction_family_id": source["reaction_family_id"],
                "reaction_family_semantic_name":
                    source["reaction_family_semantic_name"],
                "canonical_reaction_family_signature_sha256":
                    source["canonical_reaction_family_signature_sha256"],
                "warhead_rule_id": source["warhead_rule_id"],
                "canonical_local_graph_rule_sha256":
                    source["canonical_local_graph_rule_sha256"],
                "selected_signature_radius":
                    int(source["selected_signature_radius"]),
                "Current11_match_count": int(source["Current11_match_count"]),
                "Current11_unique_component_count":
                    int(source["Current11_unique_component_count"]),
                "representative_sample_ids": ";".join(samples),
                "representative_component_ids": ";".join(components),
                "family_identity_evidence_complete": True,
                "rule_topology_evidence_complete": True,
                "assignment_support_complete":
                    len(support) == int(source["Current11_match_count"]),
                "class_identity_verified": True,
                "reaction_family_identity_review_decision": DESIGN_DECISION,
                "warhead_rule_topology_review_decision": DESIGN_DECISION,
                "warhead_smarts_review_status": DESIGN_SMARTS_STATUS,
                "candidate_warhead_smarts": "",
                "reviewer_id": "",
                "review_rationale": "",
                "review_notes": "",
                "class_review_package_ready": True,
                "family_identity_review_completed": False,
                "rule_topology_review_completed": False,
                "warhead_rule_topology_review_passed": False,
                "approved_reaction_family_available": False,
                "approved_warhead_rule_available": False,
                "ready_for_sample_assignment_review": True,
                "ready_for_role_proposal_generation": False,
                "ready_for_training": False,
                "blocking_reasons": blockers,
                "verified": True,
            }
        )
    return tuple(rows)


def _sample_rows(
    assignments: Sequence[Mapping[str, str]],
    class_rows: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    classes = {
        row["warhead_type_candidate_class_id"]: row for row in class_rows
    }
    blockers = ";".join(SAMPLE_BLOCKERS)
    rows = []
    for source in sorted(assignments, key=lambda row: row["sample_index_row_id"]):
        class_row = classes[source["warhead_type_candidate_class_id"]]
        rows.append(
            {
                "sample_index_row_id": source["sample_index_row_id"],
                "pdb_id": source["pdb_id"],
                "ligand_comp_id": source["ligand_comp_id"],
                "assignment_record_sha256": source["assignment_record_sha256"],
                "warhead_type_candidate_class_index_0based":
                    int(source["warhead_type_candidate_class_index_0based"]),
                "warhead_type_candidate_class_id":
                    source["warhead_type_candidate_class_id"],
                "reaction_family_id": source["candidate_reaction_family_id"],
                "warhead_rule_id": source["candidate_warhead_rule_id"],
                "target_residue_name": source["target_residue_name"],
                "target_residue_number": source["target_residue_number"],
                "target_residue_atom_name": source["target_residue_atom_name"],
                "ligand_reactive_atom_name": source["ligand_reactive_atom_name"],
                "component_parent_graph_sha256":
                    source["component_parent_graph_sha256"],
                "observed_graph_sha256": source["observed_graph_sha256"],
                "radius_1_signature_sha256": source["radius_1_signature_sha256"],
                "class_review_package_ready":
                    class_row["class_review_package_ready"],
                "sample_assignment_evidence_complete": True,
                "sample_assignment_identity_verified": True,
                "sample_assignment_review_decision": DESIGN_DECISION,
                "reviewer_id": "",
                "review_rationale": "",
                "review_notes": "",
                "sample_review_package_ready": True,
                "sample_review_completed": False,
                "approved_reaction_family_available": False,
                "approved_warhead_rule_available": False,
                "human_gold_review_completed": False,
                "training_label_approved": False,
                "ready_for_role_proposal_generation": False,
                "ready_for_minimal_seed_proposal_generation": False,
                "ready_for_mask_materialization": False,
                "ready_for_tensorization": False,
                "ready_for_model_integration": False,
                "ready_for_training": False,
                "blocking_reasons": blockers,
                "verified": True,
            }
        )
    return tuple(rows)


def observe_failure_scenario(scenario: ReviewGateScenario) -> tuple[str, ...]:
    checks = (
        (not scenario.base_source_present, "BASE_source_missing"),
        (not scenario.base_source_sha_matches, "BASE_source_SHA_mismatch"),
        (not scenario.assignment_transaction_succeeded,
         "assignment_transaction_not_succeeded"),
        (scenario.candidate_class_count != 7, "candidate_class_count_not_7"),
        (not scenario.class_indices_contiguous, "class_index_non_contiguous"),
        (scenario.assignment_count != 11, "Current11_assignment_count_not_11"),
        (scenario.duplicate_class_identity, "duplicate_class_identity"),
        (scenario.duplicate_sample_identity, "duplicate_sample_identity"),
        (not scenario.links_match, "sample_rule_family_class_link_mismatch"),
        (not scenario.assignment_record_sha_matches,
         "assignment_record_SHA_mismatch"),
        (not scenario.class_review_package_complete,
         "class_review_package_incomplete"),
        (not scenario.sample_review_package_complete,
         "sample_review_package_incomplete"),
        (not scenario.review_decision_valid,
         "review_decision_outside_vocabulary"),
        (not scenario.non_not_reviewed_has_reviewer,
         "non_not_reviewed_decision_without_reviewer"),
        (not scenario.non_not_reviewed_has_rationale,
         "non_not_reviewed_decision_without_rationale"),
        (not scenario.family_approval_dependency_valid,
         "family_approved_without_identity_approval"),
        (not scenario.topology_family_dependency_valid,
         "topology_approved_without_family_approval"),
        (not scenario.approved_rule_has_smarts,
         "approved_warhead_rule_without_SMARTS"),
        (not scenario.smarts_approved_nonempty, "SMARTS_approved_but_empty"),
        (scenario.smarts_match_count == 0, "SMARTS_match_count_zero"),
        (scenario.smarts_match_count > 1, "SMARTS_match_count_multiple"),
        (not scenario.smarts_includes_reactive_atom,
         "SMARTS_excludes_reactive_atom"),
        (scenario.warhead_attachment_boundary_count != 1,
         "warhead_attachment_boundary_not_exact_one"),
        (not scenario.sample_approval_class_not_quarantined,
         "sample_approved_while_class_quarantined"),
        (not scenario.sample_approval_rule_approved,
         "sample_approved_while_rule_not_approved"),
        (not scenario.gold_dependency_valid,
         "gold_marked_without_complete_human_review"),
        (not scenario.training_gold_dependency_valid,
         "training_label_approved_without_gold"),
        (not scenario.role_dependency_valid,
         "role_readiness_opened_without_approved_family_rule_SMARTS"),
        (scenario.partial_materialization_attempted,
         "partial_materialization_attempted"),
        (scenario.execution_boundary_crossed, "execution_boundary_crossed"),
    )
    return tuple(reason for failed, reason in checks if failed)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = ReviewGateScenario()
    rows = []
    signatures = set()
    for case, field, value, expected in FAILURE_MUTATIONS:
        baseline_value = getattr(baseline, field)
        if type(value) is not type(baseline_value):
            raise AssertionError(f"mutation_type_not_exact:{case}")
        if baseline_value == value:
            raise AssertionError(f"mutation_does_not_change_baseline:{case}")
        scenario = dataclasses.replace(baseline, **{field: value})
        observed = observe_failure_scenario(scenario)
        signature = f"{field}={canonical_json(value)}"
        if signature in signatures:
            raise AssertionError(f"duplicate_mutation_signature:{signature}")
        signatures.add(signature)
        verified = expected in observed
        rows.append(
            {
                "failure_case": case,
                "mutation_signature": signature,
                "mutated_field": field,
                "mutated_value_json": canonical_json(value),
                "expected_reason": expected,
                "observed_reasons": ";".join(observed),
                "expected_reason_verified": verified,
                "fails_closed": bool(observed),
                "review_policy_registry_row_count": 0,
                "candidate_class_review_readiness_row_count": 0,
                "sample_assignment_review_readiness_row_count": 0,
                "role_proposal_generation_ready": False,
                "mask_materialization_ready": False,
                "model_integration_ready": False,
                "training_ready": False,
                "verified": verified and bool(observed),
            }
        )
    if len(rows) != 30 or len(signatures) != 30:
        raise AssertionError("failure_matrix_not_Exact30")
    return tuple(rows)


def transaction_tables(
    blocking_reasons: Sequence[str],
    policy_rows: Sequence[Mapping[str, Any]],
    class_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    """Fail closed: all three core tables become header-only together."""

    if blocking_reasons:
        return (), (), ()
    return tuple(policy_rows), tuple(class_rows), tuple(sample_rows)


def build_result(repo_root: Path) -> BuildResult:
    payloads = load_frozen_sources(repo_root)
    classes, assignments, _rules, reasons = _validate_phase_a(payloads)
    policies: tuple[Mapping[str, Any], ...] = ()
    class_rows: tuple[Mapping[str, Any], ...] = ()
    sample_rows: tuple[Mapping[str, Any], ...] = ()
    if not reasons:
        policies = _policy_rows()
        class_rows = _class_rows(classes, assignments)
        sample_rows = _sample_rows(assignments, class_rows)
        phase_b: list[str] = []
        _require(len(policies) == 12, "review_policy_count_not_12", phase_b)
        _require(
            [row["policy_id"] for row in policies]
            == [f"REVIEW_POLICY_{index:03d}" for index in range(1, 13)],
            "review_policy_identity_mismatch", phase_b)
        _require(len(class_rows) == 7, "class_review_package_incomplete", phase_b)
        _require(
            all(
                row["class_review_package_ready"]
                and row["ready_for_sample_assignment_review"]
                and row["reaction_family_identity_review_decision"] == DESIGN_DECISION
                and row["warhead_rule_topology_review_decision"] == DESIGN_DECISION
                and row["warhead_smarts_review_status"] == DESIGN_SMARTS_STATUS
                and row["candidate_warhead_smarts"] == ""
                and row["reviewer_id"] == ""
                and not row["approved_reaction_family_available"]
                and not row["approved_warhead_rule_available"]
                and not row["ready_for_role_proposal_generation"]
                and not row["ready_for_training"]
                for row in class_rows
            ),
            "class_review_package_incomplete", phase_b)
        _require(len(sample_rows) == 11, "sample_review_package_incomplete", phase_b)
        _require(
            all(
                row["sample_review_package_ready"]
                and row["sample_assignment_review_decision"] == DESIGN_DECISION
                and row["reviewer_id"] == ""
                and not row["sample_review_completed"]
                and not row["approved_reaction_family_available"]
                and not row["approved_warhead_rule_available"]
                and not row["human_gold_review_completed"]
                and not row["training_label_approved"]
                and not row["ready_for_role_proposal_generation"]
                and not row["ready_for_mask_materialization"]
                and not row["ready_for_training"]
                for row in sample_rows
            ),
            "sample_review_package_incomplete", phase_b)
        reasons.extend(phase_b)
    policies, class_rows, sample_rows = transaction_tables(
        reasons, policies, class_rows, sample_rows
    )
    return BuildResult(
        source_rows=_source_inventory(payloads),
        policy_rows=policies,
        class_rows=class_rows,
        sample_rows=sample_rows,
        failure_rows=build_failure_rows(),
        transaction_succeeded=not reasons,
        blocking_reasons=tuple(sorted(set(reasons))),
    )


def _manifest(
    result: BuildResult, payloads_without_manifest: Mapping[str, bytes]
) -> dict[str, Any]:
    success = result.transaction_succeeded
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "source_count": 12,
        "source_sha256": {
            row["source_path"]: row["BASE_SHA256"] for row in result.source_rows
        },
        "review_policy_count": len(result.policy_rows),
        "candidate_class_count": len(result.class_rows),
        "current11_sample_count": len(result.sample_rows),
        "review_decision_vocabulary": list(HUMAN_REVIEW_DECISIONS),
        "smarts_review_status_vocabulary": list(SMARTS_REVIEW_STATUSES),
        "review_record_version": REVIEW_RECORD_VERSION,
        "class_review_record_fields": list(CLASS_REVIEW_RECORD_FIELDS),
        "sample_review_record_fields": list(SAMPLE_REVIEW_RECORD_FIELDS),
        "class_review_package_ready_count": sum(
            bool(row["class_review_package_ready"]) for row in result.class_rows
        ),
        "sample_review_package_ready_count": sum(
            bool(row["sample_review_package_ready"]) for row in result.sample_rows
        ),
        "family_identity_review_completed_count": 0,
        "rule_topology_review_completed_count": 0,
        "sample_review_completed_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "approved_warhead_smarts_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "phase_a_source_and_assignment_validation_passed": success,
        "phase_b_review_contract_and_readiness_validation_passed": success,
        "transaction_succeeded": success,
        "failure_mutation_count": 30,
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] and row["verified"] for row in result.failure_rows
        ),
        "review_gate_design_completed": success,
        "review_package_materialized": False,
        "human_review_execution_completed": False,
        "ready_for_review_package_materialization": success,
        "ready_for_human_review_execution": False,
        "ready_for_role_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "warhead_type_model_head_integrated": False,
        "warhead_type_loss_integrated": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "role_annotation_materialized": False,
        "minimal_seed_materialized": False,
        "mask_materialized": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_used": False,
        "blocking_reasons": list(result.blocking_reasons),
        "remaining_readiness_blockers": list(SAMPLE_BLOCKERS),
        "recommended_next_step": (
            "materialize_covapie_current11_cys_sg_reaction_family_and_warhead_rule_"
            "review_packages_v1"
            if success
            else "resolve_covapie_current11_cys_sg_review_gate_design_blockers_v1"
        ),
        "output_sha256": {
            name: sha256(payload) for name, payload in payloads_without_manifest.items()
        },
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        POLICY_FILE: _csv_bytes(POLICY_COLUMNS, result.policy_rows),
        CLASS_FILE: _csv_bytes(CLASS_COLUMNS, result.class_rows),
        SAMPLE_FILE: _csv_bytes(SAMPLE_COLUMNS, result.sample_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(
            _manifest(result, payloads),
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
        )
        + "\n"
    ).encode("utf-8")
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    destination = repo_root / OUTPUT_ROOT
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (destination / name).write_bytes(payload)
    return payloads


def main() -> int:
    materialize(Path(__file__).resolve().parents[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
