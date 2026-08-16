from __future__ import annotations

import copy
import hashlib

import pytest
import torch

from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    AUTHORITATIVE_SUPERVISION_SCHEMA_V1,
    CANONICAL_TASKS_V1,
    TENSORIZER_ERROR,
    canonical_task_id_for_covapie_current11_sample_v1,
    tensorize_covapie_current11_training_supervision_v1,
)


TARGET_INDICATOR_FIELD = "pocket_target_residue_atom_condition_indicator"


def _fixture() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    sample_keys = [
        "CYS_SG_SAMPLE_INDEX_000001",
        "CYS_SG_SAMPLE_INDEX_000002",
    ]
    sample_identities = [
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
    ]
    ligand_offsets = [0, 3, 6]
    pocket_offsets = [0, 2, 4]
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
        "num_lig_atoms": torch.tensor([3, 3], dtype=torch.long),
        "num_pocket_nodes": torch.tensor([2, 2], dtype=torch.long),
        "lig_mask": torch.tensor([0, 0, 0, 1, 1, 1], dtype=torch.float32),
        "pocket_mask": torch.tensor([0, 0, 1, 1], dtype=torch.float32),
    }
    output17: dict[str, object] = {
        "batch_sample_order": sample_identities,
        "pair_values_parser_local_indices": [[0, 2], [0, 2]],
        # Published Output17 columns are pocket separate-flat, ligand
        # separate-flat.  The tensorizer emits explicitly named reverse order.
        "pair_values_batch_indices": [[0, 2], [2, 5]],
        "pair_values_joint_global_indices": None,
        "pair_sample_indices": [0, 1],
        "sample_pair_offsets": [0, 1, 2],
        "entry_validity": [True, True],
        "sample_validity": [True, True],
        "remap_status": "REMAPPED_EXACT",
        "failure_reason": "NONE",
    }
    runtime: dict[str, object] = {
        "runtime_status": "full_success",
        "batch_sample_keys_or_none": sample_keys[:],
        "remap_output17_or_none": output17,
    }
    batch["covapie_current11_task2_runtime_result_v1"] = runtime
    authority: dict[str, object] = {
        "schema_version": AUTHORITATIVE_SUPERVISION_SCHEMA_V1,
        "sample_keys": sample_keys[:],
        "ligand_node_offsets": ligand_offsets,
        "pocket_node_offsets": pocket_offsets,
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


def _derived_target_evidence(
    runtime: dict[str, object], *, pocket_total: int
) -> tuple[list[int], list[int], torch.Tensor]:
    output17 = runtime["remap_output17_or_none"]
    assert type(output17) is dict
    batch_pairs = output17["pair_values_batch_indices"]
    parser_pairs = output17["pair_values_parser_local_indices"]
    assert type(batch_pairs) is list and type(parser_pairs) is list
    pocket_flat = [pair[0] for pair in batch_pairs]
    pocket_local = [pair[0] for pair in parser_pairs]
    indicator = torch.zeros(pocket_total, dtype=torch.bool)
    indicator[pocket_flat] = True
    return pocket_flat, pocket_local, indicator


def _run(
    batch: dict[str, object],
    runtime: dict[str, object],
    authority: dict[str, object],
    *,
    epoch: int = 0,
    seed: int = 0,
):
    return tensorize_covapie_current11_training_supervision_v1(
        batch=batch,
        runtime_result=runtime,
        authoritative_supervision=authority,
        device=torch.device("cpu"),
        epoch=epoch,
        task_schedule_seed=seed,
    )


def _fails(
    batch: dict[str, object],
    runtime: dict[str, object],
    authority: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match=f"^{TENSORIZER_ERROR}$"):
        _run(batch, runtime, authority)


def test_exact5_registry_includes_mandatory_b3_and_no_sixth() -> None:
    assert CANONICAL_TASKS_V1 == (
        (0, "warhead_only", "A", (2,)),
        (1, "linker_plus_warhead", "B", (1, 2)),
        (2, "scaffold_plus_warhead", "B2", (0, 2)),
        (3, "scaffold_only", "B3", (0,)),
        (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
    )
    assert len(CANONICAL_TASKS_V1) == 5


def test_exact_schedule_encoding_cycle_and_batch_reorder_independence() -> None:
    keys = [
        "CYS_SG_SAMPLE_INDEX_000001",
        "CYS_SG_SAMPLE_INDEX_000011",
    ]
    for key in keys:
        observed = [
            canonical_task_id_for_covapie_current11_sample_v1(
                sample_key=key, epoch=epoch, task_schedule_seed=17
            )
            for epoch in range(5)
        ]
        assert sorted(observed) == list(range(5))
        payload = (
            b"COVAPIE_CURRENT11_CANONICAL_TASK_SCHEDULE_V1\0"
            + b"17\0"
            + key.encode("ascii")
        )
        base = int.from_bytes(
            hashlib.sha256(payload).digest()[:8], "big", signed=False
        ) % 5
        assert observed == [(base + epoch) % 5 for epoch in range(5)]
    forward = {
        key: canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=key, epoch=8, task_schedule_seed=17
        )
        for key in keys
    }
    reverse = {
        key: canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=key, epoch=8, task_schedule_seed=17
        )
        for key in reversed(keys)
    }
    assert forward == reverse


