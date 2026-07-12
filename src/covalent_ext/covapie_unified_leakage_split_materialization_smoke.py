from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
from typing import Any

from covalent_ext import covapie_unified_independence_group_assignment_and_sample_index_merge_smoke as ap

REPO=Path(__file__).resolve().parents[2]
STAGE="covapie_unified_leakage_split_materialization_smoke_v0"
PREVIOUS=ap.STAGE
SOURCE_COMMIT="475ce58dae1aa650a7345374682893490f458cf1"
ROOT=Path("data/derived/covalent_small")/STAGE
SOURCE_ROOT=ap.ROOT
SUMMARY=Path("docs/covapie_unified_leakage_split_materialization_smoke_v0_summary.md")
POLICY="deterministic_final_leakage_group_exhaustive_ratio_fit_v1"
SPLITS=["train","validation","test"]
RANK={name:n for n,name in enumerate(SPLITS)}
TARGET={"train":Fraction(7,10),"validation":Fraction(3,20),"test":Fraction(3,20)}
POLICY_EXPECTED={
    "policy_name":POLICY,"split_unit":"final_leakage_group_id","split_names":"train;validation;test","target_ratios":"7/10;3/20;3/20","randomization_used":"false","split_seed_used":"false","exhaustive_small_n_search":"true","candidate_assignment_count":"243","valid_candidate_count":"56","objective_order":"sample_l1_error;sample_max_error;group_l1_error;assignment_signature","tie_break_rule":"lexicographic_assignment_signature","selected_assignment_signature":"0;1;1;0;2","selected_sample_counts":"8;2;1","selected_group_counts":"2;2;1","sample_l1_error":"13/10","sample_max_error":"13/20","group_l1_error":"3","group_integrity_priority":"true","small_n_status":"provisional_small_n_smoke_only","statistical_representativeness":"false","production_split_policy_finalized":"false","feature_semantics_audit_still_required":"true","validation_test_target_symmetry":"true","asymmetric_validation_test_constraint_added":"false","tie_resolved_by_assignment_signature":"true","selected_signature_is_lexicographic_minimum":"true","each_split_has_group":"true","train_not_smaller_than_validation":"true","train_not_smaller_than_test":"true"}

OUT={name:ROOT/name for name in [
"covapie_leakage_split_precondition_audit.csv","covapie_leakage_split_policy_audit.csv","covapie_leakage_group_split_assignment.csv","covapie_sample_split_assignment.csv","train_sample_index.csv","validation_sample_index.csv","test_sample_index.csv","covapie_cross_split_leakage_audit.csv","covapie_split_balance_audit.csv","covapie_leakage_split_issue_inventory.csv","covapie_leakage_split_safety_audit.csv","covapie_unified_leakage_split_materialization_smoke_manifest.json"]}

PRE_FIELDS=["precondition_item","expected_status","observed_status","precondition_passed","blocking_reasons"]
POLICY_FIELDS=["policy_audit_item","observed_value","expected_value","policy_check_passed","blocking_reasons"]
GROUP_FIELDS=["group_split_assignment_id","final_leakage_group_id","group_order","member_count","member_sample_index_row_ids","source_stage_composition","final_leakage_group_status","assigned_split","assigned_split_rank","split_policy","group_kept_intact","group_split_assignment_passed","eligible_for_final_dataset_materialization_smoke","ready_for_training_current_step","feature_semantics_audit_required_before_training","blocking_reasons"]
SAMPLE_FIELDS=["sample_split_assignment_id","sample_index_row_id","pdb_id","ligand_comp_id","source_index_stage","final_leakage_group_id","final_leakage_group_member_count","assigned_split","split_unit_type","group_assignment_row_found","source_unified_row_found","source_assignment_row_found","sample_split_assignment_passed","eligible_for_final_dataset_materialization_smoke","ready_for_training_current_step","feature_semantics_audit_required_before_training","leakage_split_design_required_before_training","blocking_reasons"]
LEAK_FIELDS=["split_leakage_audit_id","left_sample_index_row_id","right_sample_index_row_id","left_final_leakage_group_id","right_final_leakage_group_id","left_split","right_split","cross_split_pair","same_final_leakage_group_after_transitive_closure","direct_must_link_edge","same_ligand_graph","same_murcko_scaffold","same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50","transitive_only_same_group","leakage_violation","pair_split_leakage_passed","blocking_reasons"]
BALANCE_FIELDS=["split_balance_audit_id","split_name","target_sample_ratio","actual_sample_count","actual_sample_ratio","sample_ratio_absolute_deviation","target_group_ratio","actual_group_count","actual_group_ratio","group_ratio_absolute_deviation","minimum_one_group_passed","group_integrity_passed","statistically_representative","balance_status","balance_audit_passed","blocking_reasons"]
ISSUE_FIELDS=["issue_id","issue_scope","issue_severity","issue_type","issue_description","issue_status"]
SAFETY_FIELDS=["safety_item","required_status","observed_status","safety_passed","blocking_reasons"]

@dataclass(frozen=True)
class InputPaths:
    unified_csv:Path; unified_json:Path; assignment_csv:Path; assignment_json:Path; inventory_csv:Path; pair_audit:Path; issue_inventory:Path; manifest:Path; safety_audit:Path

DEFAULT_INPUT_PATHS=InputPaths(
    SOURCE_ROOT/"unified_sample_index.csv",SOURCE_ROOT/"unified_sample_index.json",SOURCE_ROOT/"covapie_final_leakage_group_assignment.csv",SOURCE_ROOT/"covapie_final_leakage_group_assignment.json",SOURCE_ROOT/"covapie_final_leakage_group_inventory.csv",SOURCE_ROOT/"covapie_pairwise_group_assignment_decision_audit.csv",SOURCE_ROOT/"covapie_unified_assignment_merge_issue_inventory.csv",SOURCE_ROOT/"covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json",SOURCE_ROOT/"covapie_unified_assignment_merge_safety_audit.csv")

@dataclass
class RunActivity:
    read_paths:set[str]=field(default_factory=set)
    written_paths:set[str]=field(default_factory=set)
    network_access_used:bool=False
    download_attempted:bool=False

@dataclass
class SourceValidationResult:
    passed:bool
    blocking_reasons:list[str]
    typed_unified_rows:list[dict[str,Any]]
    typed_assignment_rows:list[dict[str,Any]]
    inventory_rows:list[dict[str,Any]]
    pair_rows:list[dict[str,Any]]
    checks:dict[str,bool]
    @property
    def source_validation_passed(self)->bool:return self.passed and not self.blocking_reasons

def rp(path:Path|str)->Path:
    path=Path(path); return path if path.is_absolute() else REPO/path
def sha(path:Path|str,activity:RunActivity|None=None)->str:
    target=rp(path);value=hashlib.sha256(target.read_bytes()).hexdigest()
    if activity is not None:activity.read_paths.add(str(target.resolve()))
    return value
def atomic(path:Path,text:str,activity:RunActivity|None=None)->None:
    target=rp(path); target.parent.mkdir(parents=True,exist_ok=True); tmp=target.with_name(target.name+".tmp")
    try:
        tmp.write_text(text,encoding="utf-8"); os.replace(tmp,target)
        if activity is not None:activity.written_paths.add(str(target.resolve()))
    finally:
        if tmp.exists():tmp.unlink()
def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str],activity:RunActivity|None=None)->None:
    import io
    h=io.StringIO(); w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows({f:r.get(f,"") for f in fields} for r in rows); atomic(path,h.getvalue(),activity)
def write_json(path:Path,value:Any,activity:RunActivity|None=None)->None:atomic(path,json.dumps(value,indent=2,sort_keys=True)+"\n",activity)
def read_csv(path:Path|str,activity:RunActivity|None=None)->list[dict[str,str]]:
    target=rp(path)
    with target.open(newline="",encoding="utf-8") as h:rows=list(csv.DictReader(h))
    if activity is not None:activity.read_paths.add(str(target.resolve()))
    return rows
def git(*args:str)->tuple[str,bool]:
    r=subprocess.run(["git",*args],cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False); return r.stdout.strip(),r.returncode==0
def clean(paths:list[str|Path])->bool:
    a,ok1=git("diff","--name-only","--",*[str(p) for p in paths]); b,ok2=git("diff","--cached","--name-only","--",*[str(p) for p in paths]); return ok1 and ok2 and not a and not b
def strict(v:Any)->bool:return ap.strict_bool(v)

def optimize_group_split(groups:list[dict[str,Any]])->dict[str,Any]:
    groups=sorted(groups,key=lambda r:r["final_leakage_group_id"]); total=sum(int(r["member_count"]) for r in groups); count=len(groups); best=None;candidate_count=0;valid_objectives=[]
    for signature in product(range(3),repeat=count):
        candidate_count+=1
        group_counts=[signature.count(i) for i in range(3)]; sample_counts=[sum(int(row["member_count"]) for row,rank in zip(groups,signature) if rank==i) for i in range(3)]
        if min(group_counts)<1 or sample_counts[0]<sample_counts[1] or sample_counts[0]<sample_counts[2]:continue
        objective=(sum(abs(Fraction(sample_counts[i])-TARGET[SPLITS[i]]*total) for i in range(3)),max(abs(Fraction(sample_counts[i])-TARGET[SPLITS[i]]*total) for i in range(3)),sum(abs(Fraction(group_counts[i])-TARGET[SPLITS[i]]*count) for i in range(3)),signature)
        valid_objectives.append(objective)
        if best is None or objective<best[0]:best=(objective,sample_counts,group_counts)
    if best is None:raise ValueError("no_valid_split_assignment")
    objective,sample_counts,group_counts=best
    return {"signature":list(objective[3]),"sample_l1_error":objective[0],"sample_max_error":objective[1],"group_l1_error":objective[2],"sample_counts":sample_counts,"group_counts":group_counts,"candidate_assignment_count":candidate_count,"valid_candidate_count":len(valid_objectives),"selected_objective_tuple":objective,"all_splits_nonempty":min(group_counts)>0,"train_not_smaller_than_validation":sample_counts[0]>=sample_counts[1],"train_not_smaller_than_test":sample_counts[0]>=sample_counts[2],"lexicographic_minimum_confirmed":objective==min(valid_objectives)}

