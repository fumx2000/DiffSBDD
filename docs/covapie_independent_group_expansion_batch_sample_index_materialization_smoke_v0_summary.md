# CovaPIE Step 14AN Expansion Batch Sample-Index Materialization Smoke

Step 14AN writes a standalone eight-row expansion batch sample index using the
canonical 33-field schema. The committed Step 14AM preparation outputs provide
all source tables and embedded QA evidence.

The existing three-row pilot index is read only for schema, namespace, collision,
and hash guards. This step does not write a combined index, split assignments,
leakage matrices, a final dataset, dataloader artifacts, or training artifacts.

The index retains dynamic ligand atom names and covalent bond pairs from Step 14AM.
Passing enables batch ligand graph/scaffold and protein accession/sequence
independence evidence materialization only. Training remains blocked pending feature
semantics audit and leakage/split design.
