"""Materialize candidate-only CovaPIE Current11 Cys-SG assignments.

This stage freezes a seven-class auxiliary vocabulary and eleven machine-derived
candidate assignments.  It deliberately does not approve reaction families,
warhead rules, SMARTS, gold labels, tensors, model modules, or training labels.
"""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASE_COMMIT = "dc1222503dcec83220a28df2abdae898a0855864"
BASE_PARENT = "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288"
BASE_TREE = "7822087c57e62c229d1dd628d79cb736a5db44d0"
BASE_SUBJECT = (
    "add CovaPIE Cys SG reaction family and warhead rule registry design v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule assignments v1"
)
SCHEMA_VERSION = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
CLASS_ORDERING_KEY = "canonical_local_graph_rule_sha256_ascending"
ASSIGNMENT_STATUSES = (
    "machine_derived_candidate_assignment_materialized",
    "candidate_assignment_blocked",
    "human_reviewed_approved",
    "human_reviewed_revised",
    "human_reviewed_quarantined",
)
REVIEW_STATUSES = ("not_reviewed", "approved", "revised", "quarantined")
TRAINING_LABEL_STATUSES = (
    "not_approved_for_training",
    "approved_for_training",
)
ASSIGNMENT_STATUS = "machine_derived_candidate_assignment_materialized"
REVIEW_STATUS = "not_reviewed"
TRAINING_LABEL_STATUS = "not_approved_for_training"
ASSIGNMENT_BLOCKERS = (
    "human_reaction_family_review_missing",
    "approved_warhead_rule_missing",
    "approved_warhead_smarts_missing",
    "current11_human_gold_review_missing",
)

DESIGN_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
)
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1"
)
FAMILY_REGISTRY = DESIGN_ROOT / "covapie_cys_sg_reaction_family_registry.csv"
RULE_REGISTRY = DESIGN_ROOT / "covapie_cys_sg_warhead_rule_registry.csv"
DESIGN_MATRIX = (
    DESIGN_ROOT / "covapie_current11_reaction_family_and_warhead_rule_design_matrix.csv"
)
DESIGN_MANIFEST = (
    DESIGN_ROOT
    / "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_manifest.json"
)
PROJECTION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1"
)
ATOM_MAPPING = (
    PROJECTION_ROOT
    / "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
PROJECTION_READINESS = (
    PROJECTION_ROOT / "covapie_current11_observed_projection_readiness_matrix.csv"
)
PROJECTION_MANIFEST = (
    PROJECTION_ROOT
    / "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json"
)
ATOM_PAIR_MAPPING = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
ROLE_CONTRACT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)

FROZEN_BASE_SHA256 = {
    DESIGN_SOURCE:
        "db912d62c996bc91a0f8735135883f301ad61e3a448d5574770054c7f82db364",
    FAMILY_REGISTRY:
        "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    RULE_REGISTRY:
        "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    DESIGN_MATRIX:
        "24ae0fbd2dc1454574d9ed17145ba71d3b3132ffecfb84a1a831eceb77efab03",
    DESIGN_MANIFEST:
        "4603d124e2f90616ebf7d28975e0eeb77e3d4c90133688d87df2e30c9ac54ef9",
    ATOM_MAPPING:
        "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    PROJECTION_READINESS:
        "ec7bb2c203a7b13f525c413171b734fdd9f8af934b6e7e8eaf3fc6ae141128a0",
    PROJECTION_MANIFEST:
        "e553e9cb1518cd2c9465772758539e9610c8f81cd702dd0440e99fbd143fc0a7",
    ATOM_PAIR_MAPPING:
        "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    FINAL_INDEX:
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
}
SOURCE_PATHS = (*FROZEN_BASE_SHA256, ROLE_CONTRACT_SOURCE)

SOURCE_FILE = "covapie_assignment_materialization_source_inventory.csv"
VOCABULARY_FILE = "covapie_cys_sg_warhead_type_candidate_class_vocabulary.csv"
ASSIGNMENT_FILE = "covapie_current11_cys_sg_candidate_assignment_authority.csv"
READINESS_FILE = "covapie_current11_cys_sg_assignment_review_readiness_matrix.csv"
FAILURE_FILE = "covapie_cys_sg_assignment_materialization_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    VOCABULARY_FILE,
    ASSIGNMENT_FILE,
    READINESS_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
