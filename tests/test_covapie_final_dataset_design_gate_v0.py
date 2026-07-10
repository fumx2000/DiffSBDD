from __future__ import annotations
import ast, csv, hashlib, json, subprocess, sys
from pathlib import Path
SRC_ROOT=Path(__file__).resolve().parents[1]/'src'
if str(SRC_ROOT) not in sys.path: sys.path.insert(0,str(SRC_ROOT))
from covalent_ext import covapie_final_dataset_design_gate as gate
from covalent_ext import covapie_sample_index_qa_gate as qa
ROOT=Path('data/derived/covalent_small/covapie_final_dataset_design_gate_v0')
def rows(name):
    with (ROOT/name).open(newline='',encoding='utf-8') as h:return list(csv.DictReader(h))
def manifest():return json.loads((ROOT/'covapie_final_dataset_design_gate_manifest.json').read_text())
def imports(path,name):
    t=ast.parse(path.read_text()); return any((isinstance(n,ast.Import) and any(a.name.split('.')[0]==name for a in n.names)) or (isinstance(n,ast.ImportFrom) and n.module and n.module.split('.')[0]==name) for n in ast.walk(t))
def test_step14ae_precondition_and_inventory():
    m=manifest(); prior=json.loads(qa.MANIFEST_JSON.read_text())
    assert prior['stage']==qa.STAGE and prior['all_checks_passed'] is True
    assert m['stage']==gate.STAGE and m['step_label']=='Step 14AF' and m['all_checks_passed'] is True
    source=rows('covapie_final_dataset_source_inventory.csv'); source_json=json.loads((ROOT/'covapie_final_dataset_source_inventory.json').read_text())
    assert len(source)==len(source_json)==3
    assert [f"{r['pdb_id']}/{r['expected_het_id']}" for r in source]==['6BV6/JUG','6BV8/JUG','6BV5/JUG']
    assert {r['approved_for_final_dataset_design_by_qa'] for r in source}=={'True'}
    assert {r['source_eligible_for_final_dataset_design'] for r in source}=={'False'}
def test_schema_mapping_and_projection_are_design_only():
    schema=rows('covapie_final_dataset_schema_contract.csv'); mapping=rows('covapie_final_dataset_field_mapping.csv'); plan=rows('covapie_final_dataset_row_projection_plan.csv')
    assert len(schema)==len(mapping)==46
    assert [r['final_dataset_field'] for r in schema]==gate.FINAL_FIELDS
    assert {r['current_step_materializes_field'] for r in schema}=={'False'} and {r['schema_contract_passed'] for r in schema}=={'True'}
    assert {r['mapping_status'] for r in mapping}=={'planned_and_validated'}
    assert [r['planned_final_dataset_row_id'] for r in plan]==['CYS_SG_FINAL_DATASET_000001','CYS_SG_FINAL_DATASET_000002','CYS_SG_FINAL_DATASET_000003']
    assert {r['eligible_for_leakage_split_design'] for r in plan}=={'True'} and {r['eligible_for_final_dataset_materialization'] for r in plan}=={'False'} and {r['final_dataset_written_current_step'] for r in plan}=={'False'}
def test_auxiliary_readiness_preserves_missing_label_boundaries():
    aux=rows('covapie_final_dataset_auxiliary_label_readiness.csv'); m=manifest()
    assert len(aux)==9
    assert sum(r['auxiliary_task_name']=='warhead_type' and r['readiness_status']=='pending_semantics_and_annotation' for r in aux)==3
    assert sum(r['auxiliary_task_name']=='ligand_residue_atom_pair' and r['readiness_status']=='available_from_validated_struct_conn' and r['ready_for_final_dataset_materialization']=='True' for r in aux)==3
    assert sum(r['auxiliary_task_name']=='pre_post_covalent_geometry' and r['readiness_status']=='partial_post_only' for r in aux)==3
    assert m['warhead_type_ready_count']==0 and m['ligand_residue_atom_pair_ready_count']==3 and m['pre_post_geometry_fully_ready_count']==0 and m['pre_post_geometry_partial_post_only_count']==3
def test_manifest_readiness_and_no_final_dataset_written():
    m=manifest(); assert m['qa_approved_for_final_dataset_design_count']==3 and m['eligible_for_leakage_split_design_count']==3 and m['eligible_for_final_dataset_materialization_count']==0
    assert m['ready_for_covapie_leakage_split_design_gate'] is True and m['ready_for_training'] is False and m['ready_to_train_now'] is False
    assert m['feature_semantics_known_for_training'] is False and m['unknown_atom_feature_policy_finalized_for_training'] is False and m['feature_semantics_audit_required_before_training'] is True
    assert m['recommended_next_step']=='covapie_leakage_split_design_gate'
    assert not any((ROOT/n).exists() for n in ['final_dataset.csv','final_dataset.json','split_assignments.csv','leakage_matrix.csv'])
def test_hashes_safety_masks_and_import_boundaries():
    m=manifest(); assert m['source_sample_index_csv_sha256']==hashlib.sha256(qa.material.SAMPLE_INDEX_CSV.read_bytes()).hexdigest(); assert m['source_sample_index_json_sha256']==hashlib.sha256(qa.material.SAMPLE_INDEX_JSON.read_bytes()).hexdigest()
    safety=rows('covapie_final_dataset_design_safety_audit.csv'); assert {r['safety_passed'] for r in safety}=={'True'}
    assert m['canonical_mask_task_aliases']==['A','B','B2','B3','C'] and m['b3_scaffold_only_included'] is True
    for p in [Path('src/covalent_ext/covapie_final_dataset_design_gate.py'),Path('scripts/check_covapie_final_dataset_design_gate_v0.py')]:
        for n in ['torch','numpy','rdkit','Bio','gemmi','requests','urllib','selenium','playwright','bs4']:assert not imports(p,n)
    raw=qa.material.design.RAW_ROOT; assert not subprocess.run(['git','ls-files',str(raw)],text=True,stdout=subprocess.PIPE,check=False).stdout.strip(); assert not subprocess.run(['git','diff','--cached','--name-only','--',str(raw)],text=True,stdout=subprocess.PIPE,check=False).stdout.strip()
