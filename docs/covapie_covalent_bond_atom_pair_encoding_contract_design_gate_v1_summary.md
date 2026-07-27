# CovaPIE covalent-bond atom-pair encoding contract design gate V1

## Outcome and scope

The V1 encoding contract is frozen as a metadata-only design. The sole
canonical semantic identity is a `structured_role_labeled_record` containing a
target-residue atom locator, ligand atom locator, explicit-bond authority, and
event/provenance identity. This step does not validate or materialize the 11
current records as structured locators or atom-table indices.

The exact canonical carrier is the frozen
`CovalentBondAtomPairCanonicalRecordDesign`:

1. `pair_record_schema_version: str`
2. `residue_atom_locator: CovalentAtomLocatorContractDesign`
3. `ligand_atom_locator: CovalentAtomLocatorContractDesign`
4. `explicit_bond_authority_class: str`
5. `explicit_bond_provenance_id: str`

Its schema version is
`covapie_covalent_bond_atom_pair_canonical_record_v1`. The existing
`CovalentBondAtomPairEncodingContractDesign` remains the policy/readiness
contract and is not the canonical pair record.

The current `residue_atom_name--ligand_atom_name` value remains only a
`legacy_display_and_backward_compatibility_projection`. It must agree with the
structured atom names, but it cannot serve as the sole locator, canonical
identity, or tensor target.

`project_covapie_legacy_atom_name_pair_v1` accepts only a canonical record that
passes the exact validator, then emits
`residue_atom_locator.atom_name--ligand_atom_locator.atom_name`. It never parses
a legacy string to recover semantic identity. The seven compatibility rows are
generated from structured name-level fixtures built from the committed
current-representation audit.

## Frozen locator and authority rules

`CovalentAtomLocatorContractDesign` uses schema
`covapie_covalent_atom_locator_v1` and exact string fields. The only roles are
`target_residue_atom` and `ligand_atom`. `event_id`, `pdb_id`, `entity_role`,
`comp_id`, and `atom_name` are non-empty; an empty string is the only V1
missing sentinel for allowed missing fields. `None`, coercion, nearest-atom
selection, and unresolved model, insertion-code, or altloc ambiguity are
invalid.

Locator syntactic validity is not successful atom-table mapping. An empty
optional field means only that the current semantic record has no available
value; it does not prove confirmed absence, uniqueness, or lack of ambiguity.
Future mapping validation must still match exactly one row or fail closed.

Positive pairs require exactly one of:

- `validated_struct_conn`
- `explicit_curated_covalent_annotation`

Distance, nearest-atom geometry, docking proximity, model prediction, or a
legacy string without provenance cannot independently create a positive pair.

## Cardinality and future mapping

V1 supports exactly one positive explicit pair per sample. Zero pairs,
multiple distinct pairs, conflicts, missing locators, and ambiguous mappings
fail closed. Exact duplicate evidence may be deduplicated only when every
identity and authority field matches.

Future derived model-facing indices are zero-based
`pocket_atom_table_row_index` and `ligand_atom_table_row_index` values. The
semantic locator remains authoritative; a row index is only a derived view
after exactly-one matching and row-order validation. Full-protein mapping may
be used for trace or QA, not as the V1 model-facing target.

Compatibility is independently derived from committed BASE evidence:

- final-dataset schema and 11 materialized metadata records contain nonempty
  pocket and ligand atom-table path references;
- the current atom-pair audit records no tensor-index pair, mapping,
  dataloader, forward, loss, or training target;
- the unresolved-semantics inventory defers locator-to-row mapping and
  row-order validation;
- the tensorization audit blocks the pair label, collate, loss, and training
  targets;
- the actual-dataloader design preserves pocket/ligand artifact boundaries and
  contains no conflicting pair-index contract.

Thus compatibility means only that no conflicting existing pair-index contract
was found and the selected future spaces fit the current artifact boundaries.
It does not mean the 11 rows have been mapped.

## Mask and implementation boundaries

The five canonical semantic masks—`warhead_only`,
`linker_plus_warhead`, `scaffold_plus_warhead`, `scaffold_only`, and
`scaffold_plus_linker_plus_warhead`—share the same structured pair identity.
Aliases A, B, B2, B3, and C are display-only. B3 warhead retention does not
change pair identity; auxiliary-loss activation remains deferred.

No pair tensor, tensor shape, negative construction, loss mask, pair head,
contrastive loss, dataloader/collate change, model/forward/loss change, raw
read, provider access, checkpoint access, or training occurs here.

## Readiness

- `encoding_contract_frozen=true`
- `canonical_pair_record_schema_frozen=true`
- `model_input_index_space_compatibility_derived_from_committed_evidence=true`
- `model_input_index_space_compatibility_verified=true`
- `encoding_contract_validation_completed=false`
- `atom_pair_issue_resolved=false`
- `ready_for_contract_validation=true`
- `ready_for_tensorization=false`
- `feature_semantics_audit_completed=false`
- `ready_for_training=false`

The required pre-training feature-semantics audit remains open, including
historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=false`. Step12D remains only a smoke legality check,
not a final training-feature contract.

Recommended next step:
`validate_covapie_covalent_bond_atom_pair_encoding_contract_against_current_canonical_evidence_v1`.
