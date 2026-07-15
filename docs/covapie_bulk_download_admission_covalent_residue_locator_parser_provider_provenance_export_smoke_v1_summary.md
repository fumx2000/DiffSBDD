# CovaPIE covalent residue locator parser/provider provenance export smoke v1

Step14AU-E0-P5-B adds an independent, synthetic-only adapter for preserving
raw logical mmCIF loop tokens. It does not modify the historical sample
preparation parser or the independent-group expansion parser. A separate
compatibility view converts dot and question markers to the defaults expected
by the historical parser, and the synthetic atom-site and struct-conn fixtures
confirm that tags, rows, and status remain compatible.

The raw view distinguishes dot, question, a missing tag, and a parsed empty
value. It explicitly preserves whether the covalent residue is struct-conn
partner 1 or partner 2, then binds exactly one matching atom-site row. Missing
and multiple matches are rejected rather than guessed. The frozen P4 helpers
produce the five P3 locator provenance fields after namespace, row identity,
and insertion evidence checks.

The 16 fixed cases produce five `exported_pass`, five `exported_blocking`, and
six `rejected` results. Question, missing, parsed-empty, and conflicting
insertion evidence still export complete provenance metadata, but retain an
unknown insertion state and block ADMIT_004. Provider-contract failures are
rejected and contain no P3 provenance fields. A rejection before complete
two-sided insertion resolution leaves the insertion-resolution fields
unavailable rather than claiming an ADMIT_004 result. A later provenance
source-ID rejection preserves an already completed insertion resolution and
records the failure only at the provider-export layer. The resulting 33-column
sidecar is synthetic evidence only; it is neither a real candidate set nor a
backfill of real provider payloads.

Materialization also fails before writing when the requested output root is a
symbolic link or an existing non-directory. Output validation independently
rejects symbolic-link output files and source-hash contract drift.

The 11 existing real samples remain insertion-unknown, and insertion absence
has not been proven for any of them. Real historical and expansion pipeline
integration has not been implemented. ADMIT_004 and E1 remain not ready, and
the residue atom-name semantics blocker remains independent of this smoke.

The canonical mask scope remains exactly:

- `warhead_only / A`
- `linker_plus_warhead / B`
- `scaffold_plus_warhead / B2`
- `scaffold_only / B3`
- `scaffold_plus_linker_plus_warhead / C`

No real candidate evaluation, bulk download, model execution, or training is
authorized. A feature semantics audit is still required before formal
training, fine-tuning, or real parameter updates.
