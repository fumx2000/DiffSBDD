# CovaPIE Real Locator Pipeline Integration Design Gate v1

## Scope

Step14AU-E0-P6-A freezes a metadata-only design for connecting the validated
P5-B raw-preserving parser adapter and the P4 provider to the 11 existing real
samples. It does not open, stat, hash, or traverse ignored raw structures and
does not execute a real provider export.

P5-B already proves that the additive adapter works for 16 synthetic cases and
preserves a 33-column synthetic sidecar. This gate joins existing committed
metadata into an exact 11-row binding matrix: three historical samples followed
by eight expansion samples in shortlist-rank order.

Historical binding order is controlled by the original sample-index row order,
not by execution-manifest order. Each historical row obtains its raw path from
the execution manifest and must prove exact three-way ligand identity across
`execution.expected_het_id`, `sample_index.expected_het_id`, and
`sample_index.ligand_comp_id`. Execution ID, PDB ID, artifact root, execution
status, and sample-index status must also agree exactly.

## Frozen Architecture

The sole architecture is `ADDITIVE_EXTERNAL_REAL_EXPORT_EXECUTOR`. A future
outer executor will validate an exact raw relative path and a frozen SHA256,
provide raw bytes or text to the P5-B parser, select the expected `struct_conn`
event, re-establish partner-side and auth/label namespace evidence, bind one
atom-site row, preserve insertion tags and raw tokens, and then call the P4
provider.

The historical and expansion parsers remain unchanged. Existing event tables,
pair tables, sample-index rows, and admission records are not overwritten. The
admission evaluator and P4 provider do not open raw files, and distance is not
accepted as evidence for partner side or insertion semantics.

## Binding And Raw Boundary

All 11 bindings carry persisted metadata references for raw path, `conn_id`,
residue hints, and event/pair tables. A persisted path is not evidence that its
target has been read or validated. No raw SHA256 is frozen here, so every row is
blocked by `REAL_RAW_SOURCE_SHA256_PRECONDITION_NOT_YET_FROZEN` and real export
is disallowed.

Metadata identity validation and raw-source validation are separate layers. An
identity or status mismatch is reported as `REAL_SAMPLE_METADATA_JOIN_FAILED`;
it is never mislabeled as a missing raw SHA256 precondition. Path checks are
lexical only and require the raw root, structure suffix, derived artifact root,
exact table filenames, and matching artifact parents without opening targets.

The next step must therefore be a dedicated raw-source precondition gate. It
must freeze the expected SHA256 before any real parser/provider executor may
run. Partner side, namespace, matched atom-site row, and insertion evidence must
still be proved from raw source material in that future controlled execution.

## Future Interface

The future executor accepts one binding row at a time using 13 exact input
fields, including `expected_raw_sha256`. Its results remain layered so that a
raw-source failure cannot be misreported as an insertion failure.

The future real sidecar has 41 columns and an expected 11 rows. Eight execution
and raw-precondition fields precede the frozen P5-B 33-column schema. It stores
no raw contents, absolute paths, timestamps, or nested JSON. Success, blocking,
and rejection remain distinct. The sidecar requires separate QA and does not
automatically merge into the 22-field admission schema.

The 33-column suffix is bound to the actual committed P5-B synthetic-sidecar
CSV header in its original order; it is not accepted merely because a separate
handwritten tuple has the same length. The complete 41-column proposal is the
eight fixed execution fields followed by that independently read header.

Each expansion binding also requires exact preparation status, embedded-QA
status, one event, one ligand-residue pair, and agreement between the persisted
bond pair and selected ligand atom. A failure remains as a failed metadata row
rather than disappearing from the batch. This metadata-readiness failure is
distinct from the later raw SHA256 precondition. No real raw execution occurs
in this gate.

## Readiness

The design is ready only for the raw-source precondition gate. The real executor
is not implemented, no real provider row is materialized, and none of the 11
samples is backfilled. All 11 insertion states remain unknown and zero insertion
absences are proven. The atom-name normalization blocker remains independent;
ADMIT_004 and E1 are not ready.

The canonical masks remain exactly:

- `warhead_only / A`
- `linker_plus_warhead / B`
- `scaffold_plus_warhead / B2`
- `scaffold_only / B3`
- `scaffold_plus_linker_plus_warhead / C`

Candidate evaluation, bulk download, model execution, and training remain
disallowed. A feature-semantics audit is still required before formal training,
fine-tuning, or real parameter updates.
