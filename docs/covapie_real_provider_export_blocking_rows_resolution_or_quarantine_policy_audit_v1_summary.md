# CovaPIE real-provider export blocking-row policy audit V1

This metadata-only audit is bound to commit
`e5563ed50db6e56cbdfb6cc629e5eb4fe9137edf`. It dynamically selects the 11
`exported_blocking` rows from the committed real-provider export sidecar and
joins them by `binding_row_id` to the committed candidate binding matrix,
execution evidence, integration overlay, and downstream integration audit.
No `data/raw` reference is dereferenced.

The committed ADMIT_004 insertion-code state vocabulary is exactly `absent`,
`present`, and `unknown`. `absent` requires an empty value and is the only
state for which an empty value explicitly means no insertion code. `unknown`
also requires an empty value for schema validity, but that empty value means
unknown/unprovided/unparseable provenance and ADMIT_004 blocks it.
`present` requires a nonempty value satisfying the committed grammar and the
additional evidence-context attestations. Unsupported states, `present` plus
empty, and `absent`/`unknown` plus nonempty are invalid.

Field presence is a separate evidence dimension from field-value validity.
A missing insertion-code state field or a missing insertion-code value field
is evidence insufficiency and therefore requires fail-closed quarantine
pending provider re-export or curated explicit evidence. In particular,
`absent` with a missing code field must not be defaulted to an empty string.
By contrast, a state field that is present but contains an unsupported value,
or a present state/code pair that contradicts the closed contract, is
invalid/contradictory evidence.

All 11 committed rows contain `unknown` plus an empty value. Their provider
provenance is present and their ADMIT_004 result independently reproduces as
`blocked` with
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`. This proves the block,
not the correct insertion-code value. Consequently the audit disposition is
11 `quarantine_required_pending_provider_reexport`, 0
`explicitly_resolvable_from_committed_evidence`, and 0
`contradictory_or_invalid_committed_evidence`.

The frozen policy preserves every provider row and its provenance. A
quarantine candidate is neither deleted nor changed to passed and cannot
enter the provider-admitted candidate set, canonical dataset materialization,
tensorization, or training. A future quarantine step must wait for an
explicit provider re-export or human-curated explicit evidence. Resolution
candidacy is not issue resolution; this audit performs neither resolution nor
quarantine materialization.

The policy matrix is an executable Exact17 contract. Every CSV row is
generated from the public frozen policy-case evaluator and is checked against
the public row classifier for the applicable cases. Unknown policy case IDs
fail closed as contradictory/invalid; they never default to resolution or
quarantine.

The predecessor 30-row issue inventory is copied byte-for-byte. The atom-pair
issue remains resolved, while
`REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remains the sole effective open
issue. Feature-semantics audit, tensorization, model work, and training remain
not ready. The recommended next step is
`materialize_covapie_real_provider_export_blocking_row_quarantine_v1`.
