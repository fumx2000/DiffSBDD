from __future__ import annotations

import csv
import dataclasses
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1
    as stage,
)
from covalent_ext.covapie_hermetic_git_lifecycle_harness_v1 import (
    exercise_hermetic_git_lifecycle_matrix,
)


ROOT = Path(__file__).resolve().parents[1]


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


def test_formal_base_identity_and_lifecycle() -> None:
    shown = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%P%n%T%n%s", stage.BASE_COMMIT),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert shown.stdout.decode().splitlines() == [
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


def test_exact12_sources_are_immutable_base_reads(
    result: stage.BuildResult,
) -> None:
    assert len(stage.SOURCE_PATHS) == len(stage.FROZEN_BASE_SHA256) == 12
    assert len(result.source_rows) == 12
    for path, inventory in zip(stage.SOURCE_PATHS, result.source_rows):
        payload = subprocess.run(
            ("git", "show", f"{stage.BASE_COMMIT}:{path.as_posix()}"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout
        expected = stage.FROZEN_BASE_SHA256[path]
        assert hashlib.sha256(payload).hexdigest() == expected
        assert inventory == {
            **inventory,
            "source_path": path.as_posix(),
            "BASE_SHA256": expected,
            "Current11_coverage": "11/11",
            "verified": True,
        }
        assert inventory["source_row_count"] > 0
        assert inventory["fields_actually_used"]
        assert inventory["authority_class"]


def test_predecessor_state_is_frozen_and_phase_a_succeeds(
    result: stage.BuildResult,
) -> None:
    assert result.transaction_succeeded
    assert result.blocking_reasons == ()
    assert len(result.class_source_records) == 7
    assert len(result.class_template_rows) == 7
    assert len(result.sample_template_rows) == 11
    assert len(result.package_rows) == 18


def test_class_source_record_exact23_schema_and_types(
    result: stage.BuildResult,
) -> None:
    assert len(stage.CLASS_SOURCE_RECORD_FIELDS) == 23
    for index, record in enumerate(result.class_source_records):
        assert type(record) is dict
        assert tuple(record) == stage.CLASS_SOURCE_RECORD_FIELDS
        stage.validate_class_source_record(record)
        assert type(record["warhead_type_candidate_class_index_0based"]) is int
        assert record["warhead_type_candidate_class_index_0based"] == index
        assert type(record["selected_signature_radius"]) is int
        assert record["selected_signature_radius"] == 1
        assert type(record["Current11_match_count"]) is int
        assert type(record["Current11_unique_component_count"]) is int
        assert type(record["representative_sample_ids"]) is list
        assert type(record["representative_component_ids"]) is list
        for field in (
            "family_identity_evidence_complete",
            "rule_topology_evidence_complete",
            "assignment_support_complete",
            "class_identity_verified",
        ):
            assert type(record[field]) is bool and record[field] is True


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("warhead_type_candidate_class_index_0based", True, "bool_as_int"),
        ("selected_signature_radius", 1.0, "exact_type_invalid"),
        ("Current11_match_count", "2", "exact_type_invalid"),
        ("family_identity_evidence_complete", 1, "exact_type_invalid"),
        ("warhead_type_candidate_class_id", " ", "text_invalid"),
        ("canonical_local_graph_rule_sha256", "A" * 64, "SHA_invalid"),
    ),
)
def test_class_source_exact_types_fail_closed(
    result: stage.BuildResult, field: str, value: object, reason: str
) -> None:
    mutated = dict(result.class_source_records[0])
    mutated[field] = value
    with pytest.raises(ValueError, match=reason):
        stage.validate_class_source_record(mutated)


def test_class_source_missing_extra_and_string_subclass_fail_closed(
    result: stage.BuildResult,
) -> None:
    missing = dict(result.class_source_records[0])
    del missing["warhead_rule_id"]
    with pytest.raises(ValueError, match="field_missing"):
        stage.validate_class_source_record(missing)
    extra = dict(result.class_source_records[0], unexpected="x")
    with pytest.raises(ValueError, match="extra_field"):
        stage.validate_class_source_record(extra)

    class Text(str):
        pass

    subclass = dict(result.class_source_records[0])
    subclass["reaction_family_id"] = Text(subclass["reaction_family_id"])
    with pytest.raises(ValueError, match="exact_type_invalid"):
        stage.validate_class_source_record(subclass)


