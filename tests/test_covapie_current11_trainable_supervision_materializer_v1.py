from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

from dataset import ProcessedLigandPocketDataset
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge,
)
from covalent_ext import covapie_current11_task2_runtime_caller_v1 as caller
from covalent_ext import (
    covapie_current11_trainable_supervision_materializer_v1 as materializer,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    AUTHORITATIVE_SUPERVISION_SCHEMA_V1,
    FORMAL_CARRIER_FEATURE_BINDING_SCHEMA_V1,
    _FORMAL_CARRIER_FEATURE_BINDING_FIELDS_V1,
    _REQUIRED_AUTHORITY_FIELDS,
    _RUNTIME_DERIVED_FORBIDDEN_INPUTS,
)
from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import (
    CHECKPOINT_CHANNEL_ORDER,
    CHECKPOINT_TOKEN_TO_INDEX,
)
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)
from scripts import check_covapie_current11_task2_runtime_caller_v1 as caller_checker


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
ERROR = materializer.MATERIALIZER_ERROR
STRUCTURE_AID = (
    STATE / "manual-review-aids/"
    "current11-trainable-supervision-role-seed-v1-structure-aids"
)
BOND_AUTHORITY = (
    ROOT / "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_parent_and_observed_projected_bond_authority.csv"
)
ATOM_MAPPING_AUTHORITY = (
    ROOT / "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
NONRETAINED_ENDPOINT = "NOT_RETAINED_NOT_PRESENT_IN_OBSERVED_SOURCE"
PACKET_NAMES = {
    "README.md",
    "current11_role_seed_review_worklist.csv",
    "current11_role_seed_atom_evidence.csv",
    "current11_role_seed_review_decisions.csv",
}


def _environment() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": "src:.",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


@pytest.fixture(scope="module")
def actual_bundle() -> dict[str, object]:
    remap_context, acquisition = bridge_checker._acquire_remap_context(
        lifecycle="precommit-untracked",
        repo_root=ROOT,
        state_root=STATE,
    )
    assert acquisition["test_harness_only"] is True
    assert acquisition["real_public_remap_context_build_performed"] is False
    assert acquisition["predecessor_public_call_counts"] == {
            "reconciliation": 1,
            "successor": 1,
            "B2": 1,
    }
    assert acquisition["formal_before_after_call_count"] == 2
    assert acquisition["production_monkeypatch_used"] is False
    assert acquisition["patch_restoration_passed"] is True
    assert acquisition["private_fixture_builder_patch_restoration_passed"] is True
    compiler_context = (
        bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap_context,
        )
    )
    dataset = ProcessedLigandPocketDataset(
        STATE / caller_checker._FORMAL_CARRIER, center=False
    )
    batch = dataset.collate_fn([dataset[index] for index in range(11)])
    runtime = caller.run_covapie_current11_task2_runtime_caller_v1(
        batch=batch,
        remap_context=remap_context,
        compiler_context=compiler_context,
    )
    assert runtime["runtime_status"] == "full_success"
    payload = materializer.load_covapie_current11_machine_authority_payload_v1(
        repo_root=ROOT,
        state_root=STATE,
        runtime_output17=runtime["remap_output17_or_none"],
    )
    result = materializer.build_current11_training_supervision_v1(
        authority_payload=payload
    )
    return {
        "batch": batch,
        "runtime": runtime,
        "payload": payload,
        "result": result,
    }


def _payload(actual_bundle: dict[str, object]) -> dict[str, object]:
    value = copy.deepcopy(actual_bundle["payload"])
    assert type(value) is dict
    return value


def _samples(payload: dict[str, object]) -> list[dict[str, object]]:
    samples = payload["samples"]
    assert type(samples) is list
    return samples