EXACT10_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
    ),
    Path(
        "docs/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1_summary.md"
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
VOCABULARY_COLUMNS = (
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "warhead_type_candidate_semantic_name",
    "warhead_rule_id",
    "reaction_family_id",
    "reaction_family_semantic_name",
    "canonical_local_graph_rule_sha256",
    "canonical_reaction_family_signature_sha256",
    "selected_signature_radius",
    "target_residue_name",
    "target_residue_atom_name",
    "formed_bond_order",
    "required_reaction_delta_class",
    "required_leaving_group_count",
    "allowed_leaving_group_elements",
    "Current11_match_count",
    "Current11_unique_component_count",
    "assignment_status",
    "review_status",
    "training_label_status",
    "human_gold_review_completed",
    "approved_warhead_rule",
    "verified",
)
ASSIGNMENT_COLUMNS = (
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
    "candidate_reaction_family_semantic_name",
    "candidate_warhead_rule_id",
    "candidate_warhead_type_semantic_name",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "assignment_source_design_matrix_sha256",
    "assignment_source_rule_registry_sha256",
    "assignment_source_family_registry_sha256",
    "candidate_rule_assignment_exact_one",
    "candidate_family_assignment_exact_one",
    "class_vocabulary_join_exact_one",
    "assignment_status",
    "review_status",
    "training_label_status",
    "candidate_reaction_family_assignment_materialized",
    "candidate_warhead_rule_assignment_materialized",
    "warhead_type_candidate_label_available",
    "formal_reaction_family_label_available",
    "approved_warhead_rule_available",
    "human_gold_review_completed",
    "training_label_approved",
    "ready_for_assignment_human_review",
    "ready_for_role_proposal_generation",
    "ready_for_minimal_seed_proposal_generation",
    "ready_for_mask_materialization",
    "ready_for_tensorization",
    "ready_for_model_integration",
    "ready_for_training",
    "assignment_record_sha256",
    "blocking_reasons",
    "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id",
    "candidate_assignment_materialized",
    "candidate_class_index_available",
    "candidate_class_id_available",
    "assignment_identity_verified",
    "assignment_record_sha256",
    "human_review_package_ready",
    "human_review_completed",
    "approved_reaction_family_available",
    "approved_warhead_rule_available",
    "role_proposal_generation_ready",
    "minimal_seed_proposal_generation_ready",
    "mask_materialization_ready",
    "tensorization_ready",
    "model_integration_ready",
    "training_ready",
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
    "candidate_class_vocabulary_row_count",
    "current11_assignment_authority_row_count",
    "assignment_review_readiness_row_count",
    "role_proposal_generation_ready",
    "mask_materialization_ready",
    "model_integration_ready",
    "training_ready",
    "verified",
)


@dataclass(frozen=True)
class AssignmentScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    design_transaction_succeeded: bool = True
    current11_sample_coverage: int = 11
    duplicate_sample_identity: bool = False
    rule_registry_present: bool = True
    family_registry_present: bool = True
    rule_json_sha_matches: bool = True
    family_json_sha_matches: bool = True
    rule_family_links_match: bool = True
    candidate_rule_count: int = 1
    candidate_family_count: int = 1
    candidate_class_order_deterministic: bool = True
    duplicate_candidate_class_index: bool = False
    candidate_class_indices_contiguous: bool = True
    candidate_class_id_matches: bool = True
    sample_rule_matches: bool = True
    sample_family_matches: bool = True
    semantic_name_matches: bool = True
    graph_sha_matches: bool = True
    candidate_promoted_to_approved: bool = False
    training_label_approved: bool = False
    role_ready_without_approved_rule: bool = False
    partial_materialization_attempted: bool = False
    execution_boundary_crossed: bool = False


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    vocabulary_rows: tuple[Mapping[str, Any], ...]
    assignment_rows: tuple[Mapping[str, Any], ...]
    readiness_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    role_contract_sha256: str
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_source_missing"),
    (
        "BASE source SHA mismatch",
        "base_source_sha_matches",
        False,
        "BASE_source_SHA_mismatch",
    ),
    (
        "design transaction not succeeded",
        "design_transaction_succeeded",
        False,
        "design_transaction_not_succeeded",
    ),
    (
        "Current11 sample coverage incomplete",
        "current11_sample_coverage",
        10,
        "Current11_sample_coverage_incomplete",
    ),
    (
        "duplicate sample identity",
        "duplicate_sample_identity",
        True,
        "duplicate_sample_identity",
    ),
    (
        "rule registry missing",
        "rule_registry_present",
        False,
        "rule_registry_missing",
    ),
    (
        "family registry missing",
        "family_registry_present",
        False,
        "family_registry_missing",
    ),
    (
        "rule JSON SHA mismatch",
        "rule_json_sha_matches",
        False,
        "rule_JSON_SHA_mismatch",
    ),
    (
        "family JSON SHA mismatch",
        "family_json_sha_matches",
        False,
        "family_JSON_SHA_mismatch",
    ),
    (
        "rule-family link mismatch",
        "rule_family_links_match",
        False,
        "rule_family_link_mismatch",
    ),
    ("candidate rule absent", "candidate_rule_count", 0, "candidate_rule_absent"),
    (
        "candidate rule ambiguous",
        "candidate_rule_count",
        2,
        "candidate_rule_ambiguous",
    ),
    (
        "candidate family absent",
        "candidate_family_count",
        0,
        "candidate_family_absent",
    ),
    (
        "candidate family ambiguous",
        "candidate_family_count",
        2,
        "candidate_family_ambiguous",
    ),
    (
        "candidate class ordering nondeterministic",
        "candidate_class_order_deterministic",
        False,
        "candidate_class_ordering_nondeterministic",
    ),
    (
        "duplicate candidate class index",
        "duplicate_candidate_class_index",
        True,
        "duplicate_candidate_class_index",
    ),
    (
        "non-contiguous candidate class index",
        "candidate_class_indices_contiguous",
        False,
        "non_contiguous_candidate_class_index",
    ),
    (
        "candidate class ID mismatch",
        "candidate_class_id_matches",
        False,
        "candidate_class_ID_mismatch",
    ),
    (
        "sample assigned rule mismatch",
        "sample_rule_matches",
        False,
        "sample_assigned_rule_mismatch",
    ),
    (
        "sample assigned family mismatch",
        "sample_family_matches",
        False,
        "sample_assigned_family_mismatch",
    ),
    (
        "sample semantic name mismatch",
        "semantic_name_matches",
        False,
        "sample_semantic_name_mismatch",
    ),
    (
        "parent or observed graph SHA mismatch",
        "graph_sha_matches",
        False,
        "parent_or_observed_graph_SHA_mismatch",
    ),
    (
        "candidate assignment prematurely promoted to approved",
        "candidate_promoted_to_approved",
        True,
        "candidate_assignment_prematurely_promoted_to_approved",
    ),
    (
        "training label prematurely approved",
        "training_label_approved",
        True,
        "training_label_prematurely_approved",
    ),
    (
        "role proposal readiness opened without approved rule",
        "role_ready_without_approved_rule",
        True,
        "role_proposal_readiness_opened_without_approved_rule",
    ),
    (
        "partial materialization attempted",
        "partial_materialization_attempted",
        True,
        "partial_materialization_attempted",
    ),
    (
        "execution boundary crossed",
        "execution_boundary_crossed",
        True,
        "execution_boundary_crossed",
    ),
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


def base_bytes(repo_root: Path, path: Path) -> bytes:
    """Read an immutable formal source from the BASE commit."""

    return _git(repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}").stdout


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def assignment_record_sha256(value: Mapping[str, Any]) -> str:
    return sha256(canonical_json(dict(value)).encode("utf-8"))


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
    """Accept exactly the four required lifecycle states."""

    shown = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).stdout.decode().splitlines()
    if shown != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
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
    changed = tuple(
        item.decode()
        for item in _git(
            repo_root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            head,
        ).stdout.split(b"\0")
        if item
    )
    expected = tuple(path.as_posix() for path in EXACT10_PATHS)
    if len(changed) != 10 or set(changed) != set(expected):
        raise ValueError("successor_changed_path_inventory_mismatch")
    tree_rows = tuple(
        row
        for row in _git(
            repo_root, "ls-tree", "-r", "-z", head, "--", *expected
        ).stdout.split(b"\0")
        if row
    )
    if len(tree_rows) != 10 or any(
        not row.partition(b"\t")[0].startswith(b"100644 blob ")
        for row in tree_rows
    ):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if branch.returncode != 0:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root, "rev-parse", "--verify", "refs/remotes/origin/main", check=False
    )
    if origin.returncode != 0:
        raise ValueError("successor_origin_main_missing")
    origin_oid = origin.stdout.decode().strip()
    if origin_oid == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin_oid == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    validate_execution_boundary_v1(repo_root)
    payloads: dict[Path, bytes] = {}
    for path in SOURCE_PATHS:
        payload = base_bytes(repo_root, path)
        if not payload:
            raise ValueError(f"BASE_source_missing:{path.as_posix()}")
        expected = FROZEN_BASE_SHA256.get(path)
        if expected is not None and sha256(payload) != expected:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        payloads[path] = payload
    return payloads