@pytest.mark.parametrize(
    ("key", "epoch", "seed"),
    (
        ("CYS_SG_SAMPLE_INDEX_000001", True, 0),
        ("CYS_SG_SAMPLE_INDEX_000001", -1, 0),
        ("CYS_SG_SAMPLE_INDEX_000001", 0, True),
        ("CYS_SG_SAMPLE_INDEX_000001", 0, -1),
        ("CYS_SG_SAMPLE_INDEX_000001", 0, 2**63),
        ("A", 0, 0),
        ("CYS_SG_SAMPLE_INDEX_00001", 0, 0),
        ("CYS_SG_SAMPLE_INDEX_000001\N{SNOWMAN}", 0, 0),
    ),
)
def test_schedule_exact_types_and_sample_key_validation(
    key: str, epoch: object, seed: object
) -> None:
    with pytest.raises(ValueError, match=f"^{TENSORIZER_ERROR}$"):
        canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=key, epoch=epoch, task_schedule_seed=seed
        )


def test_tensorizer_shapes_dtypes_masks_candidates_and_joint_none_success() -> None:
    batch, runtime, authority = _fixture()
    output = _run(batch, runtime, authority)
    pocket_coords = batch["pocket_coords"]
    assert isinstance(pocket_coords, torch.Tensor)
    expected_flat, _, _ = _derived_target_evidence(
        runtime, pocket_total=len(pocket_coords)
    )
    assert output.canonical_task_id.shape == (2,)
    assert output.canonical_task_id.dtype == torch.long
    assert output.ligand_base_generation_mask.shape == (6, 1)
    assert output.ligand_base_fixed_mask.shape == (6, 1)
    assert torch.equal(
        output.ligand_base_generation_mask,
        output.ligand_base_target_mask,
    )
    assert torch.equal(
        output.ligand_base_fixed_mask,
        output.ligand_base_context_mask,
    )
    assert torch.equal(
        output.ligand_base_generation_mask
        ^ output.ligand_base_fixed_mask,
        torch.ones((6, 1), dtype=torch.bool),
    )
    assert output.pair_candidate_offsets.tolist() == [0, 6, 12]
    assert output.pair_candidate_ligand_local_index.tolist() == [
        0, 0, 1, 1, 2, 2,
        0, 0, 1, 1, 2, 2,
    ]
    assert output.pair_candidate_residue_local_index.tolist() == [
        0, 1, 0, 1, 0, 1,
        0, 1, 0, 1, 0, 1,
    ]
    assert output.pair_candidate_ligand_flat_index.tolist() == [
        0, 0, 1, 1, 2, 2,
        3, 3, 4, 4, 5, 5,
    ]
    assert output.pair_candidate_pocket_flat_index.tolist() == [
        0, 1, 0, 1, 0, 1,
        2, 3, 2, 3, 2, 3,
    ]
    assert output.pair_positive_candidate_index.tolist() == [4, 10]
    assert output.pair_negative_count.tolist() == [5, 5]
    assert output.pair_candidate_is_positive.sum().item() == 2
    assert output.pair_candidate_is_negative.sum().item() == 10
    assert output.pair_contrastive_sample_loss_mask.tolist() == [True, True]
    assert output.target_residue_reactive_atom_flat_index.tolist() == expected_flat
    assert output.ligand_anchor_distance_valid.all()
    assert output.pre_post_geometry_component_loss_mask.sum().item() == 0


