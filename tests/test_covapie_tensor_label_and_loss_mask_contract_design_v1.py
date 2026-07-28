from __future__ import annotations

import csv
import dataclasses
import io
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

from covalent_ext import (  # noqa: E402
    covapie_hermetic_git_lifecycle_harness_v1 as lifecycle,
)
from covalent_ext import (  # noqa: E402
    covapie_tensor_label_and_loss_mask_contract_design_v1 as contract,
)
import check_covapie_tensor_label_and_loss_mask_contract_design_v1 as checker  # noqa: E402


NESTED_LIFECYCLE_ENV = "COVAPIE_TENSOR_CONTRACT_NESTED_LIFECYCLE"
CONTRACT_BOOL_FIELDS = tuple(
    field.name
    for field in dataclasses.fields(
        contract.TensorLabelAndLossMaskContractScenario
    )
    if type(getattr(contract.BASELINE_SCENARIO, field.name)) is bool
)
CONTRACT_INT_FIELDS = tuple(
    field.name
    for field in dataclasses.fields(
        contract.TensorLabelAndLossMaskContractScenario
    )
    if type(getattr(contract.BASELINE_SCENARIO, field.name)) is int
)
PAIR_POLICY_BOOL_FIELDS = tuple(
    field.name
    for field in dataclasses.fields(contract.PairCandidatePolicyScenario)
    if type(
        getattr(contract.BASELINE_PAIR_POLICY_SCENARIO, field.name)
    ) is bool
)


def _git(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _base(path: Path) -> bytes:
    return _git("show", f"{contract.BASE_COMMIT}:{path.as_posix()}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@lru_cache(maxsize=1)
def _result() -> dict:
    return contract.derive_covapie_tensor_label_and_loss_mask_contract_design_v1(
        ROOT
    )


@lru_cache(maxsize=1)
def _artifacts() -> dict[str, bytes]:
    return (
        contract.build_covapie_tensor_label_and_loss_mask_contract_design_artifacts_v1(
            ROOT
        )
    )


def _manifest() -> dict:
    return json.loads(_artifacts()[contract.MANIFEST_FILE])


def _registry_by_name() -> dict[str, dict]:
    return {
        row["semantic_name"]: row for row in _result()["registry_rows"]
    }


def test_public_api_and_frozen_decision() -> None:
    decision = _result()["decision"]
    assert dataclasses.is_dataclass(decision)
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.outcome = "invalid"  # type: ignore[misc]
    assert decision.schema_version == contract.SCHEMA_VERSION
    assert decision.outcome == "designed_with_blockers"


def test_scenario_has_explicit_state_and_no_failure_case_field() -> None:
    fields = {
        field.name
        for field in dataclasses.fields(
            contract.TensorLabelAndLossMaskContractScenario
        )
    }
    assert "failure_case" not in fields
    assert {
        "predecessor_sha_valid",
        "checkpoint_atom_feature_width",
        "pair_candidate_offsets_valid",
        "geometry_components_semantically_complete",
        "training_used",
    }.issubset(fields)


def test_baseline_scenario_is_truthful_blocked_design() -> None:
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            contract.BASELINE_SCENARIO
        )
    )
    assert observation.outcome == "designed_with_blockers"
    assert observation.reasons == (
        "current11_per_atom_role_and_minimal_seed_authority_missing",
        "current11_warhead_type_vocabulary_missing",
        "complete_pre_post_geometry_contract_missing",
    )
    assert not observation.condition_contract_resolved
    assert observation.pair_contract_resolved
    assert not observation.geometry_and_auxiliary_label_contract_resolved
    assert not observation.tensor_label_loss_mask_contract_designed
    assert not observation.ready_for_tensor_materialization_smoke


def test_formal_base_identity() -> None:
    observed = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", contract.BASE_COMMIT
    ).decode().splitlines()
    assert observed == [
        contract.BASE_COMMIT,
        contract.BASE_PARENT,
        contract.BASE_TREE,
        contract.BASE_SUBJECT,
    ]


@pytest.mark.parametrize("path,expected", tuple(contract.FROZEN_SHA256.items()))
def test_predecessor_sha(path: Path, expected: str) -> None:
    import hashlib

    assert hashlib.sha256(_base(path)).hexdigest() == expected


def test_predecessor_effective_open_issue_count_zero() -> None:
    predecessor = _result()["predecessor_manifest"]
    assert predecessor["effective_open_issue_count"] == 0
    assert predecessor["effective_open_issues"] == []
    assert predecessor["ready_for_tensor_label_loss_mask_contract_design"]


def test_checkpoint_10d_width() -> None:
    registry = _registry_by_name()
    for name in (
        "ligand_heavy_atom_one_hot_10d",
        "pocket_heavy_atom_one_hot_10d",
    ):
        assert registry[name]["dtype"] == "float32"
        assert registry[name]["width_or_component_count"] == 10
        assert registry[name]["shape"].endswith(",10]")
        assert registry[name]["contract_category"] == "current_checkpoint_input"


def test_sidecars_do_not_change_checkpoint_width() -> None:
    manifest = _manifest()
    assert manifest["base_checkpoint_atom_feature_width"] == 10
    assert not manifest["base_checkpoint_atom_feature_width_changed"]
    assert manifest["new_covalent_tensors_are_sidecars"]
    assert manifest["future_adapter_required"]
    assert all(
        not row["changes_checkpoint_input_width"]
        for row in _result()["registry_rows"]
    )


