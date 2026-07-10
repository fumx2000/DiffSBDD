#!/usr/bin/env python
from __future__ import annotations
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'src'
if str(SRC) not in sys.path:sys.path.insert(0,str(SRC))
from covalent_ext import covapie_leakage_split_review_gate as gate
def write(rows,path,fields):
 out=ROOT/path;out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows([{f:r.get(f,'') for f in fields} for r in rows])
def run():
 r=gate.run_covapie_leakage_split_review_gate_v0()
 for rows,path,fields in [(r['pre'],gate.PRE,gate.PRE_COLUMNS),(r['pair'],gate.PAIR,gate.PAIR_COLUMNS),(r['group'],gate.GROUP,gate.GROUP_COLUMNS),(r['feas'],gate.FEAS,gate.FEAS_COLUMNS),(r['dec'],gate.DEC,gate.DEC_COLUMNS),(r['issue'],gate.ISSUE,gate.ISSUE_COLUMNS),(r['policy'],gate.POLICY,gate.POLICY_COLUMNS),(r['ready'],gate.READY,gate.READY_COLUMNS),(r['safe'],gate.SAFETY,gate.SAFETY_COLUMNS)]:write(rows,path,fields)
 (ROOT/gate.MANIFEST).write_text(json.dumps(r['manifest'],indent=2)+'\n');(ROOT/gate.SUMMARY).write_text(f"# CovaPIE Leakage Split Review Gate v0 Summary\n\nStep 14AH accepts the conservative one-group design only for the current pilot. It does not accept a general similarity algorithm, split materialization, final-dataset materialization, or training. Independent group expansion is required next.\n\n- pairwise_review_passed_count: `{r['manifest']['pairwise_review_passed_count']}`\n- review_decision_accepted_count: `{r['manifest']['review_decision_accepted_count']}`\n- recommended_next_step: `{r['manifest']['recommended_next_step']}`\n")
 m=r['manifest'];print('covapie_leakage_split_review_gate_v0_passed' if m['all_checks_passed'] else 'covapie_leakage_split_review_gate_v0_blocked');print(f"pairwise_review_count={m['pairwise_review_count']}");print(f"group_member_review_count={m['group_member_review_count']}");print(f"review_decision_count={m['review_decision_count']}");print(f"recommended_next_step={m['recommended_next_step']}");return 0 if m['all_checks_passed'] else 1
if __name__=='__main__':raise SystemExit(run())
