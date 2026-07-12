from __future__ import annotations
import copy,csv,hashlib,json,shutil,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from covalent_ext import covapie_unified_leakage_split_materialization_smoke as smoke

@pytest.fixture(scope="module")
def result():return smoke.run()

def test_optimizer_deterministic(result):
    assert smoke.optimize_group_split(result["groups"]) ["signature"]==result["optimizer"]["signature"]
def test_optimizer_uses_no_random(result):assert result["manifest"]["randomization_used"] is False and result["manifest"]["split_seed_used"] is False
def test_exact_assignment_signature(result):assert result["optimizer"]["signature"]==[0,1,1,0,2]
def test_exact_group_split_mapping(result):assert {r["final_leakage_group_id"]:r["assigned_split"] for r in result["groups"]}=={"COVAPIE_LEAKAGE_GROUP_000001":"train","COVAPIE_LEAKAGE_GROUP_000002":"validation","COVAPIE_LEAKAGE_GROUP_000003":"validation","COVAPIE_LEAKAGE_GROUP_000004":"train","COVAPIE_LEAKAGE_GROUP_000005":"test"}
def test_exact_sample_split_mapping(result):
    by={r["sample_index_row_id"]:r["assigned_split"] for r in result["samples"]}; assert [k for k,v in by.items() if v=="train"]==[f"CYS_SG_SAMPLE_INDEX_{i:06d}" for i in [1,2,3,6,7,8,9,10]]; assert [k for k,v in by.items() if v=="validation"]==[f"CYS_SG_SAMPLE_INDEX_{i:06d}" for i in [4,5]]; assert [k for k,v in by.items() if v=="test"]==["CYS_SG_SAMPLE_INDEX_000011"]
def test_groups_are_not_split(result):assert all(r["group_kept_intact"] for r in result["groups"])
def test_all_three_splits_nonempty(result):assert {r["assigned_split"] for r in result["samples"]}==set(smoke.SPLITS)
def test_sample_counts_8_2_1(result):assert result["optimizer"]["sample_counts"]==[8,2,1]
def test_group_counts_2_2_1(result):assert result["optimizer"]["group_counts"]==[2,2,1]
def test_objective_values(result):assert str(result["optimizer"]["sample_l1_error"])=="13/10" and str(result["optimizer"]["sample_max_error"])=="13/20" and str(result["optimizer"]["group_l1_error"])=="3"
def test_group_assignment_5_of_5(result):assert len(result["groups"])==5 and all(r["group_split_assignment_passed"] for r in result["groups"])
def test_sample_assignment_11_of_11(result):assert len(result["samples"])==11 and all(r["sample_split_assignment_passed"] for r in result["samples"])
def _csv(name):return list(csv.DictReader(smoke.rp(smoke.OUT[name]).open()))
def test_train_csv_8_rows_33_fields(result):rows=_csv("train_sample_index.csv");assert len(rows)==8 and list(rows[0])==smoke.ap.SAMPLE_INDEX_FIELDS
def test_validation_csv_2_rows_33_fields(result):rows=_csv("validation_sample_index.csv");assert len(rows)==2 and list(rows[0])==smoke.ap.SAMPLE_INDEX_FIELDS
def test_test_csv_1_row_33_fields(result):rows=_csv("test_sample_index.csv");assert len(rows)==1 and list(rows[0])==smoke.ap.SAMPLE_INDEX_FIELDS
def test_split_csvs_mutually_exclusive(result):sets=[{r["sample_index_row_id"] for r in _csv(f"{s}_sample_index.csv")} for s in smoke.SPLITS];assert not(sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2])
def test_split_csv_union_recovers_unified(result):assert {r["sample_index_row_id"] for s in smoke.SPLITS for r in _csv(f"{s}_sample_index.csv")}=={r["sample_index_row_id"] for r in smoke.read_csv(smoke.DEFAULT_INPUT_PATHS.unified_csv)}
def test_source_fields_preserved(result):
    source={r["sample_index_row_id"]:r for r in smoke.read_csv(smoke.DEFAULT_INPUT_PATHS.unified_csv)}
    assert all(r==source[r["sample_index_row_id"]] for s in smoke.SPLITS for r in _csv(f"{s}_sample_index.csv"))
def test_split_row_order_preserved(result):
    order={r["sample_index_row_id"]:i for i,r in enumerate(smoke.read_csv(smoke.DEFAULT_INPUT_PATHS.unified_csv))}
    assert all([order[r["sample_index_row_id"]] for r in _csv(f"{s}_sample_index.csv")]==sorted(order[r["sample_index_row_id"]] for r in _csv(f"{s}_sample_index.csv")) for s in smoke.SPLITS)