def test_exact6_index_spaces() -> None:
    assert contract.EXACT_INDEX_SPACES == (
        "source_full_atom_row_index_0based",
        "retained_heavy_local_index_0based",
        "flattened_ligand_index_0based",
        "flattened_pocket_index_0based",
        "pair_candidate_index_0based",
        "batch_sample_index_0based",
    )
    assert _result()["decision"].index_space_contract_count == 6
    assert _manifest()["index_spaces"] == list(contract.EXACT_INDEX_SPACES)


def test_offsets_and_local_to_flat() -> None:
    offsets = (0, 3, 3, 8)
    assert contract.validate_offsets_v1(offsets, 8)
    assert contract.flatten_local_index_v1(offsets, 0, 2) == 2
    assert contract.flatten_local_index_v1(offsets, 2, 4) == 7
    assert not contract.validate_offsets_v1((1, 3), 3)
    assert not contract.validate_offsets_v1((0, 4, 3), 3)
    assert not contract.validate_offsets_v1((0, 2), 3)
    with pytest.raises(ValueError):
        contract.flatten_local_index_v1(offsets, 1, 0)


@pytest.mark.parametrize(
    "offsets,terminal",
    (
        ((0, 1), True),
        ((0, 1), False),
        ((0, 1), 1.0),
        ((0, 1), "1"),
        ((0, True), 1),
        ((False, 1), 1),
        ((0, 1.0), 1),
        (None, 0),
        ((), 0),
    ),
)
def test_offsets_reject_non_exact_int_and_malformed_inputs(
    offsets: object,
    terminal: object,
) -> None:
    assert not contract.validate_offsets_v1(offsets, terminal)


def test_offsets_accept_exact_zero_and_sequence_contract() -> None:
    assert contract.validate_offsets_v1((0,), 0)
    assert contract.validate_offsets_v1((0, 1), 1)
    assert contract.validate_offsets_v1([0, 1], 1)
    assert contract.validate_offsets_v1(range(0, 2), 1)


@pytest.mark.parametrize(
    "offsets",
    (
        {0: "x", 1: "y"},
        {0, 1},
        frozenset({0, 1}),
        iter([0, 1]),
        (value for value in [0, 1]),
        "01",
        b"\x00\x01",
        bytearray([0, 1]),
        memoryview(b"\x00\x01"),
        None,
    ),
)
def test_offsets_reject_unordered_single_pass_and_binary_containers(
    offsets: object,
) -> None:
    assert not contract.validate_offsets_v1(offsets, 1)


def test_offsets_fail_closed_when_sequence_read_raises() -> None:
    class BrokenSequence(list):
        def __iter__(self):
            raise RuntimeError("unreadable sequence")

    offsets = BrokenSequence((0, 1))
    assert not contract.validate_offsets_v1(offsets, 1)
    with pytest.raises(ValueError, match="^offset contract invalid$"):
        contract.flatten_local_index_v1(offsets, 0, 0)


@pytest.mark.parametrize(
    "batch,local,reason",
    (
        (False, 0, "batch sample index exact int required"),
        (True, 0, "batch sample index exact int required"),
        (0.0, 0, "batch sample index exact int required"),
        ("0", 0, "batch sample index exact int required"),
        (0, False, "retained-heavy local index exact int required"),
        (0, True, "retained-heavy local index exact int required"),
        (0, 1.0, "retained-heavy local index exact int required"),
        (0, "1", "retained-heavy local index exact int required"),
    ),
)
def test_flatten_local_index_rejects_non_exact_int(
    batch: object,
    local: object,
    reason: str,
) -> None:
    with pytest.raises(ValueError, match=f"^{reason}$"):
        contract.flatten_local_index_v1((0, 2), batch, local)


def test_flatten_local_index_accepts_zero_and_returns_exact_int() -> None:
    first = contract.flatten_local_index_v1((0, 2), 0, 0)
    second = contract.flatten_local_index_v1((0, 2), 0, 1)
    from_list = contract.flatten_local_index_v1([0, 2], 0, 1)
    from_range = contract.flatten_local_index_v1(range(0, 3, 2), 0, 1)
    assert first == 0 and type(first) is int
    assert second == 1 and type(second) is int
    assert from_list == 1 and type(from_list) is int
    assert from_range == 1 and type(from_range) is int


@pytest.mark.parametrize(
    "offsets",
    (
        {0: "x", 1: "y"},
        {0, 1},
        frozenset({0, 1}),
        iter([0, 2]),
        (value for value in [0, 2]),
        "02",
        b"\x00\x02",
        bytearray([0, 2]),
        memoryview(b"\x00\x02"),
    ),
)
def test_flatten_local_index_rejects_non_sequence_offsets(
    offsets: object,
) -> None:
    with pytest.raises(ValueError, match="^offset contract invalid$"):
        contract.flatten_local_index_v1(offsets, 0, 0)


def test_sentinel_requires_validity_and_zero_is_not_missing() -> None:
    assert contract.validate_sentinel_with_validity_v1(-1, False)
    assert contract.validate_sentinel_with_validity_v1(0, True)
    assert not contract.validate_sentinel_with_validity_v1(0, False)
    assert not contract.validate_sentinel_with_validity_v1(-1, True)
    assert not contract.validate_sentinel_with_validity_v1(True, True)
    assert not contract.validate_sentinel_with_validity_v1(0, 1)
    assert not contract.validate_sentinel_with_validity_v1(0.0, True)
    manifest = _manifest()
    assert manifest["sentinel_requires_validity_mask"]
    assert not manifest["zero_means_missing"]


