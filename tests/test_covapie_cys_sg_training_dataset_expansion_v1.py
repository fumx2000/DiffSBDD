from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import (
    project_type_symbols_to_checkpoint_heavy_v1,
)
from covalent_ext import covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer


INVENTORY = (
    ROOT
    / "data/derived/covalent_small/covapie_cys_sg_training_dataset_expansion_v1"
    / "covapie_cys_sg_non_exact16_candidate_inventory.csv"
)
REVIEW_PACKET = INVENTORY.with_name(
    "covapie_cys_sg_near_ready_human_review_packet_v1.md"
)
EXPANDED_CANDIDATES = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1/"
    "covapie_cys_sg_expanded_candidate_inventory_and_eligibility.csv"
)
EXACT12_SNAPSHOT = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_execution_v1/"
    "covapie_cys_sg_exact12_post_acquisition_structural_recovery_snapshot.csv"
)
RECOVERED7_EVIDENCE = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1/"
    "covapie_cys_sg_recovered7_canonical_model_graph_and_pocket_evidence.json"
)
RECOVERED7_CLOSURE = RECOVERED7_EVIDENCE.with_name(
    "covapie_cys_sg_recovered7_canonical_closure_matrix.csv"
)
DIRECT_CONFIRMED = (
    ROOT
    / "data/derived/covalent_small/"
    "real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/"
    "real_covalent_struct_conn_confirmed_candidate_table.csv"
)
DIRECT_PAIR = (
    ROOT
    / "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_table_v1_altloc_aware.csv"
)
DIRECT_POCKET = (
    ROOT
    / "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
)
DIRECT_MODEL_INPUT = (
    ROOT
    / "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_model_input_materialization_smoke_v0/"
    "model_input_smoke_index.csv"
)
DIRECT_ROLE_DRAFT = (
    ROOT
    / "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0/"
    "ligand_observed_atom_topology_smoke_table.csv"
)
DIRECT_PRE_WRITEBACK = (
    ROOT
    / "data/derived/covalent_small/pre_reaction_graph/"
    "pre_reaction_transform_manual_write_back_report.csv"
)
DIRECT_PRE_READINESS = DIRECT_PRE_WRITEBACK.with_name(
    "pre_reaction_training_readiness_gate_report.csv"
)
ROLE_RULE_REGISTRY = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/"
    "covapie_ligand_role_annotation_rule_registry.csv"
)
REVIEW_POLICY_REGISTRY = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1/"
    "covapie_reaction_family_and_warhead_rule_review_policy_registry.csv"
)
FAMILY_RULE_AUTHORITY_REGISTRY = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/"
    "covapie_family_and_warhead_rule_authority_registry.csv"
)
TARGETED_SEED_AUDIT = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_cys_sg_targeted_metadata_expansion_gate_v0/"
    "covapie_cys_sg_targeted_seed_candidate_audit.csv"
)
LEAKAGE_ASSIGNMENTS = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "covapie_final_leakage_group_assignment.csv"
)
SPLIT_ASSIGNMENTS = (
    ROOT
    / "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_sample_split_assignment.csv"
)
STATE_ROOT = ROOT.parent / "covapie-state"
RECOVERED7_REVIEW_TEMPLATE = (
    STATE_ROOT
    / "manual-review-aids/recovered7-targeted-chemistry-review-v1/"
    "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
    "C0E3CCE067B699C68B74C8260D5479A4D3FF5454A5B40B68EA11DDA2B147E2AD/"
    "review_decision_template.csv"
)
K36_REVIEW_AUTHORITY_DIR = (
    STATE_ROOT
    / "manual-review/recovered7-targeted-chemistry-review-v1/"
    "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
    "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92"
)
DIRECT_ROLE_TEMPLATES = {
    "6DI9": ROOT / "data/raw/covalent_small/metadata/BTK_C481_6DI9_GJJ_annotation_template.csv",
    "5F2E": ROOT / "data/raw/covalent_small/metadata/KRAS_G12C_5F2E_5UT_annotation_template.csv",
    "6OIM": ROOT / "data/raw/covalent_small/metadata/KRAS_G12C_6OIM_MOV_annotation_template.csv",
}
DIRECT_PRE_SDFS = {
    "6DI9": ROOT / "data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf",
    "5F2E": ROOT / "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf",
    "6OIM": ROOT / "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf",
}
EXACT4_IDENTITIES = ("2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV")

