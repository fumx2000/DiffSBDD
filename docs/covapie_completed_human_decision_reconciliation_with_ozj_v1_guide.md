# CovaPIE completed human decision reconciliation with OZJ V1

## Scope

This metadata-only successor adds the published OZJ Exact4 completed human
decision to the CHT completed-decision source chain. It performs one in-memory
reconciliation and does not materialize a global census, refresh the priority
queue, begin F24 review, create tensors, admit training data, run a model, or
update parameters.

The production entry point is
`reconcile_real_completed_human_decisions_with_ozj_v1(repo_root)`.

## Why OZJ has no transition adapter

All four original OZJ historical rows already have the generic reconciler's
required prior state:

- `current_review_status = CURRENTLY_UNREVIEWED`
- `calibration_eligible = true`
- `calibration_exclusion_reason = ""`

The successor proves the complete Exact4 event set, its single review-unit
identity, absence of missing, duplicate, or extra unit events, and the three
prior-state fields above. It does not rewrite an OZJ row or create an OZJ
transition owner.

ONL remains the sole special unit whose completed decision follows a
`CURRENTLY_IN_PROGRESS` prior. The existing ONL normalization owner is called
exactly once. OZJ Exact4 rows are compared before and after that call and must
remain field-for-field identical. Calling the generic reconciler on the
original historical rows still fails closed on the ONL prior.

## Source composition and architecture

The successor calls the published CHT source loader exactly once and appends
one projected OZJ source:

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
- OZJ: 4

The result is exactly 11 source bindings, 11 review units, and 87
collision-free normalized facts. The CHT reconciliation result is not used as
an overlay. The unchanged generic reconciler is called exactly once on the
ONL-adapted historical rows and all eleven sources. Source reversal produces
the same semantic result under the generic owner's canonical ordering.

## OZJ Exact4 and normalized semantics

The thin projector calls only the OZJ ingestion owner's public validated
formal-decision loader. It does not parse the formal JSON independently and
does not use the published matrix, snapshot, summary, or manifest as a second
reconciliation authority path.

The source binding is the formal OZJ human decision with schema
`covapie_ozj_exact4_formal_human_decision_v1`, review unit
`COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450`, approval time
`2026-08-28T14:03:16Z`, and SHA256
`0b14271a4541e69d768e28b6433c87b8b22c21505f6e3bdf075bb94381c3c606`.

The four distinct PDB 4CL8 event contexts are ranks 670 through 673:

- `COVAPIE_CYS_SG_EVENT_V1:4CL8:A:CYS:168-:SG:E:OZJ:CAF`
- `COVAPIE_CYS_SG_EVENT_V1:4CL8:B:CYS:168-:SG:I:OZJ:CAF`
- `COVAPIE_CYS_SG_EVENT_V1:4CL8:C:CYS:168-:SG:L:OZJ:CAF`
- `COVAPIE_CYS_SG_EVENT_V1:4CL8:D:CYS:168-:SG:O:OZJ:CAF`

Every projected generic fact has:

- human review completed: `true`
- legacy completed status: `COMPLETED_HUMAN_POSITIVE`
- task relevance: `RELEVANT`
- chemistry: `POSITIVE`
- training disposition: `INCLUDE`
- `human_training_excluded = false`

These meanings remain separate. `INCLUDE` is a normalized human training-use
disposition; it is not formal training admission, runtime usability, or
authorization to materialize training data.

The ingestion owner derives four
`CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION` candidates. That candidacy
remains owned by the published ingestion/census projection chain. It is not
copied into `NormalizedCompletedDecisionFact`, and the reconciliation result
does not create a future-candidate aggregate. Candidate-1 roles, CAF/OAD,
warhead/linker/scaffold atoms, geometry, scientific narrative, reaction-family
flags, warhead flags, and topology boundaries likewise remain outside the
generic reconciliation contract.

## Reconciled priority-review state

The in-memory reconciliation covers 338 events in 131 units:

- completed positive: 87 events / 11 units
- completed negative: 24 events / 4 units
- completed total: 111 events / 15 units
- currently unreviewed and pending: 227 events / 116 units
- currently in progress: 0 events / 0 units
- normalized training dispositions: 23 `INCLUDE` and 64
  `EXCLUDE_FROM_TRAINING_ONLY`

Relative to the published CHT reconciliation, OZJ contributes +4 completed
positive events, +1 completed positive unit, +4 completed total events, +1
completed total unit, -4 unreviewed/pending events, -1 unreviewed/pending unit,
+4 normalized `INCLUDE`, +0 normalized `EXCLUDE_FROM_TRAINING_ONLY`, and +0
formal training admissions.

## Current global census boundary

This candidate is not a global census refresh. The published CHT census
remains authoritative with 100 positive events, 101 task-relevant events, 36
training `INCLUDE`, 64 training `EXCLUDE_FROM_TRAINING_ONLY`, 19 future
candidates, and 100 sample-level pair and role authorities. In that census
OZJ remains `CURRENTLY_UNREVIEWED`, and its chemistry, task, and training
dispositions remain unresolved.

The following values are `INFORMATIONAL_ONLY` derivations for a future census
successor: 104 positive, 105 relevant, 40 `INCLUDE`, 64 `EXCLUDE`, 23 future
candidates, 104 pair authorities, 104 role authorities, 48 strict-profile and
56 direct-profile events. Canonical Exact5 authoritative applicability would
be A=104, B=48, B2=48, B3=104, and C=104. None of these values is materialized
or declared current by this successor.

After a future authoritative queue refresh, the expected pending head is F24,
review unit `COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5`, with four events from
PDB 3V4X. This is `INFORMATIONAL_ONLY`; this successor does not refresh the
queue, begin F24 review, or create an F24 package.

## Readiness and checker

The OZJ completed decision is reconciled in this uncommitted candidate and is
ready for external review. The global reconciliation update is candidate-only
and unpublished; the global census update is `NOT_DONE`.

It is not ready for training. Feature semantics remain
`AUDIT_REQUIRED_LATER`, and Step12D remains a smoke legality check rather than
a final training-feature contract. The OZJ 3-formylphenyl/TbPTR1 context is not
promoted here to PRE topology authority, complete POST topology, a reaction
family, a warhead rule, a warhead type, or a training feature.

Run the repository-state-neutral checker with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_completed_human_decision_reconciliation_with_ozj_v1.py
```
