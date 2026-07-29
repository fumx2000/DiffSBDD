from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import rdkit

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_packages_v1
    as package,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle


ROOT = Path(__file__).resolve().parents[1]
PYTEST_VERSION = "9.1.0"
RDKIT_VERSION = "2022.03.2"
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
}


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode())))


@pytest.fixture(scope="module")
def payloads():
    return package.load_frozen_sources(ROOT)


@pytest.fixture(scope="module")
def result():
    value = package.build_result(ROOT)
    assert value.transaction_succeeded and not value.blocking_reasons
    return value


def test_formal_python_pytest_rdkit_environment():
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == (3, 10, 4)
    assert pytest.__version__ == PYTEST_VERSION
    assert rdkit.__version__ == RDKIT_VERSION


def test_base_identity_and_current_lifecycle():
    identity = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%P%n%T%n%s", package.BASE_COMMIT),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode().splitlines()
    assert identity == [
        package.BASE_COMMIT, package.BASE_PARENT, package.BASE_TREE,
        package.BASE_SUBJECT,
    ]
    assert package.validate_execution_boundary_v1(ROOT) in lifecycle.LIFECYCLES


def test_exact15_are_git_show_sources_with_frozen_sha(payloads):
    assert len(payloads) == len(package.FROZEN_BASE_SHA256) == 15
    for path, expected in package.FROZEN_BASE_SHA256.items():
        assert hashlib.sha256(payloads[path]).hexdigest() == expected
        assert subprocess.run(
            ("git", "cat-file", "-e", f"{package.BASE_COMMIT}:{path.as_posix()}"),
            cwd=ROOT, check=False,
        ).returncode == 0


def test_source_inventory_exact15(result):
    assert tuple(result.source_rows[0]) == package.SOURCE_COLUMNS
    assert len(result.source_rows) == 15
    assert all(row["verified"] is True for row in result.source_rows)


def test_predecessor_counts_statuses_and_closed_authority(payloads):
    proposals = _rows(payloads[package.PROPOSALS])
    enumerations = _rows(payloads[package.ENUMERATIONS])
    readiness = _rows(payloads[package.READINESS])
    assert (len(proposals), len(enumerations), len(readiness)) == (11, 200, 11)
    assert {row["proposal_status"] for row in proposals} == {"ambiguous_candidate"}
    assert sum(row["candidate_admitted"] == "true" for row in enumerations) == 185
    assert all(row["ready_for_proposal_human_review"] == "true" for row in readiness)
    assert all(
        row["complete_warhead_atom_set_authority_available"] == "false"
        and row["exact_one_attachment_boundary_authority_available"] == "false"
        for row in readiness
    )


def test_predecessor_record_sha_exact11_and_exact200(payloads):
    proposals = [package.typed_proposal(row) for row in _rows(payloads[package.PROPOSALS])]
    candidates = [
        package.typed_enumeration(row) for row in _rows(payloads[package.ENUMERATIONS])
    ]
    assert len(proposals) == 11 and all(
        row["proposal_record_sha256"] == package.proposal_record_sha256(row)
        for row in proposals
    )
    assert len(candidates) == 200 and all(
        row["bridge_candidate_record_sha256"]
        == package.bridge_candidate_record_sha256(row) for row in candidates
    )


def test_candidate_set_determinism_ordered_subset_and_unique(result):
    second = package.build_result(ROOT)
    assert result.candidate_set_sha256s == second.candidate_set_sha256s
    assert len(result.candidate_set_sha256s) == len(set(result.candidate_set_sha256s)) == 11
    grouped = {}
    for row in result.option_rows:
        grouped.setdefault(row["sample_index_row_id"], []).append(row)
    assert sum(sum(row["review_eligible"] for row in rows) for rows in grouped.values()) == 185
    assert all(
        [row["source_bridge_candidate_index_0based"] for row in rows]
        == list(range(len(rows))) for rows in grouped.values()
    )


def test_exact200_option_schema_types_order_and_sha(result):
    assert len(result.option_rows) == 200
    for index, row in enumerate(result.option_rows):
        assert tuple(row) == package.OPTION_FIELDS
        assert row["package_item_order_0based"] == index
        package.validate_option_record(row)
    assert sum(row["review_eligible"] for row in result.option_rows) == 185
    assert sum(not row["review_eligible"] for row in result.option_rows) == 15