def test_pair_audit_exactly_55(result):assert len(result["leakage"])==55
def test_cross_within_pair_counts_26_29(result):assert sum(r["cross_split_pair"] for r in result["leakage"])==26 and sum(not r["cross_split_pair"] for r in result["leakage"])==29
def test_leakage_violations_zero(result):assert not any(r["leakage_violation"] for r in result["leakage"])
def test_direct_edge_cross_split_zero(result):assert not any(r["cross_split_pair"] and r["direct_must_link_edge"] for r in result["leakage"])
def test_same_final_group_cross_split_zero(result):assert not any(r["cross_split_pair"] and r["same_final_leakage_group_after_transitive_closure"] for r in result["leakage"])
def test_ligand_axes_cross_split_zero(result):assert not any(r["cross_split_pair"] and (r["same_ligand_graph"] or r["same_murcko_scaffold"]) for r in result["leakage"])
def test_protein_axes_cross_split_zero(result):assert not any(r["cross_split_pair"] and any(r[f] for f in ["same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50"]) for r in result["leakage"])

def _bundle(tmp_path):
    vals={}
    for name in smoke.DEFAULT_INPUT_PATHS.__dataclass_fields__:
        src=smoke.rp(getattr(smoke.DEFAULT_INPUT_PATHS,name));dst=tmp_path/name/src.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);vals[name]=dst
    return smoke.InputPaths(**vals)
def _redirect(monkeypatch,tmp_path):root=tmp_path/"out";monkeypatch.setattr(smoke,"ROOT",root);monkeypatch.setattr(smoke,"OUT",{n:root/n for n in smoke.OUT});monkeypatch.setattr(smoke,"SUMMARY",tmp_path/"summary.md")
def _blocked(tmp_path,monkeypatch,kind):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path)
    if kind=="missing_manifest":paths.manifest.unlink()
    elif kind=="malformed_json":paths.unified_json.write_text("bad")
    elif kind=="assignment_mismatch":
        rows=smoke.read_csv(paths.assignment_csv);rows[0]["pdb_id"]="XXXX";smoke.write_csv(paths.assignment_csv,rows,list(rows[0]))
    elif kind=="inventory_mismatch":
        rows=smoke.read_csv(paths.inventory_csv);rows[0]["member_sample_index_row_ids"]="CYS_SG_SAMPLE_INDEX_000001";smoke.write_csv(paths.inventory_csv,rows,list(rows[0]))
    elif kind=="missing_pair":
        rows=smoke.read_csv(paths.pair_audit);rows.pop();smoke.write_csv(paths.pair_audit,rows,list(rows[0]))
    elif kind=="not_ready":
        m=json.loads(paths.manifest.read_text());m["ready_for_covapie_unified_leakage_split_materialization_smoke"]=False;paths.manifest.write_text(json.dumps(m))
    return smoke.run(paths)
def test_missing_manifest_safely_blocked(tmp_path,monkeypatch):assert _blocked(tmp_path,monkeypatch,"missing_manifest")["manifest"]["all_checks_passed"] is False
def test_malformed_unified_json_safely_blocked(tmp_path,monkeypatch):assert _blocked(tmp_path,monkeypatch,"malformed_json")["manifest"]["split_optimizer_executed"] is False
def test_assignment_mismatch_safely_blocked(tmp_path,monkeypatch):assert _blocked(tmp_path,monkeypatch,"assignment_mismatch")["groups"]==[]
def test_inventory_mismatch_safely_blocked(tmp_path,monkeypatch):assert _blocked(tmp_path,monkeypatch,"inventory_mismatch")["groups"]==[]
def test_missing_pair_safely_blocked(tmp_path,monkeypatch):assert _blocked(tmp_path,monkeypatch,"missing_pair")["leakage"]==[]
def test_not_ready_manifest_safely_blocked(tmp_path,monkeypatch):assert _blocked(tmp_path,monkeypatch,"not_ready")["manifest"]["ready_for_covapie_final_dataset_materialization_smoke"] is False
def test_blocked_path_writes_all_12_artifacts(tmp_path,monkeypatch):_blocked(tmp_path,monkeypatch,"missing_manifest");assert sum(smoke.rp(p).is_file() for p in smoke.OUT.values())==12
def test_blocked_path_has_no_sentinel(tmp_path,monkeypatch):r=_blocked(tmp_path,monkeypatch,"malformed_json");assert not any(x["issue_id"]=="NO_UNIFIED_LEAKAGE_SPLIT_MATERIALIZATION_ISSUES" for x in r["issues"])
def test_blocked_readiness_false(tmp_path,monkeypatch):m=_blocked(tmp_path,monkeypatch,"inventory_mismatch")["manifest"];assert m["ready_for_covapie_final_dataset_materialization_smoke"] is False and m["ready_for_training"] is False
def test_small_n_status_does_not_fail(result):assert result["manifest"]["all_checks_passed"] is True and all(r["balance_status"].startswith("provisional_small_n") for r in result["balance"])
def test_statistical_representativeness_false(result):assert result["manifest"]["statistical_representativeness_claimed"] is False and all(r["statistically_representative"] is False for r in result["balance"])
def test_training_readiness_false_and_masks_preserved(result):m=result["manifest"];assert m["ready_for_training"] is False and m["canonical_mask_task_aliases"]==["A","B","B2","B3","C"] and m["b3_scaffold_only_included"] is True
def test_two_run_hashes_are_stable(result):
    first={n:hashlib.sha256(smoke.rp(p).read_bytes()).hexdigest() for n,p in smoke.OUT.items()};smoke.run();second={n:hashlib.sha256(smoke.rp(p).read_bytes()).hexdigest() for n,p in smoke.OUT.items()};assert first==second
