# CovaPIE cumulative1000 readiness census with 1N0 V1

This additive successor freezes the published with-I12 census as its unique
predecessor, rebuilds the published 1N0 event task-label matrix through the
1N0 ingestion owner, and consumes the published with-1N0 reconciliation owner.
It never reads the rich formal decision directly. It deep-copies all 1,000
predecessor rows and overlays only ranks 775, 776, 778, and 780 in review unit
`COVAPIE_BULK_REVIEW_UNIT_80FE8023FD901B01`.

The schema remains the predecessor Exact47. Every target changes the same
Exact9 fields: global and review status, human completion and provenance,
chemistry disposition provenance, task-relevance disposition provenance, and
training-use disposition. The rows become `COMPLETED_HUMAN_NEGATIVE`,
`NOT_RELEVANT`, `NOT_ESTABLISHED`, and `NOT_APPLICABLE`.
`NOT_ESTABLISHED` is disposition provenance, not positive or negative
chemistry authority. Positive provenance remains empty.

Ranks 777 and 779 are mandatory whole-row negative controls. They belong to
`COVAPIE_BULK_REVIEW_UNIT_D60E67E860A87B24` and remain field-for-field
identical to the predecessor. An overlay selected by ligand component alone is
therefore forbidden. All other 996 rows are also predecessor-identical.

The refreshed global counts are 211 currently unreviewed and 58 completed human
negative. Chemistry is 116 positive, 90 not established, and 794 unresolved.
Task relevance is 117 relevant, 90 not relevant, and 793 unresolved. Training
use is 48 include, 68 training-only exclude, 90 not applicable, and 794
unresolved. Human review contains 127 completed events in 19 units: 99 positive
in 14 units and 28 negative in 5 units. There are 211 unreviewed events in 112
units.

No pair, role, mask, geometry-training, split, admission, or reusable chemistry
authority is added. Pair and role authoritative populations remain 116.
Canonical applicability remains A=116, B=52, B2=52, B3=116, and C=116. The
canonical task contract remains exactly `warhead_only`,
`linker_plus_warhead`, `scaffold_plus_warhead`, `scaffold_only`, and
`scaffold_plus_linker_plus_warhead`; B3 is present and no sixth task exists.

The frozen priority queue is read but never refreshed. With the completed 1N0
review unit removed from pending, current pending rank 1 is raw priority rank 19,
`COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A`, ligand CER, with four events.
The separate 1N0/C2 review unit remains pending.

Six additive semantic bindings extend the 114 predecessor bindings to 120:
the with-I12 owner, census, and summary, plus the 1N0 reconciliation owner,
ingestion owner, and event task-label matrix. The with-I12 manifest is a
separate validation binding and is not counted in the semantic Exact6.
Bindings use content identity and executable class through source-binding V2;
numeric POSIX mode is not semantic identity.

Exact3 materialization is deterministic UTF-8/LF text without timestamps,
machine paths, or manifest self-hash circularity. The checker supports an
untracked Exact7 candidate on the frozen baseline and any later tracked-clean
descendant for which that baseline remains an ancestor. It deliberately does
not require a one-commit publication shape or a permanently fixed count of
later repository paths.

No queue successor, tensorization, loader or model change, loss, backward pass,
optimizer, parameter update, training, commit, or push is performed. Feature
semantics still require a later audit; Step12D remains a smoke legality check,
not a final training-feature contract. `READY_FOR_TRAINING=false`.