def test_option_boundary_endpoint_and_extra_atom_difference(result):
    for row in result.option_rows:
        left, right, order = row["boundary_bond_id"].split("|")
        warhead = set(row["warhead_side_atom_ids"])
        assert (left in warhead) != (right in warhead)
        assert row["warhead_attachment_atom_id"] == (left if left in warhead else right)
        assert row["nonwarhead_boundary_atom_id"] == (right if left in warhead else left)
        assert row["boundary_bond_order"] == order
        assert row["warhead_extra_atom_ids_beyond_local_center"] == sorted(
            warhead - set(row["local_reaction_center_atom_ids"]),
            key=lambda value: value.encode(),
        )


def test_each_option_boundary_is_exact_parent_authority_bond(result, payloads):
    parent_bonds = _rows(payloads[package.PARENT_BONDS])
    for option in result.option_rows:
        left, right, order = option["boundary_bond_id"].split("|")
        matches = [
            row for row in parent_bonds
            if row["ligand_comp_id"] == option["ligand_comp_id"]
            and {row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]}
            == {left, right}
            and row["normalized_bond_order"] == order
        ]
        assert len(matches) == 1


def test_option_exact_type_contract_rejects_bool(result):
    row = dict(result.option_rows[0])
    row["package_item_order_0based"] = True
    with pytest.raises(ValueError, match="exact_int"):
        package.validate_option_record(row)


def test_review_schema_exact26_and_typed_optional_index(result):
    assert len(package.REVIEW_RECORD_FIELDS) == 26
    row = result.template_rows[0]
    assert tuple(row) == package.REVIEW_RECORD_FIELDS
    package.validate_review_record(row)
    payload = package._csv_bytes(package.REVIEW_RECORD_FIELDS, [row])
    parsed = package.parse_review_record_csv(_rows(payload)[0])
    assert parsed["selected_bridge_candidate_index_0based"] is None
    bad = dict(_rows(payload)[0])
    bad["selected_bridge_candidate_index_0based"] = "01"
    with pytest.raises(ValueError, match="canonical_nonnegative"):
        package.parse_review_record_csv(bad)


def _completed(record):
    record["reviewer_id"] = "human-reviewer-01"
    record["review_rationale"] = "Evidence was inspected by the named reviewer."
    record["review_record_sha256"] = package.review_record_sha256(record)
    return record


def test_not_reviewed_blank_dependency(result):
    for row in result.template_rows:
        package.validate_review_record(row)
        assert row["review_record_sha256"] == ""
        assert package.unreviewed_template_payload_sha256(row) != row["review_record_sha256"]


def test_select_admitted_candidate_success_and_hash_self_exclusion(result):
    option = next(row for row in result.option_rows if row["review_eligible"])
    record = dict(next(
        row for row in result.template_rows
        if row["sample_index_row_id"] == option["sample_index_row_id"]
    ))
    record.update({
        "review_decision": "select_admitted_candidate",
        "selected_bridge_candidate_index_0based":
            option["source_bridge_candidate_index_0based"],
        "selected_bridge_candidate_record_sha256":
            option["source_bridge_candidate_record_sha256"],
        "reviewed_warhead_atom_ids": option["warhead_side_atom_ids"],
        "reviewed_warhead_attachment_atom_id": option["warhead_attachment_atom_id"],
        "reviewed_nonwarhead_boundary_atom_id": option["nonwarhead_boundary_atom_id"],
        "reviewed_attachment_boundary_bond_order": option["boundary_bond_order"],
        "reviewed_boundary_bond_id": option["boundary_bond_id"],
    })
    _completed(record)
    package.validate_review_record(record, options=result.option_rows)
    digest = record["review_record_sha256"]
    record["review_record_sha256"] = ""
    assert package.review_record_sha256(record) == digest


def test_select_blocked_candidate_and_identity_mismatch_rejected(result):
    blocked = next(row for row in result.option_rows if not row["review_eligible"])
    record = dict(next(
        row for row in result.template_rows
        if row["sample_index_row_id"] == blocked["sample_index_row_id"]
    ))
    record.update({
        "review_decision": "select_admitted_candidate",
        "selected_bridge_candidate_index_0based":
            blocked["source_bridge_candidate_index_0based"],
        "selected_bridge_candidate_record_sha256":
            blocked["source_bridge_candidate_record_sha256"],
        "reviewed_warhead_atom_ids": blocked["warhead_side_atom_ids"],
        "reviewed_warhead_attachment_atom_id": blocked["warhead_attachment_atom_id"],
        "reviewed_nonwarhead_boundary_atom_id": blocked["nonwarhead_boundary_atom_id"],
        "reviewed_attachment_boundary_bond_order": blocked["boundary_bond_order"],
        "reviewed_boundary_bond_id": blocked["boundary_bond_id"],
    })
    _completed(record)
    with pytest.raises(ValueError, match="not_unique_review_eligible"):
        package.validate_review_record(record, options=result.option_rows)
    record["selected_bridge_candidate_record_sha256"] = "0" * 64
    record["review_record_sha256"] = package.review_record_sha256(record)
    with pytest.raises(ValueError, match="not_unique_review_eligible"):
        package.validate_review_record(record, options=result.option_rows)