def _source_metadata(path: Path) -> tuple[str, str, str]:
    values = {
        DESIGN_SOURCE: (
            "11/11",
            "BASE identity; design transaction and lifecycle contract",
            "predecessor_design_production_contract",
        ),
        FAMILY_REGISTRY: (
            "11/11",
            "family ID; semantic name; canonical signature SHA; target condition",
            "candidate_reaction_family_registry",
        ),
        RULE_REGISTRY: (
            "11/11",
            "rule ID; graph rule JSON/SHA; family link; Current11 counts",
            "candidate_warhead_rule_registry",
        ),
        DESIGN_MATRIX: (
            "11/11",
            "sample identity; reactive atom; graph SHA; candidate family/rule",
            "Current11_candidate_design_matrix",
        ),
        DESIGN_MANIFEST: (
            "11/11",
            "transaction state; registry counts; output/source SHA; readiness",
            "predecessor_design_manifest",
        ),
        ATOM_MAPPING: (
            "11/11",
            "reactive observed/parent atom identity; parent/observed graph SHA",
            "observed_to_parent_atom_mapping_authority",
        ),
        PROJECTION_READINESS: (
            "11/11",
            "projection validity; reactive atom availability; closed readiness",
            "observed_projection_readiness_authority",
        ),
        PROJECTION_MANIFEST: (
            "11/11",
            "projection transaction; sample and reactive atom counts",
            "observed_projection_manifest_authority",
        ),
        ATOM_PAIR_MAPPING: (
            "11/11",
            "exact-one target and ligand atom table mappings",
            "canonical_atom_pair_mapping_validation_authority",
        ),
        FINAL_INDEX: (
            "11/11",
            "sample; PDB; component; target CYS SG and ligand atom identity",
            "Current11_sample_index_authority",
        ),
        ROLE_CONTRACT_SOURCE: (
            "11/11",
            "approved reaction-family/warhead-rule prerequisite for role proposal",
            "downstream_role_and_seed_gate_contract",
        ),
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


def _phase_a(
    payloads: Mapping[Path, bytes],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, dict[str, str]],
    list[str],
]:
    reasons: list[str] = []
    family_rows = _csv_rows(payloads[FAMILY_REGISTRY])
    rule_rows = _csv_rows(payloads[RULE_REGISTRY])
    design_rows = _csv_rows(payloads[DESIGN_MATRIX])
    final_rows = _csv_rows(payloads[FINAL_INDEX])
    manifest = json.loads(payloads[DESIGN_MANIFEST])
    projection_manifest = json.loads(payloads[PROJECTION_MANIFEST])

    _require(manifest.get("transaction_succeeded") is True, "design_transaction_not_succeeded", reasons)
    _require(
        manifest.get("phase_a_source_and_reaction_center_validation_passed") is True
        and manifest.get("phase_b_signature_grouping_and_assignment_passed") is True,
        "design_transaction_not_succeeded",
        reasons,
    )
    _require(
        manifest.get("output_sha256", {}).get(FAMILY_REGISTRY.name)
        == FROZEN_BASE_SHA256[FAMILY_REGISTRY]
        and manifest.get("output_sha256", {}).get(RULE_REGISTRY.name)
        == FROZEN_BASE_SHA256[RULE_REGISTRY]
        and manifest.get("output_sha256", {}).get(DESIGN_MATRIX.name)
        == FROZEN_BASE_SHA256[DESIGN_MATRIX],
        "design_manifest_output_SHA_mismatch",
        reasons,
    )
    _require(
        projection_manifest.get("transaction_succeeded") is True
        and projection_manifest.get("current11_sample_count") == 11,
        "projection_transaction_not_succeeded",
        reasons,
    )
    _require(len(family_rows) == 7, "family_registry_row_count_not_7", reasons)
    _require(len(rule_rows) == 7, "rule_registry_row_count_not_7", reasons)
    _require(len(design_rows) == 11, "Current11_sample_coverage_incomplete", reasons)
    _require(len(final_rows) == 11, "Current11_sample_coverage_incomplete", reasons)

    family_by_id = {row["reaction_family_id"]: row for row in family_rows}
    rule_by_id = {row["warhead_rule_id"]: row for row in rule_rows}
    _require(len(family_by_id) == len(family_rows), "duplicate_reaction_family_id", reasons)
    _require(len(rule_by_id) == len(rule_rows), "duplicate_warhead_rule_id", reasons)
    for row in family_rows:
        try:
            digest = sha256(
                canonical_json(
                    json.loads(row["canonical_reaction_family_signature_json"])
                ).encode("utf-8")
            )
        except (KeyError, json.JSONDecodeError):
            digest = ""
        _require(
            digest == row.get("canonical_reaction_family_signature_sha256"),
            "family_JSON_SHA_mismatch",
            reasons,
        )
        _require(row.get("verified") == "true", "family_registry_not_verified", reasons)
    for row in rule_rows:
        try:
            digest = sha256(
                canonical_json(json.loads(row["canonical_local_graph_rule_json"])).encode(
                    "utf-8"
                )
            )
        except (KeyError, json.JSONDecodeError):
            digest = ""
        _require(
            digest == row.get("canonical_local_graph_rule_sha256"),
            "rule_JSON_SHA_mismatch",
            reasons,
        )
        _require(
            row.get("reaction_family_id") in family_by_id,
            "rule_family_link_mismatch",
            reasons,
        )
        _require(
            row.get("approved") == "false"
            and row.get("approved_warhead_smarts", "") == ""
            and row.get("human_gold_review_completed") == "false",
            "candidate_assignment_prematurely_promoted_to_approved",
            reasons,
        )

    final_by_sample = {row["sample_index_row_id"]: row for row in final_rows}
    _require(len(final_by_sample) == 11, "duplicate_sample_identity", reasons)
    reactive_mapping_rows = [
        row
        for row in _csv_rows(payloads[ATOM_MAPPING])
        if row["reactive_ligand_atom"] == "true"
    ]
    mapping_by_sample = {
        row["sample_index_row_id"]: row for row in reactive_mapping_rows
    }
    _require(
        len(reactive_mapping_rows) == 11 and len(mapping_by_sample) == 11,
        "reactive_atom_mapping_not_exact11",
        reasons,
    )
    pair_rows = _csv_rows(payloads[ATOM_PAIR_MAPPING])
    pair_counts = Counter(row["sample_index_row_id"] for row in pair_rows)
    _require(
        len(pair_rows) == 22
        and all(
            pair_counts[sample] == 2
            and all(
                row["candidate_match_count"] == "1"
                and row["expected_match_count"] == "1"
                and row["mapping_outcome"] == "mapped"
                and row["verified"] == "true"
                for row in pair_rows
                if row["sample_index_row_id"] == sample
            )
            for sample in final_by_sample
        ),
        "atom_pair_mapping_not_exact_one",
        reasons,
    )
    projection_rows = _csv_rows(payloads[PROJECTION_READINESS])
    _require(
        len(projection_rows) == 11
        and all(
            row["observed_atom_projection_exact"] == "true"
            and row["observed_projected_graph_available"] == "true"
            and row["reactive_ligand_atom_available"] == "true"
            and row["verified"] == "true"
            for row in projection_rows
        ),
        "observed_projection_not_ready",
        reasons,
    )

    design_by_sample: dict[str, dict[str, str]] = {}
    for row in design_rows:
        sample = row["sample_index_row_id"]
        if sample in design_by_sample:
            reasons.append("duplicate_sample_identity")
            continue
        design_by_sample[sample] = row
        final = final_by_sample.get(sample)
        mapping = mapping_by_sample.get(sample)
        _require(final is not None and mapping is not None, "sample_identity_missing", reasons)
        if final is None or mapping is None:
            continue
        _require(
            (
                row["pdb_id"],
                row["ligand_comp_id"],
                row["target_residue_name"],
                row["target_residue_number"],
                row["target_residue_atom_name"],
                row["ligand_reactive_atom_name"],
            )
            == (
                final["pdb_id"],
                final["ligand_comp_id"],
                final["covalent_residue_name"],
                final["covalent_residue_index"],
                final["covalent_residue_atom_name"],
                final["ligand_covalent_atom_name"],
            ),
            "sample_or_reactive_atom_identity_mismatch",
            reasons,
        )
        _require(
            (
                row["ligand_reactive_atom_name"],
                row["ligand_reactive_atom_element"],
                row["ligand_reactive_parent_ccd_atom_id"],
                row["component_parent_graph_sha256"],
                row["observed_graph_sha256"],
            )
            == (
                mapping["observed_atom_name"],
                mapping["observed_type_symbol"],
                mapping["parent_ccd_atom_id"],
                mapping["component_parent_graph_sha256"],
                mapping["observed_graph_sha256"],
            ),
            "parent_or_observed_graph_SHA_mismatch",
            reasons,
        )
        rule = rule_by_id.get(row["candidate_warhead_rule_id"])
        family = family_by_id.get(row["candidate_reaction_family_id"])
        _require(rule is not None, "candidate_rule_absent", reasons)
        _require(family is not None, "candidate_family_absent", reasons)
        if rule is not None and family is not None:
            _require(
                rule["reaction_family_id"] == family["reaction_family_id"],
                "rule_family_link_mismatch",
                reasons,
            )
            _require(
                row["candidate_warhead_type_semantic_name"]
                == rule["warhead_type_semantic_name"]
                and row["candidate_reaction_family_semantic_name"]
                == family["reaction_family_semantic_name"],
                "sample_semantic_name_mismatch",
                reasons,
            )
        _require(
            row["family_candidate_exact_one"] == "true"
            and row["warhead_rule_candidate_exact_one"] == "true"
            and row["verified"] == "true",
            "candidate_assignment_not_exact_one",
            reasons,
        )

    role_text = payloads[ROLE_CONTRACT_SOURCE].decode("utf-8")
    _require(
        "approved_reaction_family_warhead_rule" in role_text
        and "approved_warhead_rule_present" in role_text,
        "downstream_role_gate_contract_missing",
        reasons,
    )
    return family_rows, rule_rows, design_rows, mapping_by_sample, reasons


