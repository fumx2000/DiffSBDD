from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import get_type_hints

import pytest

from covalent_ext import (
    covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1 as stage,
)
from covalent_ext.covapie_hermetic_git_lifecycle_harness_v1 import (
    exercise_hermetic_git_lifecycle_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER = (
    ROOT
    / "scripts"
    / "check_covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
)


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def result() -> stage.BuildResult:
    return stage.build_result(ROOT)


@pytest.fixture(scope="module")
def payloads() -> dict[str, bytes]:
    return stage.build_evidence_payloads(ROOT)


def test_fixed_interpreter_contract() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"


def test_formal_base_identity_and_current_lifecycle() -> None:
    shown = subprocess.run(
        (
            "git",
            "show",
            "-s",
            "--format=%H%n%P%n%T%n%s",
            stage.BASE_COMMIT,
        ),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout.decode().splitlines()
    assert shown == [
        stage.BASE_COMMIT,
        stage.BASE_PARENT,
        stage.BASE_TREE,
        stage.BASE_SUBJECT,
    ]
    assert stage.validate_execution_boundary_v1(ROOT) in {
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    }


def test_all_11_sources_are_read_from_base_and_sha_frozen(
    result: stage.BuildResult,
) -> None:
    assert len(stage.SOURCE_PATHS) == len(result.source_rows) == 11
    assert tuple(row["source_path"] for row in result.source_rows) == tuple(
        path.as_posix() for path in stage.SOURCE_PATHS
    )
    for row, path in zip(result.source_rows, stage.SOURCE_PATHS):
        base_payload = stage.base_bytes(ROOT, path)
        assert row["BASE_SHA256"] == hashlib.sha256(base_payload).hexdigest()
        if path in stage.FROZEN_BASE_SHA256:
            assert row["BASE_SHA256"] == stage.FROZEN_BASE_SHA256[path]
    role = next(
        row for row in result.source_rows if row["source_path"] == stage.ROLE_CONTRACT_SOURCE.as_posix()
    )
    assert role["BASE_SHA256"] == (
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b"
    )


def test_transaction_and_exact_source_authorities(result: stage.BuildResult) -> None:
    assert result.transaction_succeeded
    assert result.blocking_reasons == ()
    assert len(result.vocabulary_rows) == 7
    assert len(result.assignment_rows) == len(result.readiness_rows) == 11
    assert all(row["verified"] for row in result.source_rows)


def test_candidate_vocabulary_uses_full_sha_order_only(
    result: stage.BuildResult,
) -> None:
    rows = result.vocabulary_rows
    digests = [row["canonical_local_graph_rule_sha256"] for row in rows]
    assert digests == sorted(digests)
    assert [row["warhead_type_candidate_class_index_0based"] for row in rows] == list(
        range(7)
    )
    assert len(set(digests)) == 7
    assert len({row["warhead_rule_id"] for row in rows}) == 7
    assert len({row["reaction_family_id"] for row in rows}) == 7
    assert len({row["warhead_type_candidate_class_id"] for row in rows}) == 7
    assert digests != [
        row["canonical_local_graph_rule_sha256"]
        for row in sorted(
            rows,
            key=lambda row: (
                -int(row["Current11_match_count"]),
                row["warhead_type_candidate_semantic_name"],
            ),
        )
    ]
    assert digests != [
        row["canonical_local_graph_rule_sha256"]
        for row in sorted(rows, key=lambda row: row["warhead_type_candidate_semantic_name"])
    ]


def test_all_seven_class_ids_are_sha_derived(result: stage.BuildResult) -> None:
    expected = [
        "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_106441A31FA4F951",
        "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_1D1D9C797859191F",
        "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_3B7FB1395768B690",
        "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_8B640E1A031138F0",
        "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_CEAC766EEE61D251",
        "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_DF48FCEE8872B92A",
        "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_EE022EB419200D14",
    ]
    actual = [row["warhead_type_candidate_class_id"] for row in result.vocabulary_rows]
    assert actual == expected
    for row in result.vocabulary_rows:
        assert row["warhead_type_candidate_class_id"] == (
            "COVAPIE_CYS_SG_WARHEAD_TYPE_CLASS_"
            + row["canonical_local_graph_rule_sha256"][:16].upper()
        )


def test_sample_rule_family_class_join_is_exact_one(
    result: stage.BuildResult,
) -> None:
    class_by_rule = {
        row["warhead_rule_id"]: row for row in result.vocabulary_rows
    }
    assert len(class_by_rule) == 7
    assert len({row["sample_index_row_id"] for row in result.assignment_rows}) == 11
    for row in result.assignment_rows:
        class_row = class_by_rule[row["candidate_warhead_rule_id"]]
        assert row["candidate_reaction_family_id"] == class_row["reaction_family_id"]
        assert row["warhead_type_candidate_class_id"] == class_row[
            "warhead_type_candidate_class_id"
        ]
        assert row["candidate_rule_assignment_exact_one"]
        assert row["candidate_family_assignment_exact_one"]
        assert row["class_vocabulary_join_exact_one"]


def test_reactive_atoms_and_graph_sha_match_base_mapping(
    result: stage.BuildResult,
) -> None:
    mapping = [
        row
        for row in csv_rows(stage.base_bytes(ROOT, stage.ATOM_MAPPING))
        if row["reactive_ligand_atom"] == "true"
    ]
    mapping_by_sample = {row["sample_index_row_id"]: row for row in mapping}
    assert len(mapping) == len(mapping_by_sample) == 11
    for row in result.assignment_rows:
        expected = mapping_by_sample[row["sample_index_row_id"]]
        assert row["ligand_reactive_atom_name"] == expected["observed_atom_name"]
        assert row["ligand_reactive_atom_element"] == expected["observed_type_symbol"]
        assert row["ligand_reactive_parent_ccd_atom_id"] == expected["parent_ccd_atom_id"]
        assert row["component_parent_graph_sha256"] == expected[
            "component_parent_graph_sha256"
        ]
        assert row["observed_graph_sha256"] == expected["observed_graph_sha256"]


def test_assignment_record_sha_is_canonical_deterministic_and_order_independent(
    result: stage.BuildResult,
) -> None:
    row = result.assignment_rows[0]
    record = stage.assignment_hash_input(row)
    reversed_record = dict(reversed(tuple(record.items())))
    first = stage.assignment_record_sha256(record)
    second = stage.assignment_record_sha256(record)
    assert first == second == stage.assignment_record_sha256(reversed_record)
    assert first == row["assignment_record_sha256"]
    assert len(first) == 64
    int(first, 16)
    assert "assignment_record_sha256" not in record
    assert len({row["assignment_record_sha256"] for row in result.assignment_rows}) == 11


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidate_reaction_family_id", "CHANGED_FAMILY"),
        ("candidate_warhead_rule_id", "CHANGED_RULE"),
        ("warhead_type_candidate_class_id", "CHANGED_CLASS"),
        ("warhead_type_candidate_class_index_0based", 99),
        ("assignment_status", "human_reviewed_approved"),
        ("review_status", "approved"),
        ("training_label_status", "approved_for_training"),
    ),
)
def test_assignment_record_sha_changes_for_every_id_class_or_status(
    result: stage.BuildResult, field: str, value: object
) -> None:
    record = stage.assignment_hash_input(result.assignment_rows[0])
    changed = dict(record)
    changed[field] = value
    assert stage.assignment_record_sha256(changed) != stage.assignment_record_sha256(
        record
    )


