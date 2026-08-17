from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import torch

from covalent_ext import covapie_direct_attachment_optional_linker_runtime_v1 as runtime
from covalent_ext import (
    covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1
    as published_role_contract,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11AuxiliaryModelV1,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
K36_SIGNATURE_SHA256 = (
    "83e9c7b9d43444d7e50fbfd7e6c3dafef5e0dc92cf1a7c571e3f4e3fe4e08d92"
)
K36_EVIDENCE = REPO_ROOT / (
    "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1/"
    "covapie_recovered7_chemistry_review_package_evidence.json"
)


def _small_direct_profile(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "role_profile": runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "retained_heavy_atoms": (0, 1, 2),
        "scaffold_atoms": (0, 1),
        "linker_atoms": (),
        "warhead_atoms": (2,),
        "reactive_atom_id": 2,
        "direct_scaffold_warhead_boundaries": ((1, 2, "single"),),
        "explicit_graph_bonds": (
            runtime.ExplicitBondV1(0, 1, "single"),
            runtime.ExplicitBondV1(1, 2, "single"),
        ),
    }
    values.update(overrides)
    return values


@pytest.fixture(scope="module")
def k36_review_class() -> dict[str, object]:
    evidence = json.loads(K36_EVIDENCE.read_text(encoding="utf-8"))
    matches = [
        review_class
        for review_class in evidence["review_classes"]
        if review_class["chemistry_review_signature_sha256"]
        == K36_SIGNATURE_SHA256
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture(scope="module")
def k36_profile(k36_review_class: dict[str, object]) -> dict[str, object]:
    signature = k36_review_class["chemistry_review_signature"]
    retained = tuple(
        row["atom_id"]
        for row in signature[
            "canonical_model_bound_ligand_heavy_atom_inventory"
        ]
    )
    warhead = ("C21", "O22")
    scaffold = tuple(atom for atom in retained if atom not in set(warhead))
    bonds = tuple(
        runtime.ExplicitBondV1(
            row["atom_id_1"], row["atom_id_2"], row["bond_order"]
        )
        for row in signature[
            "canonical_internal_heavy_heavy_bond_graph_with_bond_orders"
        ]
    )
    return {
        "signature": signature,
        "retained": retained,
        "scaffold": scaffold,
        "linker": (),
        "warhead": warhead,
        "bonds": bonds,
    }


def test_frozen_exact3_roles_exact5_tasks_and_profile_task_sets() -> None:
    assert runtime.CANONICAL_ROLE_NAMES_V1 == (
        "scaffold",
        "linker",
        "warhead",
    )
    assert runtime.CANONICAL_ROLE_IDS_V1 == (0, 1, 2)
    assert runtime.CANONICAL_TASKS_V1 is published_role_contract.CANONICAL_TASKS
    assert tuple(row[0] for row in runtime.CANONICAL_TASKS_V1) == (0, 1, 2, 3, 4)
    assert tuple(row[1] for row in runtime.CANONICAL_TASKS_V1) == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    assert runtime.valid_canonical_task_ids_for_role_profile_v1(
        runtime.STRICT_LINKER_PRESENT_V1
    ) == (0, 1, 2, 3, 4)
    assert runtime.valid_canonical_task_ids_for_role_profile_v1(
        runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
    ) == (0, 3, 4)
    assert len(runtime.DIRECT_PROFILE_TASK_APPLICABILITY_V1) == 5
    assert tuple(
        row[0] for row in runtime.DIRECT_PROFILE_TASK_APPLICABILITY_V1 if row[3]
    ) == (0, 3, 4)


@pytest.mark.parametrize(
    ("retained", "scaffold", "linker", "warhead"),
    (
        ((0, 1, 2), (0,), (1,), (2,)),
        ((0, 1, 2), (0, 1), (), (2,)),
        ((0, 1, 2), (0, 1), (1,), (2,)),
        ((0, 1, 2, 3), (0,), (1,), (2,)),
    ),
)
def test_strict_partition_validity_parity_with_published_v1(
    retained: tuple[int, ...],
    scaffold: tuple[int, ...],
    linker: tuple[int, ...],
    warhead: tuple[int, ...],
) -> None:
    published_reasons = published_role_contract.validate_exact3_partition(
        retained, scaffold, linker, warhead
    )
    successor = runtime.validate_role_partition_for_profile_v1(
        role_profile=runtime.STRICT_LINKER_PRESENT_V1,
        retained_heavy_atoms=retained,
        scaffold_atoms=scaffold,
        linker_atoms=linker,
        warhead_atoms=warhead,
    )
    assert successor.valid is (not published_reasons)
    assert successor.reasons == published_reasons


def test_strict_profile_delegates_nonempty_exact3_and_exact5_masks() -> None:
    result = runtime.validate_role_profile_v1(
        role_profile=runtime.STRICT_LINKER_PRESENT_V1,
        retained_heavy_atoms=(0, 1, 2),
        scaffold_atoms=(0,),
        linker_atoms=(1,),
        warhead_atoms=(2,),
    )
    assert result.valid is True
    assert result.direct_scaffold_warhead_boundary_applicable is False
    assert result.direct_scaffold_warhead_boundary is None
    expected_levels = (
        "A_warhead_only",
        "B_linker_warhead",
        "B2_scaffold_warhead",
        "B3_scaffold_only",
        "C_scaffold_linker_warhead",
    )
    for task_id, expected_level in enumerate(expected_levels):
        mask = runtime.build_mask_for_role_profile_v1(
            role_profile=runtime.STRICT_LINKER_PRESENT_V1,
            canonical_task_id=task_id,
            scaffold_atoms=(0,),
            linker_atoms=(1,),
            warhead_atoms=(2,),
            num_ligand_atoms=3,
        )
        assert mask.mask_type == expected_level


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    (
        (
            {
                "retained_heavy_atoms": (2,),
                "scaffold_atoms": (),
                "warhead_atoms": (2,),
                "direct_scaffold_warhead_boundaries": (),
                "explicit_graph_bonds": (),
            },
            "scaffold_empty",
        ),
        (
            {
                "retained_heavy_atoms": (0, 1),
                "warhead_atoms": (),
                "reactive_atom_id": 1,
                "direct_scaffold_warhead_boundaries": (),
                "explicit_graph_bonds": (
                    runtime.ExplicitBondV1(0, 1, "single"),
                ),
            },
            "warhead_empty",
        ),
        (
            {
                "scaffold_atoms": (0,),
                "linker_atoms": (1,),
                "warhead_atoms": (2,),
                "direct_scaffold_warhead_boundaries": ((0, 2, "single"),),
                "explicit_graph_bonds": (
                    runtime.ExplicitBondV1(0, 2, "single"),
                ),
            },
            "linker_not_empty",
        ),
        (
            {"scaffold_atoms": (0, 1), "warhead_atoms": (1, 2)},
            "partition_overlap",
        ),
        (
            {
                "retained_heavy_atoms": (0, 1, 2, 3),
                "scaffold_atoms": (0, 1),
                "warhead_atoms": (2,),
            },
            "partition_not_exhaustive",
        ),
        ({"reactive_atom_id": 0}, "reactive_atom_outside_warhead"),
        ({"direct_scaffold_warhead_boundaries": ()}, "direct_boundary_missing"),
        (
            {
                "direct_scaffold_warhead_boundaries": (
                    (1, 2, "single"),
                    (0, 2, "single"),
                ),
                "explicit_graph_bonds": (
                    runtime.ExplicitBondV1(0, 1, "single"),
                    runtime.ExplicitBondV1(1, 2, "single"),
                    runtime.ExplicitBondV1(0, 2, "single"),
                ),
            },
            "multiple_direct_boundaries",
        ),
        (
            {"direct_scaffold_warhead_boundaries": ((2, 1, "single"),)},
            "direct_boundary_role_sides_inconsistent",
        ),
        (
            {
                "explicit_graph_bonds": (
                    runtime.ExplicitBondV1(0, 1, "single"),
                )
            },
            "direct_boundary_bond_absent_from_explicit_graph",
        ),
        (
            {
                "explicit_graph_bonds": (
                    runtime.ExplicitBondV1(0, 1, "single"),
                    runtime.ExplicitBondV1(1, 2, "single"),
                    runtime.ExplicitBondV1(0, 2, "single"),
                )
            },
            "multiple_direct_boundaries_in_explicit_graph",
        ),
    ),
)
def test_direct_role_validator_fails_closed(
    overrides: dict[str, object], expected_reason: str
) -> None:
    result = runtime.validate_role_profile_v1(
        **_small_direct_profile(**overrides)
    )
    assert result.valid is False
    assert expected_reason in result.reasons


def test_direct_role_validator_requires_explicit_graph_not_distance() -> None:
    result = runtime.validate_role_profile_v1(
        **_small_direct_profile(explicit_graph_bonds=())
    )
    assert result.valid is False
    assert "direct_boundary_bond_absent_from_explicit_graph" in result.reasons
    assert "distance" not in " ".join(result.reasons)


def test_direct_boundary_representation_and_applicability_are_truthful() -> None:
    result = runtime.validate_role_profile_v1(**_small_direct_profile())
    assert result.valid is True
    assert result.scaffold_linker_boundary_applicable is False
    assert result.linker_warhead_boundary_applicable is False
    assert result.direct_scaffold_warhead_boundary_applicable is True
    assert result.direct_scaffold_warhead_boundary == (
        runtime.DirectScaffoldWarheadBoundaryV1(1, 2, "single", True)
    )


def test_direct_masks_are_exact_and_B_B2_fail_as_not_applicable() -> None:
    common = {
        "role_profile": runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "scaffold_atoms": (0, 1),
        "linker_atoms": (),
        "warhead_atoms": (2, 3),
        "num_ligand_atoms": 4,
    }
    task_a = runtime.build_mask_for_role_profile_v1(
        canonical_task_id=0, **common
    )
    assert task_a.masked_atoms == (2, 3)
    assert task_a.visible_atoms == (0, 1)
    for task_id in (1, 2):
        with pytest.raises(ValueError, match="TASK_NOT_APPLICABLE"):
            runtime.build_mask_for_role_profile_v1(
                canonical_task_id=task_id, **common
            )
    task_b3 = runtime.build_mask_for_role_profile_v1(
        canonical_task_id=3, **common
    )
    assert task_b3.masked_atoms == (0, 1)
    assert task_b3.visible_atoms == (2, 3)
    task_c = runtime.build_mask_for_role_profile_v1(
        canonical_task_id=4, **common
    )
    assert task_c.masked_atoms == (0, 1, 2, 3)
    assert task_c.visible_atoms == ()


def test_deterministic_direct_schedule_cycles_only_A_B3_C() -> None:
    kwargs = {
        "role_profile": runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "sample_identity": "4DCD/K36",
        "task_schedule_seed": 2026,
    }
    tasks = tuple(
        runtime.canonical_task_id_for_role_profile_v1(epoch=epoch, **kwargs)
        for epoch in range(12)
    )
    assert all(set(tasks[start : start + 3]) == {0, 3, 4} for start in range(10))
    assert tasks == tuple(
        runtime.canonical_task_id_for_role_profile_v1(epoch=epoch, **kwargs)
        for epoch in range(12)
    )
    assert set(
        runtime.canonical_task_id_for_role_profile_v1(
            role_profile=runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
            sample_identity="4DCD/K36",
            epoch=0,
            task_schedule_seed=seed,
        )
        for seed in range(32)
    ) == {0, 3, 4}


def test_deterministic_strict_schedule_retains_five_task_cycle_and_domains_differ() -> None:
    tasks = tuple(
        runtime.canonical_task_id_for_role_profile_v1(
            role_profile=runtime.STRICT_LINKER_PRESENT_V1,
            sample_identity="CYS_SG_SAMPLE_INDEX_000001",
            epoch=epoch,
            task_schedule_seed=11,
        )
        for epoch in range(10)
    )
    assert set(tasks[:5]) == {0, 1, 2, 3, 4}
    assert tasks[:5] == tasks[5:]
    assert (
        runtime.SCHEDULE_DOMAINS_BY_ROLE_PROFILE_V1[
            runtime.STRICT_LINKER_PRESENT_V1
        ]
        != runtime.SCHEDULE_DOMAINS_BY_ROLE_PROFILE_V1[
            runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
        ]
    )


@pytest.mark.parametrize(
    ("seed", "expected_valid", "expected_reason"),
    (
        ((1,), False, "seed_size_not_2_or_3"),
        ((0, 1, 3, 4), False, "seed_size_not_2_or_3"),
        ((1, 0), True, None),
        ((1, 0, 3), True, None),
        ((1, 2), False, "seed_outside_scaffold"),
        ((1, 4), False, "seed_disconnected"),
    ),
)
def test_direct_minimal_seed_contract(
    seed: tuple[int, ...], expected_valid: bool, expected_reason: str | None
) -> None:
    bonds = (
        runtime.ExplicitBondV1(0, 1, "single"),
        runtime.ExplicitBondV1(0, 3, "single"),
        runtime.ExplicitBondV1(3, 4, "single"),
        runtime.ExplicitBondV1(1, 2, "single"),
    )
    boundary = runtime.DirectScaffoldWarheadBoundaryV1(
        1, 2, "single", True
    )
    result = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile=runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        seed_atoms=seed,
        scaffold_atoms=(0, 1, 3, 4),
        linker_atoms=(),
        warhead_atoms=(2,),
        explicit_graph_bonds=bonds,
        direct_boundary=boundary,
    )
    assert result.valid is expected_valid
    assert result.primary_anchor_atom_id == 1
    if expected_reason is not None:
        assert expected_reason in result.reasons