def _gold(payload: dict[str, object]) -> dict[str, object]:
    result = copy.deepcopy(payload)
    for sample in _samples(result):
        ligand_nodes = sample["ligand_nodes"]
        assert type(ligand_nodes) is list and len(ligand_nodes) >= 5
        count = len(ligand_nodes)
        roles = [0, 0, 0, 1] + [2] * (count - 4)
        sample["role_authority"] = {
            "authority_class": "AUTHORITATIVE_HUMAN_GOLD",
            "role_ids": roles,
            "role_valid": [True] * count,
            "candidate_role_names": [""] * count,
            "proposal_only": False,
            "human_approved": True,
            "review_disposition": "approved_test_fixture_only",
            "reviewer_id": "unit-test-human-reviewer",
            "attestation": "Synthetic fixture approval; not Current11 authority.",
        }
        sample["seed_authority"] = {
            "authority_class": "AUTHORITATIVE_HUMAN_GOLD",
            "mask": [index == 3 for index in range(count)],
            "valid": True,
            "candidate_mask": [False] * count,
            "proposal_only": False,
            "human_approved": True,
            "review_disposition": "approved_test_fixture_only",
            "reviewer_id": "unit-test-human-reviewer",
            "attestation": "Synthetic fixture approval; not Current11 authority.",
        }
    return result


def _fails(action: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        action()
    assert captured.value.__cause__ is not None


def _build(payload: dict[str, object]) -> dict[str, object]:
    return materializer.build_current11_training_supervision_v1(
        authority_payload=payload
    )


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def test_public_api_exact_signatures_schema_and_silent_import() -> None:
    assert materializer.__all__ == (
        "CURRENT11_SAMPLE_KEYS_V1",
        "MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1",
        "TRAINABLE_SUPERVISION_MATERIALIZATION_SCHEMA_V1",
        "build_current11_role_seed_review_packet_v1",
        "build_current11_training_supervision_v1",
        "load_covapie_current11_machine_authority_payload_v1",
        "validate_authoritative_current11_training_supervision_v1",
        "write_current11_role_seed_review_packet_v1",
    )
    assert str(inspect.signature(materializer.build_current11_training_supervision_v1)) == (
        "(*, authority_payload: 'object') -> 'dict[str, object]'"
    )
    assert str(inspect.signature(
        materializer.validate_authoritative_current11_training_supervision_v1
    )) == "(*, authoritative_supervision: 'object') -> 'None'"
    with pytest.raises(TypeError):
        materializer.build_current11_training_supervision_v1({})
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import "
            "covapie_current11_trainable_supervision_materializer_v1",
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_actual_exact11_machine_truth_matrix_and_partial_admission(
    actual_bundle: dict[str, object],
) -> None:
    payload = actual_bundle["payload"]
    result = actual_bundle["result"]
    assert type(payload) is dict and type(result) is dict
    expected_keys = [
        f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
    ]
    assert payload["sample_order"] == expected_keys
    samples = _samples(payload)
    assert [sample["sample_key"] for sample in samples] == expected_keys
    assert [(sample["pdb_id"], sample["ligand_comp_id"]) for sample in samples] == [
        ("6BV6", "JUG"),
        ("6BV8", "JUG"),
        ("6BV5", "JUG"),
        ("1AEC", "E64"),
        ("1AIM", "ZYA"),
        ("1AU3", "PCM"),
        ("1AU4", "INP"),
        ("1AYU", "INA"),
        ("1AYV", "IN6"),
        ("1AYW", "IN3"),
        ("1B02", "UFP"),
    ]
    assert [len(sample["ligand_nodes"]) for sample in samples] == [
        13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21,
    ]
    assert [len(sample["pocket_nodes"]) for sample in samples] == [
        66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228,
    ]
    assert [sample["split"] for sample in samples] == [
        "train", "train", "train", "val", "val", "train",
        "train", "train", "train", "train", "test",
    ]
    summary = result["summary"]
    assert summary == {
        "sample_count": 11,
        "target_residue_membership_count": 11,
        "target_reactive_atom_consistency_count": 11,
        "positive_pair_consistency_count": 11,
        "supported_atom_sample_count": 11,
        "unsupported_atom_count": 0,
        "split_binding_count": 11,
        "observed_geometry_count": 11,
        "pre_geometry_authoritative_count": 0,
        "post_geometry_authoritative_count": 0,
        "exact3_role_human_gold_count": 0,
        "minimal_seed_human_gold_count": 0,
        "real_admitted_sample_count": 0,
        "checkpoint_channel_order": "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9",
    }
    source = result["authoritative_supervision"]
    assert source["schema_version"] == AUTHORITATIVE_SUPERVISION_SCHEMA_V1
    assert set(source) == _REQUIRED_AUTHORITY_FIELDS
    assert not set(source) & _RUNTIME_DERIVED_FORBIDDEN_INPUTS
    assert source["ligand_node_offsets"][-1] == 323
    assert source["pocket_node_offsets"][-1] == 2202
    binding = source["formal_carrier_feature_binding"]
    assert set(binding) == _FORMAL_CARRIER_FEATURE_BINDING_FIELDS_V1
    assert binding["schema_version"] == FORMAL_CARRIER_FEATURE_BINDING_SCHEMA_V1
    assert binding["checkpoint_channel_order"] == CHECKPOINT_CHANNEL_ORDER
    ligand_nodes = [
        node for sample in samples for node in sample["ligand_nodes"]
    ]
    pocket_nodes = [
        node for sample in samples for node in sample["pocket_nodes"]
    ]
    assert len(binding["ligand_source_row_index"]) == len(ligand_nodes) == 323
    assert len(binding["pocket_source_row_index"]) == len(pocket_nodes) == 2202
    assert binding["ligand_source_row_index"] == [
        node["source_row_index"] for node in ligand_nodes
    ]
    assert binding["pocket_source_row_index"] == [
        node["source_row_index"] for node in pocket_nodes
    ]
    assert binding["ligand_parser_local_index"] == [
        node["parser_local_index"] for node in ligand_nodes
    ]
    assert binding["pocket_parser_local_index"] == [
        node["parser_local_index"] for node in pocket_nodes
    ]
    assert binding["ligand_checkpoint_channel_index"] == [
        CHECKPOINT_TOKEN_TO_INDEX[node["element"]] for node in ligand_nodes
    ]
    assert binding["pocket_checkpoint_channel_index"] == [
        CHECKPOINT_TOKEN_TO_INDEX[node["element"]] for node in pocket_nodes
    ]
    assert source["sample_training_admitted"] == [False] * 11
    assert all(record["training_admission_blockers"] == [
        "EXACT3_ROLE_HUMAN_GOLD_MISSING",
        "MINIMAL_SEED_HUMAN_GOLD_MISSING",
    ] for record in result["reconciliation_records"])
    materializer.validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=source
    )