def test_target_reactive_indicator_is_derived_from_output17_when_absent() -> None:
    batch, runtime, authority = _fixture()
    assert TARGET_INDICATOR_FIELD not in batch
    pocket_coords = batch["pocket_coords"]
    assert isinstance(pocket_coords, torch.Tensor)
    expected_flat, expected_local, expected_indicator = _derived_target_evidence(
        runtime, pocket_total=len(pocket_coords)
    )

    output = _run(batch, runtime, authority)

    assert TARGET_INDICATOR_FIELD not in batch
    assert output.target_residue_reactive_atom_flat_index.tolist() == expected_flat
    assert output.target_residue_reactive_atom_local_index.tolist() == expected_local
    assert torch.equal(
        output.target_residue_reactive_atom_mask.squeeze(1),
        expected_indicator,
    )
    assert output.target_residue_condition_valid.tolist() == [True, True]
    offsets = authority["pocket_node_offsets"]
    assert type(offsets) is list
    assert [
        int(output.target_residue_reactive_atom_mask[
            offsets[sample]:offsets[sample + 1]
        ].sum().item())
        for sample in range(len(offsets) - 1)
    ] == [1, 1]


def test_matching_optional_target_indicator_is_parity_only_and_not_mutated() -> None:
    batch, runtime, authority = _fixture()
    pocket_coords = batch["pocket_coords"]
    assert isinstance(pocket_coords, torch.Tensor)
    _, _, indicator = _derived_target_evidence(
        runtime, pocket_total=len(pocket_coords)
    )
    original = indicator.clone()
    batch[TARGET_INDICATOR_FIELD] = indicator

    output = _run(batch, runtime, authority)

    assert batch[TARGET_INDICATOR_FIELD] is indicator
    assert torch.equal(indicator, original)
    assert torch.equal(
        output.target_residue_reactive_atom_mask.squeeze(1), indicator
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_dtype",
        "wrong_rank",
        "wrong_length",
        "zero_targets",
        "extra_target",
        "wrong_target_atom",
        "target_outside_membership",
    ),
)
def test_optional_target_indicator_invalid_parity_fails_closed(
    mutation: str,
) -> None:
    batch, runtime, authority = _fixture()
    pocket_coords = batch["pocket_coords"]
    assert isinstance(pocket_coords, torch.Tensor)
    pocket_flat, _, indicator = _derived_target_evidence(
        runtime, pocket_total=len(pocket_coords)
    )
    invalid = indicator.clone()
    if mutation == "wrong_dtype":
        invalid = invalid.to(dtype=torch.float32)
    elif mutation == "wrong_rank":
        invalid = invalid.unsqueeze(0)
    elif mutation == "wrong_length":
        invalid = invalid[:-1]
    elif mutation == "zero_targets":
        invalid.zero_()
    elif mutation == "extra_target":
        false_index = int(torch.nonzero(~invalid, as_tuple=False)[0, 0].item())
        invalid[false_index] = True
    elif mutation == "wrong_target_atom":
        offsets = authority["pocket_node_offsets"]
        assert type(offsets) is list
        replacement = next(
            index for index in range(offsets[0], offsets[1])
            if index != pocket_flat[0]
        )
        invalid[pocket_flat[0]] = False
        invalid[replacement] = True
    else:
        membership = authority["target_residue_membership_mask"]
        assert type(membership) is list
        membership[pocket_flat[0]] = False
    batch[TARGET_INDICATOR_FIELD] = invalid
    _fails(batch, runtime, authority)


@pytest.mark.parametrize(
    "dtype", (torch.float32, torch.float64, torch.int64, torch.int16)
)
def test_runtime_membership_accepts_exact_numeric_dtypes_without_mutation(
    dtype: torch.dtype,
) -> None:
    batch, runtime, authority = _fixture()
    original: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    for field in ("lig_mask", "pocket_mask"):
        value = batch[field]
        assert isinstance(value, torch.Tensor)
        converted = value.to(dtype=dtype)
        batch[field] = converted
        original[field] = (converted, converted.clone())

    output = _run(batch, runtime, authority)

    for field, (identity, contents) in original.items():
        assert batch[field] is identity
        assert identity.dtype == dtype
        assert torch.equal(identity, contents)
    assert output.pair_candidate_batch_index.dtype == torch.long


