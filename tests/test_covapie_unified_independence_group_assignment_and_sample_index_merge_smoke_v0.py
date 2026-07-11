from __future__ import annotations
import copy
import csv
import json
import shutil
from collections import defaultdict
import pytest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from covalent_ext import covapie_unified_independence_group_assignment_and_sample_index_merge_smoke as smoke
def test_must_link_policy_axes() -> None:
    base={"combined_pairwise_independence_evidence_classification":"provisional_distinct_both_axes","same_ligand_graph":"False","same_murcko_scaffold":"False","same_protein_accession":"False","same_exact_protein_sequence":"False","same_sequence_cluster_90":"False","same_sequence_cluster_50":"False"}
    assert smoke.decide_pair({**base,"same_ligand_graph":"True"})["direct_must_link_edge"] is True
    assert smoke.decide_pair({**base,"same_sequence_cluster_50":"True"})["direct_must_link_edge"] is True
    assert smoke.decide_pair(base)["direct_must_link_edge"] is False
    assert smoke.decide_pair({**base,"combined_pairwise_independence_evidence_classification":"evidence_incomplete"})["direct_must_link_edge"] is False
def test_transitive_groups_are_deterministic() -> None:
    rows=[{"left_sample_index_row_id":"A","right_sample_index_row_id":"B","direct_must_link_edge":True},{"left_sample_index_row_id":"B","right_sample_index_row_id":"C","direct_must_link_edge":True}]
    assert smoke.groups(["A","B","C","D"],rows)=={"A":"COVAPIE_LEAKAGE_GROUP_000001","B":"COVAPIE_LEAKAGE_GROUP_000001","C":"COVAPIE_LEAKAGE_GROUP_000001","D":"COVAPIE_LEAKAGE_GROUP_000002"}
def test_current_assignment_contract() -> None:
    m=smoke.run()["manifest"]
    assert m["all_checks_passed"] is True
    assert m["final_leakage_group_sizes"]==[3,1,1,5,1]
    assert m["direct_must_link_edge_count"]==13
    assert m["confirmed_new_independent_group_count_current_step"]==4
    assert m["ready_for_training"] is False

@pytest.mark.parametrize("field", smoke.SAMPLE_INDEX_FIELDS)
def test_unified_index_preserves_each_canonical_schema_field(field: str) -> None:
    rows = list(csv.DictReader(smoke.rp(smoke.OUT["unified_sample_index.csv"]).open()))
    assert len(rows) == 11
    assert field in rows[0]
    assert "final_leakage_group_id" not in rows[0]


def _validator_inputs() -> dict[str, object]:
    result = smoke.run()
    rows = smoke.read_csv(smoke.PILOT) + smoke.read_csv(smoke.EXP)
    ligand = smoke.read_csv(smoke.EVIDENCE / "covapie_ligand_graph_scaffold_evidence.csv")
    protein = smoke.read_csv(smoke.EVIDENCE / "covapie_protein_sequence_accession_evidence.csv")
    decisions = result["decisions"]
    assignment = {
        row["sample_index_row_id"]: row["final_leakage_group_id"]
        for row in result["assignment"]
    }
    members: dict[str, list[str]] = defaultdict(list)
    for sample_id, group_id in assignment.items():
        members[group_id].append(sample_id)
    candidates = smoke.build_candidate_assignment_rows(
        rows, decisions, ligand, protein, assignment, members
    )
    return {
        "rows": rows,
        "ligand": ligand,
        "protein": protein,
        "decisions": decisions,
        "assignment": assignment,
        "members": members,
        "candidates": candidates,
    }


def _validate_assignment(data: dict[str, object], candidates=None, ligand=None, protein=None):
    return smoke.validate_assignment_rows(
        candidates if candidates is not None else data["candidates"],
        data["rows"],
        data["decisions"],
        ligand if ligand is not None else data["ligand"],
        protein if protein is not None else data["protein"],
        data["assignment"],
        data["members"],
    )


def test_assignment_validator_accepts_valid_rows() -> None:
    data = _validator_inputs()
    validated = _validate_assignment(data)
    assert len(validated) == 11
    assert all(row["final_group_assignment_passed"] for row in validated)


def test_assignment_validator_rejects_wrong_neighbor_count() -> None:
    data = _validator_inputs()
    candidates = copy.deepcopy(data["candidates"])
    candidates[0]["direct_must_link_neighbor_count"] += 1
    validated = _validate_assignment(data, candidates=candidates)
    assert validated[0]["final_group_assignment_passed"] is False
    assert "direct_neighbor_count_mismatch" in validated[0]["blocking_reasons"]


def test_assignment_validator_rejects_wrong_member_count() -> None:
    data = _validator_inputs()
    candidates = copy.deepcopy(data["candidates"])
    candidates[0]["final_leakage_group_member_count"] += 1
    validated = _validate_assignment(data, candidates=candidates)
    assert validated[0]["final_group_assignment_passed"] is False
    assert "final_group_member_count_mismatch" in validated[0]["blocking_reasons"]


def test_assignment_validator_handles_missing_ligand_evidence() -> None:
    data = _validator_inputs()
    sample_id = data["candidates"][0]["sample_index_row_id"]
    ligand = [row for row in data["ligand"] if row["sample_index_row_id"] != sample_id]
    validated = _validate_assignment(data, ligand=ligand)
    assert validated[0]["final_group_assignment_passed"] is False
    assert "missing_ligand_evidence_row" in validated[0]["blocking_reasons"]


