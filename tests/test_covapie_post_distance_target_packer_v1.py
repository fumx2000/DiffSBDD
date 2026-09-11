from __future__ import annotations

import copy
from dataclasses import fields

import pytest
import torch

from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    AUTHORITATIVE_SUPERVISION_SCHEMA_V1,
    FORMAL_CARRIER_FEATURE_BINDING_SCHEMA_V1,
    tensorize_covapie_current11_training_supervision_v1,
)
from covalent_ext.covapie_post_distance_target_packer_v1 import (
    COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR,
    CovapiePostDistanceTargetPackV1,
    pack_covapie_post_distance_targets_v1,
)
from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import (
    CHECKPOINT_CHANNEL_ORDER,
)


SYNTHETIC_EVENT_IDS = (
    "SYNTHETIC_EVENT_A",
    "SYNTHETIC_EVENT_B",
    "SYNTHETIC_EVENT_C",
)


def _assert_packer_error(reason: str, *, event_ids: object, values: object) -> None:
    message = f"{COVAPIE_POST_DISTANCE_TARGET_PACKER_V1_ERROR}:{reason}"
    with pytest.raises(ValueError, match=f"^{message}$"):
        pack_covapie_post_distance_targets_v1(
            event_ids=event_ids,  # type: ignore[arg-type]
            post_distance_by_event=values,  # type: ignore[arg-type]
        )


