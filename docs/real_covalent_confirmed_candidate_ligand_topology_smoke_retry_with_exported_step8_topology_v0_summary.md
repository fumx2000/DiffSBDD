# Real Covalent Confirmed Candidate Ligand Topology Smoke Retry With Exported Step 8 Topology v0 Summary

Step 13R consumes Step 13Q exported topology evidence tables only.
It does not run RDKit and does not read SDF.
It promotes exported evidence into current CYS/SG golden topology smoke tables.
The promoted tables are not model input and are not training data.
No sample_index, enriched_sample_index, final_dataset, split, leakage matrix, or model input was written.
No forward, loss, backward, optimizer step, trainer fit, checkpoint save, model save, or tensor dump was run.
`ready_for_sample_index_design_gate=true` only means the next design gate may begin.
`ready_to_write_sample_index_now` remains `false`.
`ready_to_train_now` remains `false`.
Feature semantics audit remains required before formal training.

atom smoke table rows: `104`
bond smoke table rows: `113`
cross_boundary_or_unassigned_bond_count: `7`
ready_for_sample_index_design_gate: `True`
ready_to_write_sample_index_now: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_sample_index_design_gate`