def test_assignment_validator_rejects_duplicate_ligand_evidence() -> None:
    data = _validator_inputs()
    ligand = copy.deepcopy(data["ligand"])
    ligand.append(copy.deepcopy(ligand[0]))
    validated = _validate_assignment(data, ligand=ligand)
    assert validated[0]["final_group_assignment_passed"] is False
    assert "duplicate_ligand_evidence_row" in validated[0]["blocking_reasons"]


def test_assignment_validator_handles_missing_protein_evidence() -> None:
    data = _validator_inputs()
    sample_id = data["candidates"][0]["sample_index_row_id"]
    protein = [row for row in data["protein"] if row["sample_index_row_id"] != sample_id]
    validated = _validate_assignment(data, protein=protein)
    assert validated[0]["final_group_assignment_passed"] is False
    assert "missing_protein_evidence_row" in validated[0]["blocking_reasons"]


def _inventory_inputs() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    data = _validator_inputs()
    assignments = _validate_assignment(data)
    candidates = smoke.build_candidate_group_inventory_rows(
        data["members"], data["decisions"], data["rows"]
    )
    return data, assignments, candidates


def test_group_inventory_validator_accepts_valid_rows() -> None:
    data, assignments, candidates = _inventory_inputs()
    validated = smoke.validate_group_inventory_rows(
        candidates, assignments, data["decisions"], data["rows"]
    )
    assert len(validated) == 5
    assert all(row["group_inventory_passed"] for row in validated)


def test_group_inventory_validator_rejects_membership_mismatch() -> None:
    data, assignments, candidates = _inventory_inputs()
    candidates[1]["member_sample_index_row_ids"] = candidates[2]["member_sample_index_row_ids"]
    validated = smoke.validate_group_inventory_rows(
        candidates, assignments, data["decisions"], data["rows"]
    )
    assert not all(row["group_inventory_passed"] for row in validated)
    assert any("assignment_inventory_membership_mismatch" in row["blocking_reasons"] for row in validated)


def test_group_inventory_validator_rejects_internal_edge_count_mismatch() -> None:
    data, assignments, candidates = _inventory_inputs()
    candidates[0]["direct_internal_must_link_edge_count"] += 1
    validated = smoke.validate_group_inventory_rows(
        candidates, assignments, data["decisions"], data["rows"]
    )
    assert validated[0]["group_inventory_passed"] is False
    assert "direct_internal_edge_count_mismatch" in validated[0]["blocking_reasons"]


def test_group_inventory_validator_rejects_cross_group_direct_edge() -> None:
    data, assignments, candidates = _inventory_inputs()
    decisions = copy.deepcopy(data["decisions"])
    left_sample = candidates[1]["member_sample_index_row_ids"].split(";")[0]
    right_sample = candidates[2]["member_sample_index_row_ids"].split(";")[0]
    decisions.append(
        {
            "left_sample_index_row_id": left_sample,
            "right_sample_index_row_id": right_sample,
            "direct_must_link_edge": True,
            "ligand_axis_must_link": True,
            "protein_axis_must_link": False,
        }
    )
    validated = smoke.validate_group_inventory_rows(
        candidates, assignments, decisions, data["rows"]
    )
    assert not all(row["group_inventory_passed"] for row in validated)
    assert all("cross_group_direct_edge" in row["blocking_reasons"] for row in validated)


def _synthetic_assignment_rows() -> list[dict[str, object]]:
    rows=[]
    for n,(sample_id,pdb_id,ligand_id) in enumerate(smoke.EXPECTED,1):
        rows.append({
            "assignment_id":f"COVAPIE_ASSIGNMENT_{n:06d}",
            "sample_index_row_id":sample_id,
            "pdb_id":pdb_id,
            "ligand_comp_id":ligand_id,
            "source_index_stage":"pilot" if n<=3 else "expansion",
            "ligand_graph_group_id":f"LG_{n:06d}",
            "ligand_scaffold_group_id":f"LS_{n:06d}",
            "protein_exact_sequence_group_id":f"PE_{n:06d}",
            "protein_accession_group_id":f"PA_{n:06d}",
            "protein_sequence_cluster_90_id":f"P90_{n:06d}",
            "protein_sequence_cluster_50_id":f"P50_{n:06d}",
            "direct_must_link_neighbor_count":0,
            "final_leakage_group_id":f"COVAPIE_LEAKAGE_GROUP_{n:06d}",
            "final_leakage_group_member_count":1,
            "final_leakage_group_status":"provisional_independent_singleton_within_current_11_sample_set",
            "assignment_policy":smoke.POLICY,
            "final_group_assignment_passed":True,
            "eligible_for_split_materialization_current_step":True,
            "ready_for_training_current_step":False,
            "feature_semantics_audit_required_before_training":True,
            "leakage_split_design_required_before_training":True,
            "blocking_reasons":"",
        })
    return rows


def _write_assignment_fixture(tmp_path: Path, rows: list[dict[str, object]], fields=None):
    csv_path=tmp_path/"assignment.csv"; json_path=tmp_path/"assignment.json"
    smoke.write_csv(csv_path,rows,fields or smoke.ASSIGNMENT_FIELDS)
    smoke.write_json(json_path,rows)
    return csv_path,json_path


