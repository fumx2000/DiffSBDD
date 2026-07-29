"""Independent checker for blank Current11 Cys-SG review packages."""

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
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1
    as review_gate,
)
from covalent_ext.covapie_hermetic_git_lifecycle_harness_v1 import (
    exercise_hermetic_git_lifecycle_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "c0de1003ec1de9dd05e3c4204b458d1f3757d95d"
BASE_PARENT = "0c8d1d10260a028360357b8c309f22676fc81645"
BASE_TREE = "0434d3265acd47d3c96f3bfbd4166f753eb9054f"
BASE_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review gate "
    "design v1"
)
SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review "
    "packages v1"
)
SCHEMA = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1"
)
OUTPUT = Path("data/derived/covalent_small") / SCHEMA
CLASS_SOURCE_VERSION = "covapie_cys_sg_class_review_source_record_v1"
SAMPLE_SOURCE_VERSION = "covapie_current11_cys_sg_candidate_assignment_record_v1"
REVIEW_VERSION = "covapie_cys_sg_human_review_record_v1"

GATE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
    "design_v1.py"
)
GATE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
    "design_v1"
)
POLICY_SOURCE = (
    GATE_ROOT / "covapie_reaction_family_and_warhead_rule_review_policy_registry.csv"
)
CLASS_SOURCE = (
    GATE_ROOT / "covapie_cys_sg_candidate_class_review_readiness_matrix.csv"
)
SAMPLE_SOURCE = (
    GATE_ROOT / "covapie_current11_candidate_assignment_review_readiness_matrix.csv"
)
GATE_MANIFEST = (
    GATE_ROOT
    / "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_"
    "design_manifest.json"
)
ASSIGNMENT_CODE = Path(
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
ASSIGNMENT_SOURCE = (
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
FAMILY_SOURCE = REGISTRY_ROOT / "covapie_cys_sg_reaction_family_registry.csv"
RULE_SOURCE = REGISTRY_ROOT / "covapie_cys_sg_warhead_rule_registry.csv"
ROLE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
EXPECTED_SHA = {
    GATE_SOURCE:
        "08b7d7aeacfcd7065e6ea8aa2ae27b2cc4959d476fbb1568a5231307d7e308a1",
    POLICY_SOURCE:
        "af80255bfd507c26eeaab37a951e679edc166b2cf8f9da18aed3fb170ebc7881",
    CLASS_SOURCE:
        "b33f1b66900937548998076515ba8adc7376f7d9dd5893255aba38abe6470f78",
    SAMPLE_SOURCE:
        "1dc2499d8746285bb80851036c72b7c204e9feb53fea086acd788f2c04798c8c",
    GATE_MANIFEST:
        "8acf40e9771bbd6874a7d7cefbe09c8dec9d1ea2ba15a97625a06045f91d393d",
    ASSIGNMENT_CODE:
        "fe6c67940efef89290b2f276f9fb4c39245468181d52b219951a6f9ca7f454aa",
    CLASS_VOCABULARY:
        "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    ASSIGNMENT_SOURCE:
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    ASSIGNMENT_MANIFEST:
        "5e5acefc9051fc07d3243917292f073fc09fb432a0eb0325fa8d344d37c0e265",
    FAMILY_SOURCE:
        "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    RULE_SOURCE:
        "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    ROLE_SOURCE:
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
}
SOURCES = tuple(EXPECTED_SHA)

SOURCE_FILE = "covapie_review_package_source_inventory.csv"
PACKAGE_FILE = "covapie_review_package_index.csv"
CLASS_TEMPLATE_FILE = "covapie_cys_sg_candidate_class_review_record_templates.csv"
SAMPLE_TEMPLATE_FILE = "covapie_current11_sample_assignment_review_record_templates.csv"
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
EXACT10 = (
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
    *(OUTPUT / name for name in OUTPUT_FILES),
)

CLASS_SOURCE_FIELDS = (
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
CLASS_TEMPLATE_FIELDS = (
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
SAMPLE_TEMPLATE_FIELDS = (
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
ASSIGNMENT_FIELDS = (
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
LOWER_SHA = re.compile(r"[0-9a-f]{64}")

FAILURES = (
    ("base_source_present", "false", "BASE_source_missing"),
    ("base_source_sha_matches", "false", "BASE_source_SHA_mismatch"),
    ("review_gate_transaction_succeeded", "false", "review_gate_transaction_not_succeeded"),
    ("review_gate_design_completed", "false", "review_gate_design_not_completed"),
    ("package_materialization_ready", "false", "package_materialization_readiness_false"),
    ("class_source_count", "6", "class_source_count_not_7"),
    ("sample_source_count", "10", "sample_source_count_not_11"),
    ("duplicate_class_identity", "true", "duplicate_class_identity"),
    ("class_index_contiguous", "false", "class_index_non_contiguous"),
    ("duplicate_sample_identity", "true", "duplicate_sample_identity"),
    ("class_family_rule_links_match", "false", "class_family_rule_link_mismatch"),
    ("sample_class_family_rule_links_match", "false", "sample_class_family_rule_link_mismatch"),
    ("assignment_record_sha_matches", "false", "assignment_record_SHA_mismatch"),
    ("class_source_field_present", "false", "class_source_record_field_missing"),
    ("class_source_has_no_extra_field", "false", "class_source_record_extra_field"),
    ("class_source_exact_type_valid", "false", "class_source_record_exact_type_invalid"),
    ("class_source_bool_not_int", "false", "class_source_record_bool_as_int"),
    ("class_source_sha_matches", "false", "class_source_SHA_mismatch"),
    ("duplicate_class_source_sha", "true", "duplicate_class_source_SHA"),
    ("representative_samples_sorted", "false", "representative_sample_IDs_unsorted"),
    ("representative_samples_unique", "false", "representative_sample_IDs_duplicated"),
    ("representative_sample_coverage_matches", "false", "representative_sample_coverage_mismatch"),
    ("representative_components_valid", "false", "representative_component_IDs_invalid"),
    ("class_template_inventory_matches", "false", "class_template_field_inventory_mismatch"),
    ("sample_template_inventory_matches", "false", "sample_template_field_inventory_mismatch"),
    ("review_version_and_unit_match", "false", "review_version_or_unit_type_mismatch"),
    ("template_decisions_blank", "false", "template_decision_prefilled"),
    ("template_metadata_blank", "false", "template_reviewer_rationale_notes_prefilled"),
    ("template_smarts_blank", "false", "template_SMARTS_prefilled"),
    ("template_review_sha_blank", "false", "template_review_record_SHA_prefilled"),
    ("sample_source_assignment_sha_matches", "false", "sample_source_assignment_SHA_mismatch"),
    ("package_index_count_and_order_match", "false", "package_index_count_or_ordering_mismatch"),
    ("package_index_source_and_template_sha_match", "false", "package_index_source_or_template_SHA_mismatch"),
    ("partial_materialization_attempted", "true", "partial_materialization_attempted"),
    ("downstream_readiness_closed", "false", "downstream_readiness_prematurely_opened"),
    ("execution_boundary_crossed", "true", "execution_boundary_crossed"),
)


def run_git(repo: Path, *args: str, check: bool = True) -> bytes:
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
        raise AssertionError(
            f"git failed: {args!r}: {result.stderr.decode('utf-8', 'replace')}"
        )
    return result.stdout


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def header(payload: bytes) -> tuple[str, ...]:
    return tuple(csv.DictReader(io.StringIO(payload.decode("utf-8"))).fieldnames or ())


def base_payload(repo: Path, path: Path) -> bytes:
    payload = run_git(repo, "show", f"{BASE}:{path.as_posix()}")
    assert payload and digest(payload) == EXPECTED_SHA[path]
    return payload


def lifecycle(repo: Path) -> str:
    identity = run_git(
        repo, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    ).decode().splitlines()
    assert identity == [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    head = run_git(repo, "rev-parse", "HEAD").decode().strip()
    if head == BASE:
        return "pre_commit"
    raw = run_git(repo, "cat-file", "commit", head)
    headers, separator, message = raw.partition(b"\n\n")
    assert separator
    assert tuple(
        line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")
    ) == (BASE,)
    subject, newline, body = message.partition(b"\n")
    assert newline and subject.decode() == SUBJECT and body == b""
    changed = {
        value.decode()
        for value in run_git(
            repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).split(b"\0")
        if value
    }
    assert changed == {path.as_posix() for path in EXACT10}
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
    origin = run_git(repo, "rev-parse", "refs/remotes/origin/main").decode().strip()
    if origin == BASE:
        return "formal_main_post_commit_unpushed"
    assert origin == head
    return "formal_main_post_push"


def assignment_identity(row: Mapping[str, str]) -> dict[str, Any]:
    value: dict[str, Any] = {field: row[field] for field in ASSIGNMENT_FIELDS}
    value["warhead_type_candidate_class_index_0based"] = int(
        value["warhead_type_candidate_class_index_0based"]
    )
    return value


def reconstruct_class_sources(
    class_rows: Sequence[Mapping[str, str]],
    assignments: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[str]]:
    support: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in assignments:
        support[row["warhead_type_candidate_class_id"]].append(row)
    records = []
    shas = []
    for expected_index, row in enumerate(class_rows):
        assert int(row["warhead_type_candidate_class_index_0based"]) == expected_index
        linked = support[row["warhead_type_candidate_class_id"]]
        samples = row["representative_sample_ids"].split(";")
        components = row["representative_component_ids"].split(";")
        assert samples == sorted(samples) == sorted(
            item["sample_index_row_id"] for item in linked
        )
        assert len(samples) == len(set(samples))
        assert components == sorted(components) == sorted(
            {item["ligand_comp_id"] for item in linked}
        )
        assert len(components) == len(set(components))
        record = {
            "source_record_version": CLASS_SOURCE_VERSION,
            "formal_base_commit": BASE,
            "warhead_type_candidate_class_index_0based": expected_index,
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
            "representative_sample_ids": samples,
            "representative_component_ids": components,
            "family_identity_evidence_complete": row["family_identity_evidence_complete"] == "true",
            "rule_topology_evidence_complete": row["rule_topology_evidence_complete"] == "true",
            "assignment_support_complete": row["assignment_support_complete"] == "true",
            "class_identity_verified": row["class_identity_verified"] == "true",
            "source_class_readiness_file_sha256": EXPECTED_SHA[CLASS_SOURCE],
            "source_assignment_authority_file_sha256": EXPECTED_SHA[ASSIGNMENT_SOURCE],
            "source_family_registry_file_sha256": EXPECTED_SHA[FAMILY_SOURCE],
            "source_rule_registry_file_sha256": EXPECTED_SHA[RULE_SOURCE],
        }
        assert tuple(record) == CLASS_SOURCE_FIELDS
        assert record["selected_signature_radius"] == 1
        assert record["Current11_match_count"] == len(linked) > 0
        assert record["Current11_unique_component_count"] == len(components) > 0
        assert all(
            type(record[field]) is bool and record[field] is True
            for field in (
                "family_identity_evidence_complete",
                "rule_topology_evidence_complete",
                "assignment_support_complete",
                "class_identity_verified",
            )
        )
        records.append(record)
        shas.append(digest(canonical(record).encode()))
    assert len(records) == len(set(shas)) == 7
    return records, shas


def typed_class_template(row: Mapping[str, str]) -> dict[str, Any]:
    record: dict[str, Any] = dict(row)
    record["warhead_type_candidate_class_index_0based"] = int(
        record["warhead_type_candidate_class_index_0based"]
    )
    return record


def validate_blank_templates(
    class_templates: Sequence[Mapping[str, str]],
    sample_templates: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    assert len(class_templates) == 7 and len(sample_templates) == 11
    typed_classes = [typed_class_template(row) for row in class_templates]
    typed_samples = [dict(row) for row in sample_templates]
    for record in typed_classes:
        assert review_gate.validate_review_record_schema(record) == "candidate_class"
        assert record["reaction_family_identity_review_decision"] == "not_reviewed"
        assert record["warhead_rule_topology_review_decision"] == "not_reviewed"
        assert record["warhead_smarts_review_status"] == "not_materialized"
        assert record["candidate_warhead_smarts"] == ""
        assert all(
            record[field] == ""
            for field in (
                "reviewer_id", "review_rationale", "review_notes",
                "review_record_sha256",
            )
        )
    for record in typed_samples:
        assert review_gate.validate_review_record_schema(record) == "sample_assignment"
        assert record["sample_assignment_review_decision"] == "not_reviewed"
        assert record["source_assignment_record_sha256"] == record["assignment_record_sha256"]
        assert all(
            record[field] == ""
            for field in (
                "reviewer_id", "review_rationale", "review_notes",
                "review_record_sha256",
            )
        )
    return typed_classes, typed_samples


def check(
    repo_root: Path = ROOT, *, run_lifecycle_matrix: bool = True
) -> dict[str, Any]:
    repo = repo_root.resolve()
    observed_lifecycle = lifecycle(repo)
    source_payloads = {path: base_payload(repo, path) for path in SOURCES}
    gate_manifest = json.loads(source_payloads[GATE_MANIFEST])
    assignment_manifest = json.loads(source_payloads[ASSIGNMENT_MANIFEST])
    assert gate_manifest["transaction_succeeded"] is True
    assert gate_manifest["review_gate_design_completed"] is True
    assert gate_manifest["ready_for_review_package_materialization"] is True
    assert gate_manifest["class_review_package_ready_count"] == 7
    assert gate_manifest["sample_review_package_ready_count"] == 11
    assert gate_manifest["failure_mutation_count"] == 30
    assert assignment_manifest["transaction_succeeded"] is True

    class_rows = rows(source_payloads[CLASS_SOURCE])
    sample_ready = rows(source_payloads[SAMPLE_SOURCE])
    assignments = rows(source_payloads[ASSIGNMENT_SOURCE])
    families = rows(source_payloads[FAMILY_SOURCE])
    rules = rows(source_payloads[RULE_SOURCE])
    assert len(class_rows) == len(families) == len(rules) == 7
    assert len(sample_ready) == len(assignments) == 11
    assert len({row["sample_index_row_id"] for row in assignments}) == 11
    for row in assignments:
        assert digest(canonical(assignment_identity(row)).encode()) == row["assignment_record_sha256"]
    assert all(
        row["reaction_family_identity_review_decision"] == "not_reviewed"
        and row["warhead_rule_topology_review_decision"] == "not_reviewed"
        and row["warhead_smarts_review_status"] == "not_materialized"
        and row["candidate_warhead_smarts"] == ""
        and row["reviewer_id"] == ""
        and row["review_rationale"] == ""
        and row["review_notes"] == ""
        and row["approved_reaction_family_available"] == "false"
        and row["approved_warhead_rule_available"] == "false"
        for row in class_rows
    )
    assert all(
        row["sample_assignment_review_decision"] == "not_reviewed"
        and row["reviewer_id"] == ""
        and row["review_rationale"] == ""
        and row["review_notes"] == ""
        and row["human_gold_review_completed"] == "false"
        and row["training_label_approved"] == "false"
        for row in sample_ready
    )
    assert all(
        row["approved_warhead_smarts"] == ""
        and row["SMARTS_status"] == "not_materialized_in_design_stage"
        and row["approved"] == "false"
        for row in rules
    )

    class_sources, class_shas = reconstruct_class_sources(class_rows, assignments)
    output_payloads = {
        name: (repo / OUTPUT / name).read_bytes() for name in OUTPUT_FILES
    }
    assert header(output_payloads[CLASS_TEMPLATE_FILE]) == CLASS_TEMPLATE_FIELDS
    assert header(output_payloads[SAMPLE_TEMPLATE_FILE]) == SAMPLE_TEMPLATE_FIELDS
    class_templates_raw = rows(output_payloads[CLASS_TEMPLATE_FILE])
    sample_templates_raw = rows(output_payloads[SAMPLE_TEMPLATE_FILE])
    class_templates, sample_templates = validate_blank_templates(
        class_templates_raw, sample_templates_raw
    )
    for source, source_sha, template in zip(
        class_sources, class_shas, class_templates
    ):
        assert template["source_class_record_sha256"] == source_sha
        assert template["warhead_type_candidate_class_id"] == source["warhead_type_candidate_class_id"]
        assert template["reaction_family_id"] == source["reaction_family_id"]
        assert template["warhead_rule_id"] == source["warhead_rule_id"]
    ordered_assignments = sorted(assignments, key=lambda row: row["sample_index_row_id"])
    for source, template in zip(ordered_assignments, sample_templates):
        assert template["sample_index_row_id"] == source["sample_index_row_id"]
        assert template["assignment_record_sha256"] == source["assignment_record_sha256"]
        assert template["source_assignment_record_sha256"] == source["assignment_record_sha256"]

    package_rows = rows(output_payloads[PACKAGE_FILE])
    assert len(package_rows) == 18
    assert [int(row["package_item_order_0based"]) for row in package_rows] == list(range(18))
    assert [row["package_item_type"] for row in package_rows[:7]] == ["candidate_class"] * 7
    assert [row["package_item_type"] for row in package_rows[7:]] == ["sample_assignment"] * 11
    all_templates = [*class_templates, *sample_templates]
    expected_source_json = [
        *(canonical(source) for source in class_sources),
        *(canonical(assignment_identity(row)) for row in ordered_assignments),
    ]
    expected_source_shas = [
        *class_shas, *(row["assignment_record_sha256"] for row in ordered_assignments)
    ]
    for package, template, source_json, source_sha in zip(
        package_rows, all_templates, expected_source_json, expected_source_shas
    ):
        assert package["source_record_json"] == source_json
        assert package["source_record_sha256"] == source_sha == digest(source_json.encode())
        assert package["unreviewed_template_payload_sha256"] == digest(
            canonical(template).encode()
        )
        assert package["review_record_sha256_populated"] == "false"
        assert package["human_review_execution_completed"] == "false"
        assert package["package_item_materialized"] == "true"
        assert package["verified"] == "true"
    for package in package_rows[:7]:
        assert package["source_record_version"] == CLASS_SOURCE_VERSION
        assert package["family_identity_review_ready"] == "true"
        assert package["rule_topology_review_ready"] == "true"
        assert package["SMARTS_review_ready"] == "false"
        assert package["sample_assignment_review_ready"] == "false"
    for package in package_rows[7:]:
        assert package["source_record_version"] == SAMPLE_SOURCE_VERSION
        assert package["family_identity_review_ready"] == "false"
        assert package["rule_topology_review_ready"] == "false"
        assert package["SMARTS_review_ready"] == "false"
        assert package["sample_assignment_review_ready"] == "true"

    failure_rows = rows(output_payloads[FAILURE_FILE])
    assert len(failure_rows) == len(FAILURES) == 36
    assert len({row["mutation_signature"] for row in failure_rows}) == 36
    for (field, value, reason), row in zip(FAILURES, failure_rows):
        assert row["mutated_field"] == field
        assert row["mutated_value_json"] == value
        assert row["mutation_signature"] == f"{field}={value}"
        assert row["expected_reason"] == reason
        assert reason in row["observed_reasons"].split(";")
        assert row["expected_reason_verified"] == "true"
        assert row["fails_closed"] == "true"
        assert row["review_package_index_row_count"] == "0"
        assert row["class_review_template_row_count"] == "0"
        assert row["sample_review_template_row_count"] == "0"
        assert row["role_proposal_generation_ready"] == "false"
        assert row["mask_materialization_ready"] == "false"
        assert row["model_integration_ready"] == "false"
        assert row["training_ready"] == "false"
        assert row["verified"] == "true"

    source_inventory = rows(output_payloads[SOURCE_FILE])
    assert len(source_inventory) == 12
    assert [row["source_path"] for row in source_inventory] == [
        path.as_posix() for path in SOURCES
    ]
    assert all(
        row["BASE_SHA256"] == EXPECTED_SHA[path]
        and row["Current11_coverage"] == "11/11"
        and row["verified"] == "true"
        for row, path in zip(source_inventory, SOURCES)
    )
    manifest = json.loads(output_payloads[MANIFEST_FILE])
    assert manifest["formal_base"] == {
        "commit": BASE,
        "parent": BASE_PARENT,
        "tree": BASE_TREE,
        "subject": BASE_SUBJECT,
    }
    assert manifest["source_count"] == 12
    assert manifest["class_source_record_fields"] == list(CLASS_SOURCE_FIELDS)
    assert manifest["class_source_record_count"] == 7
    assert manifest["class_source_record_sha_unique_count"] == 7
    assert manifest["class_review_record_fields"] == list(CLASS_TEMPLATE_FIELDS)
    assert manifest["sample_review_record_fields"] == list(SAMPLE_TEMPLATE_FIELDS)
    assert manifest["class_review_template_count"] == 7
    assert manifest["sample_review_template_count"] == 11
    assert manifest["review_package_item_count"] == 18
    assert manifest["failure_mutation_count"] == 36
    assert manifest["template_decision_not_reviewed_count"] == 18
    for field in (
        "template_reviewer_nonempty_count", "template_rationale_nonempty_count",
        "template_notes_nonempty_count", "template_SMARTS_nonempty_count",
        "template_review_record_sha_populated_count",
        "approved_reaction_family_available_count",
        "approved_warhead_rule_available_count", "approved_warhead_smarts_count",
        "human_gold_review_completed_count", "training_label_approved_count",
        "integrated_covalent_model_module_count",
    ):
        assert manifest[field] == 0 and type(manifest[field]) is int
    for field in (
        "transaction_succeeded", "review_package_materialized",
        "ready_for_family_identity_review_execution",
        "ready_for_rule_topology_review_execution",
        "ready_for_sample_assignment_review_execution",
        "ready_for_human_review_execution",
    ):
        assert manifest[field] is True
    for field in (
        "ready_for_SMARTS_review_execution",
        "ready_for_complete_human_review_execution",
        "human_review_execution_completed", "ready_for_role_proposal_generation",
        "ready_for_minimal_seed_proposal_generation",
        "ready_for_mask_materialization", "ready_for_tensorization",
        "ready_for_model_integration", "ready_for_training",
        "role_annotation_materialized", "minimal_seed_materialized",
        "mask_materialized", "tensor_materialized", "model_changed",
        "training_used", "warhead_type_model_head_integrated",
        "warhead_type_loss_integrated",
    ):
        assert manifest[field] is False
    assert MANIFEST_FILE not in manifest["output_sha256"]
    assert manifest["output_sha256"] == {
        name: digest(output_payloads[name])
        for name in OUTPUT_FILES if name != MANIFEST_FILE
    }

    combined = b"".join(output_payloads.values())
    assert str(repo).encode() not in combined
    assert b"timestamp" not in combined.lower()
    assert b"chatgpt" not in combined.lower()
    assert b"codex" not in combined.lower()
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    for relative in EXACT10:
        target = repo / relative
        assert target.is_file() and not target.is_symlink()
        mode = stat.S_IMODE(target.stat(follow_symlinks=False).st_mode)
        assert mode in {0o644, 0o664} and mode & 0o111 == 0
        assert relative.suffix.lower() not in forbidden

    matrix = None
    if run_lifecycle_matrix:
        matrix = exercise_hermetic_git_lifecycle_matrix(
            repo,
            repo.parent,
            base_commit=BASE,
            formal_commit_subject=SUBJECT,
            exact_paths=EXACT10,
        )
        assert matrix.cleanup_verified
        assert matrix.candidate_parent == BASE
        assert matrix.candidate_subject == SUBJECT
        assert matrix.exact_path_count == 10
        assert (
            matrix.pre_commit.lifecycle,
            matrix.detached_candidate_post_commit.lifecycle,
            matrix.formal_main_post_commit_unpushed.lifecycle,
            matrix.formal_main_post_push.lifecycle,
        ) == (
            "pre_commit",
            "detached_candidate_post_commit",
            "formal_main_post_commit_unpushed",
            "formal_main_post_push",
        )
    return {
        "lifecycle": observed_lifecycle,
        "source_count": 12,
        "class_source_count": 7,
        "class_template_count": 7,
        "sample_template_count": 11,
        "package_count": 18,
        "failure_count": 36,
        "candidate_commit": matrix.candidate_commit if matrix else "",
        "class_source_sha256": class_shas,
        "artifact_sha256": {
            name: digest(output_payloads[name]) for name in OUTPUT_FILES
        },
        "modules": "0/5",
        "ready_for_training": False,
    }


def main() -> int:
    report = check()
    print(
        "covapie_review_packages_check=passed "
        f"lifecycle={report['lifecycle']} "
        f"sources={report['source_count']} "
        f"class_sources={report['class_source_count']} "
        f"class_templates={report['class_template_count']} "
        f"sample_templates={report['sample_template_count']} "
        f"packages={report['package_count']} "
        f"failures={report['failure_count']} "
        f"candidate={report['candidate_commit']} "
        f"modules={report['modules']} "
        "training_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