def _synthetic_revise(result):
    record = dict(result.template_rows[0])
    record.update({
        "review_decision": "revise_atom_set_and_boundary",
        "reviewed_warhead_atom_ids": ["A", "B"],
        "reviewed_warhead_attachment_atom_id": "B",
        "reviewed_nonwarhead_boundary_atom_id": "C",
        "reviewed_attachment_boundary_bond_order": "single",
        "reviewed_boundary_bond_id": "B|C|single",
    })
    proposal = {
        "local_reaction_center_atom_ids": ["A"],
        "required_leaving_group_atom_ids": ["B"],
    }
    return _completed(record), proposal


def test_revise_graph_invariant_synthetic_success(result):
    record, proposal = _synthetic_revise(result)
    package.validate_review_record(
        record, proposal=proposal, parent_atom_ids=["A", "B", "C"],
        parent_bonds=[("A", "B", "double"), ("B", "C", "single")],
    )


@pytest.mark.parametrize(
    ("change", "reason"),
    (
        ({"reviewed_warhead_atom_ids": ["A", "C"]}, "missing_required"),
        ({"reviewed_warhead_atom_ids": ["B"]}, "missing_local"),
        ({"reviewed_warhead_atom_ids": ["A", "B", "D"]}, "disconnected"),
    ),
)
def test_revise_missing_or_disconnected_rejected(result, change, reason):
    record, proposal = _synthetic_revise(result)
    record.update(change)
    record["review_record_sha256"] = package.review_record_sha256(record)
    atoms = ["A", "B", "C", "D"]
    bonds = [("A", "B", "double"), ("B", "C", "single")]
    with pytest.raises(ValueError, match=reason):
        package.validate_review_record(
            record, proposal=proposal, parent_atom_ids=atoms, parent_bonds=bonds,
        )


def test_revise_non_exact_one_boundary_rejected(result):
    record, proposal = _synthetic_revise(result)
    with pytest.raises(ValueError, match="not_exact_one"):
        package.validate_review_record(
            record, proposal=proposal, parent_atom_ids=["A", "B", "C", "D"],
            parent_bonds=[
                ("A", "B", "double"), ("B", "C", "single"),
                ("A", "D", "single"),
            ],
        )


def test_quarantine_dependency_synthetic(result):
    record = dict(result.template_rows[0])
    record["review_decision"] = "quarantine"
    _completed(record)
    package.validate_review_record(record)
    record["reviewed_warhead_atom_ids"] = ["A"]
    record["review_record_sha256"] = package.review_record_sha256(record)
    with pytest.raises(ValueError, match="quarantine_dependency"):
        package.validate_review_record(record)


@pytest.mark.parametrize("reviewer", ["codex", " ChatGPT ", "OPENAI", "automation", "auto", "system", "model"])
def test_forbidden_reviewer_rejected(result, reviewer):
    record = dict(result.template_rows[0])
    record.update({
        "review_decision": "quarantine", "reviewer_id": reviewer,
        "review_rationale": "Human evidence rationale.",
    })
    record["review_record_sha256"] = package.review_record_sha256(record)
    with pytest.raises(ValueError, match="forbidden_reviewer"):
        package.validate_review_record(record)


def test_meaningful_text_required(result):
    record = dict(result.template_rows[0])
    record.update({
        "review_decision": "quarantine", "reviewer_id": "human",
        "review_rationale": "   ",
    })
    record["review_record_sha256"] = package.review_record_sha256(record)
    with pytest.raises(ValueError, match="rationale_not_meaningful"):
        package.validate_review_record(record)


def test_exact11_blank_templates_no_human_review(result):
    assert len(result.template_rows) == 11
    assert all(row["review_decision"] == "not_reviewed" for row in result.template_rows)
    assert not any(
        row["reviewer_id"] or row["review_rationale"] or row["review_notes"]
        or row["review_record_sha256"] or row["reviewed_warhead_atom_ids"]
        for row in result.template_rows
    )