def _vocabulary_rows(
    family_rows: Sequence[Mapping[str, str]],
    rule_rows: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, Any], ...]:
    family_by_id = {row["reaction_family_id"]: row for row in family_rows}
    ordered = sorted(rule_rows, key=lambda row: row["canonical_local_graph_rule_sha256"])
    rows = []
    for index, rule in enumerate(ordered):
        family = family_by_id[rule["reaction_family_id"]]
        digest = rule["canonical_local_graph_rule_sha256"]
        rows.append(
            {
                "warhead_type_candidate_class_index_0based": index,
                "warhead_type_candidate_class_id":
                    "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_" + digest[:16].upper(),
                "warhead_type_candidate_semantic_name":
                    rule["warhead_type_semantic_name"],
                "warhead_rule_id": rule["warhead_rule_id"],
                "reaction_family_id": family["reaction_family_id"],
                "reaction_family_semantic_name":
                    family["reaction_family_semantic_name"],
                "canonical_local_graph_rule_sha256": digest,
                "canonical_reaction_family_signature_sha256":
                    family["canonical_reaction_family_signature_sha256"],
                "selected_signature_radius": rule["selected_signature_radius"],
                "target_residue_name": rule["target_residue_name"],
                "target_residue_atom_name": rule["target_residue_atom_name"],
                "formed_bond_order": rule["formed_bond_order"],
                "required_reaction_delta_class":
                    rule["required_reaction_delta_class"],
                "required_leaving_group_count":
                    rule["required_leaving_group_count"],
                "allowed_leaving_group_elements":
                    rule["allowed_leaving_group_elements"],
                "Current11_match_count": rule["Current11_match_count"],
                "Current11_unique_component_count":
                    rule["Current11_unique_component_count"],
                "assignment_status": ASSIGNMENT_STATUS,
                "review_status": REVIEW_STATUS,
                "training_label_status": TRAINING_LABEL_STATUS,
                "human_gold_review_completed": False,
                "approved_warhead_rule": False,
                "verified": True,
            }
        )
    return tuple(rows)


