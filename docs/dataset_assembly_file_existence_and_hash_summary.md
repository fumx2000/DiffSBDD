# Dataset Assembly File Existence and Hash Gate Summary

This is file existence and hash gate only.

- It reads schema-valid candidates.
- It does not modify manifest files.
- It does not modify or generate SDF files.
- It does not generate real training datasets.
- It does not train or fine-tune any model.
- Passing this gate means candidate files are hash-locked for the next preview step.
- Passing this gate does not mean the samples are training-ready.

| candidate_id | source_sample_id | protein_pdb_path | protein_pdb_size_bytes | protein_pdb_sha256 | ligand_sdf_path | ligand_sdf_size_bytes | ligand_sdf_sha256 | file_existence_and_hash_gate_status | hash_locked_candidate_written | training_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9_pre_reaction | BTK_C481_6DI9 | data/raw/covalent_small/proteins/BTK_C481_6DI9.pdb | 226395 | d62004ac38434a0cc5846862e03169a132c095e475603e4725058ea04328cf5d | data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf | 2851 | 004ec8e1ccb4552156762180137f092ae745179a2ae7b9ea06ff5632e62eb126 | file_existence_and_hash_gate_passed | true | false | build_dataset_assembly_graph_preview_not_training |
| KRAS_G12C_5F2E_pre_reaction | KRAS_G12C_5F2E | data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb | 308367 | ddfa80d8ca2ae558ce6633702d417ed0ba61514ac2f8506fecf6061311412f78 | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf | 2615 | 4015047b42b77f1f8e785c10eb073fb01d60198245d5e76b1db7db73781eeb9b | file_existence_and_hash_gate_passed | true | false | build_dataset_assembly_graph_preview_not_training |
| KRAS_G12C_6OIM_pre_reaction | KRAS_G12C_6OIM | data/raw/covalent_small/proteins/KRAS_G12C_6OIM.pdb | 173016 | 42deda943440cc8dd3020a2c65ddc260970936d675b47c8b43564195b77d5006 | data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf | 3541 | 09e366d2e8d7b761b23c0e0f8efb86173f9b5815bc84e53d29c8d465c445dfe1 | file_existence_and_hash_gate_passed | true | false | build_dataset_assembly_graph_preview_not_training |

## Global Conclusion

- All three candidates passed file existence and hash gate.
- Hash-locked candidates CSV contains exactly 3 rows: true.
- Manifest was not modified.
- No SDF files were modified or generated.
- No real dataset was generated.
- No training was run.
- Next step is graph preview, not training.
