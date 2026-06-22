# Dataset Assembly Graph Preview Summary

This is graph preview only.

- It reads hash-locked candidates.
- It does not modify manifest files.
- It does not modify or generate SDF files.
- It does not generate real training datasets.
- It does not train or fine-tune any model.
- Passing this preview means candidates can enter final readiness gate.
- Passing this preview does not mean the samples are training-ready.

| candidate_id | ligand_atom_count | ligand_heavy_atom_count | ligand_bond_count | protein_atom_count | protein_residue_count | reactive_residue_found | reactive_atom_found | graph_preview_status | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | 33 | 33 | 35 | 2306 | 473 | true | true | dataset_assembly_graph_preview_passed | false | build_dataset_assembly_final_readiness_gate_not_training |
| KRAS_G12C_5F2E_pre_reaction | 30 | 30 | 33 | 1723 | 353 | true | true | dataset_assembly_graph_preview_passed | false | build_dataset_assembly_final_readiness_gate_not_training |
| KRAS_G12C_6OIM_pre_reaction | 41 | 41 | 45 | 1613 | 377 | true | true | dataset_assembly_graph_preview_passed | false | build_dataset_assembly_final_readiness_gate_not_training |

## Global Conclusion

- All three candidates passed graph preview.
- Graph preview candidates CSV contains exactly 3 rows: true.
- Manifest was not modified.
- No SDF files were modified or generated.
- No real dataset was generated.
- No training was run.
- Next step is final readiness gate, not training.
