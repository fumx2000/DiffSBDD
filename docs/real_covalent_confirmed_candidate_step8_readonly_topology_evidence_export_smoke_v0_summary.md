# Real Covalent Confirmed Candidate Step 8 Readonly Topology Evidence Export Smoke v0 Summary

Step 13Q is a read-only RDKit topology evidence export smoke.
It only reads the three Step 8 manual-reviewed pre-reaction SDF files listed in the Step 13P candidate contract.
It does not glob extra SDF files and does not read raw `.cif.gz` or parse mmCIF.
It uses RDKit only for read-only SDF topology export.
It does not generate, modify, or copy SDF files.
It does not automatically restore ligands.
It does not generalize the current CYS/SG golden sample scope to non-CYS residues.
It writes exported Step 8 evidence tables, not final ligand topology or training tables.
`ligand_topology_table_written` remains `false`.
No sample_index, final_dataset, or model input was written.
No forward, loss, backward, optimizer step, trainer fit, checkpoint save, model save, or tensor dump was run.
Feature semantics audit is still required before formal training.

atom topology evidence rows: `104`
bond topology evidence rows: `113`
ready_for_ligand_topology_smoke_retry: `True`
ready_for_sample_index_design_gate: `False`
ready_to_train_now: `False`
recommended_next_step: `real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology`