def test_r1b_valid_assignment_write_reread_passes(tmp_path: Path) -> None:
    rows=_synthetic_assignment_rows(); csv_path,json_path=_write_assignment_fixture(tmp_path,rows)
    result=smoke.validate_written_assignment(rows,csv_path,json_path)
    assert result["assignment_write_validation_passed"] is True
    assert result["assignment_csv_json_consistent"] is True


def test_r1b_assignment_csv_tamper_is_detected(tmp_path: Path) -> None:
    rows=_synthetic_assignment_rows(); csv_path,json_path=_write_assignment_fixture(tmp_path,rows)
    tampered=copy.deepcopy(rows); tampered[0]["pdb_id"]="XXXX"
    smoke.write_csv(csv_path,tampered,smoke.ASSIGNMENT_FIELDS)
    result=smoke.validate_written_assignment(rows,csv_path,json_path)
    assert result["assignment_write_validation_passed"] is False
    assert result["assignment_csv_json_consistent"] is False


def test_r1b_assignment_json_tamper_is_detected(tmp_path: Path) -> None:
    rows=_synthetic_assignment_rows(); csv_path,json_path=_write_assignment_fixture(tmp_path,rows)
    tampered=copy.deepcopy(rows); tampered[0]["ligand_comp_id"]="XXX"
    smoke.write_json(json_path,tampered)
    result=smoke.validate_written_assignment(rows,csv_path,json_path)
    assert result["assignment_write_validation_passed"] is False
    assert result["assignment_source_preservation_passed"] is False


def test_r1b_assignment_csv_field_order_mismatch_is_detected(tmp_path: Path) -> None:
    rows=_synthetic_assignment_rows(); csv_path,json_path=_write_assignment_fixture(tmp_path,rows)
    fields=list(smoke.ASSIGNMENT_FIELDS); fields[0],fields[1]=fields[1],fields[0]
    smoke.write_csv(csv_path,rows,fields)
    result=smoke.validate_written_assignment(rows,csv_path,json_path)
    assert result["assignment_csv_field_order_passed"] is False
    assert result["assignment_write_validation_passed"] is False


def test_r1b_assignment_row_order_mismatch_is_detected(tmp_path: Path) -> None:
    rows=_synthetic_assignment_rows(); reordered=copy.deepcopy(rows); reordered[0],reordered[1]=reordered[1],reordered[0]
    csv_path,json_path=_write_assignment_fixture(tmp_path,reordered)
    result=smoke.validate_written_assignment(rows,csv_path,json_path)
    assert result["assignment_csv_json_consistent"] is True
    assert result["assignment_row_order_passed"] is False


def _trace_inputs():
    source_csv=smoke.read_csv(smoke.PILOT)+smoke.read_csv(smoke.EXP)
    source_json=json.loads(smoke.rp(smoke.PILOT_JSON).read_text())+json.loads(smoke.rp(smoke.EXP_JSON).read_text())
    unified_csv=[smoke.typed(row) for row in source_csv]
    unified_json=copy.deepcopy(source_json)
    assignment=_synthetic_assignment_rows()
    return source_csv,source_json,unified_csv,unified_json,assignment,copy.deepcopy(assignment)


def test_r1b_valid_traceability_rows_all_pass() -> None:
    inputs=_trace_inputs(); rows=smoke.build_merge_traceability_rows(*inputs)
    assert len(rows)==11
    assert all(row["merge_traceability_passed"] for row in rows)


def test_r1b_missing_unified_csv_row_causes_trace_failure() -> None:
    inputs=list(_trace_inputs()); inputs[2]=inputs[2][1:]
    rows=smoke.build_merge_traceability_rows(*inputs)
    assert rows[0]["merge_traceability_passed"] is False
    assert "unified_csv_row_missing" in rows[0]["blocking_reasons"]


def test_r1b_unified_csv_json_value_mismatch_causes_trace_failure() -> None:
    inputs=list(_trace_inputs()); inputs[2][0]["pdb_id"]="XXXX"
    rows=smoke.build_merge_traceability_rows(*inputs)
    assert rows[0]["unified_csv_json_consistent"] is False
    assert "unified_csv_json_mismatch" in rows[0]["blocking_reasons"]


def test_r1b_missing_assignment_json_row_causes_trace_failure() -> None:
    inputs=list(_trace_inputs()); inputs[5]=inputs[5][1:]
    rows=smoke.build_merge_traceability_rows(*inputs)
    assert rows[0]["final_group_assignment_row_found"] is False
    assert "assignment_json_row_missing" in rows[0]["blocking_reasons"]


def test_r1b_missing_artifact_path_causes_trace_failure() -> None:
    inputs=list(_trace_inputs())
    missing="data/derived/covalent_small/does_not_exist/protein_atom_table.csv"
    inputs[2][0]["protein_atom_table_path"]=missing; inputs[3][0]["protein_atom_table_path"]=missing
    rows=smoke.build_merge_traceability_rows(*inputs)
    assert rows[0]["artifact_paths_still_exist"] is False
    assert "artifact_path_missing" in rows[0]["blocking_reasons"]


def test_r1b_traceability_written_file_tamper_is_detected(tmp_path: Path) -> None:
    trace=smoke.build_merge_traceability_rows(*_trace_inputs()); path=tmp_path/"trace.csv"
    tampered=copy.deepcopy(trace); tampered[0]["merge_traceability_passed"]=False
    smoke.write_csv(path,tampered,smoke.TRACEABILITY_FIELDS)
    result=smoke.validate_written_traceability(trace,path)
    assert result["traceability_written_validation_passed"] is False


