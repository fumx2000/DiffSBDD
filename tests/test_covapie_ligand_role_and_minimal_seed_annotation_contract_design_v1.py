from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from covalent_ext import (  # noqa: E402
    covapie_hermetic_git_lifecycle_harness_v1 as lifecycle,
)
from covalent_ext import (  # noqa: E402
    covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1 as contract,
)
import check_covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1 as checker  # noqa: E402


NESTED_LIFECYCLE_ENV = "COVAPIE_ROLE_SEED_NESTED_LIFECYCLE"


def _git(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@lru_cache(maxsize=1)
def _result() -> dict:
    return contract.derive_contract_design(ROOT)


@lru_cache(maxsize=1)
def _artifacts() -> dict[str, bytes]:
    return contract.build_artifacts(ROOT)


def test_formal_base_and_predecessor_sha() -> None:
    identity = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", contract.BASE_COMMIT
    ).decode().splitlines()
    assert identity == [
        contract.BASE_COMMIT,
        contract.BASE_PARENT,
        contract.BASE_TREE,
        contract.BASE_SUBJECT,
    ]
    payload = _git(
        "show", f"{contract.BASE_COMMIT}:{contract.PREDECESSOR_SOURCE.as_posix()}"
    )
    assert hashlib.sha256(payload).hexdigest() == contract.FROZEN_SHA256[
        contract.PREDECESSOR_SOURCE
    ]


def test_exact3_roles_exact5_masks_and_b3() -> None:
    assert contract.EXACT3_ROLES == ("scaffold", "linker", "warhead")
    assert [row[1] for row in contract.CANONICAL_TASKS] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert len(contract.CANONICAL_TASKS) == 5
    regions = contract.canonical_task_regions()
    assert regions["scaffold_only"] == {
        "target": ("scaffold",),
        "context": ("linker", "warhead"),
        "minimal_seed_context_override": False,
    }
    assert regions["scaffold_plus_linker_plus_warhead"][
        "minimal_seed_context_override"
    ]


def test_partition_success_and_fail_closed_paths() -> None:
    assert contract.validate_exact3_partition(
        range(6), (0, 1), (2, 3), (4, 5)
    ) == ()
    reasons = contract.validate_exact3_partition(
        range(6), (0, 1), (1, 2), (4,), hydrogen_atoms=(1,)
    )
    assert {
        "partition_overlap",
        "partition_not_exhaustive",
        "hydrogen_in_role_partition",
    } <= set(reasons)


@pytest.mark.parametrize(
    ("vertices", "edges", "warhead", "core", "expected"),
    [
        (range(5), ((0, 1), (1, 2), (2, 3), (3, 4)), (4,), (0, 1), 1),
        (range(6), ((0, 1), (1, 2), (2, 4), (1, 3), (3, 5)), (4,), (0, 1), 1),
        (range(6), ((0, 2), (2, 5), (1, 3), (3, 5), (0, 1)), (5,), (0, 1), 2),
        (range(2), ((0, 1),), (1,), (0,), 0),
        (range(4), ((0, 1), (2, 3)), (3,), (0,), 0),
        (range(4), ((0, 1), (2, 3), (1, 2)), (2, 3), (0,), 1),
    ],
)
def test_synthetic_graph_contracts(vertices, edges, warhead, core, expected) -> None:
    result = contract.classify_linker_components(vertices, edges, warhead, core)
    assert result["bridge_count"] == expected


def test_graph_component_classification_details() -> None:
    result = contract.classify_linker_components(
        range(7),
        ((0, 1), (1, 2), (2, 5), (1, 3), (5, 4)),
        (5,),
        (0, 1),
    )
    classes = {row["classification"] for row in result["components"]}
    assert "linker_bridge_component_candidate" in classes
    assert "scaffold_side_substituent" in classes
    assert "disconnected_graph_blocked" in classes


def test_minimal_seed_contract() -> None:
    assert contract.validate_minimal_seed(
        (0, 1), (0, 1, 2), (3,), (4,), ((0, 1), (1, 2)), 0
    ) == ()
    reasons = contract.validate_minimal_seed(
        (1, 3, 4, 5), (0, 1), (3,), (4,), (), 0
    )
    assert {
        "seed_outside_scaffold",
        "seed_overlaps_linker",
        "seed_overlaps_warhead",
        "seed_missing_primary_anchor",
        "seed_size_not_2_or_3",
        "seed_disconnected",
    } <= set(reasons)


