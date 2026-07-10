#!/usr/bin/env python
from __future__ import annotations
import csv, json, sys
from pathlib import Path
from typing import Any
REPO_ROOT=Path(__file__).resolve().parents[1]; SRC_ROOT=REPO_ROOT/"src"
if str(SRC_ROOT) not in sys.path: sys.path.insert(0,str(SRC_ROOT))
from covalent_ext import covapie_final_dataset_design_gate as gate  # noqa: E402
def write_csv(rows:list[dict[str,Any]],path:Path,fields:list[str])->None:
    out=REPO_ROOT/path; out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows([{f:r.get(f,"") for f in fields} for r in rows])
def write_json(value:Any,path:Path)->None:
    out=REPO_ROOT/path; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
def summary(m:dict[str,Any])->None:
    text=f"""# CovaPIE Final Dataset Design Gate v0 Summary

Step 14AF designs a future final dataset for the three independently QA-approved sample-index rows. It writes source, schema, mapping, projection, auxiliary-label, contract, readiness, and safety design artifacts only. It does not create a final dataset, split assignment, leakage matrix, dataloader artifact, tensor, checkpoint, or training output.

Leakage group and split assignment remain unassigned pending the required leakage/split design gate. Warhead type remains pending formal semantics and annotation; pre-covalent geometry remains unavailable; only the validated ligand-residue SG--CAG pair and post-covalent bond distance are available. Feature semantics remain unresolved for training.

- final_dataset_source_inventory_count: `{m['final_dataset_source_inventory_count']}`
- final_dataset_schema_field_count: `{m['final_dataset_schema_field_count']}`
- auxiliary_label_readiness_count: `{m['auxiliary_label_readiness_count']}`
- ready_for_covapie_leakage_split_design_gate: `{m['ready_for_covapie_leakage_split_design_gate']}`
- ready_for_training: `{m['ready_for_training']}`
- recommended_next_step: `{m['recommended_next_step']}`
"""
    out=REPO_ROOT/gate.SUMMARY_MD; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(text,encoding="utf-8")
def run()->int:
    r=gate.run_covapie_final_dataset_design_gate_v0()
    for rows,path,fields in [(r['precondition_rows'],gate.PRECONDITION_AUDIT_CSV,gate.PRECONDITION_COLUMNS),(r['source_rows'],gate.SOURCE_INVENTORY_CSV,gate.SOURCE_COLUMNS),(r['schema_rows'],gate.SCHEMA_CONTRACT_CSV,gate.SCHEMA_COLUMNS),(r['mapping_rows'],gate.FIELD_MAPPING_CSV,gate.MAPPING_COLUMNS),(r['plan_rows'],gate.ROW_PROJECTION_PLAN_CSV,gate.PROJECTION_COLUMNS),(r['aux_rows'],gate.AUXILIARY_READINESS_CSV,gate.AUX_COLUMNS),(r['contract_rows'],gate.DESIGN_CONTRACT_CSV,gate.CONTRACT_COLUMNS),(r['safety_rows'],gate.SAFETY_AUDIT_CSV,gate.SAFETY_COLUMNS)]: write_csv(rows,path,fields)
    write_json(r['source_rows'],gate.SOURCE_INVENTORY_JSON); write_json(r['manifest'],gate.MANIFEST_JSON); summary(r['manifest'])
    m=r['manifest']; print('covapie_final_dataset_design_gate_v0_passed' if m['all_checks_passed'] else 'covapie_final_dataset_design_gate_v0_blocked')
    for k in ['final_dataset_source_inventory_count','final_dataset_schema_field_count','final_dataset_field_mapping_count','final_dataset_row_projection_plan_count','auxiliary_label_readiness_count','warhead_type_ready_count','ligand_residue_atom_pair_ready_count','pre_post_geometry_partial_post_only_count','eligible_for_leakage_split_design_count','eligible_for_final_dataset_materialization_count','ready_for_covapie_leakage_split_design_gate','ready_for_training','feature_semantics_known_for_training','unknown_atom_feature_policy_finalized_for_training','feature_semantics_audit_required_before_training','recommended_next_step','blocking_reasons']: print(f'{k}={m[k]}')
    return 0 if m['all_checks_passed'] else 1
if __name__=='__main__': raise SystemExit(run())