def validate_step14ap_source_contract(loaded_data:dict[str,Any],manifest:dict[str,Any])->SourceValidationResult:
    blockers=[]; checks={};activity=loaded_data.get("_activity"); uc=loaded_data.get("unified_csv",[]); uj=loaded_data.get("unified_json",[]); ac=loaded_data.get("assignment_csv",[]); aj=loaded_data.get("assignment_json",[]); inv=loaded_data.get("inventory_csv",[]); pairs=loaded_data.get("pair_audit",[])
    source_commit_is_ancestor=subprocess.run(["git","merge-base","--is-ancestor",SOURCE_COMMIT,"HEAD"],cwd=REPO,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False).returncode==0
    if not source_commit_is_ancestor:blockers.append("source_step14ap_commit_not_ancestor")
    try:typed_uc=[ap.typed(r) for r in uc]
    except (KeyError,ValueError,TypeError):typed_uc=[];blockers.append("source_unified_csv_json_mismatch")
    try:typed_ac=[ap.normalize_assignment_csv_row(r) for r in ac]
    except (KeyError,ValueError,TypeError):typed_ac=[];blockers.append("source_assignment_csv_json_mismatch")
    checks["manifest_contract"]=manifest.get("stage")==PREVIOUS and manifest.get("all_checks_passed") is True and manifest.get("blocking_reasons")==[] and manifest.get("input_load_passed") is True and manifest.get("semantic_validation_passed") is True and manifest.get("premerge_block_scope")=="none"
    checks["manifest_readiness"]=manifest.get("ready_for_covapie_unified_leakage_split_materialization_smoke") is True and manifest.get("ready_for_covapie_final_dataset_materialization_smoke") is False and manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False
    checks["feature_mask_contract"]=manifest.get("feature_semantics_known_for_training") is False and manifest.get("unknown_atom_feature_policy_finalized_for_training") is False and manifest.get("feature_semantics_audit_required_before_training") is True and manifest.get("canonical_mask_task_names")==ap.CANONICAL_MASK_TASK_NAMES and manifest.get("canonical_mask_task_aliases")==ap.CANONICAL_MASK_TASK_ALIASES
    if len(uc)!=11 or len(uj)!=11:blockers.append("source_unified_row_count_mismatch")
    if not uc or list(uc[0])!=ap.SAMPLE_INDEX_FIELDS or any(not isinstance(r,dict) or set(r)!=set(ap.SAMPLE_INDEX_FIELDS) for r in uj):blockers.append("source_unified_schema_mismatch")
    if typed_uc!=uj:blockers.append("source_unified_csv_json_mismatch")
    expected_ids=[f"CYS_SG_SAMPLE_INDEX_{i:06d}" for i in range(1,12)]; ids=[r.get("sample_index_row_id","") for r in typed_uc]
    if ids!=expected_ids:blockers.append("source_unified_sample_order_mismatch")
    blockers.extend(f"source_unified_duplicate_sample:{sid}" for sid,n in Counter(ids).items() if n>1)
    pdb_lig=[(r.get("pdb_id",""),r.get("ligand_comp_id","")) for r in typed_uc];blockers.extend(f"source_unified_duplicate_pdb_ligand:{p}/{l}" for (p,l),n in Counter(pdb_lig).items() if n>1)
    for label,path,key in [("csv",loaded_data.get("unified_csv_path"),"unified_sample_index_csv_sha256"),("json",loaded_data.get("unified_json_path"),"unified_sample_index_json_sha256")]:
        try:ok=sha(path,activity)==manifest.get(key)
        except (OSError,TypeError):ok=False
        if not ok:blockers.append(f"source_unified_hash_mismatch:{label}")
    if len(ac)!=11 or len(aj)!=11:blockers.append("source_assignment_row_count_mismatch")
    if typed_ac!=aj:blockers.append("source_assignment_csv_json_mismatch")
    for label,path,key in [("csv",loaded_data.get("assignment_csv_path"),"final_group_assignment_csv_sha256"),("json",loaded_data.get("assignment_json_path"),"final_group_assignment_json_sha256")]:
        try:ok=sha(path,activity)==manifest.get(key)
        except (OSError,TypeError):ok=False
        if not ok:blockers.append(f"source_assignment_hash_mismatch:{label}")
    assignment_multi={}; assignment_ids=[]
    for n,row in enumerate(typed_ac,1):assignment_multi.setdefault(row.get("sample_index_row_id",""),[]).append(row);assignment_ids.append(row.get("assignment_id",""));
    if assignment_ids!=[f"COVAPIE_ASSIGNMENT_{i:06d}" for i in range(1,12)]:blockers.extend(f"source_assignment_id_mismatch:{i}" for i,(a,b) in enumerate(zip(assignment_ids,[f"COVAPIE_ASSIGNMENT_{i:06d}" for i in range(1,12)]),1) if a!=b)
    blockers.extend(f"source_assignment_duplicate_sample:{sid}" for sid,rows in assignment_multi.items() if len(rows)>1)
    if [r.get("sample_index_row_id") for r in typed_ac]!=ids:blockers.append("source_assignment_sample_order_mismatch")
    unified_by={r.get("sample_index_row_id"):r for r in typed_uc}
    for row in typed_ac:
        sid=row.get("sample_index_row_id","");u=unified_by.get(sid,{})
        if row.get("pdb_id")!=u.get("pdb_id"):blockers.append(f"source_assignment_pdb_mismatch:{sid}")
        if row.get("ligand_comp_id")!=u.get("ligand_comp_id"):blockers.append(f"source_assignment_ligand_mismatch:{sid}")
        if row.get("final_group_assignment_passed") is not True:blockers.append(f"source_assignment_not_passed:{sid}")
        if row.get("blocking_reasons"):blockers.append(f"source_assignment_has_blocker:{sid}")
        if not row.get("final_leakage_group_id"):blockers.append(f"source_assignment_group_missing:{sid}")
        if not isinstance(row.get("final_leakage_group_member_count"),int) or row.get("final_leakage_group_member_count",0)<=0:blockers.append(f"source_assignment_member_count_invalid:{sid}")
        if row.get("ready_for_training_current_step") is not False or row.get("feature_semantics_audit_required_before_training") is not True:blockers.append(f"source_assignment_not_passed:{sid}")
    inv_multi={};all_members=[]
    expected_gids=[f"COVAPIE_LEAKAGE_GROUP_{i:06d}" for i in range(1,6)]
    if len(inv)!=5:blockers.append("source_inventory_row_count_mismatch")
    if [r.get("final_leakage_group_id") for r in inv]!=expected_gids or [str(r.get("group_order")) for r in inv]!=[str(i) for i in range(1,6)]:blockers.append("source_inventory_group_id_mismatch")
    for row in inv:
        gid=row.get("final_leakage_group_id","");inv_multi.setdefault(gid,[]).append(row);members=row.get("member_sample_index_row_ids","").split(";") if row.get("member_sample_index_row_ids") else [];all_members+=members
        if len(inv_multi[gid])>1:blockers.append(f"source_inventory_duplicate_group:{gid}")
        try:passed=strict(row.get("group_inventory_passed"));count=int(row.get("member_count",0))
        except (ValueError,TypeError):passed=False;count=-1
        if not passed:blockers.append(f"source_inventory_not_passed:{gid}")
        if row.get("blocking_reasons"):blockers.append(f"source_inventory_has_blocker:{gid}")
        if count!=len(members):blockers.append(f"source_inventory_member_count_mismatch:{gid}")
        if members!=sorted(members):blockers.append(f"source_inventory_members_unsorted:{gid}")
        blockers.extend(f"source_inventory_duplicate_member:{gid}:{sid}" for sid,n in Counter(members).items() if n>1)
        blockers.extend(f"source_inventory_unknown_sample:{gid}:{sid}" for sid in members if sid not in unified_by)
        assigned={sid for sid,rows in assignment_multi.items() for a in rows if a.get("final_leakage_group_id")==gid}
        if set(members)!=assigned:blockers.append(f"source_inventory_assignment_membership_mismatch:{gid}")
        for sid in members:
            for a in assignment_multi.get(sid,[]):
                if a.get("final_leakage_group_member_count")!=count:blockers.append(f"source_assignment_inventory_member_count_mismatch:{sid}")
    counts=Counter(all_members);blockers.extend(f"source_inventory_sample_missing:{sid}" for sid in ids if counts[sid]==0);blockers.extend(f"source_inventory_sample_multiple_groups:{sid}" for sid,n in counts.items() if n>1)
    expected_pairs=list(combinations(ids,2));seen={};pair_ids=[];bool_fields=["source_ligand_evidence_complete","source_protein_evidence_complete","ligand_axis_must_link","protein_axis_must_link","direct_must_link_edge","source_combined_evidence_row_found","same_ligand_graph","same_murcko_scaffold","same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50","same_final_leakage_group_after_transitive_closure","transitive_only_same_group","pair_assignment_passed"]
    if len(pairs)!=55:blockers.append("source_pair_row_count_mismatch")
    for n,row in enumerate(pairs,1):
        l,r=row.get("left_sample_index_row_id",""),row.get("right_sample_index_row_id","");pair=(l,r);seen.setdefault(pair,[]).append(row);pair_ids.append(row.get("pair_assignment_decision_id",""))
        if row.get("pair_assignment_decision_id")!=f"COVAPIE_PAIR_ASSIGNMENT_{n:06d}":blockers.append(f"source_pair_id_mismatch:{n}")
        if pair not in expected_pairs:blockers.append(f"source_pair_unexpected:{l}:{r}")
        if (r,l) in expected_pairs:blockers.append(f"source_pair_reversed:{l}:{r}")
        if n<=len(expected_pairs) and pair!=expected_pairs[n-1]:blockers.append(f"source_pair_order_mismatch:{n}")
        if l not in unified_by or r not in unified_by:blockers.append(f"source_pair_unknown_sample:{l if l not in unified_by else r}")
        lu,ru=unified_by.get(l,{}),unified_by.get(r,{})
        if row.get("left_pdb_id")!=lu.get("pdb_id") or row.get("right_pdb_id")!=ru.get("pdb_id"):blockers.append(f"source_pair_pdb_mismatch:{l}:{r}")
        if row.get("left_ligand_comp_id")!=lu.get("ligand_comp_id") or row.get("right_ligand_comp_id")!=ru.get("ligand_comp_id"):blockers.append(f"source_pair_ligand_mismatch:{l}:{r}")
        parsed={}
        try:parsed={f:strict(row.get(f)) for f in bool_fields}
        except ValueError:blockers.append(f"source_pair_not_passed:{l}:{r}")
        if parsed.get("pair_assignment_passed") is not True:blockers.append(f"source_pair_not_passed:{l}:{r}")
        if row.get("blocking_reasons"):blockers.append(f"source_pair_has_blocker:{l}:{r}")
        same=bool(assignment_multi.get(l) and assignment_multi.get(r) and assignment_multi[l][0].get("final_leakage_group_id")==assignment_multi[r][0].get("final_leakage_group_id"))
        if parsed.get("same_final_leakage_group_after_transitive_closure")!=same:blockers.append(f"source_pair_final_group_flag_mismatch:{l}:{r}")
        if parsed.get("direct_must_link_edge") and not same:blockers.append(f"source_pair_direct_edge_cross_group:{l}:{r}")
        if parsed.get("transitive_only_same_group") and (not same or parsed.get("direct_must_link_edge")):blockers.append(f"source_pair_transitive_flag_invalid:{l}:{r}")
    blockers.extend(f"source_pair_duplicate:{l}:{r}" for (l,r),rows in seen.items() if len(rows)>1);blockers.extend(f"source_pair_missing:{l}:{r}" for l,r in expected_pairs if (l,r) not in seen)
    try:edge_count=sum(strict(r.get("direct_must_link_edge")) for r in pairs)
    except ValueError:edge_count=-1
    if edge_count!=13 or len(pairs)-edge_count!=42:blockers.append("source_pair_edge_count_mismatch")
    issue=loaded_data.get("issue_inventory",[]);checks["issue_sentinel"]=len(issue)==1 and issue[0].get("issue_id")=="NO_UNIFIED_ASSIGNMENT_OR_SAMPLE_INDEX_MERGE_ISSUES" and issue[0].get("issue_type")=="no_issues" and issue[0].get("issue_status")=="passed"
    if not checks["issue_sentinel"]:blockers.append("source_issue_sentinel_invalid")
    safety=loaded_data.get("safety_audit",[]);sm={}
    if len(safety)!=39:blockers.append("source_safety_row_count_mismatch")
    for row in safety:
        item=row.get("safety_item","");sm.setdefault(item,[]).append(row)
        if len(sm[item])>1:blockers.append(f"source_safety_duplicate_item:{item}")
        try:passed=strict(row.get("safety_passed"))
        except ValueError:passed=False
        if not passed:blockers.append(f"source_safety_not_passed:{item}")
        if row.get("blocking_reasons"):blockers.append(f"source_safety_has_blocker:{item}")
    prefixes=lambda prefix:not any(b.startswith(prefix) for b in blockers)
    checks.update({
        "manifest_stage_validated":manifest.get("stage")==PREVIOUS,
        "manifest_all_checks_passed":manifest.get("all_checks_passed") is True,
        "manifest_blocking_reasons_clear":manifest.get("blocking_reasons")==[],
        "manifest_input_load_passed":manifest.get("input_load_passed") is True,
        "manifest_semantic_validation_passed":manifest.get("semantic_validation_passed") is True,
        "manifest_premerge_scope_clear":manifest.get("premerge_block_scope")=="none",
        "manifest_split_readiness_validated":manifest.get("ready_for_covapie_unified_leakage_split_materialization_smoke") is True,
        "manifest_final_dataset_boundary_validated":manifest.get("ready_for_covapie_final_dataset_materialization_smoke") is False,
        "manifest_training_boundary_validated":manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False,
        "manifest_feature_semantics_boundary_validated":manifest.get("feature_semantics_known_for_training") is False and manifest.get("unknown_atom_feature_policy_finalized_for_training") is False and manifest.get("feature_semantics_audit_required_before_training") is True,
        "manifest_canonical_masks_validated":manifest.get("canonical_mask_task_names")==ap.CANONICAL_MASK_TASK_NAMES and manifest.get("canonical_mask_task_aliases")==ap.CANONICAL_MASK_TASK_ALIASES,
        "source_step14ap_commit_is_ancestor":source_commit_is_ancestor,
        "unified_row_count_validated":not any(b=="source_unified_row_count_mismatch" for b in blockers),
        "unified_schema_validated":not any(b=="source_unified_schema_mismatch" for b in blockers),
        "unified_csv_json_validated":not any(b=="source_unified_csv_json_mismatch" for b in blockers),
        "unified_identity_validated":not any(b.startswith("source_unified_duplicate") or b=="source_unified_sample_order_mismatch" for b in blockers),
        "unified_hashes_validated":not any(b.startswith("source_unified_hash_mismatch") for b in blockers),
        "assignment_row_count_validated":not any(b=="source_assignment_row_count_mismatch" for b in blockers),
        "assignment_csv_json_validated":not any(b=="source_assignment_csv_json_mismatch" for b in blockers),
        "assignment_hashes_validated":not any(b.startswith("source_assignment_hash_mismatch") for b in blockers),
        "assignment_identity_validated":not any(b.startswith("source_assignment_id_mismatch") or b.startswith("source_assignment_duplicate_sample") or b=="source_assignment_sample_order_mismatch" for b in blockers),
        "assignment_fields_validated":not any(b.startswith("source_assignment_pdb_mismatch") or b.startswith("source_assignment_ligand_mismatch") or b.startswith("source_assignment_not_passed") or b.startswith("source_assignment_has_blocker") or b.startswith("source_assignment_group_missing") or b.startswith("source_assignment_member_count_invalid") for b in blockers),
        "inventory_row_identity_validated":not any(b in {"source_inventory_row_count_mismatch","source_inventory_group_id_mismatch"} or b.startswith("source_inventory_duplicate_group") for b in blockers),
        "inventory_member_contract_validated":not any(b.startswith("source_inventory_member_count") or b.startswith("source_inventory_members_unsorted") or b.startswith("source_inventory_duplicate_member") or b.startswith("source_inventory_unknown_sample") for b in blockers),
        "inventory_coverage_validated":not any(b.startswith("source_inventory_sample_missing") or b.startswith("source_inventory_sample_multiple_groups") for b in blockers),
        "inventory_assignment_membership_validated":not any("membership_mismatch" in b or "inventory_member_count_mismatch" in b for b in blockers),
        "pair_exact_set_validated":not any(b.startswith("source_pair_") and any(x in b for x in ["row_count","duplicate","missing","unexpected","reversed","order","id_mismatch"]) for b in blockers),
        "pair_identity_validated":not any("pdb_mismatch" in b or "ligand_mismatch" in b or "unknown_sample" in b for b in blockers),
        "pair_status_validated":not any("pair_not_passed" in b or "pair_has_blocker" in b for b in blockers),
        "pair_group_consistency_validated":not any("final_group_flag" in b or "cross_group" in b or "transitive_flag" in b for b in blockers),
        "pair_edge_count_validated":"source_pair_edge_count_mismatch" not in blockers,
        "issue_sentinel_validated":checks["issue_sentinel"],
        "source_safety_contract_validated":prefixes("source_safety"),
        "unified_contract":prefixes("source_unified"),
        "assignment_contract":prefixes("source_assignment"),
        "inventory_contract":prefixes("source_inventory"),
        "inventory_assignment_membership":not any("membership_mismatch" in b or "inventory_member_count" in b for b in blockers),
        "pair_exact_set":not any(b.startswith("source_pair_") and any(x in b for x in ["row_count","duplicate","missing","unexpected","reversed","order","id_mismatch"]) for b in blockers),
        "pair_identity":not any("pdb_mismatch" in b or "ligand_mismatch" in b for b in blockers),
        "pair_group_consistency":not any("final_group_flag" in b or "cross_group" in b or "transitive_flag" in b for b in blockers),
        "source_safety_contract":prefixes("source_safety"),
    })
    blockers=sorted(set(blockers+[f"step14ap_precondition_failed:{k}" for k,v in checks.items() if not v]))
    return SourceValidationResult(not blockers,blockers,typed_uc,typed_ac,copy_rows(inv),copy_rows(pairs),checks)

