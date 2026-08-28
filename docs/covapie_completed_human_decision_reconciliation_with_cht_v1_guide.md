# CovaPIE completed human decision reconciliation with CHT V1

## Scope

This metadata-only successor adds the frozen CHT Exact5 completed human
decision to the published NEQ completed-decision source chain. It performs one
in-memory reconciliation and does not materialize a census, refresh the
priority queue, create tensors, admit training data, run a model, or update
parameters.

The production entry point is
`reconcile_real_completed_human_decisions_with_cht_v1(repo_root)`.

## Why CHT has no transition adapter

All five original CHT historical rows already have the generic reconciler's
required prior state:

- `current_review_status = CURRENTLY_UNREVIEWED`
- `calibration_eligible = true`
- `calibration_exclusion_reason = ""`

The successor proves the complete Exact5 event set, its single review-unit
identity, absence of missing, duplicate, or extra unit events, and the three
prior-state fields above. It does not rewrite a CHT row or create a CHT
transition owner.

ONL remains the sole special unit whose completed decision follows a
`CURRENTLY_IN_PROGRESS` prior. The existing ONL normalization owner is called
exactly once. CHT Exact5 rows are compared before and after that call and must
remain field-for-field identical. Calling the generic reconciler on the
original historical rows still fails closed on the ONL prior.

## Source composition and architecture

The successor calls the published NEQ source loader exactly once and appends
one projected CHT source:

- FFQ: 8
- POA: 16
- G3H: 8
- ONL: 9
- PRF: 8
- 2VS: 8
- 1F8: 8
- YUN: 7
- NEQ: 6
- CHT: 5

The result is exactly 10 source bindings, 10 review units, and 83
collision-free normalized facts. The NEQ reconciliation result is not used as
an overlay. The unchanged generic reconciler is called exactly once on the
ONL-adapted historical rows and all ten sources. Source reversal produces the
same semantic result under the generic owner's canonical ordering.

## CHT normalized semantics

The thin projector calls only the CHT ingestion owner's public validated
formal-decision loader. It does not parse the formal JSON independently and
does not use the published snapshot, matrix, summary, or manifest as a second
authority path.

The source binding is the formal CHT human decision with schema
`covapie_cht_exact5_formal_human_decision_v1`, review unit
`COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410`, approval time
`2026-08-28T08:07:26Z`, and SHA256
`0f8b48d08a116aa6fa2b30a67d89a51ae2b730f68514b0ce2e0985189dd1ea2b`.

The five distinct event contexts are ranks 913, 914, 915, 958, and 959:
three events from PDB 4V3F and two from 5A2D. Every event retains
`cys_residue_id = CYS:450-`.

Every projected fact has:

- human review completed: `true`
- legacy completed status: `COMPLETED_HUMAN_POSITIVE`
- task relevance: `RELEVANT`
- chemistry: `POSITIVE`
- training disposition: `EXCLUDE_FROM_TRAINING_ONLY`
- `human_training_excluded = true`
- `training_admitted = false`

These meanings remain separate. Training exclusion does not change task
relevance to `NOT_RELEVANT` or chemistry to `NEGATIVE` or
`NOT_ESTABLISHED`. CHT contributes five positive facts, five normalized
training exclusions, no normalized includes, and no training admissions.

Candidate-2 role details, C4-O6 source bond order, PRE boundaries,
reaction-family or warhead flags, geometry arrays, and the complete ingestion
snapshot remain owned by the ingestion stage and are not copied into generic
reconciliation facts.

## Reconciled priority-review state

The in-memory reconciliation covers 338 events in 131 units:

- completed positive: 83 events / 10 units
- completed negative: 24 events / 4 units
- completed total: 107 events / 14 units
- currently unreviewed and pending: 231 events / 117 units
- currently in progress: 0 events / 0 units
- normalized training dispositions: 19 `INCLUDE` and 64
  `EXCLUDE_FROM_TRAINING_ONLY`

Relative to the published NEQ reconciliation, CHT contributes +5 completed
positive events, +1 completed positive unit, +5 completed total events, +1
completed total unit, -5 unreviewed/pending events, -1 unreviewed/pending
unit, +0 normalized `INCLUDE`, +5 normalized
`EXCLUDE_FROM_TRAINING_ONLY`, and +0 training admissions.

## Current global census boundary

This candidate is not a global census refresh. The published NEQ census
remains authoritative with 95 positive events, 96 task-relevant events, 36
training `INCLUDE`, 59 training `EXCLUDE_FROM_TRAINING_ONLY`, 19 future
candidates, and 95 sample-level pair and role authorities. In that census CHT
remains `CURRENTLY_UNREVIEWED` and its chemistry, task, and training
dispositions remain unresolved.

The following values are `INFORMATIONAL_ONLY` derivations for a future census
successor: 100 positive, 101 relevant, 36 `INCLUDE`, 64 `EXCLUDE`, 19 future
candidates, 100 pair authorities, 100 role authorities, 44 strict-profile and
56 direct-profile events. Canonical Exact5 authoritative applicability would
be A=100, B=44, B2=44, B3=100, and C=100. None of these values is materialized
or declared current by this successor.

After a future authoritative queue refresh, the expected pending head is OZJ,
review unit `COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450`, with four events from
PDB 4CL8. This is `INFORMATIONAL_ONLY`; this successor does not refresh the
queue, begin OZJ review, or create an OZJ package.

## Readiness and checker

The CHT completed decision is reconciled in this uncommitted candidate and is
ready for external review. The global reconciliation update is candidate-only
and unpublished; the global census update is `NOT_DONE`.

It is not ready for training. Feature semantics remain
`AUDIT_REQUIRED_LATER`, and Step12D remains a smoke legality check rather than
a final training-feature contract. The approved betaine-aldehyde-mediated
thiohemiacetal context is not promoted here to PRE C4=O authority, complete
POST topology, a warhead type, a reaction family, or a training feature.

Run the repository-state-neutral checker with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_completed_human_decision_reconciliation_with_cht_v1.py
```