def test_signature_tie_resolves_lexicographically(result):
    assert tuple([0,1,1,0,2])<tuple([0,1,2,0,2]) and result["optimizer"]["signature"]==[0,1,1,0,2]

def _source_blockers(paths):
    data,pre,blockers=smoke._load(paths)
    return data,pre,blockers
def _rewrite(path,rows):smoke.write_csv(path,rows,list(rows[0]))

def test_r1a_valid_source_contract_passes(tmp_path):
    data,pre,blockers=_source_blockers(_bundle(tmp_path))
    assert blockers==[] and data["checks"]["unified_contract"] and len(pre)>=30
def test_r1a_inventory_assignment_membership_mismatch_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.inventory_csv);rows[0]["member_sample_index_row_ids"]=rows[1]["member_sample_index_row_ids"];rows[0]["member_count"]=rows[1]["member_count"];
    _rewrite(paths.inventory_csv,rows);assert any("source_inventory_assignment_membership_mismatch" in b for b in _source_blockers(paths)[2])
def test_r1a_inventory_group_ids_swapped_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.inventory_csv);rows[0]["final_leakage_group_id"],rows[1]["final_leakage_group_id"]=rows[1]["final_leakage_group_id"],rows[0]["final_leakage_group_id"];
    _rewrite(paths.inventory_csv,rows);assert "source_inventory_group_id_mismatch" in _source_blockers(paths)[2]
def test_r1a_inventory_same_count_wrong_membership_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.inventory_csv);a=rows[0]["member_sample_index_row_ids"].split(";");b=rows[3]["member_sample_index_row_ids"].split(";");a[0],b[0]=b[0],a[0];rows[0]["member_sample_index_row_ids"]=";".join(sorted(a));rows[3]["member_sample_index_row_ids"]=";".join(sorted(b));
    _rewrite(paths.inventory_csv,rows);assert any("source_inventory_assignment_membership_mismatch" in x for x in _source_blockers(paths)[2])
def test_r1a_assignment_inventory_member_count_mismatch_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.assignment_csv);rows[0]["final_leakage_group_member_count"]="99";_rewrite(paths.assignment_csv,rows);j=json.loads(paths.assignment_json.read_text());j[0]["final_leakage_group_member_count"]=99;paths.assignment_json.write_text(json.dumps(j));m=json.loads(paths.manifest.read_text());m["final_group_assignment_csv_sha256"]=hashlib.sha256(paths.assignment_csv.read_bytes()).hexdigest();m["final_group_assignment_json_sha256"]=hashlib.sha256(paths.assignment_json.read_bytes()).hexdigest();paths.manifest.write_text(json.dumps(m));
    assert any("source_assignment_inventory_member_count_mismatch" in x for x in _source_blockers(paths)[2])
def test_r1a_duplicate_inventory_group_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.inventory_csv);rows[1]["final_leakage_group_id"]=rows[0]["final_leakage_group_id"];
    _rewrite(paths.inventory_csv,rows);assert any("source_inventory_duplicate_group" in x for x in _source_blockers(paths)[2])
def test_r1a_pair_duplicate_and_missing_with_55_rows_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.pair_audit);rows[-1]=dict(rows[0]);_rewrite(paths.pair_audit,rows);b=_source_blockers(paths)[2]
    assert any("source_pair_duplicate" in x for x in b) and any("source_pair_missing" in x for x in b)
def test_r1a_reversed_pair_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.pair_audit);r=rows[0];r["left_sample_index_row_id"],r["right_sample_index_row_id"]=r["right_sample_index_row_id"],r["left_sample_index_row_id"];r["left_pdb_id"],r["right_pdb_id"]=r["right_pdb_id"],r["left_pdb_id"];r["left_ligand_comp_id"],r["right_ligand_comp_id"]=r["right_ligand_comp_id"],r["left_ligand_comp_id"];
    _rewrite(paths.pair_audit,rows);assert any("source_pair_reversed" in x for x in _source_blockers(paths)[2])
def test_r1a_wrong_pair_id_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.pair_audit);rows[0]["pair_assignment_decision_id"]="WRONG";_rewrite(paths.pair_audit,rows)
    assert "source_pair_id_mismatch:1" in _source_blockers(paths)[2]
def test_r1a_pair_pdb_and_ligand_mismatch_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.pair_audit);rows[0]["left_pdb_id"]="XXXX";rows[0]["left_ligand_comp_id"]="BAD";_rewrite(paths.pair_audit,rows);b=_source_blockers(paths)[2]
    assert any("source_pair_pdb_mismatch" in x for x in b) and any("source_pair_ligand_mismatch" in x for x in b)
def test_r1a_same_final_group_flag_mismatch_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.pair_audit);rows[0]["same_final_leakage_group_after_transitive_closure"]="False";_rewrite(paths.pair_audit,rows)
    assert any("source_pair_final_group_flag_mismatch" in x for x in _source_blockers(paths)[2])
