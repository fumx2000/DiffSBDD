# CovaPIE legacy four-level mask retirement gate V1

This R3 gate is the independent formal evidence step for retirement of the old
four-level mask API. It does not modify runtime code, model code, data, or a
checkpoint, and it performs no training or parameter update.

## R1, R2, and R3

R1 moved the covalent demo from the old `--mask_level` and four-level builder
surface to the canonical `--mask_semantic` surface. R2 then removed the old
core provider, schema type, dataset short-key behavior, checker behavior, and
positive legacy tests across its committed ten-path scope.

R2 established a retirement candidate: its own post-change evidence reports
zero candidate active and unresolved references. That is not the same claim as
formal repository retirement. R3 independently reconstructs the R2 commit
identity, scans the complete R2 tracked tree, verifies negative runtime facts,
and proves the canonical five-level runtime. R3 is therefore a separate gate,
not a restatement of an R2 manifest boolean.

## Frozen R2 snapshot

The scan subject is the exact R2 commit
`8711c1899759ca4c1f4a24f7ff9782b81a257245`, including its single parent,
tree, subject, exact ten changed paths, modes, and blob SHA256 values. Blob
content is obtained through read-only Git object operations. The working tree
and index are not used as R2 retirement evidence.

This matters once C1, C2, C3, or C4 changes exist: successor work cannot alter
what R3 concluded about R2. The four R3 source/test/checker/guide files also do
not enter their own reference inventory, because they are absent from the
fixed R2 scan subject. Their constants may name old symbols without creating a
self-referential active-runtime finding.

The scan combines Python AST inspection, notebook JSON code-cell AST
inspection, structured schema inspection, and controlled text search. Notebook
markdown cells are read-only text evidence. Code-cell magic and shell lines
are sanitized only enough to make safe AST parsing possible; they are never
executed.

## Reference classification

Every detected record has a path, line or notebook-cell location, exact symbol
or token, context kind, classification, runtime/schema/training flags, and a
retained reason. The permitted classifications are active runtime, current
positive test, negative rejection evidence, historical read-only evidence,
design/documentation evidence, and gate-control evidence.

An active definition, import, call, CLI argument, schema admission, short-key
dataset API, resolver translation, positive current test, or notebook code
hit is a blocker. Dangerous runtime kinds default to `active_runtime` in
source and scripts, and to `current_positive_test` in current tests. Negative
records are retained only where the SHA-bound source proves the exact records
occur in an explicit rejection context. Historical records are retained
without import or execution. Design and documentation records describe the
migration or use short aliases only as display/reporting labels; long semantic
names remain the source of truth.

Retention is governed jointly by an exact path policy, allowed reference
kinds, allowed symbols or tokens, classification, and retained reason. A
directory prefix or a Markdown suffix never grants retention. An unknown path,
kind, or context is unresolved and fails closed; it is not converted into
reviewed evidence.

The complete ordered retained collection is frozen by a canonical digest that
includes path, location, token, context, classification, and reason. An added,
removed, moved, or reclassified record fails closed. This is why the gate does
not need—and must not use—rules such as “ignore all docs,” “ignore all data,”
or “ignore all tests.” Repository text cannot be required to contain zero old
terms: rejection tests, historical evidence, and reviewed design explanation
are legitimate and necessary evidence. The digest is a final exact-set freeze,
not a substitute for safe classification.

## Historical B3 boundary

The historical B3 implementation source and its checker remain byte-frozen,
read-only evidence. The historical module is not imported by the package,
current runtime, or non-historical tests. Its current importability is not a
requirement. The historical checker must not run: after R2 removed the old
provider, its failure is the expected retirement boundary rather than a
current regression.

The separately SHA-bound real-feature mapping-loader test retains `B2`, `B3`,
and `mask_scaffold` only inside rejection behavior. It does not require or
translate a positive legacy runtime input.

## Canonical five-level runtime

The canonical semantic order is:

1. `warhead_only` (display alias `A`)
2. `linker_plus_warhead` (display alias `B`)
3. `scaffold_plus_warhead` (display alias `B2`)
4. `scaffold_only` (display alias `B3`)
5. `scaffold_plus_linker_plus_warhead` (display alias `C`)

Before importing any live provider, R3 verifies that `masking.py`, `schema.py`,
and `dataset.py` are ordinary non-symlink, non-executable files whose bytes
exactly match their SHA-bound blobs in R2. R3 then verifies the matching
internal long-form levels, all five toy masks, the
different B2 and B3 partitions, the exact five-item dataset result, four
current dataset consumers, and the R1 demo CLI. Short aliases are rejected as
public runtime inputs with `COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID`; no
automatic translation is permitted. No sixth mask is added.

## Exact47 and lifecycle

The public evaluator returns exactly 47 ordered, JSON-safe fields. Its digest
is SHA256 over canonical JSON for the first 46 fields and excludes the digest
field itself. The response contains no `Path` or tensor objects and is
deterministic.

Before commit, all four R3 paths must be ordinary untracked regular files and
there may be no other ordinary untracked path, tracked modification, or staged
change. The lifecycle is `r3_precommit_candidate`; evidence can pass and the
gate can be ready for commit review, but
`legacy_four_level_full_runtime_retired` remains false.

After a unique single-parent R3 commit with the exact subject and duplicate-free
four-path scope exists above R2, the lifecycle is `r3_committed_unpushed` until
it is on `origin/main`. This state requires a globally clean working tree and
index and no ordinary untracked files. The commit body must be empty; every R3
entry must be a nonempty bounded `100644 blob`; and each live R3 file must be an
ordinary non-symlink file byte-identical to that commit. At that point the
formal full-runtime-retired claim may become true, but C1 readiness remains
false.

Once the same unique R3 commit is an ancestor of both HEAD and `origin/main`,
the lifecycle is `r3_published_successor`. HEAD and `origin/main` may be later
successors. Unrelated successor tracked, staged, and ordinary-untracked changes
do not invalidate the historical R3 gate; modifications, staged changes,
missing/nonregular paths, or byte drift in any R3 gate file do invalidate it.
The R3 gate files and frozen canonical core therefore remain commit-bound.
Only this published state permits repository CLI forwarding C1.

The checker and targeted test suite validate the exact cross-field contract for
all three real lifecycle states—precommit candidate, committed-unpushed, and
published successor—and select the state reported by the evaluator. They do
not require HEAD or `origin/main` to equal the R3 commit because later
successors use ancestor semantics.

The evaluator, not this guide, is the source of truth for the current lifecycle
profile. The same committed artifacts support precommit, committed-unpushed,
and published-successor validation. At each stage, the response and digest are
derived from the actual Git state and its exact cross-field contract. Because
Exact47 includes lifecycle fields, it is normal for the precommit digest to
differ from committed and published digests; neither the tests nor the checker
may require the precommit digest after the repository advances. This guide does
not claim that an R3 commit has been created or published.

## Safety and training boundary

Checkpoint compatibility is unchanged because R3 changes no model,
checkpoint, forward path, loss, dataloader, or training-critical source. It
does not execute model forward, backward, optimization, fine-tuning,
parameter updates, checkpoint loading, or checkpoint saving.

Formal training still requires a feature-semantics audit. Step12D was a smoke
legality check, not the final training-feature contract; the historical
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` state must be
resolved or formally audited before training readiness can be claimed.