EXACT16_IDENTITIES = {
    *(f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)),
    "4DCD/K36",
    "4F49/K36",
    "5WKJ/K36",
    "6L70/K36",
    "6WTT/K36",
}
EXPECTED_COLUMNS = (
    "candidate_identity",
    "pdb_id",
    "ligand_comp_id",
    "source_kind",
    "source_relative_path",
    "source_SHA256",
    "explicit_covalent_event_available",
    "explicit_covalent_event_authority",
    "protein_reactive_endpoint",
    "ligand_reactive_endpoint",
    "protein_endpoint_exact_CYS_SG",
    "ligand_endpoint_identity",
    "endpoint_mapping_unique",
    "endpoint_retained_in_model_projection",
    "checkpoint_feature_semantics_valid",
    "unsupported_nonhydrogen_count",
    "explicit_hydrogen_handling_valid",
    "observed_complex_distance_available",
    "observed_complex_distance_angstrom",
    "role_authority_status",
    "seed_anchor_authority_status",
    "warhead_authority_status",
    "reaction_family_authority_status",
    "warhead_rule_authority_status",
    "profile_candidate",
    "existing_leakage_group",
    "existing_split_or_none",
    "POST_authority_eligible",
    "PRE_authority_status",
    "blocking_reasons",
    "final_classification",
)


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == EXPECTED_COLUMNS or path != INVENTORY
        return list(reader)


def _inventory() -> list[dict[str, str]]:
    return _csv(INVENTORY)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _truth(value: str) -> bool:
    assert value in {"true", "false"}
    return value == "true"


def test_inventory_is_exact_non_exact16_population_and_has_no_ready_member() -> None:
    rows = _inventory()
    identities = [row["candidate_identity"] for row in rows]
    assert len(rows) == len(set(identities)) == 12
    assert not set(identities) & EXACT16_IDENTITIES
    assert Counter(row["final_classification"] for row in rows) == {
        "READY_AFTER_HUMAN_APPROVAL": 4,
        "NEEDS_RUNTIME_PROFILE_EXTENSION": 1,
        "MISSING_SOURCE_AUTHORITY": 5,
        "REJECT": 2,
    }
    assert all(
        row["final_classification"] != "READY_FOR_TRAINABLE_EXPANSION"
        for row in rows
    )


def test_every_candidate_source_sha_is_live_and_verified() -> None:
    for row in _inventory():
        source = ROOT / row["source_relative_path"]
        assert source.is_file()
        assert _sha256(source) == row["source_SHA256"]


def test_targeted_mmcif_recovery_distinguishes_exact_events_from_missing_authority() -> None:
    snapshot = {row["pdb_id"]: row for row in _csv(EXACT12_SNAPSHOT)}
    inventory = {row["pdb_id"]: row for row in _inventory()}
    assert set(snapshot) >= {"1A54", "2DJF", "6VWE", "2R9F", "6WTJ", "7C8U", "6WTK"}
    for pdb_id in ("2DJF", "2R9F"):
        assert snapshot[pdb_id]["cys_sg_event_recovered"] == "true"
        assert snapshot[pdb_id]["explicit_connection_evidence_status"] == (
            "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
        )
        assert _truth(inventory[pdb_id]["explicit_covalent_event_available"])
    for pdb_id in ("1A54", "6VWE", "6WTJ", "7C8U", "6WTK"):
        assert snapshot[pdb_id]["cys_sg_event_recovered"] == "false"
        assert snapshot[pdb_id]["explicit_connection_evidence_status"] == (
            "STRUCT_CONN_LOOP_ABSENT"
        )
        assert not _truth(inventory[pdb_id]["explicit_covalent_event_available"])
        assert inventory[pdb_id]["final_classification"] == "MISSING_SOURCE_AUTHORITY"