def _r1c_observations(tmp_path: Path):
    names={
        "unified_sample_index_csv_written":"unified_sample_index.csv",
        "unified_sample_index_json_written":"unified_sample_index.json",
        "final_group_assignment_csv_written":"assignment.csv",
        "final_group_assignment_json_written":"assignment.json",
        "group_inventory_csv_written":"inventory.csv",
        "pairwise_assignment_audit_written":"pairwise.csv",
        "merge_traceability_csv_written":"trace.csv",
        "schema_validation_audit_written":"schema.csv",
    }
    outputs={key:tmp_path/name for key,name in names.items()}
    for path in outputs.values(): path.write_text("x\n")
    observations=smoke.build_safety_observations(
        read_paths=set(),written_paths=set(),
        embedded_assignment_qa_passed=True,
        embedded_schema_qa_passed=True,
        embedded_traceability_qa_passed=True,
        scan_roots=[tmp_path],output_paths=outputs,
    )
    return observations,outputs


def test_r1c_safety_observation_keys_exactly_match_expected(tmp_path: Path) -> None:
    observations,_=_r1c_observations(tmp_path)
    assert set(observations)==set(smoke.SAFETY_EXPECTED)
    assert len(observations)==39


def test_r1c_valid_observations_produce_39_passed_rows(tmp_path: Path) -> None:
    observations,_=_r1c_observations(tmp_path); rows=smoke.build_safety_rows(observations)
    assert len(rows)==39
    assert all(row["safety_passed"] for row in rows)


def test_r1c_tmp_file_sets_part_or_tmp_observation(tmp_path: Path) -> None:
    (tmp_path/"leftover.tmp").write_text("x")
    observations,_=_r1c_observations(tmp_path)
    assert observations["part_or_tmp_files_remaining"] is True


def test_r1c_part_file_sets_part_or_tmp_observation(tmp_path: Path) -> None:
    (tmp_path/"download.part").write_text("x")
    observations,_=_r1c_observations(tmp_path)
    assert observations["part_or_tmp_files_remaining"] is True


def test_r1c_pt_file_is_forbidden_but_not_part_or_tmp(tmp_path: Path) -> None:
    (tmp_path/"tensor.pt").write_text("x")
    observations,_=_r1c_observations(tmp_path)
    assert observations["forbidden_artifacts_present"] is True
    assert observations["part_or_tmp_files_remaining"] is False


def test_r1c_split_artifact_is_detected(tmp_path: Path) -> None:
    (tmp_path/"candidate_split_assignments.csv").write_text("x")
    observations,_=_r1c_observations(tmp_path)
    assert observations["split_assignments_written"] is True


def test_r1c_leakage_matrix_artifact_is_detected(tmp_path: Path) -> None:
    (tmp_path/"pairwise_leakage_matrix.csv").write_text("x")
    observations,_=_r1c_observations(tmp_path)
    assert observations["leakage_matrix_written"] is True


def test_r1c_final_dataset_artifact_is_detected(tmp_path: Path) -> None:
    (tmp_path/"final_dataset.csv").write_text("x")
    observations,_=_r1c_observations(tmp_path)
    assert observations["final_dataset_written"] is True


def test_r1c_missing_required_output_is_detected(tmp_path: Path) -> None:
    _,outputs=_r1c_observations(tmp_path); outputs["group_inventory_csv_written"].unlink()
    observations=smoke.build_safety_observations(
        read_paths=set(),written_paths=set(),embedded_assignment_qa_passed=True,
        embedded_schema_qa_passed=True,embedded_traceability_qa_passed=True,
        scan_roots=[tmp_path],output_paths=outputs,
    )
    assert observations["group_inventory_csv_written"] is False


def test_r1c_unexpected_staged_observation_blocks_safety(tmp_path: Path) -> None:
    observations,_=_r1c_observations(tmp_path); observations["unexpected_staged_files_present"]=True
    rows=smoke.build_safety_rows(observations)
    row=next(row for row in rows if row["safety_item"]=="unexpected_staged_files_present")
    assert row["safety_passed"] is False
    assert "safety_mismatch:unexpected_staged_files_present" in row["blocking_reasons"]


def test_r1c_blocking_safety_row_produces_failed_issue_without_sentinel(tmp_path: Path) -> None:
    observations,_=_r1c_observations(tmp_path); observations["forbidden_artifacts_present"]=True
    safety=smoke.build_safety_rows(observations)
    issues,blockers=smoke.build_issue_rows([row["blocking_reasons"] for row in safety if not row["safety_passed"]])
    assert blockers
    assert all(row["issue_status"]=="failed" for row in issues)
    assert not any(row["issue_id"]=="NO_UNIFIED_ASSIGNMENT_OR_SAMPLE_INDEX_MERGE_ISSUES" for row in issues)


def test_r1c_fully_passed_audits_produce_one_sentinel(tmp_path: Path) -> None:
    observations,_=_r1c_observations(tmp_path); safety=smoke.build_safety_rows(observations)
    issues,blockers=smoke.build_issue_rows([row["blocking_reasons"] for row in safety if not row["safety_passed"]])
    assert blockers==[]
    assert len(issues)==1
    assert issues[0]["issue_id"]=="NO_UNIFIED_ASSIGNMENT_OR_SAMPLE_INDEX_MERGE_ISSUES"