def test_exact11_package_index_contiguous_spans_and_closed_downstream(result):
    assert len(result.index_rows) == 11
    cursor = 0
    for order, row in enumerate(result.index_rows):
        assert row["package_item_order_0based"] == order
        assert row["candidate_option_row_start_0based"] == cursor
        cursor = row["candidate_option_row_end_exclusive"]
        assert cursor - row["candidate_option_row_start_0based"] == row["total_candidate_count"]
        assert row["ready_for_human_review"] is True
        assert row["human_review_completed"] is False
        assert row["complete_warhead_atom_set_authority_available"] is False
        assert row["exact_one_attachment_boundary_authority_available"] is False
        assert row["ready_for_candidate_warhead_smarts_materialization"] is False
        assert row["ready_for_role_proposal_generation"] is False
    assert cursor == 200


def test_exact38_typed_unique_fail_closed_failure_matrix(result):
    assert len(package.FAILURE_MUTATIONS) == len(result.failure_rows) == 38
    assert len({row["mutation_signature"] for row in result.failure_rows}) == 38
    assert all(
        row["expected_reason_verified"] and row["fails_closed"]
        and row["option_row_count"] == row["template_row_count"]
        == row["package_index_row_count"] == 0
        and not row["human_review_completed"]
        and not row["complete_warhead_atom_set_authority_available"]
        and not row["SMARTS_ready"] and not row["role_ready"]
        and not row["mask_ready"] and not row["model_ready"]
        and not row["training_ready"]
        for row in result.failure_rows
    )
    baseline = package.PackageScenario()
    for _, field, value, _ in package.FAILURE_MUTATIONS:
        assert type(getattr(baseline, field)) is type(value)
        assert getattr(baseline, field) != value
        assert package.transaction_tables(replace(baseline, **{field: value})) == (
            (), (), (),
        )


def test_manifest_truth_and_five_module_boundary():
    manifest = json.loads((ROOT / package.OUTPUT_ROOT / package.MANIFEST_FILE).read_bytes())
    assert manifest["transaction_succeeded"] is True
    assert manifest["candidate_set_count"] == manifest["candidate_set_sha_unique_count"] == 11
    assert manifest["package_option_record_count"] == 200
    assert manifest["review_eligible_option_count"] == 185
    assert manifest["review_ineligible_option_count"] == 15
    assert manifest["review_template_count"] == manifest["package_index_count"] == 11
    assert manifest["warhead_boundary_human_review_completed_count"] == 0
    assert manifest["complete_warhead_atom_set_authority_available_count"] == 0
    assert manifest["exact_one_attachment_boundary_authority_available_count"] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False
    assert package.MANIFEST_FILE not in manifest["output_sha256"]
    text = json.dumps(manifest)
    assert "/cpfs" not in text and "timestamp" not in text.casefold()


def test_transaction_failure_emits_three_core_headers_only(monkeypatch):
    scenario = replace(package.PackageScenario(), base_source_present=False)
    assert package.transaction_tables(scenario) == ((), (), ())


def test_materialization_byte_determinism():
    first = package.build_evidence_payloads(ROOT)
    second = package.build_evidence_payloads(ROOT)
    assert first == second
    assert set(first) == set(package.OUTPUT_FILES)


def test_isolated_import_silent_and_side_effect_free(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    code = (
        "import covalent_ext."
        "covapie_current11_warhead_atom_set_and_attachment_boundary_"
        "review_packages_v1"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        (sys.executable, "-B", "-c", code), cwd=tmp_path, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert before == after


def test_exact10_filesystem_safety():
    assert len(package.EXACT10_PATHS) == len(set(package.EXACT10_PATHS)) == 10
    for relative in package.EXACT10_PATHS:
        path = ROOT / relative
        assert path.is_file() and not path.is_symlink()
        assert stat.S_IMODE(path.stat(follow_symlinks=False).st_mode) in {0o644, 0o664}
        assert path.stat().st_size < 5 * 1024 * 1024
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES


def test_shared_hermetic_lifecycle_exact4_and_cleanup(tmp_path):
    workspace = tmp_path / "lifecycle"
    workspace.mkdir()
    before = subprocess.run(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT, workspace, base_commit=package.BASE_COMMIT,
        formal_commit_subject=package.FORMAL_COMMIT_SUBJECT,
        exact_paths=package.EXACT10_PATHS,
    )
    after = subprocess.run(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout
    states = (
        report.pre_commit, report.detached_candidate_post_commit,
        report.formal_main_post_commit_unpushed, report.formal_main_post_push,
    )
    assert tuple(state.lifecycle for state in states) == lifecycle.LIFECYCLES
    assert report.candidate_parent == package.BASE_COMMIT
    assert report.candidate_subject == package.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert before == after and tuple(workspace.iterdir()) == ()