@pytest.mark.parametrize("field", ("lig_mask", "pocket_mask"))
@pytest.mark.parametrize(
    "mutation",
    (
        "bool",
        "complex",
        "nan",
        "positive_inf",
        "negative_inf",
        "fractional",
        "negative",
        "wrong_ordinal",
        "wrong_length",
        "wrong_rank",
    ),
)
def test_runtime_membership_invalid_representations_fail_closed(
    field: str, mutation: str
) -> None:
    batch, runtime, authority = _fixture()
    value = batch[field]
    assert isinstance(value, torch.Tensor)
    if mutation == "bool":
        invalid = value.to(dtype=torch.bool)
    elif mutation == "complex":
        invalid = value.to(dtype=torch.complex64)
    elif mutation in ("nan", "positive_inf", "negative_inf"):
        invalid = value.clone()
        invalid[0] = {
            "nan": float("nan"),
            "positive_inf": float("inf"),
            "negative_inf": -float("inf"),
        }[mutation]
    elif mutation == "fractional":
        invalid = value.clone()
        invalid[0] = 0.5
    elif mutation == "negative":
        invalid = value.clone()
        invalid[0] = -1
    elif mutation == "wrong_ordinal":
        invalid = value.clone()
        invalid[0] = 1
    elif mutation == "wrong_length":
        invalid = value[:-1]
    else:
        invalid = value.unsqueeze(0)
    batch[field] = invalid
    _fails(batch, runtime, authority)


@pytest.mark.parametrize("field", ("num_lig_atoms", "num_pocket_nodes"))
def test_runtime_length_tensors_remain_strict_long(field: str) -> None:
    batch, runtime, authority = _fixture()
    value = batch[field]
    assert isinstance(value, torch.Tensor)
    batch[field] = value.to(dtype=torch.float32)
    _fails(batch, runtime, authority)


def test_source_vs_runtime_f03_f09_ownership_and_alias_only_fail_closed() -> None:
    for forbidden in (
        "canonical_task_id",
        "canonical_task_valid",
        "ligand_base_generation_mask",
        "ligand_active_diffusion_loss_mask",
        "task_alias",
    ):
        batch, runtime, authority = _fixture()
        authority[forbidden] = [0, 0]
        _fails(batch, runtime, authority)


def test_runtime_result_requires_same_object_identity() -> None:
    batch, runtime, authority = _fixture()
    copied = copy.deepcopy(runtime)
    _fails(batch, copied, authority)


def test_output17_formal_sample_identity_schema_and_key_triangle() -> None:
    batch, runtime, authority = _fixture()
    output17 = runtime["remap_output17_or_none"]
    assert type(output17) is dict
    identities = output17["batch_sample_order"]
    assert type(identities) is list
    assert [identity["sample_index_row_id"] for identity in identities] == (
        runtime["batch_sample_keys_or_none"]
    ) == authority["sample_keys"]
    _run(batch, runtime, authority)


@pytest.mark.parametrize(
    "mutation",
    (
        "legacy_string_list",
        "missing_field",
        "extra_field",
        "blank_value",
        "non_string_value",
        "wrong_sample_key",
        "output17_order_mismatch",
        "duplicate_identity",
        "runtime_key_mismatch",
    ),
)
def test_output17_formal_sample_identity_fail_closed(mutation: str) -> None:
    batch, runtime, authority = _fixture()
    output17 = runtime["remap_output17_or_none"]
    assert type(output17) is dict
    identities = output17["batch_sample_order"]
    assert type(identities) is list
    if mutation == "legacy_string_list":
        output17["batch_sample_order"] = authority["sample_keys"][:]
    elif mutation == "missing_field":
        del identities[0]["pdb_id"]
    elif mutation == "extra_field":
        identities[0]["unknown"] = "value"
    elif mutation == "blank_value":
        identities[0]["ligand_comp_id"] = " "
    elif mutation == "non_string_value":
        identities[0]["sample_preparation_input_id"] = 1
    elif mutation == "wrong_sample_key":
        identities[0]["sample_index_row_id"] = "CYS_SG_SAMPLE_INDEX_000011"
    elif mutation == "output17_order_mismatch":
        identities.reverse()
    elif mutation == "duplicate_identity":
        identities[1] = copy.deepcopy(identities[0])
    elif mutation == "runtime_key_mismatch":
        runtime["batch_sample_keys_or_none"].reverse()
    _fails(batch, runtime, authority)


