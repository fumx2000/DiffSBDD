# CovaPIE CYS/SG Ligand Covale Annotation Alignment Gate v0 Summary

Step 14J aligns the Step 14I ligand covale candidates against the local CovPDB manual metadata CSV.
It does not use network access, download files, read raw CIF content, create ready candidates, create sample/final/split/leakage artifacts, instantiate a dataloader, or train.

input_ligand_covale_candidate_count: `9`
annotation_alignment_candidate_count: `9`
metadata_pdb_match_count: `9`
metadata_ligand_or_het_alignment_count: `9`
metadata_event_annotation_gap_count: `9`
metadata_conflict_count: `0`
all_annotation_alignment_candidates_pending_manual_review: `True`
ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20: `True`
ready_for_training: `False`
recommended_next_step: `covapie_cys_sg_targeted_metadata_expansion_gate`

PDB ID and CovPDB ligand IDs remain context fields, not event identity. Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