def test_status_pipeline_and_rule_schema_are_closed() -> None:
    assert contract.ANNOTATION_STATUSES == (
        "proposal_only", "auto_exact", "gold_curated", "ambiguous_blocked"
    )
    assert len(contract.PIPELINE) == 11
    assert len(contract.WARHEAD_RULE_FIELDS) == 12
    assert "warhead_smarts" in contract.WARHEAD_RULE_FIELDS
    assert "ligand_reactive_atom_map_number" in contract.WARHEAD_RULE_FIELDS
    assert "minimal_seed_atom_indices" in contract.REVIEW_PACKAGE_FIELDS


@pytest.mark.parametrize("field_name", contract.SCENARIO_BOOL_FIELDS)
def test_all_scenario_bool_fields_reject_integer_one(field_name: str) -> None:
    scenario = dataclasses.replace(
        contract.BASELINE_SCENARIO, **{field_name: 1}
    )
    observation = contract.evaluate_annotation_scenario(scenario)
    assert observation.reasons == (
        f"scenario_field_type_invalid:{field_name}",
    )
    assert not observation.valid


@pytest.mark.parametrize(
    "field_name",
    (
        "warhead_boundary_count",
        "linker_bridge_count",
        "scaffold_linker_boundary_count",
    ),
)
@pytest.mark.parametrize("invalid_value", (True, False, 1.0, 0.0, "1", None))
def test_boundary_and_bridge_counts_require_exact_int(
    field_name: str,
    invalid_value: object,
) -> None:
    scenario = dataclasses.replace(
        contract.BASELINE_SCENARIO, **{field_name: invalid_value}
    )
    observation = contract.evaluate_annotation_scenario(scenario)
    assert observation.reasons == (
        f"scenario_field_type_invalid:{field_name}",
    )


@pytest.mark.parametrize(
    "field_name",
    contract.SCENARIO_NONNEGATIVE_INT_FIELDS,
)
@pytest.mark.parametrize(
    "invalid_value",
    (True, False, 1.0, 0.0, "1", None),
)
def test_all_scenario_count_fields_require_exact_nonnegative_int(
    field_name: str,
    invalid_value: object,
) -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO, **{field_name: invalid_value}
        )
    )
    assert observation.reasons == (
        f"scenario_field_type_invalid:{field_name}",
    )


@pytest.mark.parametrize(
    "field_name",
    contract.SCENARIO_NONNEGATIVE_INT_FIELDS,
)
def test_scenario_count_fields_reject_negative_int(field_name: str) -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO, **{field_name: -1}
        )
    )
    assert observation.reasons == (
        f"scenario_field_value_invalid:{field_name}",
    )


@pytest.mark.parametrize("invalid_value", (None, 1, True, ("gold_curated",)))
def test_annotation_status_requires_exact_str(invalid_value: object) -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO, annotation_status=invalid_value
        )
    )
    assert observation.reasons == (
        "scenario_field_type_invalid:annotation_status",
    )


@pytest.mark.parametrize(
    "invalid_value",
    (
        ["warhead_only"],
        ("warhead_only", 1),
        "warhead_only",
        None,
    ),
)
def test_canonical_masks_requires_exact_tuple_of_str(
    invalid_value: object,
) -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO, canonical_masks=invalid_value
        )
    )
    assert observation.reasons == (
        "scenario_field_type_invalid:canonical_masks",
    )


def test_gold_curated_always_requires_human_review() -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO,
            annotation_status="gold_curated",
            human_review_completed=False,
        )
    )
    assert "gold_curated_without_human_review" in observation.reasons
    assert not observation.valid


@pytest.mark.parametrize(
    "status",
    ("proposal_only", "auto_exact", "ambiguous_blocked"),
)
def test_non_gold_status_cannot_be_training_eligible(status: str) -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO,
            annotation_status=status,
            training_eligible=True,
        )
    )
    assert "non_gold_annotation_training_eligible" in observation.reasons
    if status == "ambiguous_blocked":
        assert "ambiguous_annotation_training_eligible" in observation.reasons


def test_gold_without_review_cannot_be_training_eligible() -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO,
            human_review_completed=False,
            training_eligible=True,
        )
    )
    assert "gold_curated_without_human_review" in observation.reasons
    assert "non_gold_annotation_training_eligible" in observation.reasons


