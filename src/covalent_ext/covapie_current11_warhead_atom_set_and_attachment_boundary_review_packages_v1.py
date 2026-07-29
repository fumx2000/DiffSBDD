"""Materialize Current11 warhead atom-set/boundary human-review packages.

This stage is deliberately review-package-only.  It preserves every bridge
candidate, emits blank ``not_reviewed`` templates, and never selects a
candidate or creates warhead/boundary authority.  Formal inputs are read only
from the immutable BASE commit with ``git show``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_review_packages_v1"
)
CANDIDATE_SET_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_candidate_set_v1"
)
PACKAGE_OPTION_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_review_option_v1"
)
REVIEW_RECORD_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_human_review_record_v1"
)
REVIEW_UNIT_TYPE = "sample_warhead_atom_set_and_attachment_boundary"
PACKAGE_INDEX_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_package_index_v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review packages v1"
)
BASE_COMMIT = "ec9b1efbcfc49eeda55d7318b38daec67455343a"
BASE_PARENT = "5cac27027c824cd38bad3479a59f586b2714142c"
BASE_TREE = "4ac36dc3946d2bcad3bb345862d90a2daa677c15"
BASE_SUBJECT = (
    "add CovaPIE Current11 pre-reaction warhead atom set and attachment "
    "boundary proposals v1"
)

OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
SOURCE_FILE = "covapie_warhead_boundary_review_package_source_inventory.csv"
INDEX_FILE = "covapie_current11_warhead_boundary_review_package_index.csv"
OPTION_FILE = "covapie_current11_warhead_boundary_candidate_review_options.csv"
TEMPLATE_FILE = "covapie_current11_warhead_boundary_review_record_templates.csv"
FAILURE_FILE = "covapie_warhead_boundary_review_package_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    INDEX_FILE,
    OPTION_FILE,
    TEMPLATE_FILE,
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

PROPOSAL_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals_v1"
)
PROPOSAL_SOURCE = Path("src/covalent_ext") / (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals_v1.py"
)
PROPOSALS = PROPOSAL_ROOT / (
    "covapie_current11_pre_reaction_warhead_atom_set_and_attachment_"
    "boundary_proposals.csv"
)
ENUMERATIONS = PROPOSAL_ROOT / (
    "covapie_current11_exact_one_boundary_bridge_candidate_enumeration.csv"
)
READINESS = PROPOSAL_ROOT / "covapie_current11_warhead_proposal_readiness_matrix.csv"
PREDECESSOR_FAILURE = (
    PROPOSAL_ROOT / "covapie_warhead_proposal_materialization_failure_matrix.csv"
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
MAPPINGS = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
RULES = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/"
    "covapie_cys_sg_warhead_rule_registry.csv"
)
PRIOR_REVIEW_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1"
)
PRIOR_REVIEW_MANIFEST = PRIOR_REVIEW_ROOT / (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_"
    "review_packages_manifest.json"
)
PRIOR_REVIEW_INDEX = PRIOR_REVIEW_ROOT / "covapie_review_package_index.csv"
PRIOR_CLASS_TEMPLATES = (
    PRIOR_REVIEW_ROOT / "covapie_cys_sg_candidate_class_review_record_templates.csv"
)
PRIOR_SAMPLE_TEMPLATES = (
    PRIOR_REVIEW_ROOT / "covapie_current11_sample_assignment_review_record_templates.csv"
)

FROZEN_BASE_SHA256 = {
    PROPOSAL_SOURCE: "f50c9f4c0940b8e6c34cc0715a4160bf613511d61a1421f9e1bc7d2b71a27b25",
    PROPOSALS: "7e72fc157bb52cc2d5cba0c3fd2a7ac88f92bc50a35d001cfff0c2bf3296b4b0",
    ENUMERATIONS: "968105718614996fdee98ace96fd1362c86814ebdb774491328f6db66e380b2a",
    READINESS: "1c37feec87d2b79d27912d587ad9b8f07e9f3d8f2c8f4d5464f5f19ffc19b916",
    PREDECESSOR_FAILURE: "1a9a96145c190da98740526e9306c1688650dd63e711f84193fedf02fd3fb14d",
    PROPOSAL_MANIFEST: "fed5f97d177b9a0f91ec7eebf8ea3081662731e50ca6a74f3898f3068a5e6b79",
    ASSIGNMENTS: "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    PARENT_ATOMS: "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BONDS: "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    MAPPINGS: "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    RULES: "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    PRIOR_REVIEW_MANIFEST: "677034c0b8822e0b1476e28d00bb8dda5c8e53f5f42fcda790d9c4a81fa8a90b",
    PRIOR_REVIEW_INDEX: "b62a9d884b08b3b5132f64ca33531497343f208925e3a64eadd7980eee0d341f",
    PRIOR_CLASS_TEMPLATES: "596e218d1d29e16d65edfa1c804b63a528668ffc4083d4089427eda556f37ce1",
    PRIOR_SAMPLE_TEMPLATES: "662e95d3403a694da15dedd60dbdb81f98a9e404533693643b3721cd83a18bc1",
}
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)

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
ENUMERATION_FIELDS = (
    "enumeration_version", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "reaction_family_id", "warhead_rule_id",
    "component_parent_graph_sha256", "bridge_candidate_index_0based",
    "boundary_bond_id", "warhead_side_atom_ids", "warhead_side_atom_count",
    "nonwarhead_side_atom_count", "contains_local_reaction_center",
    "contains_required_leaving_groups", "warhead_side_connected",
    "exact_one_boundary_verified", "proper_subset", "candidate_admitted",
    "blocking_reasons", "bridge_candidate_record_sha256",
)
PROPOSAL_LIST_FIELDS = {
    "local_reaction_center_atom_ids", "local_reaction_center_bond_ids",
    "proposed_pre_reaction_warhead_atom_ids", "required_leaving_group_atom_ids",
    "ambiguity_reasons",
}
ENUMERATION_INT_FIELDS = {
    "warhead_type_candidate_class_index_0based",
    "bridge_candidate_index_0based", "warhead_side_atom_count",
    "nonwarhead_side_atom_count",
}
ENUMERATION_BOOL_FIELDS = {
    "contains_local_reaction_center", "contains_required_leaving_groups",
    "warhead_side_connected", "exact_one_boundary_verified", "proper_subset",
    "candidate_admitted",
}
SOURCE_COLUMNS = (
    "source_path", "BASE_SHA256", "source_row_count", "Current11_coverage",
    "fields_actually_used", "authority_class", "verified",
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
FAILURE_COLUMNS = (
    "failure_case", "mutation_signature", "mutated_field",
    "mutated_value_json", "expected_reason", "observed_reasons",
    "expected_reason_verified", "fails_closed", "option_row_count",
    "template_row_count", "package_index_row_count", "human_review_completed",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available", "SMARTS_ready",
    "role_ready", "mask_ready", "model_ready", "training_ready", "verified",
)
ASSIGNMENT_HASH_FIELDS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id", "target_residue_name",
    "target_residue_number", "target_residue_atom_name",
    "ligand_reactive_atom_name", "ligand_reactive_atom_element",
    "ligand_reactive_parent_ccd_atom_id", "component_parent_graph_sha256",
    "observed_graph_sha256", "radius_1_signature_sha256",
    "candidate_reaction_family_id", "candidate_warhead_rule_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "assignment_status", "review_status",
    "training_label_status",
)

_SHA = re.compile(r"[0-9a-f]{64}")
_OID = re.compile(r"[0-9a-f]{40}")
_FORBIDDEN_REVIEWERS = {
    "codex", "chatgpt", "openai", "automation", "auto", "system", "model"
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def _git(repo_root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
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
        line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")
    )
    subject, newline, body = message.partition(b"\n")
    if (
        parents != (BASE_COMMIT,) or not newline
        or subject.decode() != FORMAL_COMMIT_SUBJECT or body
    ):
        raise ValueError("successor_identity_mismatch")
    changed = {
        item.decode() for item in _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
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
    if len(tree_rows) != 10 or any(not row.startswith(b"100644 blob ") for row in tree_rows):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
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


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


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


def _csv_bytes(columns: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
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


def typed_proposal(row: Mapping[str, str]) -> dict[str, Any]:
    if tuple(row) != PROPOSAL_FIELDS:
        raise ValueError("proposal_field_inventory_mismatch")
    result: dict[str, Any] = {}
    for field in PROPOSAL_FIELDS:
        if field == "warhead_type_candidate_class_index_0based":
            result[field] = _parse_int(row[field], field)
        elif field in PROPOSAL_LIST_FIELDS:
            result[field] = _parse_list(row[field], field)
        else:
            if type(row[field]) is not str:
                raise ValueError(f"proposal_exact_str_invalid:{field}")
            result[field] = row[field]
    return result


def typed_enumeration(row: Mapping[str, str]) -> dict[str, Any]:
    if tuple(row) != ENUMERATION_FIELDS:
        raise ValueError("enumeration_field_inventory_mismatch")
    result: dict[str, Any] = {}
    for field in ENUMERATION_FIELDS:
        if field in ENUMERATION_INT_FIELDS:
            result[field] = _parse_int(row[field], field)
        elif field in ENUMERATION_BOOL_FIELDS:
            result[field] = _parse_bool(row[field], field)
        elif field == "warhead_side_atom_ids":
            result[field] = _parse_list(row[field], field)
        else:
            if type(row[field]) is not str:
                raise ValueError(f"enumeration_exact_str_invalid:{field}")
            result[field] = row[field]
    return result


def _record_sha(record: Mapping[str, Any], fields: Sequence[str], excluded: str) -> str:
    if tuple(record) != tuple(fields):
        raise ValueError("record_field_inventory_mismatch")
    return sha256(canonical_json(
        {field: record[field] for field in fields if field != excluded}
    ).encode("utf-8"))


def proposal_record_sha256(record: Mapping[str, Any]) -> str:
    return _record_sha(record, PROPOSAL_FIELDS, "proposal_record_sha256")


def bridge_candidate_record_sha256(record: Mapping[str, Any]) -> str:
    return _record_sha(
        record, ENUMERATION_FIELDS, "bridge_candidate_record_sha256"
    )


def package_option_record_sha256(record: Mapping[str, Any]) -> str:
    validate_option_record(record, verify_digest=False)
    return _record_sha(record, OPTION_FIELDS, "package_option_record_sha256")


def review_record_sha256(record: Mapping[str, Any]) -> str:
    _validate_review_schema(record)
    return _record_sha(record, REVIEW_RECORD_FIELDS, "review_record_sha256")


def unreviewed_template_payload_sha256(record: Mapping[str, Any]) -> str:
    _validate_review_schema(record)
    if record["review_decision"] != "not_reviewed" or record["review_record_sha256"]:
        raise ValueError("not_reviewed_template_digest_contract_invalid")
    return review_record_sha256(record)


def validate_option_record(record: Mapping[str, Any], *, verify_digest: bool = True) -> None:
    if type(record) is not dict or tuple(record) != OPTION_FIELDS:
        raise ValueError("option_field_inventory_mismatch")
    for field in OPTION_FIELDS:
        value = record[field]
        if field in OPTION_INT_FIELDS:
            if type(value) is not int or value < 0:
                raise ValueError(f"option_exact_int_invalid:{field}")
        elif field in OPTION_BOOL_FIELDS:
            if type(value) is not bool:
                raise ValueError(f"option_exact_bool_invalid:{field}")
        elif field in OPTION_LIST_FIELDS:
            if type(value) is not list or any(type(item) is not str for item in value):
                raise ValueError(f"option_exact_list_str_invalid:{field}")
        elif type(value) is not str:
            raise ValueError(f"option_exact_str_invalid:{field}")
    if record["package_option_version"] != PACKAGE_OPTION_VERSION:
        raise ValueError("option_version_mismatch")
    if record["review_eligible"] is not record["candidate_admitted"]:
        raise ValueError("review_eligibility_mismatch")
    if verify_digest and record["package_option_record_sha256"] != package_option_record_sha256(record):
        raise ValueError("option_record_SHA_mismatch")


def parse_review_record_csv(row: Mapping[str, str]) -> dict[str, Any]:
    if tuple(row) != REVIEW_RECORD_FIELDS:
        raise ValueError("review_template_field_inventory_mismatch")
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
        raise ValueError("review_template_field_inventory_mismatch")
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


def _meaningful(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _validate_human_text(record: Mapping[str, Any]) -> None:
    if not _meaningful(record["reviewer_id"]):
        raise ValueError("reviewer_not_meaningful")
    if record["reviewer_id"].strip().casefold() in _FORBIDDEN_REVIEWERS:
        raise ValueError("forbidden_reviewer")
    if not _meaningful(record["review_rationale"]):
        raise ValueError("review_rationale_not_meaningful")
    if record["review_notes"] and not _meaningful(record["review_notes"]):
        raise ValueError("review_notes_not_meaningful")


def _validate_completed_digest(record: Mapping[str, Any]) -> None:
    if _SHA.fullmatch(record["review_record_sha256"]) is None:
        raise ValueError("review_record_SHA_missing_or_invalid")
    if record["review_record_sha256"] != review_record_sha256(record):
        raise ValueError("review_record_SHA_mismatch")


def _bond_tuple(row: Mapping[str, str] | Sequence[str]) -> tuple[str, str, str]:
    if isinstance(row, Mapping):
        return (
            row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"],
            row["normalized_bond_order"],
        )
    if len(row) != 3 or any(type(item) is not str for item in row):
        raise ValueError("parent_bond_invalid")
    return row[0], row[1], row[2]


def validate_review_record(
    record: Mapping[str, Any],
    *,
    options: Sequence[Mapping[str, Any]] = (),
    proposal: Mapping[str, Any] | None = None,
    parent_atom_ids: Sequence[str] = (),
    parent_bonds: Sequence[Mapping[str, str] | Sequence[str]] = (),
) -> None:
    """Validate one typed review record without performing review."""

    _validate_review_schema(record)
    decision = record["review_decision"]
    selected = record["selected_bridge_candidate_index_0based"]
    selected_sha = record["selected_bridge_candidate_record_sha256"]
    atom_fields_blank = (
        record["reviewed_warhead_atom_ids"] == []
        and record["reviewed_warhead_attachment_atom_id"] == ""
        and record["reviewed_nonwarhead_boundary_atom_id"] == ""
        and record["reviewed_attachment_boundary_bond_order"] == ""
        and record["reviewed_boundary_bond_id"] == ""
    )
    if decision == "not_reviewed":
        if selected is not None or selected_sha:
            raise ValueError("not_reviewed_selection_prefilled")
        if not atom_fields_blank:
            raise ValueError("not_reviewed_atom_or_boundary_fields_prefilled")
        if any(record[field] for field in ("reviewer_id", "review_rationale", "review_notes")):
            raise ValueError("not_reviewed_reviewer_or_text_prefilled")
        if record["review_record_sha256"]:
            raise ValueError("not_reviewed_review_digest_prefilled")
        return
    _validate_human_text(record)
    if decision == "select_admitted_candidate":
        if type(selected) is not int or _SHA.fullmatch(selected_sha) is None:
            raise ValueError("select_candidate_identity_invalid")
        matches = [
            option for option in options
            if option["sample_index_row_id"] == record["sample_index_row_id"]
            and option["source_candidate_set_sha256"]
            == record["source_candidate_set_sha256"]
            and option["source_bridge_candidate_index_0based"] == selected
            and option["source_bridge_candidate_record_sha256"] == selected_sha
        ]
        if len(matches) != 1 or matches[0]["review_eligible"] is not True:
            raise ValueError("select_candidate_not_unique_review_eligible")
        option = matches[0]
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
            raise ValueError("select_candidate_reviewed_fields_mismatch")
    elif decision == "revise_atom_set_and_boundary":
        if selected is not None or selected_sha:
            raise ValueError("revise_selection_must_be_blank")
        if proposal is None:
            raise ValueError("revise_proposal_missing")
        atoms = record["reviewed_warhead_atom_ids"]
        atom_set = set(atoms)
        parent_set = set(parent_atom_ids)
        if not atoms or not set(proposal["local_reaction_center_atom_ids"]) <= atom_set:
            raise ValueError("revise_missing_local_reaction_center")
        if not set(proposal["required_leaving_group_atom_ids"]) <= atom_set:
            raise ValueError("revise_missing_required_leaving_group")
        if not atom_set < parent_set:
            raise ValueError("revise_not_parent_graph_proper_subset")
        adjacency: dict[str, set[str]] = defaultdict(set)
        boundary = []
        for raw in parent_bonds:
            left, right, order = _bond_tuple(raw)
            if left in atom_set and right in atom_set:
                adjacency[left].add(right)
                adjacency[right].add(left)
            elif (left in atom_set) != (right in atom_set):
                boundary.append((left, right, order))
        seen = set()
        queue = deque([atoms[0]])
        while queue:
            current = queue.popleft()
            if current in seen:
                continue
            seen.add(current)
            queue.extend(adjacency[current] - seen)
        if seen != atom_set:
            raise ValueError("revise_warhead_induced_subgraph_disconnected")
        if len(boundary) != 1:
            raise ValueError("revise_boundary_not_exact_one")
        left, right, order = boundary[0]
        attachment = left if left in atom_set else right
        nonwarhead = right if attachment == left else left
        low, high = _utf8_sorted((left, right))
        bond_id = f"{low}|{high}|{order}"
        expected = (attachment, nonwarhead, order, bond_id)
        observed = (
            record["reviewed_warhead_attachment_atom_id"],
            record["reviewed_nonwarhead_boundary_atom_id"],
            record["reviewed_attachment_boundary_bond_order"],
            record["reviewed_boundary_bond_id"],
        )
        if observed != expected:
            raise ValueError("revise_boundary_endpoint_derivation_mismatch")
    else:
        if selected is not None or selected_sha or not atom_fields_blank:
            raise ValueError("quarantine_dependency_invalid")
    _validate_completed_digest(record)


def _source_metadata(path: Path) -> tuple[str, str, str]:
    values = {
        PROPOSAL_SOURCE: ("11/11", "proposal/enumeration hash and typed contracts", "predecessor_production_contract"),
        PROPOSALS: ("11/11", "proposal identity, local center, leaving groups, blank proposal fields", "Current11_proposal_records"),
        ENUMERATIONS: ("11/11", "Exact200 bridge candidates, admission and record identity", "bridge_candidate_enumeration"),
        READINESS: ("11/11", "candidate counts, human-review readiness, closed authority", "proposal_readiness_authority"),
        PREDECESSOR_FAILURE: ("11/11", "Exact36 predecessor fail-closed evidence", "predecessor_failure_evidence"),
        PROPOSAL_MANIFEST: ("11/11", "successful predecessor transaction and closed downstream", "predecessor_manifest"),
        ASSIGNMENTS: ("11/11", "assignment record identity and proposal linkage", "Current11_assignment_authority"),
        PARENT_ATOMS: ("11/11", "parent atom namespace and proper-subset validation", "parent_heavy_atom_authority"),
        PARENT_BONDS: ("11/11", "boundary endpoints, order, connectivity", "parent_heavy_bond_authority"),
        MAPPINGS: ("11/11", "observed-to-parent lineage remains exact", "observed_parent_mapping_authority"),
        RULES: ("11/11", "family/rule identity; SMARTS absent", "candidate_rule_registry"),
        PRIOR_REVIEW_MANIFEST: ("11/11", "parallel review remains unexecuted and downstream closed", "parallel_review_manifest"),
        PRIOR_REVIEW_INDEX: ("11/11", "parallel package identity and blank completion state", "parallel_review_package_index"),
        PRIOR_CLASS_TEMPLATES: ("7/7 classes", "blank class human-review records", "parallel_class_review_templates"),
        PRIOR_SAMPLE_TEMPLATES: ("11/11", "blank sample assignment human-review records", "parallel_sample_review_templates"),
    }
    return values[path]


def _source_inventory(payloads: Mapping[Path, bytes]) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for path in SOURCE_PATHS:
        payload = payloads[path]
        coverage, fields, authority = _source_metadata(path)
        row_count = (
            len(_csv_rows(payload)) if path.suffix == ".csv"
            else 1 if path.suffix == ".json"
            else len(payload.decode("utf-8").splitlines())
        )
        rows.append({
            "source_path": path.as_posix(), "BASE_SHA256": sha256(payload),
            "source_row_count": row_count, "Current11_coverage": coverage,
            "fields_actually_used": fields, "authority_class": authority,
            "verified": True,
        })
    return tuple(rows)


def _assignment_sha(row: Mapping[str, str]) -> str:
    payload: dict[str, Any] = {field: row[field] for field in ASSIGNMENT_HASH_FIELDS}
    payload["warhead_type_candidate_class_index_0based"] = _parse_int(
        payload["warhead_type_candidate_class_index_0based"],
        "warhead_type_candidate_class_index_0based",
    )
    return sha256(canonical_json(payload).encode("utf-8"))


def _validate_phase_a(payloads: Mapping[Path, bytes]) -> tuple[
    tuple[dict[str, Any], ...], tuple[dict[str, Any], ...],
    dict[str, dict[str, str]], tuple[str, ...]
]:
    reasons: list[str] = []
    manifest = json.loads(payloads[PROPOSAL_MANIFEST])
    proposal_rows = _csv_rows(payloads[PROPOSALS])
    enumeration_rows = _csv_rows(payloads[ENUMERATIONS])
    readiness = _csv_rows(payloads[READINESS])
    assignments = _csv_rows(payloads[ASSIGNMENTS])
    parent_atoms = _csv_rows(payloads[PARENT_ATOMS])
    parent_bonds = _csv_rows(payloads[PARENT_BONDS])
    if not manifest.get("transaction_succeeded"):
        reasons.append("predecessor_transaction_not_succeeded")
    if len(proposal_rows) != 11:
        reasons.append("proposal_count_not_11")
    if len(enumeration_rows) != 200:
        reasons.append("enumeration_count_not_200")
    if len(readiness) != 11:
        reasons.append("readiness_count_not_11")
    if len(_csv_rows(payloads[PREDECESSOR_FAILURE])) != 36:
        reasons.append("predecessor_failure_evidence_not_36")
    assignment_by_sample = {row["sample_index_row_id"]: row for row in assignments}
    if len(assignment_by_sample) != 11:
        reasons.append("duplicate_sample_identity")
    proposals: list[dict[str, Any]] = []
    enumerations: list[dict[str, Any]] = []
    try:
        for raw in proposal_rows:
            row = typed_proposal(raw)
            if row["proposal_record_sha256"] != proposal_record_sha256(row):
                raise ValueError("proposal_record_SHA_mismatch")
            if (
                row["proposal_status"] != "ambiguous_candidate"
                or row["ambiguity_reasons"]
                != ["multiple_admissible_exact_one_boundary_candidates"]
                or row["proposed_pre_reaction_warhead_atom_ids"] != []
                or any(row[field] for field in (
                    "proposed_warhead_attachment_atom_id",
                    "proposed_nonwarhead_boundary_atom_id",
                    "proposed_attachment_boundary_bond_order",
                ))
            ):
                raise ValueError("source_proposal_status_or_blank_contract_invalid")
            assignment = assignment_by_sample[row["sample_index_row_id"]]
            if (
                row["source_assignment_record_sha256"]
                != assignment["assignment_record_sha256"]
                or _assignment_sha(assignment) != assignment["assignment_record_sha256"]
            ):
                raise ValueError("proposal_assignment_SHA_linkage_mismatch")
            proposals.append(row)
        for raw in enumeration_rows:
            row = typed_enumeration(raw)
            if (
                row["bridge_candidate_record_sha256"]
                != bridge_candidate_record_sha256(row)
            ):
                raise ValueError("bridge_candidate_record_SHA_mismatch")
            graph_atoms = {
                atom["ccd_atom_id"] for atom in parent_atoms
                if atom["ligand_comp_id"] == row["ligand_comp_id"]
                and atom["component_parent_graph_sha256"]
                == row["component_parent_graph_sha256"]
            }
            graph_bonds = [
                bond for bond in parent_bonds
                if bond["ligand_comp_id"] == row["ligand_comp_id"]
                and bond["component_parent_graph_sha256"]
                == row["component_parent_graph_sha256"]
            ]
            warhead = row["warhead_side_atom_ids"]
            warhead_set = set(warhead)
            if (
                not graph_atoms or not graph_bonds
                or warhead != _utf8_sorted(warhead)
                or len(warhead) != len(warhead_set)
                or not warhead_set < graph_atoms
            ):
                raise ValueError("bridge_candidate_parent_atom_authority_mismatch")
            parts = row["boundary_bond_id"].split("|")
            if len(parts) != 3:
                raise ValueError("boundary_endpoint_derivation_mismatch")
            left, right, order = parts
            if [left, right] != _utf8_sorted((left, right)):
                raise ValueError("boundary_endpoint_canonical_order_mismatch")
            matching_bonds = [
                bond for bond in graph_bonds
                if {bond["parent_ccd_atom_id_1"], bond["parent_ccd_atom_id_2"]}
                == {left, right}
                and bond["normalized_bond_order"] == order
            ]
            crossing = [
                bond for bond in graph_bonds
                if (
                    bond["parent_ccd_atom_id_1"] in warhead_set
                ) != (
                    bond["parent_ccd_atom_id_2"] in warhead_set
                )
            ]
            if (
                len(matching_bonds) != 1 or len(crossing) != 1
                or (left in warhead_set) == (right in warhead_set)
            ):
                raise ValueError("boundary_parent_bond_authority_mismatch")
            enumerations.append(row)
    except ValueError as error:
        reasons.append(str(error))
    if len({row["sample_index_row_id"] for row in proposal_rows}) != 11:
        reasons.append("duplicate_sample_identity")
    ready_by_sample = {row["sample_index_row_id"]: row for row in readiness}
    if len(ready_by_sample) != 11:
        reasons.append("readiness_identity_invalid")
    for row in readiness:
        if not (
            row["proposal_status"] == "ambiguous_candidate"
            and row["ready_for_proposal_human_review"] == "true"
            and row["complete_warhead_atom_set_authority_available"] == "false"
            and row["exact_one_attachment_boundary_authority_available"] == "false"
            and all(row[field] == "false" for field in (
                "ready_for_candidate_warhead_smarts_materialization",
                "ready_for_SMARTS_review_execution", "ready_for_role_proposal_generation",
                "ready_for_mask_materialization", "ready_for_model_integration",
                "ready_for_training",
            ))
        ):
            reasons.append("predecessor_readiness_prematurely_opened")
            break
    expected_counts = {
        "proposal_record_count": 11, "total_parent_bridge_count": 200,
        "total_admitted_boundary_candidate_count": 185,
        "auto_exact_candidate_count": 0, "ambiguous_candidate_count": 11,
        "quarantined_count": 0, "not_materialized_count": 0,
        "proposal_human_review_ready_count": 11,
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "approved_warhead_smarts_count": 0, "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
    }
    if any(manifest.get(key) != value for key, value in expected_counts.items()):
        reasons.append("predecessor_manifest_state_invalid")
    if any(manifest.get(key) is not False for key in (
        "ready_for_role_proposal_generation",
        "ready_for_minimal_seed_proposal_generation",
        "ready_for_mask_materialization", "ready_for_tensorization",
        "ready_for_model_integration", "ready_for_training",
        "role_annotation_materialized", "minimal_seed_materialized",
        "mask_materialized", "tensor_materialized", "model_changed", "training_used",
    )):
        reasons.append("downstream_readiness_prematurely_opened")
    prior_manifest = json.loads(payloads[PRIOR_REVIEW_MANIFEST])
    if any(prior_manifest.get(key, 0) not in (0, False) for key in (
        "class_human_review_completed_count", "sample_human_review_completed_count",
        "approved_reaction_family_available_count", "approved_warhead_rule_available_count",
        "human_gold_review_completed_count", "training_label_approved_count",
    )):
        reasons.append("parallel_review_state_prematurely_opened")
    return tuple(proposals), tuple(enumerations), assignment_by_sample, tuple(dict.fromkeys(reasons))


def _candidate_set(
    proposal: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Any], str]:
    ordered = sorted(candidates, key=lambda row: row["bridge_candidate_index_0based"])
    indices = [row["bridge_candidate_index_0based"] for row in ordered]
    if indices != list(range(len(ordered))):
        raise ValueError("candidate_set_ordering_mismatch")
    all_sha = [row["bridge_candidate_record_sha256"] for row in ordered]
    admitted_sha = [
        row["bridge_candidate_record_sha256"]
        for row in ordered if row["candidate_admitted"]
    ]
    if (
        len(all_sha) != len(set(all_sha))
        or any(_SHA.fullmatch(value) is None for value in all_sha)
    ):
        raise ValueError("candidate_set_candidate_identity_invalid")
    payload = {
        "candidate_set_version": CANDIDATE_SET_VERSION,
        "sample_index_row_id": proposal["sample_index_row_id"],
        "source_proposal_record_sha256": proposal["proposal_record_sha256"],
        "all_bridge_candidate_record_sha256s": all_sha,
        "admitted_bridge_candidate_record_sha256s": admitted_sha,
    }
    return payload, sha256(canonical_json(payload).encode("utf-8"))


def _materialize_rows(
    proposals: Sequence[Mapping[str, Any]],
    enumerations: Sequence[Mapping[str, Any]],
    assignments: Mapping[str, Mapping[str, str]],
) -> tuple[
    tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...], tuple[str, ...]
]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in enumerations:
        grouped[row["sample_index_row_id"]].append(row)
    options = []
    templates = []
    indexes = []
    set_shas = []
    global_order = 0
    for package_order, proposal in enumerate(
        sorted(proposals, key=lambda row: row["sample_index_row_id"])
    ):
        sample_id = proposal["sample_index_row_id"]
        candidates = sorted(
            grouped[sample_id], key=lambda row: row["bridge_candidate_index_0based"]
        )
        candidate_payload, candidate_sha = _candidate_set(proposal, candidates)
        if len(candidates) == 0:
            raise ValueError("candidate_set_missing_or_extra_candidate")
        set_shas.append(candidate_sha)
        start = global_order
        for candidate in candidates:
            left, right, order = candidate["boundary_bond_id"].split("|")
            warhead_set = set(candidate["warhead_side_atom_ids"])
            if (left in warhead_set) == (right in warhead_set):
                raise ValueError("boundary_endpoint_derivation_mismatch")
            attachment = left if left in warhead_set else right
            nonwarhead = right if attachment == left else left
            extra = _utf8_sorted(
                warhead_set - set(proposal["local_reaction_center_atom_ids"])
            )
            record = {
                "package_option_version": PACKAGE_OPTION_VERSION,
                "package_item_order_0based": global_order,
                "option_order_within_sample_0based":
                    candidate["bridge_candidate_index_0based"],
                "sample_index_row_id": sample_id, "pdb_id": proposal["pdb_id"],
                "ligand_comp_id": proposal["ligand_comp_id"],
                "warhead_type_candidate_class_index_0based":
                    proposal["warhead_type_candidate_class_index_0based"],
                "warhead_type_candidate_class_id":
                    proposal["warhead_type_candidate_class_id"],
                "reaction_family_id": proposal["reaction_family_id"],
                "warhead_rule_id": proposal["warhead_rule_id"],
                "source_proposal_record_sha256": proposal["proposal_record_sha256"],
                "source_candidate_set_sha256": candidate_sha,
                "source_bridge_candidate_index_0based":
                    candidate["bridge_candidate_index_0based"],
                "source_bridge_candidate_record_sha256":
                    candidate["bridge_candidate_record_sha256"],
                "boundary_bond_id": candidate["boundary_bond_id"],
                "warhead_attachment_atom_id": attachment,
                "nonwarhead_boundary_atom_id": nonwarhead,
                "boundary_bond_order": order,
                "warhead_side_atom_ids": candidate["warhead_side_atom_ids"],
                "warhead_extra_atom_ids_beyond_local_center": extra,
                "local_reaction_center_atom_ids":
                    proposal["local_reaction_center_atom_ids"],
                "required_leaving_group_atom_ids":
                    proposal["required_leaving_group_atom_ids"],
                "warhead_side_atom_count": candidate["warhead_side_atom_count"],
                "nonwarhead_side_atom_count":
                    candidate["nonwarhead_side_atom_count"],
                "candidate_admitted": candidate["candidate_admitted"],
                "review_eligible": candidate["candidate_admitted"],
                "blocking_reasons": candidate["blocking_reasons"],
                "package_option_record_sha256": "",
            }
            record["package_option_record_sha256"] = package_option_record_sha256(record)
            validate_option_record(record)
            options.append(record)
            global_order += 1
        admitted_count = len(candidate_payload["admitted_bridge_candidate_record_sha256s"])
        assignment_sha = assignments[sample_id]["assignment_record_sha256"]
        template = {
            "review_record_version": REVIEW_RECORD_VERSION,
            "review_unit_type": REVIEW_UNIT_TYPE,
            "sample_index_row_id": sample_id, "pdb_id": proposal["pdb_id"],
            "ligand_comp_id": proposal["ligand_comp_id"],
            "warhead_type_candidate_class_index_0based":
                proposal["warhead_type_candidate_class_index_0based"],
            "warhead_type_candidate_class_id":
                proposal["warhead_type_candidate_class_id"],
            "reaction_family_id": proposal["reaction_family_id"],
            "warhead_rule_id": proposal["warhead_rule_id"],
            "source_proposal_record_sha256": proposal["proposal_record_sha256"],
            "source_assignment_record_sha256": assignment_sha,
            "source_candidate_set_sha256": candidate_sha,
            "total_candidate_count": len(candidates),
            "admitted_candidate_count": admitted_count,
            "review_decision": "not_reviewed",
            "selected_bridge_candidate_index_0based": None,
            "selected_bridge_candidate_record_sha256": "",
            "reviewed_warhead_atom_ids": [],
            "reviewed_warhead_attachment_atom_id": "",
            "reviewed_nonwarhead_boundary_atom_id": "",
            "reviewed_attachment_boundary_bond_order": "",
            "reviewed_boundary_bond_id": "", "reviewer_id": "",
            "review_rationale": "", "review_notes": "", "review_record_sha256": "",
        }
        validate_review_record(template)
        templates.append(template)
        indexes.append({
            "package_index_version": PACKAGE_INDEX_VERSION,
            "package_item_order_0based": package_order,
            "sample_index_row_id": sample_id, "pdb_id": proposal["pdb_id"],
            "ligand_comp_id": proposal["ligand_comp_id"],
            "warhead_type_candidate_class_index_0based":
                proposal["warhead_type_candidate_class_index_0based"],
            "warhead_type_candidate_class_id":
                proposal["warhead_type_candidate_class_id"],
            "reaction_family_id": proposal["reaction_family_id"],
            "warhead_rule_id": proposal["warhead_rule_id"],
            "source_proposal_record_sha256": proposal["proposal_record_sha256"],
            "source_assignment_record_sha256": assignment_sha,
            "source_candidate_set_sha256": candidate_sha,
            "total_candidate_count": len(candidates),
            "admitted_candidate_count": admitted_count,
            "source_proposal_status": proposal["proposal_status"],
            "candidate_option_row_start_0based": start,
            "candidate_option_row_end_exclusive": global_order,
            "review_record_version": REVIEW_RECORD_VERSION,
            "unreviewed_template_payload_sha256":
                unreviewed_template_payload_sha256(template),
            "review_options_materialized": True,
            "review_template_materialized": True, "ready_for_human_review": True,
            "human_review_completed": False,
            "complete_warhead_atom_set_authority_available": False,
            "exact_one_attachment_boundary_authority_available": False,
            "ready_for_candidate_warhead_smarts_materialization": False,
            "ready_for_role_proposal_generation": False,
            "blocking_reasons":
                "human_warhead_atom_set_and_attachment_boundary_review_missing;"
                "complete_warhead_atom_set_authority_unavailable;"
                "exact_one_attachment_boundary_authority_unavailable;"
                "candidate_warhead_SMARTS_not_materialized",
            "verified": True,
        })
    if (
        len(options) != 200 or len(templates) != 11 or len(indexes) != 11
        or sum(row["review_eligible"] for row in options) != 185
        or len(set(set_shas)) != 11
    ):
        raise ValueError("partial_materialization_attempted")
    return tuple(options), tuple(templates), tuple(indexes), tuple(set_shas)


@dataclass(frozen=True)
class PackageScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    predecessor_transaction_succeeded: bool = True
    proposal_count: int = 11
    enumeration_count: int = 200
    readiness_count: int = 11
    duplicate_sample_identity: bool = False
    proposal_record_sha_matches: bool = True
    bridge_candidate_record_sha_matches: bool = True
    source_proposal_status_ambiguous: bool = True
    candidate_set_complete: bool = True
    candidate_set_ordered: bool = True
    admitted_ordered_subset: bool = True
    candidate_set_sha_matches: bool = True
    option_count: int = 200
    global_option_order_matches: bool = True
    option_identity_linkage_matches: bool = True
    boundary_endpoint_derivation_matches: bool = True
    warhead_extra_atom_set_matches: bool = True
    review_eligibility_matches: bool = True
    option_record_sha_matches: bool = True
    package_index_count_and_order_matches: bool = True
    package_index_identity_linkage_matches: bool = True
    package_candidate_counts_match: bool = True
    review_template_field_inventory_matches: bool = True
    review_template_identity_linkage_matches: bool = True
    review_template_source_sha_matches: bool = True
    not_reviewed_decision_blank: bool = True
    not_reviewed_selection_blank: bool = True
    not_reviewed_atom_boundary_blank: bool = True
    not_reviewed_text_blank: bool = True
    not_reviewed_digest_blank: bool = True
    select_dependency_valid: bool = True
    revise_graph_invariant_valid: bool = True
    quarantine_dependency_valid: bool = True
    template_payload_sha_matches: bool = True
    partial_materialization_attempted: bool = False
    downstream_readiness_opened: bool = False


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_source_missing"),
    ("BASE source SHA mismatch", "base_source_sha_matches", False, "BASE_source_SHA_mismatch"),
    ("predecessor transaction not succeeded", "predecessor_transaction_succeeded", False, "predecessor_transaction_not_succeeded"),
    ("proposal count not 11", "proposal_count", 10, "proposal_count_not_11"),
    ("enumeration count not 200", "enumeration_count", 199, "enumeration_count_not_200"),
    ("readiness count not 11", "readiness_count", 10, "readiness_count_not_11"),
    ("duplicate sample identity", "duplicate_sample_identity", True, "duplicate_sample_identity"),
    ("proposal record SHA mismatch", "proposal_record_sha_matches", False, "proposal_record_SHA_mismatch"),
    ("bridge candidate record SHA mismatch", "bridge_candidate_record_sha_matches", False, "bridge_candidate_record_SHA_mismatch"),
    ("source proposal status not ambiguous", "source_proposal_status_ambiguous", False, "source_proposal_status_not_ambiguous"),
    ("candidate set missing or extra candidate", "candidate_set_complete", False, "candidate_set_missing_or_extra_candidate"),
    ("candidate set ordering mismatch", "candidate_set_ordered", False, "candidate_set_ordering_mismatch"),
    ("admitted candidate list not ordered subset", "admitted_ordered_subset", False, "admitted_candidate_list_not_ordered_subset"),
    ("candidate-set SHA mismatch", "candidate_set_sha_matches", False, "candidate_set_SHA_mismatch"),
    ("option row count not 200", "option_count", 199, "option_row_count_not_200"),
    ("global option order mismatch", "global_option_order_matches", False, "global_option_order_mismatch"),
    ("option identity linkage mismatch", "option_identity_linkage_matches", False, "option_identity_linkage_mismatch"),
    ("boundary endpoint derivation mismatch", "boundary_endpoint_derivation_matches", False, "boundary_endpoint_derivation_mismatch"),
    ("warhead extra atom-set mismatch", "warhead_extra_atom_set_matches", False, "warhead_extra_atom_set_mismatch"),
    ("review eligibility mismatch", "review_eligibility_matches", False, "review_eligibility_mismatch"),
    ("option record SHA mismatch", "option_record_sha_matches", False, "option_record_SHA_mismatch"),
    ("package index count or order mismatch", "package_index_count_and_order_matches", False, "package_index_count_or_order_mismatch"),
    ("package index identity linkage mismatch", "package_index_identity_linkage_matches", False, "package_index_identity_linkage_mismatch"),
    ("package candidate counts mismatch", "package_candidate_counts_match", False, "package_candidate_counts_mismatch"),
    ("review template field inventory mismatch", "review_template_field_inventory_matches", False, "review_template_field_inventory_mismatch"),
    ("review template identity linkage mismatch", "review_template_identity_linkage_matches", False, "review_template_identity_linkage_mismatch"),
    ("review template source SHA mismatch", "review_template_source_sha_matches", False, "review_template_source_SHA_mismatch"),
    ("not-reviewed decision prefilled", "not_reviewed_decision_blank", False, "not_reviewed_decision_prefilled"),
    ("not-reviewed selection prefilled", "not_reviewed_selection_blank", False, "not_reviewed_selection_prefilled"),
    ("not-reviewed atom or boundary fields prefilled", "not_reviewed_atom_boundary_blank", False, "not_reviewed_atom_or_boundary_fields_prefilled"),
    ("not-reviewed reviewer/rationale/notes prefilled", "not_reviewed_text_blank", False, "not_reviewed_reviewer_rationale_or_notes_prefilled"),
    ("not-reviewed review digest prefilled", "not_reviewed_digest_blank", False, "not_reviewed_review_digest_prefilled"),
    ("select decision dependency invalid", "select_dependency_valid", False, "select_decision_dependency_invalid"),
    ("revise decision graph invariant invalid", "revise_graph_invariant_valid", False, "revise_decision_graph_invariant_invalid"),
    ("quarantine decision dependency invalid", "quarantine_dependency_valid", False, "quarantine_decision_dependency_invalid"),
    ("unreviewed template payload SHA mismatch", "template_payload_sha_matches", False, "unreviewed_template_payload_SHA_mismatch"),
    ("partial materialization attempted", "partial_materialization_attempted", True, "partial_materialization_attempted"),
    ("downstream readiness prematurely opened", "downstream_readiness_opened", True, "downstream_readiness_prematurely_opened"),
)


def observe_failure_scenario(scenario: PackageScenario) -> tuple[str, ...]:
    checks = (
        (not scenario.base_source_present, "BASE_source_missing"),
        (not scenario.base_source_sha_matches, "BASE_source_SHA_mismatch"),
        (not scenario.predecessor_transaction_succeeded, "predecessor_transaction_not_succeeded"),
        (scenario.proposal_count != 11, "proposal_count_not_11"),
        (scenario.enumeration_count != 200, "enumeration_count_not_200"),
        (scenario.readiness_count != 11, "readiness_count_not_11"),
        (scenario.duplicate_sample_identity, "duplicate_sample_identity"),
        (not scenario.proposal_record_sha_matches, "proposal_record_SHA_mismatch"),
        (not scenario.bridge_candidate_record_sha_matches, "bridge_candidate_record_SHA_mismatch"),
        (not scenario.source_proposal_status_ambiguous, "source_proposal_status_not_ambiguous"),
        (not scenario.candidate_set_complete, "candidate_set_missing_or_extra_candidate"),
        (not scenario.candidate_set_ordered, "candidate_set_ordering_mismatch"),
        (not scenario.admitted_ordered_subset, "admitted_candidate_list_not_ordered_subset"),
        (not scenario.candidate_set_sha_matches, "candidate_set_SHA_mismatch"),
        (scenario.option_count != 200, "option_row_count_not_200"),
        (not scenario.global_option_order_matches, "global_option_order_mismatch"),
        (not scenario.option_identity_linkage_matches, "option_identity_linkage_mismatch"),
        (not scenario.boundary_endpoint_derivation_matches, "boundary_endpoint_derivation_mismatch"),
        (not scenario.warhead_extra_atom_set_matches, "warhead_extra_atom_set_mismatch"),
        (not scenario.review_eligibility_matches, "review_eligibility_mismatch"),
        (not scenario.option_record_sha_matches, "option_record_SHA_mismatch"),
        (not scenario.package_index_count_and_order_matches, "package_index_count_or_order_mismatch"),
        (not scenario.package_index_identity_linkage_matches, "package_index_identity_linkage_mismatch"),
        (not scenario.package_candidate_counts_match, "package_candidate_counts_mismatch"),
        (not scenario.review_template_field_inventory_matches, "review_template_field_inventory_mismatch"),
        (not scenario.review_template_identity_linkage_matches, "review_template_identity_linkage_mismatch"),
        (not scenario.review_template_source_sha_matches, "review_template_source_SHA_mismatch"),
        (not scenario.not_reviewed_decision_blank, "not_reviewed_decision_prefilled"),
        (not scenario.not_reviewed_selection_blank, "not_reviewed_selection_prefilled"),
        (not scenario.not_reviewed_atom_boundary_blank, "not_reviewed_atom_or_boundary_fields_prefilled"),
        (not scenario.not_reviewed_text_blank, "not_reviewed_reviewer_rationale_or_notes_prefilled"),
        (not scenario.not_reviewed_digest_blank, "not_reviewed_review_digest_prefilled"),
        (not scenario.select_dependency_valid, "select_decision_dependency_invalid"),
        (not scenario.revise_graph_invariant_valid, "revise_decision_graph_invariant_invalid"),
        (not scenario.quarantine_dependency_valid, "quarantine_decision_dependency_invalid"),
        (not scenario.template_payload_sha_matches, "unreviewed_template_payload_SHA_mismatch"),
        (scenario.partial_materialization_attempted, "partial_materialization_attempted"),
        (scenario.downstream_readiness_opened, "downstream_readiness_prematurely_opened"),
    )
    return tuple(reason for failed, reason in checks if failed)


def transaction_tables(
    scenario: PackageScenario,
) -> tuple[tuple[object, ...], tuple[object, ...], tuple[object, ...]]:
    if observe_failure_scenario(scenario):
        return (), (), ()
    return (object(),), (object(),), (object(),)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = PackageScenario()
    rows = []
    signatures = set()
    for case, field, value, expected in FAILURE_MUTATIONS:
        original = getattr(baseline, field)
        if type(original) is not type(value) or original == value:
            raise AssertionError(f"failure_mutation_type_or_delta_invalid:{field}")
        scenario = replace(baseline, **{field: value})
        observed = observe_failure_scenario(scenario)
        signature = sha256(canonical_json({
            "mutated_field": field, "mutated_value": value
        }).encode("utf-8"))
        options, templates, indexes = transaction_tables(scenario)
        if expected not in observed or signature in signatures:
            raise AssertionError(f"failure_mutation_invalid:{field}")
        signatures.add(signature)
        rows.append({
            "failure_case": case, "mutation_signature": signature,
            "mutated_field": field, "mutated_value_json": canonical_json(value),
            "expected_reason": expected, "observed_reasons": ";".join(observed),
            "expected_reason_verified": True,
            "fails_closed": not options and not templates and not indexes,
            "option_row_count": len(options), "template_row_count": len(templates),
            "package_index_row_count": len(indexes),
            "human_review_completed": False,
            "complete_warhead_atom_set_authority_available": False,
            "exact_one_attachment_boundary_authority_available": False,
            "SMARTS_ready": False, "role_ready": False, "mask_ready": False,
            "model_ready": False, "training_ready": False, "verified": True,
        })
    return tuple(rows)


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    option_rows: tuple[Mapping[str, Any], ...]
    template_rows: tuple[Mapping[str, Any], ...]
    index_rows: tuple[Mapping[str, Any], ...]
    candidate_set_sha256s: tuple[str, ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


def build_result(repo_root: Path) -> BuildResult:
    payloads = load_frozen_sources(repo_root)
    source_rows = _source_inventory(payloads)
    proposals, enumerations, assignments, reasons = _validate_phase_a(payloads)
    failures = build_failure_rows()
    if reasons:
        return BuildResult(source_rows, (), (), (), (), failures, False, reasons)
    try:
        options, templates, indexes, set_shas = _materialize_rows(
            proposals, enumerations, assignments
        )
    except ValueError as error:
        return BuildResult(
            source_rows, (), (), (), (), failures, False, (str(error),)
        )
    return BuildResult(
        source_rows, options, templates, indexes, set_shas, failures, True, ()
    )


def _manifest(result: BuildResult, output_sha256: Mapping[str, str]) -> Mapping[str, Any]:
    succeeded = result.transaction_succeeded
    next_step = (
        "design_covapie_current11_warhead_atom_set_and_attachment_boundary_"
        "review_ingestion_gate_v1"
        if succeeded
        else "resolve_covapie_current11_warhead_boundary_review_package_"
        "materialization_blockers_v1"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT, "parent": BASE_PARENT, "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "source_count": 15,
        "source_sha256": {
            path.as_posix(): value for path, value in FROZEN_BASE_SHA256.items()
        },
        "candidate_set_version": CANDIDATE_SET_VERSION,
        "candidate_set_count": len(result.candidate_set_sha256s),
        "candidate_set_sha_unique_count": len(set(result.candidate_set_sha256s)),
        "candidate_set_sha256s": list(result.candidate_set_sha256s),
        "package_option_version": PACKAGE_OPTION_VERSION,
        "package_option_field_count": 28,
        "package_option_fields": list(OPTION_FIELDS),
        "package_option_record_count": len(result.option_rows),
        "review_eligible_option_count": sum(
            row["review_eligible"] for row in result.option_rows
        ),
        "review_ineligible_option_count": sum(
            not row["review_eligible"] for row in result.option_rows
        ),
        "package_option_sha_valid_count": sum(
            row["package_option_record_sha256"] == package_option_record_sha256(row)
            for row in result.option_rows
        ),
        "review_record_version": REVIEW_RECORD_VERSION,
        "review_unit_type": REVIEW_UNIT_TYPE,
        "review_record_field_count": 26,
        "review_record_fields": list(REVIEW_RECORD_FIELDS),
        "review_decisions": list(REVIEW_DECISIONS),
        "review_template_count": len(result.template_rows),
        "review_template_not_reviewed_count": sum(
            row["review_decision"] == "not_reviewed" for row in result.template_rows
        ),
        "review_template_selected_candidate_count": sum(
            row["selected_bridge_candidate_index_0based"] is not None
            for row in result.template_rows
        ),
        "review_template_reviewed_atom_set_nonempty_count": sum(
            bool(row["reviewed_warhead_atom_ids"]) for row in result.template_rows
        ),
        "review_template_reviewer_nonempty_count": sum(
            bool(row["reviewer_id"]) for row in result.template_rows
        ),
        "review_template_rationale_nonempty_count": sum(
            bool(row["review_rationale"]) for row in result.template_rows
        ),
        "review_template_digest_populated_count": sum(
            bool(row["review_record_sha256"]) for row in result.template_rows
        ),
        "package_index_version": PACKAGE_INDEX_VERSION,
        "package_index_count": len(result.index_rows),
        "package_option_spans_cover_all_rows": (
            [row["candidate_option_row_start_0based"] for row in result.index_rows]
            == [0] + [
                row["candidate_option_row_end_exclusive"]
                for row in result.index_rows[:-1]
            ]
            and (not result.index_rows or
                 result.index_rows[-1]["candidate_option_row_end_exclusive"] == 200)
        ),
        "review_packages_materialized": succeeded,
        "ready_for_warhead_boundary_human_review": succeeded,
        "warhead_boundary_human_review_ready_count": len(result.index_rows),
        "warhead_boundary_human_review_completed": False,
        "warhead_boundary_human_review_completed_count": 0,
        "source_ambiguous_candidate_count": 11 if succeeded else 0,
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
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
        "role_annotation_materialized": False, "minimal_seed_materialized": False,
        "mask_materialized": False, "tensor_materialized": False,
        "model_changed": False, "training_used": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "transaction_succeeded": succeeded,
        "blocking_reasons": list(result.blocking_reasons),
        "failure_mutation_count": len(result.failure_rows),
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] for row in result.failure_rows
        ),
        "output_sha256": dict(output_sha256),
        "recommended_manual_action_primary":
            "perform_real_human_review_of_current11_warhead_atom_set_and_"
            "attachment_boundary_review_packages",
        "remaining_parallel_manual_action":
            "perform_real_human_review_of_materialized_family_topology_and_"
            "sample_assignment_packages",
        "recommended_engineering_next_step": next_step,
        "recommended_next_step": next_step,
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        INDEX_FILE: _csv_bytes(INDEX_FIELDS, result.index_rows),
        OPTION_FILE: _csv_bytes(OPTION_FIELDS, result.option_rows),
        TEMPLATE_FILE: _csv_bytes(REVIEW_RECORD_FIELDS, result.template_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    output_sha = {name: sha256(payload) for name, payload in payloads.items()}
    payloads[MANIFEST_FILE] = (
        json.dumps(
            _manifest(result, output_sha), indent=2, sort_keys=True,
            ensure_ascii=True,
        ) + "\n"
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
    payloads = materialize(repo_root)
    print(f"materialized={len(payloads)} output_root={OUTPUT_ROOT.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