@pytest.mark.parametrize(
    "mutation",
    (
        "positive_indicator_mismatch",
        "cross_sample_pair",
        "invalid_offsets",
        "empty_membership",
        "reactive_outside_membership",
        "duplicate_positive",
        "missing_positive",
    ),
)
def test_pair_target_and_offset_mutations_fail_closed(mutation: str) -> None:
    batch, runtime, authority = _fixture()
    output17 = runtime["remap_output17_or_none"]
    assert isinstance(output17, dict)
    if mutation == "positive_indicator_mismatch":
        pocket_coords = batch["pocket_coords"]
        assert isinstance(pocket_coords, torch.Tensor)
        _, _, indicator = _derived_target_evidence(
            runtime, pocket_total=len(pocket_coords)
        )
        batch[TARGET_INDICATOR_FIELD] = indicator
        output17["pair_values_batch_indices"][0] = [1, 2]
        output17["pair_values_parser_local_indices"][0] = [1, 2]
    elif mutation == "cross_sample_pair":
        output17["pair_values_batch_indices"][0] = [0, 5]
        output17["pair_values_parser_local_indices"][0] = [0, 2]
    elif mutation == "invalid_offsets":
        authority["ligand_node_offsets"] = [0, 4, 6]
    elif mutation == "empty_membership":
        authority["target_residue_membership_mask"] = [False, False, True, True]
    elif mutation == "reactive_outside_membership":
        authority["target_residue_membership_mask"] = [False, True, True, True]
    elif mutation == "duplicate_positive":
        output17["pair_values_batch_indices"] = [[0, 2], [0, 2], [2, 5]]
        output17["pair_values_parser_local_indices"] = [[0, 2], [0, 2], [0, 2]]
        output17["pair_sample_indices"] = [0, 0, 1]
        output17["sample_pair_offsets"] = [0, 2, 3]
        output17["entry_validity"] = [True, True, True]
    elif mutation == "missing_positive":
        output17["pair_values_batch_indices"] = [[2, 5]]
        output17["pair_values_parser_local_indices"] = [[0, 2]]
        output17["pair_sample_indices"] = [1]
        output17["sample_pair_offsets"] = [0, 0, 1]
        output17["entry_validity"] = [True]
    _fails(batch, runtime, authority)


@pytest.mark.parametrize("mutation", ("padding", "virtual", "hydrogen_like"))
def test_non_retained_or_non_checkpoint_node_rows_fail_closed(mutation: str) -> None:
    batch, runtime, authority = _fixture()
    if mutation == "padding":
        batch["lig_one_hot"][0].zero_()
    elif mutation == "virtual":
        batch["lig_one_hot"] = torch.cat((
            batch["lig_one_hot"], torch.zeros((6, 1))
        ), dim=1)
    else:
        batch["pocket_one_hot"][0] = torch.full((10,), 0.1)
    _fails(batch, runtime, authority)


def test_missing_role_authority_and_fourth_role_fail_closed() -> None:
    batch, runtime, authority = _fixture()
    authority["ligand_role_id"][0] = -1
    authority["ligand_role_valid"][0] = False
    _fails(batch, runtime, authority)
    batch, runtime, authority = _fixture()
    authority["ligand_role_id"][0] = 3
    _fails(batch, runtime, authority)


def test_observed_distance_cannot_fill_unavailable_pre_post() -> None:
    batch, runtime, authority = _fixture()
    authority["pre_post_geometry_target_angstrom"][0] = [1.0, 1.0]
    _fails(batch, runtime, authority)


def test_geometry_partial_authority_has_exact_component_loss_mask() -> None:
    batch, runtime, authority = _fixture()
    authority["pre_post_geometry_target_angstrom"][0] = [2.0, float("nan")]
    authority["pre_post_geometry_component_valid_mask"][0] = [True, False]
    authority["pre_post_geometry_component_loss_mask"][0] = [True, False]
    output = _run(batch, runtime, authority)
    assert output.pre_post_geometry_component_loss_mask.tolist() == [
        [True, False], [False, False],
    ]