def test_r1a_direct_edge_cross_final_group_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.pair_audit);row=next(r for r in rows if r["same_final_leakage_group_after_transitive_closure"]=="False");row["direct_must_link_edge"]="True";_rewrite(paths.pair_audit,rows)
    assert any("source_pair_direct_edge_cross_group" in x for x in _source_blockers(paths)[2])
def test_r1a_duplicate_safety_item_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.safety_audit);rows[-1]["safety_item"]=rows[0]["safety_item"];_rewrite(paths.safety_audit,rows)
    assert any("source_safety_duplicate_item" in x for x in _source_blockers(paths)[2])
def test_r1a_wrong_issue_sentinel_blocks(tmp_path):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.issue_inventory);rows[0]["issue_id"]="WRONG";_rewrite(paths.issue_inventory,rows)
    assert "source_issue_sentinel_invalid" in _source_blockers(paths)[2]
def test_r1a_source_failure_prevents_optimizer_execution(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);rows=smoke.read_csv(paths.inventory_csv);rows[0]["member_count"]="99";_rewrite(paths.inventory_csv,rows);_redirect(monkeypatch,tmp_path)
    monkeypatch.setattr(smoke,"optimize_group_split",lambda rows:pytest.fail("optimizer must not execute"));result=smoke.run(paths)
    assert result["manifest"]["split_optimizer_executed"] is False and result["groups"]==[] and result["samples"]==[]

def _r1b_rows():
    data,_,blockers=smoke._load(smoke.DEFAULT_INPUT_PATHS);assert not blockers
    optimized=smoke.optimize_group_split(data["inventory_csv"]);group_candidates=smoke.build_candidate_group_split_assignment_rows(data["inventory_csv"],optimized);groups=smoke.validate_group_split_assignment_rows(group_candidates,data["inventory_csv"],optimized);sample_candidates=smoke.build_candidate_sample_split_assignment_rows(data["typed_unified"],data["typed_assignment"],groups);samples=smoke.validate_sample_split_assignment_rows(sample_candidates,data["typed_unified"],data["typed_assignment"],groups)
    return data,optimized,group_candidates,groups,sample_candidates,samples
def _split_files(tmp_path,data,samples):
    paths={s:tmp_path/f"{s}.csv" for s in smoke.SPLITS}
    for split in smoke.SPLITS:smoke.write_csv(paths[split],[r for r in data["typed_unified"] if next(x for x in samples if x["sample_index_row_id"]==r["sample_index_row_id"])["assigned_split"]==split],smoke.ap.SAMPLE_INDEX_FIELDS)
    return paths

def test_r1b_valid_group_rows_pass():
    *_,groups,_,_=_r1b_rows();assert len(groups)==5 and all(r["group_split_assignment_passed"] for r in groups)
def test_r1b_wrong_group_assigned_split_detected():
    data,opt,candidates,*_=_r1b_rows();rows=copy.deepcopy(candidates);rows[0]["assigned_split"]="test";validated=smoke.validate_group_split_assignment_rows(rows,data["inventory_csv"],opt)
    assert "group_split_optimizer_mismatch" in validated[0]["blocking_reasons"]
def test_r1b_wrong_group_split_rank_detected():
    data,opt,candidates,*_=_r1b_rows();rows=copy.deepcopy(candidates);rows[0]["assigned_split_rank"]=2;validated=smoke.validate_group_split_assignment_rows(rows,data["inventory_csv"],opt)
    assert "group_split_rank_mismatch" in validated[0]["blocking_reasons"]
def test_r1b_missing_source_inventory_group_detected():
    data,opt,candidates,*_=_r1b_rows();validated=smoke.validate_group_split_assignment_rows(candidates,data["inventory_csv"][1:],opt)
    assert "group_split_source_row_missing" in validated[0]["blocking_reasons"]
def test_r1b_duplicate_group_candidate_detected():
    data,opt,candidates,*_=_r1b_rows();rows=copy.deepcopy(candidates)+[copy.deepcopy(candidates[0])];validated=smoke.validate_group_split_assignment_rows(rows,data["inventory_csv"],opt)
    assert any("group_split_duplicate_group" in r["blocking_reasons"] for r in validated)
def test_r1b_group_source_member_list_mismatch_detected():
    data,opt,candidates,*_=_r1b_rows();rows=copy.deepcopy(candidates);rows[0]["member_sample_index_row_ids"]="CYS_SG_SAMPLE_INDEX_000001";validated=smoke.validate_group_split_assignment_rows(rows,data["inventory_csv"],opt)
    assert "group_split_source_field_mismatch" in validated[0]["blocking_reasons"]
def test_r1b_valid_sample_rows_pass():
    *_,samples=_r1b_rows();assert len(samples)==11 and all(r["sample_split_assignment_passed"] for r in samples)
def test_r1b_missing_unified_source_sample_detected():
    data,_,_,groups,candidates,_=_r1b_rows();validated=smoke.validate_sample_split_assignment_rows(candidates,data["typed_unified"][1:],data["typed_assignment"],groups)
    assert "sample_split_source_unified_missing" in validated[0]["blocking_reasons"]