def test_exact5_tasks_and_b3() -> None:
    assert len(contract.CANONICAL_TASKS) == 5
    assert contract.CANONICAL_TASKS[3] == (3, "scaffold_only", "B3")
    assert [row[0] for row in contract.CANONICAL_TASKS] == list(range(5))


@pytest.mark.parametrize(
    "task_id",
    (True, False, 0.0, 1.0, "0", None),
)
def test_canonical_task_id_requires_exact_int(task_id: object) -> None:
    with pytest.raises(
        ValueError,
        match="^canonical task id exact int required$",
    ):
        contract.canonical_task_regions_v1(task_id)


def test_long_semantic_names_are_authoritative() -> None:
    assert [row[1] for row in contract.CANONICAL_TASKS] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert [row[2] for row in contract.CANONICAL_TASKS] == [
        "A", "B", "B2", "B3", "C"
    ]


def test_dynamic_role_vocabulary_and_current11_gap() -> None:
    result = _result()
    assert result["role_contract"]["role_vocabulary"] == (
        "scaffold", "linker", "warhead"
    )
    assert result["role_contract"]["role_vocabulary_frozen"]
    assert result["analysis"]["role_fields_present"] == ()
    role = _registry_by_name()["ligand_role_id"]
    assert role["contract_status"] == "designed_with_blocker"


@pytest.mark.parametrize(
    "task_id,target,context",
    (
        (0, ("warhead",), ("scaffold", "linker")),
        (1, ("linker", "warhead"), ("scaffold",)),
        (2, ("scaffold", "warhead"), ("linker",)),
        (3, ("scaffold",), ("linker", "warhead")),
        (
            4,
            ("scaffold", "linker", "warhead"),
            ("minimal_seed_or_anchor",),
        ),
    ),
)
def test_role_to_task_mask_truth_table(
    task_id: int,
    target: tuple[str, ...],
    context: tuple[str, ...],
) -> None:
    row = contract.canonical_task_regions_v1(task_id)
    assert row["target"] == target
    assert row["context"] == context


def test_target_context_complement_contract() -> None:
    registry = _registry_by_name()
    for name in (
        "ligand_generation_mask",
        "ligand_fixed_mask",
        "ligand_target_mask",
        "ligand_context_mask",
    ):
        row = registry[name]
        assert row["dtype"] == "bool"
        assert row["shape"] == "[N_ligand,1]"
        assert "disjoint and exhaustive" in row["derivation_rule"]


def test_c_minimal_seed_anchor_stays_context_and_is_blocked() -> None:
    c = contract.canonical_task_regions_v1(4)
    assert c["minimal_seed_or_anchor_context_override"] is True
    seed = _registry_by_name()["ligand_minimal_seed_or_anchor_mask"]
    assert seed["contract_status"] == "designed_with_blocker"
    assert seed["blocking_reason"] == "minimal_seed_or_anchor_authority_missing"


def test_target_residue_membership_and_reactive_exact_one() -> None:
    evidence = _result()["analysis"]["sample_evidence"]
    assert len(evidence) == 11
    assert all(row["target_residue_retained_heavy_count"] == 6 for row in evidence)
    assert all(
        row["positive_pocket_local_index"]
        in row["target_residue_pocket_local_indices"]
        for row in evidence
    )
    assert _result()["analysis"][
        "target_residue_condition_current_valid_sample_count"
    ] == 11


def test_target_residue_local_flat_index_contract() -> None:
    registry = _registry_by_name()
    local = registry["target_residue_reactive_atom_local_index"]
    flat = registry["target_residue_reactive_atom_flat_index"]
    assert local["index_space"] == "retained_heavy_local_index_0based"
    assert flat["index_space"] == "flattened_pocket_index_0based"
    assert "pocket_node_offsets" in flat["derivation_rule"]
    assert local["sentinel_semantics"].startswith("-1")
    assert flat["sentinel_semantics"].startswith("-1")


def test_anchor_distance_semantics() -> None:
    registry = _registry_by_name()
    distance = registry["ligand_anchor_distance_angstrom"]
    valid = registry["ligand_anchor_distance_valid"]
    assert distance["dtype"] == "float32"
    assert distance["shape"] == "[N_ligand,1]"
    assert distance["unit"] == "angstrom"
    assert distance["coordinate_frame"] == "centering_invariant_euclidean_distance"
    assert valid["dtype"] == "bool"


def test_pair_candidate_domain_and_total() -> None:
    manifest = _manifest()
    assert manifest["pair_candidate_domain"] == (
        "retained_ligand_heavy_atoms_x_target_residue_retained_heavy_atoms"
    )
    assert manifest["pair_candidate_count_current11"] == 1938
    assert sum(
        row["candidate_count"]
        for row in _result()["analysis"]["sample_evidence"]
    ) == 1938
    assert manifest["pair_contrastive_sample_loss_mask_current11"] == (
        [True] * 11
    )
    assert manifest["pair_contrastive_mask_true_count_current11"] == 11


def test_pair_deterministic_order_and_indices() -> None:
    manifest = _manifest()
    assert manifest["pair_candidate_order"] == (
        "sample_then_ligand_local_then_target_residue_local"
    )
    registry = _registry_by_name()
    assert registry["pair_candidate_ligand_local_index"][
        "index_space"
    ] == "retained_heavy_local_index_0based"
    assert registry["pair_candidate_ligand_flat_index"][
        "index_space"
    ] == "flattened_ligand_index_0based"
    assert registry["pair_candidate_pocket_flat_index"][
        "index_space"
    ] == "flattened_pocket_index_0based"
    residue_local = registry["pair_candidate_residue_local_index"]
    assert residue_local["local_or_flat"] == (
        "pocket_retained_heavy_local_within_sample"
    )
    assert "never target-residue member ordinal" in residue_local[
        "derivation_rule"
    ]


