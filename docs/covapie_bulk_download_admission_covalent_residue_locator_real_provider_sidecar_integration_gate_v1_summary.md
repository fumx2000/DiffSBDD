# CovaPIE Step14AU-E0-P6-D summary

Step14AU-E0-P6-D performs the value-level integration authorized after the
P6-C real-provider execution smoke. It joins the frozen 11-row P6-C sidecar to
the frozen 11-row P6-A binding identity layer by `binding_row_id`, recomputes
the P4 provider fields and canonical provenance for every row, and writes an
additive six-column integration overlay. It does not add schema fields: P3
already integrated the five locator fields into the effective 22-field
admission schema.

## Frozen source and runtime boundary

The gate freezes exactly 19 committed sources at base commit
`4958f9124dd831cccc3a1a22b981764f279e85d7`: the P2, P3, P4, P6-A, and P6-C
production modules plus the specified P3, P6-A, and P6-C committed outputs.
Every path must be tracked, regular, non-symlink, and match its hard-coded
SHA256. All structural checks finish before the first source-content read;
CSV and JSON parsing then uses those retained bytes. Artifact-reference paths
are never followed.

Only P2 and P4 are requested by the P6-D runtime loader, after predecessor
validation. Their module names, source paths, current bytes, SHA256 values,
and required callables must match the frozen snapshot. Runtime isolation is a
per-call identity-delta contract, not a process-global purity requirement: a
shared test process may already contain P3, P6-A, P6-B, P6-C, or P5-B modules,
but the P6-D loader may not newly import, replace, or delete any of them. Their
pre-call identities must remain unchanged. In a clean subprocess P6-D does not
load them, and P6-D computation never uses their module objects. No parser is
invoked and no raw path is opened, scanned, statted, or hashed.

## Direct predecessor validation

P3 is verified from its five direct CSV outputs plus manifest: the effective
schema remains 22 fields, 15 rules, and 18 contexts. The five locator fields
are candidate-record fields produced by the candidate metadata provider and
consumed only by ADMIT_004. ADMIT_004 retains the original four residue fields,
the five locator fields, and its two unresolved semantics blockers. All ten P3
domain issues remain open and unchanged.

P6-A's 26-column binding matrix remains the target identity layer, not a full
admission candidate record. Its exact order is the historical three bindings
followed by eight expansion bindings. The gate validates unique binding,
sample-preparation, and PDB/ligand identities plus all persisted metadata
status fields without opening sample artifacts.

P6-C is verified from its direct contract, 41x11 sidecar, 11-row execution
evidence, safety audit, issue inventory, and manifest. The predecessor remains
0 exported-pass, 11 exported-blocking, and 0 rejected, with 11 unique source
IDs and provenance hashes. The predecessor merge-pending issue is resolved by
P6-D; `REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT` remains active with count
11.

## Keyed join and provenance recomputation

The only primary join key is `binding_row_id`. Target, sidecar, and evidence
must contain each canonical ID exactly once. Input ordering is not trusted;
the output is always restored to P6-A canonical order. Source pipeline,
sample-preparation ID, execution ID, PDB ID, ligand ID, connection ID, raw-path
metadata, smoke ID, raw SHA, provider status, and residue atom identity are
checked as secondary invariants.

For each joined row, P2 revalidates `unknown` plus an empty insertion value as
a schema-valid but ADMIT_004-blocking combination. P4 then re-resolves locator
namespace evidence, atom-site identity, raw insertion tokens, and insertion
evidence; rebuilds the exact five provider fields and provenance source ID;
and hashes the validated canonical 20-key payload. Every recomputed value must
equal the frozen P6-C sidecar.

## Outputs and readiness

The overlay is exactly 11 rows by six columns: `binding_row_id` followed by the
five P3 locator fields. All namespaces are `auth`; all insertion states are
`unknown`; all insertion values are the legal empty string; and all source IDs
and SHA256 values are valid and unique. Provider status, raw SHA, smoke ID,
matched atom identity, and auth/label conflict evidence remain in the separate
31-column integration evidence audit, not in the candidate-schema overlay.

All 11 rows have `integration_status=integrated_blocking` and retain
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`. The overlay therefore
records real values without making any row admissible.

P6-D does not materialize a 22-field candidate record, modify admission
artifacts, rewrite a final dataset or sample index, backfill a sample, access a
network or checkpoint, execute a model, or train. ADMIT_004 rule logic, E1,
real candidate evaluation, bulk download, and training remain not ready. The
fixed next step is a design for resolving ADMIT_004 residue-identity and
atom-name semantics. Formal training still requires the feature-semantics
audit, including resolution or formal audit of the historical unknown atom
feature policy.