def test_recovered_1zb_and_k2z_endpoint_projection_geometry_and_disposition() -> None:
    evidence = json.loads(RECOVERED7_EVIDENCE.read_text(encoding="utf-8"))
    samples = {
        f"{sample['pdb_id']}/{sample['ligand_component_id']}": sample
        for sample in evidence["samples"]
    }
    inventory = {row["candidate_identity"]: row for row in _inventory()}
    for identity in ("2DJF/1ZB", "2R9F/K2Z"):
        sample = samples[identity]
        row = inventory[identity]
        protein = sample["explicit_event"]["protein_endpoint"]
        ligand = sample["explicit_event"]["ligand_endpoint"]
        assert protein["auth_comp_id"] == "CYS"
        assert protein["auth_atom_id"] == "SG"
        assert sample["exact10"] == {
            "channel_order": "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9",
            "explicit_hydrogen_excluded_count": 0,
            "status": "EXACT10_PASS",
            "unknown_or_other_channel_present": False,
            "unsupported_nonh_model_bound_atoms": [],
            "zero_vector_fallback_used": False,
        }
        ligand_matches = [
            atom
            for atom in sample["canonical_model_bound_ligand_atoms"]
            if atom["atom_site_id"] == ligand["atom_site_id"]
        ]
        protein_matches = [
            atom
            for atom in sample["canonical_pocket"]["retained_atoms"]
            if atom["atom_site_id"] == protein["atom_site_id"]
        ]
        assert len(ligand_matches) == len(protein_matches) == 1
        distance = math.dist(
            [float(ligand_matches[0][axis]) for axis in ("x", "y", "z")],
            [float(protein_matches[0][axis]) for axis in ("x", "y", "z")],
        )
        assert math.isclose(
            distance,
            float(row["observed_complex_distance_angstrom"]),
            abs_tol=5e-10,
        )
        assert _truth(row["POST_authority_eligible"])
        assert row["PRE_authority_status"] == "MISSING_MASKED"
    assert inventory["2DJF/1ZB"]["final_classification"] == (
        "READY_AFTER_HUMAN_APPROVAL"
    )
    assert inventory["2R9F/K2Z"]["final_classification"] == (
        "NEEDS_RUNTIME_PROFILE_EXTENSION"
    )


def test_pdb_direct_three_have_real_endpoints_features_and_post_but_not_role_authority() -> None:
    confirmed = {row["pdb_id"]: row for row in _csv(DIRECT_CONFIRMED)}
    pair = {row["pdb_id"]: row for row in _csv(DIRECT_PAIR)}
    model_input = {row["pdb_id"]: row for row in _csv(DIRECT_MODEL_INPUT)}
    inventory = {row["pdb_id"]: row for row in _inventory()}
    pocket_rows = _csv(DIRECT_POCKET)
    role_rows = _csv(DIRECT_ROLE_DRAFT)
    for pdb_id in ("6DI9", "5F2E", "6OIM"):
        row = inventory[pdb_id]
        assert confirmed[pdb_id]["manual_review_validated"] == "True"
        assert confirmed[pdb_id]["manual_confirmed_residue_atom_id"] == "SG"
        assert pair[pdb_id]["coordinate_pair_sanity_passed"] == "True"
        assert math.isclose(
            float(pair[pdb_id]["computed_endpoint_distance_angstrom"]),
            float(row["observed_complex_distance_angstrom"]),
            abs_tol=5e-5,
        )
        ligand_projection = project_type_symbols_to_checkpoint_heavy_v1(
            tuple(
                atom["atom_symbol"]
                for atom in role_rows
                if atom["pdb_id"] == pdb_id
            )
        )
        pocket_projection = project_type_symbols_to_checkpoint_heavy_v1(
            tuple(
                atom["type_symbol"]
                for atom in pocket_rows
                if atom["pdb_id"] == pdb_id
            )
        )
        assert not ligand_projection.sample_rejected
        assert not pocket_projection.sample_rejected
        assert model_input[pdb_id]["training_use_status"] == "not_training_input_yet"
        assert {
            atom["training_use_status"]
            for atom in role_rows
            if atom["pdb_id"] == pdb_id
        } == {"not_training_input_yet"}
        assert row["role_authority_status"] == (
            "HISTORICAL_DRAFT_PROPOSAL_ONLY;HUMAN_GOLD_AUTHORITY_REQUIRED"
        )
        assert row["final_classification"] == "READY_AFTER_HUMAN_APPROVAL"
        assert _truth(row["POST_authority_eligible"])