def test_pair_candidate_offsets_and_1938_metadata_records() -> None:
    analysis = _result()["analysis"]
    projection = analysis["pair_projection"]
    assert analysis["ligand_node_offsets"] == (
        0, 13, 26, 39, 64, 92, 135, 177, 219, 262, 302, 323
    )
    assert analysis["pocket_node_offsets"] == (
        0, 66, 170, 266, 474, 662, 940, 1207, 1464, 1713, 1974, 2202
    )
    assert projection.pair_candidate_offsets == (
        0, 78, 156, 234, 384, 552, 810, 1062, 1314, 1572, 1812, 1938
    )
    assert len(projection.records) == 1938
    assert sum(projection.pair_candidate_is_positive) == 11
    assert all(projection.pair_positive_candidate_valid)
    assert all(value >= 1 for value in projection.pair_negative_count)
    assert projection.pair_contrastive_sample_loss_mask == (True,) * 11
    for row in projection.records:
        batch = row.pair_candidate_batch_index
        assert row.pair_candidate_ligand_flat_index == (
            analysis["ligand_node_offsets"][batch]
            + row.pair_candidate_ligand_local_index
        )
        assert row.pair_candidate_pocket_flat_index == (
            analysis["pocket_node_offsets"][batch]
            + row.pair_candidate_residue_local_index
        )
    for spec, positive in zip(
        analysis["pair_candidate_sample_specs"],
        projection.pair_positive_candidate_index,
    ):
        member_ordinal = (
            spec.target_residue_pocket_local_indices.index(
                spec.positive_pocket_local_index
            )
        )
        batch = spec.batch_sample_index_0based
        assert positive == (
            projection.pair_candidate_offsets[batch]
            + spec.positive_ligand_local_index
            * len(spec.target_residue_pocket_local_indices)
            + member_ordinal
        )
    assert any(
        value > 5
        for value in projection.pair_candidate_residue_local_index
    )
    registry = _registry_by_name()["pair_candidate_offsets"]
    assert registry["dtype"] == "int64"
    assert registry["rank"] == 1
    assert registry["shape"] == "[B+1]"
    assert registry["index_space"] == "pair_candidate_index_0based"
    assert registry["local_or_flat"] == (
        "batch_boundary_to_global_candidate"
    )


def test_pair_candidate_builder_fails_closed_on_offset_or_order_drift() -> None:
    spec = contract.PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=2,
        retained_pocket_count=6,
        target_residue_pocket_local_indices=(1, 4),
        positive_ligand_local_index=1,
        positive_pocket_local_index=4,
    )
    projection = contract.build_pair_candidate_records_v1(
        (spec,), (0, 2), (0, 6)
    )
    assert projection.pair_candidate_offsets == (0, 4)
    assert projection.pair_candidate_residue_local_index == (1, 4, 1, 4)
    assert projection.pair_positive_candidate_index == (3,)
    with pytest.raises(ValueError, match="ligand node offsets invalid"):
        contract.build_pair_candidate_records_v1(
            (spec,), (0, 3), (0, 6)
        )
    with pytest.raises(ValueError, match="sorted unique pocket-local"):
        contract.build_pair_candidate_records_v1(
            (
                dataclasses.replace(
                    spec,
                    target_residue_pocket_local_indices=(4, 1),
                ),
            ),
            (0, 2),
            (0, 6),
        )
    missing_pair_offsets = dataclasses.replace(
        contract.BASELINE_SCENARIO,
        pair_offsets_present=False,
    )
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            missing_pair_offsets
        )
    )
    assert observation.outcome == "invalid"
    assert "pair_candidate_offsets_missing" in observation.reasons


def test_one_positive_zero_negative_pair_head_projection_is_valid() -> None:
    spec = contract.PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=1,
        retained_pocket_count=1,
        target_residue_pocket_local_indices=(0,),
        positive_ligand_local_index=0,
        positive_pocket_local_index=0,
    )
    valid, reasons = (
        contract.validate_pair_candidate_sample_spec_exact_types_v1(spec)
    )
    assert valid and reasons == ()
    projection = contract.build_pair_candidate_records_v1(
        (spec,), (0, 1), (0, 1)
    )
    assert len(projection.records) == 1
    assert projection.pair_candidate_is_positive == (True,)
    assert projection.pair_candidate_is_negative == (False,)
    assert projection.pair_positive_candidate_valid == (True,)
    assert projection.pair_negative_count == (0,)
    assert projection.pair_contrastive_sample_loss_mask == (False,)


@pytest.mark.parametrize(
    "field_name,value",
    (
        ("batch_sample_index_0based", False),
        ("batch_sample_index_0based", True),
        ("retained_ligand_count", True),
        ("retained_pocket_count", True),
        ("positive_ligand_local_index", True),
        ("positive_pocket_local_index", True),
        ("target_residue_pocket_local_indices", (False, 4)),
        ("target_residue_pocket_local_indices", [1, 4]),
    ),
)
def test_pair_candidate_sample_spec_rejects_bool_and_non_tuple_types(
    field_name: str,
    value: object,
) -> None:
    baseline = contract.PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=2,
        retained_pocket_count=6,
        target_residue_pocket_local_indices=(1, 4),
        positive_ligand_local_index=0,
        positive_pocket_local_index=1,
    )
    invalid = dataclasses.replace(
        baseline,
        **{field_name: value},
    )
    valid, reasons = (
        contract.validate_pair_candidate_sample_spec_exact_types_v1(
            invalid
        )
    )
    assert not valid
    assert reasons
    with pytest.raises(ValueError, match="type_invalid"):
        contract.build_pair_candidate_records_v1(
            (invalid,),
            (0, 2),
            (0, 6),
        )


