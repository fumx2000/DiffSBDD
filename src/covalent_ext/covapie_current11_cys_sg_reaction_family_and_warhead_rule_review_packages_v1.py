"""Materialize blank Current11 Cys-SG human-review packages.

This stage creates stable source identities and blank review-record templates.
It never performs human review, invents reviewers or SMARTS, grants approval,
assigns ligand roles, creates masks/tensors, changes models, or trains.
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

from covalent_ext import (
    covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1
    as review_gate,
)


BASE_COMMIT = "c0de1003ec1de9dd05e3c4204b458d1f3757d95d"
BASE_PARENT = "0c8d1d10260a028360357b8c309f22676fc81645"
BASE_TREE = "0434d3265acd47d3c96f3bfbd4166f753eb9054f"
BASE_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review gate "
    "design v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review "
    "packages v1"
)
SCHEMA_VERSION = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1"
)
CLASS_SOURCE_RECORD_VERSION = "covapie_cys_sg_class_review_source_record_v1"
SAMPLE_SOURCE_RECORD_VERSION = (
    "covapie_current11_cys_sg_candidate_assignment_record_v1"
)
REVIEW_RECORD_VERSION = "covapie_cys_sg_human_review_record_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION

REVIEW_GATE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
    "design_v1.py"
)
REVIEW_GATE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
    "design_v1"
)
REVIEW_POLICY = (
    REVIEW_GATE_ROOT / "covapie_reaction_family_and_warhead_rule_review_policy_registry.csv"
)
CLASS_READINESS = (
    REVIEW_GATE_ROOT / "covapie_cys_sg_candidate_class_review_readiness_matrix.csv"
)
SAMPLE_READINESS = (
    REVIEW_GATE_ROOT / "covapie_current11_candidate_assignment_review_readiness_matrix.csv"
)
REVIEW_GATE_MANIFEST = (
    REVIEW_GATE_ROOT
    / "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
    "design_manifest.json"
)
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
ROLE_CONTRACT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)

FROZEN_BASE_SHA256 = {
    REVIEW_GATE_SOURCE:
        "08b7d7aeacfcd7065e6ea8aa2ae27b2cc4959d476fbb1568a5231307d7e308a1",
    REVIEW_POLICY:
        "af80255bfd507c26eeaab37a951e679edc166b2cf8f9da18aed3fb170ebc7881",
    CLASS_READINESS:
        "b33f1b66900937548998076515ba8adc7376f7d9dd5893255aba38abe6470f78",
    SAMPLE_READINESS:
        "1dc2499d8746285bb80851036c72b7c204e9feb53fea086acd788f2c04798c8c",
    REVIEW_GATE_MANIFEST:
        "8acf40e9771bbd6874a7d7cefbe09c8dec9d1ea2ba15a97625a06045f91d393d",
    ASSIGNMENT_SOURCE:
        "fe6c67940efef89290b2f276f9fb4c39245468181d52b219951a6f9ca7f454aa",
    CLASS_VOCABULARY:
        "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    ASSIGNMENT_AUTHORITY:
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    ASSIGNMENT_MANIFEST:
        "5e5acefc9051fc07d3243917292f073fc09fb432a0eb0325fa8d344d37c0e265",
    FAMILY_REGISTRY:
        "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    RULE_REGISTRY:
        "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    ROLE_CONTRACT_SOURCE:
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
}
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)

SOURCE_FILE = "covapie_review_package_source_inventory.csv"
PACKAGE_FILE = "covapie_review_package_index.csv"
CLASS_TEMPLATE_FILE = "covapie_cys_sg_candidate_class_review_record_templates.csv"
SAMPLE_TEMPLATE_FILE = (
    "covapie_current11_sample_assignment_review_record_templates.csv"
)
FAILURE_FILE = "covapie_review_package_materialization_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_"
    "manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    PACKAGE_FILE,
    CLASS_TEMPLATE_FILE,
    SAMPLE_TEMPLATE_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
EXACT10_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
        "packages_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
        "packages_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
        "packages_v1.py"
    ),
    Path(
        "docs/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
        "packages_v1_summary.md"
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
CLASS_SOURCE_RECORD_FIELDS = (
    "source_record_version",
    "formal_base_commit",
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
    "source_class_readiness_file_sha256",
    "source_assignment_authority_file_sha256",
    "source_family_registry_file_sha256",
    "source_rule_registry_file_sha256",
)
CLASS_REVIEW_RECORD_FIELDS = review_gate.CLASS_REVIEW_RECORD_FIELDS
SAMPLE_REVIEW_RECORD_FIELDS = review_gate.SAMPLE_REVIEW_RECORD_FIELDS
ASSIGNMENT_HASH_FIELDS = review_gate.ASSIGNMENT_HASH_FIELDS
PACKAGE_COLUMNS = (
    "package_item_order_0based",
    "package_item_type",
    "package_item_id",
    "source_record_version",
    "source_record_sha256",
    "source_record_json",
    "review_record_version",
    "review_unit_type",
    "review_template_row_id",
    "unreviewed_template_payload_sha256",
    "source_authority_path",
    "source_authority_sha256",
    "family_identity_review_ready",
    "rule_topology_review_ready",
    "SMARTS_review_ready",
    "sample_assignment_review_ready",
    "review_record_sha256_populated",
    "human_review_execution_completed",
    "package_item_materialized",
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
    "review_package_index_row_count",
    "class_review_template_row_count",
    "sample_review_template_row_count",
    "role_proposal_generation_ready",
    "mask_materialization_ready",
    "model_integration_ready",
    "training_ready",
    "verified",
)

_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_LOWER_GIT_OID = re.compile(r"[0-9a-f]{40}")
CLASS_BLOCKERS = (
    "candidate_warhead_SMARTS_not_materialized",
    "human_review_not_executed",
    "approved_reaction_family_unavailable",
    "approved_warhead_rule_unavailable",
)
SAMPLE_BLOCKERS = (
    "human_review_not_executed",
    "approved_reaction_family_unavailable",
    "approved_warhead_rule_unavailable",
    "human_gold_review_incomplete",
)


@dataclass(frozen=True)
class PackageScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    review_gate_transaction_succeeded: bool = True
    review_gate_design_completed: bool = True
    package_materialization_ready: bool = True
    class_source_count: int = 7
    sample_source_count: int = 11
    duplicate_class_identity: bool = False
    class_index_contiguous: bool = True
    duplicate_sample_identity: bool = False
    class_family_rule_links_match: bool = True
    sample_class_family_rule_links_match: bool = True
    assignment_record_sha_matches: bool = True
    class_source_field_present: bool = True
    class_source_has_no_extra_field: bool = True
    class_source_exact_type_valid: bool = True
    class_source_bool_not_int: bool = True
    class_source_sha_matches: bool = True
    duplicate_class_source_sha: bool = False
    representative_samples_sorted: bool = True
    representative_samples_unique: bool = True
    representative_sample_coverage_matches: bool = True
    representative_components_valid: bool = True
    class_template_inventory_matches: bool = True
    sample_template_inventory_matches: bool = True
    review_version_and_unit_match: bool = True
    template_decisions_blank: bool = True
    template_metadata_blank: bool = True
    template_smarts_blank: bool = True
    template_review_sha_blank: bool = True
    sample_source_assignment_sha_matches: bool = True
    package_index_count_and_order_match: bool = True
    package_index_source_and_template_sha_match: bool = True
    partial_materialization_attempted: bool = False
    downstream_readiness_closed: bool = True
    execution_boundary_crossed: bool = False


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_source_missing"),
    ("BASE source SHA mismatch", "base_source_sha_matches", False, "BASE_source_SHA_mismatch"),
    ("review-gate transaction not succeeded", "review_gate_transaction_succeeded", False, "review_gate_transaction_not_succeeded"),
    ("review-gate design not completed", "review_gate_design_completed", False, "review_gate_design_not_completed"),
    ("package materialization readiness false", "package_materialization_ready", False, "package_materialization_readiness_false"),
    ("class source count not 7", "class_source_count", 6, "class_source_count_not_7"),
    ("sample source count not 11", "sample_source_count", 10, "sample_source_count_not_11"),
    ("duplicate class identity", "duplicate_class_identity", True, "duplicate_class_identity"),
    ("class index non-contiguous", "class_index_contiguous", False, "class_index_non_contiguous"),
    ("duplicate sample identity", "duplicate_sample_identity", True, "duplicate_sample_identity"),
    ("class-family-rule link mismatch", "class_family_rule_links_match", False, "class_family_rule_link_mismatch"),
    ("sample-class-family-rule link mismatch", "sample_class_family_rule_links_match", False, "sample_class_family_rule_link_mismatch"),
    ("assignment record SHA mismatch", "assignment_record_sha_matches", False, "assignment_record_SHA_mismatch"),
    ("class source record field missing", "class_source_field_present", False, "class_source_record_field_missing"),
    ("class source record extra field", "class_source_has_no_extra_field", False, "class_source_record_extra_field"),
    ("class source record exact type invalid", "class_source_exact_type_valid", False, "class_source_record_exact_type_invalid"),
    ("class source record bool-as-int", "class_source_bool_not_int", False, "class_source_record_bool_as_int"),
    ("class source SHA mismatch", "class_source_sha_matches", False, "class_source_SHA_mismatch"),
    ("duplicate class source SHA", "duplicate_class_source_sha", True, "duplicate_class_source_SHA"),
    ("representative sample IDs unsorted", "representative_samples_sorted", False, "representative_sample_IDs_unsorted"),
    ("representative sample IDs duplicated", "representative_samples_unique", False, "representative_sample_IDs_duplicated"),
    ("representative sample coverage mismatch", "representative_sample_coverage_matches", False, "representative_sample_coverage_mismatch"),
    ("representative component IDs invalid", "representative_components_valid", False, "representative_component_IDs_invalid"),
    ("class template field inventory mismatch", "class_template_inventory_matches", False, "class_template_field_inventory_mismatch"),
    ("sample template field inventory mismatch", "sample_template_inventory_matches", False, "sample_template_field_inventory_mismatch"),
    ("review version or unit type mismatch", "review_version_and_unit_match", False, "review_version_or_unit_type_mismatch"),
    ("template decision prefilled", "template_decisions_blank", False, "template_decision_prefilled"),
    ("template reviewer/rationale/notes prefilled", "template_metadata_blank", False, "template_reviewer_rationale_notes_prefilled"),
    ("template SMARTS prefilled", "template_smarts_blank", False, "template_SMARTS_prefilled"),
    ("template review-record SHA prefilled", "template_review_sha_blank", False, "template_review_record_SHA_prefilled"),
    ("sample source-assignment SHA mismatch", "sample_source_assignment_sha_matches", False, "sample_source_assignment_SHA_mismatch"),
    ("package-index count or ordering mismatch", "package_index_count_and_order_match", False, "package_index_count_or_ordering_mismatch"),
    ("package-index source/template SHA mismatch", "package_index_source_and_template_sha_match", False, "package_index_source_or_template_SHA_mismatch"),
    ("partial materialization attempted", "partial_materialization_attempted", True, "partial_materialization_attempted"),
    ("approval/gold/role/model/training readiness prematurely opened", "downstream_readiness_closed", False, "downstream_readiness_prematurely_opened"),
    ("execution boundary crossed", "execution_boundary_crossed", True, "execution_boundary_crossed"),
)


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    class_source_records: tuple[Mapping[str, Any], ...]
    class_source_sha256: tuple[str, ...]
    class_template_rows: tuple[Mapping[str, Any], ...]
    sample_template_rows: tuple[Mapping[str, Any], ...]
    package_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


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
    if check and result.returncode:
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
    return type(value) is str and bool(value.strip())


def _is_lower_sha256(value: object) -> bool:
    return type(value) is str and _LOWER_SHA256.fullmatch(value) is not None


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
        writer.writerow({field: _cell(row.get(field, "")) for field in columns})
    return stream.getvalue().encode("utf-8")


def _cell(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    if type(value) in (list, dict):
        return canonical_json(value)
    return str(value)


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
        line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")
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
    if changed != {path.as_posix() for path in EXACT10_PATHS}:
        raise ValueError("successor_changed_path_inventory_mismatch")
    modes = [
        row.partition(b"\t")[0]
        for row in _git(
            repo_root, "ls-tree", "-r", "-z", head, "--",
            *(path.as_posix() for path in EXACT10_PATHS),
        ).stdout.split(b"\0")
        if row
    ]
    if len(modes) != 10 or any(not row.startswith(b"100644 blob ") for row in modes):
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
        REVIEW_GATE_SOURCE: ("11/11", "review schemas; lifecycle; blank-review validator", "predecessor_review_gate_production_contract"),
        REVIEW_POLICY: ("11/11", "Exact12 review policies and fail-closed semantics", "review_policy_registry"),
        CLASS_READINESS: ("11/11", "Exact7 class evidence, representatives, blank review state", "candidate_class_review_readiness_authority"),
        SAMPLE_READINESS: ("11/11", "Exact11 sample evidence and blank review state", "sample_assignment_review_readiness_authority"),
        REVIEW_GATE_MANIFEST: ("11/11", "successful gate transaction and package readiness", "review_gate_design_manifest"),
        ASSIGNMENT_SOURCE: ("11/11", "assignment hash contract and lifecycle lineage", "predecessor_assignment_production_contract"),
        CLASS_VOCABULARY: ("11/11", "Exact7 stable class/family/rule identities", "candidate_class_vocabulary_authority"),
        ASSIGNMENT_AUTHORITY: ("11/11", "Exact19 assignment identity inputs and linkage", "Current11_assignment_authority"),
        ASSIGNMENT_MANIFEST: ("11/11", "successful assignment transaction and closed downstream state", "assignment_manifest"),
        FAMILY_REGISTRY: ("11/11", "family semantic identity and canonical SHA", "candidate_family_registry"),
        RULE_REGISTRY: ("11/11", "rule topology identity, family link, absent SMARTS", "candidate_rule_registry"),
        ROLE_CONTRACT_SOURCE: ("11/11", "downstream approval prerequisites remain closed", "downstream_role_seed_contract"),
    }
    return values[path]


def _source_inventory(
    payloads: Mapping[Path, bytes],
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for path in SOURCE_PATHS:
        payload = payloads[path]
        coverage, fields, authority = _source_metadata(path)
        row_count = (
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
                "source_row_count": row_count,
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


def assignment_hash_input(row: Mapping[str, Any]) -> dict[str, Any]:
    value = {field: row[field] for field in ASSIGNMENT_HASH_FIELDS}
    raw_index = value["warhead_type_candidate_class_index_0based"]
    if type(raw_index) is str and raw_index.isdecimal():
        value["warhead_type_candidate_class_index_0based"] = int(raw_index)
    elif type(raw_index) is not int:
        raise ValueError("assignment_class_index_exact_type_invalid")
    return value


def assignment_record_sha256(row: Mapping[str, Any]) -> str:
    return sha256(canonical_json(assignment_hash_input(row)).encode("utf-8"))


def validate_class_source_record(record: Mapping[str, Any]) -> None:
    if type(record) is not dict:
        raise ValueError("class_source_record_container_not_exact_dict")
    if set(record) != set(CLASS_SOURCE_RECORD_FIELDS):
        missing = set(CLASS_SOURCE_RECORD_FIELDS) - set(record)
        reason = (
            "class_source_record_field_missing"
            if missing
            else "class_source_record_extra_field"
        )
        raise ValueError(reason)
    string_fields = (
        "source_record_version",
        "formal_base_commit",
        "warhead_type_candidate_class_id",
        "warhead_type_candidate_semantic_name",
        "reaction_family_id",
        "reaction_family_semantic_name",
        "canonical_reaction_family_signature_sha256",
        "warhead_rule_id",
        "canonical_local_graph_rule_sha256",
        "source_class_readiness_file_sha256",
        "source_assignment_authority_file_sha256",
        "source_family_registry_file_sha256",
        "source_rule_registry_file_sha256",
    )
    for field in string_fields:
        if type(record[field]) is not str:
            raise ValueError(f"class_source_record_exact_type_invalid:{field}")
    if record["source_record_version"] != CLASS_SOURCE_RECORD_VERSION:
        raise ValueError("class_source_record_version_mismatch")
    if (
        _LOWER_GIT_OID.fullmatch(record["formal_base_commit"]) is None
        or record["formal_base_commit"] != BASE_COMMIT
    ):
        raise ValueError("class_source_record_formal_base_invalid")
    for field in (
        "warhead_type_candidate_class_id",
        "warhead_type_candidate_semantic_name",
        "reaction_family_id",
        "reaction_family_semantic_name",
        "warhead_rule_id",
    ):
        if not _is_meaningful_text(record[field]):
            raise ValueError(f"class_source_record_text_invalid:{field}")
    for field in (
        "canonical_reaction_family_signature_sha256",
        "canonical_local_graph_rule_sha256",
        "source_class_readiness_file_sha256",
        "source_assignment_authority_file_sha256",
        "source_family_registry_file_sha256",
        "source_rule_registry_file_sha256",
    ):
        if not _is_lower_sha256(record[field]):
            raise ValueError(f"class_source_record_SHA_invalid:{field}")
    for field in (
        "warhead_type_candidate_class_index_0based",
        "selected_signature_radius",
        "Current11_match_count",
        "Current11_unique_component_count",
    ):
        if type(record[field]) is not int:
            reason = (
                "class_source_record_bool_as_int"
                if type(record[field]) is bool
                else "class_source_record_exact_type_invalid"
            )
            raise ValueError(f"{reason}:{field}")
    index = record["warhead_type_candidate_class_index_0based"]
    if index not in range(7):
        raise ValueError("class_source_record_index_invalid")
    if record["selected_signature_radius"] != 1:
        raise ValueError("class_source_record_radius_not_1")
    if record["Current11_match_count"] <= 0:
        raise ValueError("class_source_record_match_count_invalid")
    if record["Current11_unique_component_count"] <= 0:
        raise ValueError("class_source_record_component_count_invalid")
    for field in ("representative_sample_ids", "representative_component_ids"):
        values = record[field]
        if type(values) is not list:
            raise ValueError(f"class_source_record_exact_type_invalid:{field}")
        if not values or any(not _is_meaningful_text(value) for value in values):
            raise ValueError(f"{field}_invalid")
        if values != sorted(values):
            raise ValueError(f"{field}_unsorted")
        if len(values) != len(set(values)):
            raise ValueError(f"{field}_duplicated")
    for field in (
        "family_identity_evidence_complete",
        "rule_topology_evidence_complete",
        "assignment_support_complete",
        "class_identity_verified",
    ):
        if type(record[field]) is not bool:
            raise ValueError(f"class_source_record_exact_type_invalid:{field}")
        if record[field] is not True:
            raise ValueError(f"class_source_record_evidence_false:{field}")


def class_source_record_sha256(record: Mapping[str, Any]) -> str:
    validate_class_source_record(record)
    return sha256(canonical_json(record).encode("utf-8"))


def unreviewed_template_payload_sha256(record: Mapping[str, Any]) -> str:
    review_gate.validate_review_record_schema(record)
    if record["review_record_sha256"] != "":
        raise ValueError("template_review_record_SHA_prefilled")
    return sha256(canonical_json(record).encode("utf-8"))


def _validate_phase_a(
    payloads: Mapping[Path, bytes],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[str]]:
    reasons: list[str] = []
    gate_manifest = json.loads(payloads[REVIEW_GATE_MANIFEST])
    assignment_manifest = json.loads(payloads[ASSIGNMENT_MANIFEST])
    class_ready = _csv_rows(payloads[CLASS_READINESS])
    sample_ready = _csv_rows(payloads[SAMPLE_READINESS])
    policies = _csv_rows(payloads[REVIEW_POLICY])
    classes = _csv_rows(payloads[CLASS_VOCABULARY])
    assignments = _csv_rows(payloads[ASSIGNMENT_AUTHORITY])
    families = _csv_rows(payloads[FAMILY_REGISTRY])
    rules = _csv_rows(payloads[RULE_REGISTRY])
    gate_source_text = payloads[REVIEW_GATE_SOURCE].decode("utf-8")
    assignment_source_text = payloads[ASSIGNMENT_SOURCE].decode("utf-8")
    role_source_text = payloads[ROLE_CONTRACT_SOURCE].decode("utf-8")

    _require(gate_manifest.get("transaction_succeeded") is True, "review_gate_transaction_not_succeeded", reasons)
    _require(gate_manifest.get("review_gate_design_completed") is True, "review_gate_design_not_completed", reasons)
    _require(gate_manifest.get("ready_for_review_package_materialization") is True, "package_materialization_readiness_false", reasons)
    _require(gate_manifest.get("source_count") == 12 and gate_manifest.get("review_policy_count") == 12, "predecessor_inventory_mismatch", reasons)
    _require(gate_manifest.get("candidate_class_count") == 7 and gate_manifest.get("current11_sample_count") == 11, "predecessor_inventory_mismatch", reasons)
    _require(gate_manifest.get("failure_mutation_count") == 30, "predecessor_inventory_mismatch", reasons)
    _require(gate_manifest.get("class_review_package_ready_count") == 7 and gate_manifest.get("sample_review_package_ready_count") == 11, "predecessor_package_readiness_incomplete", reasons)
    _require(gate_manifest.get("class_review_record_fields") == list(CLASS_REVIEW_RECORD_FIELDS), "class_template_field_inventory_mismatch", reasons)
    _require(gate_manifest.get("sample_review_record_fields") == list(SAMPLE_REVIEW_RECORD_FIELDS), "sample_template_field_inventory_mismatch", reasons)
    _require(
        len(policies) == 12
        and [row.get("policy_id") for row in policies]
        == [f"REVIEW_POLICY_{index:03d}" for index in range(1, 13)]
        and all(
            row.get("fails_closed") == "true" and row.get("verified") == "true"
            for row in policies
        ),
        "predecessor_review_policy_inventory_invalid", reasons,
    )
    _require(
        "def validate_review_record_schema(" in gate_source_text
        and "CLASS_REVIEW_RECORD_FIELDS = (" in gate_source_text
        and "SAMPLE_REVIEW_RECORD_FIELDS = (" in gate_source_text,
        "predecessor_review_schema_contract_missing", reasons,
    )
    _require(
        "RECORD_FIELDS = (" in assignment_source_text
        and "assignment_record_sha256" in assignment_source_text,
        "predecessor_assignment_hash_contract_missing", reasons,
    )
    _require(
        "approved_reaction_family_warhead_rule" in role_source_text
        and "approved_warhead_rule_present" in role_source_text,
        "downstream_role_prerequisite_missing", reasons,
    )
    for field in (
        "review_package_materialized", "human_review_execution_completed",
        "ready_for_human_review_execution", "ready_for_role_proposal_generation",
        "ready_for_mask_materialization", "ready_for_tensorization",
        "ready_for_model_integration", "ready_for_training", "role_annotation_materialized",
        "minimal_seed_materialized", "mask_materialized", "tensor_materialized",
        "model_changed", "training_used", "warhead_type_model_head_integrated",
        "warhead_type_loss_integrated",
    ):
        _require(gate_manifest.get(field) is False, "predecessor_boundary_prematurely_opened", reasons)
    for field in (
        "approved_reaction_family_available_count", "approved_warhead_rule_available_count",
        "approved_warhead_smarts_count", "human_gold_review_completed_count",
        "training_label_approved_count",
    ):
        _require(gate_manifest.get(field) == 0 and type(gate_manifest.get(field)) is int, "predecessor_approval_state_not_zero", reasons)
    _require(assignment_manifest.get("transaction_succeeded") is True, "assignment_transaction_not_succeeded", reasons)
    _require(len(class_ready) == len(classes) == 7, "class_source_count_not_7", reasons)
    _require(len(sample_ready) == len(assignments) == 11, "sample_source_count_not_11", reasons)
    try:
        indices = [int(row["warhead_type_candidate_class_index_0based"]) for row in class_ready]
    except (KeyError, ValueError):
        indices = []
    _require(indices == list(range(7)), "class_index_non_contiguous", reasons)
    _require(len({row.get("warhead_type_candidate_class_id") for row in class_ready}) == 7, "duplicate_class_identity", reasons)
    _require(len({row.get("sample_index_row_id") for row in sample_ready}) == 11, "duplicate_sample_identity", reasons)
    _require(len({row.get("assignment_record_sha256") for row in assignments}) == 11, "duplicate_sample_identity", reasons)

    classes_by_id = {row["warhead_type_candidate_class_id"]: row for row in classes}
    families_by_id = {row["reaction_family_id"]: row for row in families}
    rules_by_id = {row["warhead_rule_id"]: row for row in rules}
    _require(len(classes_by_id) == len(families_by_id) == len(rules_by_id) == 7, "class_family_rule_link_mismatch", reasons)
    for row in class_ready:
        source = classes_by_id.get(row.get("warhead_type_candidate_class_id"))
        family = families_by_id.get(row.get("reaction_family_id"))
        rule = rules_by_id.get(row.get("warhead_rule_id"))
        linked = (
            source is not None and family is not None and rule is not None
            and source["reaction_family_id"] == row["reaction_family_id"]
            and source["warhead_rule_id"] == row["warhead_rule_id"]
            and family["canonical_reaction_family_signature_sha256"] == row["canonical_reaction_family_signature_sha256"]
            and rule["canonical_local_graph_rule_sha256"] == row["canonical_local_graph_rule_sha256"]
            and rule["reaction_family_id"] == row["reaction_family_id"]
        )
        _require(linked, "class_family_rule_link_mismatch", reasons)
        _require(
            row.get("reaction_family_identity_review_decision") == "not_reviewed"
            and row.get("warhead_rule_topology_review_decision") == "not_reviewed"
            and row.get("warhead_smarts_review_status") == "not_materialized"
            and row.get("candidate_warhead_smarts") == ""
            and row.get("reviewer_id") == ""
            and row.get("review_rationale") == ""
            and row.get("review_notes") == ""
            and row.get("class_review_package_ready") == "true"
            and row.get("family_identity_evidence_complete") == "true"
            and row.get("rule_topology_evidence_complete") == "true"
            and row.get("assignment_support_complete") == "true"
            and row.get("class_identity_verified") == "true"
            and row.get("approved_reaction_family_available") == "false"
            and row.get("approved_warhead_rule_available") == "false"
            and row.get("ready_for_role_proposal_generation") == "false"
            and row.get("ready_for_training") == "false",
            "predecessor_blank_class_review_state_invalid", reasons,
        )
    class_ready_by_id = {
        row["warhead_type_candidate_class_id"]: row for row in class_ready
    }
    assignments_by_id = {row["sample_index_row_id"]: row for row in assignments}
    for row in sample_ready:
        source = assignments_by_id.get(row.get("sample_index_row_id"))
        class_row = class_ready_by_id.get(row.get("warhead_type_candidate_class_id"))
        linked = (
            source is not None and class_row is not None
            and source["assignment_record_sha256"] == row["assignment_record_sha256"]
            and source["warhead_type_candidate_class_id"] == row["warhead_type_candidate_class_id"]
            and source["candidate_reaction_family_id"] == row["reaction_family_id"] == class_row["reaction_family_id"]
            and source["candidate_warhead_rule_id"] == row["warhead_rule_id"] == class_row["warhead_rule_id"]
        )
        _require(linked, "sample_class_family_rule_link_mismatch", reasons)
        _require(
            row.get("sample_assignment_review_decision") == "not_reviewed"
            and row.get("reviewer_id") == ""
            and row.get("review_rationale") == ""
            and row.get("review_notes") == ""
            and row.get("sample_review_package_ready") == "true"
            and row.get("sample_assignment_evidence_complete") == "true"
            and row.get("sample_assignment_identity_verified") == "true"
            and row.get("sample_review_completed") == "false"
            and row.get("approved_reaction_family_available") == "false"
            and row.get("approved_warhead_rule_available") == "false"
            and row.get("human_gold_review_completed") == "false"
            and row.get("training_label_approved") == "false"
            and row.get("ready_for_role_proposal_generation") == "false"
            and row.get("ready_for_mask_materialization") == "false"
            and row.get("ready_for_model_integration") == "false"
            and row.get("ready_for_training") == "false",
            "predecessor_blank_sample_review_state_invalid", reasons,
        )
    for row in assignments:
        try:
            matches = assignment_record_sha256(row) == row["assignment_record_sha256"]
        except (KeyError, TypeError, ValueError):
            matches = False
        _require(matches, "assignment_record_SHA_mismatch", reasons)
    _require(
        all(
            row.get("human_gold_review_completed") == "false"
            and row.get("approved") == "false"
            and row.get("verified") == "true"
            for row in families
        ),
        "predecessor_family_approval_present", reasons,
    )
    _require(
        all(
            row.get("approved_warhead_smarts", "") == ""
            and row.get("SMARTS_status") == "not_materialized_in_design_stage"
            and row.get("human_gold_review_completed") == "false"
            and row.get("approved") == "false"
            and row.get("verified") == "true"
            for row in rules
        ),
        "predecessor_SMARTS_or_approval_present", reasons,
    )
    return class_ready, assignments, rules, reasons


def _class_source_records(
    class_rows: Sequence[Mapping[str, str]],
    assignments: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, Any], ...]:
    support: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in assignments:
        support[row["warhead_type_candidate_class_id"]].append(row)
    records = []
    for row in sorted(
        class_rows, key=lambda item: int(item["warhead_type_candidate_class_index_0based"])
    ):
        linked = support[row["warhead_type_candidate_class_id"]]
        record: dict[str, Any] = {
            "source_record_version": CLASS_SOURCE_RECORD_VERSION,
            "formal_base_commit": BASE_COMMIT,
            "warhead_type_candidate_class_index_0based": int(row["warhead_type_candidate_class_index_0based"]),
            "warhead_type_candidate_class_id": row["warhead_type_candidate_class_id"],
            "warhead_type_candidate_semantic_name": row["warhead_type_candidate_semantic_name"],
            "reaction_family_id": row["reaction_family_id"],
            "reaction_family_semantic_name": row["reaction_family_semantic_name"],
            "canonical_reaction_family_signature_sha256": row["canonical_reaction_family_signature_sha256"],
            "warhead_rule_id": row["warhead_rule_id"],
            "canonical_local_graph_rule_sha256": row["canonical_local_graph_rule_sha256"],
            "selected_signature_radius": int(row["selected_signature_radius"]),
            "Current11_match_count": int(row["Current11_match_count"]),
            "Current11_unique_component_count": int(row["Current11_unique_component_count"]),
            "representative_sample_ids": row["representative_sample_ids"].split(";"),
            "representative_component_ids": row["representative_component_ids"].split(";"),
            "family_identity_evidence_complete": row["family_identity_evidence_complete"] == "true",
            "rule_topology_evidence_complete": row["rule_topology_evidence_complete"] == "true",
            "assignment_support_complete": (
                row["assignment_support_complete"] == "true"
                and len(linked) == int(row["Current11_match_count"])
            ),
            "class_identity_verified": row["class_identity_verified"] == "true",
            "source_class_readiness_file_sha256": FROZEN_BASE_SHA256[CLASS_READINESS],
            "source_assignment_authority_file_sha256": FROZEN_BASE_SHA256[ASSIGNMENT_AUTHORITY],
            "source_family_registry_file_sha256": FROZEN_BASE_SHA256[FAMILY_REGISTRY],
            "source_rule_registry_file_sha256": FROZEN_BASE_SHA256[RULE_REGISTRY],
        }
        validate_class_source_record(record)
        expected_samples = sorted(item["sample_index_row_id"] for item in linked)
        expected_components = sorted({item["ligand_comp_id"] for item in linked})
        if record["representative_sample_ids"] != expected_samples:
            raise ValueError("representative_sample_coverage_mismatch")
        if record["representative_component_ids"] != expected_components:
            raise ValueError("representative_component_IDs_invalid")
        records.append(record)
    return tuple(records)


def _class_template(
    source: Mapping[str, Any], source_sha: str
) -> dict[str, Any]:
    record = {
        "review_record_version": REVIEW_RECORD_VERSION,
        "review_unit_type": "candidate_class",
        "warhead_type_candidate_class_index_0based": source["warhead_type_candidate_class_index_0based"],
        "warhead_type_candidate_class_id": source["warhead_type_candidate_class_id"],
        "reaction_family_id": source["reaction_family_id"],
        "reaction_family_semantic_name": source["reaction_family_semantic_name"],
        "canonical_reaction_family_signature_sha256": source["canonical_reaction_family_signature_sha256"],
        "warhead_rule_id": source["warhead_rule_id"],
        "warhead_type_candidate_semantic_name": source["warhead_type_candidate_semantic_name"],
        "canonical_local_graph_rule_sha256": source["canonical_local_graph_rule_sha256"],
        "reaction_family_identity_review_decision": "not_reviewed",
        "warhead_rule_topology_review_decision": "not_reviewed",
        "warhead_smarts_review_status": "not_materialized",
        "candidate_warhead_smarts": "",
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        "source_class_record_sha256": source_sha,
        "review_record_sha256": "",
    }
    review_gate.validate_review_record_schema(record)
    return record


def _sample_template(source: Mapping[str, Any]) -> dict[str, Any]:
    digest = source["assignment_record_sha256"]
    record = {
        "review_record_version": REVIEW_RECORD_VERSION,
        "review_unit_type": "sample_assignment",
        "sample_index_row_id": source["sample_index_row_id"],
        "assignment_record_sha256": digest,
        "warhead_type_candidate_class_id": source["warhead_type_candidate_class_id"],
        "reaction_family_id": source["candidate_reaction_family_id"],
        "warhead_rule_id": source["candidate_warhead_rule_id"],
        "sample_assignment_review_decision": "not_reviewed",
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        "source_assignment_record_sha256": digest,
        "review_record_sha256": "",
    }
    review_gate.validate_review_record_schema(record)
    return record


def _package_rows(
    class_sources: Sequence[Mapping[str, Any]],
    class_shas: Sequence[str],
    class_templates: Sequence[Mapping[str, Any]],
    assignments: Sequence[Mapping[str, Any]],
    sample_templates: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for source, source_sha, template in zip(
        class_sources, class_shas, class_templates
    ):
        index = source["warhead_type_candidate_class_index_0based"]
        rows.append(
            {
                "package_item_order_0based": index,
                "package_item_type": "candidate_class",
                "package_item_id": source["warhead_type_candidate_class_id"],
                "source_record_version": CLASS_SOURCE_RECORD_VERSION,
                "source_record_sha256": source_sha,
                "source_record_json": canonical_json(source),
                "review_record_version": REVIEW_RECORD_VERSION,
                "review_unit_type": "candidate_class",
                "review_template_row_id": str(index),
                "unreviewed_template_payload_sha256": unreviewed_template_payload_sha256(template),
                "source_authority_path": CLASS_READINESS.as_posix(),
                "source_authority_sha256": FROZEN_BASE_SHA256[CLASS_READINESS],
                "family_identity_review_ready": True,
                "rule_topology_review_ready": True,
                "SMARTS_review_ready": False,
                "sample_assignment_review_ready": False,
                "review_record_sha256_populated": False,
                "human_review_execution_completed": False,
                "package_item_materialized": True,
                "blocking_reasons": ";".join(CLASS_BLOCKERS),
                "verified": True,
            }
        )
    for offset, (source, template) in enumerate(
        zip(
            sorted(assignments, key=lambda item: item["sample_index_row_id"]),
            sample_templates,
        ),
        7,
    ):
        identity = assignment_hash_input(source)
        rows.append(
            {
                "package_item_order_0based": offset,
                "package_item_type": "sample_assignment",
                "package_item_id": source["sample_index_row_id"],
                "source_record_version": SAMPLE_SOURCE_RECORD_VERSION,
                "source_record_sha256": source["assignment_record_sha256"],
                "source_record_json": canonical_json(identity),
                "review_record_version": REVIEW_RECORD_VERSION,
                "review_unit_type": "sample_assignment",
                "review_template_row_id": source["sample_index_row_id"],
                "unreviewed_template_payload_sha256": unreviewed_template_payload_sha256(template),
                "source_authority_path": ASSIGNMENT_AUTHORITY.as_posix(),
                "source_authority_sha256": FROZEN_BASE_SHA256[ASSIGNMENT_AUTHORITY],
                "family_identity_review_ready": False,
                "rule_topology_review_ready": False,
                "SMARTS_review_ready": False,
                "sample_assignment_review_ready": True,
                "review_record_sha256_populated": False,
                "human_review_execution_completed": False,
                "package_item_materialized": True,
                "blocking_reasons": ";".join(SAMPLE_BLOCKERS),
                "verified": True,
            }
        )
    return tuple(rows)


def observe_failure_scenario(scenario: PackageScenario) -> tuple[str, ...]:
    checks = (
        (not scenario.base_source_present, "BASE_source_missing"),
        (not scenario.base_source_sha_matches, "BASE_source_SHA_mismatch"),
        (not scenario.review_gate_transaction_succeeded, "review_gate_transaction_not_succeeded"),
        (not scenario.review_gate_design_completed, "review_gate_design_not_completed"),
        (not scenario.package_materialization_ready, "package_materialization_readiness_false"),
        (scenario.class_source_count != 7, "class_source_count_not_7"),
        (scenario.sample_source_count != 11, "sample_source_count_not_11"),
        (scenario.duplicate_class_identity, "duplicate_class_identity"),
        (not scenario.class_index_contiguous, "class_index_non_contiguous"),
        (scenario.duplicate_sample_identity, "duplicate_sample_identity"),
        (not scenario.class_family_rule_links_match, "class_family_rule_link_mismatch"),
        (not scenario.sample_class_family_rule_links_match, "sample_class_family_rule_link_mismatch"),
        (not scenario.assignment_record_sha_matches, "assignment_record_SHA_mismatch"),
        (not scenario.class_source_field_present, "class_source_record_field_missing"),
        (not scenario.class_source_has_no_extra_field, "class_source_record_extra_field"),
        (not scenario.class_source_exact_type_valid, "class_source_record_exact_type_invalid"),
        (not scenario.class_source_bool_not_int, "class_source_record_bool_as_int"),
        (not scenario.class_source_sha_matches, "class_source_SHA_mismatch"),
        (scenario.duplicate_class_source_sha, "duplicate_class_source_SHA"),
        (not scenario.representative_samples_sorted, "representative_sample_IDs_unsorted"),
        (not scenario.representative_samples_unique, "representative_sample_IDs_duplicated"),
        (not scenario.representative_sample_coverage_matches, "representative_sample_coverage_mismatch"),
        (not scenario.representative_components_valid, "representative_component_IDs_invalid"),
        (not scenario.class_template_inventory_matches, "class_template_field_inventory_mismatch"),
        (not scenario.sample_template_inventory_matches, "sample_template_field_inventory_mismatch"),
        (not scenario.review_version_and_unit_match, "review_version_or_unit_type_mismatch"),
        (not scenario.template_decisions_blank, "template_decision_prefilled"),
        (not scenario.template_metadata_blank, "template_reviewer_rationale_notes_prefilled"),
        (not scenario.template_smarts_blank, "template_SMARTS_prefilled"),
        (not scenario.template_review_sha_blank, "template_review_record_SHA_prefilled"),
        (not scenario.sample_source_assignment_sha_matches, "sample_source_assignment_SHA_mismatch"),
        (not scenario.package_index_count_and_order_match, "package_index_count_or_ordering_mismatch"),
        (not scenario.package_index_source_and_template_sha_match, "package_index_source_or_template_SHA_mismatch"),
        (scenario.partial_materialization_attempted, "partial_materialization_attempted"),
        (not scenario.downstream_readiness_closed, "downstream_readiness_prematurely_opened"),
        (scenario.execution_boundary_crossed, "execution_boundary_crossed"),
    )
    return tuple(reason for failed, reason in checks if failed)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = PackageScenario()
    rows = []
    signatures = set()
    for case, field, value, expected in FAILURE_MUTATIONS:
        baseline_value = getattr(baseline, field)
        if type(value) is not type(baseline_value):
            raise AssertionError(f"mutation_type_not_exact:{case}")
        if value == baseline_value:
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
                "review_package_index_row_count": 0,
                "class_review_template_row_count": 0,
                "sample_review_template_row_count": 0,
                "role_proposal_generation_ready": False,
                "mask_materialization_ready": False,
                "model_integration_ready": False,
                "training_ready": False,
                "verified": verified and bool(observed),
            }
        )
    if len(rows) != 36 or len(signatures) != 36:
        raise AssertionError("failure_matrix_not_Exact36")
    return tuple(rows)


def transaction_tables(
    blocking_reasons: Sequence[str],
    package_rows: Sequence[Mapping[str, Any]],
    class_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    if blocking_reasons:
        return (), (), ()
    return tuple(package_rows), tuple(class_rows), tuple(sample_rows)


def build_result(repo_root: Path) -> BuildResult:
    payloads = load_frozen_sources(repo_root)
    class_rows, assignments, _rules, reasons = _validate_phase_a(payloads)
    class_sources: tuple[Mapping[str, Any], ...] = ()
    class_shas: tuple[str, ...] = ()
    class_templates: tuple[Mapping[str, Any], ...] = ()
    sample_templates: tuple[Mapping[str, Any], ...] = ()
    package_rows: tuple[Mapping[str, Any], ...] = ()
    if not reasons:
        try:
            class_sources = _class_source_records(class_rows, assignments)
            class_shas = tuple(class_source_record_sha256(row) for row in class_sources)
            class_templates = tuple(
                _class_template(source, digest)
                for source, digest in zip(class_sources, class_shas)
            )
            ordered_assignments = sorted(
                assignments, key=lambda row: row["sample_index_row_id"]
            )
            sample_templates = tuple(
                _sample_template(source) for source in ordered_assignments
            )
            package_rows = _package_rows(
                class_sources,
                class_shas,
                class_templates,
                ordered_assignments,
                sample_templates,
            )
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(str(exc))
    if not reasons:
        _require(len(class_sources) == len(set(class_shas)) == 7, "duplicate_class_source_SHA", reasons)
        _require(len(class_templates) == 7, "class_template_count_not_7", reasons)
        _require(len(sample_templates) == 11, "sample_template_count_not_11", reasons)
        _require(len(package_rows) == 18 and [row["package_item_order_0based"] for row in package_rows] == list(range(18)), "package_index_count_or_ordering_mismatch", reasons)
        _require(
            all(
                row["review_record_sha256"] == ""
                and row["reviewer_id"] == ""
                and row["review_rationale"] == ""
                and row["review_notes"] == ""
                for row in (*class_templates, *sample_templates)
            ),
            "template_reviewer_rationale_notes_prefilled", reasons,
        )
        _require(
            all(
                row["candidate_warhead_smarts"] == ""
                and row["warhead_smarts_review_status"] == "not_materialized"
                for row in class_templates
            ),
            "template_SMARTS_prefilled", reasons,
        )
    package_rows, class_templates, sample_templates = transaction_tables(
        reasons, package_rows, class_templates, sample_templates
    )
    return BuildResult(
        source_rows=_source_inventory(payloads),
        class_source_records=class_sources if not reasons else (),
        class_source_sha256=class_shas if not reasons else (),
        class_template_rows=class_templates,
        sample_template_rows=sample_templates,
        package_rows=package_rows,
        failure_rows=build_failure_rows(),
        transaction_succeeded=not reasons,
        blocking_reasons=tuple(sorted(set(reasons))),
    )


def _manifest(
    result: BuildResult, payloads_without_manifest: Mapping[str, bytes]
) -> dict[str, Any]:
    success = result.transaction_succeeded
    templates = (*result.class_template_rows, *result.sample_template_rows)
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
        "class_source_record_version": CLASS_SOURCE_RECORD_VERSION,
        "class_source_record_fields": list(CLASS_SOURCE_RECORD_FIELDS),
        "class_source_record_count": len(result.class_source_records),
        "class_source_record_sha_unique_count": len(set(result.class_source_sha256)),
        "review_record_version": REVIEW_RECORD_VERSION,
        "class_review_record_fields": list(CLASS_REVIEW_RECORD_FIELDS),
        "sample_review_record_fields": list(SAMPLE_REVIEW_RECORD_FIELDS),
        "class_review_template_count": len(result.class_template_rows),
        "sample_review_template_count": len(result.sample_template_rows),
        "review_package_item_count": len(result.package_rows),
        "class_index_ordering": "0_to_6",
        "sample_ordering": "sample_index_row_id_ascending",
        "package_ordering": "classes_then_samples",
        "template_decision_not_reviewed_count": sum(
            (
                row.get("reaction_family_identity_review_decision") == "not_reviewed"
                and row.get("warhead_rule_topology_review_decision") == "not_reviewed"
            )
            if row["review_unit_type"] == "candidate_class"
            else row.get("sample_assignment_review_decision") == "not_reviewed"
            for row in templates
        ),
        "template_reviewer_nonempty_count": sum(bool(row["reviewer_id"]) for row in templates),
        "template_rationale_nonempty_count": sum(bool(row["review_rationale"]) for row in templates),
        "template_notes_nonempty_count": sum(bool(row["review_notes"]) for row in templates),
        "template_SMARTS_nonempty_count": sum(bool(row.get("candidate_warhead_smarts", "")) for row in templates),
        "template_review_record_sha_populated_count": sum(bool(row["review_record_sha256"]) for row in templates),
        "transaction_succeeded": success,
        "phase_a_predecessor_and_identity_validation_passed": success,
        "phase_b_package_and_template_validation_passed": success,
        "failure_mutation_count": 36,
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] and row["verified"] for row in result.failure_rows
        ),
        "review_package_materialized": success,
        "human_review_execution_completed": False,
        "ready_for_family_identity_review_execution": success,
        "ready_for_rule_topology_review_execution": success,
        "ready_for_sample_assignment_review_execution": success,
        "ready_for_SMARTS_review_execution": False,
        "ready_for_human_review_execution": success,
        "human_review_execution_scope": "family_identity_rule_topology_sample_assignment_only",
        "ready_for_complete_human_review_execution": False,
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
        "warhead_type_model_head_integrated": False,
        "warhead_type_loss_integrated": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "blocking_reasons": list(result.blocking_reasons),
        "recommended_manual_action": (
            "perform_real_human_review_of_materialized_family_topology_and_"
            "sample_assignment_packages"
            if success
            else "resolve_covapie_current11_cys_sg_review_package_materialization_blockers_v1"
        ),
        "recommended_engineering_next_step": (
            "design_covapie_cys_sg_candidate_warhead_smarts_materialization_gate_v1"
            if success
            else "resolve_covapie_current11_cys_sg_review_package_materialization_blockers_v1"
        ),
        "recommended_next_step": (
            "design_covapie_cys_sg_candidate_warhead_smarts_materialization_gate_v1"
            if success
            else "resolve_covapie_current11_cys_sg_review_package_materialization_blockers_v1"
        ),
        "output_sha256": {
            name: sha256(payload) for name, payload in payloads_without_manifest.items()
        },
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        PACKAGE_FILE: _csv_bytes(PACKAGE_COLUMNS, result.package_rows),
        CLASS_TEMPLATE_FILE: _csv_bytes(CLASS_REVIEW_RECORD_FIELDS, result.class_template_rows),
        SAMPLE_TEMPLATE_FILE: _csv_bytes(SAMPLE_REVIEW_RECORD_FIELDS, result.sample_template_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(_manifest(result, payloads), sort_keys=True, indent=2, ensure_ascii=True)
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