def test_target_membership_reactive_sg_strict_subset_and_positive_triangle(
    actual_bundle: dict[str, object],
) -> None:
    result = actual_bundle["result"]
    payload = actual_bundle["payload"]
    runtime = actual_bundle["runtime"]
    assert type(result) is dict and type(payload) is dict and type(runtime) is dict
    source = result["authoritative_supervision"]
    output17 = runtime["remap_output17_or_none"]
    for index, sample in enumerate(_samples(payload)):
        pleft, pright = source["pocket_node_offsets"][index:index + 2]
        membership = source["target_residue_membership_mask"][pleft:pright]
        reactive = sample["target_reactive_pocket_local_index"]
        pair = sample["positive_pair"]
        assert sum(membership) == 6
        assert membership[reactive] is True
        assert sample["pocket_nodes"][reactive]["atom_name"] == "SG"
        assert pair["pocket_local_index"] == reactive
        assert output17["pair_values_parser_local_indices"][index] == [
            reactive, pair["ligand_local_index"],
        ]
        assert output17["pair_values_batch_indices"][index] == [
            pair["output17_pocket_flat_index"],
            pair["output17_ligand_flat_index"],
        ]


def test_actual_exact10_features_ordering_geometry_and_candidate_authority(
    actual_bundle: dict[str, object],
) -> None:
    payload = actual_bundle["payload"]
    assert type(payload) is dict
    assert CHECKPOINT_CHANNEL_ORDER == "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    allowed = {"C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"}
    all_nodes = []
    for sample in _samples(payload):
        all_nodes.extend(sample["ligand_nodes"])
        all_nodes.extend(sample["pocket_nodes"])
        assert sample["role_authority"]["authority_class"] == "CANDIDATE_ONLY"
        assert sample["role_authority"]["proposal_only"] is True
        assert sample["role_authority"]["human_approved"] is False
        assert sample["seed_authority"]["human_approved"] is False
        assert sample["observed_complex_pair_distance_valid"] is True
        assert sample["pre_post_geometry_component_valid_mask"] == [False, False]
        assert sample["pre_post_geometry_component_loss_mask"] == [False, False]
        assert all(value != value for value in sample["pre_post_geometry_target_angstrom"])
    assert len(all_nodes) == 2525
    assert all(node["element"] in allowed and node["element"] != "H" for node in all_nodes)
    assert all(len(node["one_hot"]) == 10 and sum(node["one_hot"]) == 1.0 for node in all_nodes)


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_residue_membership",
        "reactive_not_membership",
        "positive_pair_local_mismatch",
        "positive_pair_source_mismatch",
        "retained_local_mismatch",
        "parser_local_mismatch",
    ),
)
def test_identity_membership_pair_and_index_mismatches_fail_closed(
    actual_bundle: dict[str, object], mutation: str,
) -> None:
    payload = _payload(actual_bundle)
    sample = _samples(payload)[0]
    if mutation == "wrong_residue_membership":
        sample["target_residue"]["auth_seq_id"] = "999999"
    elif mutation == "reactive_not_membership":
        sample["target_reactive_pocket_local_index"] = 0
    elif mutation == "positive_pair_local_mismatch":
        sample["positive_pair"]["ligand_local_index"] = 0
    elif mutation == "positive_pair_source_mismatch":
        sample["positive_pair"]["ligand_source_row_index"] += 1
    elif mutation == "retained_local_mismatch":
        sample["ligand_nodes"][0]["retained_local_index"] = 1
    else:
        sample["pocket_nodes"][0]["parser_local_index"] = 1
    _fails(lambda: _build(payload))