def test_k36_exact_hypothetical_27_0_2_profile_and_boundary(
    k36_profile: dict[str, object],
) -> None:
    result = runtime.validate_role_profile_v1(
        role_profile=runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        retained_heavy_atoms=k36_profile["retained"],
        scaffold_atoms=k36_profile["scaffold"],
        linker_atoms=k36_profile["linker"],
        warhead_atoms=k36_profile["warhead"],
        reactive_atom_id="C21",
        direct_scaffold_warhead_boundaries=(("C20", "C21", "single"),),
        explicit_graph_bonds=k36_profile["bonds"],
    )
    assert result.valid is True
    assert (result.scaffold_count, result.linker_count, result.warhead_count) == (
        27,
        0,
        2,
    )
    assert result.direct_scaffold_warhead_boundary == (
        runtime.DirectScaffoldWarheadBoundaryV1(
            "C20", "C21", "single", True
        )
    )


def test_k36_actual_retained_order_direct_task_masks(
    k36_profile: dict[str, object],
) -> None:
    retained = k36_profile["retained"]
    assert len(retained) == 29
    assert retained[8] == "C20"
    assert retained[9] == "C21"
    assert retained[26] == "O22"
    warhead_indices = tuple(
        index for index, atom in enumerate(retained) if atom in {"C21", "O22"}
    )
    scaffold_indices = tuple(
        index for index in range(len(retained)) if index not in set(warhead_indices)
    )
    common = {
        "role_profile": runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "scaffold_atoms": scaffold_indices,
        "linker_atoms": (),
        "warhead_atoms": warhead_indices,
        "num_ligand_atoms": 29,
    }
    task_a = runtime.build_mask_for_role_profile_v1(
        canonical_task_id=0, **common
    )
    task_b3 = runtime.build_mask_for_role_profile_v1(
        canonical_task_id=3, **common
    )
    task_c = runtime.build_mask_for_role_profile_v1(
        canonical_task_id=4, **common
    )
    assert task_a.masked_atoms == (9, 26)
    assert task_a.visible_atoms == scaffold_indices
    assert task_b3.masked_atoms == scaffold_indices
    assert task_b3.visible_atoms == (9, 26)
    assert task_c.masked_atoms == tuple(range(29))
    assert task_c.visible_atoms == ()


