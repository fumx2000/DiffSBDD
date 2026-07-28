"""Tests for the CovaPIE Cys-SG registry design v1."""

from __future__ import annotations

import csv
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1
    as design,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle  # noqa: E402

CHECKER_PATH = (
    ROOT / "scripts/"
    "check_covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
)
spec = importlib.util.spec_from_file_location("cys_sg_design_checker", CHECKER_PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

NESTED_ENV = "COVAPIE_CYS_SG_REGISTRY_DESIGN_NESTED_LIFECYCLE"


def csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def test_fixed_interpreter_contract() -> None:
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert pytest.__version__ == "9.1.0"


def test_formal_base_identity_and_lifecycle() -> None:
    shown = subprocess.run(
        (
            "git", "show", "-s", "--format=%H%n%P%n%T%n%s",
            design.BASE_COMMIT,
        ),
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=False, check=True,
    ).stdout.decode().splitlines()
    assert shown == [
        design.BASE_COMMIT, design.BASE_PARENT, design.BASE_TREE,
        design.BASE_SUBJECT,
    ]
    production_state = design.validate_execution_boundary_v1(ROOT)
    checker_state = checker.validate_execution_boundary_independent(ROOT)
    assert production_state == checker_state
    assert production_state in lifecycle.LIFECYCLES


def test_all_21_sources_are_read_from_base_and_sha_frozen() -> None:
    payloads = design.load_frozen_sources(ROOT)
    assert len(payloads) == 21
    assert tuple(payloads) == tuple(design.FROZEN_BASE_SHA256)
    for path, expected in design.FROZEN_BASE_SHA256.items():
        assert hashlib.sha256(payloads[path]).hexdigest() == expected
        direct = subprocess.run(
            ("git", "show", f"{design.BASE_COMMIT}:{path.as_posix()}"),
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False, check=True,
        ).stdout
        assert direct == payloads[path]


def test_source_inventory_reports_rows_coverage_fields_and_authority() -> None:
    result = design.build_design_result(ROOT)
    assert len(result.source_rows) == 21
    assert all(row["BASE_SHA256"] for row in result.source_rows)
    assert all(int(row["source_row_count"]) > 0 for row in result.source_rows)
    assert all(row["Current11_coverage"] for row in result.source_rows)
    assert all(row["fields_actually_used"] for row in result.source_rows)
    assert all(row["authority_class"] for row in result.source_rows)
    assert all(row["verified"] is True for row in result.source_rows)


def test_current11_reaction_center_evidence_is_exact() -> None:
    result = design.build_design_result(ROOT)
    assert len(result.design_rows) == 11
    assert len({row["sample_index_row_id"] for row in result.design_rows}) == 11
    assert all(row["target_residue_name"] == "CYS" for row in result.design_rows)
    assert all(
        row["target_residue_atom_name"] == "SG" for row in result.design_rows
    )
    assert all(row["ligand_reactive_atom_name"] for row in result.design_rows)
    assert all(row["ligand_reactive_atom_element"] == "C" for row in result.design_rows)
    assert all(
        len(row["component_parent_graph_sha256"]) == 64
        and len(row["observed_graph_sha256"]) == 64
        for row in result.design_rows
    )


def test_zya_f1_is_the_only_verified_missing_parent_atom() -> None:
    result = design.build_design_result(ROOT)
    missing = [
        row for row in result.design_rows
        if row["verified_missing_parent_atom_ids"]
    ]
    assert len(missing) == 1
    assert missing[0]["ligand_comp_id"] == "ZYA"
    assert missing[0]["verified_missing_parent_atom_ids"] == "F1"
    assert missing[0]["leaving_group_atom_ids"] == "F1"
    assert missing[0]["reaction_delta_class"] == "covalent_leaving_group_loss"


def test_radius_0_1_2_signatures_are_deterministic_under_input_reversal() -> None:
    payloads = design.load_frozen_sources(ROOT)
    samples, evidence, mapping, bonds, _, parent_atoms = design._validate_phase_a(
        payloads
    )
    for sample in samples:
        sid = sample["sample_index_row_id"]
        reactive = next(
            row for row in mapping[sid] if row["reactive_ligand_atom"] == "true"
        )
        atom_map = parent_atoms[sample["ligand_comp_id"]]
        reverse_atoms = dict(reversed(tuple(atom_map.items())))
        reverse_bonds = list(reversed(bonds[sid]))
        retained = {row["parent_ccd_atom_id"] for row in mapping[sid]}
        delta_row = evidence[sid]
        leaving = set(design._split_ids(delta_row["leaving_group_atom_ids"]))
        delta = design._reaction_delta(delta_row)
        for radius in (0, 1, 2):
            first = design.canonical_local_signature(
                center=reactive["parent_ccd_atom_id"], atoms=atom_map,
                bonds=bonds[sid], retained=retained, leaving_groups=leaving,
                reaction_delta_class=delta, radius=radius,
            )
            second = design.canonical_local_signature(
                center=reactive["parent_ccd_atom_id"], atoms=reverse_atoms,
                bonds=reverse_bonds, retained=set(reversed(sorted(retained))),
                leaving_groups=set(reversed(sorted(leaving))),
                reaction_delta_class=delta, radius=radius,
            )
            assert design.canonical_json(first[0]) == design.canonical_json(second[0])
            assert design.canonical_json(first[1]) == design.canonical_json(second[1])


def test_same_component_repeats_have_identical_signatures() -> None:
    rows = design.build_design_result(ROOT).design_rows
    jug = [row for row in rows if row["ligand_comp_id"] == "JUG"]
    assert len(jug) == 3
    for radius in (0, 1, 2):
        assert len({
            row[f"radius_{radius}_signature_sha256"] for row in jug
        }) == 1


def test_radius_1_is_minimal_and_radius_2_adds_no_rule_group() -> None:
    result = design.build_design_result(ROOT)
    assert result.radius_signature_unique_counts == {0: 7, 1: 9, 2: 9}
    assert result.radius_rule_projection_unique_counts == {0: 2, 1: 7, 2: 7}
    assert result.selected_radius == 1


def test_grouping_is_not_component_or_pdb_hard_coding() -> None:
    result = design.build_design_result(ROOT)
    assert len(result.family_rows) == len(result.rule_rows) == 7
    shared = [
        row for row in result.rule_rows
        if row["Current11_unique_component_count"] == 2
    ]
    assert len(shared) == 2
    component_ids = {row["ligand_comp_id"] for row in result.design_rows}
    pdb_ids = {row["pdb_id"] for row in result.design_rows}
    semantic_values = {
        row["reaction_family_semantic_name"] for row in result.family_rows
    } | {
        row["warhead_type_semantic_name"] for row in result.rule_rows
    }
    assert not any(
        token in value
        for value in semantic_values
        for token in component_ids | pdb_ids
    )


def test_family_and_rule_semantics_are_long_names_and_exact_graph_authority() -> None:
    result = design.build_design_result(ROOT)
    for family in result.family_rows:
        assert family["reaction_family_semantic_name"].startswith(
            "CYS_SG_single_bond_formation__"
        )
        assert family["mechanism_claim_status"] == (
            "topology_defined_mechanism_not_claimed"
        )
        parsed = json.loads(family["canonical_reaction_family_signature_json"])
        assert parsed["target_condition"]["residue"] == "CYS"
        assert family["candidate_assignment_ready"] is True
        assert family["approved"] is False
    for rule in result.rule_rows:
        assert rule["rule_kind"] == "canonical_local_graph_exact_match_v1"
        assert rule["approved_warhead_smarts"] == ""
        assert rule["SMARTS_status"] == "not_materialized_in_design_stage"
        assert rule["candidate_rule_assignment_ready"] is True
        assert rule["approved"] is False


def test_current11_candidate_assignments_are_exact_one_but_not_labels() -> None:
    rows = design.build_design_result(ROOT).design_rows
    assert len(rows) == 11
    for row in rows:
        assert row["family_candidate_exact_one"] is True
        assert row["warhead_rule_candidate_exact_one"] is True
        assert row["rule_matches_parent_graph"] is True
        assert row["rule_consistent_with_observed_delta"] is True
        assert row["reaction_family_label_available"] is False
        assert row["approved_warhead_rule_available"] is False
        assert row["human_gold_review_completed"] is False


def test_all_successor_readiness_interfaces_remain_closed() -> None:
    rows = design.build_design_result(ROOT).design_rows
    fields = (
        "ready_for_role_proposal_generation",
        "ready_for_minimal_seed_proposal_generation",
        "ready_for_mask_materialization", "ready_for_tensorization",
        "ready_for_model_integration", "ready_for_training",
    )
    assert all(not row[field] for row in rows for field in fields)


def test_mechanism_is_not_inferred_from_topology() -> None:
    result = design.build_design_result(ROOT)
    forbidden = ("Michael", "SN2", "ring_opening", "acyl_substitution")
    assert all(
        not any(term in row["reaction_family_semantic_name"] for term in forbidden)
        for row in result.family_rows
    )
    assert {
        row["mechanism_claim_status"] for row in result.family_rows
    } == {"topology_defined_mechanism_not_claimed"}


def test_transaction_failure_is_header_only_for_all_three_core_tables() -> None:
    rows = ({"x": 1},)
    assert design.transaction_tables(False, True, rows, rows, rows) == ((), (), ())
    assert design.transaction_tables(True, False, rows, rows, rows) == ((), (), ())
    assert design.transaction_tables(True, True, rows, rows, rows) == (
        rows, rows, rows,
    )


def test_failure_matrix_has_all_25_exact_typed_mutations() -> None:
    rows = design.build_failure_rows()
    assert len(rows) == 25
    assert len({row["failure_case"] for row in rows}) == 25
    assert len({row["mutation_signature"] for row in rows}) == 25
    for row in rows:
        signature = json.loads(row["mutation_signature"])
        assert signature["dataclass"] == "DesignScenario"
        assert signature["field"] == row["mutated_fields"]
        assert row["expected_reasons_verified"] is True
        assert row["fails_closed"] is True
        assert row["ready_for_training"] is False


def test_manifest_separates_candidate_labels_from_model_head_and_loss() -> None:
    payloads = design.build_evidence_payloads(ROOT)
    manifest = json.loads(payloads[design.MANIFEST_FILE])
    assert manifest["warhead_type_auxiliary_label_contract_designed"] is True
    assert manifest["warhead_type_candidate_class_count"] == 7
    assert manifest["warhead_type_model_head_integrated"] is False
    assert manifest["warhead_type_loss_integrated"] is False
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["ready_for_training"] is False


def test_builder_is_byte_deterministic_and_matches_materialization() -> None:
    first = design.build_evidence_payloads(ROOT)
    second = design.build_evidence_payloads(ROOT)
    assert first == second
    assert tuple(first) == design.OUTPUT_FILES
    for name, payload in first.items():
        assert payload == (ROOT / design.OUTPUT_ROOT / name).read_bytes()
    manifest = json.loads(first[design.MANIFEST_FILE])
    for name, expected in manifest["output_sha256"].items():
        assert hashlib.sha256(first[name]).hexdigest() == expected


def test_manifest_has_no_timestamp_absolute_path_or_self_sha() -> None:
    payload = (ROOT / design.OUTPUT_ROOT / design.MANIFEST_FILE).read_bytes()
    manifest = json.loads(payload)
    assert "timestamp" not in payload.decode().lower()
    assert str(ROOT) not in payload.decode()
    assert design.MANIFEST_FILE not in manifest["output_sha256"]
    assert manifest["recommended_next_step"] == (
        "materialize_covapie_current11_cys_sg_reaction_family_and_"
        "warhead_rule_assignments_v1"
    )


def test_independent_checker_reconstructs_sources_signatures_and_groups() -> None:
    result = checker.check(ROOT)
    assert result == {
        "lifecycle": design.validate_execution_boundary_v1(ROOT),
        "sources": 21, "samples": 11, "families": 7, "rules": 7,
        "failures": 25, "selected_radius": 1,
    }


@pytest.fixture
def assignment_identity_inputs(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = []
    real_validator = checker.validate_materialized_assignment_identity

    def capture(*arguments) -> None:
        captured.append(copy.deepcopy(arguments))

    monkeypatch.setattr(
        checker, "validate_materialized_assignment_identity", capture
    )
    checker.check(ROOT)
    monkeypatch.setattr(
        checker, "validate_materialized_assignment_identity", real_validator
    )
    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    (
        (
            "swap_assigned_rule_ids",
            "assigned_rule_id_does_not_match_reconstructed_digest",
        ),
        (
            "swap_assigned_family_ids",
            "assigned_family_id_does_not_match_reconstructed_family",
        ),
        (
            "change_assigned_rule_semantic_name",
            "assigned_rule_semantic_name_mismatch",
        ),
        (
            "change_assigned_family_semantic_name",
            "assigned_family_semantic_name_mismatch",
        ),
        ("change_rule_registry_sha", "rule_registry_JSON_SHA_mismatch"),
        ("change_rule_json_only", "rule_registry_JSON_SHA_mismatch"),
        ("change_rule_family_link", "rule_family_link_mismatch"),
        ("change_family_json_only", "family_registry_JSON_SHA_mismatch"),
        ("change_rule_match_count", "rule_assignment_count_mismatch"),
        ("change_family_component_count", "family_assignment_count_mismatch"),
        ("delete_rule", "rule_candidate_absent"),
        ("duplicate_rule_digest", "rule_candidate_ambiguous"),
    ),
)
def test_assignment_identity_mutations_fail_closed(
    assignment_identity_inputs,
    mutation: str,
    expected_reason: str,
) -> None:
    (
        samples,
        reconstructed,
        design_rows,
        rule_rows,
        family_rows,
        manifest,
    ) = copy.deepcopy(assignment_identity_inputs)

    def different_design_indexes(field: str) -> tuple[int, int]:
        for left in range(len(design_rows)):
            for right in range(left + 1, len(design_rows)):
                if design_rows[left][field] != design_rows[right][field]:
                    return left, right
        raise AssertionError("test_fixture_has_no_distinct_assignment_groups")

    if mutation == "swap_assigned_rule_ids":
        left, right = different_design_indexes("candidate_warhead_rule_id")
        design_rows[left]["candidate_warhead_rule_id"], design_rows[right][
            "candidate_warhead_rule_id"
        ] = (
            design_rows[right]["candidate_warhead_rule_id"],
            design_rows[left]["candidate_warhead_rule_id"],
        )
    elif mutation == "swap_assigned_family_ids":
        left, right = different_design_indexes("candidate_reaction_family_id")
        design_rows[left]["candidate_reaction_family_id"], design_rows[right][
            "candidate_reaction_family_id"
        ] = (
            design_rows[right]["candidate_reaction_family_id"],
            design_rows[left]["candidate_reaction_family_id"],
        )
    elif mutation == "change_assigned_rule_semantic_name":
        design_rows[0]["candidate_warhead_type_semantic_name"] += "_corrupt"
    elif mutation == "change_assigned_family_semantic_name":
        design_rows[0]["candidate_reaction_family_semantic_name"] += "_corrupt"
    elif mutation == "change_rule_registry_sha":
        rule_rows[0]["canonical_local_graph_rule_sha256"] = "0" * 64
    elif mutation == "change_rule_json_only":
        parsed = json.loads(rule_rows[0]["canonical_local_graph_rule_json"])
        parsed["center_atom"]["element"] = "N"
        rule_rows[0]["canonical_local_graph_rule_json"] = checker.canonical(parsed)
    elif mutation == "change_rule_family_link":
        alternative = next(
            row["reaction_family_id"] for row in family_rows
            if row["reaction_family_id"] != rule_rows[0]["reaction_family_id"]
        )
        rule_rows[0]["reaction_family_id"] = alternative
    elif mutation == "change_family_json_only":
        parsed = json.loads(
            family_rows[0]["canonical_reaction_family_signature_json"]
        )
        parsed["selected_signature_radius"] = 2
        family_rows[0]["canonical_reaction_family_signature_json"] = (
            checker.canonical(parsed)
        )
    elif mutation == "change_rule_match_count":
        rule_rows[0]["Current11_match_count"] = str(
            int(rule_rows[0]["Current11_match_count"]) + 1
        )
    elif mutation == "change_family_component_count":
        family_rows[0]["unique_component_count"] = str(
            int(family_rows[0]["unique_component_count"]) + 1
        )
    elif mutation == "delete_rule":
        target_sample = samples[0]["sample_index_row_id"]
        target_sha = reconstructed[target_sample]["rule_sha256"]
        rule_rows[:] = [
            row for row in rule_rows
            if row["canonical_local_graph_rule_sha256"] != target_sha
        ]
    elif mutation == "duplicate_rule_digest":
        target_sample = samples[0]["sample_index_row_id"]
        target_sha = reconstructed[target_sample]["rule_sha256"]
        source_index = next(
            index for index, row in enumerate(rule_rows)
            if row["canonical_local_graph_rule_sha256"] == target_sha
        )
        replacement_index = next(
            index for index, row in enumerate(rule_rows)
            if row["canonical_local_graph_rule_sha256"] != target_sha
        )
        rule_rows[replacement_index] = copy.deepcopy(rule_rows[source_index])
    else:
        raise AssertionError("unhandled_test_mutation:" + mutation)

    with pytest.raises(ValueError, match=f"^{re.escape(expected_reason)}$"):
        checker.validate_materialized_assignment_identity(
            samples,
            reconstructed,
            design_rows,
            rule_rows,
            family_rows,
            manifest,
        )


def test_exact10_paths_are_safe_and_only_new_inventory() -> None:
    assert len(design.EXACT10_PATHS) == 10
    assert len(set(design.EXACT10_PATHS)) == 10
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    assert all(path.suffix not in forbidden for path in design.EXACT10_PATHS)
    assert all(not path.is_absolute() for path in design.EXACT10_PATHS)
    assert all(
        subprocess.run(
            ("git", "cat-file", "-e", f"{design.BASE_COMMIT}:{path.as_posix()}"),
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False, check=False,
        ).returncode != 0
        for path in design.EXACT10_PATHS
    )


def test_shared_hermetic_lifecycle_exact4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_ENV) == "1":
        assert design.validate_execution_boundary_v1(ROOT) in lifecycle.LIFECYCLES
        assert checker.validate_execution_boundary_independent(ROOT) in (
            lifecycle.LIFECYCLES
        )
        assert design.build_evidence_payloads(ROOT) == {
            name: (ROOT / design.OUTPUT_ROOT / name).read_bytes()
            for name in design.OUTPUT_FILES
        }
        return

    reference = {
        name: (ROOT / design.OUTPUT_ROOT / name).read_bytes()
        for name in design.OUTPUT_FILES
    }
    real_capture = lifecycle._capture_state
    observed_states: list[str] = []
    targeted_counts: list[int] = []
    checker_stdout: list[bytes] = []

    def capture(repository: Path, **kwargs):
        state = real_capture(repository, **kwargs)
        assert design.validate_execution_boundary_v1(repository) == state.lifecycle
        assert checker.validate_execution_boundary_independent(
            repository
        ) == state.lifecycle
        assert design.build_evidence_payloads(repository) == reference
        assert checker.check(repository)["lifecycle"] == state.lifecycle
        environment = {
            **os.environ, NESTED_ENV: "1", "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        }
        targeted = subprocess.run(
            (
                sys.executable, "-B", "-m", "pytest", "-q",
                "-p", "no:cacheprovider", design.EXACT10_PATHS[1].as_posix(),
            ),
            cwd=repository, env=environment, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=False, check=False,
        )
        assert targeted.returncode == 0, targeted.stdout + targeted.stderr
        assert targeted.stderr == b""
        match = re.search(rb"(\d+) passed", targeted.stdout)
        assert match
        targeted_counts.append(int(match.group(1)))
        checked = subprocess.run(
            (sys.executable, "-B", design.EXACT10_PATHS[2].as_posix()),
            cwd=repository, env=environment, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=False, check=False,
        )
        assert checked.returncode == 0, checked.stdout + checked.stderr
        assert checked.stderr == b""
        observed_states.append(state.lifecycle)
        checker_stdout.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT, tmp_path, base_commit=design.BASE_COMMIT,
        formal_commit_subject=design.FORMAL_COMMIT_SUBJECT,
        exact_paths=design.EXACT10_PATHS,
    )
    assert observed_states == list(lifecycle.LIFECYCLES)
    assert len(set(targeted_counts)) == 1
    assert len(set(checker_stdout)) == 1
    assert report.candidate_parent == design.BASE_COMMIT
    assert report.candidate_subject == design.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert tuple(tmp_path.iterdir()) == ()


def test_isolated_import_has_no_output_or_file_side_effects() -> None:
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / design.OUTPUT_ROOT).iterdir() if path.is_file()
    }
    code = (
        "import sys;"
        f"sys.path.insert(0,{str(ROOT / 'src')!r});"
        "import covalent_ext."
        "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1"
    )
    result = subprocess.run(
        (sys.executable, "-B", "-c", code), cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
    after = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / design.OUTPUT_ROOT).iterdir() if path.is_file()
    }
    assert before == after