@pytest.mark.parametrize(
    ("element", "one_hot"),
    (
        ("Xe", [1.0] + [0.0] * 9),
        ("H", [1.0] + [0.0] * 9),
        ("", [1.0] + [0.0] * 9),
        ("C", [0.0, 1.0] + [0.0] * 8),
        ("C", [1.0, 1.0] + [0.0] * 8),
        ("C", [1.0] + [0.0] * 8),
    ),
)
def test_unsupported_hydrogen_missing_and_exact10_corruption_fail_closed(
    actual_bundle: dict[str, object], element: str, one_hot: list[float],
) -> None:
    payload = _payload(actual_bundle)
    node = _samples(payload)[0]["ligand_nodes"][0]
    node["element"] = element
    node["one_hot"] = one_hot
    _fails(lambda: _build(payload))


@pytest.mark.parametrize(
    "mutation",
    (
        "role_overlap_encoding",
        "role_incomplete",
        "role_empty_class",
        "fourth_role",
    ),
)
def test_exact3_role_partition_failures(
    actual_bundle: dict[str, object], mutation: str,
) -> None:
    payload = _gold(_payload(actual_bundle))
    authority = _samples(payload)[0]["role_authority"]
    if mutation == "role_overlap_encoding":
        authority["role_ids"][0] = [0, 1]
    elif mutation == "role_incomplete":
        authority["role_valid"][0] = False
        authority["role_ids"][0] = -1
    elif mutation == "role_empty_class":
        authority["role_ids"] = [0] * 3 + [2] * (len(authority["role_ids"]) - 3)
    else:
        authority["role_ids"][0] = 3
    _fails(lambda: _build(payload))


@pytest.mark.parametrize(
    ("forbidden_name", "forbidden_value"),
    (
        ("seed_role_id", 3),
        ("canonical_seed_mask", [False]),
        ("canonical_task_id", 0),
        ("canonical_task_valid", True),
        ("ligand_base_generation_mask", [True]),
        ("ligand_base_fixed_mask", [False]),
        ("ligand_active_diffusion_loss_mask", [True]),
        ("anchor_distance_target", 1.0),
    ),
)
def test_seed_role_sixth_mask_and_runtime_derived_inputs_forbidden(
    actual_bundle: dict[str, object], forbidden_name: str, forbidden_value: object,
) -> None:
    payload = _payload(actual_bundle)
    _samples(payload)[0][forbidden_name] = forbidden_value
    _fails(lambda: _build(payload))