def copy_rows(rows:list[dict[str,Any]])->list[dict[str,Any]]:return [dict(r) for r in rows]

def _load(paths:InputPaths,activity:RunActivity|None=None)->tuple[dict[str,Any],list[dict[str,Any]],list[str]]:
    blockers=[];data={"_activity":activity}
    for name in paths.__dataclass_fields__:
        path=getattr(paths,name)
        try:
            if name in {"unified_json","assignment_json","manifest"}:
                target=rp(path);data[name]=json.loads(target.read_text())
                if activity is not None:activity.read_paths.add(str(target.resolve()))
            else:data[name]=read_csv(path,activity)
        except (OSError,UnicodeError,json.JSONDecodeError,csv.Error):data[name]=[] if name!="manifest" else {};blockers.append(f"unreadable_input:{name}")
    manifest=data.get("manifest") if isinstance(data.get("manifest"),dict) else {};data.update({"unified_csv_path":paths.unified_csv,"unified_json_path":paths.unified_json,"assignment_csv_path":paths.assignment_csv,"assignment_json_path":paths.assignment_json})
    result=validate_step14ap_source_contract(data,manifest) if not blockers else SourceValidationResult(False,[],[],[],[],[],{})
    blockers=sorted(set(blockers+result.blocking_reasons));checks=result.checks or {"source_inputs_readable":False}
    pre=[{"precondition_item":k,"expected_status":True,"observed_status":v,"precondition_passed":v,"blocking_reasons":"" if v else next((b for b in blockers if k in b),f"step14ap_precondition_failed:{k}")} for k,v in checks.items()]
    return {**data,"typed_unified":result.typed_unified_rows,"typed_assignment":result.typed_assignment_rows,"inventory_csv":result.inventory_rows,"pair_audit":result.pair_rows,"checks":checks,"source_validation_passed":result.source_validation_passed},pre,blockers

def build_candidate_group_split_assignment_rows(source_inventory_rows:list[dict[str,Any]],optimized:dict[str,Any])->list[dict[str,Any]]:
    rows=[]
    for n,(source,rank) in enumerate(zip(sorted(copy_rows(source_inventory_rows),key=lambda r:r.get("final_leakage_group_id","")),optimized.get("signature",[])),1):
        split=SPLITS[rank] if isinstance(rank,int) and 0<=rank<len(SPLITS) else ""
        rows.append({"group_split_assignment_id":f"COVAPIE_GROUP_SPLIT_{n:06d}",**{k:source.get(k,"") for k in ["final_leakage_group_id","group_order","member_count","member_sample_index_row_ids","source_stage_composition","final_leakage_group_status"]},"assigned_split":split,"assigned_split_rank":rank,"split_policy":POLICY,"eligible_for_final_dataset_materialization_smoke":False,"ready_for_training_current_step":False,"feature_semantics_audit_required_before_training":True})
    return rows

def validate_group_split_assignment_rows(candidate_rows:list[dict[str,Any]],source_inventory_rows:list[dict[str,Any]],optimized:dict[str,Any])->list[dict[str,Any]]:
    candidates=copy_rows(candidate_rows);sources=copy_rows(source_inventory_rows);source_multi={};candidate_multi={}
    for row in sources:source_multi.setdefault(row.get("final_leakage_group_id",""),[]).append(row)
    for row in candidates:candidate_multi.setdefault(row.get("final_leakage_group_id",""),[]).append(row)
    expected_ids=[f"COVAPIE_GROUP_SPLIT_{i:06d}" for i in range(1,6)];expected_groups=[f"COVAPIE_LEAKAGE_GROUP_{i:06d}" for i in range(1,6)];expected_split={gid:SPLITS[rank] for gid,rank in zip(expected_groups,optimized.get("signature",[])) if isinstance(rank,int) and 0<=rank<3}
    global_blockers=[]
    if len(candidates)!=5:global_blockers.append("group_split_row_count_mismatch")
    validated=[]
    for n,row in enumerate(candidates,1):
        blockers=[];gid=row.get("final_leakage_group_id","");source_rows=source_multi.get(gid,[])
        if row.get("group_split_assignment_id")!=(expected_ids[n-1] if n<=5 else ""):blockers.append(f"group_split_assignment_id_mismatch:{n}")
        if len(candidate_multi.get(gid,[]))>1:blockers.append(f"group_split_duplicate_group:{gid}")
        if len(source_rows)==0:blockers.append(f"group_split_source_row_missing:{gid}")
        if len(source_rows)>1:blockers.append(f"group_split_source_row_duplicate:{gid}")
        source=source_rows[0] if len(source_rows)==1 else {}
        for field in ["member_count","member_sample_index_row_ids","source_stage_composition","final_leakage_group_status"]:
            left=int(row.get(field,-1)) if field=="member_count" and str(row.get(field,"")).isdigit() else row.get(field)
            right=int(source.get(field,-2)) if field=="member_count" and str(source.get(field,"")).isdigit() else source.get(field)
            if left!=right:blockers.append(f"group_split_source_field_mismatch:{gid}:{field}")
        try:group_order=int(row.get("group_order"));member_count=int(row.get("member_count"));rank=int(row.get("assigned_split_rank"))
        except (TypeError,ValueError):group_order=member_count=rank=-1
        if gid not in expected_groups or group_order!=(expected_groups.index(gid)+1 if gid in expected_groups else -2):blockers.append(f"group_split_source_field_mismatch:{gid}:group_order")
        if row.get("assigned_split") not in SPLITS:blockers.append(f"group_split_invalid_split:{gid}")
        if row.get("assigned_split")!=expected_split.get(gid):blockers.append(f"group_split_optimizer_mismatch:{gid}")
        if row.get("assigned_split") in RANK and rank!=RANK[row["assigned_split"]]:blockers.append(f"group_split_rank_mismatch:{gid}")
        if row.get("split_policy")!=POLICY:blockers.append(f"group_split_policy_mismatch:{gid}")
        members=str(row.get("member_sample_index_row_ids","")).split(";") if row.get("member_sample_index_row_ids") else []
        if not members or members!=sorted(members) or len(members)!=len(set(members)) or member_count!=len(members):blockers.append(f"group_split_member_contract_invalid:{gid}")
        if row.get("ready_for_training_current_step") is not False or row.get("feature_semantics_audit_required_before_training") is not True:blockers.append(f"group_split_readiness_boundary_mismatch:{gid}")
        preserved=len(source_rows)==1 and not any(b.startswith(f"group_split_source_field_mismatch:{gid}") or b==f"group_split_member_contract_invalid:{gid}" or b==f"group_split_duplicate_group:{gid}" for b in blockers)
        passed=not blockers
        validated.append({**row,"group_order":group_order,"member_count":member_count,"assigned_split_rank":rank,"group_kept_intact":preserved,"group_split_assignment_passed":passed,"eligible_for_final_dataset_materialization_smoke":passed,"blocking_reasons":";".join(sorted(set(blockers)))})
    if global_blockers and validated:
        validated[0]["blocking_reasons"]=";".join(sorted(set(filter(None,[validated[0]["blocking_reasons"],*global_blockers]))));validated[0]["group_split_assignment_passed"]=False;validated[0]["eligible_for_final_dataset_materialization_smoke"]=False
    return validated