def test_representative_lists_are_sorted_unique_and_exact_coverage(
    result: stage.BuildResult,
) -> None:
    assignments = csv_rows(stage.base_bytes(ROOT, stage.ASSIGNMENT_AUTHORITY))
    for record in result.class_source_records:
        support = [
            row for row in assignments
            if row["warhead_type_candidate_class_id"]
            == record["warhead_type_candidate_class_id"]
        ]
        assert record["representative_sample_ids"] == sorted(
            row["sample_index_row_id"] for row in support
        )
        assert record["representative_component_ids"] == sorted(
            {row["ligand_comp_id"] for row in support}
        )
        assert len(record["representative_sample_ids"]) == record["Current11_match_count"]
        assert len(record["representative_component_ids"]) == record["Current11_unique_component_count"]


def test_representative_list_negative_paths(result: stage.BuildResult) -> None:
    record = result.class_source_records[0]
    unsorted = dict(record)
    unsorted["representative_sample_ids"] = list(
        reversed(record["representative_sample_ids"])
    )
    with pytest.raises(ValueError, match="unsorted"):
        stage.validate_class_source_record(unsorted)
    duplicated = dict(record)
    duplicated["representative_component_ids"] = [
        record["representative_component_ids"][0],
        record["representative_component_ids"][0],
    ]
    with pytest.raises(ValueError, match="duplicated"):
        stage.validate_class_source_record(duplicated)


def test_class_source_sha_is_canonical_deterministic_and_sensitive(
    result: stage.BuildResult,
) -> None:
    assert len(result.class_source_sha256) == len(set(result.class_source_sha256)) == 7
    for record, expected in zip(
        result.class_source_records, result.class_source_sha256
    ):
        assert stage.class_source_record_sha256(record) == expected
        assert stage.class_source_record_sha256(dict(reversed(tuple(record.items())))) == expected
        assert len(expected) == 64 and expected == expected.lower()
        mutated = dict(record)
        mutated["reaction_family_semantic_name"] += "_changed"
        assert stage.class_source_record_sha256(mutated) != expected


def test_exact11_assignment_sha_is_independently_reconstructed() -> None:
    assignments = csv_rows(stage.base_bytes(ROOT, stage.ASSIGNMENT_AUTHORITY))
    assert len(assignments) == 11
    assert len(stage.ASSIGNMENT_HASH_FIELDS) == 19
    assert len({row["sample_index_row_id"] for row in assignments}) == 11
    for row in assignments:
        hash_input = stage.assignment_hash_input(row)
        assert tuple(hash_input) == stage.ASSIGNMENT_HASH_FIELDS
        assert type(hash_input["warhead_type_candidate_class_index_0based"]) is int
        expected = hashlib.sha256(
            json.dumps(
                hash_input, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            ).encode()
        ).hexdigest()
        assert expected == row["assignment_record_sha256"]


def test_class_templates_are_exact19_blank_and_valid(
    result: stage.BuildResult,
) -> None:
    assert len(stage.CLASS_REVIEW_RECORD_FIELDS) == 19
    for source, source_sha, row in zip(
        result.class_source_records,
        result.class_source_sha256,
        result.class_template_rows,
    ):
        assert tuple(row) == stage.CLASS_REVIEW_RECORD_FIELDS
        assert review_unit(row) == "candidate_class"
        assert row["warhead_type_candidate_class_id"] == source["warhead_type_candidate_class_id"]
        assert row["source_class_record_sha256"] == source_sha
        assert row["reaction_family_identity_review_decision"] == "not_reviewed"
        assert row["warhead_rule_topology_review_decision"] == "not_reviewed"
        assert row["warhead_smarts_review_status"] == "not_materialized"
        assert row["candidate_warhead_smarts"] == ""
        assert_blank_review_metadata(row)


def test_sample_templates_are_exact13_blank_and_valid(
    result: stage.BuildResult,
) -> None:
    assert len(stage.SAMPLE_REVIEW_RECORD_FIELDS) == 13
    for row in result.sample_template_rows:
        assert tuple(row) == stage.SAMPLE_REVIEW_RECORD_FIELDS
        assert review_unit(row) == "sample_assignment"
        assert row["sample_assignment_review_decision"] == "not_reviewed"
        assert row["source_assignment_record_sha256"] == row["assignment_record_sha256"]
        assert_blank_review_metadata(row)


def review_unit(row: MappingForTest) -> str:
    return stage.review_gate.validate_review_record_schema(dict(row))


MappingForTest = dict[str, object]


def assert_blank_review_metadata(row: MappingForTest) -> None:
    assert row["reviewer_id"] == ""
    assert row["review_rationale"] == ""
    assert row["review_notes"] == ""
    assert row["review_record_sha256"] == ""