def test_zero_negative_scenario_keeps_pair_contract_resolved() -> None:
    scenario = dataclasses.replace(
        contract.BASELINE_SCENARIO,
        pair_negative_count=0,
        contrastive_sample_loss_mask_enabled=False,
    )
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            scenario
        )
    )
    assert observation.outcome == "designed_with_blockers"
    assert observation.pair_contract_resolved
    assert observation.reasons == (
        "current11_per_atom_role_and_minimal_seed_authority_missing",
        "current11_warhead_type_vocabulary_missing",
        "complete_pre_post_geometry_contract_missing",
    )
    assert not observation.ready_for_tensor_materialization_smoke


@pytest.mark.parametrize(
    "field_name,reason",
    (
        ("pair_positive_count", "positive_pair_count_negative"),
        ("pair_negative_count", "negative_pair_count_negative"),
    ),
)
def test_top_level_pair_counts_reject_negative_values(
    field_name: str,
    reason: str,
) -> None:
    invalid = dataclasses.replace(
        contract.BASELINE_SCENARIO,
        **{
            field_name: -1,
            "contrastive_sample_loss_mask_enabled": False,
        },
    )
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            invalid
        )
    )
    assert observation.outcome == "invalid"
    assert observation.reasons == (reason,)
    assert not observation.pair_contract_resolved


@pytest.mark.parametrize("field_name", CONTRACT_BOOL_FIELDS)
def test_contract_scenario_bool_fields_require_exact_bool(
    field_name: str,
) -> None:
    invalid = dataclasses.replace(
        contract.BASELINE_SCENARIO,
        **{field_name: 1},
    )
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            invalid
        )
    )
    assert observation.outcome == "invalid"
    assert observation.reasons == (
        f"scenario_field_type_invalid:{field_name}",
    )


@pytest.mark.parametrize("field_name", CONTRACT_INT_FIELDS)
def test_contract_scenario_integer_fields_reject_bool(
    field_name: str,
) -> None:
    invalid = dataclasses.replace(
        contract.BASELINE_SCENARIO,
        **{field_name: True},
    )
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            invalid
        )
    )
    assert observation.outcome == "invalid"
    assert observation.reasons == (
        f"scenario_field_type_invalid:{field_name}",
    )


@pytest.mark.parametrize(
    "field_name,value",
    (
        ("pair_positive_count", 1.0),
        ("pair_positive_count", "1"),
        ("pair_negative_count", 1.0),
        ("pair_negative_count", "1"),
    ),
)
def test_contract_scenario_counts_reject_float_and_string(
    field_name: str,
    value: object,
) -> None:
    invalid = dataclasses.replace(
        contract.BASELINE_SCENARIO,
        **{field_name: value},
    )
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            invalid
        )
    )
    assert observation.outcome == "invalid"
    assert observation.reasons == (
        f"scenario_field_type_invalid:{field_name}",
    )


@pytest.mark.parametrize("field_name", PAIR_POLICY_BOOL_FIELDS)
def test_pair_policy_bool_fields_require_exact_bool(
    field_name: str,
) -> None:
    invalid = dataclasses.replace(
        contract.BASELINE_PAIR_POLICY_SCENARIO,
        **{field_name: 1},
    )
    observation = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            invalid
        )
    )
    assert not observation.candidate_allowed
    assert observation.fails_closed
    assert observation.reasons == (
        f"pair_policy_scenario_field_type_invalid:{field_name}",
    )


@pytest.mark.parametrize("field_name", ("positive_count", "negative_count"))
def test_pair_policy_integer_counts_reject_bool(field_name: str) -> None:
    invalid = dataclasses.replace(
        contract.BASELINE_PAIR_POLICY_SCENARIO,
        **{field_name: True},
    )
    observation = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            invalid
        )
    )
    assert not observation.candidate_allowed
    assert observation.reasons == (
        f"pair_policy_scenario_field_type_invalid:{field_name}",
    )


@pytest.mark.parametrize(
    "field_name,reason",
    (
        ("positive_count", "positive_pair_count_negative"),
        ("negative_count", "negative_pair_count_negative"),
    ),
)
def test_pair_policy_counts_reject_negative_values(
    field_name: str,
    reason: str,
) -> None:
    invalid = dataclasses.replace(
        contract.BASELINE_PAIR_POLICY_SCENARIO,
        **{
            field_name: -1,
            "contrastive_sample_loss_mask_enabled": False,
        },
    )
    observation = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            invalid
        )
    )
    assert not observation.candidate_allowed
    assert observation.reasons == (reason,)
    assert observation.loss_mask_semantics == "all_related_loss_masks_false"


def test_zero_negative_pair_policy_only_disables_contrastive_loss() -> None:
    disabled = dataclasses.replace(
        contract.BASELINE_PAIR_POLICY_SCENARIO,
        negative_count=0,
        contrastive_sample_loss_mask_enabled=False,
    )
    disabled_observation = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            disabled
        )
    )
    assert disabled_observation.candidate_allowed
    assert disabled_observation.reasons == (
        "valid_exact_positive_in_frozen_candidate_domain",
    )

    enabled = dataclasses.replace(
        disabled,
        contrastive_sample_loss_mask_enabled=True,
    )
    enabled_observation = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            enabled
        )
    )
    assert enabled_observation.candidate_allowed
    assert enabled_observation.reasons == (
        "contrastive_loss_requires_at_least_one_negative",
    )
    assert enabled_observation.loss_mask_semantics == (
        "pair_head_may_be_valid_but_contrastive_sample_mask_false"
    )


