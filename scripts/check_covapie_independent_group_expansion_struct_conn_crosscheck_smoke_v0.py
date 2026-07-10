#!/usr/bin/env python
import csv,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from covalent_ext import covapie_independent_group_expansion_struct_conn_crosscheck_smoke as g
def w(rows,path,fields):
 p=R/path;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as h: x=csv.DictWriter(h,fieldnames=fields);x.writeheader();x.writerows([{f:r.get(f,'') for f in fields} for r in rows])
r=g.run()
for a,b,c in [(r['pre'],g.PRE,g.PRECOL),(r['fp'],g.FP,g.FPCOL),(r['inv'],g.INV,g.INVCOL),(r['audit'],g.AUDIT,g.AUDCOL),(r['safe'],g.SAFE,g.SAFECOL)]:w(a,b,c)
(R/g.MANIFEST).write_text(json.dumps(r['manifest'],indent=2)+'\n');m=r['manifest'];(R/g.SUMMARY).write_text(f"# CovaPIE Struct Conn Crosscheck Smoke\n\n- confirmed: `{m['confirmed_unique_exact_match_count']}`\n- recommended next step: `{m['recommended_next_step']}`\n")
print('covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0_passed' if m['all_checks_passed'] else 'covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0_blocked');print(f"candidate_count={m['input_candidate_count']}");print(f"parse_succeeded_count={m['struct_conn_parse_succeeded_count']}");print(f"confirmed_unique_count={m['confirmed_unique_exact_match_count']}");print(f"sample_preparation_eligible_count={m['eligible_for_batch_sample_preparation_count']}");print(f"recommended_next_step={m['recommended_next_step']}")
