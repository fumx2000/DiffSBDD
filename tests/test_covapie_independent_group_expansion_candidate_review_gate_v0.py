from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_candidate_review_gate_v0")
EXPECTED = ["1AEC/E64", "1AIM/ZYA", "1AU3/PCM", "1AU4/INP", "1AYU/INA", "1AYV/IN6", "1AYW/IN3", "1B02/UFP"]


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def manifest() -> dict:
    return json.loads((ROOT / "covapie_independent_group_expansion_candidate_review_gate_manifest.json").read_text(encoding="utf-8"))


def test_candidate_review_registry_and_diversity() -> None:
    review = rows("covapie_expansion_candidate_review_registry.csv")
    diversity = rows("covapie_expansion_candidate_diversity_review.csv")[0]
    assert len(review) == 8
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in review] == EXPECTED
    assert len({(row["pdb_id"], row["expected_het_id"]) for row in review}) == 8
    assert len({row["expected_het_id"] for row in review}) == 8
    for row in review:
        for key in ["source_identity_complete_confirmed", "cys_sg_v1_scope_confirmed", "non_jug_candidate_confirmed", "not_current_sample_index_pair_confirmed", "not_known_blocked_pair_confirmed", "unique_pdb_het_pair_confirmed", "unique_het_representative_confirmed", "historical_struct_conn_evidence_available_confirmed", "raw_acquisition_required_confirmed", "struct_conn_crosscheck_required_confirmed", "ligand_graph_evidence_pending_confirmed", "protein_sequence_evidence_pending_confirmed", "provisional_independence_pending_confirmed", "approved_for_controlled_acquisition_preflight"]:
            assert row[key] == "True"
        assert row["approved_for_acquisition_execution"] == "False"
        assert row["confirmed_as_new_independent_group"] == "False"
        assert row["candidate_review_decision"] == "approved_for_controlled_acquisition_preflight_only"
        assert row["candidate_review_status"] == "passed"
    assert diversity["candidate_count"] == diversity["unique_pdb_het_pair_count"] == diversity["distinct_non_jug_het_id_count"] == "8"
    assert diversity["confirmed_independent_group_count"] == "0"
    assert diversity["acquisition_diversity_target_met"] == "True"
    assert diversity["independence_confirmation_target_met"] == "False"


def test_preflight_only_boundaries_and_readiness() -> None:
    plan = rows("covapie_expansion_acquisition_preflight_approval_plan.csv")
    decisions = rows("covapie_expansion_candidate_review_decision_registry.csv")
    issues = rows("covapie_expansion_candidate_review_issue_inventory.csv")
    evidence = rows("covapie_expansion_candidate_review_evidence_boundary_contract.csv")
    safety = rows("covapie_expansion_candidate_review_safety_audit.csv")
    data = manifest()
    assert len(plan) == 8 and len(decisions) == 7 and len(evidence) == 12
    for row in plan:
        assert row["planned_raw_filename"] == f"{row['pdb_id'].lower()}.cif"
        assert row["approved_for_acquisition_preflight"] == "True"
        for key in ["acquisition_execution_authorized", "network_access_authorized", "download_authorized", "raw_file_written_current_step", "scientific_independence_confirmed", "ready_for_training_current_step"]:
            assert row[key] == "False"
    assert {row["decision_status"] for row in decisions} == {"accepted"}
    assert issues[0]["issue_id"] == "NO_EXPANSION_CANDIDATE_REVIEW_ISSUES"
    assert {row["boundary_contract_passed"] for row in evidence} == {"True"}
    assert {row["safety_passed"] for row in safety} == {"True"}
    assert data["all_checks_passed"] is True
    assert data["candidate_review_approved_for_preflight_count"] == 8
    assert data["candidate_review_approved_for_execution_count"] == 0
    assert data["confirmed_new_independent_group_count_current_step"] == 0
    assert data["ready_for_covapie_independent_group_expansion_acquisition_preflight_gate"] is True
    assert data["ready_for_covapie_independent_group_expansion_acquisition_execution"] is False
    assert data["ready_for_training"] is False
    assert data["feature_semantics_known_for_training"] is False
    assert data["unknown_atom_feature_policy_finalized_for_training"] is False
    assert data["recommended_next_step"] == "covapie_independent_group_expansion_acquisition_preflight_gate"
