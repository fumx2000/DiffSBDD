# CovaPIE real-provider export blocking-row quarantine materialization V1

This step materializes a metadata-only, fail-closed quarantine registry for the
11 real-provider export rows frozen by the predecessor policy audit. The
quarantine scope is exactly `real_provider_export_ingestion_path_only`.

The stable projection maps `REAL_LOCATOR_BINDING_000001` through
`REAL_LOCATOR_BINDING_000011` one-to-one, in predecessor order, to
`REAL_PROVIDER_EXPORT_QUARANTINE_000001` through
`REAL_PROVIDER_EXPORT_QUARANTINE_000011`. Every row remains
`unknown` with an empty insertion-code value, retains its provider provenance
and `ADMIT_004=blocked` result, and is marked
`active_pending_provider_reexport`.

Quarantine registry validity requires an exact full-field projection across all
33 `QUARANTINE_COLUMNS` fields. Generation and validation share one canonical
expected-row helper; identity, PDB/ligand/residue values, insertion state and
code, ADMIT_004 result and reason, quarantine reason, source locator,
provenance, memberships, schema order, and exact field types must all match.
Validation is not limited to an ID/provenance/membership subset.

Each quarantine row is excluded from exactly five forward-looking scopes:
the provider-admitted candidate set, the provider-export passed set, future
provider-derived canonical materialization input, tensorization input, and
training input. The resulting exclusion matrix has 55 rows. It has no
exception scope. Every exclusion row must exactly match all 10
`EXCLUSION_COLUMNS` fields produced by the shared expected-row helper,
including the normalized exclusion reason, schema order, and exact string
types.

The original provider sidecar, provider integration overlay and evidence,
current `final_dataset_index.csv`, current canonical sample artifacts, and
atom-pair validation artifacts remain byte-identical to BASE. The quarantine
does not retroactively invalidate the current 11 canonical samples. It neither
corrects insertion-code values nor treats an empty value as proof of no
insertion code.

The executable 36-case failure matrix covers predecessor drift, incomplete or
duplicated identities, provider-source drift, ADMIT_004 mismatches, incomplete
quarantine/exclusion evidence, attempted membership admission, attempted
provider/final-dataset mutation, issue regression, and premature training
readiness. Seven projection-specific cases additionally tamper provider-export
identity, PDB/ligand, residue, insertion-code, ADMIT_004, quarantine reason, and
exclusion reason fields. Each case reports the actual validity of its candidate quarantine
and exclusion registries. Missing or duplicate quarantine rows invalidate both
registries; a missing exclusion leaves the quarantine registry valid while
invalidating the exclusion registry. Regardless of whether either candidate
registry remains structurally complete, every invalid case rejects the
provider transition, leaves the effective provider issue `open`, and cannot
enter feature-semantics readiness.

With exact 11/11 quarantine rows, exact 55/55 exclusions, complete failure
evidence, and unchanged provider values, the training-preparation blocking
effect is contained. The predecessor provider issue remains `open` throughout
core validation. Only after core evidence and all 36 failure observations pass
does the implementation apply the successor transition. Therefore
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` transitions to effective
`resolved` solely by the four successor fields. This does not mean provider
values were corrected or provider coverage became complete:

- `provider_blocking_effect_contained=true`
- `provider_issue_resolved=true`
- `provider_values_resolved=false`
- `provider_reexport_still_required=true`
- `provider_coverage_complete=false`

`COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED` remains resolved and unchanged.
The effective-open issue set is empty. The next authorized step is
`audit_covapie_final_training_feature_semantics_and_unknown_atom_policy_v1`.
That step remains a prerequisite audit: feature semantics are still unknown,
the historical Step12D smoke legality check is not a final training-feature
contract, the unknown-atom feature policy remains unresolved, tensorization is
not ready, and training is not ready.