def test_pair_positive_exact_one_and_negative_counts() -> None:
    result = _result()
    assert result["decision"].pair_positive_exact_one_verified
    assert all(row["negative_count"] >= 1 for row in result["analysis"]["sample_evidence"])
    assert sum(
        row["negative_count"] for row in result["analysis"]["sample_evidence"]
    ) == 1938 - 11
    assert all(
        value >= 0
        for value in result["analysis"]["pair_projection"].pair_negative_count
    )


def test_all_same_sample_negatives_and_forbidden_policies() -> None:
    manifest = _manifest()
    assert manifest["pair_negative_policy"] == (
        "all_valid_same_sample_non_positive_candidates"
    )
    assert not manifest["cross_sample_negatives_allowed"]
    assert not manifest["random_negative_sampling_allowed"]
    assert not manifest["hard_negative_mining_allowed"]


@pytest.mark.parametrize("case_id", contract.PAIR_POLICY_CASES)
def test_pair_policy_matrix_uses_explicit_scenario_mutation(
    case_id: str,
) -> None:
    mutation = contract.PAIR_POLICY_MUTATIONS[case_id]
    fields = mutation["fields"]
    scenario = dataclasses.replace(
        contract.BASELINE_PAIR_POLICY_SCENARIO,
        **fields,
    )
    observed = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            scenario
        )
    )
    assert mutation["expected_reason"] in observed.reasons
    assert contract.mutation_signature_v1(fields)
    if case_id in {"valid_same_sample_positive", "valid_same_sample_negative"}:
        assert observed.candidate_allowed
        assert not observed.fails_closed
    elif case_id == "no_negative_candidate":
        assert observed.candidate_allowed
        assert observed.fails_closed
    else:
        assert not observed.candidate_allowed
        assert observed.fails_closed


def test_pair_head_and_contrastive_loss_masks() -> None:
    registry = _registry_by_name()
    pair = registry["pair_head_candidate_loss_mask"]
    contrastive = registry["pair_contrastive_sample_loss_mask"]
    assert pair["shape"] == "[P]"
    assert pair["contract_status"] == "designed"
    assert "label available" in pair["derivation_rule"]
    assert contrastive["shape"] == "[B]"
    assert "exactly one positive" in contrastive["derivation_rule"]
    assert "at least one negative" in contrastive["derivation_rule"]


def test_warhead_vocabulary_and_label_validity_blocker() -> None:
    result = _result()
    manifest = _manifest()
    assert result["analysis"]["warhead_type_vocabulary"] == ()
    assert result["analysis"]["warhead_fields_present"] == ()
    assert not result["decision"].warhead_type_vocabulary_frozen
    assert manifest["warhead_type_valid_sample_count"] == 0
    assert _registry_by_name()["warhead_type_id"][
        "contract_status"
    ] == "designed_with_blocker"


def test_geometry_component_registry_units_and_periodicity() -> None:
    manifest = _manifest()
    assert manifest["geometry_component_count"] == 1
    component = manifest["geometry_components"][0]
    assert component["semantic_name"] == (
        "post_covalent_positive_pair_bond_distance_angstrom"
    )
    assert component["unit"] == "angstrom"
    assert component["periodic_or_nonperiodic"] == "nonperiodic"
    assert component["canonical_range"] == "[0,+inf)"
    assert component["current_valid_sample_count"] == 11
    assert not manifest["geometry_contract_frozen"]


def test_geometry_missing_component_and_loss_masks() -> None:
    registry = _registry_by_name()
    component_valid = registry["geometry_component_valid_mask"]
    component_loss = registry["geometry_component_loss_mask"]
    sample_loss = registry["geometry_sample_loss_mask"]
    assert "never zero-filled into loss" in component_valid[
        "label_availability_semantics"
    ]
    assert component_loss["contract_status"] == "designed_with_blocker"
    assert sample_loss["contract_status"] == "designed_with_blocker"


def test_generation_and_padding_masks_are_not_label_or_loss_masks() -> None:
    manifest = _manifest()
    assert manifest["generation_masks_are_not_loss_masks"]
    assert manifest["padding_masks_are_not_label_availability_masks"]


def test_issue_inventory_exact3_and_predecessor_prefix() -> None:
    payload = _artifacts()[contract.ISSUE_INVENTORY_FILE]
    predecessor = _base(contract.PREDECESSOR_ISSUES)
    assert payload.startswith(predecessor)
    rows = _rows(payload)
    assert len(rows) == 35
    assert rows[:32] == _rows(predecessor)
    assert [
        (row["issue_id"], row["successor_effective_status"])
        for row in rows[32:]
    ] == [
        ("COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED", "open"),
        ("COVALENT_PAIR_LABEL_AND_NEGATIVE_POLICY_UNRESOLVED", "resolved"),
        ("COVALENT_GEOMETRY_AND_AUXILIARY_LABEL_CONTRACT_UNRESOLVED", "open"),
    ]