def test_r1c_issue_blockers_are_deduplicated_and_sorted() -> None:
    issues,blockers=smoke.build_issue_rows(["zeta","alpha","zeta"])
    assert blockers==["alpha","zeta"]
    assert [row["issue_description"] for row in issues]==blockers
    assert [row["issue_id"] for row in issues]==["COVAPIE_ASSIGNMENT_ISSUE_000001","COVAPIE_ASSIGNMENT_ISSUE_000002"]


def test_r1c_embedded_assignment_qa_is_derived_from_all_aggregates(tmp_path: Path) -> None:
    _,outputs=_r1c_observations(tmp_path)
    observations=smoke.build_safety_observations(
        read_paths=set(),written_paths=set(),embedded_assignment_qa_passed=True,
        embedded_schema_qa_passed=False,embedded_traceability_qa_passed=True,
        scan_roots=[tmp_path],output_paths=outputs,
    )
    assert observations["embedded_assignment_qa_performed"] is False


def _r2a_input_bundle(tmp_path: Path) -> smoke.InputPaths:
    source=smoke.DEFAULT_INPUT_PATHS; values={}
    for name in smoke.LOGICAL_INPUT_NAMES:
        original=smoke.rp(getattr(source,name)); target=tmp_path/name/original.name
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(original,target); values[name]=target
    return smoke.InputPaths(**values)


def _r2a_load(paths: smoke.InputPaths):
    return smoke.load_inputs_safely(paths,smoke.RunActivity())


def _r2a_redirect_outputs(monkeypatch, tmp_path: Path) -> None:
    root=tmp_path/"blocked_outputs"
    monkeypatch.setattr(smoke,"ROOT",root)
    monkeypatch.setattr(smoke,"OUT",{name:root/name for name in smoke.OUT})
    monkeypatch.setattr(smoke,"SUMMARY",tmp_path/"summary.md")


def test_r2a_complete_input_bundle_loads_without_blockers(tmp_path: Path) -> None:
    loaded=_r2a_load(_r2a_input_bundle(tmp_path))
    assert loaded.input_load_passed is True
    assert loaded.blocking_reasons==[]


def test_r2a_missing_pilot_csv_returns_blocker(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_csv.unlink(); loaded=_r2a_load(paths)
    assert loaded.input_load_passed is False
    assert any("pilot_csv" in reason for reason in loaded.blocking_reasons)


def test_r2a_malformed_pilot_json_returns_blocker(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_json.write_text("{bad json")
    loaded=_r2a_load(paths)
    assert "unreadable_json:pilot_index" in loaded.blocking_reasons


def test_r2a_pilot_json_dict_root_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_json.write_text("{}")
    loaded=_r2a_load(paths)
    assert "invalid_json_root_type:pilot_index" in loaded.blocking_reasons


def test_r2a_pilot_json_non_dict_row_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_json.write_text("[1]")
    loaded=_r2a_load(paths)
    assert "invalid_json_row_type:pilot_index:1" in loaded.blocking_reasons


def test_r2a_missing_step14ao_manifest_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.step14ao_manifest.unlink(); loaded=_r2a_load(paths)
    assert "unreadable_json:step14ao_manifest" in loaded.blocking_reasons


def test_r2a_malformed_step14ao_manifest_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.step14ao_manifest.write_text("not-json"); loaded=_r2a_load(paths)
    assert "unreadable_json:step14ao_manifest" in loaded.blocking_reasons


def test_r2a_step14ao_manifest_missing_required_field_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); manifest=json.loads(paths.step14ao_manifest.read_text()); manifest.pop("stage"); paths.step14ao_manifest.write_text(json.dumps(manifest))
    loaded=_r2a_load(paths)
    assert "missing_manifest_field:step14ao_manifest:stage" in loaded.blocking_reasons


def test_r2a_ligand_evidence_missing_required_column_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); rows=smoke.read_csv(paths.ligand_evidence); fields=[field for field in rows[0] if field!="blocking_reasons"]
    smoke.write_csv(paths.ligand_evidence,rows,fields); loaded=_r2a_load(paths)
    assert "missing_csv_column:ligand_evidence:blocking_reasons" in loaded.blocking_reasons


def test_r2a_missing_combined_pairwise_file_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.combined_pairwise.unlink(); loaded=_r2a_load(paths)
    assert any("combined_pairwise" in reason for reason in loaded.blocking_reasons)


def test_r2a_header_only_evidence_csv_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); rows=smoke.read_csv(paths.protein_pairwise); smoke.write_csv(paths.protein_pairwise,[],list(rows[0])); loaded=_r2a_load(paths)
    assert "header_only_csv:protein_pairwise" in loaded.blocking_reasons


def test_r2a_blocked_writer_emits_all_12_fixed_schema_artifacts(tmp_path: Path, monkeypatch) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_csv.unlink(); _r2a_redirect_outputs(monkeypatch,tmp_path); result=smoke.run(paths)
    assert len(smoke.OUT)==12
    assert all(smoke.rp(path).is_file() for path in smoke.OUT.values())
    assert list(csv.DictReader(smoke.rp(smoke.OUT["unified_sample_index.csv"]).open()).fieldnames)==smoke.SAMPLE_INDEX_FIELDS
    assert list(csv.DictReader(smoke.rp(smoke.OUT["covapie_final_leakage_group_assignment.csv"]).open()).fieldnames)==smoke.ASSIGNMENT_FIELDS
    assert result["manifest"]["input_blocked_output_contract_written"] is True


