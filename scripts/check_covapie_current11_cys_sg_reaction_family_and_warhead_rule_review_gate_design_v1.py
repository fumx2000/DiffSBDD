"""Independent checker for the Current11 Cys-SG human-review gate design."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from covalent_ext.covapie_hermetic_git_lifecycle_harness_v1 import (
    exercise_hermetic_git_lifecycle_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "0c8d1d10260a028360357b8c309f22676fc81645"
BASE_PARENT = "dc1222503dcec83220a28df2abdae898a0855864"
BASE_TREE = "5d1ddb25404e55858001267135536450428dfb25"
BASE_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule assignments v1"
)
SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review gate "
    "design v1"
)
SCHEMA = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1"
)
OUTPUT = Path("data/derived/covalent_small") / SCHEMA

ASSIGNMENT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
)
ASSIGNMENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1"
)
CLASS_SOURCE = (
    ASSIGNMENT_ROOT / "covapie_cys_sg_warhead_type_candidate_class_vocabulary.csv"
)
ASSIGNMENT_SOURCE_CSV = (
    ASSIGNMENT_ROOT / "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
READINESS_SOURCE = (
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
FAMILY_SOURCE = REGISTRY_ROOT / "covapie_cys_sg_reaction_family_registry.csv"
RULE_SOURCE = REGISTRY_ROOT / "covapie_cys_sg_warhead_rule_registry.csv"
DESIGN_SOURCE = (
    REGISTRY_ROOT / "covapie_current11_reaction_family_and_warhead_rule_design_matrix.csv"
)
REGISTRY_MANIFEST = (
    REGISTRY_ROOT
    / "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_manifest.json"
)
ROLE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
MAPPING_SOURCE = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
FINAL_SOURCE = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
EXPECTED_SHA = {
    ASSIGNMENT_SOURCE:
        "fe6c67940efef89290b2f276f9fb4c39245468181d52b219951a6f9ca7f454aa",
    CLASS_SOURCE:
        "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    ASSIGNMENT_SOURCE_CSV:
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    READINESS_SOURCE:
        "3405eb96ae610315a0a6f607267a2c2522fb2c1debec5f492c787d4e11e4d474",
    ASSIGNMENT_MANIFEST:
        "5e5acefc9051fc07d3243917292f073fc09fb432a0eb0325fa8d344d37c0e265",
    FAMILY_SOURCE:
        "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    RULE_SOURCE:
        "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    DESIGN_SOURCE:
        "24ae0fbd2dc1454574d9ed17145ba71d3b3132ffecfb84a1a831eceb77efab03",
    REGISTRY_MANIFEST:
        "4603d124e2f90616ebf7d28975e0eeb77e3d4c90133688d87df2e30c9ac54ef9",
    ROLE_SOURCE:
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    MAPPING_SOURCE:
        "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    FINAL_SOURCE:
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
}
SOURCES = tuple(EXPECTED_SHA)

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
    SOURCE_FILE, POLICY_FILE, CLASS_FILE, SAMPLE_FILE, FAILURE_FILE, MANIFEST_FILE
)
EXACT10 = (
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
    *(OUTPUT / name for name in OUTPUT_FILES),
)
DECISIONS = ("not_reviewed", "approve", "revise", "quarantine")
REVIEW_RECORD_VERSION = "covapie_cys_sg_human_review_record_v1"
REVIEW_UNIT_TYPES = ("candidate_class", "sample_assignment")
SMARTS_STATUSES = (
    "not_materialized", "candidate_not_reviewed", "approved", "revised",
    "quarantined",
)
SMARTS_UNREVIEWED_STATUSES = ("not_materialized", "candidate_not_reviewed")
SMARTS_HUMAN_REVIEWED_STATUSES = ("approved", "revised", "quarantined")
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
LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
FORBIDDEN_REVIEWERS = {
    "codex", "chatgpt", "auto", "system", "synthetic", "placeholder",
    "unknown", "none",
}
POLICY_NAMES = (
    "candidate identity is not approval",
    "family identity requires explicit human approval",
    "topology rule approval is separate from SMARTS approval",
    "approved warhead rule requires approved SMARTS",
    "SMARTS must match exact-one atom set",
    "SMARTS must include known reactive ligand atom",
    "warhead attachment boundary must be exact-one",
    "sample assignment requires independent sample review",
    "quarantine overrides downstream readiness",
    "gold requires approved family rule and sample assignment",
    "role proposal requires approved family rule and gold sample",
    "training approval remains a separate future gate",
)
FAILURE_REASONS = (
    ("base_source_present", "false", "BASE_source_missing"),
    ("base_source_sha_matches", "false", "BASE_source_SHA_mismatch"),
    ("assignment_transaction_succeeded", "false",
     "assignment_transaction_not_succeeded"),
    ("candidate_class_count", "6", "candidate_class_count_not_7"),
    ("class_indices_contiguous", "false", "class_index_non_contiguous"),
    ("assignment_count", "10", "Current11_assignment_count_not_11"),
    ("duplicate_class_identity", "true", "duplicate_class_identity"),
    ("duplicate_sample_identity", "true", "duplicate_sample_identity"),
    ("links_match", "false", "sample_rule_family_class_link_mismatch"),
    ("assignment_record_sha_matches", "false", "assignment_record_SHA_mismatch"),
    ("class_review_package_complete", "false", "class_review_package_incomplete"),
    ("sample_review_package_complete", "false",
     "sample_review_package_incomplete"),
    ("review_decision_valid", "false", "review_decision_outside_vocabulary"),
    ("non_not_reviewed_has_reviewer", "false",
     "non_not_reviewed_decision_without_reviewer"),
    ("non_not_reviewed_has_rationale", "false",
     "non_not_reviewed_decision_without_rationale"),
    ("family_approval_dependency_valid", "false",
     "family_approved_without_identity_approval"),
    ("topology_family_dependency_valid", "false",
     "topology_approved_without_family_approval"),
    ("approved_rule_has_smarts", "false", "approved_warhead_rule_without_SMARTS"),
    ("smarts_approved_nonempty", "false", "SMARTS_approved_but_empty"),
    ("smarts_match_count", "0", "SMARTS_match_count_zero"),
    ("smarts_match_count", "2", "SMARTS_match_count_multiple"),
    ("smarts_includes_reactive_atom", "false", "SMARTS_excludes_reactive_atom"),
    ("warhead_attachment_boundary_count", "2",
     "warhead_attachment_boundary_not_exact_one"),
    ("sample_approval_class_not_quarantined", "false",
     "sample_approved_while_class_quarantined"),
    ("sample_approval_rule_approved", "false",
     "sample_approved_while_rule_not_approved"),
    ("gold_dependency_valid", "false",
     "gold_marked_without_complete_human_review"),
    ("training_gold_dependency_valid", "false",
     "training_label_approved_without_gold"),
    ("role_dependency_valid", "false",
     "role_readiness_opened_without_approved_family_rule_SMARTS"),
    ("partial_materialization_attempted", "true",
     "partial_materialization_attempted"),
    ("execution_boundary_crossed", "true", "execution_boundary_crossed"),
)
HASH_FIELDS = (
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


def git(repo: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def base(repo: Path, path: Path) -> bytes:
    return git(repo, "show", f"{BASE}:{path.as_posix()}")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def meaningful_text(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def lower_sha256(value: object) -> bool:
    return type(value) is str and LOWER_SHA256.fullmatch(value) is not None


def exact_bool(value: object) -> bool:
    return type(value) is bool


def exact_int(value: object) -> bool:
    return type(value) is int


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def lifecycle(repo: Path) -> str:
    identity = git(
        repo, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    ).decode().splitlines()
    assert identity == [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    if head == BASE:
        return "pre_commit"
    raw = git(repo, "cat-file", "commit", head)
    headers, separator, message = raw.partition(b"\n\n")
    assert separator
    parents = [
        line[7:].decode() for line in headers.splitlines()
        if line.startswith(b"parent ")
    ]
    assert parents == [BASE]
    subject, newline, body = message.partition(b"\n")
    assert newline and subject.decode() == SUBJECT and body == b""
    changed = {
        item.decode()
        for item in git(
            repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).split(b"\0")
        if item
    }
    assert changed == {path.as_posix() for path in EXACT10}
    modes = [
        row.partition(b"\t")[0]
        for row in git(
            repo, "ls-tree", "-r", "-z", head, "--",
            *(path.as_posix() for path in EXACT10)
        ).split(b"\0")
        if row
    ]
    assert len(modes) == 10
    assert all(mode.startswith(b"100644 blob ") for mode in modes)
    branch = subprocess.run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    assert branch.stdout.decode().strip() == "main"
    origin = git(repo, "rev-parse", "refs/remotes/origin/main").decode().strip()
    if origin == BASE:
        return "formal_main_post_commit_unpushed"
    assert origin == head
    return "formal_main_post_push"


def _assignment_digest(row: dict[str, str]) -> str:
    value: dict[str, Any] = {field: row[field] for field in HASH_FIELDS}
    value["warhead_type_candidate_class_index_0based"] = int(
        value["warhead_type_candidate_class_index_0based"]
    )
    return digest(canonical(value).encode("utf-8"))


def _validate_review_record(record: dict[str, Any]) -> str:
    assert type(record) is dict
    assert record.get("review_record_version") == REVIEW_RECORD_VERSION
    unit_type = record.get("review_unit_type")
    assert type(unit_type) is str and unit_type in REVIEW_UNIT_TYPES
    fields = (
        CLASS_REVIEW_RECORD_FIELDS
        if unit_type == "candidate_class"
        else SAMPLE_REVIEW_RECORD_FIELDS
    )
    assert set(record) == set(fields)
    for field in fields:
        if field != "warhead_type_candidate_class_index_0based":
            assert type(record[field]) is str
    if unit_type == "candidate_class":
        assert type(record["warhead_type_candidate_class_index_0based"]) is int
        assert record["warhead_type_candidate_class_index_0based"] >= 0
        sha_fields = (
            "canonical_reaction_family_signature_sha256",
            "canonical_local_graph_rule_sha256",
            "source_class_record_sha256",
        )
        decisions = (
            record["reaction_family_identity_review_decision"],
            record["warhead_rule_topology_review_decision"],
        )
        assert all(decision in DECISIONS for decision in decisions)
        status = record["warhead_smarts_review_status"]
        candidate_smarts = record["candidate_warhead_smarts"]
        assert status in SMARTS_STATUSES
        assert not (status == "not_materialized" and candidate_smarts)
        assert not (
            status in {"candidate_not_reviewed", "approved", "revised"}
            and not meaningful_text(candidate_smarts)
        )
        assert not (
            status == "quarantined"
            and candidate_smarts != ""
            and not meaningful_text(candidate_smarts)
        )
    else:
        sha_fields = (
            "assignment_record_sha256",
            "source_assignment_record_sha256",
        )
        decisions = (record["sample_assignment_review_decision"],)
        assert decisions[0] in DECISIONS
        assert record["source_assignment_record_sha256"] == (
            record["assignment_record_sha256"]
        )
    assert all(LOWER_SHA256.fullmatch(record[field]) for field in sha_fields)
    record_digest = record["review_record_sha256"]
    assert record_digest == "" or LOWER_SHA256.fullmatch(record_digest)
    reviewer = record["reviewer_id"]
    rationale = record["review_rationale"]
    assert not (
        reviewer and reviewer.strip().casefold() in FORBIDDEN_REVIEWERS
    )
    human_decision_requires_metadata = any(
        decision != "not_reviewed" for decision in decisions
    )
    smarts_review_requires_metadata = (
        unit_type == "candidate_class"
        and record["warhead_smarts_review_status"]
        in SMARTS_HUMAN_REVIEWED_STATUSES
    )
    if human_decision_requires_metadata:
        assert meaningful_text(reviewer) and meaningful_text(rationale)
    elif smarts_review_requires_metadata:
        assert meaningful_text(reviewer) and meaningful_text(rationale)
    else:
        assert reviewer == rationale == ""
    return unit_type


def _review_record_hash_input(record: dict[str, Any]) -> dict[str, Any]:
    unit_type = _validate_review_record(record)
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


def _review_record_digest(record: dict[str, Any]) -> str:
    return digest(canonical(_review_record_hash_input(record)).encode("utf-8"))


def _assert_schema_failure(record: dict[str, Any]) -> None:
    try:
        _validate_review_record(record)
    except (AssertionError, KeyError, TypeError):
        return
    raise AssertionError("synthetic invalid review record did not fail closed")


def _family_approval(
    decision: object,
    reviewer: object,
    rationale: object,
    canonical_identity_sha256: object,
    source_identity_sha256: object,
) -> bool:
    return (
        type(decision) is str
        and decision == "approve"
        and meaningful_text(reviewer)
        and meaningful_text(rationale)
        and lower_sha256(canonical_identity_sha256)
        and lower_sha256(source_identity_sha256)
        and canonical_identity_sha256 == source_identity_sha256
    )


def _rule_approval(
    family_available: object,
    topology_decision: object,
    approved_smarts: object,
    smarts_review_status: object,
    smarts_match_count: object,
    smarts_includes_reactive_atom: object,
    warhead_atom_count: object,
    attachment_boundary_count: object,
    reviewer: object,
    rationale: object,
    identities_unchanged: object,
) -> bool:
    return (
        family_available is True
        and type(topology_decision) is str
        and topology_decision == "approve"
        and meaningful_text(approved_smarts)
        and type(smarts_review_status) is str
        and smarts_review_status == "approved"
        and exact_int(smarts_match_count)
        and smarts_match_count == 1
        and smarts_includes_reactive_atom is True
        and exact_int(warhead_atom_count)
        and warhead_atom_count > 0
        and exact_int(attachment_boundary_count)
        and attachment_boundary_count == 1
        and meaningful_text(reviewer)
        and meaningful_text(rationale)
        and identities_unchanged is True
    )


def _gold_completed(
    sample_decision: object,
    family_available: object,
    rule_available: object,
    assignment_record_sha256: object,
    source_assignment_record_sha256: object,
    reviewer: object,
    rationale: object,
) -> bool:
    return (
        type(sample_decision) is str
        and sample_decision == "approve"
        and family_available is True
        and rule_available is True
        and lower_sha256(assignment_record_sha256)
        and lower_sha256(source_assignment_record_sha256)
        and assignment_record_sha256 == source_assignment_record_sha256
        and meaningful_text(reviewer)
        and meaningful_text(rationale)
    )


def _role_ready(
    family_available: object,
    rule_available: object,
    gold_completed: object,
) -> bool:
    return (
        family_available is True
        and rule_available is True
        and gold_completed is True
    )


def check(
    repo: Path = ROOT, *, run_lifecycle_matrix: bool = True
) -> dict[str, Any]:
    observed_lifecycle = lifecycle(repo)
    source_payloads = {path: base(repo, path) for path in SOURCES}
    assert len(source_payloads) == 12
    assert all(digest(source_payloads[path]) == EXPECTED_SHA[path] for path in SOURCES)

    assignment_manifest = json.loads(source_payloads[ASSIGNMENT_MANIFEST])
    registry_manifest = json.loads(source_payloads[REGISTRY_MANIFEST])
    assert assignment_manifest["transaction_succeeded"] is True
    assert assignment_manifest["candidate_class_count"] == 7
    assert assignment_manifest["current11_sample_count"] == 11
    assert registry_manifest["transaction_succeeded"] is True

    source_classes = rows(source_payloads[CLASS_SOURCE])
    source_assignments = rows(source_payloads[ASSIGNMENT_SOURCE_CSV])
    source_families = rows(source_payloads[FAMILY_SOURCE])
    source_rules = rows(source_payloads[RULE_SOURCE])
    source_design = rows(source_payloads[DESIGN_SOURCE])
    assert len(source_classes) == len(source_families) == len(source_rules) == 7
    assert len(source_assignments) == len(source_design) == 11
    assert [int(row["warhead_type_candidate_class_index_0based"])
            for row in source_classes] == list(range(7))
    assert len({row["warhead_type_candidate_class_id"]
                for row in source_classes}) == 7
    assert len({row["sample_index_row_id"] for row in source_assignments}) == 11
    assert all(_assignment_digest(row) == row["assignment_record_sha256"]
               for row in source_assignments)

    families = {row["reaction_family_id"]: row for row in source_families}
    rules_by_id = {row["warhead_rule_id"]: row for row in source_rules}
    classes_by_id = {
        row["warhead_type_candidate_class_id"]: row for row in source_classes
    }
    for family in source_families:
        assert digest(
            canonical(
                json.loads(family["canonical_reaction_family_signature_json"])
            ).encode("utf-8")
        ) == family["canonical_reaction_family_signature_sha256"]
    for rule in source_rules:
        assert rule["reaction_family_id"] in families
        assert digest(
            canonical(json.loads(rule["canonical_local_graph_rule_json"])).encode(
                "utf-8"
            )
        ) == rule["canonical_local_graph_rule_sha256"]
        assert rule["approved_warhead_smarts"] == ""
        assert rule["approved"] == "false"
    for assignment in source_assignments:
        class_row = classes_by_id[assignment["warhead_type_candidate_class_id"]]
        rule = rules_by_id[assignment["candidate_warhead_rule_id"]]
        assert class_row["warhead_rule_id"] == assignment["candidate_warhead_rule_id"]
        assert class_row["reaction_family_id"] == (
            assignment["candidate_reaction_family_id"]
        )
        assert rule["reaction_family_id"] == assignment["candidate_reaction_family_id"]

    role_text = source_payloads[ROLE_SOURCE].decode("utf-8")
    assert "approved_reaction_family_warhead_rule" in role_text
    assert "approved_warhead_rule_present" in role_text

    output_payloads = {
        name: (repo / OUTPUT / name).read_bytes() for name in OUTPUT_FILES
    }
    source_inventory = rows(output_payloads[SOURCE_FILE])
    policy_rows = rows(output_payloads[POLICY_FILE])
    class_rows = rows(output_payloads[CLASS_FILE])
    sample_rows = rows(output_payloads[SAMPLE_FILE])
    failure_rows = rows(output_payloads[FAILURE_FILE])
    manifest = json.loads(output_payloads[MANIFEST_FILE])

    assert len(source_inventory) == 12
    assert [row["source_path"] for row in source_inventory] == [
        path.as_posix() for path in SOURCES
    ]
    assert [row["BASE_SHA256"] for row in source_inventory] == [
        EXPECTED_SHA[path] for path in SOURCES
    ]
    assert all(row["verified"] == "true" for row in source_inventory)

    assert len(policy_rows) == 12
    assert [row["policy_id"] for row in policy_rows] == [
        f"REVIEW_POLICY_{index:03d}" for index in range(1, 13)
    ]
    assert [row["semantic_name"] for row in policy_rows] == list(POLICY_NAMES)
    assert all(row["fails_closed"] == row["verified"] == "true"
               for row in policy_rows)

    support: dict[str, list[dict[str, str]]] = defaultdict(list)
    for assignment in source_assignments:
        support[assignment["warhead_type_candidate_class_id"]].append(assignment)
    assert len(class_rows) == 7
    for output_row, source_row in zip(class_rows, source_classes):
        linked = support[source_row["warhead_type_candidate_class_id"]]
        assert output_row["warhead_type_candidate_class_id"] == (
            source_row["warhead_type_candidate_class_id"]
        )
        assert output_row["reaction_family_id"] == source_row["reaction_family_id"]
        assert output_row["warhead_rule_id"] == source_row["warhead_rule_id"]
        assert output_row["canonical_reaction_family_signature_sha256"] == (
            source_row["canonical_reaction_family_signature_sha256"]
        )
        assert output_row["canonical_local_graph_rule_sha256"] == (
            source_row["canonical_local_graph_rule_sha256"]
        )
        assert output_row["representative_sample_ids"] == ";".join(
            sorted(row["sample_index_row_id"] for row in linked)
        )
        assert output_row["representative_component_ids"] == ";".join(
            sorted({row["ligand_comp_id"] for row in linked})
        )
        for field in (
            "family_identity_evidence_complete",
            "rule_topology_evidence_complete",
            "assignment_support_complete",
            "class_identity_verified",
            "class_review_package_ready",
            "ready_for_sample_assignment_review",
            "verified",
        ):
            assert output_row[field] == "true"
        assert output_row["reaction_family_identity_review_decision"] == "not_reviewed"
        assert output_row["warhead_rule_topology_review_decision"] == "not_reviewed"
        assert output_row["warhead_smarts_review_status"] == "not_materialized"
        assert output_row["candidate_warhead_smarts"] == ""
        assert output_row["reviewer_id"] == ""
        assert output_row["review_rationale"] == ""
        assert output_row["review_notes"] == ""
        for field in (
            "family_identity_review_completed",
            "rule_topology_review_completed",
            "warhead_rule_topology_review_passed",
            "approved_reaction_family_available",
            "approved_warhead_rule_available",
            "ready_for_role_proposal_generation",
            "ready_for_training",
        ):
            assert output_row[field] == "false"

    assignments_by_id = {
        row["sample_index_row_id"]: row for row in source_assignments
    }
    assert len(sample_rows) == 11
    for output_row in sample_rows:
        source_row = assignments_by_id[output_row["sample_index_row_id"]]
        for output_field, source_field in (
            ("pdb_id", "pdb_id"),
            ("ligand_comp_id", "ligand_comp_id"),
            ("assignment_record_sha256", "assignment_record_sha256"),
            ("warhead_type_candidate_class_id", "warhead_type_candidate_class_id"),
            ("reaction_family_id", "candidate_reaction_family_id"),
            ("warhead_rule_id", "candidate_warhead_rule_id"),
            ("target_residue_name", "target_residue_name"),
            ("target_residue_number", "target_residue_number"),
            ("target_residue_atom_name", "target_residue_atom_name"),
            ("ligand_reactive_atom_name", "ligand_reactive_atom_name"),
            ("component_parent_graph_sha256", "component_parent_graph_sha256"),
            ("observed_graph_sha256", "observed_graph_sha256"),
            ("radius_1_signature_sha256", "radius_1_signature_sha256"),
        ):
            assert output_row[output_field] == source_row[source_field]
        assert output_row["sample_assignment_review_decision"] == "not_reviewed"
        assert output_row["reviewer_id"] == ""
        assert output_row["review_rationale"] == ""
        assert output_row["review_notes"] == ""
        assert output_row["sample_review_package_ready"] == "true"
        assert output_row["verified"] == "true"
        for field in (
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
        ):
            assert output_row[field] == "false"

    assert len(failure_rows) == 30
    assert len({row["mutation_signature"] for row in failure_rows}) == 30
    for row, (field, value, reason) in zip(failure_rows, FAILURE_REASONS):
        assert row["mutated_field"] == field
        assert row["mutated_value_json"] == value
        assert row["mutation_signature"] == f"{field}={value}"
        assert row["expected_reason"] == reason
        assert reason in row["observed_reasons"].split(";")
        assert row["expected_reason_verified"] == "true"
        assert row["fails_closed"] == row["verified"] == "true"
        assert row["review_policy_registry_row_count"] == "0"
        assert row["candidate_class_review_readiness_row_count"] == "0"
        assert row["sample_assignment_review_readiness_row_count"] == "0"
        assert row["role_proposal_generation_ready"] == "false"
        assert row["mask_materialization_ready"] == "false"
        assert row["model_integration_ready"] == "false"
        assert row["training_ready"] == "false"

    assert manifest["source_count"] == 12
    assert manifest["review_decision_vocabulary"] == list(DECISIONS)
    assert manifest["smarts_review_status_vocabulary"] == list(SMARTS_STATUSES)
    assert manifest["review_record_version"] == REVIEW_RECORD_VERSION
    assert manifest["class_review_record_fields"] == list(
        CLASS_REVIEW_RECORD_FIELDS
    )
    assert manifest["sample_review_record_fields"] == list(
        SAMPLE_REVIEW_RECORD_FIELDS
    )

    # Synthetic empty drafts exercise only the schema/hash contract.  They are
    # never written and are not human-review records or decisions.
    synthetic_class_source_sha = digest(
        canonical(class_rows[0]).encode("utf-8")
    )
    class_draft: dict[str, Any] = {
        "review_record_version": REVIEW_RECORD_VERSION,
        "review_unit_type": "candidate_class",
        "warhead_type_candidate_class_index_0based":
            int(class_rows[0]["warhead_type_candidate_class_index_0based"]),
        "warhead_type_candidate_class_id":
            class_rows[0]["warhead_type_candidate_class_id"],
        "reaction_family_id": class_rows[0]["reaction_family_id"],
        "reaction_family_semantic_name":
            class_rows[0]["reaction_family_semantic_name"],
        "canonical_reaction_family_signature_sha256":
            class_rows[0]["canonical_reaction_family_signature_sha256"],
        "warhead_rule_id": class_rows[0]["warhead_rule_id"],
        "warhead_type_candidate_semantic_name":
            class_rows[0]["warhead_type_candidate_semantic_name"],
        "canonical_local_graph_rule_sha256":
            class_rows[0]["canonical_local_graph_rule_sha256"],
        "reaction_family_identity_review_decision": "not_reviewed",
        "warhead_rule_topology_review_decision": "not_reviewed",
        "warhead_smarts_review_status": "not_materialized",
        "candidate_warhead_smarts": "",
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        "source_class_record_sha256": synthetic_class_source_sha,
        "review_record_sha256": "",
    }
    assignment_sha = sample_rows[0]["assignment_record_sha256"]
    sample_draft: dict[str, Any] = {
        "review_record_version": REVIEW_RECORD_VERSION,
        "review_unit_type": "sample_assignment",
        "sample_index_row_id": sample_rows[0]["sample_index_row_id"],
        "assignment_record_sha256": assignment_sha,
        "warhead_type_candidate_class_id":
            sample_rows[0]["warhead_type_candidate_class_id"],
        "reaction_family_id": sample_rows[0]["reaction_family_id"],
        "warhead_rule_id": sample_rows[0]["warhead_rule_id"],
        "sample_assignment_review_decision": "not_reviewed",
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        "source_assignment_record_sha256": assignment_sha,
        "review_record_sha256": "",
    }
    assert _validate_review_record(class_draft) == "candidate_class"
    assert _validate_review_record(sample_draft) == "sample_assignment"
    assert SMARTS_UNREVIEWED_STATUSES + SMARTS_HUMAN_REVIEWED_STATUSES == (
        SMARTS_STATUSES
    )
    assert meaningful_text("human-reviewer")
    assert all(
        not meaningful_text(value)
        for value in ("", " ", "\t", "\n", True, 1, object())
    )
    assert all(
        lower_sha256(value)
        for value in ("a" * 64, "0123456789abcdef" * 4)
    )
    assert all(
        not lower_sha256(value)
        for value in (
            "",
            "abc",
            "a" * 63,
            "a" * 65,
            "A" * 64,
            " " + "a" * 64,
            "a" * 64 + " ",
            True,
            1,
            1.0,
            object(),
        )
    )
    assert exact_bool(True) and exact_bool(False)
    assert not exact_bool(1) and not exact_bool(object())
    assert exact_int(1) and not exact_int(True) and not exact_int(1.0)

    candidate_not_reviewed = dict(class_draft)
    candidate_not_reviewed["warhead_smarts_review_status"] = (
        "candidate_not_reviewed"
    )
    candidate_not_reviewed["candidate_warhead_smarts"] = "[C:1]"
    assert _validate_review_record(candidate_not_reviewed) == "candidate_class"
    approved_smarts = dict(class_draft)
    approved_smarts["warhead_smarts_review_status"] = "approved"
    approved_smarts["candidate_warhead_smarts"] = "[C:1]"
    approved_smarts["reviewer_id"] = "human-reviewer"
    approved_smarts["review_rationale"] = "SMARTS candidate approved after review"
    assert _validate_review_record(approved_smarts) == "candidate_class"
    quarantined_smarts = dict(class_draft)
    quarantined_smarts["warhead_smarts_review_status"] = "quarantined"
    quarantined_smarts["candidate_warhead_smarts"] = "[C:1]"
    quarantined_smarts["reviewer_id"] = "human-reviewer"
    quarantined_smarts["review_rationale"] = (
        "SMARTS candidate quarantined after review"
    )
    assert _validate_review_record(quarantined_smarts) == "candidate_class"
    quarantined_empty_smarts = dict(quarantined_smarts)
    quarantined_empty_smarts["candidate_warhead_smarts"] = ""
    assert _validate_review_record(quarantined_empty_smarts) == "candidate_class"

    class StringSubclass(str):
        pass

    valid_sha = "a" * 64
    family_valid = (
        "approve",
        "human-reviewer",
        "family reviewed",
        valid_sha,
        valid_sha,
    )
    result = _family_approval(*family_valid)
    assert result is True and type(result) is bool
    family_invalid = (
        ("approve", "   ", "family reviewed", valid_sha, valid_sha),
        ("approve", True, "family reviewed", valid_sha, valid_sha),
        ("approve", "human", "\t", valid_sha, valid_sha),
        (StringSubclass("approve"), "human", "reviewed", valid_sha, valid_sha),
        ("approve", "human", "reviewed", 1, True),
        ("approve", "human", "reviewed", True, 1),
        ("approve", "human", "reviewed", "abc", "abc"),
        ("approve", "human", "reviewed", "A" * 64, "A" * 64),
        (
            "approve",
            "human",
            "reviewed",
            " " + valid_sha,
            " " + valid_sha,
        ),
        ("approve", "human", "reviewed", valid_sha, "b" * 64),
    )
    for arguments in family_invalid:
        result = _family_approval(*arguments)
        assert result is False and type(result) is bool

    rule_valid = (
        True,
        "approve",
        "[C:1]",
        "approved",
        1,
        True,
        1,
        1,
        "human-reviewer",
        "SMARTS reviewed",
        True,
    )
    result = _rule_approval(*rule_valid)
    assert result is True and type(result) is bool
    rule_invalid = (
        (1, *rule_valid[1:]),
        (object(), *rule_valid[1:]),
        (*rule_valid[:4], True, *rule_valid[5:]),
        (*rule_valid[:4], 1.0, *rule_valid[5:]),
        (*rule_valid[:5], 1, *rule_valid[6:]),
        (*rule_valid[:6], True, *rule_valid[7:]),
        (*rule_valid[:6], 1.0, *rule_valid[7:]),
        (*rule_valid[:7], 1.0, *rule_valid[8:]),
        (*rule_valid[:10], object()),
        (*rule_valid[:2], "\t", *rule_valid[3:]),
        (*rule_valid[:9], "\n", rule_valid[10]),
        (
            rule_valid[0],
            StringSubclass("approve"),
            *rule_valid[2:],
        ),
        (
            *rule_valid[:3],
            StringSubclass("approved"),
            *rule_valid[4:],
        ),
    )
    for arguments in rule_invalid:
        result = _rule_approval(*arguments)
        assert result is False and type(result) is bool

    gold_valid = (
        "approve",
        True,
        True,
        valid_sha,
        valid_sha,
        "human-reviewer",
        "assignment reviewed",
    )
    result = _gold_completed(*gold_valid)
    assert result is True and type(result) is bool
    gold_invalid = (
        ("approve", 1, True, valid_sha, valid_sha, "human", "reviewed"),
        ("approve", object(), True, valid_sha, valid_sha, "human", "reviewed"),
        ("approve", True, 1, valid_sha, valid_sha, "human", "reviewed"),
        ("approve", True, True, 1, True, "human", "reviewed"),
        ("approve", True, True, "abc", "abc", "human", "reviewed"),
        ("approve", True, True, "A" * 64, "A" * 64, "human", "reviewed"),
        (
            "approve",
            True,
            True,
            " " + valid_sha,
            " " + valid_sha,
            "human",
            "reviewed",
        ),
        ("approve", True, True, valid_sha, "b" * 64, "human", "reviewed"),
        ("approve", True, True, valid_sha, valid_sha, object(), "reviewed"),
        ("approve", True, True, valid_sha, valid_sha, "human", "   "),
    )
    for arguments in gold_invalid:
        result = _gold_completed(*arguments)
        assert result is False and type(result) is bool

    result = _role_ready(True, True, True)
    assert result is True and type(result) is bool
    for arguments in (
        (1, True, True),
        (object(), True, True),
        (True, 1, True),
        (True, object(), True),
        (True, True, 1),
        (True, True, "yes"),
    ):
        result = _role_ready(*arguments)
        assert result is False and type(result) is bool

    assert _review_record_digest(class_draft) == _review_record_digest(
        dict(reversed(tuple(class_draft.items())))
    )
    populated = dict(sample_draft)
    populated["review_record_sha256"] = _review_record_digest(populated)
    assert populated["review_record_sha256"] == _review_record_digest(populated)
    self_changed = dict(populated)
    self_changed["review_record_sha256"] = "0" * 64
    assert _review_record_digest(self_changed) == _review_record_digest(populated)
    field_changed = dict(sample_draft)
    field_changed["review_notes"] = "synthetic contract-only note"
    assert _review_record_digest(field_changed) != _review_record_digest(
        sample_draft
    )

    missing = dict(class_draft)
    del missing["review_notes"]
    _assert_schema_failure(missing)
    extra = dict(sample_draft)
    extra["timestamp"] = "forbidden"
    _assert_schema_failure(extra)
    wrong_unit = dict(class_draft)
    wrong_unit["review_unit_type"] = "class"
    _assert_schema_failure(wrong_unit)
    wrong_version = dict(sample_draft)
    wrong_version["review_record_version"] = "v0"
    _assert_schema_failure(wrong_version)
    bool_index = dict(class_draft)
    bool_index["warhead_type_candidate_class_index_0based"] = True
    _assert_schema_failure(bool_index)
    bad_sha = dict(sample_draft)
    bad_sha["assignment_record_sha256"] = "bad"
    _assert_schema_failure(bad_sha)
    bad_decision = dict(sample_draft)
    bad_decision["sample_assignment_review_decision"] = "approved"
    _assert_schema_failure(bad_decision)
    reviewer_missing = dict(sample_draft)
    reviewer_missing["sample_assignment_review_decision"] = "approve"
    _assert_schema_failure(reviewer_missing)
    smarts_inconsistent = dict(class_draft)
    smarts_inconsistent["candidate_warhead_smarts"] = "[C:1]"
    _assert_schema_failure(smarts_inconsistent)
    approved_without_metadata = dict(class_draft)
    approved_without_metadata["warhead_smarts_review_status"] = "approved"
    approved_without_metadata["candidate_warhead_smarts"] = "[C:1]"
    _assert_schema_failure(approved_without_metadata)
    approved_whitespace_reviewer = dict(approved_smarts)
    approved_whitespace_reviewer["reviewer_id"] = "   "
    _assert_schema_failure(approved_whitespace_reviewer)
    revised_without_rationale = dict(class_draft)
    revised_without_rationale["warhead_smarts_review_status"] = "revised"
    revised_without_rationale["candidate_warhead_smarts"] = "[C:1]"
    revised_without_rationale["reviewer_id"] = "human-reviewer"
    _assert_schema_failure(revised_without_rationale)
    revised_whitespace_rationale = dict(revised_without_rationale)
    revised_whitespace_rationale["review_rationale"] = "\n"
    _assert_schema_failure(revised_whitespace_rationale)
    quarantined_without_reviewer = dict(class_draft)
    quarantined_without_reviewer["warhead_smarts_review_status"] = "quarantined"
    quarantined_without_reviewer["candidate_warhead_smarts"] = "[C:1]"
    quarantined_without_reviewer["review_rationale"] = "reviewed"
    _assert_schema_failure(quarantined_without_reviewer)
    quarantined_whitespace_smarts = dict(quarantined_smarts)
    quarantined_whitespace_smarts["candidate_warhead_smarts"] = "\t"
    _assert_schema_failure(quarantined_whitespace_smarts)
    candidate_with_metadata = dict(candidate_not_reviewed)
    candidate_with_metadata["reviewer_id"] = "human-reviewer"
    candidate_with_metadata["review_rationale"] = "not reviewed"
    _assert_schema_failure(candidate_with_metadata)
    candidate_whitespace_smarts = dict(candidate_not_reviewed)
    candidate_whitespace_smarts["candidate_warhead_smarts"] = "   "
    _assert_schema_failure(candidate_whitespace_smarts)
    not_reviewed_whitespace_metadata = dict(class_draft)
    not_reviewed_whitespace_metadata["reviewer_id"] = " "
    _assert_schema_failure(not_reviewed_whitespace_metadata)
    padded_forbidden_reviewer = dict(approved_smarts)
    padded_forbidden_reviewer["reviewer_id"] = "\tChatGPT\n"
    _assert_schema_failure(padded_forbidden_reviewer)
    second_identity = dict(sample_draft)
    second_identity["source_assignment_record_sha256"] = "d" * 64
    _assert_schema_failure(second_identity)

    counts = {
        "review_policy_count": 12,
        "candidate_class_count": 7,
        "current11_sample_count": 11,
        "class_review_package_ready_count": 7,
        "sample_review_package_ready_count": 11,
        "family_identity_review_completed_count": 0,
        "rule_topology_review_completed_count": 0,
        "sample_review_completed_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "approved_warhead_smarts_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "failure_mutation_count": 30,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
    }
    assert all(manifest[key] == value for key, value in counts.items())
    assert manifest["review_gate_design_completed"] is True
    assert manifest["ready_for_review_package_materialization"] is True
    for key in (
        "review_package_materialized",
        "human_review_execution_completed",
        "ready_for_human_review_execution",
        "ready_for_role_proposal_generation",
        "ready_for_mask_materialization",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
        "warhead_type_model_head_integrated",
        "warhead_type_loss_integrated",
        "role_annotation_materialized",
        "minimal_seed_materialized",
        "mask_materialized",
        "tensor_materialized",
        "model_changed",
        "training_used",
    ):
        assert manifest[key] is False
    assert MANIFEST_FILE not in manifest["output_sha256"]
    for name in OUTPUT_FILES[:-1]:
        assert manifest["output_sha256"][name] == digest(output_payloads[name])

    assert len(EXACT10) == len(set(EXACT10)) == 10
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    for relative in EXACT10:
        target = repo / relative
        assert target.is_file() and not target.is_symlink()
        assert stat.S_IMODE(target.stat(follow_symlinks=False).st_mode) in {
            0o644, 0o664,
        }
        assert target.stat(follow_symlinks=False).st_mode & 0o111 == 0
        assert relative.suffix.lower() not in forbidden

    matrix_report = None
    if run_lifecycle_matrix:
        matrix_report = exercise_hermetic_git_lifecycle_matrix(
            repo,
            repo.parent,
            base_commit=BASE,
            formal_commit_subject=SUBJECT,
            exact_paths=EXACT10,
        )
        assert matrix_report.cleanup_verified
        assert matrix_report.exact_path_count == 10
        assert (
            matrix_report.pre_commit.lifecycle,
            matrix_report.detached_candidate_post_commit.lifecycle,
            matrix_report.formal_main_post_commit_unpushed.lifecycle,
            matrix_report.formal_main_post_push.lifecycle,
        ) == (
            "pre_commit",
            "detached_candidate_post_commit",
            "formal_main_post_commit_unpushed",
            "formal_main_post_push",
        )

    return {
        "lifecycle": observed_lifecycle,
        "source_count": 12,
        "policy_count": 12,
        "class_count": 7,
        "sample_count": 11,
        "failure_count": 30,
        "candidate_commit": matrix_report.candidate_commit if matrix_report else "",
        "artifact_sha256": {
            name: digest(output_payloads[name]) for name in OUTPUT_FILES
        },
        "modules": "0/5",
        "ready_for_training": False,
    }


def main() -> int:
    report = check()
    print(
        "covapie_review_gate_design_check=passed "
        f"lifecycle={report['lifecycle']} "
        f"sources={report['source_count']} "
        f"policies={report['policy_count']} "
        f"classes={report['class_count']} "
        f"samples={report['sample_count']} "
        f"failures={report['failure_count']} "
        f"candidate={report['candidate_commit']} "
        f"modules={report['modules']} "
        "training_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