def test_template_hash_is_integrity_only_not_review_identity(
    result: stage.BuildResult,
) -> None:
    digests = {
        stage.unreviewed_template_payload_sha256(row)
        for row in (*result.class_template_rows, *result.sample_template_rows)
    }
    assert len(digests) == 18
    assert all(len(value) == 64 and value == value.lower() for value in digests)
    assert all(row["review_record_sha256"] == "" for row in result.class_template_rows)
    assert all(row["review_record_sha256"] == "" for row in result.sample_template_rows)


def test_package_index_exact18_ordering_and_source_json(
    result: stage.BuildResult,
) -> None:
    rows = result.package_rows
    assert [row["package_item_order_0based"] for row in rows] == list(range(18))
    assert [row["package_item_type"] for row in rows[:7]] == ["candidate_class"] * 7
    assert [row["package_item_type"] for row in rows[7:]] == ["sample_assignment"] * 11
    assert [row["package_item_id"] for row in rows[7:]] == sorted(
        row["package_item_id"] for row in rows[7:]
    )
    for row in rows:
        source = json.loads(row["source_record_json"])
        assert stage.canonical_json(source) == row["source_record_json"]
        assert hashlib.sha256(row["source_record_json"].encode()).hexdigest() == row["source_record_sha256"]
        assert row["review_record_sha256_populated"] is False
        assert row["human_review_execution_completed"] is False
        assert row["package_item_materialized"] is True
        assert row["verified"] is True


def test_package_readiness_split_is_exact(result: stage.BuildResult) -> None:
    for row in result.package_rows[:7]:
        assert row["family_identity_review_ready"] is True
        assert row["rule_topology_review_ready"] is True
        assert row["SMARTS_review_ready"] is False
        assert row["sample_assignment_review_ready"] is False
    for row in result.package_rows[7:]:
        assert row["family_identity_review_ready"] is False
        assert row["rule_topology_review_ready"] is False
        assert row["SMARTS_review_ready"] is False
        assert row["sample_assignment_review_ready"] is True


def test_failure_matrix_is_exact36_typed_unique_and_fail_closed(
    result: stage.BuildResult,
) -> None:
    assert len(stage.FAILURE_MUTATIONS) == len(result.failure_rows) == 36
    assert len({row["mutation_signature"] for row in result.failure_rows}) == 36
    baseline = stage.PackageScenario()
    for definition, row in zip(stage.FAILURE_MUTATIONS, result.failure_rows):
        case, field, value, expected = definition
        assert hasattr(baseline, field)
        assert type(value) is type(getattr(baseline, field))
        assert value != getattr(baseline, field)
        assert row["failure_case"] == case
        assert row["expected_reason"] == expected
        assert expected in row["observed_reasons"]
        assert row["expected_reason_verified"] is True
        assert row["fails_closed"] is True
        assert row["review_package_index_row_count"] == 0
        assert row["class_review_template_row_count"] == 0
        assert row["sample_review_template_row_count"] == 0
        assert row["role_proposal_generation_ready"] is False
        assert row["mask_materialization_ready"] is False
        assert row["model_integration_ready"] is False
        assert row["training_ready"] is False
        assert row["verified"] is True


def test_transaction_is_all_or_nothing(result: stage.BuildResult) -> None:
    tables = stage.transaction_tables(
        ("synthetic_blocker",),
        result.package_rows,
        result.class_template_rows,
        result.sample_template_rows,
    )
    assert tables == ((), (), ())
    assert stage.transaction_tables(
        (), result.package_rows, result.class_template_rows, result.sample_template_rows
    ) == (
        result.package_rows,
        result.class_template_rows,
        result.sample_template_rows,
    )