def test_r2a_blocked_manifest_readiness_is_false(tmp_path: Path, monkeypatch) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_csv.unlink(); _r2a_redirect_outputs(monkeypatch,tmp_path); manifest=smoke.run(paths)["manifest"]
    assert manifest["all_checks_passed"] is False
    assert manifest["ready_for_covapie_unified_leakage_split_materialization_smoke"] is False
    assert manifest["ready_for_training"] is False


def test_r2a_blocked_issue_inventory_has_no_sentinel(tmp_path: Path, monkeypatch) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_csv.unlink(); _r2a_redirect_outputs(monkeypatch,tmp_path); result=smoke.run(paths)
    assert result["manifest"]["blocking_issue_count"]>0
    assert all(row["issue_status"]=="failed" for row in result["issue_rows"])
    assert not any(row["issue_id"]=="NO_UNIFIED_ASSIGNMENT_OR_SAMPLE_INDEX_MERGE_ISSUES" for row in result["issue_rows"])


def test_r2a_blocked_path_does_not_produce_groups_or_assignments(tmp_path: Path, monkeypatch) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.combined_pairwise.unlink(); _r2a_redirect_outputs(monkeypatch,tmp_path); result=smoke.run(paths)
    assert result["assignment"]==[] and result["inventory"]==[] and result["decisions"]==[]
    assert result["manifest"]["final_leakage_group_count"]==0


def test_r2a_blocked_path_records_no_raw_or_network_activity(tmp_path: Path, monkeypatch) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.step14ao_manifest.unlink(); _r2a_redirect_outputs(monkeypatch,tmp_path); observations=smoke.run(paths)["safety_observations"]
    assert observations["raw_entry_files_read_current_step"] is False
    assert observations["ccd_raw_files_read_current_step"] is False
    assert observations["raw_files_modified"] is False
    assert observations["network_access_used_current_step"] is False


def _r2b_semantic(paths: smoke.InputPaths):
    loaded=_r2a_load(paths)
    assert loaded.input_load_passed, loaded.blocking_reasons
    return smoke.validate_loaded_inputs_semantically(loaded)


def _rewrite_csv(path: Path, mutate) -> None:
    rows=smoke.read_csv(path); mutate(rows); smoke.write_csv(path,rows,list(rows[0]))


def _rewrite_json(path: Path, mutate) -> None:
    rows=json.loads(path.read_text()); mutate(rows); path.write_text(json.dumps(rows))


def test_r2b_complete_bundle_semantic_validation_passes(tmp_path: Path) -> None:
    result=_r2b_semantic(_r2a_input_bundle(tmp_path))
    assert result.semantic_validation_passed is True
    assert result.blocking_reasons==[]


def test_r2b_invalid_sample_index_boolean_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.pilot_csv,lambda rows:rows[0].__setitem__("ready_for_training_current_step","yes")); result=_r2b_semantic(paths)
    assert any(reason.startswith("invalid_boolean:pilot_csv:1:ready_for_training_current_step") for reason in result.blocking_reasons)


def test_r2b_invalid_sample_index_integer_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.pilot_csv,lambda rows:rows[0].__setitem__("protein_atom_count","1.0")); result=_r2b_semantic(paths)
    assert any(reason.startswith("invalid_integer:pilot_csv:1:protein_atom_count") for reason in result.blocking_reasons)


def test_r2b_nan_bond_distance_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.pilot_csv,lambda rows:rows[0].__setitem__("bond_distance_angstrom","NaN")); result=_r2b_semantic(paths)
    assert any(reason.startswith("invalid_float:pilot_csv:1:bond_distance_angstrom") for reason in result.blocking_reasons)


def test_r2b_sample_csv_json_value_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.pilot_csv,lambda rows:rows[0].__setitem__("pdb_id","XXXX")); result=_r2b_semantic(paths)
    assert "sample_index_csv_json_mismatch:CYS_SG_SAMPLE_INDEX_000001:pdb_id" in result.blocking_reasons


def test_r2b_duplicate_sample_id_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path)
    for path,rewrite in [(paths.pilot_csv,_rewrite_csv),(paths.pilot_json,_rewrite_json)]: rewrite(path,lambda rows:rows[1].__setitem__("sample_index_row_id",rows[0]["sample_index_row_id"]))
    result=_r2b_semantic(paths)
    assert "duplicate_sample_index_row_id:CYS_SG_SAMPLE_INDEX_000001" in result.blocking_reasons


def test_r2b_ligand_evidence_duplicate_row_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.ligand_evidence,lambda rows:rows.append(copy.deepcopy(rows[0]))); result=_r2b_semantic(paths)
    assert "duplicate_ligand_evidence_row:CYS_SG_SAMPLE_INDEX_000001" in result.blocking_reasons


def test_r2b_ligand_evidence_pdb_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.ligand_evidence,lambda rows:rows[0].__setitem__("pdb_id","XXXX")); result=_r2b_semantic(paths)
    assert "ligand_evidence_pdb_mismatch:CYS_SG_SAMPLE_INDEX_000001" in result.blocking_reasons


def test_r2b_protein_evidence_empty_group_id_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.protein_evidence,lambda rows:rows[0].__setitem__("protein_sequence_cluster_50_id","")); result=_r2b_semantic(paths)
    assert "protein_sequence_cluster_50_id_missing:CYS_SG_SAMPLE_INDEX_000001" in result.blocking_reasons