@pytest.mark.parametrize("failure_case", contract.FAILURE_CASES)
def test_failure_matrix_cases_mutate_state_and_fail_closed(
    failure_case: str,
) -> None:
    mutation = contract.FAILURE_MUTATIONS[failure_case]
    fields = mutation["fields"]
    scenario = dataclasses.replace(contract.BASELINE_SCENARIO, **fields)
    assert fields
    assert all(
        getattr(scenario, name) == value
        and getattr(contract.BASELINE_SCENARIO, name) != value
        for name, value in fields.items()
    )
    observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            scenario
        )
    )
    assert observation.outcome == "invalid"
    assert mutation["expected_reason"] in observation.reasons
    assert observation.fails_closed
    assert not observation.tensor_label_loss_mask_contract_designed
    assert not observation.ready_for_tensor_materialization_smoke
    assert not observation.ready_for_tensorization
    assert not observation.ready_for_model_integration
    assert not observation.ready_for_training


def test_failure_mutation_signatures_are_exact40_and_distinct() -> None:
    signatures = [
        contract.mutation_signature_v1(
            contract.FAILURE_MUTATIONS[case_id]["fields"]
        )
        for case_id in contract.FAILURE_CASES
    ]
    assert tuple(contract.FAILURE_MUTATIONS) == contract.FAILURE_CASES
    assert len(signatures) == len(set(signatures)) == 40
    rows = _result()["failure_rows"]
    assert [row["mutation_signature"] for row in rows] == signatures
    assert all(row["failure_detected"] and row["verified"] for row in rows)


def test_mutation_registries_use_existing_fields_and_exact_types() -> None:
    failure_valid, failure_reasons = (
        contract.validate_mutation_registry_exact_types_v1(
            contract.BASELINE_SCENARIO,
            contract.FAILURE_MUTATIONS,
            registry_name="failure",
        )
    )
    pair_valid, pair_reasons = (
        contract.validate_mutation_registry_exact_types_v1(
            contract.BASELINE_PAIR_POLICY_SCENARIO,
            contract.PAIR_POLICY_MUTATIONS,
            registry_name="pair_policy",
        )
    )
    assert failure_valid and failure_reasons == ()
    assert pair_valid and pair_reasons == ()
    assert len({
        contract.mutation_signature_v1(mutation["fields"])
        for mutation in contract.FAILURE_MUTATIONS.values()
    }) == 40
    assert len({
        contract.mutation_signature_v1(mutation["fields"])
        for mutation in contract.PAIR_POLICY_MUTATIONS.values()
    }) == 16

    invalid_type, type_reasons = (
        contract.validate_mutation_registry_exact_types_v1(
            contract.BASELINE_SCENARIO,
            {
                "invalid": {
                    "fields": {"pair_negative_count": False},
                    "expected_reason": "not_used",
                }
            },
            registry_name="failure",
        )
    )
    missing_field, missing_reasons = (
        contract.validate_mutation_registry_exact_types_v1(
            contract.BASELINE_PAIR_POLICY_SCENARIO,
            {
                "invalid": {
                    "fields": {"unknown_field": True},
                    "expected_reason": "not_used",
                }
            },
            registry_name="pair_policy",
        )
    )
    assert not invalid_type
    assert type_reasons == (
        "failure_mutation_field_type_invalid:"
        "invalid:pair_negative_count",
    )
    assert not missing_field
    assert missing_reasons == (
        "pair_policy_mutation_field_missing:invalid:unknown_field",
    )


@pytest.mark.parametrize(
    "failure_case,expected_fields",
    (
        ("checkpoint_width_changed_from_10", {"checkpoint_atom_feature_width": 11}),
        ("generation_fixed_masks_overlap", {"generation_fixed_masks_disjoint": False}),
        ("generation_fixed_masks_incomplete", {"generation_fixed_masks_exhaustive": False}),
        ("target_context_masks_overlap", {"target_context_masks_disjoint": False}),
        ("c_minimal_seed_or_anchor_incorrectly_generated", {"c_seed_override_marked_resolved": True}),
        ("target_residue_membership_empty", {"target_residue_membership_nonempty": False}),
        ("pair_candidate_includes_cross_sample_atoms", {"pair_candidates_same_sample": False}),
        ("pair_candidate_includes_h", {"pair_candidates_retained_heavy": False}),
        ("pair_candidate_includes_non_target_residue_pocket_atom", {"pair_candidates_target_residue_only": False}),
        ("pair_local_flat_index_mismatch", {"pair_local_flat_indices_valid": False}),
        ("contrastive_loss_enabled_with_no_negative", {"pair_negative_count": 0}),
        ("geometry_unit_or_periodicity_missing", {"geometry_units_and_periodicity_valid": False}),
        ("missing_geometry_label_participates_in_loss", {"missing_geometry_excluded_from_loss": False}),
        ("warhead_vocabulary_unresolved_but_marked_designed", {"warhead_contract_marked_resolved": True}),
        ("execution_boundary_crossed", {"tensor_materialization_requested": True}),
    ),
)
def test_required_failure_cases_expose_actual_mutated_state(
    failure_case: str,
    expected_fields: dict[str, object],
) -> None:
    assert contract.FAILURE_MUTATIONS[failure_case]["fields"] == expected_fields


def test_lower_contract_validators_are_state_driven() -> None:
    assert contract.validate_checkpoint_sidecar_boundary_v1(
        contract.BASELINE_SCENARIO
    ).valid
    assert not contract.validate_task_mask_partition_v1(
        contract.BASELINE_SCENARIO
    ).resolved
    assert contract.validate_target_residue_condition_contract_v1(
        contract.BASELINE_SCENARIO
    ).resolved
    geometry = contract.validate_geometry_component_contract_v1(
        contract.BASELINE_SCENARIO
    )
    assert geometry.valid and not geometry.resolved
    auxiliary = contract.validate_auxiliary_label_and_loss_mask_contract_v1(
        contract.BASELINE_SCENARIO
    )
    assert auxiliary.valid and not auxiliary.resolved


