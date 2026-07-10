from __future__ import annotations
import ast,csv,hashlib,json,sys
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'src'
if str(SRC) not in sys.path:sys.path.insert(0,str(SRC))
from covalent_ext import covapie_leakage_split_design_gate as gate
from covalent_ext import covapie_final_dataset_design_gate as final
ROOT=Path('data/derived/covalent_small/covapie_leakage_split_design_gate_v0')
def rows(name):
    with (ROOT/name).open(newline='',encoding='utf-8') as h:return list(csv.DictReader(h))
def manifest():return json.loads((ROOT/'covapie_leakage_split_design_gate_manifest.json').read_text())
def imports(path,name):
    t=ast.parse(path.read_text());return any((isinstance(n,ast.Import) and any(a.name.split('.')[0]==name for a in n.names)) or (isinstance(n,ast.ImportFrom) and n.module and n.module.split('.')[0]==name) for n in ast.walk(t))
def test_source_inventory_and_pairwise_evidence():
    m=manifest();assert m['stage']==gate.STAGE and m['step_label']=='Step 14AG' and m['all_checks_passed'] is True
    source=rows('covapie_leakage_source_inventory.csv');assert len(source)==3 and [f"{r['pdb_id']}/{r['expected_het_id']}" for r in source]==['6BV6/JUG','6BV8/JUG','6BV5/JUG']
    assert {r['ligand_comp_id'] for r in source}=={'JUG'} and {r['covalent_bond_atom_pair'] for r in source}=={'SG--CAG'} and {r['current_split_assignment'] for r in source}=={''}
    pair=rows('covapie_leakage_pairwise_evidence.csv');assert len(pair)==3 and len({tuple(sorted((r['left_sample_index_row_id'],r['right_sample_index_row_id']))) for r in pair})==3
    for key in ['same_expected_het_id','same_ligand_comp_id','same_covalent_residue_name','same_covalent_residue_atom_name','same_ligand_covalent_atom_name','same_covalent_bond_atom_pair']:assert {r[key] for r in pair}=={'True'}
    assert {r['pdb_id_proximity_used_as_evidence'] for r in pair}=={'False'} and {r['protein_sequence_identity_evidence_status'] for r in pair}=={'unavailable_in_current_source'} and {r['ligand_graph_identity_evidence_status'] for r in pair}=={'unavailable_use_conservative_component_id_grouping'}
def test_group_plan_feasibility_and_rules():
    group=rows('covapie_proposed_leakage_group_plan.csv');feas=rows('covapie_split_feasibility_assessment.csv')[0];rules=rows('covapie_leakage_rule_contract.csv');m=manifest()
    assert len(group)==3 and {r['proposed_leakage_group_id'] for r in group}=={'CYS_SG_LEAKAGE_GROUP_000001'} and {r['proposed_split_assignment'] for r in group}=={''} and {r['eligible_for_split_materialization'] for r in group}=={'False'}
    assert feas['proposed_leakage_group_count']=='1' and feas['train_validation_test_split_feasible']=='False' and feas['random_row_level_split_allowed']=='False' and feas['all_current_samples_must_remain_together']=='True' and feas['additional_independent_samples_required']=='True'
    assert len(rules)==10 and {r['rule_status'] for r in rules}=={'accepted_for_v0_design'}
    assert m['high_conservative_pair_count']==3 and m['proposed_leakage_group_count']==1 and m['additional_independent_samples_required'] is True
def test_safety_readiness_hashes_and_imports():
    m=manifest();assert m['source_sample_index_csv_sha256']==hashlib.sha256(final.qa.material.SAMPLE_INDEX_CSV.read_bytes()).hexdigest();assert m['source_sample_index_json_sha256']==hashlib.sha256(final.qa.material.SAMPLE_INDEX_JSON.read_bytes()).hexdigest()
    assert m['ready_for_covapie_leakage_split_review_gate'] is True and m['ready_for_training'] is False and m['feature_semantics_known_for_training'] is False and m['unknown_atom_feature_policy_finalized_for_training'] is False and m['feature_semantics_audit_required_before_training'] is True and m['recommended_next_step']=='covapie_leakage_split_review_gate'
    safety=rows('covapie_leakage_split_design_safety_audit.csv');assert {r['safety_passed'] for r in safety}=={'True'}
    assert not any(p.is_file() and (p.name in gate.FORBIDDEN_NAMES or p.suffix.lower() in gate.FORBIDDEN_SUFFIXES) for p in ROOT.rglob('*'))
    for path in [Path('src/covalent_ext/covapie_leakage_split_design_gate.py'),Path('scripts/check_covapie_leakage_split_design_gate_v0.py')]:
        for name in ['torch','numpy','rdkit','Bio','gemmi','requests','urllib','selenium','playwright','bs4']:assert not imports(path,name)