def test_r2b_ligand_group_inventory_membership_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.ligand_group_inventory,lambda rows:rows[0].__setitem__("member_sample_index_row_ids","CYS_SG_SAMPLE_INDEX_000001")); result=_r2b_semantic(paths)
    assert any(reason.startswith("ligand_group_membership_mismatch:") for reason in result.blocking_reasons)


def test_r2b_protein_group_inventory_membership_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.protein_group_inventory,lambda rows:rows[0].__setitem__("member_sample_index_row_ids","CYS_SG_SAMPLE_INDEX_000001")); result=_r2b_semantic(paths)
    assert any(reason.startswith("protein_group_membership_mismatch:") for reason in result.blocking_reasons)


def test_r2b_duplicate_ligand_pair_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.ligand_pairwise,lambda rows:rows.append(copy.deepcopy(rows[0]))); result=_r2b_semantic(paths)
    assert any(reason.startswith("duplicate_pair:ligand_pairwise:") for reason in result.blocking_reasons)


def test_r2b_missing_protein_pair_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.protein_pairwise,lambda rows:rows.pop()); result=_r2b_semantic(paths)
    assert any(reason.startswith("missing_pair:protein_pairwise:") for reason in result.blocking_reasons)


def test_r2b_reversed_combined_pair_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path)
    def reverse(rows): rows[0]["left_sample_index_row_id"],rows[0]["right_sample_index_row_id"]=rows[0]["right_sample_index_row_id"],rows[0]["left_sample_index_row_id"]
    _rewrite_csv(paths.combined_pairwise,reverse); result=_r2b_semantic(paths)
    assert any(reason.startswith("reversed_pair:combined_pairwise:") for reason in result.blocking_reasons)


def test_r2b_wrong_ligand_pair_id_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.ligand_pairwise,lambda rows:rows[0].__setitem__("ligand_pairwise_evidence_id","WRONG")); result=_r2b_semantic(paths)
    assert "pair_id_mismatch:ligand_pairwise:1" in result.blocking_reasons


def test_r2b_ligand_graph_flag_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.ligand_pairwise,lambda rows:rows[0].__setitem__("same_ligand_graph","False" if rows[0]["same_ligand_graph"]=="True" else "True")); result=_r2b_semantic(paths)
    assert any(reason.startswith("ligand_pair_graph_flag_mismatch:") for reason in result.blocking_reasons)


def test_r2b_protein_cluster50_flag_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.protein_pairwise,lambda rows:rows[0].__setitem__("same_sequence_cluster_50","False" if rows[0]["same_sequence_cluster_50"]=="True" else "True")); result=_r2b_semantic(paths)
    assert any(reason.startswith("protein_pair_cluster50_flag_mismatch:") for reason in result.blocking_reasons)


def test_r2b_protein_identity_out_of_range_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.protein_pairwise,lambda rows:rows[0].__setitem__("protein_sequence_identity","2.0")); result=_r2b_semantic(paths)
    assert any(reason.startswith("invalid_protein_sequence_identity:") for reason in result.blocking_reasons)


def test_r2b_combined_flag_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.combined_pairwise,lambda rows:rows[0].__setitem__("same_murcko_scaffold","False" if rows[0]["same_murcko_scaffold"]=="True" else "True")); result=_r2b_semantic(paths)
    assert any(reason.startswith("combined_ligand_flag_mismatch:") for reason in result.blocking_reasons)


def test_r2b_combined_identity_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.combined_pairwise,lambda rows:rows[0].__setitem__("protein_sequence_identity","0.123")); result=_r2b_semantic(paths)
    assert any(reason.startswith("combined_identity_mismatch:") for reason in result.blocking_reasons)


def test_r2b_classification_mismatch_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.combined_pairwise,lambda rows:rows[0].__setitem__("combined_pairwise_independence_evidence_classification","provisional_distinct_both_axes")); result=_r2b_semantic(paths)
    assert any(reason.startswith("combined_classification_mismatch:") for reason in result.blocking_reasons)


def test_r2b_evidence_incomplete_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.combined_pairwise,lambda rows:rows[0].__setitem__("combined_pairwise_independence_evidence_classification","evidence_incomplete")); result=_r2b_semantic(paths)
    assert any(reason.startswith("evidence_incomplete:") for reason in result.blocking_reasons)


def _r2b_semantic_blocked_run(tmp_path: Path, monkeypatch):
    paths=_r2a_input_bundle(tmp_path); _rewrite_csv(paths.ligand_evidence,lambda rows:rows[0].__setitem__("pdb_id","XXXX")); _r2a_redirect_outputs(monkeypatch,tmp_path); return smoke.run(paths)


def test_r2b_semantic_blocked_writer_produces_12_artifacts(tmp_path: Path, monkeypatch) -> None:
    result=_r2b_semantic_blocked_run(tmp_path,monkeypatch)
    assert sum(smoke.rp(path).is_file() for path in smoke.OUT.values())==12
    assert result["manifest"]["premerge_block_scope"]=="semantic_validation"


def test_r2b_semantic_blocked_path_produces_zero_groups_and_assignments(tmp_path: Path, monkeypatch) -> None:
    result=_r2b_semantic_blocked_run(tmp_path,monkeypatch)
    assert result["assignment"]==[] and result["inventory"]==[] and result["decisions"]==[]


