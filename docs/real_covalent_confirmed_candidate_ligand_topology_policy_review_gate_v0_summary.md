# Real Covalent Confirmed Candidate Ligand Topology Policy Review Gate v0 Summary

Step 13N is a ligand topology policy review gate.
This step reviewed and accepted the Step 13M CYS-only V1 scope.
The schema remains residue-agnostic.
The restoration rule remains residue-warhead-specific.
Current topology smoke scope is limited to the 3 CYS/SG golden samples.
The topology smoke must not automatically restore ligands again.
The topology smoke must not generalize to non-CYS residue classes.
The topology smoke may use Step 8 manual-reviewed pre-reaction provenance or existing graph preview only.
This step did not read raw `.cif.gz`, did not use gzip_open_used, did not parse mmCIF, and did not run atom_site scan.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not generate SDF, did not modify SDF, and did not write ligand_topology_table.
This step did not write sample_index, final_dataset, split assignments, leakage matrix, or model input.
This step did not run forward, loss, backward, optimizer, trainer, checkpoint, model save, or tensor dump.
This step did not train.
Feature semantics audit is still required before formal training.
The next step can enter current CYS golden samples ligand topology smoke, but it is not training.