def _tensorizer_fixture(
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    sample_keys = [
        "CYS_SG_SAMPLE_INDEX_000001",
        "CYS_SG_SAMPLE_INDEX_000002",
    ]
    batch: dict[str, object] = {
        "names": sample_keys[:],
        "lig_coords": torch.tensor([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [2.0, 1.0, 0.0],
        ]),
        "pocket_coords": torch.tensor([
            [2.0, 0.0, 1.0],
            [3.0, 0.0, 0.0],
            [2.0, 1.0, 1.0],
            [3.0, 1.0, 0.0],
        ]),
        "lig_one_hot": torch.eye(10)[torch.tensor([0, 1, 2, 0, 1, 2])],
        "pocket_one_hot": torch.eye(10)[torch.tensor([3, 0, 3, 0])],
        "lig_source_row_index": torch.tensor(
            [10, 11, 12, 20, 21, 22], dtype=torch.int64
        ),
        "pocket_source_row_index": torch.tensor(
            [30, 31, 40, 41], dtype=torch.int64
        ),
        "lig_parser_local_index": torch.tensor(
            [0, 1, 2, 0, 1, 2], dtype=torch.int64
        ),
        "pocket_parser_local_index": torch.tensor(
            [0, 1, 0, 1], dtype=torch.int64
        ),
        "num_lig_atoms": torch.tensor([3, 3], dtype=torch.long),
        "num_pocket_nodes": torch.tensor([2, 2], dtype=torch.long),
        "lig_mask": torch.tensor([0, 0, 0, 1, 1, 1], dtype=torch.float32),
        "pocket_mask": torch.tensor([0, 0, 1, 1], dtype=torch.float32),
    }
    runtime: dict[str, object] = {
        "runtime_status": "full_success",
        "batch_sample_keys_or_none": sample_keys[:],
        "remap_output17_or_none": {
            "batch_sample_order": [
                {
                    "sample_index_row_id": sample_keys[0],
                    "sample_preparation_input_id": "SYNTHETIC_PREP_000001",
                    "pdb_id": "1AAA",
                    "ligand_comp_id": "L01",
                },
                {
                    "sample_index_row_id": sample_keys[1],
                    "sample_preparation_input_id": "SYNTHETIC_PREP_000002",
                    "pdb_id": "2BBB",
                    "ligand_comp_id": "L02",
                },
            ],
            "pair_values_parser_local_indices": [[0, 2], [0, 2]],
            "pair_values_batch_indices": [[0, 2], [2, 5]],
            "pair_values_joint_global_indices": None,
            "pair_sample_indices": [0, 1],
            "sample_pair_offsets": [0, 1, 2],
            "entry_validity": [True, True],
            "sample_validity": [True, True],
            "remap_status": "REMAPPED_EXACT",
            "failure_reason": "NONE",
        },
    }
    batch["covapie_current11_task2_runtime_result_v1"] = runtime
    authority: dict[str, object] = {
        "schema_version": AUTHORITATIVE_SUPERVISION_SCHEMA_V1,
        "sample_keys": sample_keys[:],
        "formal_carrier_feature_binding": {
            "schema_version": FORMAL_CARRIER_FEATURE_BINDING_SCHEMA_V1,
            "checkpoint_channel_order": CHECKPOINT_CHANNEL_ORDER,
            "ligand_source_row_index": [10, 11, 12, 20, 21, 22],
            "pocket_source_row_index": [30, 31, 40, 41],
            "ligand_parser_local_index": [0, 1, 2, 0, 1, 2],
            "pocket_parser_local_index": [0, 1, 0, 1],
            "ligand_checkpoint_channel_index": [0, 1, 2, 0, 1, 2],
            "pocket_checkpoint_channel_index": [3, 0, 3, 0],
        },
        "ligand_node_offsets": [0, 3, 6],
        "pocket_node_offsets": [0, 2, 4],
        "ligand_role_id": [0, 1, 2, 0, 1, 2],
        "ligand_role_valid": [True] * 6,
        "ligand_minimal_seed_or_anchor_mask": [
            True, False, False, True, False, False,
        ],
        "ligand_minimal_seed_or_anchor_valid": [True, True],
        "sample_training_admitted": [True, True],
        "target_residue_membership_mask": [True, True, True, True],
        "observed_complex_pair_distance_angstrom": [1.0, 1.0],
        "observed_complex_pair_distance_valid": [True, True],
        "pre_post_geometry_target_angstrom": [
            [float("nan"), float("nan")],
            [float("nan"), float("nan")],
        ],
        "pre_post_geometry_component_valid_mask": [
            [False, False], [False, False],
        ],
        "pre_post_geometry_component_loss_mask": [
            [False, False], [False, False],
        ],
    }
    return batch, runtime, authority


def test_post_only_pack_has_exact_cpu_shapes_dtypes_and_semantics() -> None:
    result = pack_covapie_post_distance_targets_v1(
        event_ids=SYNTHETIC_EVENT_IDS,
        post_distance_by_event={
            "SYNTHETIC_EVENT_A": 2.25,
            "SYNTHETIC_EVENT_B": 3.75,
            "SYNTHETIC_EVENT_C": None,
        },
    )

    assert result.event_ids == SYNTHETIC_EVENT_IDS
    assert result.pre_post_geometry_target_angstrom.shape == (3, 2)
    assert result.pre_post_geometry_target_angstrom.dtype == torch.float32
    assert result.pre_post_geometry_target_angstrom.device.type == "cpu"
    assert result.pre_post_geometry_component_valid_mask.shape == (3, 2)
    assert result.pre_post_geometry_component_valid_mask.dtype == torch.bool
    assert result.pre_post_geometry_component_valid_mask.device.type == "cpu"
    assert result.pre_post_geometry_component_loss_mask.shape == (3, 2)
    assert result.pre_post_geometry_component_loss_mask.dtype == torch.bool
    assert result.pre_post_geometry_component_loss_mask.device.type == "cpu"
    assert torch.isnan(result.pre_post_geometry_target_angstrom[:, 0]).all()
    assert torch.equal(
        result.pre_post_geometry_target_angstrom[:2, 1],
        torch.tensor([2.25, 3.75], dtype=torch.float32),
    )
    assert torch.isnan(result.pre_post_geometry_target_angstrom[2, 1])
    assert result.pre_post_geometry_component_valid_mask.tolist() == [
        [False, True], [False, True], [False, False],
    ]
    assert not result.pre_post_geometry_component_loss_mask.any()
    assert all(
        not tensor.requires_grad and tensor.grad_fn is None
        for tensor in (
            result.pre_post_geometry_target_angstrom,
            result.pre_post_geometry_component_valid_mask,
            result.pre_post_geometry_component_loss_mask,
        )
    )
    assert {field.name for field in fields(result)} == {
        "event_ids",
        "pre_post_geometry_target_angstrom",
        "pre_post_geometry_component_valid_mask",
        "pre_post_geometry_component_loss_mask",
    }
    assert not hasattr(result, "sample_training_admitted")
    assert not hasattr(result, "authority")


def test_event_order_and_mapping_insertion_order_are_independent() -> None:
    values = {
        "SYNTHETIC_EVENT_C": None,
        "SYNTHETIC_EVENT_A": 2.25,
        "SYNTHETIC_EVENT_B": 3.75,
    }
    result = pack_covapie_post_distance_targets_v1(
        event_ids=(
            "SYNTHETIC_EVENT_B",
            "SYNTHETIC_EVENT_C",
            "SYNTHETIC_EVENT_A",
        ),
        post_distance_by_event=values,
    )

    assert result.event_ids == (
        "SYNTHETIC_EVENT_B",
        "SYNTHETIC_EVENT_C",
        "SYNTHETIC_EVENT_A",
    )
    assert result.pre_post_geometry_target_angstrom[:, 1].tolist()[:1] == [3.75]
    assert torch.isnan(result.pre_post_geometry_target_angstrom[1, 1])
    assert result.pre_post_geometry_target_angstrom[2, 1].item() == 2.25
    assert result.pre_post_geometry_component_valid_mask[:, 1].tolist() == [
        True, False, True,
    ]
    assert torch.isnan(result.pre_post_geometry_target_angstrom[:, 0]).all()


def test_all_unknown_post_values_remain_nan_and_all_masks_false() -> None:
    result = pack_covapie_post_distance_targets_v1(
        event_ids=SYNTHETIC_EVENT_IDS,
        post_distance_by_event={event_id: None for event_id in SYNTHETIC_EVENT_IDS},
    )

    assert torch.isnan(result.pre_post_geometry_target_angstrom).all()
    assert not (result.pre_post_geometry_target_angstrom == 0).any()
    assert not result.pre_post_geometry_component_valid_mask.any()
    assert not result.pre_post_geometry_component_loss_mask.any()


@pytest.mark.parametrize(
    ("event_ids", "values", "reason"),
    (
        ((), {}, "EVENT_IDS_EMPTY"),
        ("SYNTHETIC_EVENT_A", {}, "EVENT_IDS_ORDERED_SEQUENCE_REQUIRED"),
        (
            ("SYNTHETIC_EVENT_A", "SYNTHETIC_EVENT_A"),
            {"SYNTHETIC_EVENT_A": 2.25},
            "EVENT_ID_DUPLICATE",
        ),
        (
            ("SYNTHETIC_EVENT_A",),
            {},
            "POST_DISTANCE_EVENT_KEY_MISSING",
        ),
        (
            ("SYNTHETIC_EVENT_A",),
            {"SYNTHETIC_EVENT_A": 2.25, "SYNTHETIC_EVENT_B": 3.75},
            "POST_DISTANCE_EVENT_KEY_EXTRA",
        ),
        ((1,), {1: 2.25}, "EVENT_ID_INVALID"),
        (("",), {"": 2.25}, "EVENT_ID_INVALID"),
        ((" SYNTHETIC_EVENT_A",), {" SYNTHETIC_EVENT_A": 2.25}, "EVENT_ID_INVALID"),
        (("SYNTHETIC\nEVENT_A",), {"SYNTHETIC\nEVENT_A": 2.25}, "EVENT_ID_INVALID"),
        (("SYNTHETIC_EVENT_A",), [("SYNTHETIC_EVENT_A", 2.25)], "POST_DISTANCE_MAPPING_REQUIRED"),
    ),
)
def test_invalid_event_collections_fail_with_specific_reason(
    event_ids: object, values: object, reason: str
) -> None:
    _assert_packer_error(reason, event_ids=event_ids, values=values)


@pytest.mark.parametrize(
    ("value", "reason"),
    (
        (True, "POST_DISTANCE_PYTHON_NUMBER_REQUIRED"),
        ("2.25", "POST_DISTANCE_PYTHON_NUMBER_REQUIRED"),
        (torch.tensor(2.25), "POST_DISTANCE_PYTHON_NUMBER_REQUIRED"),
        (float("nan"), "POST_DISTANCE_NOT_FINITE_POSITIVE"),
        (float("inf"), "POST_DISTANCE_NOT_FINITE_POSITIVE"),
        (-float("inf"), "POST_DISTANCE_NOT_FINITE_POSITIVE"),
        (0.0, "POST_DISTANCE_NOT_FINITE_POSITIVE"),
        (-2.25, "POST_DISTANCE_NOT_FINITE_POSITIVE"),
        (1.0e39, "POST_DISTANCE_FLOAT32_NOT_FINITE_POSITIVE"),
        (1.0e-50, "POST_DISTANCE_FLOAT32_NOT_FINITE_POSITIVE"),
    ),
)
def test_invalid_post_values_fail_with_specific_reason(
    value: object, reason: str
) -> None:
    _assert_packer_error(
        reason,
        event_ids=("SYNTHETIC_EVENT_A",),
        values={"SYNTHETIC_EVENT_A": value},
    )


def test_inputs_are_unchanged_outputs_are_independent_and_repeatable() -> None:
    event_ids = ["SYNTHETIC_EVENT_A", "SYNTHETIC_EVENT_B"]
    values = {"SYNTHETIC_EVENT_B": None, "SYNTHETIC_EVENT_A": 2.25}
    original_event_ids = event_ids[:]
    original_values = values.copy()

    first = pack_covapie_post_distance_targets_v1(
        event_ids=event_ids, post_distance_by_event=values
    )
    second = pack_covapie_post_distance_targets_v1(
        event_ids=event_ids, post_distance_by_event=values
    )
    assert event_ids == original_event_ids
    assert values == original_values
    assert torch.allclose(
        first.pre_post_geometry_target_angstrom,
        second.pre_post_geometry_target_angstrom,
        rtol=0,
        atol=0,
        equal_nan=True,
    )
    assert torch.equal(
        first.pre_post_geometry_component_valid_mask,
        second.pre_post_geometry_component_valid_mask,
    )
    assert torch.equal(
        first.pre_post_geometry_component_loss_mask,
        second.pre_post_geometry_component_loss_mask,
    )
    assert (
        first.pre_post_geometry_target_angstrom.untyped_storage().data_ptr()
        != second.pre_post_geometry_target_angstrom.untyped_storage().data_ptr()
    )

    first.pre_post_geometry_target_angstrom.fill_(9.0)
    first.pre_post_geometry_component_valid_mask.fill_(True)
    first.pre_post_geometry_component_loss_mask.fill_(True)
    third = pack_covapie_post_distance_targets_v1(
        event_ids=event_ids, post_distance_by_event=values
    )
    assert event_ids == original_event_ids
    assert values == original_values
    assert torch.allclose(
        third.pre_post_geometry_target_angstrom,
        second.pre_post_geometry_target_angstrom,
        rtol=0,
        atol=0,
        equal_nan=True,
    )
    assert torch.equal(
        third.pre_post_geometry_component_valid_mask,
        second.pre_post_geometry_component_valid_mask,
    )
    assert not third.pre_post_geometry_component_loss_mask.any()


def test_synthetic_pack_is_accepted_by_real_current11_tensorizer() -> None:
    batch, runtime, authority = _tensorizer_fixture()
    event_ids = ("SYNTHETIC_EVENT_A", "SYNTHETIC_EVENT_B")
    packed = pack_covapie_post_distance_targets_v1(
        event_ids=event_ids,
        post_distance_by_event={
            "SYNTHETIC_EVENT_B": None,
            "SYNTHETIC_EVENT_A": 2.25,
        },
    )
    preserved_roles = copy.deepcopy(authority["ligand_role_id"])
    preserved_pairs = copy.deepcopy(
        runtime["remap_output17_or_none"]["pair_values_batch_indices"]
    )
    preserved_observed = copy.deepcopy(
        authority["observed_complex_pair_distance_angstrom"]
    )
    authority["pre_post_geometry_target_angstrom"] = (
        packed.pre_post_geometry_target_angstrom.tolist()
    )
    authority["pre_post_geometry_component_valid_mask"] = (
        packed.pre_post_geometry_component_valid_mask.tolist()
    )
    authority["pre_post_geometry_component_loss_mask"] = (
        packed.pre_post_geometry_component_loss_mask.tolist()
    )

    output = tensorize_covapie_current11_training_supervision_v1(
        batch=batch,
        runtime_result=runtime,
        authoritative_supervision=authority,
        device=torch.device("cpu"),
        epoch=0,
        task_schedule_seed=0,
    )

    assert torch.allclose(
        output.pre_post_geometry_target_angstrom,
        packed.pre_post_geometry_target_angstrom,
        rtol=0,
        atol=0,
        equal_nan=True,
    )
    assert torch.equal(
        output.pre_post_geometry_component_valid_mask,
        packed.pre_post_geometry_component_valid_mask,
    )
    assert torch.equal(
        output.pre_post_geometry_component_loss_mask,
        packed.pre_post_geometry_component_loss_mask,
    )
    assert torch.isnan(output.pre_post_geometry_target_angstrom[:, 0]).all()
    assert output.pre_post_geometry_target_angstrom[0, 1].item() == 2.25
    assert torch.isnan(output.pre_post_geometry_target_angstrom[1, 1])
    assert output.pre_post_geometry_component_valid_mask.tolist() == [
        [False, True], [False, False],
    ]
    assert not output.pre_post_geometry_component_loss_mask.any()
    assert authority["ligand_role_id"] == preserved_roles
    assert runtime["remap_output17_or_none"]["pair_values_batch_indices"] == (
        preserved_pairs
    )
    assert authority["observed_complex_pair_distance_angstrom"] == (
        preserved_observed
    )
    assert output.ligand_role_id.tolist() == [0, 1, 2, 0, 1, 2]
    assert output.pair_positive_candidate_index.tolist() == [4, 10]
    assert output.pair_negative_count.tolist() == [5, 5]
    assert output.observed_complex_pair_distance_angstrom.tolist() == [
        [1.0], [1.0],
    ]
    assert packed.event_ids == event_ids
    assert not hasattr(packed, "sample_training_admitted")
    assert not hasattr(packed, "authoritative_supervision")
