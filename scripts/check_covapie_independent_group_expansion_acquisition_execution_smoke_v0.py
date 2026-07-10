#!/usr/bin/env python
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'src'
if str(SRC) not in sys.path:sys.path.insert(0,str(SRC))
from covalent_ext import covapie_independent_group_expansion_acquisition_execution_smoke as gate
def write(rows,path,fields):
 out=ROOT/path;out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='',encoding='utf-8') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows([{f:r.get(f,'') for f in fields} for r in rows])
def main():
 args=argparse.ArgumentParser();args.add_argument('--execute-network',action='store_true');flag=args.parse_args().execute_network
 r=gate.run(flag)
 if flag:
  for rows,path,fields in [(r['pre'],gate.PRE,gate.PRE_COLUMNS),(r['download'],gate.DOWNLOAD,gate.DOWNLOAD_COLUMNS),(r['integrity'],gate.INTEGRITY,gate.INTEGRITY_COLUMNS),(r['failures'],gate.FAILURES,gate.FAIL_COLUMNS),(r['safety'],gate.SAFETY,gate.SAFETY_COLUMNS)]:write(rows,path,fields)
  (ROOT/gate.MANIFEST).write_text(json.dumps(r['manifest'],indent=2)+'\n')
  m=r['manifest'];(ROOT/gate.SUMMARY).write_text(f"# CovaPIE Independent Group Expansion Acquisition Execution Smoke v0\n\nStep 14AK downloaded or reused the approved raw mmCIF batch without struct_conn parsing, atom-site extraction, grouping confirmation, or training.\n\n- acquisition_succeeded_count: `{m['acquisition_succeeded_count']}`\n- raw_integrity_passed_count: `{m['raw_integrity_passed_count']}`\n- recommended_next_step: `{m['recommended_next_step']}`\n")
 m=r['manifest'];print('covapie_independent_group_expansion_acquisition_execution_smoke_v0_passed' if m['all_checks_passed'] else 'covapie_independent_group_expansion_acquisition_execution_smoke_v0_blocked');print(f"acquisition_candidate_count={m['acquisition_candidate_count']}");print(f"acquisition_succeeded_count={m['acquisition_succeeded_count']}");print(f"acquisition_failed_count={m['acquisition_failed_count']}");print(f"raw_integrity_passed_count={m['raw_integrity_passed_count']}");print(f"batch_complete={m['batch_complete']}");print(f"recommended_next_step={m['recommended_next_step']}");return 0 if m['all_checks_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