def test_r1b_duplicate_source_assignment_sample_detected():
    data,_,_,groups,candidates,_=_r1b_rows();assignments=copy.deepcopy(data["typed_assignment"])+[copy.deepcopy(data["typed_assignment"][0])];validated=smoke.validate_sample_split_assignment_rows(candidates,data["typed_unified"],assignments,groups)
    assert "sample_split_source_assignment_duplicate" in validated[0]["blocking_reasons"]
def test_r1b_wrong_sample_final_group_detected():
    data,_,_,groups,candidates,_=_r1b_rows();rows=copy.deepcopy(candidates);rows[0]["final_leakage_group_id"]=groups[-1]["final_leakage_group_id"];validated=smoke.validate_sample_split_assignment_rows(rows,data["typed_unified"],data["typed_assignment"],groups)
    assert "sample_split_group_mismatch" in validated[0]["blocking_reasons"]
def test_r1b_wrong_sample_assigned_split_detected():
    data,_,_,groups,candidates,_=_r1b_rows();rows=copy.deepcopy(candidates);rows[0]["assigned_split"]="test";validated=smoke.validate_sample_split_assignment_rows(rows,data["typed_unified"],data["typed_assignment"],groups)
    assert "sample_split_assigned_split_mismatch" in validated[0]["blocking_reasons"]
def test_r1b_group_sample_membership_mismatch_detected():
    _,_,_,groups,_,samples=_r1b_rows();rows=copy.deepcopy(samples);rows[0]["final_leakage_group_id"]=groups[-1]["final_leakage_group_id"];result=smoke.validate_group_sample_split_consistency(groups,rows)
    assert not result["group_sample_membership_consistent"]
def test_r1b_same_group_two_splits_detected():
    _,_,_,groups,_,samples=_r1b_rows();rows=copy.deepcopy(samples);rows[0]["assigned_split"]="test";result=smoke.validate_group_sample_split_consistency(groups,rows)
    assert not result["group_sample_split_consistent"]
def test_r1b_group_assignment_csv_tamper_detected(tmp_path):
    _,_,_,groups,_,_=_r1b_rows();path=tmp_path/"groups.csv";smoke.write_csv(path,groups,smoke.GROUP_FIELDS);rows=smoke.read_csv(path);rows[0]["assigned_split"]="test";smoke.write_csv(path,rows,smoke.GROUP_FIELDS)
    assert not smoke.validate_written_group_split_assignment(groups,path)["passed"]
def test_r1b_sample_assignment_csv_tamper_detected(tmp_path):
    *_,samples=_r1b_rows();path=tmp_path/"samples.csv";smoke.write_csv(path,samples,smoke.SAMPLE_FIELDS);rows=smoke.read_csv(path);rows[0]["pdb_id"]="XXXX";smoke.write_csv(path,rows,smoke.SAMPLE_FIELDS)
    assert not smoke.validate_written_sample_split_assignment(samples,path)["passed"]
def test_r1b_split_csv_missing_row_detected(tmp_path):
    data,_,_,_,_,samples=_r1b_rows();paths=_split_files(tmp_path,data,samples);rows=smoke.read_csv(paths["train"]);rows.pop();smoke.write_csv(paths["train"],rows,smoke.ap.SAMPLE_INDEX_FIELDS)
    assert not smoke.validate_written_split_sample_indexes(data["typed_unified"],samples,paths["train"],paths["validation"],paths["test"])["split_files_counts_passed"]
def test_r1b_split_csv_duplicate_sample_detected(tmp_path):
    data,_,_,_,_,samples=_r1b_rows();paths=_split_files(tmp_path,data,samples);rows=smoke.read_csv(paths["train"]);rows[-1]=dict(rows[0]);smoke.write_csv(paths["train"],rows,smoke.ap.SAMPLE_INDEX_FIELDS)
    assert not smoke.validate_written_split_sample_indexes(data["typed_unified"],samples,paths["train"],paths["validation"],paths["test"])["split_files_mutually_exclusive"]
def test_r1b_split_csv_wrong_header_detected(tmp_path):
    data,_,_,_,_,samples=_r1b_rows();paths=_split_files(tmp_path,data,samples);rows=smoke.read_csv(paths["train"]);smoke.write_csv(paths["train"],rows,smoke.ap.SAMPLE_INDEX_FIELDS[:-1]);result=smoke.validate_written_split_sample_indexes(data["typed_unified"],samples,paths["train"],paths["validation"],paths["test"])
    assert not result["split_files_schema_passed"]
def test_r1b_split_csv_source_field_tamper_detected(tmp_path):
    data,_,_,_,_,samples=_r1b_rows();paths=_split_files(tmp_path,data,samples);rows=smoke.read_csv(paths["train"]);rows[0]["pdb_id"]="XXXX";smoke.write_csv(paths["train"],rows,smoke.ap.SAMPLE_INDEX_FIELDS);result=smoke.validate_written_split_sample_indexes(data["typed_unified"],samples,paths["train"],paths["validation"],paths["test"])
    assert not result["split_files_source_preservation_passed"]