def test_manifest_truthfulness_and_closed_boundaries(
    payloads: dict[str, bytes],
) -> None:
    manifest = json.loads(payloads[stage.MANIFEST_FILE])
    assert manifest["source_count"] == 12
    assert manifest["class_source_record_fields"] == list(stage.CLASS_SOURCE_RECORD_FIELDS)
    assert manifest["class_source_record_count"] == 7
    assert manifest["class_source_record_sha_unique_count"] == 7
    assert manifest["class_review_template_count"] == 7
    assert manifest["sample_review_template_count"] == 11
    assert manifest["review_package_item_count"] == 18
    assert manifest["template_decision_not_reviewed_count"] == 18
    for field in (
        "template_reviewer_nonempty_count",
        "template_rationale_nonempty_count",
        "template_notes_nonempty_count",
        "template_SMARTS_nonempty_count",
        "template_review_record_sha_populated_count",
        "approved_reaction_family_available_count",
        "approved_warhead_rule_available_count",
        "approved_warhead_smarts_count",
        "human_gold_review_completed_count",
        "training_label_approved_count",
        "integrated_covalent_model_module_count",
    ):
        assert manifest[field] == 0 and type(manifest[field]) is int
    assert manifest["review_package_materialized"] is True
    assert manifest["ready_for_family_identity_review_execution"] is True
    assert manifest["ready_for_rule_topology_review_execution"] is True
    assert manifest["ready_for_sample_assignment_review_execution"] is True
    assert manifest["ready_for_human_review_execution"] is True
    for field in (
        "ready_for_SMARTS_review_execution",
        "ready_for_complete_human_review_execution",
        "human_review_execution_completed",
        "ready_for_role_proposal_generation",
        "ready_for_minimal_seed_proposal_generation",
        "ready_for_mask_materialization",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
        "role_annotation_materialized",
        "minimal_seed_materialized",
        "mask_materialized",
        "tensor_materialized",
        "model_changed",
        "training_used",
        "warhead_type_model_head_integrated",
        "warhead_type_loss_integrated",
    ):
        assert manifest[field] is False
    assert stage.MANIFEST_FILE not in manifest["output_sha256"]
    for name, expected in manifest["output_sha256"].items():
        assert hashlib.sha256(payloads[name]).hexdigest() == expected


def test_outputs_are_byte_deterministic_and_safe_text(
    payloads: dict[str, bytes],
) -> None:
    assert payloads == stage.build_evidence_payloads(ROOT)
    joined = b"".join(payloads.values())
    assert b"timestamp" not in joined.lower()
    assert str(ROOT).encode() not in joined
    assert b"codex" not in joined.lower()
    assert b"chatgpt" not in joined.lower()
    assert b"candidate_warhead_smarts,[^,]" not in joined


def test_materialized_files_match_builder(payloads: dict[str, bytes]) -> None:
    for name, expected in payloads.items():
        assert (ROOT / stage.OUTPUT_ROOT / name).read_bytes() == expected


def test_csv_headers_and_counts_are_exact(payloads: dict[str, bytes]) -> None:
    expectations = (
        (stage.SOURCE_FILE, stage.SOURCE_COLUMNS, 12),
        (stage.PACKAGE_FILE, stage.PACKAGE_COLUMNS, 18),
        (stage.CLASS_TEMPLATE_FILE, stage.CLASS_REVIEW_RECORD_FIELDS, 7),
        (stage.SAMPLE_TEMPLATE_FILE, stage.SAMPLE_REVIEW_RECORD_FIELDS, 11),
        (stage.FAILURE_FILE, stage.FAILURE_COLUMNS, 36),
    )
    for name, fields, count in expectations:
        reader = csv.DictReader(io.StringIO(payloads[name].decode()))
        assert tuple(reader.fieldnames or ()) == fields
        assert len(list(reader)) == count


def test_independent_checker_without_lifecycle() -> None:
    path = ROOT / stage.EXACT10_PATHS[2]
    spec = importlib.util.spec_from_file_location("review_package_checker", path)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    report = checker.check(ROOT, run_lifecycle_matrix=False)
    assert report["source_count"] == 12
    assert report["class_source_count"] == 7
    assert report["class_template_count"] == 7
    assert report["sample_template_count"] == 11
    assert report["package_count"] == 18
    assert report["failure_count"] == 36
    assert report["ready_for_training"] is False


def test_exact10_safe_unstaged_filesystem_contract() -> None:
    assert len(stage.EXACT10_PATHS) == len(set(stage.EXACT10_PATHS)) == 10
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    for relative in stage.EXACT10_PATHS:
        target = ROOT / relative
        assert target.is_file() and not target.is_symlink()
        mode = stat.S_IMODE(target.stat(follow_symlinks=False).st_mode)
        assert mode in {0o644, 0o664}
        assert mode & 0o111 == 0
        assert relative.suffix.lower() not in forbidden
        assert subprocess.run(
            ("git", "cat-file", "-e", f"{stage.BASE_COMMIT}:{relative.as_posix()}"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        ).returncode != 0
    assert subprocess.run(
        ("git", "diff", "--cached", "--name-only"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout == b""
    if stage.validate_execution_boundary_v1(ROOT) == "pre_commit":
        status = subprocess.run(
            ("git", "status", "--short", "--untracked-files=all"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode().splitlines()
        assert set(status) == {f"?? {path.as_posix()}" for path in stage.EXACT10_PATHS}


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


def test_isolated_import_has_no_output_or_side_effects(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext."
            "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_"
            "packages_v1",
        ),
        cwd=tmp_path,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""
    assert tuple(tmp_path.iterdir()) == ()
