# CovaPIE Current11 Cys-SG review-gate design v1

## Scope

This metadata-only step freezes the human-review gate for seven candidate
reaction-family/warhead-rule classes and eleven Current11 sample assignments.
It designs review policies, records, dependencies, readiness, and fail-closed
behavior. It does not execute human review or create review packages.

No reaction family, local-graph topology rule, SMARTS, sample assignment, gold
label, training label, ligand role, minimal seed, mask, tensor, model head, loss,
or training operation is approved or materialized here.

## Immutable input boundary

The twelve sources are read only with `git show` from formal BASE
`0c8d1d10260a028360357b8c309f22676fc81645`. Their path identities, SHA256
digests, row counts, Current11 coverage, fields used, and authority classes are
recorded in the source inventory. The predecessor assignment transaction must
be successful, all seven class identities and eleven assignment-record digests
must reconstruct, and every sample-to-class-to-rule-to-family link must be
exact-one.

## Four independent review dimensions

1. Reaction-family identity review confirms the canonical family identity.
2. Warhead-rule topology review confirms the candidate local-graph topology.
3. Warhead SMARTS review evaluates a separately materialized SMARTS candidate.
4. Sample-assignment review independently evaluates each Current11 assignment.

A topology approval is not a SMARTS approval and cannot make an approved
warhead rule available. A class-level candidate never automatically approves a
sample assignment.

## Decision and record contracts

General human decisions are exactly `not_reviewed`, `approve`, `revise`, and
`quarantine`. SMARTS statuses are exactly `not_materialized`,
`candidate_not_reviewed`, `approved`, `revised`, and `quarantined`.

The future record version is `covapie_cys_sg_human_review_record_v1`.
Class- and sample-level record field inventories are frozen in the manifest.
Review-record SHA256 uses canonical JSON with sorted keys, compact separators,
UTF-8, no timestamps or absolute paths, and excludes `review_record_sha256`
from its own hash input.

Every actual design row remains `not_reviewed`; reviewer ID, rationale, and
notes are empty; SMARTS is empty and `not_materialized`.

Review records are not arbitrary mappings. The only unit types are
`candidate_class` and `sample_assignment`, and each uses its own exact key
inventory. The validator requires an exact `dict`, the frozen record version,
the matching exact key set, exact scalar types, valid lowercase SHA256 values,
closed decision/status vocabularies, and consistent reviewer, rationale, and
SMARTS states. Missing fields, extra metadata (including timestamps and paths),
bool-as-int class indices, forbidden synthetic reviewer identities, and
inconsistent SMARTS states fail closed.

Canonical hashing validates the complete record first and excludes only
`review_record_sha256`; all other formal fields remain in the hash input.
Identity verification requires a populated digest equal to the recomputed
value. `source_class_record_sha256` remains a future review-package source
identity: this design freezes only its field, type, format, and hash behavior
and does not invent seven class identities. A future sample review record must
copy the existing `assignment_record_sha256` into
`source_assignment_record_sha256`, rather than define a second assignment
identity. Complete synthetic empty drafts are used only by tests and the
independent checker to exercise this schema/hash contract; they are never
written and are not human-review results.

SMARTS review status is itself a source of review-metadata requirements.
`not_materialized` and `candidate_not_reviewed` are unreviewed states:
`candidate_not_reviewed` means a candidate SMARTS exists but has not received
human approval, and it carries no reviewer metadata when family and topology
also remain unreviewed. In contrast, `approved`, `revised`, and `quarantined`
are human-reviewed outcomes and require a real reviewer identity plus a
nonempty rationale even when family and topology decisions are still
`not_reviewed`. A quarantined outcome may retain or omit the candidate SMARTS,
but it cannot omit the human-review identity. The current real design evidence
remains `not_materialized`, with empty SMARTS, reviewer, rationale, and notes.

For every review boundary, “nonempty” formally means an exact string that
still contains content after `strip()`. Whitespace-only reviewer IDs and
rationales are not human-review metadata, and whitespace-only SMARTS is not a
candidate SMARTS. Padded forbidden reviewer identities remain forbidden after
trimmed case-fold comparison. The public family-approval, warhead-rule
approval, and human-gold helpers use the same meaningful-text boundary as the
review-record validator, so whitespace or non-string truthy values cannot open
readiness. Current real records remain exactly empty and retain their
`not_reviewed` / `not_materialized` state.

The public family-approval, warhead-rule, human-gold, and role-readiness
helpers are also fail-closed gates. Python equality such as `1 == True` and
other truthy operands do not establish an identity or open a boolean gate.
Identity digests must be exact strings containing exactly 64 lowercase
hexadecimal characters. Boolean dependencies must be exact `bool` values, and
counts must be exact `int` values, explicitly excluding `bool` and `float`.
Every helper returns an exact `bool`, including for invalid synthetic inputs.
These stricter public boundaries do not change any current data row, artifact,
decision, or readiness value.

## Approval dependencies

An approved reaction family requires an explicit `approve` decision, nonempty
reviewer and rationale, and unchanged canonical family identity.

An approved warhead rule additionally requires topology approval, a nonempty
approved SMARTS, an exact-one SMARTS match containing the known reactive ligand
atom, a nonempty warhead atom set, an exact-one attachment boundary, nonempty
reviewer and rationale, and unchanged class/rule/family identities.

Human gold requires independent sample approval, an approved linked family and
rule, unchanged assignment-record identity, and nonempty reviewer and rationale.
Role-proposal generation requires approved family, approved rule, and human
gold together. Quarantine closes every downstream gate. Training-label approval
always remains the responsibility of an independent future gate.

## Readiness and transaction result

All twelve policies, seven class review packages, and eleven sample review
packages materialize atomically. If either validation phase fails, all three
core tables are header-only; partial class or sample materialization is
forbidden.

The successful design state is:

- class review package ready: 7/7;
- sample assignment review ready: 7/7 classes;
- sample review package ready: 11/11;
- family/topology/sample reviews completed: 0;
- approved family/rule/SMARTS, human gold, and training labels: 0;
- role, seed, mask, tensor, model, and training readiness: 0;
- integrated covalent model modules: 0/5.

The Exact30 typed mutation matrix independently proves that source, identity,
review, SMARTS, gold, role, materialization, and execution-boundary violations
fail closed.

## Next step

The recommended next step is
`materialize_covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1`.
That future step may package the frozen evidence for human review, but it must
not invent or pre-fill reviewer decisions.