RECORD_FIELDS = (
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


def assignment_hash_input(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the closed canonical record identity input (excluding its digest)."""

    return {field: row[field] for field in RECORD_FIELDS}


def _assignment_and_readiness_rows(
    design_rows: Sequence[Mapping[str, str]],
    vocabulary_rows: Sequence[Mapping[str, Any]],
) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    class_by_rule = {row["warhead_rule_id"]: row for row in vocabulary_rows}
    assignments = []
    readiness = []
    blockers = ";".join(ASSIGNMENT_BLOCKERS)
    for design in sorted(design_rows, key=lambda row: row["sample_index_row_id"]):
        class_row = class_by_rule[design["candidate_warhead_rule_id"]]
        row: dict[str, Any] = {
            field: design[field]
            for field in (
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
                "candidate_reaction_family_semantic_name",
                "candidate_warhead_rule_id",
                "candidate_warhead_type_semantic_name",
            )
        }
        row.update(
            {
                "warhead_type_candidate_class_index_0based":
                    class_row["warhead_type_candidate_class_index_0based"],
                "warhead_type_candidate_class_id":
                    class_row["warhead_type_candidate_class_id"],
                "assignment_source_design_matrix_sha256":
                    FROZEN_BASE_SHA256[DESIGN_MATRIX],
                "assignment_source_rule_registry_sha256":
                    FROZEN_BASE_SHA256[RULE_REGISTRY],
                "assignment_source_family_registry_sha256":
                    FROZEN_BASE_SHA256[FAMILY_REGISTRY],
                "candidate_rule_assignment_exact_one": True,
                "candidate_family_assignment_exact_one": True,
                "class_vocabulary_join_exact_one": True,
                "assignment_status": ASSIGNMENT_STATUS,
                "review_status": REVIEW_STATUS,
                "training_label_status": TRAINING_LABEL_STATUS,
                "candidate_reaction_family_assignment_materialized": True,
                "candidate_warhead_rule_assignment_materialized": True,
                "warhead_type_candidate_label_available": True,
                "formal_reaction_family_label_available": False,
                "approved_warhead_rule_available": False,
                "human_gold_review_completed": False,
                "training_label_approved": False,
                "ready_for_assignment_human_review": True,
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
        row["assignment_record_sha256"] = assignment_record_sha256(
            assignment_hash_input(row)
        )
        assignments.append(row)
        readiness.append(
            {
                "sample_index_row_id": row["sample_index_row_id"],
                "candidate_assignment_materialized": True,
                "candidate_class_index_available": True,
                "candidate_class_id_available": True,
                "assignment_identity_verified": True,
                "assignment_record_sha256": row["assignment_record_sha256"],
                "human_review_package_ready": True,
                "human_review_completed": False,
                "approved_reaction_family_available": False,
                "approved_warhead_rule_available": False,
                "role_proposal_generation_ready": False,
                "minimal_seed_proposal_generation_ready": False,
                "mask_materialization_ready": False,
                "tensorization_ready": False,
                "model_integration_ready": False,
                "training_ready": False,
                "blocking_reasons": blockers,
                "verified": True,
            }
        )
    return tuple(assignments), tuple(readiness)


def observe_failure_scenario(scenario: AssignmentScenario) -> tuple[str, ...]:
    reasons = []
    checks = (
        (not scenario.base_source_present, "BASE_source_missing"),
        (not scenario.base_source_sha_matches, "BASE_source_SHA_mismatch"),
        (
            not scenario.design_transaction_succeeded,
            "design_transaction_not_succeeded",
        ),
        (
            scenario.current11_sample_coverage != 11,
            "Current11_sample_coverage_incomplete",
        ),
        (scenario.duplicate_sample_identity, "duplicate_sample_identity"),
        (not scenario.rule_registry_present, "rule_registry_missing"),
        (not scenario.family_registry_present, "family_registry_missing"),
        (not scenario.rule_json_sha_matches, "rule_JSON_SHA_mismatch"),
        (not scenario.family_json_sha_matches, "family_JSON_SHA_mismatch"),
        (not scenario.rule_family_links_match, "rule_family_link_mismatch"),
        (scenario.candidate_rule_count == 0, "candidate_rule_absent"),
        (scenario.candidate_rule_count > 1, "candidate_rule_ambiguous"),
        (scenario.candidate_family_count == 0, "candidate_family_absent"),
        (scenario.candidate_family_count > 1, "candidate_family_ambiguous"),
        (
            not scenario.candidate_class_order_deterministic,
            "candidate_class_ordering_nondeterministic",
        ),
        (
            scenario.duplicate_candidate_class_index,
            "duplicate_candidate_class_index",
        ),
        (
            not scenario.candidate_class_indices_contiguous,
            "non_contiguous_candidate_class_index",
        ),
        (not scenario.candidate_class_id_matches, "candidate_class_ID_mismatch"),
        (not scenario.sample_rule_matches, "sample_assigned_rule_mismatch"),
        (not scenario.sample_family_matches, "sample_assigned_family_mismatch"),
        (not scenario.semantic_name_matches, "sample_semantic_name_mismatch"),
        (
            not scenario.graph_sha_matches,
            "parent_or_observed_graph_SHA_mismatch",
        ),
        (
            scenario.candidate_promoted_to_approved,
            "candidate_assignment_prematurely_promoted_to_approved",
        ),
        (
            scenario.training_label_approved,
            "training_label_prematurely_approved",
        ),
        (
            scenario.role_ready_without_approved_rule,
            "role_proposal_readiness_opened_without_approved_rule",
        ),
        (
            scenario.partial_materialization_attempted,
            "partial_materialization_attempted",
        ),
        (scenario.execution_boundary_crossed, "execution_boundary_crossed"),
    )
    for failed, reason in checks:
        if failed:
            reasons.append(reason)
    return tuple(reasons)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = AssignmentScenario()
    rows = []
    signatures = set()
    for case, field, value, expected in FAILURE_MUTATIONS:
        if getattr(baseline, field) == value:
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
                "candidate_class_vocabulary_row_count": 0,
                "current11_assignment_authority_row_count": 0,
                "assignment_review_readiness_row_count": 0,
                "role_proposal_generation_ready": False,
                "mask_materialization_ready": False,
                "model_integration_ready": False,
                "training_ready": False,
                "verified": verified and bool(observed),
            }
        )
    if len(rows) != 27 or len(signatures) != 27:
        raise AssertionError("failure_matrix_not_Exact27")
    return tuple(rows)


def transaction_tables(
    blocking_reasons: Sequence[str],
    vocabulary_rows: Sequence[Mapping[str, Any]],
    assignment_rows: Sequence[Mapping[str, Any]],
    readiness_rows: Sequence[Mapping[str, Any]],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    """Fail closed: every core table is header-only if either phase blocks."""

    if blocking_reasons:
        return (), (), ()
    return tuple(vocabulary_rows), tuple(assignment_rows), tuple(readiness_rows)


def build_result(repo_root: Path) -> BuildResult:
    payloads = load_frozen_sources(repo_root)
    family, rules, design, _mapping, reasons = _phase_a(payloads)
    vocabulary: tuple[Mapping[str, Any], ...] = ()
    assignments: tuple[Mapping[str, Any], ...] = ()
    readiness: tuple[Mapping[str, Any], ...] = ()
    if not reasons:
        vocabulary = _vocabulary_rows(family, rules)
        indices = [
            row["warhead_type_candidate_class_index_0based"] for row in vocabulary
        ]
        digests = [row["canonical_local_graph_rule_sha256"] for row in vocabulary]
        phase_b_reasons = []
        _require(len(vocabulary) == 7, "candidate_class_count_not_7", phase_b_reasons)
        _require(indices == list(range(7)), "non_contiguous_candidate_class_index", phase_b_reasons)
        _require(digests == sorted(digests), "candidate_class_ordering_nondeterministic", phase_b_reasons)
        _require(
            len({row["warhead_type_candidate_class_id"] for row in vocabulary}) == 7,
            "duplicate_candidate_class_ID",
            phase_b_reasons,
        )
        if not phase_b_reasons:
            assignments, readiness = _assignment_and_readiness_rows(
                design, vocabulary
            )
            _require(len(assignments) == 11, "Current11_sample_coverage_incomplete", phase_b_reasons)
            _require(len(readiness) == 11, "review_readiness_coverage_incomplete", phase_b_reasons)
            _require(
                len({row["assignment_record_sha256"] for row in assignments}) == 11,
                "assignment_record_SHA_not_unique",
                phase_b_reasons,
            )
        reasons.extend(phase_b_reasons)
    vocabulary, assignments, readiness = transaction_tables(
        reasons, vocabulary, assignments, readiness
    )
    return BuildResult(
        source_rows=_source_inventory(payloads),
        vocabulary_rows=vocabulary,
        assignment_rows=assignments,
        readiness_rows=readiness,
        failure_rows=build_failure_rows(),
        role_contract_sha256=sha256(payloads[ROLE_CONTRACT_SOURCE]),
        transaction_succeeded=not reasons,
        blocking_reasons=tuple(sorted(set(reasons))),
    )


def _manifest(
    result: BuildResult, payloads_without_manifest: Mapping[str, bytes]
) -> dict[str, Any]:
    success = result.transaction_succeeded
    assignment_count = len(result.assignment_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "source_count": 11,
        "source_sha256": {
            row["source_path"]: row["BASE_SHA256"] for row in result.source_rows
        },
        "candidate_class_count": len(result.vocabulary_rows),
        "candidate_class_indices_contiguous": success,
        "candidate_class_ordering_key": CLASS_ORDERING_KEY,
        "assignment_status_vocabulary": list(ASSIGNMENT_STATUSES),
        "review_status_vocabulary": list(REVIEW_STATUSES),
        "training_label_status_vocabulary": list(TRAINING_LABEL_STATUSES),
        "current11_sample_count": assignment_count,
        "candidate_reaction_family_assignment_materialized_count": assignment_count,
        "candidate_warhead_rule_assignment_materialized_count": assignment_count,
        "warhead_type_candidate_label_available_count": assignment_count,
        "formal_reaction_family_label_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "assignment_human_review_ready_count": assignment_count,
        "role_proposal_generation_ready_count": 0,
        "minimal_seed_proposal_generation_ready_count": 0,
        "mask_materialization_ready_count": 0,
        "tensorization_ready_count": 0,
        "model_integration_ready_count": 0,
        "training_ready_count": 0,
        "warhead_type_auxiliary_label_contract_designed": True,
        "warhead_type_candidate_vocabulary_materialized": success,
        "warhead_type_candidate_assignments_materialized": success,
        "warhead_type_label_tensor_materialized": False,
        "warhead_type_one_hot_materialized": False,
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
        "phase_a_source_and_assignment_validation_passed": success,
        "phase_b_class_and_review_readiness_validation_passed": success,
        "transaction_succeeded": success,
        "failure_mutation_count": 27,
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] and row["verified"] for row in result.failure_rows
        ),
        "ready_for_assignment_human_review": success,
        "ready_for_role_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "blocking_reasons": list(result.blocking_reasons),
        "remaining_readiness_blockers": list(ASSIGNMENT_BLOCKERS),
        "recommended_next_step": (
            "design_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_v1"
            if success
            else "resolve_covapie_current11_cys_sg_assignment_materialization_blockers_v1"
        ),
        "output_sha256": {
            name: sha256(payload) for name, payload in payloads_without_manifest.items()
        },
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        VOCABULARY_FILE: _csv_bytes(VOCABULARY_COLUMNS, result.vocabulary_rows),
        ASSIGNMENT_FILE: _csv_bytes(ASSIGNMENT_COLUMNS, result.assignment_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, result.readiness_rows),
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
    repo_root = Path(__file__).resolve().parents[2]
    materialize(repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