def test_ringless_fallback_cannot_be_auto_exact_even_after_review() -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO,
            ringless_fallback_used=True,
            ringless_review_completed=True,
            annotation_status="auto_exact",
        )
    )
    assert "ringless_fallback_auto_exact_forbidden" in observation.reasons
    assert "ringless_fallback_review_missing" not in observation.reasons


def test_ringless_fallback_without_review_remains_blocked() -> None:
    observation = contract.evaluate_annotation_scenario(
        dataclasses.replace(
            contract.BASELINE_SCENARIO,
            ringless_fallback_used=True,
            ringless_review_completed=False,
        )
    )
    assert "ringless_fallback_review_missing" in observation.reasons


def test_current11_readiness_is_exact_and_truthful() -> None:
    rows = _result()["readiness_rows"]
    assert len(rows) == 11
    assert len({row["sample_index_row_id"] for row in rows}) == 11
    assert all(row["retained_heavy_atom_mapping_available"] for row in rows)
    assert all(row["ligand_reactive_atom_available"] for row in rows)
    assert all(row["residue_reactive_atom_available"] for row in rows)
    assert not any(row["pre_reaction_connectivity_available"] for row in rows)
    assert not any(row["pre_reaction_bond_order_available"] for row in rows)
    assert not any(row["reaction_family_label_available"] for row in rows)
    assert not any(row["approved_warhead_rule_available"] for row in rows)
    assert not any(row["role_proposal_generation_ready"] for row in rows)
    assert not any(row["minimal_seed_proposal_generation_ready"] for row in rows)


def test_schema_field_existence_is_not_current_value_availability() -> None:
    source_rows = {
        row["source_path"]: row for row in _result()["source_rows"]
    }
    schema = source_rows[contract.SCHEMA_SOURCE.as_posix()]
    assert schema["schema_only"]
    assert not schema["provides_actual_current11_value"]
    graph = source_rows[contract.LIGAND_GRAPH_SCAFFOLD_EVIDENCE.as_posix()]
    assert graph["evidence_class"] == "supporting"


def test_failure_matrix_uses_state_mutations_and_fails_closed() -> None:
    assert "failure_case" not in {
        field.name for field in dataclasses.fields(contract.AnnotationScenario)
    }
    rows = contract.build_failure_matrix_rows()
    assert len(rows) == len(contract.FAILURE_MUTATIONS) == 42
    assert len({row["mutation_signature"] for row in rows}) == 42
    for row, (case, specification) in zip(
        rows, contract.FAILURE_MUTATIONS.items(), strict=True
    ):
        fields = specification["fields"]
        expected_reasons = tuple(row["expected_reasons"].split(";"))
        assert fields
        assert row["failure_case"] == case
        assert row["mutated_fields"] == json.dumps(
            fields, sort_keys=True, separators=(",", ":")
        )
        scenario = dataclasses.replace(contract.BASELINE_SCENARIO, **fields)
        observation = contract.evaluate_annotation_scenario(scenario)
        assert not observation.valid
        assert observation.reasons
        assert row["mutation_signature"] == contract.mutation_signature(fields)
        assert all(reason in observation.reasons for reason in expected_reasons)
        assert row["expected_reasons_verified"]
        assert row["fails_closed"]
        assert not row["ready_for_role_annotation_proposal_generation"]
        assert not row["ready_for_mask_materialization"]
        assert not row["ready_for_model_integration"]
        assert not row["ready_for_training"]


def test_approved_warhead_rule_missing_is_independent_failure() -> None:
    specification = contract.FAILURE_MUTATIONS["approved warhead rule missing"]
    assert specification["fields"] == {
        "approved_warhead_rule_present": False
    }
    assert specification["expected_reasons"] == (
        "approved_warhead_rule_missing",
    )


def test_duplicate_failure_mutation_registry_is_rejected() -> None:
    registry = {
        case: {
            "fields": dict(specification["fields"]),
            "expected_reasons": tuple(specification["expected_reasons"]),
        }
        for case, specification in contract.FAILURE_MUTATIONS.items()
    }
    registry["duplicate signature probe"] = {
        "fields": {"reactive_atom_present": False},
        "expected_reasons": ("known_reactive_atom_missing",),
    }
    with pytest.raises(ValueError, match="failure_mutation_signature_duplicate"):
        contract.validate_failure_mutation_registry(registry)


