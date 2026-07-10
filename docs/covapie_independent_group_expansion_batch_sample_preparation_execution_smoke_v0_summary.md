# CovaPIE Step 14AM Batch Sample Preparation Execution Smoke

Step 14AM prepares isolated CSV atom/event outputs for the eight Step 14AL
confirmed CYS/SG covalent events.  It reuses the historical pure-text mmCIF
loop parser but dynamically preserves each selected ligand atom in both event
and atom-pair outputs.

The step reads ignored raw mmCIF files locally. It does not use the network,
modify raw files, modify the existing sample index, create splits or a final
dataset, or create training/model artifacts. The five canonical masks remain
unchanged, including `scaffold_only` / `B3`.

Embedded per-sample QA checks raw identity, event revalidation, atom-instance
identity, 8 A pocket selection, and the independently recomputed atom-site
distance. Passing this smoke permits the expansion-batch sample-index
materialization smoke only; it does not make training ready. Feature semantics
and leakage/split design remain required before training.
