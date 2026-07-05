# Real Covalent Confirmed Candidate Ligand Topology Smoke Current CYS Goldens v0 Summary

Step 13O is a ligand topology smoke for the current CYS/SG golden samples only.
Topology evidence is limited to Step 8 manual-reviewed pre-reaction provenance or existing graph preview.
This step did not automatically restore ligands.
This step did not read, generate, modify, or copy SDF files.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not generalize to non-CYS residue classes or unknown warheads.
This step did not write sample_index, enriched_sample_index, final_dataset, or model input.
This step did not run forward, loss, backward, optimizer, trainer, checkpoint, model save, or tensor dump.
This step did not train.
The topology smoke is blocked because existing Step 8 evidence lacks per-atom and per-bond topology evidence.
This is an expected-blocked diagnostic artifact. The script passes only because the missing topology evidence was correctly detected; ligand topology smoke itself did not pass.
Feature semantics audit is still required before formal training.
The next step is to locate or export Step 8 per-bond topology evidence, not training.

Recommended next step: `locate_or_export_step8_per_bond_topology_evidence`.
