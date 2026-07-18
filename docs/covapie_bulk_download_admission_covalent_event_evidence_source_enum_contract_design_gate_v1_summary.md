# CovaPIE covalent-event evidence-source enum contract design gate V1

This normative, metadata-only gate freezes the V1 contract for the candidate
field `covalent_event_evidence_source`. It does not assert that any canonical
member has been observed in committed provider metadata: the observed value
count remains zero.

The ordered Exact3 canonical members are:

1. `explicit_structure_bond_record`
2. `explicit_curated_covalent_annotation`
3. `distance_only_inference`

The field accepts only an exact built-in `str`, without trimming, case folding,
or alias conversion. The syntax is `[a-z][a-z0-9_]{0,63}`, followed by exact
Exact3 membership. Syntactically valid unregistered strings fail closed as
unknown; manual-review and catch-all strings are not V1 members.

The evaluation-context item `allowed_covalent_evidence_classes` is the exact
built-in tuple
`("explicit_structure_bond_record", "explicit_curated_covalent_annotation")`.
No caller variation, reordering, missing/extra member, duplicate, string
subclass, or alternate container is accepted.

ADMIT_006 is the positive explicit-evidence permission rule. The two explicit
members pass; `distance_only_inference` blocks with
`COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT`. The historical design-level reason
`covalent_event_evidence_missing` remains the semantic source for a future
adapter's missing-field and missing-value paths; distance-only is not missing.

ADMIT_007 is the negative distance-only prohibition rule. The two explicit
members pass; `distance_only_inference` blocks with
`DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE`. Malformed/unknown scalar inputs or an
invalid context produce `invalid` for both rules using the shared validation
reason. Cross-rule aggregation, deduplication, and ordering remain unfrozen.

The predecessor Exact11 issue inventory is preserved in order and schema. Only
`COVALENT_EVIDENCE_ENUM_UNRESOLVED` transitions from `open` to `resolved`, with
integration transition
`covalent_event_evidence_source_enum_contract_frozen_v1`; ten active issues
remain. ADMIT_006 remains in incomplete runtime coverage because neither
ADMIT_006 nor ADMIT_007 is implemented or registered.

This gate makes the next standalone ADMIT_006 evaluator-interface step ready,
but does not start it. Real provider mapping, candidate evaluation, bulk
download, and training remain prohibited. A feature-semantics audit remains a
mandatory prerequisite before formal training; the historical Step12D result
was a smoke legality check, not a final training-feature contract.