def test_r1b_split_csv_row_order_mismatch_detected(tmp_path):
    data,_,_,_,_,samples=_r1b_rows();paths=_split_files(tmp_path,data,samples);rows=smoke.read_csv(paths["train"]);rows[0],rows[1]=rows[1],rows[0];smoke.write_csv(paths["train"],rows,smoke.ap.SAMPLE_INDEX_FIELDS);result=smoke.validate_written_split_sample_indexes(data["typed_unified"],samples,paths["train"],paths["validation"],paths["test"])
    assert not result["split_files_row_order_passed"]
def test_r1b_manifest_integrity_and_partition_are_validator_results(result):
    m=result["manifest"]
    assert m["group_integrity_passed"] and m["group_sample_membership_consistent"] and m["group_sample_split_consistent"] and m["group_split_assignment_write_validation_passed"] and m["sample_split_assignment_write_validation_passed"] and m["split_files_write_validation_passed"] and m["split_files_partition_unified_index"]
def test_r1b_assignment_validation_failure_blocks_readiness_and_creates_issue(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path);original=smoke.build_candidate_group_split_assignment_rows
    def tampered(inventory,optimized):
        rows=original(inventory,optimized);rows[0]["assigned_split"]="test";return rows
    monkeypatch.setattr(smoke,"build_candidate_group_split_assignment_rows",tampered);result=smoke.run(paths);m=result["manifest"]
    assert m["all_checks_passed"] is False and m["ready_for_covapie_final_dataset_materialization_smoke"] is False and any(r["issue_status"]=="failed" for r in result["issues"])

def _r1c_leakage():
    data,_,_,_,_,samples=_r1b_rows();candidates=smoke.build_candidate_cross_split_leakage_rows(data["pair_audit"],samples);validated=smoke.validate_cross_split_leakage_rows(candidates,data["pair_audit"],samples);return data,samples,candidates,validated
def _r1c_balance():
    _,_,_,groups,_,samples=_r1b_rows();consistency=smoke.validate_group_sample_split_consistency(groups,samples);candidates=smoke.build_candidate_balance_rows(groups,samples,consistency);validated=smoke.validate_balance_rows(candidates,groups,samples,consistency);return groups,samples,consistency,candidates,validated

def test_r1c_valid_policy_audit_passes():
    data,_,_=smoke._load(smoke.DEFAULT_INPUT_PATHS);opt=smoke.optimize_group_split(data["inventory_csv"]);rows=smoke.build_and_validate_policy_audit_rows(smoke.build_policy_observations(opt,len(data["inventory_csv"])))
    assert len(rows)==len(smoke.POLICY_EXPECTED) and all(r["policy_check_passed"] for r in rows)
def test_r1c_policy_signature_tamper_detected():
    data,_,_=smoke._load(smoke.DEFAULT_INPUT_PATHS);opt=smoke.optimize_group_split(data["inventory_csv"]);obs=smoke.build_policy_observations(opt,5);obs["selected_assignment_signature"]="2;2;2;2;2";rows=smoke.build_and_validate_policy_audit_rows(obs)
    assert not next(r for r in rows if r["policy_audit_item"]=="selected_assignment_signature")["policy_check_passed"]
def test_r1c_policy_sample_count_tamper_detected():
    data,_,_=smoke._load(smoke.DEFAULT_INPUT_PATHS);opt=smoke.optimize_group_split(data["inventory_csv"]);obs=smoke.build_policy_observations(opt,5);obs["selected_sample_counts"]="7;3;1"
    assert not next(r for r in smoke.build_and_validate_policy_audit_rows(obs) if r["policy_audit_item"]=="selected_sample_counts")["policy_check_passed"]
def test_r1c_policy_objective_tamper_detected():
    data,_,_=smoke._load(smoke.DEFAULT_INPUT_PATHS);opt=smoke.optimize_group_split(data["inventory_csv"]);obs=smoke.build_policy_observations(opt,5);obs["sample_l1_error"]="0"
    assert not next(r for r in smoke.build_and_validate_policy_audit_rows(obs) if r["policy_audit_item"]=="sample_l1_error")["policy_check_passed"]
def test_r1c_policy_csv_tamper_detected(tmp_path):
    data,_,_=smoke._load(smoke.DEFAULT_INPUT_PATHS);opt=smoke.optimize_group_split(data["inventory_csv"]);rows=smoke.build_and_validate_policy_audit_rows(smoke.build_policy_observations(opt,5));path=tmp_path/"policy.csv";smoke.write_csv(path,rows,smoke.POLICY_FIELDS);raw=smoke.read_csv(path);raw[0]["observed_value"]="bad";smoke.write_csv(path,raw,smoke.POLICY_FIELDS)
    assert not smoke.validate_written_policy_audit(rows,path)["policy_write_validation_passed"]

def test_r1c_valid_leakage_rows_pass_55_of_55():
    *_,rows=_r1c_leakage();assert len(rows)==55 and all(r["pair_split_leakage_passed"] for r in rows)