def build_candidate_sample_split_assignment_rows(source_unified_rows:list[dict[str,Any]],source_assignment_rows:list[dict[str,Any]],group_split_candidates:list[dict[str,Any]])->list[dict[str,Any]]:
    assignment_multi={};group_multi={}
    for row in copy_rows(source_assignment_rows):assignment_multi.setdefault(row.get("sample_index_row_id",""),[]).append(row)
    for row in copy_rows(group_split_candidates):group_multi.setdefault(row.get("final_leakage_group_id",""),[]).append(row)
    rows=[]
    for n,source in enumerate(copy_rows(source_unified_rows),1):
        sid=source.get("sample_index_row_id","");assignment=assignment_multi.get(sid,[{}])[0] if len(assignment_multi.get(sid,[]))==1 else {};gid=assignment.get("final_leakage_group_id","");group=group_multi.get(gid,[{}])[0] if len(group_multi.get(gid,[]))==1 else {}
        rows.append({"sample_split_assignment_id":f"COVAPIE_SAMPLE_SPLIT_{n:06d}","sample_index_row_id":sid,"pdb_id":source.get("pdb_id",""),"ligand_comp_id":source.get("ligand_comp_id",""),"source_index_stage":assignment.get("source_index_stage",""),"final_leakage_group_id":gid,"final_leakage_group_member_count":assignment.get("final_leakage_group_member_count",0),"assigned_split":group.get("assigned_split",""),"split_unit_type":"final_leakage_group_id","eligible_for_final_dataset_materialization_smoke":False,"ready_for_training_current_step":False,"feature_semantics_audit_required_before_training":True,"leakage_split_design_required_before_training":True})
    return rows