def test_candidate_formal_approved_and_training_states_are_separate(
    result: stage.BuildResult,
) -> None:
    assert stage.ASSIGNMENT_STATUSES == (
        "machine_derived_candidate_assignment_materialized",
        "candidate_assignment_blocked",
        "human_reviewed_approved",
        "human_reviewed_revised",
        "human_reviewed_quarantined",
    )
    assert stage.REVIEW_STATUSES == (
        "not_reviewed",
        "approved",
        "revised",
        "quarantined",
    )
    assert stage.TRAINING_LABEL_STATUSES == (
        "not_approved_for_training",
        "approved_for_training",
    )
    for row in result.assignment_rows:
        assert row["assignment_status"] == stage.ASSIGNMENT_STATUS
        assert row["review_status"] == "not_reviewed"
        assert row["training_label_status"] == "not_approved_for_training"
        assert row["candidate_reaction_family_assignment_materialized"]
        assert row["candidate_warhead_rule_assignment_materialized"]
        assert row["warhead_type_candidate_label_available"]
        assert not row["formal_reaction_family_label_available"]
        assert not row["approved_warhead_rule_available"]
        assert not row["human_gold_review_completed"]
        assert not row["training_label_approved"]


def test_review_package_is_exact11_and_every_downstream_gate_stays_closed(
    result: stage.BuildResult,
) -> None:
    assert sum(row["human_review_package_ready"] for row in result.readiness_rows) == 11
    for row in result.readiness_rows:
        assert row["candidate_assignment_materialized"]
        assert row["candidate_class_index_available"]
        assert row["candidate_class_id_available"]
        assert row["assignment_identity_verified"]
        assert not row["human_review_completed"]
        assert not row["approved_reaction_family_available"]
        assert not row["approved_warhead_rule_available"]
        assert not row["role_proposal_generation_ready"]
        assert not row["minimal_seed_proposal_generation_ready"]
        assert not row["mask_materialization_ready"]
        assert not row["tensorization_ready"]
        assert not row["model_integration_ready"]
        assert not row["training_ready"]
        assert tuple(row["blocking_reasons"].split(";")) == stage.ASSIGNMENT_BLOCKERS