def test_failure_mutation_wrong_exact_type_is_rejected() -> None:
    registry = {
        "wrong type": {
            "fields": {"approved_warhead_rule_present": 0},
            "expected_reasons": ("approved_warhead_rule_missing",),
        }
    }
    with pytest.raises(
        ValueError,
        match="failure_mutation_field_type_invalid:approved_warhead_rule_present",
    ):
        contract.validate_failure_mutation_registry(registry)


@pytest.mark.parametrize(
    "invalid_atoms",
    ((False, 1), (0.0, 1), (0, "1")),
)
def test_partition_rejects_non_exact_indices(invalid_atoms) -> None:
    assert contract.validate_exact3_partition(
        invalid_atoms, (0,), (1,), (2,)
    ) == ("partition_index_type_invalid",)


@pytest.mark.parametrize(
    "invalid_atoms",
    ({0, 1, 2}, frozenset((0, 1, 2)), iter((0, 1, 2)), "012", None),
)
def test_partition_rejects_unordered_or_single_pass_container(
    invalid_atoms,
) -> None:
    assert contract.validate_exact3_partition(
        invalid_atoms, (0,), (1,), (2,)
    ) == ("partition_container_invalid",)


def test_partition_rejects_duplicate_indices() -> None:
    assert contract.validate_exact3_partition(
        (0, 1, 1, 2), (0,), (1,), (2,)
    ) == ("partition_duplicate_index",)


@pytest.mark.parametrize("invalid_vertices", ((False, 1), (0.0, 1)))
def test_graph_rejects_bool_or_float_vertex(invalid_vertices) -> None:
    with pytest.raises(ValueError, match="graph_vertex_index_type_invalid"):
        contract.classify_linker_components(
            invalid_vertices, ((0, 1),), (1,), (0,)
        )