def test_published_policy_not_lifecycle_status_requires_human_chemistry_approval() -> None:
    role_rules = {row["rule_id"]: row for row in _csv(ROLE_RULE_REGISTRY)}
    gold = role_rules["LRMSR_021"]
    assert gold["rule_status"] == "required"
    assert gold["rule_semantics"] == "training authority is gold_curated only"
    assert gold["failure_reason"] == "current11_gold_without_human_review"
    assert gold["fails_closed"] == gold["verified"] == "true"

    policies = {
        row["policy_id"]: row for row in _csv(REVIEW_POLICY_REGISTRY)
    }
    expected = {
        "REVIEW_POLICY_002": "family identity requires explicit human approval",
        "REVIEW_POLICY_004": "approved warhead rule requires approved SMARTS",
        "REVIEW_POLICY_008": "sample assignment requires independent sample review",
        "REVIEW_POLICY_010": "gold requires approved family rule and sample assignment",
        "REVIEW_POLICY_011": "role proposal requires approved family rule and gold sample",
    }
    for policy_id, semantic_name in expected.items():
        assert policies[policy_id]["semantic_name"] == semantic_name
        assert policies[policy_id]["fails_closed"] == "true"
        assert policies[policy_id]["verified"] == "true"

    registry = _csv(FAMILY_RULE_AUTHORITY_REGISTRY)
    assert len(registry) == 7
    assert {row["reaction_family_authority_status"] for row in registry} == {
        "candidate_only"
    }
    assert {row["approval_status"] for row in registry} == {"candidate_only"}

    for name in ("reaction_family_authority_v1.json", "warhead_rule_authority_v1.json"):
        authority = json.loads((K36_REVIEW_AUTHORITY_DIR / name).read_text())
        applicability = authority["canonical_semantic_signature"]["applicability_scope"]
        assert applicability["cross_signature_propagation_allowed"] is False
        assert applicability["required_chemistry_signature_sha256"] == (
            "83e9c7b9d43444d7e50fbfd7e6c3dafef5e0dc92cf1a7c571e3f4e3fe4e08d92"
        )
        assert applicability["required_chemistry_signature_sha256"] != (
            "c0e3cce067b699c68b74c8260d5479a4d3ff5454a5b40b68ea11dda2b147e2ad"
        )


def test_1zb_upstream_audit_is_human_required_and_its_review_is_blank() -> None:
    closure = {
        f"{row['pdb_id']}/{row['ligand_component_id']}": row
        for row in _csv(RECOVERED7_CLOSURE)
    }["2DJF/1ZB"]
    assert closure["mechanical_closure_status"] == "MECHANICAL_CLOSURE_PASS"
    assert closure["downstream_chemistry_label_status"] == (
        "HUMAN_CHEMISTRY_REVIEW_REQUIRED"
    )
    assert closure["primary_remaining_issue"] == (
        "REACTION_FAMILY_APPROVED_RULE_NO_MATCH"
    )

    evidence = json.loads(RECOVERED7_EVIDENCE.read_text(encoding="utf-8"))
    sample = next(sample for sample in evidence["samples"] if sample["pdb_id"] == "2DJF")
    audit = sample["downstream_chemistry_authority_audit"]
    assert audit["combined_status"] == "HUMAN_CHEMISTRY_REVIEW_REQUIRED"
    assert audit["reaction_family"]["authority_status"] == (
        "APPROVED_REUSABLE_RULE_NO_MATCH"
    )
    assert audit["warhead_rule"]["authority_status"] == (
        "APPROVED_REUSABLE_RULE_NO_MATCH"
    )
    assert audit["warhead_atom_set"]["authority_status"] == (
        "SAMPLE_BOUND_AUTHORITY_NO_MATCH"
    )
    assert audit["role_assignment"]["authority_status"] == (
        "APPROVED_DETERMINISTIC_RULE_NO_MATCH"
    )
    assert audit["anchor_role"]["authority_status"] == (
        "NOT_APPLICABLE_UNTIL_ROLE_ASSIGNMENT_RESOLVED"
    )

    review = _csv(RECOVERED7_REVIEW_TEMPLATE)
    assert len(review) == 1
    assert review[0]["review_class_member_identities"] == '["2DJF/1ZB"]'
    assert review[0]["review_status"] == review[0]["review_scope"] == "NOT_REVIEWED"
    assert review[0]["reviewed_warhead_atom_ids"] == "[]"
    assert review[0]["reviewed_scaffold_atom_ids"] == "[]"
    assert review[0]["reviewed_linker_atom_ids"] == "[]"
    assert review[0]["reviewed_minimal_seed_atom_ids"] == "[]"