def test_k36_direct_seed_anchor_is_scaffold_side_C20(
    k36_profile: dict[str, object],
) -> None:
    boundary = runtime.DirectScaffoldWarheadBoundaryV1(
        "C20", "C21", "single", True
    )
    for seed in (("C20", "N19"), ("C20", "N19", "C17")):
        result = runtime.validate_minimal_seed_for_role_profile_v1(
            role_profile=runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
            seed_atoms=seed,
            scaffold_atoms=k36_profile["scaffold"],
            linker_atoms=(),
            warhead_atoms=k36_profile["warhead"],
            explicit_graph_bonds=k36_profile["bonds"],
            direct_boundary=boundary,
        )
        assert result.valid is True
        assert result.primary_anchor_atom_id == "C20"


def _k36_direct_review_record(k36_profile: dict[str, object]) -> dict[str, object]:
    return {
        "chemistry_review_signature_sha256": K36_SIGNATURE_SHA256,
        "review_scope": "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
        "reviewed_scaffold_atom_ids": list(k36_profile["scaffold"]),
        "reviewed_linker_atom_ids": [],
        "reviewed_warhead_role_atom_ids": ["C21", "O22"],
        "reviewed_minimal_seed_atom_ids": ["C20", "N19"],
        "reviewed_warhead_attachment_atom_id": "C21",
        "reviewed_nonwarhead_boundary_atom_id": "C20",
        "reviewed_attachment_boundary_bond_order": "single",
    }


def test_future_direct_review_role_helper_accepts_synthetic_payload(
    k36_profile: dict[str, object],
) -> None:
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=_k36_direct_review_record(k36_profile),
        chemistry_review_signature=k36_profile["signature"],
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
        applicability_signatures=(K36_SIGNATURE_SHA256,) * 5,
    )
    assert result.valid is True
    assert result.review_signature_bound is True
    assert result.reusable_scope_applicability_signatures_valid is True
    assert result.role_validation is not None and result.role_validation.valid
    assert result.seed_validation is not None and result.seed_validation.valid


def test_future_direct_review_role_helper_rejects_nonempty_linker(
    k36_profile: dict[str, object],
) -> None:
    record = _k36_direct_review_record(k36_profile)
    record["reviewed_scaffold_atom_ids"] = list(k36_profile["scaffold"])[1:]
    record["reviewed_linker_atom_ids"] = [k36_profile["scaffold"][0]]
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=record,
        chemistry_review_signature=k36_profile["signature"],
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
    )
    assert result.valid is False
    assert "linker_not_empty" in result.reasons


def test_future_direct_review_role_helper_rejects_reusable_signature_mismatch(
    k36_profile: dict[str, object],
) -> None:
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=_k36_direct_review_record(k36_profile),
        chemistry_review_signature=k36_profile["signature"],
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
        applicability_signatures=("0" * 64,),
    )
    assert result.valid is False
    assert "reusable_scope_signature_mismatch" in result.reasons


def test_future_direct_review_role_helper_binds_actual_signature_content(
    k36_profile: dict[str, object],
) -> None:
    mutated_signature = copy.deepcopy(k36_profile["signature"])
    mutated_signature["semantic_topology_sha256"] = "0" * 64
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=_k36_direct_review_record(k36_profile),
        chemistry_review_signature=mutated_signature,
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
        applicability_signatures=(K36_SIGNATURE_SHA256,) * 5,
    )
    assert result.valid is False
    assert result.review_signature_bound is False
    assert (
        "chemistry_review_signature_content_sha256_mismatch" in result.reasons
    )
    assert result.role_validation is not None and result.role_validation.valid
    assert result.seed_validation is not None and result.seed_validation.valid


def test_future_direct_review_role_helper_binds_record_declared_signature(
    k36_profile: dict[str, object],
) -> None:
    record = _k36_direct_review_record(k36_profile)
    record["chemistry_review_signature_sha256"] = "0" * 64
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=record,
        chemistry_review_signature=k36_profile["signature"],
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
        applicability_signatures=(K36_SIGNATURE_SHA256,) * 5,
    )
    assert result.valid is False
    assert result.review_signature_bound is False
    assert "review_signature_binding_mismatch" in result.reasons
    assert (
        "chemistry_review_signature_content_sha256_mismatch"
        not in result.reasons
    )


def test_future_direct_review_role_helper_rejects_empty_reusable_applicability(
    k36_profile: dict[str, object],
) -> None:
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=_k36_direct_review_record(k36_profile),
        chemistry_review_signature=k36_profile["signature"],
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
        applicability_signatures=(),
    )
    assert result.valid is False
    assert result.reusable_scope_applicability_signatures_valid is False
    assert (
        "reusable_scope_applicability_signatures_missing" in result.reasons
    )


def test_future_direct_review_role_helper_accepts_sample_bound_without_applicability(
    k36_profile: dict[str, object],
) -> None:
    record = _k36_direct_review_record(k36_profile)
    record["review_scope"] = "SAMPLE_BOUND_ONLY"
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=record,
        chemistry_review_signature=k36_profile["signature"],
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
        applicability_signatures=(),
    )
    assert result.valid is True
    assert result.review_signature_bound is True
    assert result.reusable_scope_applicability_signatures_valid is True
    assert result.role_validation is not None and result.role_validation.valid
    assert result.seed_validation is not None and result.seed_validation.valid


@pytest.mark.parametrize(
    "review_scope", ("NOT_REVIEWED", "QUARANTINE", "UNKNOWN_SCOPE")
)
def test_future_direct_review_role_helper_rejects_non_role_bearing_scope(
    k36_profile: dict[str, object], review_scope: str
) -> None:
    record = _k36_direct_review_record(k36_profile)
    record["review_scope"] = review_scope
    result = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=record,
        chemistry_review_signature=k36_profile["signature"],
        expected_review_signature_sha256=K36_SIGNATURE_SHA256,
        applicability_signatures=(),
    )
    assert result.valid is False
    assert "direct_review_role_scope_invalid" in result.reasons


def test_role_and_task_embedding_indices_are_legal_and_finite() -> None:
    torch.manual_seed(17)
    model = CovapieCurrent11AuxiliaryModelV1(joint_nf=8).eval()
    with torch.no_grad():
        role_output = model.role_embedding(torch.tensor([0, 2]))
        task_output = model.task_embedding(torch.tensor([0, 3, 4]))
    assert role_output.shape == (2, 8)
    assert task_output.shape == (3, 8)
    assert bool(torch.isfinite(role_output).all().item())
    assert bool(torch.isfinite(task_output).all().item())


def test_direct_masks_satisfy_current_lightning_structural_boundary() -> None:
    roles = (0, 0, 2, 2)
    common = {
        "role_profile": runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "scaffold_atoms": (0, 1),
        "linker_atoms": (),
        "warhead_atoms": (2, 3),
        "num_ligand_atoms": 4,
    }
    results = []
    for task_id in (0, 3, 4):
        mask = runtime.build_mask_for_role_profile_v1(
            canonical_task_id=task_id, **common
        )
        results.append(
            runtime.validate_current_lightning_structural_expectations_v1(
                role_profile=runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
                canonical_task_id=task_id,
                ligand_role_ids=roles,
                mask_result=mask,
            )
        )
    assert all(result.valid for result in results)
    assert [(result.generated_count, result.fixed_count) for result in results] == [
        (2, 2),
        (2, 2),
        (4, 0),
    ]


def test_runtime_readiness_keeps_current11_and_expanded_integration_boundaries() -> None:
    readiness = runtime.runtime_readiness_v1()
    assert readiness["direct_attachment_optional_linker_runtime_implemented"] is True
    assert readiness["direct_profile_runtime_primitives_ready"] is True
    assert readiness["current11_tensorizer_direct_profile_supported"] is False
    assert readiness["expanded_tensorizer_integration_pending"] is True
    assert readiness["model_architecture_change_required"] is False