def test_r2b_semantic_blocked_manifest_readiness_is_false(tmp_path: Path, monkeypatch) -> None:
    manifest=_r2b_semantic_blocked_run(tmp_path,monkeypatch)["manifest"]
    assert manifest["input_load_passed"] is True and manifest["semantic_validation_passed"] is False
    assert manifest["ready_for_covapie_unified_leakage_split_materialization_smoke"] is False and manifest["ready_for_training"] is False


def test_r2b_semantic_blocked_issue_inventory_has_no_sentinel(tmp_path: Path, monkeypatch) -> None:
    result=_r2b_semantic_blocked_run(tmp_path,monkeypatch)
    assert result["manifest"]["blocking_issue_count"]>0
    assert not any(row["issue_id"]=="NO_UNIFIED_ASSIGNMENT_OR_SAMPLE_INDEX_MERGE_ISSUES" for row in result["issue_rows"])


def test_r2b_normal_path_exact_five_group_memberships() -> None:
    result=smoke.run(); actual=defaultdict(list)
    for row in result["assignment"]: actual[row["final_leakage_group_id"]].append(row["sample_index_row_id"])
    assert dict(actual)=={
        "COVAPIE_LEAKAGE_GROUP_000001":["CYS_SG_SAMPLE_INDEX_000001","CYS_SG_SAMPLE_INDEX_000002","CYS_SG_SAMPLE_INDEX_000003"],
        "COVAPIE_LEAKAGE_GROUP_000002":["CYS_SG_SAMPLE_INDEX_000004"],
        "COVAPIE_LEAKAGE_GROUP_000003":["CYS_SG_SAMPLE_INDEX_000005"],
        "COVAPIE_LEAKAGE_GROUP_000004":["CYS_SG_SAMPLE_INDEX_000006","CYS_SG_SAMPLE_INDEX_000007","CYS_SG_SAMPLE_INDEX_000008","CYS_SG_SAMPLE_INDEX_000009","CYS_SG_SAMPLE_INDEX_000010"],
        "COVAPIE_LEAKAGE_GROUP_000005":["CYS_SG_SAMPLE_INDEX_000011"],
    }


def test_final_cleanup_input_loading_blocker_uses_input_scope(tmp_path: Path, monkeypatch) -> None:
    paths=_r2a_input_bundle(tmp_path); paths.pilot_csv.unlink(); _r2a_redirect_outputs(monkeypatch,tmp_path); result=smoke.run(paths)
    assert "input_loading_failed_before_schema_validation" in result["manifest"]["blocking_reasons"]


def test_final_cleanup_semantic_blocker_uses_semantic_scope(tmp_path: Path, monkeypatch) -> None:
    result=_r2b_semantic_blocked_run(tmp_path,monkeypatch)
    assert "semantic_validation_failed_before_schema_validation" in result["manifest"]["blocking_reasons"]


def test_final_cleanup_semantic_blocker_excludes_input_scope_label(tmp_path: Path, monkeypatch) -> None:
    result=_r2b_semantic_blocked_run(tmp_path,monkeypatch)
    assert "input_loading_failed_before_schema_validation" not in result["manifest"]["blocking_reasons"]
    assert all(row["blocking_reasons"]=="semantic_validation_failed_before_schema_validation" for row in smoke.read_csv(smoke.OUT["covapie_unified_sample_index_schema_validation_audit.csv"]))


def test_final_cleanup_cluster90_flag_controls_classification_below_identity_threshold() -> None:
    assert smoke._classification_protein_from_flags(False,False,True,True)=="same_sequence_cluster_90"


def test_final_cleanup_cluster50_flag_controls_classification_below_identity_threshold() -> None:
    assert smoke._classification_protein_from_flags(False,False,False,True)=="same_sequence_cluster_50"


def test_final_cleanup_unexpected_ligand_inventory_group_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path)
    def add_group(rows):
        row=copy.deepcopy(rows[0]); row.update({"group_type":"ligand_exact_graph","group_id":"COVAPIE_LIGAND_GRAPH_GROUP_999999","group_key":"extra","member_count":"1","member_sample_index_row_ids":"CYS_SG_SAMPLE_INDEX_000001","group_inventory_passed":"True"}); rows.append(row)
    _rewrite_csv(paths.ligand_group_inventory,add_group); result=_r2b_semantic(paths)
    assert "unexpected_ligand_group_inventory_group:ligand_exact_graph:COVAPIE_LIGAND_GRAPH_GROUP_999999" in result.blocking_reasons


def test_final_cleanup_unexpected_protein_inventory_group_is_blocked(tmp_path: Path) -> None:
    paths=_r2a_input_bundle(tmp_path)
    def add_group(rows):
        row=copy.deepcopy(rows[0]); row.update({"group_type":"protein_exact_sequence","group_id":"COVAPIE_PROTEIN_EXACT_SEQUENCE_GROUP_999999","group_key":"extra","member_count":"1","member_sample_index_row_ids":"CYS_SG_SAMPLE_INDEX_000001","group_inventory_passed":"True"}); rows.append(row)
    _rewrite_csv(paths.protein_group_inventory,add_group); result=_r2b_semantic(paths)
    assert "unexpected_protein_group_inventory_group:protein_exact_sequence:COVAPIE_PROTEIN_EXACT_SEQUENCE_GROUP_999999" in result.blocking_reasons