def validate_sample_split_assignment_rows(candidate_rows:list[dict[str,Any]],source_unified_rows:list[dict[str,Any]],source_assignment_rows:list[dict[str,Any]],validated_group_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    candidates=copy_rows(candidate_rows);unified=copy_rows(source_unified_rows);assignments=copy_rows(source_assignment_rows);groups=copy_rows(validated_group_rows)
    def multi(rows,key):
        out={}
        for row in rows:out.setdefault(row.get(key,""),[]).append(row)
        return out
    cm=multi(candidates,"sample_index_row_id");um=multi(unified,"sample_index_row_id");am=multi(assignments,"sample_index_row_id");gm=multi(groups,"final_leakage_group_id")
    expected_order=[r.get("sample_index_row_id","") for r in unified];global_blockers=[]
    if len(candidates)!=11:global_blockers.append("sample_split_row_count_mismatch")
    if [r.get("sample_index_row_id","") for r in candidates]!=expected_order:global_blockers.append("sample_split_order_mismatch")
    validated=[]
    for n,row in enumerate(candidates,1):
        blockers=[];sid=row.get("sample_index_row_id","")
        if row.get("sample_split_assignment_id")!=f"COVAPIE_SAMPLE_SPLIT_{n:06d}":blockers.append(f"sample_split_assignment_id_mismatch:{n}")
        if len(cm.get(sid,[]))>1:blockers.append(f"sample_split_duplicate_sample:{sid}")
        if len(um.get(sid,[]))==0:blockers.append(f"sample_split_source_unified_missing:{sid}")
        if len(um.get(sid,[]))>1:blockers.append(f"sample_split_source_unified_duplicate:{sid}")
        if len(am.get(sid,[]))==0:blockers.append(f"sample_split_source_assignment_missing:{sid}")
        if len(am.get(sid,[]))>1:blockers.append(f"sample_split_source_assignment_duplicate:{sid}")
        u=um.get(sid,[{}])[0] if len(um.get(sid,[]))==1 else {};a=am.get(sid,[{}])[0] if len(am.get(sid,[]))==1 else {};gid=a.get("final_leakage_group_id","")
        if len(gm.get(gid,[]))==0:blockers.append(f"sample_split_group_row_missing:{sid}")
        if len(gm.get(gid,[]))>1:blockers.append(f"sample_split_group_row_duplicate:{sid}")
        g=gm.get(gid,[{}])[0] if len(gm.get(gid,[]))==1 else {}
        if row.get("pdb_id")!=u.get("pdb_id"):blockers.append(f"sample_split_pdb_mismatch:{sid}")
        if row.get("ligand_comp_id")!=u.get("ligand_comp_id"):blockers.append(f"sample_split_ligand_mismatch:{sid}")
        if row.get("source_index_stage")!=a.get("source_index_stage"):blockers.append(f"sample_split_source_stage_mismatch:{sid}")
        if row.get("final_leakage_group_id")!=gid:blockers.append(f"sample_split_group_mismatch:{sid}")
        try:count=int(row.get("final_leakage_group_member_count"))
        except (TypeError,ValueError):count=-1
        if count!=a.get("final_leakage_group_member_count") or count!=g.get("member_count"):blockers.append(f"sample_split_member_count_mismatch:{sid}")
        if row.get("assigned_split")!=g.get("assigned_split"):blockers.append(f"sample_split_assigned_split_mismatch:{sid}")
        if row.get("split_unit_type")!="final_leakage_group_id":blockers.append(f"sample_split_unit_type_mismatch:{sid}")
        if row.get("ready_for_training_current_step") is not False or row.get("feature_semantics_audit_required_before_training") is not True or row.get("leakage_split_design_required_before_training") is not True:blockers.append(f"sample_split_readiness_boundary_mismatch:{sid}")
        passed=not blockers
        validated.append({**row,"final_leakage_group_member_count":count,"group_assignment_row_found":len(gm.get(gid,[]))==1,"source_unified_row_found":len(um.get(sid,[]))==1,"source_assignment_row_found":len(am.get(sid,[]))==1,"sample_split_assignment_passed":passed,"eligible_for_final_dataset_materialization_smoke":passed,"blocking_reasons":";".join(sorted(set(blockers)))})
    if global_blockers and validated:
        validated[0]["blocking_reasons"]=";".join(sorted(set(filter(None,[validated[0]["blocking_reasons"],*global_blockers]))));validated[0]["sample_split_assignment_passed"]=False;validated[0]["eligible_for_final_dataset_materialization_smoke"]=False
    return validated

def validate_group_sample_split_consistency(validated_group_rows:list[dict[str,Any]],validated_sample_rows:list[dict[str,Any]])->dict[str,Any]:
    blockers=[];per_group={}
    sample_by_group={}
    for row in validated_sample_rows:sample_by_group.setdefault(row.get("final_leakage_group_id",""),[]).append(row)
    for group in validated_group_rows:
        gid=group.get("final_leakage_group_id","");members=set(str(group.get("member_sample_index_row_ids","")).split(";")) if group.get("member_sample_index_row_ids") else set();samples=sample_by_group.get(gid,[]);assigned={r.get("sample_index_row_id","") for r in samples};membership=members==assigned;splits={r.get("assigned_split","") for r in samples};split_ok=len(splits)==1 and splits=={group.get("assigned_split","")}
        reasons=[]
        if not membership:reasons.append(f"group_sample_membership_mismatch:{gid}")
        if not split_ok:reasons.append(f"group_sample_split_mismatch:{gid}")
        blockers.extend(reasons);per_group[gid]={"passed":membership and split_ok,"blocking_reasons":reasons}
    membership=not any(b.startswith("group_sample_membership_mismatch") for b in blockers);split_ok=not any(b.startswith("group_sample_split_mismatch") for b in blockers)
    return {"group_integrity_passed":membership and split_ok,"all_groups_kept_intact":membership and split_ok,"group_sample_membership_consistent":membership,"group_sample_split_consistent":split_ok,"per_group":per_group,"blocking_reasons":sorted(set(blockers))}

GROUP_INT_FIELDS={"group_order","member_count","assigned_split_rank"};GROUP_BOOL_FIELDS={"group_kept_intact","group_split_assignment_passed","eligible_for_final_dataset_materialization_smoke","ready_for_training_current_step","feature_semantics_audit_required_before_training"}
SAMPLE_INT_FIELDS={"final_leakage_group_member_count"};SAMPLE_BOOL_FIELDS={"group_assignment_row_found","source_unified_row_found","source_assignment_row_found","sample_split_assignment_passed","eligible_for_final_dataset_materialization_smoke","ready_for_training_current_step","feature_semantics_audit_required_before_training","leakage_split_design_required_before_training"}
def _typed_output_row(row:dict[str,Any],ints:set[str],bools:set[str],fields:list[str])->dict[str,Any]:
    if set(row)!=set(fields):raise ValueError("schema_mismatch")
    return {k:(int(v) if k in ints else strict(v) if k in bools else v) for k,v in row.items()}
def _read_with_header(path:Path,activity:RunActivity|None=None)->tuple[list[str],list[dict[str,str]]]:
    target=rp(path)
    with target.open(newline="",encoding="utf-8") as handle:
        reader=csv.DictReader(handle);header,rows=list(reader.fieldnames or []),list(reader)
    if activity is not None:activity.read_paths.add(str(target.resolve()))
    return header,rows
def _validate_written_assignment(expected_rows:list[dict[str,Any]],csv_path:Path,fields:list[str],ints:set[str],bools:set[str],pass_field:str,prefix:str,activity:RunActivity|None=None)->dict[str,Any]:
    blockers=[]
    try:header,raw=_read_with_header(csv_path,activity)
    except (OSError,UnicodeError,csv.Error):header=[];raw=[];blockers.append(f"{prefix}_csv_unreadable")
    if header!=fields:blockers.append(f"{prefix}_csv_schema_mismatch")
    if len(raw)!=len(expected_rows):blockers.append(f"{prefix}_csv_row_count_mismatch")
    try:typed=[_typed_output_row(r,ints,bools,fields) for r in raw]
    except (TypeError,ValueError):typed=[];blockers.append(f"{prefix}_csv_typed_parse_failed")
    expected=[{f:r.get(f,"") for f in fields} for r in expected_rows]
    if typed!=expected:blockers.append(f"{prefix}_csv_content_mismatch")
    if typed and not all(r.get(pass_field) is True for r in typed):blockers.append(f"{prefix}_csv_pass_field_failed")
    return {"passed":not blockers,"typed_rows":typed,"blocking_reasons":sorted(set(blockers))}
def validate_written_group_split_assignment(expected_rows:list[dict[str,Any]],csv_path:Path,activity:RunActivity|None=None)->dict[str,Any]:return _validate_written_assignment(expected_rows,csv_path,GROUP_FIELDS,GROUP_INT_FIELDS,GROUP_BOOL_FIELDS,"group_split_assignment_passed","group_split_assignment_write",activity)
def validate_written_sample_split_assignment(expected_rows:list[dict[str,Any]],csv_path:Path,activity:RunActivity|None=None)->dict[str,Any]:return _validate_written_assignment(expected_rows,csv_path,SAMPLE_FIELDS,SAMPLE_INT_FIELDS,SAMPLE_BOOL_FIELDS,"sample_split_assignment_passed","sample_split_assignment_write",activity)

def validate_written_split_sample_indexes(source_unified_rows:list[dict[str,Any]],validated_sample_rows:list[dict[str,Any]],train_path:Path,validation_path:Path,test_path:Path,activity:RunActivity|None=None)->dict[str,Any]:
    blockers=[];source=copy_rows(source_unified_rows);source_by={r.get("sample_index_row_id",""):r for r in source};order={r.get("sample_index_row_id",""):n for n,r in enumerate(source)};assignment={r.get("sample_index_row_id",""):r.get("assigned_split","") for r in validated_sample_rows};typed_by_split={};per_split={}
    for split,path in zip(SPLITS,[train_path,validation_path,test_path]):
        local=[]
        try:header,raw=_read_with_header(path,activity)
        except (OSError,UnicodeError,csv.Error):header=[];raw=[];local.append(f"split_file_unreadable:{split}")
        if header!=ap.SAMPLE_INDEX_FIELDS:local.append(f"split_file_schema_mismatch:{split}")
        try:typed=[ap.typed(r) for r in raw]
        except (TypeError,ValueError,KeyError):typed=[];local.append(f"split_file_typed_parse_failed:{split}")
        expected_count=sum(value==split for value in assignment.values())
        if len(typed)!=expected_count:local.append(f"split_file_count_mismatch:{split}")
        ids=[r.get("sample_index_row_id","") for r in typed]
        if ids!=sorted(ids,key=lambda sid:order.get(sid,10**9)):local.append(f"split_file_row_order_mismatch:{split}")
        if any(source_by.get(r.get("sample_index_row_id"))!=r for r in typed):local.append(f"split_file_source_mismatch:{split}")
        if any(assignment.get(sid)!=split for sid in ids):local.append(f"split_file_assignment_mismatch:{split}")
        blockers.extend(local);typed_by_split[split]=typed;per_split[split]=not local
    all_rows=[r for split in SPLITS for r in typed_by_split[split]];ids=[r.get("sample_index_row_id","") for r in all_rows];mutually_exclusive=len(ids)==len(set(ids));partition=len(all_rows)==len(source) and set(ids)==set(source_by);preserved=partition and sorted(all_rows,key=lambda r:order.get(r.get("sample_index_row_id"),10**9))==source
    if not mutually_exclusive:blockers.append("split_files_not_mutually_exclusive")
    if not partition:blockers.append("split_files_do_not_partition_unified_index")
    if not preserved:blockers.append("split_files_source_preservation_failed")
    result={"train_write_validation_passed":per_split.get("train",False),"validation_write_validation_passed":per_split.get("validation",False),"test_write_validation_passed":per_split.get("test",False),"split_files_schema_passed":not any("schema" in b for b in blockers),"split_files_counts_passed":not any("count" in b for b in blockers),"split_files_mutually_exclusive":mutually_exclusive,"split_files_partition_unified_index":partition,"split_files_source_preservation_passed":preserved,"split_files_row_order_passed":not any("row_order" in b for b in blockers),"split_files_assignment_consistency_passed":not any("assignment_mismatch" in b for b in blockers),"split_files_write_validation_passed":not blockers,"blocking_reasons":sorted(set(blockers))}
    return result

def build_policy_observations(optimized:dict[str,Any],source_group_count:int)->dict[str,str]:
    return {"policy_name":POLICY,"split_unit":"final_leakage_group_id","split_names":";".join(SPLITS),"target_ratios":";".join(str(TARGET[s]) for s in SPLITS),"randomization_used":"false","split_seed_used":"false","exhaustive_small_n_search":str(optimized.get("candidate_assignment_count")==3**source_group_count).lower(),"candidate_assignment_count":str(optimized.get("candidate_assignment_count")),"valid_candidate_count":str(optimized.get("valid_candidate_count")),"objective_order":"sample_l1_error;sample_max_error;group_l1_error;assignment_signature","tie_break_rule":"lexicographic_assignment_signature","selected_assignment_signature":";".join(map(str,optimized.get("signature",[]))),"selected_sample_counts":";".join(map(str,optimized.get("sample_counts",[]))),"selected_group_counts":";".join(map(str,optimized.get("group_counts",[]))),"sample_l1_error":str(optimized.get("sample_l1_error")),"sample_max_error":str(optimized.get("sample_max_error")),"group_l1_error":str(optimized.get("group_l1_error")),"group_integrity_priority":"true","small_n_status":"provisional_small_n_smoke_only","statistical_representativeness":"false","production_split_policy_finalized":"false","feature_semantics_audit_still_required":"true","validation_test_target_symmetry":str(TARGET["validation"]==TARGET["test"]).lower(),"asymmetric_validation_test_constraint_added":"false","tie_resolved_by_assignment_signature":str(optimized.get("lexicographic_minimum_confirmed") is True).lower(),"selected_signature_is_lexicographic_minimum":str(optimized.get("lexicographic_minimum_confirmed") is True).lower(),"each_split_has_group":str(optimized.get("all_splits_nonempty") is True).lower(),"train_not_smaller_than_validation":str(optimized.get("train_not_smaller_than_validation") is True).lower(),"train_not_smaller_than_test":str(optimized.get("train_not_smaller_than_test") is True).lower()}

def build_and_validate_policy_audit_rows(observations:dict[str,str])->list[dict[str,Any]]:
    rows=[]
    for item,expected in POLICY_EXPECTED.items():
        observed=str(observations.get(item,"<missing>"));passed=observed==expected;reason="" if passed else f"policy_mismatch:{item}:expected={expected}:observed={observed}"
        rows.append({"policy_audit_item":item,"observed_value":observed,"expected_value":expected,"policy_check_passed":passed,"blocking_reasons":reason})
    extras=sorted(set(observations)-set(POLICY_EXPECTED))
    if extras:rows[0]["policy_check_passed"]=False;rows[0]["blocking_reasons"]=";".join(filter(None,[rows[0]["blocking_reasons"],*[f"policy_unexpected_item:{x}" for x in extras]]))
    return rows

def validate_written_policy_audit(expected_rows:list[dict[str,Any]],path:Path,activity:RunActivity|None=None)->dict[str,Any]:
    result=_validate_written_assignment(expected_rows,path,POLICY_FIELDS,set(),{"policy_check_passed"},"policy_check_passed","policy_audit_write",activity)
    items=[r.get("policy_audit_item") for r in result["typed_rows"]]
    if items!=list(POLICY_EXPECTED) or len(items)!=len(set(items)):result["blocking_reasons"].append("policy_audit_write_item_contract_mismatch");result["passed"]=False
    return {"policy_write_validation_passed":result["passed"],"policy_item_count":len(result["typed_rows"]),"blocking_reasons":sorted(set(result["blocking_reasons"]))}

LEAK_SIGNAL_FIELDS=["direct_must_link_edge","same_final_leakage_group_after_transitive_closure","same_ligand_graph","same_murcko_scaffold","same_protein_accession","same_exact_protein_sequence","same_sequence_cluster_90","same_sequence_cluster_50"]
LEAK_BOOL_FIELDS={"cross_split_pair",*LEAK_SIGNAL_FIELDS,"transitive_only_same_group","leakage_violation","pair_split_leakage_passed"}
def build_candidate_cross_split_leakage_rows(source_pair_rows:list[dict[str,Any]],validated_sample_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    sample_multi={}
    for row in copy_rows(validated_sample_rows):sample_multi.setdefault(row.get("sample_index_row_id",""),[]).append(row)
    rows=[]
    for n,source in enumerate(copy_rows(source_pair_rows),1):
        left,right=source.get("left_sample_index_row_id",""),source.get("right_sample_index_row_id","");l=sample_multi.get(left,[{}])[0] if len(sample_multi.get(left,[]))==1 else {};r=sample_multi.get(right,[{}])[0] if len(sample_multi.get(right,[]))==1 else {};cross=l.get("assigned_split")!=r.get("assigned_split")
        rows.append({"split_leakage_audit_id":f"COVAPIE_SPLIT_LEAKAGE_{n:06d}","left_sample_index_row_id":left,"right_sample_index_row_id":right,"left_final_leakage_group_id":l.get("final_leakage_group_id",""),"right_final_leakage_group_id":r.get("final_leakage_group_id",""),"left_split":l.get("assigned_split",""),"right_split":r.get("assigned_split",""),"cross_split_pair":cross,**{f:strict(source.get(f)) for f in LEAK_SIGNAL_FIELDS},"transitive_only_same_group":strict(source.get("transitive_only_same_group"))})
    return rows

def validate_cross_split_leakage_rows(candidate_rows:list[dict[str,Any]],source_pair_rows:list[dict[str,Any]],validated_sample_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    candidates=copy_rows(candidate_rows);sources=copy_rows(source_pair_rows);sample_multi={}
    for row in validated_sample_rows:sample_multi.setdefault(row.get("sample_index_row_id",""),[]).append(row)
    global_blockers=[]
    if len(candidates)!=55:global_blockers.append("leakage_row_count_mismatch")
    validated=[]
    for n,row in enumerate(candidates,1):
        blockers=[];source=sources[n-1] if n<=len(sources) else {};left,right=row.get("left_sample_index_row_id",""),row.get("right_sample_index_row_id","");expected_pair=(source.get("left_sample_index_row_id",""),source.get("right_sample_index_row_id",""))
        if row.get("split_leakage_audit_id")!=f"COVAPIE_SPLIT_LEAKAGE_{n:06d}":blockers.append(f"leakage_audit_id_mismatch:{n}")
        if (left,right)!=expected_pair:blockers.append(f"leakage_pair_mismatch:{n}")
        l=sample_multi.get(left,[{}])[0] if len(sample_multi.get(left,[]))==1 else {};r=sample_multi.get(right,[{}])[0] if len(sample_multi.get(right,[]))==1 else {};lg,rg=l.get("final_leakage_group_id",""),r.get("final_leakage_group_id","");ls,rs=l.get("assigned_split",""),r.get("assigned_split","");cross=ls!=rs
        if row.get("left_final_leakage_group_id")!=lg or row.get("right_final_leakage_group_id")!=rg:blockers.append(f"leakage_group_mismatch:{left}:{right}")
        if row.get("left_split")!=ls or row.get("right_split")!=rs:blockers.append(f"leakage_split_mismatch:{left}:{right}")
        evidence={}
        for field in LEAK_SIGNAL_FIELDS+["transitive_only_same_group"]:
            try:expected=strict(source.get(field));observed=strict(row.get(field));evidence[field]=expected
            except ValueError:expected=False;observed=None
            if observed!=expected:blockers.append(f"leakage_source_field_mismatch:{left}:{right}:{field}")
        try:observed_cross=strict(row.get("cross_split_pair"))
        except ValueError:observed_cross=None
        if observed_cross!=cross:blockers.append(f"leakage_cross_split_flag_mismatch:{left}:{right}")
        must_link=any(evidence.get(f,False) for f in LEAK_SIGNAL_FIELDS);violation=cross and must_link;passed=not violation
        if "leakage_violation" in row:
            try:flag=strict(row["leakage_violation"])
            except ValueError:flag=None
            if flag!=violation:blockers.append(f"leakage_violation_flag_mismatch:{left}:{right}")
        if "pair_split_leakage_passed" in row:
            try:flag=strict(row["pair_split_leakage_passed"])
            except ValueError:flag=None
            if flag!=passed:blockers.append(f"leakage_pass_flag_mismatch:{left}:{right}")
        if violation:blockers.append(f"cross_split_must_link:{left}:{right}")
        validated.append({**row,"leakage_violation":violation,"pair_split_leakage_passed":passed and not blockers,"blocking_reasons":";".join(sorted(set(blockers)))})
    if global_blockers and validated:validated[0]["blocking_reasons"]=";".join(sorted(set(filter(None,[validated[0]["blocking_reasons"],*global_blockers]))));validated[0]["pair_split_leakage_passed"]=False
    return validated

def validate_cross_split_leakage_summary(validated_leakage_rows:list[dict[str,Any]])->dict[str,Any]:
    rows=copy_rows(validated_leakage_rows);cross=[r for r in rows if r.get("cross_split_pair") is True];counts={field:sum(r.get(field) is True for r in cross) for field in LEAK_SIGNAL_FIELDS};violations=sum(r.get("leakage_violation") is True for r in rows);all_passed=len(rows)==55 and all(r.get("pair_split_leakage_passed") is True and not r.get("blocking_reasons") for r in rows);blockers=[]
    if len(rows)!=55:blockers.append("leakage_summary_pair_count_mismatch")
    if len(cross)!=26 or len(rows)-len(cross)!=29:blockers.append("leakage_summary_cross_within_count_mismatch")
    for field,count in counts.items():
        if count:blockers.append(f"leakage_summary_cross_split_signal:{field}:{count}")
    if violations:blockers.append(f"leakage_summary_violation_count:{violations}")
    if not all_passed:blockers.append("leakage_summary_pair_rows_failed")
    return {"total_pair_count":len(rows),"cross_split_pair_count":len(cross),"within_split_pair_count":len(rows)-len(cross),"leakage_violation_count":violations,"direct_must_link_cross_split_count":counts["direct_must_link_edge"],"same_final_group_cross_split_count":counts["same_final_leakage_group_after_transitive_closure"],"same_ligand_graph_cross_split_count":counts["same_ligand_graph"],"same_murcko_scaffold_cross_split_count":counts["same_murcko_scaffold"],"same_protein_accession_cross_split_count":counts["same_protein_accession"],"same_exact_protein_sequence_cross_split_count":counts["same_exact_protein_sequence"],"same_sequence_cluster_90_cross_split_count":counts["same_sequence_cluster_90"],"same_sequence_cluster_50_cross_split_count":counts["same_sequence_cluster_50"],"all_pair_rows_passed":all_passed,"all_cross_split_leakage_checks_passed":not blockers,"blocking_reasons":sorted(set(blockers))}

def validate_written_cross_split_leakage_audit(expected_rows:list[dict[str,Any]],path:Path,activity:RunActivity|None=None)->dict[str,Any]:
    result=_validate_written_assignment(expected_rows,path,LEAK_FIELDS,set(),LEAK_BOOL_FIELDS,"pair_split_leakage_passed","leakage_audit_write",activity)
    passed=result["passed"] and len(result["typed_rows"])==55
    return {"leakage_audit_write_validation_passed":passed,"leakage_audit_row_count":len(result["typed_rows"]),"blocking_reasons":result["blocking_reasons"]+([] if len(result["typed_rows"])==55 else ["leakage_audit_write_row_count_mismatch"])}

SMALL_N_STATUS="provisional_small_n_smoke_only_not_statistically_representative"
def _expected_balance_rows(validated_group_rows:list[dict[str,Any]],validated_sample_rows:list[dict[str,Any]],group_sample_consistency:dict[str,Any])->list[dict[str,Any]]:
    total_samples=len(validated_sample_rows);total_groups=len(validated_group_rows);rows=[]
    for n,split in enumerate(SPLITS,1):
        sc=sum(r.get("assigned_split")==split for r in validated_sample_rows);gc=sum(r.get("assigned_split")==split for r in validated_group_rows);sr=Fraction(sc,total_samples);gr=Fraction(gc,total_groups)
        rows.append({"split_balance_audit_id":f"COVAPIE_BALANCE_{n:06d}","split_name":split,"target_sample_ratio":str(TARGET[split]),"actual_sample_count":sc,"actual_sample_ratio":str(sr),"sample_ratio_absolute_deviation":str(abs(sr-TARGET[split])),"target_group_ratio":str(TARGET[split]),"actual_group_count":gc,"actual_group_ratio":str(gr),"group_ratio_absolute_deviation":str(abs(gr-TARGET[split])),"minimum_one_group_passed":gc>=1,"group_integrity_passed":group_sample_consistency.get("group_integrity_passed") is True,"statistically_representative":False,"balance_status":SMALL_N_STATUS})
    rows.append({"split_balance_audit_id":"COVAPIE_BALANCE_000004","split_name":"total","target_sample_ratio":"1","actual_sample_count":total_samples,"actual_sample_ratio":"1","sample_ratio_absolute_deviation":"0","target_group_ratio":"1","actual_group_count":total_groups,"actual_group_ratio":"1","group_ratio_absolute_deviation":"0","minimum_one_group_passed":total_groups>0,"group_integrity_passed":group_sample_consistency.get("group_integrity_passed") is True,"statistically_representative":False,"balance_status":SMALL_N_STATUS})
    return rows
def build_candidate_balance_rows(validated_group_rows:list[dict[str,Any]],validated_sample_rows:list[dict[str,Any]],group_sample_consistency:dict[str,Any])->list[dict[str,Any]]:return _expected_balance_rows(validated_group_rows,validated_sample_rows,group_sample_consistency)

def validate_balance_rows(candidate_rows:list[dict[str,Any]],validated_group_rows:list[dict[str,Any]],validated_sample_rows:list[dict[str,Any]],group_sample_consistency:dict[str,Any])->list[dict[str,Any]]:
    candidates=copy_rows(candidate_rows);expected=_expected_balance_rows(validated_group_rows,validated_sample_rows,group_sample_consistency);global_blockers=[]
    if len(candidates)!=4:global_blockers.append("balance_row_count_mismatch")
    if [r.get("split_name") for r in candidates]!=SPLITS+["total"]:global_blockers.append("balance_split_order_mismatch")
    validated=[]
    for n,row in enumerate(candidates,1):
        blockers=[];exp=expected[n-1] if n<=len(expected) else {};split=row.get("split_name",f"row{n}")
        if row.get("split_balance_audit_id")!=f"COVAPIE_BALANCE_{n:06d}":blockers.append(f"balance_id_mismatch:{n}")
        checks={"actual_sample_count":"balance_sample_count_mismatch","actual_group_count":"balance_group_count_mismatch","actual_sample_ratio":"balance_sample_ratio_mismatch","actual_group_ratio":"balance_group_ratio_mismatch","sample_ratio_absolute_deviation":"balance_deviation_mismatch","group_ratio_absolute_deviation":"balance_deviation_mismatch","minimum_one_group_passed":"balance_minimum_group_mismatch","group_integrity_passed":"balance_group_integrity_mismatch","balance_status":"balance_small_n_status_mismatch"}
        for field,prefix in checks.items():
            if row.get(field)!=exp.get(field):blockers.append(f"{prefix}:{split}")
        for field in ["target_sample_ratio","target_group_ratio","statistically_representative"]:
            if row.get(field)!=exp.get(field):blockers.append(f"balance_total_mismatch" if split=="total" else f"balance_deviation_mismatch:{split}")
        if split=="total" and any(row.get(f)!=exp.get(f) for f in exp):blockers.append("balance_total_mismatch")
        passed=not blockers
        validated.append({**row,"balance_audit_passed":passed,"blocking_reasons":";".join(sorted(set(blockers)))})
    if global_blockers and validated:validated[0]["blocking_reasons"]=";".join(sorted(set(filter(None,[validated[0]["blocking_reasons"],*global_blockers]))));validated[0]["balance_audit_passed"]=False
    return validated

BALANCE_INT_FIELDS={"actual_sample_count","actual_group_count"};BALANCE_BOOL_FIELDS={"minimum_one_group_passed","group_integrity_passed","statistically_representative","balance_audit_passed"}
def validate_written_balance_audit(expected_rows:list[dict[str,Any]],path:Path,activity:RunActivity|None=None)->dict[str,Any]:
    result=_validate_written_assignment(expected_rows,path,BALANCE_FIELDS,BALANCE_INT_FIELDS,BALANCE_BOOL_FIELDS,"balance_audit_passed","balance_audit_write",activity);passed=result["passed"] and len(result["typed_rows"])==4
    return {"balance_audit_write_validation_passed":passed,"balance_audit_row_count":len(result["typed_rows"]),"blocking_reasons":result["blocking_reasons"]+([] if len(result["typed_rows"])==4 else ["balance_audit_write_row_count_mismatch"])}

def _issues(blockers:list[str])->list[dict[str,Any]]:
    blockers=sorted(set(x for x in blockers if x))
    if not blockers:return [{"issue_id":"NO_UNIFIED_LEAKAGE_SPLIT_MATERIALIZATION_ISSUES","issue_scope":"current_11_sample_group_level_split_smoke_v0","issue_severity":"none","issue_type":"no_issues","issue_description":"No unified leakage split materialization issues detected.","issue_status":"passed"}]
    return [{"issue_id":f"COVAPIE_SPLIT_ISSUE_{i:06d}","issue_scope":"current_11_sample_group_level_split_smoke_v0","issue_severity":"blocking","issue_type":"validation","issue_description":b,"issue_status":"failed"} for i,b in enumerate(blockers,1)]

SAFETY_EXPECTED_NORMAL={"network_access_used":False,"download_attempted":False,"raw_entry_read":False,"ccd_raw_read":False,"raw_modified":False,"raw_tracked":False,"raw_staged":False,"step14ap_unchanged":True,"protected_diff_empty":True,"dataloader_diff_empty":True,"unexpected_staged_files":False,"part_or_tmp":False,"forbidden_artifacts":False,"group_assignment_written":True,"sample_assignment_written":True,"train_csv_written":True,"validation_csv_written":True,"test_csv_written":True,"cross_split_audit_written":True,"balance_audit_written":True,"policy_audit_written":True,"precondition_audit_written":True,"split_assignments_written":True,"leakage_matrix_written":False,"final_dataset_written":False,"dataloader_artifacts_written":False,"training_artifacts_written":False,"torch_imported":False,"numpy_imported":False,"rdkit_used":False,"biopython_used":False,"gemmi_used":False,"requests_used":False}
SAFETY_EXPECTED_BLOCKED={**SAFETY_EXPECTED_NORMAL,"split_assignments_written":False}

def build_safety_observations(*,activity:RunActivity,normal_materialization_expected:bool)->dict[str,bool]:
    staged,ok=git("diff","--cached","--name-only");raw_tracked,ok2=git("ls-files","--","data/raw/covalent_sources");raw_staged,ok3=git("diff","--cached","--name-only","--","data/raw/covalent_sources");raw_diff,ok4=git("diff","--name-only","--","data/raw/covalent_sources")
    files=[p for p in rp(ROOT).rglob("*") if p.is_file()];suffixes={p.suffix.lower() for p in files};module_imports=set()
    for node in ast.walk(ast.parse(Path(__file__).read_text())):
        if isinstance(node,ast.Import):module_imports.update(a.name.split('.')[0] for a in node.names)
        if isinstance(node,ast.ImportFrom) and node.module:module_imports.add(node.module.split('.')[0])
    raw_marker=str((REPO/"data/raw").resolve());raw_reads={p for p in activity.read_paths if p.startswith(raw_marker)};raw_writes={p for p in activity.written_paths if p.startswith(raw_marker)}
    expected_counts={"covapie_leakage_group_split_assignment.csv":5 if normal_materialization_expected else 0,"covapie_sample_split_assignment.csv":11 if normal_materialization_expected else 0,"train_sample_index.csv":8 if normal_materialization_expected else 0,"validation_sample_index.csv":2 if normal_materialization_expected else 0,"test_sample_index.csv":1 if normal_materialization_expected else 0,"covapie_cross_split_leakage_audit.csv":55 if normal_materialization_expected else 0,"covapie_split_balance_audit.csv":4 if normal_materialization_expected else 0,"covapie_leakage_split_policy_audit.csv":len(POLICY_EXPECTED) if normal_materialization_expected else 1}
    def materialized(name:str)->bool:
        path=rp(OUT[name]);written=str(path.resolve()) in activity.written_paths
        try:count=len(read_csv(path,activity))
        except (OSError,UnicodeError,csv.Error):return False
        return written and path.is_file() and path.stat().st_size>0 and count==expected_counts[name]
    pre=rp(OUT["covapie_leakage_split_precondition_audit.csv"]);pre_written=str(pre.resolve()) in activity.written_paths and pre.is_file() and pre.stat().st_size>0
    group_ok=materialized("covapie_leakage_group_split_assignment.csv");sample_ok=materialized("covapie_sample_split_assignment.csv");train_ok=materialized("train_sample_index.csv");validation_ok=materialized("validation_sample_index.csv");test_ok=materialized("test_sample_index.csv")
    names={p.name.lower() for p in files}
    return {"network_access_used":activity.network_access_used,"download_attempted":activity.download_attempted,"raw_entry_read":bool(raw_reads),"ccd_raw_read":any("ccd" in p.lower() for p in raw_reads),"raw_modified":bool(raw_writes) or not ok4 or bool(raw_diff),"raw_tracked":not ok2 or bool(raw_tracked),"raw_staged":not ok3 or bool(raw_staged),"step14ap_unchanged":clean([SOURCE_ROOT]),"protected_diff_empty":clean(["equivariant_diffusion/","lightning_modules.py"]),"dataloader_diff_empty":clean(["dataset.py","data/prepare_crossdocked.py"]),"unexpected_staged_files":not ok or bool(staged),"part_or_tmp":bool(suffixes&{".tmp",".part"}),"forbidden_artifacts":bool(suffixes&{".pt",".ckpt",".pth",".pkl",".lmdb",".npz",".tar",".zip",".tgz",".cif",".mmcif",".pdb",".sdf",".mol2"}),"group_assignment_written":group_ok,"sample_assignment_written":sample_ok,"train_csv_written":train_ok,"validation_csv_written":validation_ok,"test_csv_written":test_ok,"cross_split_audit_written":materialized("covapie_cross_split_leakage_audit.csv"),"balance_audit_written":materialized("covapie_split_balance_audit.csv"),"policy_audit_written":materialized("covapie_leakage_split_policy_audit.csv"),"precondition_audit_written":pre_written,"split_assignments_written":group_ok and sample_ok and train_ok and validation_ok and test_ok and normal_materialization_expected,"leakage_matrix_written":any("leakage_matrix" in n for n in names),"final_dataset_written":any("final_dataset" in n for n in names),"dataloader_artifacts_written":any("dataloader" in n for n in names),"training_artifacts_written":any("training" in n or "checkpoint" in n for n in names),"torch_imported":"torch" in module_imports,"numpy_imported":"numpy" in module_imports,"rdkit_used":"rdkit" in module_imports,"biopython_used":"Bio" in module_imports,"gemmi_used":"gemmi" in module_imports,"requests_used":"requests" in module_imports}

def build_safety_rows(observations:dict[str,bool],expected:dict[str,bool])->list[dict[str,Any]]:
    rows=[]
    for item,required in expected.items():
        observed=observations.get(item);passed=observed is required;rows.append({"safety_item":item,"required_status":required,"observed_status":observed,"safety_passed":passed,"blocking_reasons":"" if passed else f"safety_mismatch:{item}"})
    return rows

def validate_written_safety_audit(expected_rows:list[dict[str,Any]],path:Path,activity:RunActivity|None=None)->dict[str,Any]:
    result=_validate_written_assignment(expected_rows,path,SAFETY_FIELDS,set(),{"required_status","observed_status","safety_passed"},"safety_passed","safety_audit_write",activity);items=[r.get("safety_item") for r in result["typed_rows"]]
    passed=result["passed"] and len(items)==33 and items==list(SAFETY_EXPECTED_NORMAL) and len(items)==len(set(items));blockers=result["blocking_reasons"]+([] if passed else ["safety_audit_write_item_contract_mismatch"])
    return {"safety_audit_write_validation_passed":passed,"safety_audit_row_count":len(items),"blocking_reasons":sorted(set(blockers))}

def _blocked(pre:list[dict[str,Any]],blockers:list[str],activity:RunActivity)->dict[str,Any]:
    write_csv(OUT["covapie_leakage_split_precondition_audit.csv"],pre or [{"precondition_item":"input_load","expected_status":True,"observed_status":False,"precondition_passed":False,"blocking_reasons":"input_load_failed"}],PRE_FIELDS,activity)
    policy=[{"policy_audit_item":"split_optimizer","observed_value":"not_executed","expected_value":"executed_after_preconditions","policy_check_passed":False,"blocking_reasons":"source_step14ap_preconditions_failed"}];write_csv(OUT["covapie_leakage_split_policy_audit.csv"],policy,POLICY_FIELDS,activity)
    for name,fields in [("covapie_leakage_group_split_assignment.csv",GROUP_FIELDS),("covapie_sample_split_assignment.csv",SAMPLE_FIELDS),("train_sample_index.csv",ap.SAMPLE_INDEX_FIELDS),("validation_sample_index.csv",ap.SAMPLE_INDEX_FIELDS),("test_sample_index.csv",ap.SAMPLE_INDEX_FIELDS),("covapie_cross_split_leakage_audit.csv",LEAK_FIELDS),("covapie_split_balance_audit.csv",BALANCE_FIELDS)]:write_csv(OUT[name],[],fields,activity)
    observations=build_safety_observations(activity=activity,normal_materialization_expected=False);safety=build_safety_rows(observations,SAFETY_EXPECTED_BLOCKED);blockers+= [r["blocking_reasons"] for r in safety if r["blocking_reasons"]];write_csv(OUT["covapie_leakage_split_safety_audit.csv"],safety,SAFETY_FIELDS,activity);safety_write=validate_written_safety_audit(safety,OUT["covapie_leakage_split_safety_audit.csv"],activity);blockers+=safety_write["blocking_reasons"]
    blockers=sorted(set(filter(None,blockers)));issues=_issues(blockers or ["source_step14ap_preconditions_failed"]);write_csv(OUT["covapie_leakage_split_issue_inventory.csv"],issues,ISSUE_FIELDS,activity)
    m={"stage":STAGE,"step_label":"Step 14AQ","previous_stage":PREVIOUS,"project_name":"CovaPIE","source_step14ap_commit":SOURCE_COMMIT,"source_step14ap_preconditions_passed":False,"split_optimizer_executed":False,"split_materialization_passed":False,"policy_audit_row_count":1,"policy_write_validation_passed":False,"group_split_assignment_row_count":0,"sample_split_assignment_row_count":0,"train_sample_count":0,"validation_sample_count":0,"test_sample_count":0,"cross_split_leakage_audit_row_count":0,"leakage_audit_write_validation_passed":False,"balance_audit_write_validation_passed":False,"safety_audit_write_validation_passed":safety_write["safety_audit_write_validation_passed"],"all_preconditions_passed":False,"all_policy_checks_passed":False,"all_group_assignment_checks_passed":False,"all_sample_assignment_checks_passed":False,"all_cross_split_leakage_checks_passed":False,"all_balance_checks_passed":False,"all_safety_checks_passed":safety_write["safety_audit_write_validation_passed"] and all(r["safety_passed"] for r in safety),"issue_inventory_clear":False,"blocking_issue_count":len(issues),"leakage_violation_count":0,"ready_for_covapie_final_dataset_materialization_smoke":False,"ready_for_training":False,"ready_to_train_now":False,"all_checks_passed":False,"recommended_next_step":"resolve_covapie_unified_leakage_split_materialization_issues","blocking_reasons":blockers,"canonical_mask_task_names":ap.CANONICAL_MASK_TASK_NAMES,"canonical_mask_task_aliases":ap.CANONICAL_MASK_TASK_ALIASES,"b3_scaffold_only_included":True}
    write_json(OUT["covapie_unified_leakage_split_materialization_smoke_manifest.json"],m,activity);atomic(SUMMARY,"# CovaPIE unified leakage split materialization smoke v0\n\nBlocked before split optimization; no split readiness claimed.\n",activity);return {"manifest":m,"issues":issues,"groups":[],"samples":[],"leakage":[],"balance":[],"policy":policy,"safety":safety,"activity":activity}

def run(paths:InputPaths=DEFAULT_INPUT_PATHS)->dict[str,Any]:
    activity=RunActivity();data,pre,source_blockers=_load(paths,activity)
    if source_blockers:return _blocked(pre,source_blockers,activity)
    source_validation_passed=data["source_validation_passed"];unified=data["typed_unified"];assignments=data["typed_assignment"];inventory=data["inventory_csv"];pairs=data["pair_audit"]
    optimized=optimize_group_split(inventory);group_candidates=build_candidate_group_split_assignment_rows(inventory,optimized);groups=validate_group_split_assignment_rows(group_candidates,inventory,optimized);sample_candidates=build_candidate_sample_split_assignment_rows(unified,assignments,groups);samples=validate_sample_split_assignment_rows(sample_candidates,unified,assignments,groups);consistency=validate_group_sample_split_consistency(groups,samples);final_groups=[]
    for row in groups:
        gid=row["final_leakage_group_id"];cross=consistency["per_group"].get(gid,{"passed":False,"blocking_reasons":[f"group_sample_membership_mismatch:{gid}"]});kept=row["group_kept_intact"] and cross["passed"];passed=row["group_split_assignment_passed"] and kept;reasons=sorted(set(filter(None,row["blocking_reasons"].split(";")+cross["blocking_reasons"])));final_groups.append({**row,"group_kept_intact":kept,"group_split_assignment_passed":passed,"eligible_for_final_dataset_materialization_smoke":passed,"blocking_reasons":";".join(reasons)})
    groups=final_groups;component_blockers=[reason for row in groups+samples for reason in str(row.get("blocking_reasons","")).split(";") if reason]+consistency["blocking_reasons"]
    write_csv(OUT["covapie_leakage_split_precondition_audit.csv"],pre,PRE_FIELDS,activity);write_csv(OUT["covapie_leakage_group_split_assignment.csv"],groups,GROUP_FIELDS,activity);group_write=validate_written_group_split_assignment(groups,OUT["covapie_leakage_group_split_assignment.csv"],activity);component_blockers+=group_write["blocking_reasons"]
    write_csv(OUT["covapie_sample_split_assignment.csv"],samples,SAMPLE_FIELDS,activity);sample_write=validate_written_sample_split_assignment(samples,OUT["covapie_sample_split_assignment.csv"],activity);component_blockers+=sample_write["blocking_reasons"]
    sample_split={r["sample_index_row_id"]:r["assigned_split"] for r in samples};split_rows={name:[row for row in unified if sample_split[row["sample_index_row_id"]]==name] for name in SPLITS}
    for name in SPLITS:write_csv(OUT[f"{name}_sample_index.csv"],split_rows[name],ap.SAMPLE_INDEX_FIELDS,activity)
    split_write=validate_written_split_sample_indexes(unified,samples,OUT["train_sample_index.csv"],OUT["validation_sample_index.csv"],OUT["test_sample_index.csv"],activity);component_blockers+=split_write["blocking_reasons"]
    leakage_candidates=build_candidate_cross_split_leakage_rows(pairs,samples);leakage=validate_cross_split_leakage_rows(leakage_candidates,pairs,samples);leakage_summary=validate_cross_split_leakage_summary(leakage);component_blockers += [reason for row in leakage for reason in str(row.get("blocking_reasons","")).split(";") if reason]+leakage_summary["blocking_reasons"]
    write_csv(OUT["covapie_cross_split_leakage_audit.csv"],leakage,LEAK_FIELDS,activity);leakage_write=validate_written_cross_split_leakage_audit(leakage,OUT["covapie_cross_split_leakage_audit.csv"],activity);component_blockers+=leakage_write["blocking_reasons"]
    balance_candidates=build_candidate_balance_rows(groups,samples,consistency);balance=validate_balance_rows(balance_candidates,groups,samples,consistency);component_blockers += [reason for row in balance for reason in str(row.get("blocking_reasons","")).split(";") if reason];write_csv(OUT["covapie_split_balance_audit.csv"],balance,BALANCE_FIELDS,activity);balance_write=validate_written_balance_audit(balance,OUT["covapie_split_balance_audit.csv"],activity);component_blockers+=balance_write["blocking_reasons"]
    observations=build_policy_observations(optimized,len(inventory));policy=build_and_validate_policy_audit_rows(observations);component_blockers += [r["blocking_reasons"] for r in policy if r["blocking_reasons"]];write_csv(OUT["covapie_leakage_split_policy_audit.csv"],policy,POLICY_FIELDS,activity);policy_write=validate_written_policy_audit(policy,OUT["covapie_leakage_split_policy_audit.csv"],activity);component_blockers+=policy_write["blocking_reasons"]
    safety_observations=build_safety_observations(activity=activity,normal_materialization_expected=True);safety=build_safety_rows(safety_observations,SAFETY_EXPECTED_NORMAL);component_blockers += [r["blocking_reasons"] for r in safety if r["blocking_reasons"]];write_csv(OUT["covapie_leakage_split_safety_audit.csv"],safety,SAFETY_FIELDS,activity);safety_write=validate_written_safety_audit(safety,OUT["covapie_leakage_split_safety_audit.csv"],activity);component_blockers+=safety_write["blocking_reasons"]
    blockers=sorted(set(filter(None,component_blockers)));issues=_issues(blockers);issue_clear=len(issues)==1 and issues[0]["issue_id"]=="NO_UNIFIED_LEAKAGE_SPLIT_MATERIALIZATION_ISSUES" and issues[0]["issue_status"]=="passed" and not blockers;write_csv(OUT["covapie_leakage_split_issue_inventory.csv"],issues,ISSUE_FIELDS,activity)
    all_group=len(groups)==5 and all(r["group_split_assignment_passed"] for r in groups) and group_write["passed"] and consistency["group_integrity_passed"];all_sample=len(samples)==11 and all(r["sample_split_assignment_passed"] for r in samples) and sample_write["passed"] and split_write["split_files_write_validation_passed"];all_policy=len(policy)==len(POLICY_EXPECTED) and all(r["policy_check_passed"] for r in policy) and policy_write["policy_write_validation_passed"];all_leakage=leakage_summary["all_cross_split_leakage_checks_passed"] and leakage_write["leakage_audit_write_validation_passed"];all_balance=len(balance)==4 and all(r["balance_audit_passed"] for r in balance) and balance_write["balance_audit_write_validation_passed"];all_safety=len(safety)==33 and all(r["safety_passed"] for r in safety) and safety_write["safety_audit_write_validation_passed"];passed=source_validation_passed and all_group and all_sample and all_policy and all_leakage and all_balance and all_safety and issue_clear
    ancestor=subprocess.run(["git","merge-base","--is-ancestor",SOURCE_COMMIT,"HEAD"],cwd=REPO,check=False).returncode==0
    m={"stage":STAGE,"step_label":"Step 14AQ","previous_stage":PREVIOUS,"project_name":"CovaPIE","source_step14ap_stage":PREVIOUS,"source_step14ap_commit":SOURCE_COMMIT,"source_step14ap_commit_is_ancestor_of_head":ancestor,"source_step14ap_preconditions_passed":source_validation_passed,"source_input_sha256":{name:sha(getattr(paths,name),activity) for name in paths.__dataclass_fields__},"split_policy":POLICY,"split_unit":"final_leakage_group_id","split_optimizer_executed":True,"randomization_used":False,"split_seed_used":False,"candidate_assignment_count":optimized["candidate_assignment_count"],"valid_candidate_count":optimized["valid_candidate_count"],"target_sample_ratios":{"train":"7/10","validation":"3/20","test":"3/20"},"target_group_ratios":{"train":"7/10","validation":"3/20","test":"3/20"},"selected_assignment_signature":optimized["signature"],"sample_l1_error":str(optimized["sample_l1_error"]),"sample_max_error":str(optimized["sample_max_error"]),"group_l1_error":str(optimized["group_l1_error"]),"unified_sample_count":len(unified),"final_leakage_group_count":len(groups),"group_split_assignment_row_count":len(groups),"sample_split_assignment_row_count":len(samples),"train_group_count":optimized["group_counts"][0],"validation_group_count":optimized["group_counts"][1],"test_group_count":optimized["group_counts"][2],"train_sample_count":optimized["sample_counts"][0],"validation_sample_count":optimized["sample_counts"][1],"test_sample_count":optimized["sample_counts"][2],"policy_audit_row_count":len(policy),"policy_write_validation_passed":policy_write["policy_write_validation_passed"],"cross_split_leakage_audit_row_count":leakage_summary["total_pair_count"],"cross_split_pair_count":leakage_summary["cross_split_pair_count"],"within_split_pair_count":leakage_summary["within_split_pair_count"],"leakage_violation_count":leakage_summary["leakage_violation_count"],"direct_must_link_cross_split_count":leakage_summary["direct_must_link_cross_split_count"],"same_final_group_cross_split_count":leakage_summary["same_final_group_cross_split_count"],"same_ligand_graph_cross_split_count":leakage_summary["same_ligand_graph_cross_split_count"],"same_murcko_scaffold_cross_split_count":leakage_summary["same_murcko_scaffold_cross_split_count"],"same_protein_accession_cross_split_count":leakage_summary["same_protein_accession_cross_split_count"],"same_exact_protein_sequence_cross_split_count":leakage_summary["same_exact_protein_sequence_cross_split_count"],"same_sequence_cluster_90_cross_split_count":leakage_summary["same_sequence_cluster_90_cross_split_count"],"same_sequence_cluster_50_cross_split_count":leakage_summary["same_sequence_cluster_50_cross_split_count"],"leakage_audit_write_validation_passed":leakage_write["leakage_audit_write_validation_passed"],"balance_audit_write_validation_passed":balance_write["balance_audit_write_validation_passed"],"safety_audit_write_validation_passed":safety_write["safety_audit_write_validation_passed"],"group_split_assignment_write_validation_passed":group_write["passed"],"sample_split_assignment_write_validation_passed":sample_write["passed"],"split_files_write_validation_passed":split_write["split_files_write_validation_passed"],"group_sample_membership_consistent":consistency["group_sample_membership_consistent"],"group_sample_split_consistent":consistency["group_sample_split_consistent"],"group_integrity_passed":consistency["group_integrity_passed"],"split_files_partition_unified_index":split_write["split_files_partition_unified_index"],"split_materialization_passed":passed,"split_materialization_scope":"current_11_sample_provisional_small_n_smoke_only","statistical_representativeness_claimed":False,"production_split_policy_finalized":False,"issue_inventory_clear":issue_clear,"blocking_issue_count":0 if issue_clear else len(issues),"all_preconditions_passed":source_validation_passed,"all_policy_checks_passed":all_policy,"all_group_assignment_checks_passed":all_group,"all_sample_assignment_checks_passed":all_sample,"all_cross_split_leakage_checks_passed":all_leakage,"all_balance_checks_passed":all_balance,"all_safety_checks_passed":all_safety,"all_checks_passed":passed,"ready_for_covapie_final_dataset_materialization_smoke":passed,"ready_for_training":False,"ready_to_train_now":False,"final_dataset_written":False,"actual_dataloader_artifacts_written":False,"training_artifacts_written":False,"feature_semantics_known_for_training":False,"unknown_atom_feature_policy_finalized_for_training":False,"feature_semantics_audit_required_before_training":True,"canonical_mask_task_names":ap.CANONICAL_MASK_TASK_NAMES,"canonical_mask_task_aliases":ap.CANONICAL_MASK_TASK_ALIASES,"b3_scaffold_only_included":True,"no_extra_mask_tasks_added":True,"recommended_next_step":"covapie_final_dataset_materialization_smoke" if passed else "resolve_covapie_unified_leakage_split_materialization_issues","blocking_reasons":blockers}
    write_json(OUT["covapie_unified_leakage_split_materialization_smoke_manifest.json"],m,activity);atomic(SUMMARY,"# CovaPIE unified leakage split materialization smoke v0\n\nDeterministic group-level split smoke only. Statistical representativeness and training readiness are not claimed.\n",activity);return {"manifest":m,"groups":groups,"samples":samples,"leakage":leakage,"leakage_summary":leakage_summary,"balance":balance,"policy":policy,"safety":safety,"issues":issues,"optimizer":optimized,"activity":activity}
