# Real Covalent Confirmed Candidate Ligand Topology Restoration Policy Design Gate v0 Summary

Step 13M is a ligand topology plus restoration policy design gate.
V1 can be CYS-only, but the ligand observed topology schema is residue-agnostic and does not hard-code CYS as the only semantic shape.
The current 3 candidates are CYS/SG golden smoke samples.
Step 8 already performed pre-reaction SDF manual review, graph preview, and packaging QA for this sample family.
This step acknowledges Step 8 manual review history; Step 8 artifact found is True.
This step did not restore ligands again, did not generate SDF, did not modify SDF, and did not run RDKit.
Observed ligand topology and pre-reaction restoration are separate contracts.
The pre-reaction restoration rule is residue-warhead-specific.
The CYS-acrylamide-like restoration rule is not generalized to other residues or other warheads.
Unknown residue-warhead pairs must be quarantined.
New residue-warhead classes require manual visual review before any restoration rule can be trusted.
This step did not read raw `.cif.gz`, did not use gzip_open_used, did not decompress raw files, and did not parse mmCIF.
This step did not use Bio.PDB/MMCIFParser/PDBParser/gemmi/RDKit.
This step did not write ligand_topology_table, sample_index, final_dataset, or model input.
This step did not train and did not save checkpoint, model, or tensor dump.
Feature semantics audit is still required before formal training.
The next step is topology policy review or design refinement, not training.
