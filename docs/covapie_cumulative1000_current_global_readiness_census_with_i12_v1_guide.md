# CovaPIE cumulative1000 readiness census with I12 V1

This additive successor freezes the published 2A2 census as its unique
predecessor, rebuilds the published I12 event matrix through the I12 ingestion
owner, and consumes the published I12 reconciliation result. It deep-copies
all 1,000 predecessor rows and overlays only the four I12 events at ranks 187,
188, 222, and 223. The other 996 rows remain field-for-field equal.

The schema remains the predecessor Exact47. Every I12 row changes the same
Exact18 fields: global and review status, human/chemistry/relevance provenance,
training disposition, pair and role authority, role profile and task
applicability, inclusion and future-candidate flags, current-source
materialization permission, and positive provenance. `human_training_excluded`
remains false and therefore is not part of the delta.

Published I12 authority establishes `RELEVANT`, `POSITIVE`, SG-C21,
`DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`, applicable task IDs `[0,3,4]`, and
`INCLUDE`. The four rows become future admission candidates, but they are not
training admissions. Pair targets, PRE/POST training authority, split
authority, formal admission, and runtime usability remain false. The canonical
contract remains exactly A, B, B2, B3, and C; B3 is present and no sixth task
exists.

The refreshed counts are 116 chemistry positives, 117 relevant events, 48
training includes, 68 training exclusions, 31 future candidates, 116 pair and
role authoritative samples, and role profiles 52 strict plus 64 direct.
Applicable authoritative-role counts are A=116, B=52, B2=52, B3=116, and
C=116. Human review is 99 positive events in 14 units, 24 negative events in
4 units, and 215 unreviewed events in 113 units.

The frozen priority queue is read but never refreshed. After completed I12 is
removed from pending units, rank 1 is
`COVAPIE_BULK_REVIEW_UNIT_80FE8023FD901B01` for ligand 1N0, with immutable raw
priority rank 18 and four events across 4JWS, 4JWU, and 4JX1.

The six additive semantic bindings use path, namespace, byte count, SHA256,
and executable class through the V2 source-binding gate. They extend 108 frozen
predecessor bindings to 114 without collision or numeric POSIX mode identity;
no separate cleanup successor is needed.

Materialization accepts only an absent, empty, partial-valid, or complete-valid
Exact3 destination. Before any directory creation, temporary file, write, or
replacement, it rejects a root symlink, any unexpected entry or directory, and
any allowed output name that is not a regular non-symlink file. Repeated Exact3
materialization is byte-identical.

The checker supports only `CANDIDATE_UNTRACKED` and `TRACKED_CLEAN`, runs the
B4 production core directly, and verifies the full source-derived census,
summary, manifest, queue, lifecycle, and pre-write boundary. It does not use a
historical publication wrapper.

No queue successor, training artifact, split, tensor, optimizer step, parameter
update, training, commit, or push is created. Feature semantics still require a
later audit; Step12D was a smoke legality check, not a final training-feature
contract. `READY_FOR_TRAINING=false`.