def _draft_cross_role_edges(
    rows: list[dict[str, str]],
) -> dict[frozenset[str], set[tuple[int, str, int, str]]]:
    by_index = {int(row["sdf_atom_index"]): row for row in rows}
    result: dict[frozenset[str], set[tuple[int, str, int, str]]] = {}
    for row in rows:
        index = int(row["sdf_atom_index"])
        for neighbor in filter(None, row["neighbors"].split(";")):
            other_index = int(neighbor.split(":", 1)[0])
            if index >= other_index:
                continue
            other = by_index[other_index]
            if row["final_role"] == other["final_role"]:
                continue
            key = frozenset((row["final_role"], other["final_role"]))
            result.setdefault(key, set()).add(
                (
                    index,
                    row["pdb_atom_name"],
                    other_index,
                    other["pdb_atom_name"],
                )
            )
    return result


def test_direct3_pre_graph_is_approved_but_role_partition_remains_only_a_draft() -> None:
    writeback = {row["sample_id"]: row for row in _csv(DIRECT_PRE_WRITEBACK)}
    readiness = {row["sample_id"]: row for row in _csv(DIRECT_PRE_READINESS)}
    expected_roles = {
        "6DI9": {
            "warhead": {17, 18, 19, 32},
            "linker": {13, 14, 15, 23, 24, 28, 29},
            "scaffold_linker_count": 2,
        },
        "5F2E": {
            "warhead": {8, 27, 28, 29},
            "linker": {7, 24, 25, 26},
            "scaffold_linker_count": 1,
        },
        "6OIM": {
            "warhead": {4, 5, 6, 7},
            "linker": {0, 1, 2, 3, 8, 9, 10},
            "scaffold_linker_count": 1,
        },
    }
    sample_ids = {
        "6DI9": "BTK_C481_6DI9",
        "5F2E": "KRAS_G12C_5F2E",
        "6OIM": "KRAS_G12C_6OIM",
    }
    expected_transforms = {
        "6DI9": ("CYS:SG-19", "18-19:double"),
        "5F2E": ("CYS:SG-29", "8-29:double"),
        "6OIM": ("CYS:SG-7", "6-7:double"),
    }
    for pdb_id, role_template in DIRECT_ROLE_TEMPLATES.items():
        sample_id = sample_ids[pdb_id]
        assert writeback[sample_id]["reviewer_decision"] == "approved"
        assert writeback[sample_id]["review_status"] == "reviewed"
        assert writeback[sample_id]["write_back_status"] == (
            "written_after_explicit_human_approval"
        )
        assert writeback[sample_id]["training_ready"] == "false"
        assert (
            writeback[sample_id]["manual_covalent_bond_to_remove"],
            writeback[sample_id]["manual_bond_order_to_restore"],
        ) == expected_transforms[pdb_id]
        assert readiness[sample_id]["safe_as_derived_pre_reaction_artifact"] == "true"
        assert readiness[sample_id]["training_ready"] == "false"
        assert _sha256(DIRECT_PRE_SDFS[pdb_id]) in REVIEW_PACKET.read_text(
            encoding="utf-8"
        )

        rows = _csv(role_template)
        assert {int(row["sdf_atom_index"]) for row in rows if row["final_role"] == "warhead"} == expected_roles[pdb_id]["warhead"]
        assert {int(row["sdf_atom_index"]) for row in rows if row["final_role"] == "linker"} == expected_roles[pdb_id]["linker"]
        proposed = [row for row in rows if row["final_role"] != "scaffold"]
        assert proposed
        assert all("workflow smoke test draft" in row["notes"] for row in proposed)
        assert all("final scientific training requires" in row["notes"] for row in proposed)

        cross_edges = _draft_cross_role_edges(rows)
        assert len(cross_edges[frozenset(("linker", "warhead"))]) == 1
        assert len(cross_edges[frozenset(("scaffold", "linker"))]) == expected_roles[pdb_id]["scaffold_linker_count"]

    seed_audit_payload = TARGETED_SEED_AUDIT.read_text(encoding="utf-8")
    assert not any(token in seed_audit_payload for token in ("6DI9", "GJJ", "5F2E", "5UT", "6OIM", "MOV"))