def test_r1c_leakage_wrong_left_split_detected():
    data,samples,candidates,_=_r1c_leakage();rows=copy.deepcopy(candidates);rows[0]["left_split"]="test";validated=smoke.validate_cross_split_leakage_rows(rows,data["pair_audit"],samples)
    assert "leakage_split_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_leakage_wrong_group_detected():
    data,samples,candidates,_=_r1c_leakage();rows=copy.deepcopy(candidates);rows[0]["left_final_leakage_group_id"]="WRONG";validated=smoke.validate_cross_split_leakage_rows(rows,data["pair_audit"],samples)
    assert "leakage_group_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_leakage_cross_split_flag_tamper_detected():
    data,samples,candidates,_=_r1c_leakage();rows=copy.deepcopy(candidates);rows[0]["cross_split_pair"]=not rows[0]["cross_split_pair"];validated=smoke.validate_cross_split_leakage_rows(rows,data["pair_audit"],samples)
    assert "leakage_cross_split_flag_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_leakage_evidence_flag_tamper_detected():
    data,samples,candidates,_=_r1c_leakage();rows=copy.deepcopy(candidates);rows[0]["same_ligand_graph"]=not rows[0]["same_ligand_graph"];validated=smoke.validate_cross_split_leakage_rows(rows,data["pair_audit"],samples)
    assert "leakage_source_field_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_leakage_violation_tamper_detected():
    data,samples,candidates,_=_r1c_leakage();rows=copy.deepcopy(candidates);rows[0]["leakage_violation"]=True;validated=smoke.validate_cross_split_leakage_rows(rows,data["pair_audit"],samples)
    assert "leakage_violation_flag_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_leakage_csv_missing_row_detected(tmp_path):
    *_,rows=_r1c_leakage();path=tmp_path/"leak.csv";smoke.write_csv(path,rows,smoke.LEAK_FIELDS);raw=smoke.read_csv(path);raw.pop();smoke.write_csv(path,raw,smoke.LEAK_FIELDS)
    assert not smoke.validate_written_cross_split_leakage_audit(rows,path)["leakage_audit_write_validation_passed"]
def test_r1c_direct_edge_cross_split_summary_fails():
    *_,rows=_r1c_leakage();tampered=copy.deepcopy(rows);row=next(r for r in tampered if r["cross_split_pair"]);row["direct_must_link_edge"]=True
    assert not smoke.validate_cross_split_leakage_summary(tampered)["all_cross_split_leakage_checks_passed"]
def test_r1c_same_final_group_cross_split_summary_fails():
    *_,rows=_r1c_leakage();tampered=copy.deepcopy(rows);row=next(r for r in tampered if r["cross_split_pair"]);row["same_final_leakage_group_after_transitive_closure"]=True
    assert not smoke.validate_cross_split_leakage_summary(tampered)["all_cross_split_leakage_checks_passed"]

def test_r1c_valid_balance_rows_pass_4_of_4():
    *_,rows=_r1c_balance();assert len(rows)==4 and all(r["balance_audit_passed"] for r in rows)
def test_r1c_balance_sample_count_tamper_detected():
    groups,samples,c,rows,_=_r1c_balance();tampered=copy.deepcopy(rows);tampered[0]["actual_sample_count"]+=1;validated=smoke.validate_balance_rows(tampered,groups,samples,c)
    assert "balance_sample_count_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_balance_group_count_tamper_detected():
    groups,samples,c,rows,_=_r1c_balance();tampered=copy.deepcopy(rows);tampered[0]["actual_group_count"]+=1;validated=smoke.validate_balance_rows(tampered,groups,samples,c)
    assert "balance_group_count_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_balance_ratio_tamper_detected():
    groups,samples,c,rows,_=_r1c_balance();tampered=copy.deepcopy(rows);tampered[0]["actual_sample_ratio"]="1";validated=smoke.validate_balance_rows(tampered,groups,samples,c)
    assert "balance_sample_ratio_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_balance_group_integrity_tamper_detected():
    groups,samples,c,rows,_=_r1c_balance();tampered=copy.deepcopy(rows);tampered[0]["group_integrity_passed"]=False;validated=smoke.validate_balance_rows(tampered,groups,samples,c)
    assert "balance_group_integrity_mismatch" in validated[0]["blocking_reasons"]
def test_r1c_balance_csv_tamper_detected(tmp_path):
    *_,rows=_r1c_balance();path=tmp_path/"balance.csv";smoke.write_csv(path,rows,smoke.BALANCE_FIELDS);raw=smoke.read_csv(path);raw[0]["actual_sample_count"]="999";smoke.write_csv(path,raw,smoke.BALANCE_FIELDS)
    assert not smoke.validate_written_balance_audit(rows,path)["balance_audit_write_validation_passed"]

def test_r1c_normal_safety_33_of_33_pass(result):assert len(result["safety"])==33 and all(r["safety_passed"] for r in result["safety"])
def test_r1c_blocked_safety_uses_blocked_expected(tmp_path,monkeypatch):
    blocked=_blocked(tmp_path,monkeypatch,"missing_manifest");assert len(blocked["safety"])==33 and all(r["safety_passed"] for r in blocked["safety"])
