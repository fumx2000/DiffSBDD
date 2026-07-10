from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_independent_group_expansion_design_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_design_gate_v0")


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def manifest() -> dict:
    return json.loads((ROOT / "covapie_independent_group_expansion_design_gate_manifest.json").read_text(encoding="utf-8"))


def test_source_inventory_and_deterministic_shortlist() -> None:
    source = rows("covapie_expansion_candidate_source_inventory.csv")
    shortlist = rows("covapie_independent_group_candidate_shortlist.csv")
    exclusions = rows("covapie_expansion_candidate_exclusion_audit.csv")
    assert len(source) == 25
    assert source == sorted(source, key=lambda row: row["source_candidate_id"])
    assert len(shortlist) == 8
    assert [row["shortlist_rank"] for row in shortlist] == [str(index) for index in range(1, 9)]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in shortlist] == ["1AEC/E64", "1AIM/ZYA", "1AU3/PCM", "1AU4/INP", "1AYU/INA", "1AYV/IN6", "1AYW/IN3", "1B02/UFP"]
    assert len({(row["pdb_id"], row["expected_het_id"]) for row in shortlist}) == len(shortlist)
    assert len({row["expected_het_id"] for row in shortlist}) == 8
    assert {row["expected_het_id"] for row in shortlist}.isdisjoint({"JUG", "MDC"})
    assert len(exclusions) == 17
    assert {(row["pdb_id"], row["expected_het_id"]) for row in source if row["already_in_current_sample_index"] == "True"} == {("6BV6", "JUG"), ("6BV8", "JUG"), ("6BV5", "JUG")}
    codes = {(row["pdb_id"], row["expected_het_id"]): row["exclusion_reason_code"] for row in exclusions}
    assert codes[("1A54", "MDC")] == "known_struct_conn_blocked"
    assert codes[("6BV9", "JUG")] == "known_ligand_comp_mismatch"
    assert codes[("1ATK", "E64")] == "lower_priority_duplicate_het_representative"


def test_boundaries_evidence_and_readiness() -> None:
    candidate_rows = rows("covapie_independent_group_candidate_shortlist.csv")
    plan_rows = rows("covapie_independent_group_acquisition_batch_plan.csv")
    evidence_rows = rows("covapie_independence_evidence_requirement_contract.csv")
    safety_rows = rows("covapie_independent_group_expansion_safety_audit.csv")
    data = manifest()
    for row in candidate_rows:
        assert row["residue_name"] == "CYS" and row["residue_atom_name"] == "SG"
        assert row["provisional_group_candidate_id"] == f"PROVISIONAL_HET_{row['expected_het_id']}"
        assert row["provisional_grouping_basis"] == "distinct_non_jug_het_id_for_acquisition_diversification_only"
        assert row["struct_conn_crosscheck_required"] == "True"
        assert row["ligand_graph_evidence_status"] == "pending_canonical_graph_hash_and_scaffold_review"
        assert row["protein_sequence_evidence_status"] == "pending_accession_and_sequence_cluster"
        assert row["provisional_independence_status"] == "pending_not_yet_independent_group"
    assert len(plan_rows) == len(candidate_rows)
    for row in plan_rows:
        assert row["raw_acquisition_authorized_current_step"] == "False"
        assert row["network_access_authorized_current_step"] == "False"
        assert row["manual_approval_required"] == "True"
        assert row["ready_for_acquisition_preflight"] == "True"
        assert row["ready_for_training_current_step"] == "False"
    assert len(evidence_rows) == 12 and {row["requirement_contract_passed"] for row in evidence_rows} == {"True"}
    assert {row["safety_passed"] for row in safety_rows} == {"True"}
    assert data["all_checks_passed"] is True
    assert data["confirmed_new_independent_group_count_current_step"] == 0
    assert data["ready_for_covapie_independent_group_expansion_candidate_review_gate"] is True
    assert data["ready_for_covapie_independent_group_expansion_acquisition_preflight"] is False
    assert data["ready_for_training"] is False
    assert data["feature_semantics_known_for_training"] is False
    assert data["unknown_atom_feature_policy_finalized_for_training"] is False
    assert data["feature_semantics_audit_required_before_training"] is True
    assert data["canonical_mask_task_aliases"] == ["A", "B", "B2", "B3", "C"]
    assert data["recommended_next_step"] == "covapie_independent_group_expansion_candidate_review_gate"