def test_exact4_is_not_registered_in_profile_leakage_or_split_owners() -> None:
    for identity in EXACT4_IDENTITIES:
        with pytest.raises(ValueError, match="SAMPLE_IDENTITY_NOT_IN_INTEGRATION_POPULATION"):
            mixed_tensorizer.valid_task_ids_for_covapie_expanded_cys_sg_sample_v1(identity)

    assignment_payload = LEAKAGE_ASSIGNMENTS.read_text(encoding="utf-8") + SPLIT_ASSIGNMENTS.read_text(encoding="utf-8")
    for identity in EXACT4_IDENTITIES:
        pdb_id, ligand = identity.split("/")
        assert identity not in assignment_payload
        assert f"{pdb_id}_{ligand}" not in assignment_payload


def test_single_packet_is_actionable_complete_and_has_blank_decision_fields() -> None:
    packets = list(INVENTORY.parent.glob("*human_review_packet*"))
    assert packets == [REVIEW_PACKET]
    payload = REVIEW_PACKET.read_text(encoding="utf-8")
    assert "`MACHINE_RESOLVABLE_NOW = 0`" in payload
    assert "`TRUE_HUMAN_APPROVAL_REQUIRED = 4`" in payload
    assert "`OTHER_BLOCKER = 0`" in payload
    assert "`human_approve_covapie_near_ready_expansion_candidates_v1`" in payload
    assert "2R9F/K2Z` remains deferred" in payload
    assert sum(line.startswith("| ") and any(line.startswith(f"| {i}.") for i in range(1, 15)) for line in payload.splitlines()) == 14
    for identity in EXACT4_IDENTITIES:
        assert f'candidate_identity: "{identity}"' in payload
    assert payload.count('review_status: ""  # APPROVE | REJECT | QUARANTINE') == 4
    assert payload.count('independent_sample_assignment_decision: ""  # APPROVE | REJECT | QUARANTINE') == 4
    assert payload.count('reviewed_minimal_seed_atom_ids: ""') == 4
    assert 'review_status: "APPROVE"' not in payload
    assert 'independent_sample_assignment_decision: "APPROVE"' not in payload
    for source in (
        EXPANDED_CANDIDATES,
        DIRECT_CONFIRMED,
        DIRECT_PAIR,
        RECOVERED7_CLOSURE,
        RECOVERED7_EVIDENCE,
        ROLE_RULE_REGISTRY,
        REVIEW_POLICY_REGISTRY,
        FAMILY_RULE_AUTHORITY_REGISTRY,
        RECOVERED7_REVIEW_TEMPLATE,
        K36_REVIEW_AUTHORITY_DIR / "reaction_family_authority_v1.json",
        K36_REVIEW_AUTHORITY_DIR / "warhead_rule_authority_v1.json",
        *DIRECT_ROLE_TEMPLATES.values(),
        *DIRECT_PRE_SDFS.values(),
    ):
        assert _sha256(source) in payload


def test_all_pre_is_masked_and_only_exact_retained_pairs_are_post_eligible() -> None:
    for row in _inventory():
        assert row["PRE_authority_status"] == "MISSING_MASKED"
        post = _truth(row["POST_authority_eligible"])
        if post:
            assert _truth(row["explicit_covalent_event_available"])
            assert _truth(row["protein_endpoint_exact_CYS_SG"])
            assert _truth(row["endpoint_mapping_unique"])
            assert _truth(row["endpoint_retained_in_model_projection"])
            assert _truth(row["checkpoint_feature_semantics_valid"])
            assert _truth(row["observed_complex_distance_available"])
            assert math.isfinite(float(row["observed_complex_distance_angstrom"]))