def test_observed_geometry_never_substituted_and_split_mismatch_fails(
    actual_bundle: dict[str, object],
) -> None:
    observed_substitution = _payload(actual_bundle)
    sample = _samples(observed_substitution)[0]
    observed = sample["observed_complex_pair_distance_angstrom"]
    sample["pre_post_geometry_target_angstrom"] = [observed, float("nan")]
    _fails(lambda: _build(observed_substitution))

    split_mismatch = _payload(actual_bundle)
    _samples(split_mismatch)[0]["split"] = "test"
    _fails(lambda: _build(split_mismatch))


def test_candidate_only_role_and_seed_cannot_admit(
    actual_bundle: dict[str, object],
) -> None:
    actual = _build(_payload(actual_bundle))
    assert actual["authoritative_supervision"]["sample_training_admitted"] == [False] * 11

    gold_roles_candidate_seed = _gold(_payload(actual_bundle))
    first = _samples(gold_roles_candidate_seed)[0]
    count = len(first["ligand_nodes"])
    first["seed_authority"] = {
        "authority_class": "CANDIDATE_ONLY",
        "mask": [False] * count,
        "valid": False,
        "candidate_mask": [True, True] + [False] * (count - 2),
        "proposal_only": True,
        "human_approved": False,
        "review_disposition": "candidate_only_test_fixture",
        "reviewer_id": "",
        "attestation": "",
    }
    result = _build(gold_roles_candidate_seed)
    assert result["authoritative_supervision"]["sample_training_admitted"][0] is False
    assert result["summary"]["exact3_role_human_gold_count"] == 11
    assert result["summary"]["minimal_seed_human_gold_count"] == 10


@pytest.mark.parametrize(
    ("approved", "reviewer", "attestation"),
    (
        (False, "unit-test-human-reviewer", "Synthetic fixture."),
        (True, "", "Synthetic fixture."),
        (True, "codex", "Synthetic fixture."),
        (True, "chatgpt-reviewer", "Synthetic fixture."),
        (True, "unit-test-human-reviewer", ""),
    ),
)
def test_human_approval_and_no_self_approval_required(
    actual_bundle: dict[str, object],
    approved: bool,
    reviewer: str,
    attestation: str,
) -> None:
    payload = _gold(_payload(actual_bundle))
    authority = _samples(payload)[0]["role_authority"]
    authority["human_approved"] = approved
    authority["reviewer_id"] = reviewer
    authority["attestation"] = attestation
    _fails(lambda: _build(payload))


def test_seed_is_nonempty_role_orthogonal_conditioning_sidecar(
    actual_bundle: dict[str, object],
) -> None:
    empty = _gold(_payload(actual_bundle))
    sample = _samples(empty)[0]
    sample["seed_authority"]["mask"] = [False] * len(sample["ligand_nodes"])
    _fails(lambda: _build(empty))

    one_linker_atom = _gold(_payload(actual_bundle))
    result = _build(one_linker_atom)
    source = result["authoritative_supervision"]
    assert source["ligand_minimal_seed_or_anchor_valid"] == [True] * 11
    materializer.validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=source
    )

    more_than_three_across_roles = _gold(_payload(actual_bundle))
    sample = _samples(more_than_three_across_roles)[0]
    sample["seed_authority"]["mask"] = [True] * len(sample["ligand_nodes"])
    result = _build(more_than_three_across_roles)
    materializer.validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=result["authoritative_supervision"]
    )


def test_full_formally_approved_synthetic_fixture_success(
    actual_bundle: dict[str, object],
) -> None:
    result = _build(_gold(_payload(actual_bundle)))
    summary = result["summary"]
    assert summary["exact3_role_human_gold_count"] == 11
    assert summary["minimal_seed_human_gold_count"] == 11
    assert summary["real_admitted_sample_count"] == 11
    source = result["authoritative_supervision"]
    assert source["sample_training_admitted"] == [True] * 11
    assert source["ligand_minimal_seed_or_anchor_valid"] == [True] * 11
    assert set(source["ligand_role_id"]) == {0, 1, 2}
    materializer.validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=source
    )