@pytest.mark.parametrize(
    ("edges", "reason"),
    (
        (((0, 1, 2),), "graph_edge_not_exact_pair"),
        (([0, 1],), "graph_edge_not_exact_pair"),
        (((False, 1),), "graph_edge_index_type_invalid"),
        (((0.0, 1),), "graph_edge_index_type_invalid"),
        (((0, 3),), "graph_edge_outside_vertices"),
        (((0, 0),), "graph_edge_self_loop"),
        (((0, 1), (1, 0)), "graph_duplicate_edge"),
    ),
)
def test_graph_rejects_invalid_edge(edges, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        contract.classify_linker_components(
            (0, 1, 2), edges, (2,), (0,)
        )


@pytest.mark.parametrize(
    ("warhead", "core", "reason"),
    (
        ((3,), (0,), "graph_warhead_outside_vertices"),
        ((2,), (3,), "graph_scaffold_core_outside_vertices"),
        ((1, 2), (0, 1), "graph_warhead_scaffold_core_overlap"),
    ),
)
def test_graph_rejects_role_domains(warhead, core, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        contract.classify_linker_components(
            (0, 1, 2), ((0, 1), (1, 2)), warhead, core
        )


@pytest.mark.parametrize(
    ("vertices", "warhead", "core", "reason"),
    (
        ((0, 1, 1), (2,), (0,), "graph_duplicate_vertex"),
        ((0, 1, 2), (2, 2), (0,), "graph_duplicate_warhead_index"),
        ((0, 1, 2), (2,), (0, 0), "graph_duplicate_scaffold_core_index"),
    ),
)
def test_graph_rejects_duplicate_role_indices(
    vertices, warhead, core, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        contract.classify_linker_components(
            vertices, ((0, 1), (1, 2)), warhead, core
        )


def test_public_helpers_accept_list_tuple_and_range_sequences() -> None:
    assert contract.validate_exact3_partition(
        range(6), [0, 1], (2, 3), [4, 5]
    ) == ()
    graph = contract.classify_linker_components(
        [0, 1, 2, 3], [(0, 1), (1, 2), (2, 3)], [3], range(1)
    )
    assert graph["bridge_count"] == 1
    assert contract.validate_minimal_seed(
        [0, 1], range(2), [2], (3,), [(0, 1)], 0
    ) == ()


def test_seed_rejects_bool_primary_anchor() -> None:
    assert contract.validate_minimal_seed(
        (0, 1), (0, 1), (2,), (3,), ((0, 1),), False
    ) == ("primary_anchor_type_invalid",)


@pytest.mark.parametrize("invalid_seed", ((False, 1), (0.0, 1), (0, "1")))
def test_seed_rejects_bool_float_or_string_atom(invalid_seed) -> None:
    assert contract.validate_minimal_seed(
        invalid_seed, (0, 1), (2,), (3,), ((0, 1),), 0
    ) == ("seed_index_type_invalid",)


def test_seed_rejects_duplicate_atom() -> None:
    assert contract.validate_minimal_seed(
        (0, 1, 1), (0, 1), (2,), (3,), ((0, 1),), 0
    ) == ("seed_duplicate_index",)


def test_deterministic_serialization_and_checked_evidence() -> None:
    first = contract.build_artifacts(ROOT)
    second = contract.build_artifacts(ROOT)
    third = contract.build_artifacts(ROOT)
    assert first == second == third == _artifacts()
    for name, payload in first.items():
        assert (ROOT / contract.OUTPUT_ROOT / name).read_bytes() == payload


def test_manifest_truthfulness_and_no_self_hash() -> None:
    manifest = json.loads(_artifacts()[contract.MANIFEST_FILE])
    assert manifest["contract_design_completed"]
    assert manifest["design_outcome"] == (
        "designed_contract_with_input_authority_gaps"
    )
    assert manifest["canonical_task_count"] == 5
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["annotation_scenario_exact_scalar_types_verified"]
    assert manifest["boundary_and_bridge_counts_exact_int_verified"]
    assert manifest["gold_curated_requires_human_review"]
    assert manifest["training_eligibility_requires_gold_curated"]
    assert manifest["ringless_fallback_auto_exact_forbidden"]
    assert manifest["public_role_atom_index_helpers_exact_types_verified"]
    assert manifest["boolean_rejected_for_role_atom_indices"]
    assert manifest["duplicate_role_atom_indices_rejected"]
    assert manifest["failure_mutation_signature_count"] == 42
    assert manifest["failure_mutation_signatures_unique"]
    assert manifest["failure_expected_reasons_verified"]
    assert manifest["failure_mutation_exact_types_verified"]
    assert not manifest["role_annotation_materialized"]
    assert not manifest["minimal_seed_materialized"]
    assert not manifest["ready_for_current11_role_annotation_proposal_generation"]
    assert not manifest["ready_for_training"]
    assert contract.MANIFEST_FILE not in manifest["evidence_sha256"]


def test_exact10_paths_and_safety() -> None:
    assert len(checker.EXACT10) == len(set(checker.EXACT10)) == 10
    assert set(path.name for path in checker.EXACT10[4:]) == set(
        contract.OUTPUT_FILES
    )
    for relative in checker.EXACT10:
        assert (ROOT / relative).is_file()
        assert relative.suffix.lower() not in checker.FORBIDDEN_SUFFIXES


def test_checker_stdout_is_deterministic() -> None:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "src",
    }
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            (sys.executable, "-B", checker.EXACT10[2].as_posix()),
            cwd=ROOT,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stderr == b""
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]


def test_shared_lifecycle_three_states(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert _result()["decision"].contract_design_completed
        return
    real_capture = lifecycle._capture_state
    states: list[str] = []
    checker_outputs: list[bytes] = []
    targeted_pass_counts: list[int] = []

    def capture(repository: Path, **kwargs):
        state = real_capture(repository, **kwargs)
        if state.lifecycle in (
            "pre_commit",
            "formal_main_post_commit_unpushed",
            "formal_main_post_push",
        ):
            environment = {
                **os.environ,
                NESTED_LIFECYCLE_ENV: "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": "src",
            }
            targeted = subprocess.run(
                (
                    sys.executable, "-m", "pytest", "-q",
                    checker.EXACT10[1].as_posix(),
                ),
                cwd=repository,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            assert targeted.stderr == b""
            targeted_pass_counts.append(
                int(targeted.stdout.decode().strip().splitlines()[-1].split()[0])
            )
            checked = subprocess.run(
                (sys.executable, "-B", checker.EXACT10[2].as_posix()),
                cwd=repository,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert checked.returncode == 0, checked.stdout + checked.stderr
            assert checked.stderr == b""
            states.append(state.lifecycle)
            checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=contract.BASE_COMMIT,
        formal_commit_subject=contract.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert states == [
        "pre_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert targeted_pass_counts[0] == targeted_pass_counts[1]
    assert targeted_pass_counts[1] == targeted_pass_counts[2]
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == contract.BASE_COMMIT
    assert report.candidate_subject == contract.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified
