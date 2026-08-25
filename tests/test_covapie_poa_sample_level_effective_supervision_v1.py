from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as reconciliation,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_poa_sample_level_effective_supervision_v1 as subject,
)


def _event_ids(pdb_id: str) -> list[str]:
    if pdb_id == "4I3U":
        ligand_chains = tuple("IJKLMNOP")
    elif pdb_id == "4I3V":
        ligand_chains = ("J", "L", "N", "P", "R", "T", "V", "W")
    else:
        raise AssertionError(pdb_id)
    return [
        f"COVAPIE_CYS_SG_EVENT_V1:{pdb_id}:{protein_chain}:"
        f"CYS:291-:SG:{ligand_chain}:POA:C2"
        for protein_chain, ligand_chain in zip(tuple("ABCDEFGH"), ligand_chains)
    ]


def _subgroup(pdb_id: str) -> dict[str, object]:
    excluded = pdb_id == "4I3V"
    return {
        "subgroup_id": (
            "POA_SUBGROUP_G2_4I3V_THIOESTER"
            if excluded
            else "POA_SUBGROUP_G1_4I3U_THIOHEMIACETAL"
        ),
        "pdb_id": pdb_id,
        "event_count": 8,
        "canonical_event_ids": _event_ids(pdb_id),
        "CHEMISTRY_POSITIVE": True,
        "TASK_RELEVANT_COVALENT_EVENT": True,
        "chemistry_identity": "COVALENT_CHEMISTRY_SUPPORTED",
        "negative_chemistry": False,
        "task_domain_negative": False,
        "ligand_component_id": "POA",
        "ligand_reactive_atom_id": "C2",
        "protein_component_id": "CYS",
        "protein_reactive_atom_id": "SG",
        "human_chemistry_interpretation": (
            "CYS_SG_NAD_DEPENDENT_THIOESTER_ACYL_ENZYME_STATE"
            if excluded
            else "CYS_SG_ALDEHYDE_ADDITION_THIOHEMIACETAL_STATE"
        ),
        "human_post_state_interpretation": (
            "THIOESTER_POST_STATE"
            if excluded
            else "THIOHEMIACETAL_POST_STATE"
        ),
        "event_training_use_decision": (
            "EXCLUDE_FROM_TRAINING_ONLY" if excluded else "INCLUDE"
        ),
        "human_training_excluded": excluded,
        "training_exclusion_scope": (
            "EXCLUDE_FROM_TRAINING_ONLY" if excluded else "NONE"
        ),
        "training_exclusion_disposition": (
            "HUMAN_EXCLUDE_FROM_TRAINING_ONLY" if excluded else None
        ),
        "training_admission_created": False,
        "POST_GEOMETRY_TRAINING_AUTHORITY": "UNCHANGED",
    }


def _formal_decision() -> dict[str, object]:
    tasks = [
        {
            "mask_index": task_id,
            "semantic_long_name": name,
            "display_alias": alias,
            "structurally_applicable": True,
        }
        for task_id, name, alias in (
            (0, "warhead_only", "A"),
            (1, "linker_plus_warhead", "B"),
            (2, "scaffold_plus_warhead", "B2"),
            (3, "scaffold_only", "B3"),
            (4, "scaffold_plus_linker_plus_warhead", "C"),
        )
    ]
    return {
        "schema_version": subject.FORMAL_DECISION_SCHEMA,
        "record_role": (
            "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
        ),
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": subject.REVIEW_UNIT_ID,
        "ligand_component_id": "POA",
        "human_review_decision_created": True,
        "human_approval_recorded": True,
        "human_approval": {"approval_recorded": True},
        "local_review_transition": {
            "prior_review_state": "CURRENTLY_UNREVIEWED",
            "materialized_review_state": "COMPLETED_HUMAN_REVIEW",
            "local_completed_human_review_delta": 16,
        },
        "unit_level_human_decisions": {
            "exact_event_count": 16,
            "completed_human_review_event_count": 16,
            "chemistry_positive_event_count": 16,
            "chemistry_negative_event_count": 0,
            "human_training_excluded_positive_event_count": 8,
            "POA_HOMOGENEOUS_CHEMISTRY": False,
            "SUBGROUP_DECISIONS_SEPARATE": True,
            "subgroup_count": 2,
            "training_admission_created": False,
            "training_dataset_changed": False,
        },
        "subgroup_human_decisions": [_subgroup("4I3U"), _subgroup("4I3V")],
        "reactive_pair_human_decision": {
            "applies_to_exact_event_count": 16,
            "protein_component_id": "CYS",
            "protein_reactive_atom_id": "SG",
            "ligand_component_id": "POA",
            "ligand_reactive_atom_id": "C2",
            "reactive_pair_human_decision_created": True,
        },
        "role_human_decision": {
            "selected_role_profile": "STRICT_LINKER_PRESENT",
            "warhead_atom_ids": ["C2", "O2"],
            "linker_atom_ids": ["C1"],
            "scaffold_atom_ids": ["P", "O1P", "O2P", "O3P"],
            "exact_ccd_heavy_atom_ids": [
                "C1",
                "C2",
                "O1P",
                "O2",
                "O2P",
                "O3P",
                "P",
            ],
            "boundaries": [
                {
                    "role_edge": "warhead_to_linker",
                    "atom_id_1": "C2",
                    "atom_id_2": "C1",
                    "CCD_bond_order": "SING",
                },
                {
                    "role_edge": "linker_to_scaffold",
                    "atom_id_1": "C1",
                    "atom_id_2": "P",
                    "CCD_bond_order": "SING",
                },
            ],
            "partition_validation": {
                "all_roles_nonempty": True,
                "pairwise_disjoint": True,
                "union_equals_exact_ccd_heavy_atom_set": True,
                "warhead_connected": True,
                "linker_connected": True,
                "scaffold_connected": True,
                "role_graph_connected": True,
                "role_partition_identical_for_all_exact16": True,
            },
            "sample_specific_role_decision_created": True,
            "reusable_role_authority_created": False,
        },
        "canonical_exact5_mask_boundary": {
            "role_profile": "STRICT_LINKER_PRESENT",
            "structurally_applicable_task_count": 5,
            "tasks": tasks,
            "sixth_task_created": False,
            "training_admission_granted": False,
            "full_task_C_seed_authority_granted": False,
            "geometry_supervision_granted": False,
        },
        "precursor_mapping_context": {
            "precursor_evidence_status": "PRECURSOR_EVIDENCE_NOT_ESTABLISHED",
            "PRE_REACTION_GRAPH_AUTHORITY": False,
            "PRE_REACTION_BOND_ORDER_AUTHORITY": False,
            "PRE_GEOMETRY_AUTHORITY": False,
        },
        "post_state_authority_boundary": {
            "POST_GEOMETRY_TRAINING_AUTHORITY": "UNCHANGED",
            "new_POST_geometry_training_target_created": False,
        },
        "reaction_family_candidate_review_decision": {
            "exact_signature_created": False,
            "reaction_family_candidate_registered": False,
            "reaction_family_authority_created": False,
        },
        "warhead_rule_candidate_review_decision": {
            "warhead_rule_candidate_registered": False,
            "warhead_rule_authority_created": False,
        },
        "existing_authority_boundary": {
            "EXISTING_EXACT_AUTHORITY_MATCH_COUNT": 0,
            "exact_existing_authority_inherited_count": 0,
            "FFQ_family_inherited": False,
            "FFQ_warhead_rule_inherited": False,
            "Current11_candidate_family_inherited": False,
            "recovered7_authority_inherited": False,
            "similarity_based_inheritance_used": False,
        },
        "authority_boundary": {
            "human_sample_level_chemistry_decision_created": True,
            "human_sample_level_training_use_decision_created": True,
            "human_sample_level_reactive_pair_decision_created": True,
            "human_sample_level_role_decision_created": True,
            "reusable_chemistry_rule_created": False,
            "reaction_family_authority_created": False,
            "warhead_rule_authority_created": False,
            "reusable_role_authority_created": False,
            "auto_resolvable_events_created": 0,
            "auto_admission_created": False,
            "runtime_rule_created": False,
            "training_admission_created": False,
            "training_dataset_changed": False,
            "ready_for_training": False,
            "model_forward_executed": False,
            "loss_executed": False,
            "backward_executed": False,
            "optimizer_step_executed": False,
            "Trainer_fit_executed": False,
            "training_performed": False,
            "finetune_performed": False,
        },
    }


@pytest.fixture
def result():
    return subject._compile_synthetic_formal_decision_mapping_v1(
        _formal_decision()
    )


def test_exact16_normalized_routing_and_summary(result) -> None:
    assert subject.validate_covapie_poa_sample_level_effective_supervision_v1(
        result
    )
    records = result.records
    assert len(records) == len({record.canonical_event_id for record in records}) == 16
    assert sum(record.pdb_id == "4I3U" for record in records) == 8
    assert sum(record.pdb_id == "4I3V" for record in records) == 8
    assert all(record.human_review_completed for record in records)
    assert all(record.chemistry_positive for record in records)
    assert not any(record.chemistry_negative for record in records)
    assert {
        record.legacy_completed_review_status for record in records
    } == {reconciliation.COMPLETED_HUMAN_POSITIVE}
    assert sum(
        record.training_use_disposition == reconciliation.TRAINING_INCLUDE
        and not record.human_training_excluded
        for record in records
    ) == 8
    assert sum(
        record.training_use_disposition == reconciliation.TRAINING_EXCLUDE
        and record.human_training_excluded
        and record.chemistry_positive
        for record in records
    ) == 8
    assert result.summary.record_count == 16
    assert result.summary.chemistry_positive_count == 16
    assert result.summary.nongeometry_future_candidate_count == 8
    assert result.summary.training_admitted_count == 0


def test_exact_reactive_pair_role_profile_and_partition(result) -> None:
    for record in result.records:
        assert (
            record.target_residue_name,
            record.target_residue_atom_id,
            record.ligand_component_id,
            record.ligand_reactive_atom_id,
        ) == ("CYS", "SG", "POA", "C2")
        assert record.reactive_pair_authority_available
        assert not record.pair_candidate_domain_materialized
        assert record.source_role_profile == "STRICT_LINKER_PRESENT"
        assert (
            record.runtime_role_profile
            == direct_runtime.STRICT_LINKER_PRESENT_V1
        )
        assert record.scaffold_atom_ids == ("P", "O1P", "O2P", "O3P")
        assert record.linker_atom_ids == ("C1",)
        assert record.warhead_atom_ids == ("C2", "O2")
        roles = tuple(
            map(
                set,
                (
                    record.scaffold_atom_ids,
                    record.linker_atom_ids,
                    record.warhead_atom_ids,
                ),
            )
        )
        assert not any(
            roles[left] & roles[right]
            for left in range(3)
            for right in range(left + 1, 3)
        )
        assert set().union(*roles) == {
            "C1",
            "C2",
            "O1P",
            "O2",
            "O2P",
            "O3P",
            "P",
        }


def test_exact5_b3_and_mask_counts_use_published_runtime(result) -> None:
    record = result.records[0]
    assert record.valid_task_ids == (0, 1, 2, 3, 4)
    assert record.not_applicable_task_ids == ()
    assert direct_runtime.CANONICAL_TASKS_V1[3][1:3] == (
        "scaffold_only",
        "B3",
    )
    heavy = ("C1", "C2", "O1P", "O2", "O2P", "O3P", "P")
    by_atom = {atom: index for index, atom in enumerate(heavy)}
    roles = tuple(
        tuple(by_atom[atom] for atom in atom_ids)
        for atom_ids in (
            record.scaffold_atom_ids,
            record.linker_atom_ids,
            record.warhead_atom_ids,
        )
    )
    observed = []
    for task_id in record.valid_task_ids:
        mask = direct_runtime.build_mask_for_role_profile_v1(
            role_profile=record.runtime_role_profile,
            canonical_task_id=task_id,
            scaffold_atoms=roles[0],
            linker_atoms=roles[1],
            warhead_atoms=roles[2],
            num_ligand_atoms=7,
        )
        observed.append((len(mask.masked_atoms), len(mask.visible_atoms)))
    assert observed == [(2, 5), (3, 4), (6, 1), (4, 3), (7, 0)]


def test_task_c_targets_geometry_family_rule_and_admission_stay_inactive(
    result,
) -> None:
    assert all(record.task_structural_mask_labels_available for record in result.records)
    assert all(record.task_C_role_mask_available for record in result.records)
    assert not any(
        record.task_C_minimal_seed_authority_available for record in result.records
    )
    assert not any(
        record.full_task_C_training_supervision_ready for record in result.records
    )
    assert {
        record.precursor_evidence_status for record in result.records
    } == {"PRECURSOR_EVIDENCE_NOT_ESTABLISHED"}
    assert not any(
        record.PRE_reaction_graph_authority_available for record in result.records
    )
    assert not any(
        record.PRE_reaction_bond_order_authority_available
        for record in result.records
    )
    assert not any(
        record.PRE_geometry_training_authority_available for record in result.records
    )
    assert not any(
        record.POST_geometry_training_authority_available for record in result.records
    )
    assert not any(record.geometry_training_target_available for record in result.records)
    assert not any(
        record.reaction_family_authority_available for record in result.records
    )
    assert not any(record.reaction_family_target_available for record in result.records)
    assert not any(
        record.warhead_rule_authority_available for record in result.records
    )
    assert not any(record.warhead_rule_target_available for record in result.records)
    assert not any(record.warhead_type_target_available for record in result.records)
    assert not any(record.split_authoritative for record in result.records)
    assert not any(record.training_admitted for record in result.records)
    assert not result.summary.loss_active
    assert not result.summary.training_dataset_changed


def test_subgroup_descriptive_state_is_not_collapsed_or_a_target(result) -> None:
    by_pdb = {
        pdb_id: {record.subgroup_id for record in result.records if record.pdb_id == pdb_id}
        for pdb_id in ("4I3U", "4I3V")
    }
    assert by_pdb == {
        "4I3U": {"POA_SUBGROUP_G1_4I3U_THIOHEMIACETAL"},
        "4I3V": {"POA_SUBGROUP_G2_4I3V_THIOESTER"},
    }
    assert not any(
        record.chemistry_state_training_target_available for record in result.records
    )


def test_result_is_frozen_slotted_and_provenance_is_result_level(result) -> None:
    assert hasattr(result.records[0], "__slots__")
    with pytest.raises(FrozenInstanceError):
        result.records[0].pdb_id = "drift"
    provenance = result.source_provenance
    assert provenance.formal_decision_path.startswith("synthetic/")
    assert provenance.formal_decision_path_namespace == "synthetic"
    assert provenance.reconciliation_projection == "project_poa_formal_decision_v1"
    assert not hasattr(result.records[0], "formal_decision_sha256")


def test_public_real_payload_entry_point_fails_closed_before_compilation() -> None:
    bad_payloads = (
        b"{}",
        b"x" * subject.FORMAL_DECISION_BYTE_COUNT,
        "not-bytes",
    )
    for payload in bad_payloads:
        with pytest.raises(
            subject.POASampleLevelEffectiveSupervisionError,
            match=subject.ERROR_TOKEN,
        ):
            subject.build_covapie_poa_sample_level_effective_supervision_v1(
                payload  # type: ignore[arg-type]
            )


NEGATIVE_CASES = (
    "schema_drift",
    "review_unit_drift",
    "duplicate_event",
    "missing_event",
    "G1_G2_overlap",
    "unexpected_PDB",
    "unexpected_component",
    "ligand_reactive_atom_drift",
    "protein_reactive_atom_drift",
    "chemistry_positive_false",
    "G2_changed_chemistry_negative",
    "G2_changed_INCLUDE",
    "G1_changed_EXCLUDE",
    "human_exclusion_disposition_mismatch",
    "role_profile_unknown",
    "role_partition_overlap",
    "role_partition_union_incomplete",
    "warhead_atom_drift",
    "linker_atom_drift",
    "scaffold_atom_drift",
    "boundary_drift",
    "missing_B3",
    "sixth_task_inserted",
    "task_applicability_false",
    "Task_C_seed_promoted",
    "PRE_authority_promoted",
    "POST_geometry_authority_promoted",
    "family_target_promoted",
    "rule_target_promoted",
    "warhead_type_target_promoted",
    "training_admitted_promoted",
)


def _mutated_formal(case: str) -> dict[str, object]:
    formal = deepcopy(_formal_decision())
    groups = formal["subgroup_human_decisions"]
    assert isinstance(groups, list)
    g1, g2 = groups
    assert isinstance(g1, dict) and isinstance(g2, dict)
    g1_ids = g1["canonical_event_ids"]
    g2_ids = g2["canonical_event_ids"]
    assert isinstance(g1_ids, list) and isinstance(g2_ids, list)
    role = formal["role_human_decision"]
    masks = formal["canonical_exact5_mask_boundary"]
    precursor = formal["precursor_mapping_context"]
    post = formal["post_state_authority_boundary"]
    assert all(
        isinstance(value, dict) for value in (role, masks, precursor, post)
    )
    assert isinstance(role, dict)
    assert isinstance(masks, dict)
    assert isinstance(precursor, dict)
    assert isinstance(post, dict)

    if case == "schema_drift":
        formal["schema_version"] = "covapie_poa_formal_human_decision_v2"
    elif case == "review_unit_drift":
        formal["review_unit_id"] = "COVAPIE_BULK_REVIEW_UNIT_DRIFT"
    elif case == "duplicate_event":
        g1_ids[1] = g1_ids[0]
    elif case == "missing_event":
        g1_ids.pop()
        g1["event_count"] = 7
    elif case == "G1_G2_overlap":
        g2_ids[0] = g1_ids[0]
    elif case == "unexpected_PDB":
        g1["pdb_id"] = "9XYZ"
    elif case == "unexpected_component":
        g1_ids[0] = str(g1_ids[0]).replace(":POA:C2", ":XXX:C2")
    elif case == "ligand_reactive_atom_drift":
        g1_ids[0] = str(g1_ids[0]).replace(":POA:C2", ":POA:C9")
    elif case == "protein_reactive_atom_drift":
        g1_ids[0] = str(g1_ids[0]).replace(":SG:", ":SE:")
    elif case == "chemistry_positive_false":
        g1["CHEMISTRY_POSITIVE"] = False
    elif case == "G2_changed_chemistry_negative":
        g2["CHEMISTRY_POSITIVE"] = False
        g2["negative_chemistry"] = True
    elif case == "G2_changed_INCLUDE":
        g2["event_training_use_decision"] = "INCLUDE"
        g2["human_training_excluded"] = False
        g2["training_exclusion_scope"] = "NONE"
    elif case == "G1_changed_EXCLUDE":
        g1["event_training_use_decision"] = "EXCLUDE_FROM_TRAINING_ONLY"
        g1["human_training_excluded"] = True
        g1["training_exclusion_scope"] = "EXCLUDE_FROM_TRAINING_ONLY"
    elif case == "human_exclusion_disposition_mismatch":
        g2["human_training_excluded"] = False
    elif case == "role_profile_unknown":
        role["selected_role_profile"] = "STRICT_LINKER_PRESENT_V2"
    elif case == "role_partition_overlap":
        role["scaffold_atom_ids"] = ["P", "O1P", "O2P", "O3P", "C1"]
    elif case == "role_partition_union_incomplete":
        role["scaffold_atom_ids"] = ["P", "O1P", "O2P"]
    elif case == "warhead_atom_drift":
        role["warhead_atom_ids"] = ["C2", "O1P"]
    elif case == "linker_atom_drift":
        role["linker_atom_ids"] = ["P"]
    elif case == "scaffold_atom_drift":
        role["scaffold_atom_ids"] = ["C1", "O1P", "O2P", "O3P"]
    elif case == "boundary_drift":
        boundaries = role["boundaries"]
        assert isinstance(boundaries, list) and isinstance(boundaries[0], dict)
        boundaries[0]["CCD_bond_order"] = "DOUB"
    elif case == "missing_B3":
        tasks = masks["tasks"]
        assert isinstance(tasks, list)
        tasks.pop(3)
        masks["structurally_applicable_task_count"] = 4
    elif case == "sixth_task_inserted":
        tasks = masks["tasks"]
        assert isinstance(tasks, list)
        tasks.append(
            {
                "mask_index": 5,
                "semantic_long_name": "forbidden_sixth",
                "display_alias": "X",
                "structurally_applicable": True,
            }
        )
        masks["structurally_applicable_task_count"] = 6
        masks["sixth_task_created"] = True
    elif case == "task_applicability_false":
        tasks = masks["tasks"]
        assert isinstance(tasks, list) and isinstance(tasks[0], dict)
        tasks[0]["structurally_applicable"] = False
    elif case == "Task_C_seed_promoted":
        masks["full_task_C_seed_authority_granted"] = True
    elif case == "PRE_authority_promoted":
        precursor["PRE_REACTION_GRAPH_AUTHORITY"] = True
    elif case == "POST_geometry_authority_promoted":
        post["new_POST_geometry_training_target_created"] = True
    elif case == "family_target_promoted":
        formal["reaction_family_target_available"] = True
    elif case == "rule_target_promoted":
        formal["warhead_rule_target_available"] = True
    elif case == "warhead_type_target_promoted":
        formal["warhead_type_target_available"] = True
    elif case == "training_admitted_promoted":
        formal["training_admitted"] = True
    else:
        raise AssertionError(case)
    return formal


@pytest.mark.parametrize("case", NEGATIVE_CASES)
def test_all_semantic_drift_fails_closed_with_one_error_token(case: str) -> None:
    with pytest.raises(
        subject.POASampleLevelEffectiveSupervisionError,
        match=subject.ERROR_TOKEN,
    ):
        subject._compile_synthetic_formal_decision_mapping_v1(
            _mutated_formal(case)
        )
