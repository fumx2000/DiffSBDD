from __future__ import annotations
import csv,json,sys
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'src'
if str(SRC) not in sys.path:sys.path.insert(0,str(SRC))
from covalent_ext import covapie_leakage_split_review_gate as gate
ROOT=Path('data/derived/covalent_small/covapie_leakage_split_review_gate_v0')
def rows(n):
 with (ROOT/n).open(newline='',encoding='utf-8') as h:return list(csv.DictReader(h))
def m():return json.loads((ROOT/'covapie_leakage_split_review_gate_manifest.json').read_text())
def test_pair_group_and_feasibility_reviews():
 pair=rows('covapie_pairwise_leakage_evidence_review.csv');group=rows('covapie_proposed_leakage_group_review.csv');feas=rows('covapie_split_feasibility_review.csv')[0]
 assert len(pair)==3 and len({tuple(sorted((r['left_sample_index_row_id'],r['right_sample_index_row_id']))) for r in pair})==3 and {r['pairwise_review_status'] for r in pair}=={'passed'}
 for k in ['same_curated_ligand_component_confirmed','identical_covalent_event_identity_confirmed','pdb_number_proximity_not_used_confirmed','protein_sequence_identity_not_claimed_confirmed','ligand_graph_identity_not_claimed_confirmed','conservative_grouping_limitation_acknowledged','required_same_group_action_confirmed']:assert {r[k] for r in pair}=={'True'}
 assert len(group)==3 and {r['proposed_leakage_group_id'] for r in group}=={'CYS_SG_LEAKAGE_GROUP_000001'} and {r['accepted_for_current_small_pilot'] for r in group}=={'True'} and {r['accepted_as_general_similarity_algorithm'] for r in group}=={'False'} and {r['proposed_split_assignment_empty'] for r in group}=={'True'}
 assert feas['reviewed_independent_group_count']=='1' and feas['minimum_additional_independent_groups_required']=='2' and feas['current_dataset_split_materialization_approved']=='False' and feas['current_dataset_final_materialization_approved']=='False'
def test_decisions_readiness_and_boundaries():
 manifest=m();dec=rows('covapie_leakage_split_review_decision_registry.csv');issue=rows('covapie_leakage_split_review_issue_inventory.csv')
 assert len(dec)==7 and {r['decision_status'] for r in dec}=={'accepted'} and issue[0]['issue_id']=='NO_LEAKAGE_SPLIT_REVIEW_ISSUES'
 assert manifest['all_checks_passed'] is True and manifest['pairwise_review_passed_count']==3 and manifest['group_member_review_passed_count']==3 and manifest['review_decision_accepted_count']==7 and manifest['review_issue_count']==0
 assert manifest['conservative_group_accepted_for_current_pilot'] is True and manifest['conservative_group_accepted_as_general_similarity_algorithm'] is False and manifest['split_materialization_approved'] is False and manifest['final_dataset_materialization_approved'] is False and manifest['independent_group_expansion_required'] is True
 assert manifest['ready_for_covapie_independent_group_expansion_design_gate'] is True and manifest['ready_for_training'] is False and manifest['feature_semantics_audit_required_before_training'] is True and manifest['recommended_next_step']=='covapie_independent_group_expansion_design_gate'
