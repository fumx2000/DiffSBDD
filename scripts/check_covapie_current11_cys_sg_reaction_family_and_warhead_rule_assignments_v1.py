#!/usr/bin/env python3
"""Independent checker for Current11 candidate family/rule assignments V1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_hermetic_git_lifecycle_harness_v1 import (  # noqa: E402
    exercise_hermetic_git_lifecycle_matrix,
)


BASE = "dc1222503dcec83220a28df2abdae898a0855864"
BASE_PARENT = "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288"
BASE_TREE = "7822087c57e62c229d1dd628d79cb736a5db44d0"
BASE_SUBJECT = (
    "add CovaPIE Cys SG reaction family and warhead rule registry design v1"
)
SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule assignments v1"
)
SCHEMA = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1"
)
OUT = Path("data/derived/covalent_small") / SCHEMA
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1"
)
FAMILY = DESIGN_ROOT / "covapie_cys_sg_reaction_family_registry.csv"
RULE = DESIGN_ROOT / "covapie_cys_sg_warhead_rule_registry.csv"
DESIGN = DESIGN_ROOT / "covapie_current11_reaction_family_and_warhead_rule_design_matrix.csv"
DESIGN_MANIFEST = (
    DESIGN_ROOT
    / "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_manifest.json"
)
PROJECTION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1"
)
MAPPING = PROJECTION_ROOT / "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
PROJECTION_READINESS = PROJECTION_ROOT / "covapie_current11_observed_projection_readiness_matrix.csv"
PROJECTION_MANIFEST = (
    PROJECTION_ROOT
    / "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json"
)
PAIR = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
FINAL = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
DESIGN_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
)
ROLE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
EXPECTED_SHA = {
    DESIGN_SOURCE: "db912d62c996bc91a0f8735135883f301ad61e3a448d5574770054c7f82db364",
    FAMILY: "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    RULE: "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    DESIGN: "24ae0fbd2dc1454574d9ed17145ba71d3b3132ffecfb84a1a831eceb77efab03",
    DESIGN_MANIFEST: "4603d124e2f90616ebf7d28975e0eeb77e3d4c90133688d87df2e30c9ac54ef9",
    MAPPING: "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    PROJECTION_READINESS: "ec7bb2c203a7b13f525c413171b734fdd9f8af934b6e7e8eaf3fc6ae141128a0",
    PROJECTION_MANIFEST: "e553e9cb1518cd2c9465772758539e9610c8f81cd702dd0440e99fbd143fc0a7",
    PAIR: "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    FINAL: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
}
SOURCES = (*EXPECTED_SHA, ROLE_SOURCE)

SOURCE_FILE = "covapie_assignment_materialization_source_inventory.csv"
VOCAB_FILE = "covapie_cys_sg_warhead_type_candidate_class_vocabulary.csv"
ASSIGN_FILE = "covapie_current11_cys_sg_candidate_assignment_authority.csv"
READY_FILE = "covapie_current11_cys_sg_assignment_review_readiness_matrix.csv"
FAILURE_FILE = "covapie_cys_sg_assignment_materialization_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    VOCAB_FILE,
    ASSIGN_FILE,
    READY_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
EXACT10 = (
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
    *(OUT / name for name in OUTPUT_FILES),
)
BLOCKERS = (
    "human_reaction_family_review_missing",
    "approved_warhead_rule_missing",
    "approved_warhead_smarts_missing",
    "current11_human_gold_review_missing",
)
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
EXPECTED_FAILURES = (
    "BASE_source_missing",
    "BASE_source_SHA_mismatch",
    "design_transaction_not_succeeded",
    "Current11_sample_coverage_incomplete",
    "duplicate_sample_identity",
    "rule_registry_missing",
    "family_registry_missing",
    "rule_JSON_SHA_mismatch",
    "family_JSON_SHA_mismatch",
    "rule_family_link_mismatch",
    "candidate_rule_absent",
    "candidate_rule_ambiguous",
    "candidate_family_absent",
    "candidate_family_ambiguous",
    "candidate_class_ordering_nondeterministic",
    "duplicate_candidate_class_index",
    "non_contiguous_candidate_class_index",
    "candidate_class_ID_mismatch",
    "sample_assigned_rule_mismatch",
    "sample_assigned_family_mismatch",
    "sample_semantic_name_mismatch",
    "parent_or_observed_graph_SHA_mismatch",
    "candidate_assignment_prematurely_promoted_to_approved",
    "training_label_prematurely_approved",
    "role_proposal_readiness_opened_without_approved_rule",
    "partial_materialization_attempted",
    "execution_boundary_crossed",
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
    if check and result.returncode != 0:
        raise AssertionError(
            "git_failed:" + " ".join(args) + ":" + result.stderr.decode("utf-8", "replace")
        )
    return result.stdout


def base(path: Path, repo: Path = ROOT) -> bytes:
    return git(repo, "show", f"{BASE}:{path.as_posix()}")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def lifecycle(repo: Path = ROOT) -> str:
    identity = git(repo, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE).decode().splitlines()
    assert identity == [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    if head == BASE:
        return "pre_commit"
    raw = git(repo, "cat-file", "commit", head)
    headers, separator, message = raw.partition(b"\n\n")
    assert separator
    parents = [line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")]
    assert parents == [BASE]
    subject, newline, body = message.partition(b"\n")
    assert newline and subject.decode() == SUBJECT and body == b""
    changed = {
        value.decode()
        for value in git(
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
    origin = git(repo, "rev-parse", "refs/remotes/origin/main").decode().strip()
    if origin == BASE:
        return "formal_main_post_commit_unpushed"
    assert origin == head
    return "formal_main_post_push"


def check(repo: Path = ROOT, *, run_lifecycle_matrix: bool = True) -> dict[str, Any]:
    observed_lifecycle = lifecycle(repo)
    source_payloads = {path: base(path, repo) for path in SOURCES}
    assert all(source_payloads.values())
    for path, expected in EXPECTED_SHA.items():
        assert digest(source_payloads[path]) == expected
    role_sha = digest(source_payloads[ROLE_SOURCE])
    assert role_sha == "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b"
    role_text = source_payloads[ROLE_SOURCE].decode()
    assert "approved_reaction_family_warhead_rule" in role_text
    assert "approved_warhead_rule_present" in role_text

    design_manifest = json.loads(source_payloads[DESIGN_MANIFEST])
    assert design_manifest["transaction_succeeded"] is True
    assert design_manifest["reaction_family_count"] == 7
    assert design_manifest["warhead_rule_count"] == 7
    assert design_manifest["candidate_family_assignment_exact_one_count"] == 11
    assert design_manifest["candidate_warhead_rule_assignment_exact_one_count"] == 11
    assert design_manifest["approved_warhead_rule_available"] is False

    family_rows = rows(source_payloads[FAMILY])
    rule_rows = rows(source_payloads[RULE])
    design_rows = rows(source_payloads[DESIGN])
    final_rows = rows(source_payloads[FINAL])
    assert len(family_rows) == len(rule_rows) == 7
    assert len(design_rows) == len(final_rows) == 11
    families = {row["reaction_family_id"]: row for row in family_rows}
    rules = {row["warhead_rule_id"]: row for row in rule_rows}
    assert len(families) == len(rules) == 7
    for row in family_rows:
        assert digest(
            canonical(json.loads(row["canonical_reaction_family_signature_json"])).encode()
        ) == row["canonical_reaction_family_signature_sha256"]
    for row in rule_rows:
        assert digest(
            canonical(json.loads(row["canonical_local_graph_rule_json"])).encode()
        ) == row["canonical_local_graph_rule_sha256"]
        assert row["reaction_family_id"] in families
        assert row["approved"] == "false"
        assert row["approved_warhead_smarts"] == ""

    output_rows = {
        name: rows((repo / OUT / name).read_bytes())
        for name in OUTPUT_FILES
        if name.endswith(".csv")
    }
    inventory = output_rows[SOURCE_FILE]
    vocab = output_rows[VOCAB_FILE]
    assignments = output_rows[ASSIGN_FILE]
    readiness = output_rows[READY_FILE]
    failures = output_rows[FAILURE_FILE]
    manifest = json.loads((repo / OUT / MANIFEST_FILE).read_bytes())

    assert len(inventory) == 11
    assert [row["source_path"] for row in inventory] == [path.as_posix() for path in SOURCES]
    for row, path in zip(inventory, SOURCES):
        assert row["BASE_SHA256"] == digest(source_payloads[path])
        assert row["verified"] == "true"

    expected_vocab = []
    for index, rule_row in enumerate(
        sorted(rule_rows, key=lambda row: row["canonical_local_graph_rule_sha256"])
    ):
        sha = rule_row["canonical_local_graph_rule_sha256"]
        family_row = families[rule_row["reaction_family_id"]]
        expected_vocab.append(
            {
                "warhead_type_candidate_class_index_0based": str(index),
                "warhead_type_candidate_class_id":
                    "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_" + sha[:16].upper(),
                "warhead_type_candidate_semantic_name":
                    rule_row["warhead_type_semantic_name"],
                "warhead_rule_id": rule_row["warhead_rule_id"],
                "reaction_family_id": rule_row["reaction_family_id"],
                "reaction_family_semantic_name":
                    family_row["reaction_family_semantic_name"],
                "canonical_local_graph_rule_sha256": sha,
                "canonical_reaction_family_signature_sha256":
                    family_row["canonical_reaction_family_signature_sha256"],
            }
        )
    assert len(vocab) == 7
    for actual, expected in zip(vocab, expected_vocab):
        for key, value in expected.items():
            assert actual[key] == value
        assert actual["assignment_status"] == "machine_derived_candidate_assignment_materialized"
        assert actual["review_status"] == "not_reviewed"
        assert actual["training_label_status"] == "not_approved_for_training"
        assert actual["approved_warhead_rule"] == "false"
        assert actual["human_gold_review_completed"] == "false"

    final_by_sample = {row["sample_index_row_id"]: row for row in final_rows}
    reactive = [
        row for row in rows(source_payloads[MAPPING]) if row["reactive_ligand_atom"] == "true"
    ]
    mapping_by_sample = {row["sample_index_row_id"]: row for row in reactive}
    pair_rows = rows(source_payloads[PAIR])
    assert len(reactive) == 11 and len(mapping_by_sample) == 11
    assert len(pair_rows) == 22
    assert Counter(row["sample_index_row_id"] for row in pair_rows) == Counter(
        {sample: 2 for sample in final_by_sample}
    )
    vocab_by_rule = {row["warhead_rule_id"]: row for row in vocab}
    design_by_sample = {row["sample_index_row_id"]: row for row in design_rows}
    assert len(assignments) == len(readiness) == len(design_by_sample) == 11
    assignment_by_sample = {row["sample_index_row_id"]: row for row in assignments}
    readiness_by_sample = {row["sample_index_row_id"]: row for row in readiness}
    assert len(assignment_by_sample) == len(readiness_by_sample) == 11
    for sample, design_row in design_by_sample.items():
        actual = assignment_by_sample[sample]
        final_row = final_by_sample[sample]
        map_row = mapping_by_sample[sample]
        class_row = vocab_by_rule[design_row["candidate_warhead_rule_id"]]
        assert actual["pdb_id"] == final_row["pdb_id"] == map_row["pdb_id"]
        assert actual["ligand_comp_id"] == final_row["ligand_comp_id"] == map_row["ligand_comp_id"]
        assert actual["ligand_reactive_atom_name"] == map_row["observed_atom_name"]
        assert actual["ligand_reactive_parent_ccd_atom_id"] == map_row["parent_ccd_atom_id"]
        assert actual["component_parent_graph_sha256"] == map_row["component_parent_graph_sha256"]
        assert actual["observed_graph_sha256"] == map_row["observed_graph_sha256"]
        assert actual["candidate_reaction_family_id"] == design_row["candidate_reaction_family_id"]
        assert actual["candidate_warhead_rule_id"] == design_row["candidate_warhead_rule_id"]
        assert actual["warhead_type_candidate_class_id"] == class_row["warhead_type_candidate_class_id"]
        assert actual["warhead_type_candidate_class_index_0based"] == class_row[
            "warhead_type_candidate_class_index_0based"
        ]
        hash_input: dict[str, Any] = {field: actual[field] for field in RECORD_FIELDS}
        hash_input["warhead_type_candidate_class_index_0based"] = int(
            hash_input["warhead_type_candidate_class_index_0based"]
        )
        expected_record_sha = digest(canonical(hash_input).encode())
        assert actual["assignment_record_sha256"] == expected_record_sha
        assert len(expected_record_sha) == 64
        assert actual["assignment_status"] == "machine_derived_candidate_assignment_materialized"
        assert actual["review_status"] == "not_reviewed"
        assert actual["training_label_status"] == "not_approved_for_training"
        assert actual["ready_for_assignment_human_review"] == "true"
        for field in (
            "formal_reaction_family_label_available",
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
            assert actual[field] == "false"
        ready = readiness_by_sample[sample]
        assert ready["assignment_record_sha256"] == expected_record_sha
        assert ready["human_review_package_ready"] == "true"
        assert ready["human_review_completed"] == "false"
        for field in (
            "approved_reaction_family_available",
            "approved_warhead_rule_available",
            "role_proposal_generation_ready",
            "minimal_seed_proposal_generation_ready",
            "mask_materialization_ready",
            "tensorization_ready",
            "model_integration_ready",
            "training_ready",
        ):
            assert ready[field] == "false"
        assert tuple(ready["blocking_reasons"].split(";")) == BLOCKERS

    assert len(failures) == 27
    assert len({row["mutation_signature"] for row in failures}) == 27
    assert tuple(row["expected_reason"] for row in failures) == EXPECTED_FAILURES
    for row, expected in zip(failures, EXPECTED_FAILURES):
        assert expected in row["observed_reasons"].split(";")
        assert row["expected_reason_verified"] == "true"
        assert row["fails_closed"] == row["verified"] == "true"
        assert row["candidate_class_vocabulary_row_count"] == "0"
        assert row["current11_assignment_authority_row_count"] == "0"
        assert row["assignment_review_readiness_row_count"] == "0"
        assert row["role_proposal_generation_ready"] == "false"
        assert row["mask_materialization_ready"] == "false"
        assert row["model_integration_ready"] == "false"
        assert row["training_ready"] == "false"

    assert manifest["formal_base"]["commit"] == BASE
    assert manifest["source_count"] == 11
    assert manifest["candidate_class_count"] == 7
    assert manifest["candidate_class_indices_contiguous"] is True
    assert manifest["candidate_class_ordering_key"] == "canonical_local_graph_rule_sha256_ascending"
    assert manifest["assignment_status_vocabulary"] == [
        "machine_derived_candidate_assignment_materialized",
        "candidate_assignment_blocked",
        "human_reviewed_approved",
        "human_reviewed_revised",
        "human_reviewed_quarantined",
    ]
    assert manifest["review_status_vocabulary"] == [
        "not_reviewed",
        "approved",
        "revised",
        "quarantined",
    ]
    assert manifest["training_label_status_vocabulary"] == [
        "not_approved_for_training",
        "approved_for_training",
    ]
    assert manifest["current11_sample_count"] == 11
    assert manifest["assignment_human_review_ready_count"] == 11
    for key in (
        "formal_reaction_family_label_available_count",
        "approved_warhead_rule_available_count",
        "human_gold_review_completed_count",
        "training_label_approved_count",
        "role_proposal_generation_ready_count",
        "minimal_seed_proposal_generation_ready_count",
        "mask_materialization_ready_count",
        "tensorization_ready_count",
        "model_integration_ready_count",
        "training_ready_count",
        "integrated_covalent_model_module_count",
    ):
        assert manifest[key] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["transaction_succeeded"] is True
    assert manifest["ready_for_assignment_human_review"] is True
    assert manifest["ready_for_role_proposal_generation"] is False
    assert manifest["ready_for_model_integration"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["recommended_next_step"] == (
        "design_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_v1"
    )
    assert MANIFEST_FILE not in manifest["output_sha256"]
    for name, expected in manifest["output_sha256"].items():
        assert digest((repo / OUT / name).read_bytes()) == expected
    encoded_manifest = canonical(manifest)
    assert "timestamp" not in encoded_manifest.lower()
    assert str(repo) not in encoded_manifest

    assert all((repo / path).is_file() for path in EXACT10)
    tree_modes = git(repo, "ls-tree", "-r", "HEAD", "--", *(path.as_posix() for path in EXACT10))
    if observed_lifecycle != "pre_commit":
        assert tree_modes.count(b"100644 blob ") == 10

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
        "source_count": 11,
        "role_contract_sha256": role_sha,
        "class_count": 7,
        "assignment_count": 11,
        "review_ready_count": 11,
        "failure_count": 27,
        "candidate_commit": matrix_report.candidate_commit if matrix_report else "",
        "modules": "0/5",
        "ready_for_training": False,
    }


def main() -> int:
    report = check()
    print(
        "covapie_assignment_check=passed "
        f"lifecycle={report['lifecycle']} "
        f"sources={report['source_count']} "
        f"classes={report['class_count']} "
        f"assignments={report['assignment_count']} "
        f"review_ready={report['review_ready_count']} "
        f"failures={report['failure_count']} "
        f"candidate={report['candidate_commit']} "
        f"modules={report['modules']} "
        "training_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