def test_r1c_tmp_file_detected(tmp_path,monkeypatch):
    _redirect(monkeypatch,tmp_path);root=smoke.rp(smoke.ROOT);root.mkdir(parents=True,exist_ok=True);(root/"probe.tmp").write_text("x");obs=smoke.build_safety_observations(activity=smoke.RunActivity(),normal_materialization_expected=False)
    assert obs["part_or_tmp"] is True
def test_r1c_forbidden_artifact_detected(tmp_path,monkeypatch):
    _redirect(monkeypatch,tmp_path);root=smoke.rp(smoke.ROOT);root.mkdir(parents=True,exist_ok=True);(root/"probe.pt").write_text("x");obs=smoke.build_safety_observations(activity=smoke.RunActivity(),normal_materialization_expected=False)
    assert obs["forbidden_artifacts"] is True
def test_r1c_missing_split_output_detected(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path);run=smoke.run(paths);smoke.rp(smoke.OUT["train_sample_index.csv"]).unlink();obs=smoke.build_safety_observations(activity=run["activity"],normal_materialization_expected=True)
    assert obs["train_csv_written"] is False
def test_r1c_split_assignments_written_uses_actual_counts(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path);run=smoke.run(paths);rows=smoke.read_csv(smoke.OUT["covapie_sample_split_assignment.csv"]);rows.pop();smoke.write_csv(smoke.OUT["covapie_sample_split_assignment.csv"],rows,smoke.SAMPLE_FIELDS,run["activity"]);obs=smoke.build_safety_observations(activity=run["activity"],normal_materialization_expected=True)
    assert obs["split_assignments_written"] is False
def test_r1c_safety_csv_duplicate_item_detected(tmp_path,result):
    rows=copy.deepcopy(result["safety"]);rows[-1]["safety_item"]=rows[0]["safety_item"];path=tmp_path/"safety.csv";smoke.write_csv(path,rows,smoke.SAFETY_FIELDS)
    assert not smoke.validate_written_safety_audit(rows,path)["safety_audit_write_validation_passed"]
def test_r1c_activity_records_successful_reads_and_writes(tmp_path):
    activity=smoke.RunActivity();path=tmp_path/"activity.csv";smoke.write_csv(path,[{"x":"1"}],["x"],activity);assert smoke.read_csv(path,activity)==[{"x":"1"}];smoke.sha(path,activity)
    assert str(path.resolve()) in activity.read_paths and str(path.resolve()) in activity.written_paths

def test_r1c_policy_failure_closes_readiness_and_creates_issue(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path);original=smoke.build_policy_observations
    def bad(opt,count):rows=original(opt,count);rows["selected_assignment_signature"]="bad";return rows
    monkeypatch.setattr(smoke,"build_policy_observations",bad);result=smoke.run(paths);assert not result["manifest"]["ready_for_covapie_final_dataset_materialization_smoke"] and any(r["issue_status"]=="failed" for r in result["issues"])
def test_r1c_leakage_failure_closes_readiness_and_creates_issue(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path);original=smoke.build_candidate_cross_split_leakage_rows
    def bad(pairs,samples):rows=original(pairs,samples);rows[0]["left_split"]="bad";return rows
    monkeypatch.setattr(smoke,"build_candidate_cross_split_leakage_rows",bad);result=smoke.run(paths);assert not result["manifest"]["ready_for_covapie_final_dataset_materialization_smoke"] and any(r["issue_status"]=="failed" for r in result["issues"])
def test_r1c_balance_failure_closes_readiness_and_creates_issue(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path);original=smoke.build_candidate_balance_rows
    def bad(groups,samples,c):rows=original(groups,samples,c);rows[0]["actual_sample_count"]+=1;return rows
    monkeypatch.setattr(smoke,"build_candidate_balance_rows",bad);result=smoke.run(paths);assert not result["manifest"]["ready_for_covapie_final_dataset_materialization_smoke"] and any(r["issue_status"]=="failed" for r in result["issues"])
def test_r1c_safety_failure_closes_readiness_and_creates_issue(tmp_path,monkeypatch):
    paths=_bundle(tmp_path);_redirect(monkeypatch,tmp_path);original=smoke.build_safety_observations
    def bad(**kwargs):rows=original(**kwargs);rows["network_access_used"]=True;return rows
    monkeypatch.setattr(smoke,"build_safety_observations",bad);result=smoke.run(paths);assert not result["manifest"]["ready_for_covapie_final_dataset_materialization_smoke"] and any(r["issue_status"]=="failed" for r in result["issues"])
def test_r1c_normal_manifest_all_aggregates_are_validated(result):
    m=result["manifest"];keys=["all_preconditions_passed","all_policy_checks_passed","all_group_assignment_checks_passed","all_sample_assignment_checks_passed","all_cross_split_leakage_checks_passed","all_balance_checks_passed","all_safety_checks_passed","all_checks_passed"]
    assert all(m[k] is True for k in keys) and m["issue_inventory_clear"] is True and m["blocking_issue_count"]==0
