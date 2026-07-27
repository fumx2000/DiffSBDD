# CovaPIE covalent-bond atom-pair current-semantics audit V1

## Decision

The audit outcome is `audited`. This means that the current committed
representation, lineage, and consumers are internally consistent enough to
begin a separate encoding-contract design step. It does not resolve
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED`, complete the feature-semantics
audit, or make the dataset ready for training.

The next step is
`design_covapie_covalent_bond_atom_pair_encoding_contract_v1`.

## Current source of truth and representation

The current materialized source of truth is
`data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv`,
whose 11 rows are covered by the committed final-dataset V1 QA lineage.

The 11 current events contain seven observed string values:

`SG--CAG`, `SG--C2`, `SG--CM`, `SG--C22`, `SG--C17`, `SG--C21`, and
`SG--C6`.

Every event has one non-empty pair. Every stored value equals the value
reconstructed from its separate residue and ligand atom-name fields. There
are no conflicting event identities or pair values. Repeated serialized
values occur across distinct events: four rows are repeats beyond the first
occurrence of their value.

The observed representation is an atom-name metadata string. Its visible
delimiter is `--`, and its visible order is residue atom name followed by
ligand atom name. It is not an atom-table index pair or a tensor. These
observations describe only the current Cys-SG evidence and are not a future
canonical generic encoding contract.

## Source lineage and explicit-bond authority

The 15-row lineage inventory is executable evidence, not an existence-only
file list. Every row records the selector that was actually run, its expected
and observed record counts, the predecessor and observed projection, the
projection comparison result, and the observed explicit-bond authority.

The original ready-candidate selector returns exactly three stable events and
the expansion crosscheck selector returns exactly eight
`confirmed_unique_exact_match` events. For all 11 producer rows, the atom pair
is rebuilt from separate residue and ligand atom fields and the explicit
`_struct_conn` authority is observed. All actual event-table and pair-table
paths referenced by those records are read and compared; no representative
single-row shortcut is used.

The original and expansion sample indexes contain 3 and 8 matching
projections respectively. Their unified index contains the same 11 events,
the three split files form a disjoint 11-event partition, and the final
dataset contains the same 11 event-to-pair mappings. Final-dataset QA,
feature-semantics, tensorization-blocker, and model-input-design selectors are
also executed. The model-input-design check is limited to static selector and
AST evidence and does not run model, dataloader, forward, or loss code.

Distances are retained as corroborating metadata. They are not used as a
substitute producer for the pair label. Every current row retains a
`conn_id`, `conn_type_id=covale`, a validated event source containing
`struct_conn`, and a pair-table validation status derived from explicit bond
and atom-site evidence.

The later feature-semantics and tensorization artifacts consume status only:
the feature audit remains required, and pair tensorization remains blocked.

Producer projection conflicts and final-record conflicts are evaluated
separately. Producer conflict compares each real producer event, atoms, pair,
connection identity, and explicit-bond authority against every downstream
projection. Final-record conflict checks whether one final event identity has
multiple pair values. Both are currently false, and the projection mismatch
reason list is empty.

## Distinct field semantics

`covalent_bond_atom_pair` is the actual current atom-name-pair metadata
value. `residue_atom_name` and `ligand_atom_name` are the separate names in
event/pair artifacts. `covalent_residue_atom_name` and
`ligand_covalent_atom_name` are their sample/final-dataset projections.

`ligand_residue_atom_pair_label_status` is status metadata, not the label
value. `ligand_residue_atom_pair_table_path` and
`covalent_event_table_path` are artifact references, not labels.
`ligand_residue_atom_pair_count` is cardinality metadata.
`post_covalent_bond_distance_angstrom` and related distance fields are
geometry metadata and do not provide explicit-bond authority.

## Downstream consumers

The BASE-level repository search classified 2,472 file/term references:

- 550 materializers
- 460 schema declarations
- 285 reports or manifests
- 271 validators
- 230 test-only references
- 196 status declarations
- 192 semantic transformers
- 142 QA gates
- 73 documentation-only references
- 35 path references
- 36 producers
- 2 tensorization blockers

There are no current matches in `equivariant_diffusion/`,
`lightning_modules.py`, or `dataset.py` for the audited pair/value/status/path
fields. No current reference maps the pair to protein or ligand atom-table
indices, creates a pair tensor, uses it in collate, consumes it in model
forward or loss, or uses it as a training target. Tests, reports, schemas,
and design references are not counted as model consumers.

The audit-decision booleans are derived from the materialized lineage,
representation, consumer, unresolved-semantics, and negative-search evidence.
They are not fixed success inputs. Missing selectors, count drift, missing or
duplicate events, split overlap, pair mismatch, lost explicit authority,
producer conflicts, final-record conflicts, or a newly discovered model
consumer all fail the audit closed.

## Deferred semantics

The Exact24 unresolved-semantics inventory covers ordering, serialization,
escaping, atom identity namespaces and locator context, altloc/model
identity, ligand identity, three atom-table mappings, row-order stability,
index base, cardinality, duplicates, conflicts, invalid labels,
directionality, Cys-SG compatibility, tensor shape, label/loss masks,
negative pairs, the future pair-head interface, and checkpoint
compatibility.

Every future encoding choice records
`decision_made_current_audit=false` and
`deferred_to_next_contract=true`.

## Continuity and safety

The inherited 30-row issue inventory is byte-identical with SHA256
`fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7`.
The effective-open issues remain exactly
`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` and
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT`; no issue changed status.

The five canonical masks remain
`warhead_only/A`, `linker_plus_warhead/B`,
`scaffold_plus_warhead/B2`, `scaffold_only/B3`, and
`scaffold_plus_linker_plus_warhead/C`.

This audit used no provider, network acquisition, download, raw read or
write, checkpoint, model/dataloader/forward/loss change, backward pass,
optimizer, parameter update, or training. The historical
`UNKNOWN_ATOM_FEATURE_POLICY` remains unresolved,
`feature_semantics_known=false`, and `ready_for_training=false`.