def test_review_packet_is_deterministic_complete_and_candidate_only(
    actual_bundle: dict[str, object],
) -> None:
    payload = _payload(actual_bundle)
    result = _build(copy.deepcopy(payload))
    first = materializer.build_current11_role_seed_review_packet_v1(
        authority_payload=payload, materialization=result
    )
    second = materializer.build_current11_role_seed_review_packet_v1(
        authority_payload=copy.deepcopy(payload),
        materialization=_build(copy.deepcopy(payload)),
    )
    assert first == second
    assert set(first) == PACKET_NAMES
    worklist = _csv_rows(first["current11_role_seed_review_worklist.csv"])
    evidence = _csv_rows(first["current11_role_seed_atom_evidence.csv"])
    decisions = _csv_rows(first["current11_role_seed_review_decisions.csv"])
    assert len(worklist) == 11
    assert len(evidence) == len(decisions) == 323
    assert all(row["proposal_only"] == "true" for row in worklist + evidence)
    assert all(row["human_approved"] == "false" for row in worklist + evidence)
    assert all(row["training_authorized"] == "false" for row in worklist + evidence)
    assert all(
        row["reviewer_id"] == row["review_decision"]
        == row["review_timestamp"] == row["attestation"] == ""
        for row in decisions
    )
    assert b"seed/anchor is a separate, role-orthogonal" in first["README.md"]
    assert b"there is no exact-cardinality" in first["README.md"]
    assert b"neither a fourth role nor a sixth mask" in first["README.md"]
    assert hashlib.sha256(first["README.md"]).hexdigest() == hashlib.sha256(
        second["README.md"]
    ).hexdigest()


def test_review_packet_writer_exact_modes_and_no_overwrite(
    actual_bundle: dict[str, object], tmp_path: Path,
) -> None:
    payload = _payload(actual_bundle)
    result = _build(copy.deepcopy(payload))
    packet = materializer.build_current11_role_seed_review_packet_v1(
        authority_payload=payload, materialization=result
    )
    output = tmp_path / "current11-trainable-supervision-role-seed-v1"
    written = materializer.write_current11_role_seed_review_packet_v1(
        packet_files=packet, output_dir=output
    )
    assert {path.name for path in written} == PACKET_NAMES
    assert stat.S_IMODE(output.stat().st_mode) == 0o755
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o644 for path in written)
    assert {path.name: path.read_bytes() for path in written} == packet
    _fails(lambda: materializer.write_current11_role_seed_review_packet_v1(
        packet_files=packet, output_dir=output
    ))


def test_output_validator_rejects_forged_runtime_source_and_admission(
    actual_bundle: dict[str, object],
) -> None:
    result = actual_bundle["result"]
    assert type(result) is dict
    extra = copy.deepcopy(result["authoritative_supervision"])
    extra["canonical_task_id"] = [0] * 11
    _fails(lambda: materializer.validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=extra
    ))

    forged = copy.deepcopy(result["authoritative_supervision"])
    forged["sample_training_admitted"][0] = True
    _fails(lambda: materializer.validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=forged
    ))


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_binding",
        "wrong_schema",
        "extra_binding_field",
        "channel_order_drift",
        "wrong_vector_length",
        "negative_source_index",
        "duplicate_parser_local",
        "channel_below_zero",
        "channel_above_nine",
    ),
)
def test_output_validator_rejects_invalid_formal_carrier_feature_binding(
    actual_bundle: dict[str, object], mutation: str,
) -> None:
    result = actual_bundle["result"]
    assert type(result) is dict
    source = copy.deepcopy(result["authoritative_supervision"])
    if mutation == "missing_binding":
        del source["formal_carrier_feature_binding"]
    else:
        binding = source["formal_carrier_feature_binding"]
        if mutation == "wrong_schema":
            binding["schema_version"] = "wrong"
        elif mutation == "extra_binding_field":
            binding["unexpected"] = []
        elif mutation == "channel_order_drift":
            binding["checkpoint_channel_order"] = "N:0|C:1"
        elif mutation == "wrong_vector_length":
            binding["ligand_source_row_index"].pop()
        elif mutation == "negative_source_index":
            binding["pocket_source_row_index"][0] = -1
        elif mutation == "duplicate_parser_local":
            binding["ligand_parser_local_index"][1] = 0
        elif mutation == "channel_below_zero":
            binding["ligand_checkpoint_channel_index"][0] = -1
        else:
            binding["pocket_checkpoint_channel_index"][0] = 10
    _fails(lambda: materializer.validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=source
    ))


