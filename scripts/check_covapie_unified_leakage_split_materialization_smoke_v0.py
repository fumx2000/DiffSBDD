from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from covalent_ext import covapie_unified_leakage_split_materialization_smoke as smoke
def main()->int:
    m=smoke.run()["manifest"]
    for key in ["unified_sample_count","final_leakage_group_count","selected_assignment_signature","train_sample_count","validation_sample_count","test_sample_count","cross_split_pair_count","within_split_pair_count","leakage_violation_count","recommended_next_step"]:print(f"{key}={m.get(key)}")
    if not m.get("all_checks_passed"):
        print("blocking_reasons="+";".join(m.get("blocking_reasons",[])));return 1
    print("covapie_unified_leakage_split_materialization_smoke_v0_passed");return 0
if __name__=="__main__":raise SystemExit(main())
