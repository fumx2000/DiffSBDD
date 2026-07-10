import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from covalent_ext.covapie_independent_group_expansion_batch_sample_index_materialization_smoke import run

if __name__=='__main__':
    m=run()['manifest']
    if not m['all_checks_passed']: raise SystemExit('covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0_failed')
    for key in ['existing_sample_index_row_count','expansion_batch_sample_index_row_count','schema_validation_passed_count','schema_validation_count','row_traceability_passed_count','row_traceability_count','collision_audit_passed_count','collision_audit_count','materialization_issue_count','future_combined_sample_count','recommended_next_step']: print(f'{key}={m[key]}')
    print('covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0_passed')