def test_role_and_seed_contract_prerequisite_remains_enforced() -> None:
    source = stage.base_bytes(ROOT, stage.ROLE_CONTRACT_SOURCE).decode("utf-8")
    assert "approved_reaction_family_warhead_rule" in source
    assert "approved_warhead_rule_present" in source
    assert "approved_warhead_rule_missing" in source


def test_no_smarts_tensor_head_loss_or_model_integration(
    result: stage.BuildResult, payloads: dict[str, bytes]
) -> None:
    rule_rows = csv_rows(stage.base_bytes(ROOT, stage.RULE_REGISTRY))
    assert all(row["approved_warhead_smarts"] == "" for row in rule_rows)
    manifest = json.loads(payloads[stage.MANIFEST_FILE])
    assert not manifest["warhead_type_label_tensor_materialized"]
    assert not manifest["warhead_type_one_hot_materialized"]
    assert not manifest["warhead_type_model_head_integrated"]
    assert not manifest["warhead_type_loss_integrated"]
    assert not manifest["role_annotation_materialized"]
    assert not manifest["minimal_seed_materialized"]
    assert not manifest["mask_materialized"]
    assert not manifest["tensor_materialized"]
    assert not manifest["model_changed"]
    assert not manifest["training_used"]
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0


def test_transaction_failure_makes_all_three_core_tables_header_only(
    result: stage.BuildResult,
) -> None:
    tables = stage.transaction_tables(
        ("synthetic_phase_blocker",),
        result.vocabulary_rows,
        result.assignment_rows,
        result.readiness_rows,
    )
    assert tables == ((), (), ())
    assert csv_rows(stage._csv_bytes(stage.VOCABULARY_COLUMNS, tables[0])) == []
    assert csv_rows(stage._csv_bytes(stage.ASSIGNMENT_COLUMNS, tables[1])) == []
    assert csv_rows(stage._csv_bytes(stage.READINESS_COLUMNS, tables[2])) == []


def test_failure_matrix_is_exact27_typed_unique_and_fail_closed(
    result: stage.BuildResult,
) -> None:
    assert len(stage.FAILURE_MUTATIONS) == len(result.failure_rows) == 27
    assert len({row["mutation_signature"] for row in result.failure_rows}) == 27
    baseline = stage.AssignmentScenario()
    scenario_types = get_type_hints(stage.AssignmentScenario)
    for mutation, row in zip(stage.FAILURE_MUTATIONS, result.failure_rows):
        case, field, value, expected = mutation
        assert field in {item.name for item in dataclasses.fields(baseline)}
        assert type(value) is scenario_types[field]
        assert value != getattr(baseline, field)
        assert row["failure_case"] == case
        assert row["expected_reason"] == expected
        assert expected in row["observed_reasons"].split(";")
        assert row["expected_reason_verified"]
        assert row["fails_closed"]
        assert row["candidate_class_vocabulary_row_count"] == 0
        assert row["current11_assignment_authority_row_count"] == 0
        assert row["assignment_review_readiness_row_count"] == 0
        assert not row["role_proposal_generation_ready"]
        assert not row["mask_materialization_ready"]
        assert not row["model_integration_ready"]
        assert not row["training_ready"]
        assert row["verified"]