def test_deterministic_decision_serialization_and_evidence_three_times() -> None:
    builds = [
        contract.build_covapie_tensor_label_and_loss_mask_contract_design_artifacts_v1(
            ROOT
        )
        for _ in range(3)
    ]
    assert builds[0] == builds[1] == builds[2]
    decisions = [
        contract.derive_covapie_tensor_label_and_loss_mask_contract_design_v1(
            ROOT
        )["decision"]
        for _ in range(3)
    ]
    assert decisions[0] == decisions[1] == decisions[2]
    serialized = [
        contract.serialize_covapie_tensor_label_and_loss_mask_contract_design_decision_v1(
            decision
        )
        for decision in decisions
    ]
    assert serialized[0] == serialized[1] == serialized[2]


def test_checked_evidence_bytes_match_builder() -> None:
    for name, payload in _artifacts().items():
        assert (ROOT / contract.OUTPUT_ROOT / name).read_bytes() == payload


def test_manifest_evidence_sha_and_no_self_hash() -> None:
    import hashlib

    manifest = _manifest()
    assert contract.MANIFEST_FILE not in manifest["evidence_sha256"]
    for name, expected in manifest["evidence_sha256"].items():
        assert hashlib.sha256(_artifacts()[name]).hexdigest() == expected


def test_v3_hardening_manifest_flags_and_exact_counts() -> None:
    manifest = _manifest()
    for field in (
        "pair_builder_zero_negative_pair_head_supported",
        "pair_contrastive_mask_false_when_zero_negative",
        "pair_candidate_sample_spec_exact_types_verified",
        "contract_scenario_exact_scalar_types_verified",
        "pair_policy_scenario_exact_scalar_types_verified",
        "boolean_rejected_for_integer_index_and_count_fields",
        "failure_mutation_registry_exact_types_verified",
        "pair_policy_mutation_registry_exact_types_verified",
    ):
        assert manifest[field] is True
    assert manifest["contract_registry_row_count"] == 48
    assert manifest["failure_matrix_row_count"] == 40
    assert manifest["pair_policy_matrix_row_count"] == 16
    assert manifest["issue_inventory_row_count"] == 35


def test_v4_public_index_helper_manifest_flags() -> None:
    manifest = _manifest()
    for field in (
        "offset_terminal_count_exact_int_verified",
        "offset_elements_exact_int_verified",
        "flatten_local_index_exact_int_verified",
        "canonical_task_id_exact_int_verified",
        "public_index_helpers_exact_scalar_types_verified",
        "boolean_rejected_across_all_public_index_helpers",
    ):
        assert manifest[field] is True


def test_v5_count_and_offset_manifest_flags() -> None:
    manifest = _manifest()
    for field in (
        "pair_positive_count_nonnegative_verified",
        "pair_negative_count_nonnegative_verified",
        "negative_pair_count_rejected_when_contrastive_disabled",
        "negative_count_reason_semantics_frozen",
        "offset_container_ordered_sequence_verified",
        "unordered_offset_containers_rejected",
        "single_pass_offset_iterables_rejected",
        "binary_offset_containers_rejected",
    ):
        assert manifest[field] is True
    assert manifest["contract_registry_row_count"] == 48
    assert manifest["failure_matrix_row_count"] == 40
    assert manifest["pair_policy_matrix_row_count"] == 16
    assert manifest["issue_inventory_row_count"] == 35


def test_readiness_and_five_module_boundary() -> None:
    decision = _result()["decision"]
    manifest = _manifest()
    assert not decision.tensor_label_loss_mask_contract_designed
    assert not decision.ready_for_tensor_materialization_smoke
    assert not decision.ready_for_tensorization
    assert not decision.ready_for_model_integration
    assert not decision.ready_for_training
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert decision.recommended_next_step == (
        "resolve_covapie_condition_and_task_mask_tensor_contract_gaps_v1"
    )


def test_metadata_only_boundary() -> None:
    manifest = _manifest()
    for field in (
        "tensor_materialized",
        "npz_created",
        "tensor_materialization_used",
        "runtime_enforcement_integrated",
        "checkpoint_access",
        "model_changed",
        "dataloader_changed",
        "forward_changed",
        "loss_changed",
        "training_used",
        "raw_read",
        "raw_write",
        "provider_used",
        "network_used",
        "download_used",
    ):
        assert manifest[field] is False


def test_exact10_paths_modes_and_safety() -> None:
    assert len(checker.EXACT10) == len(set(checker.EXACT10)) == 10
    for relative in checker.EXACT10:
        path = ROOT / relative
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_mode & 0o777 == 0o644
        assert path.suffix.lower() not in checker.FORBIDDEN_SUFFIXES
        assert path.stat().st_size < 100 * 1024 * 1024


def test_checker_stdout_is_byte_identical() -> None:
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
        assert _result()["decision"].outcome == "designed_with_blockers"
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
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
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
            summary = targeted.stdout.decode().strip().splitlines()[-1]
            targeted_pass_counts.append(int(summary.split()[0]))
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
    assert targeted_pass_counts[0] == targeted_pass_counts[1] == targeted_pass_counts[2]
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == contract.BASE_COMMIT
    assert report.candidate_subject == contract.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified
