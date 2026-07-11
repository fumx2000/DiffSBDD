from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from covalent_ext import covapie_unified_independence_group_assignment_and_sample_index_merge_smoke as smoke
def main()->int:
    m=smoke.run()["manifest"]
    for k in ["pilot_sample_count","expansion_sample_count","unified_sample_index_row_count","unified_sample_index_schema_field_count","pairwise_assignment_decision_count","direct_must_link_edge_count","final_leakage_group_count","final_leakage_group_sizes","confirmed_new_independent_group_count_current_step","recommended_next_step"]: print(f"{k}={m[k]}")
    if not m["all_checks_passed"]:
        print("blocking_reasons="+";".join(m["blocking_reasons"])); return 1
    print("covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0_passed"); return 0
if __name__=="__main__": raise SystemExit(main())
