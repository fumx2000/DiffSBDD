# CovaPIE Final Dataset Materialization Smoke v0

Step 14AR-R4a independently validates relative, repository, allowed-derived-root,
and raw-root artifact path boundaries. Its final safety evidence is derived from
the exact two planned metadata writes, dynamic read/write/readiness state, exact
canonical mask name/alias pairs, and an after-write check of all 11 regular files.

Step 14AR-R4b writes a deterministic final manifest and closes the exact 12-node
metadata-output gate. The manifest records all 12 ordered Step 14AQ source hashes
and the hashes of the preceding 11 outputs; it intentionally does not record its
own hash. The final gate is ready for `covapie_final_dataset_qa_gate_v0`, while
`ready_for_training` and `ready_to_train_now` remain false. Feature-semantics audit
remains mandatory before formal training, fine-tuning, or parameter updates;
Step 12D smoke does not finalize those semantics. Bulk data acquisition design is
only considered after the final-dataset QA gate. No training or model update occurs.

Step 14AR-R2 builds and validates the final-dataset core in memory from the twelve
Step 14AQ derived inputs. Step 14AR-R3a then atomically materializes only the core
metadata outputs: the 23-row precondition audit, 11-row final-index CSV, 11-row
final-index JSON, and 11-row membership CSV. Each output is reread and strictly
validated; CSV and JSON typed rows must agree exactly.

Step 14AR-R3b1 atomically materializes the 66-row artifact-reference inventory,
33-row canonical schema audit, and 11-row source-preservation audit. It revalidates
the R3a core outputs before writing and records its own three-write, three-read
activity separately. Referenced artifacts are neither copied nor rehashed during
this disk materialization.

Source-preservation evidence is independently derived: 33-field preservation uses
only source/final index rows; split and group preservation use their respective AQ
assignment evidence; artifact-reference consistency is separate from artifact file
metadata validity. This keeps a failure in one evidence class from changing the
truth value of an unrelated class.

Step 14AR-R4a securely preflights all nine prior metadata outputs before writing a
55-row final safety audit and the issue inventory. The normal issue inventory is a
single no-issues sentinel; failed preflight or safety evidence produces sorted,
deduplicated blocking issue rows instead. Existing output nodes must be regular
files and cannot be symlinks, directories, missing paths, raw paths, or paths
outside the frozen output root. The manifest remains unwritten until R4b.

The validated membership, artifact-inventory, and split-summary rows are explicitly
projected to their frozen schemas. Membership consistency requires exactly one
source sample row, source group row, and final-index row. Artifact existence and
regular-file status are independently recorded, and only existing non-empty
derived regular files are hashed. Integrity observations are recomputed from the
validated rows and source manifest; the integrity validator rechecks the frozen
expected value, observed value, pass flag, and blocking reason for every item.

Artifact verification is limited to safe derived regular files: existence, regular
file status, size, and streaming SHA256. Raw files, raw directories, mmCIF/CCD,
network access, tensors, dataloaders, model execution, and training are excluded.
The five canonical masks, including scaffold_only/B3, are unchanged.

Artifact file access is authorized only after the path is relative, traversal-free,
inside the repository, resolved inside `data/derived/covalent_small`, and outside
the raw-data root. Repository-local paths outside the allowed derived root,
including symlink escapes, are blocked without existence checks or reads.

R3a does not copy artifacts or write the artifact inventory, schema/source
preservation audits, split summary, integrity audit, issue inventory, safety audit,
manifest, split assignment, leakage matrix, tensor, dataloader, or training
artifact. R3b1 writes the three stated reference/audit CSVs, R3b2 writes split and
integrity audits, and R4a writes issue and safety audits. The manifest remains
unwritten. Formal training remains blocked pending feature-semantics audit and
later gates.