def test_manifest_is_truthful_and_has_no_self_sha_or_machine_metadata(
    payloads: dict[str, bytes],
) -> None:
    manifest = json.loads(payloads[stage.MANIFEST_FILE])
    assert manifest["source_count"] == 11
    assert manifest["candidate_class_count"] == 7
    assert manifest["candidate_class_indices_contiguous"]
    assert manifest["candidate_class_ordering_key"] == stage.CLASS_ORDERING_KEY
    assert manifest["assignment_status_vocabulary"] == list(stage.ASSIGNMENT_STATUSES)
    assert manifest["review_status_vocabulary"] == list(stage.REVIEW_STATUSES)
    assert manifest["training_label_status_vocabulary"] == list(
        stage.TRAINING_LABEL_STATUSES
    )
    assert manifest["current11_sample_count"] == 11
    assert manifest["assignment_human_review_ready_count"] == 11
    assert manifest["role_proposal_generation_ready_count"] == 0
    assert manifest["training_ready_count"] == 0
    assert manifest["failure_mutation_count"] == 27
    assert manifest["failure_mutations_all_fail_closed"]
    assert manifest["transaction_succeeded"]
    assert manifest["ready_for_assignment_human_review"]
    assert not manifest["ready_for_role_proposal_generation"]
    assert not manifest["ready_for_model_integration"]
    assert not manifest["ready_for_training"]
    assert stage.MANIFEST_FILE not in manifest["output_sha256"]
    encoded = stage.canonical_json(manifest)
    assert "timestamp" not in encoded.lower()
    assert str(ROOT) not in encoded


def test_builder_is_byte_deterministic_and_matches_materialized_exact6(
    payloads: dict[str, bytes],
) -> None:
    second = stage.build_evidence_payloads(ROOT)
    assert payloads == second
    assert tuple(payloads) == stage.OUTPUT_FILES
    for name, payload in payloads.items():
        assert (ROOT / stage.OUTPUT_ROOT / name).read_bytes() == payload


def test_independent_checker_reconstructs_all_authorities() -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        (sys.executable, "-B", str(CHECKER)),
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    assert completed.stderr == b""
    assert b"covapie_assignment_check=passed" in completed.stdout
    assert b"classes=7 assignments=11 review_ready=11 failures=27" in completed.stdout
    assert b"modules=0/5 training_ready=false" in completed.stdout


def test_exact10_paths_are_safe_and_only_authorized_inventory() -> None:
    assert len(stage.EXACT10_PATHS) == len(set(stage.EXACT10_PATHS)) == 10
    assert all((ROOT / path).is_file() for path in stage.EXACT10_PATHS)
    forbidden = {
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".tmp",
        ".part",
    }
    assert not any(path.suffix in forbidden for path in stage.EXACT10_PATHS)
    assert not any(
        path.parts[:2] in {("data", "raw"), ("checkpoints",)}
        for path in stage.EXACT10_PATHS
    )
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.decode().strip()
    if head == stage.BASE_COMMIT:
        status = subprocess.run(
            ("git", "status", "--short", "--untracked-files=all"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode().splitlines()
        assert {line[3:] for line in status} == {
            path.as_posix() for path in stage.EXACT10_PATHS
        }
        assert all(line.startswith("?? ") for line in status)
    else:
        changed = subprocess.run(
            (
                "git",
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                "HEAD",
            ),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode().splitlines()
        assert set(changed) == {path.as_posix() for path in stage.EXACT10_PATHS}


def test_shared_hermetic_lifecycle_exact4(tmp_path: Path) -> None:
    report = exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=stage.BASE_COMMIT,
        formal_commit_subject=stage.FORMAL_COMMIT_SUBJECT,
        exact_paths=stage.EXACT10_PATHS,
    )
    assert report.cleanup_verified
    assert report.candidate_parent == stage.BASE_COMMIT
    assert report.candidate_subject == stage.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert (
        report.pre_commit.lifecycle,
        report.detached_candidate_post_commit.lifecycle,
        report.formal_main_post_commit_unpushed.lifecycle,
        report.formal_main_post_push.lifecycle,
    ) == (
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    )


def test_isolated_import_has_no_output_or_file_side_effects(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(ROOT / "src")
    before = tuple(tmp_path.iterdir())
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1",
        ),
        cwd=tmp_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""
    assert tuple(tmp_path.iterdir()) == before