def test_offline_loader_rejects_output17_positive_pair_corruption(
    actual_bundle: dict[str, object],
) -> None:
    runtime = copy.deepcopy(actual_bundle["runtime"])
    output17 = runtime["remap_output17_or_none"]
    output17["pair_values_batch_indices"][0][1] += 1
    _fails(lambda: materializer.load_covapie_current11_machine_authority_payload_v1(
        repo_root=ROOT,
        state_root=STATE,
        runtime_output17=output17,
    ))


def test_external_structure_aid_is_complete_traceable_and_not_gold() -> None:
    output_path = STRUCTURE_AID / "current11_role_seed_bond_evidence.csv"
    atlas_path = STRUCTURE_AID / "current11_role_seed_structure_atlas.html"
    output = _csv_rows(output_path.read_bytes())
    authority = _csv_rows(BOND_AUTHORITY.read_bytes())
    mappings = _csv_rows(ATOM_MAPPING_AUTHORITY.read_bytes())
    mapping_by_atom = {
        (row["sample_index_row_id"], row["parent_ccd_atom_id"]): row
        for row in mappings
    }
    assert len(output) == len(authority) == 337
    assert len(mapping_by_atom) == len(mappings) == 323
    missing_endpoint_count = 0
    for evidence, source in zip(output, authority):
        assert (
            evidence["sample_key"],
            evidence["pdb_id"],
            evidence["ligand_comp_id"],
            evidence["atom_a_name"],
            evidence["atom_b_name"],
            evidence["bond_order"],
            evidence["projection_disposition"],
            evidence["component_parent_graph_sha256"],
            evidence["observed_graph_sha256"],
            evidence["source_verified"],
        ) == (
            source["sample_index_row_id"],
            source["pdb_id"],
            source["ligand_comp_id"],
            source["parent_ccd_atom_id_1"],
            source["parent_ccd_atom_id_2"],
            source["normalized_bond_order"],
            source["projection_disposition"],
            source["component_parent_graph_sha256"],
            source["observed_graph_sha256"],
            source["verified"],
        )
        for suffix, atom_name in (
            ("a", evidence["atom_a_name"]),
            ("b", evidence["atom_b_name"]),
        ):
            mapping = mapping_by_atom.get((evidence["sample_key"], atom_name))
            retained = evidence[
                f"atom_{suffix}_retained_heavy_local_index_0based"
            ]
            source_row = evidence[f"atom_{suffix}_source_row_index_0based"]
            if mapping is None:
                assert retained == source_row == NONRETAINED_ENDPOINT
                missing_endpoint_count += 1
            else:
                assert retained == mapping["retained_heavy_local_index_0based"]
                assert source_row == mapping["source_full_atom_row_index"]
    assert missing_endpoint_count == 1
    assert stat.S_IMODE(STRUCTURE_AID.stat().st_mode) == 0o755
    assert stat.S_IMODE(output_path.stat().st_mode) == 0o644
    assert stat.S_IMODE(atlas_path.stat().st_mode) == 0o644
    atlas = atlas_path.read_bytes()
    assert atlas.count(b'class="sample"') == 11
    assert atlas.count(b"seed proposal: NONE") == 11
    assert atlas.count(b"NOT GOLD") >= 22
    assert b"No bonds are inferred from XYZ" in atlas


def test_source_has_no_hot_path_git_subprocess_network_rdkit_checkpoint_or_training() -> None:
    source = inspect.getsource(materializer)
    hot_path = inspect.getsource(materializer._build_impl)
    assert "import subprocess" not in source
    assert "import rdkit" not in source.casefold()
    assert "torch.load" not in source
    assert "requests." not in source
    assert "optimizer" not in source.casefold()
    assert "backward(" not in source
    assert "subprocess." not in source
    assert "open(" not in hot_path
