#!/usr/bin/env python
from __future__ import annotations
import csv, json, sys
from pathlib import Path
from typing import Any
REPO_ROOT=Path(__file__).resolve().parents[1]; SRC_ROOT=REPO_ROOT/'src'
if str(SRC_ROOT) not in sys.path:sys.path.insert(0,str(SRC_ROOT))
from covalent_ext import covapie_leakage_split_design_gate as gate
def write(rows:list[dict[str,Any]],path:Path,fields:list[str]):
    out=REPO_ROOT/path;out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8') as h:
        writer=csv.DictWriter(h,fieldnames=fields);writer.writeheader();writer.writerows([{f:r.get(f,'') for f in fields} for r in rows])
def run():
    r=gate.run_covapie_leakage_split_design_gate_v0()
    for rows,path,fields in [(r['precondition_rows'],gate.PRECONDITION_AUDIT_CSV,gate.PRE_COLUMNS),(r['source_rows'],gate.SOURCE_CSV,gate.SOURCE_COLUMNS),(r['pair_rows'],gate.PAIRWISE_CSV,gate.PAIR_COLUMNS),(r['group_rows'],gate.GROUP_PLAN_CSV,gate.GROUP_COLUMNS),(r['feasibility_rows'],gate.FEASIBILITY_CSV,gate.FEAS_COLUMNS),(r['rule_rows'],gate.RULE_CSV,gate.RULE_COLUMNS),(r['contract_rows'],gate.CONTRACT_CSV,gate.CONTRACT_COLUMNS),(r['safety_rows'],gate.SAFETY_CSV,gate.SAFETY_COLUMNS)]:write(rows,path,fields)
    for value,path in [(r['source_rows'],gate.SOURCE_JSON),(r['manifest'],gate.MANIFEST_JSON)]:
        out=REPO_ROOT/path;out.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    m=r['manifest'];summary=f"""# CovaPIE Leakage Split Design Gate v0 Summary

Step 14AG conservatively groups all three current JUG CYS/SG--CAG samples together. Pairwise evidence is not a leakage matrix and no split assignment, final dataset, or training artifact is written.

This conservative grouping uses the same curated ligand component and identical covalent event identity, not PDB-number proximity. Protein sequence and ligand graph evidence are unavailable; a larger dataset needs graph hashes and sequence/accession clusters. One group cannot support a group-safe three-way split.

- leakage_source_inventory_count: `{m['leakage_source_inventory_count']}`
- pairwise_leakage_evidence_count: `{m['pairwise_leakage_evidence_count']}`
- proposed_leakage_group_count: `{m['proposed_leakage_group_count']}`
- ready_for_covapie_leakage_split_review_gate: `{m['ready_for_covapie_leakage_split_review_gate']}`
- recommended_next_step: `{m['recommended_next_step']}`
""";out=REPO_ROOT/gate.SUMMARY_MD;out.write_text(summary,encoding='utf-8')
    print('covapie_leakage_split_design_gate_v0_passed' if m['all_checks_passed'] else 'covapie_leakage_split_design_gate_v0_blocked')
    for key in ['leakage_source_inventory_count','pairwise_leakage_evidence_count','high_conservative_pair_count','proposed_leakage_group_count','proposed_leakage_group_member_count','split_feasibility_assessment_count','leakage_rule_count','train_validation_test_split_feasible','random_row_level_split_allowed','additional_independent_samples_required','ready_for_covapie_leakage_split_review_gate','ready_for_training','recommended_next_step','blocking_reasons']:print(f'{key}={m[key]}')
    return 0 if m['all_checks_passed'] else 1
if __name__=='__main__':raise SystemExit(run())
