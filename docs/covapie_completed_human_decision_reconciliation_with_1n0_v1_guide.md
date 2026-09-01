# CovaPIE 1N0 completed-decision reconciliation V1

This successor adds the published 1N0 Exact4 task-domain-negative decision to
the existing with-I12 completed-decision source chain. It validates the rich
decision through the published 1N0 ingestion owner, projects only the generic
Exact11 fact schema, and delegates reconciliation to the unchanged generic
owner.

The semantic transition is:

```text
NOT_RELEVANT
→ COMPLETED_HUMAN_NEGATIVE
→ NOT_APPLICABLE
```

D2 remains `UNRESOLVED`, so the generic chemistry disposition is
`NOT_ESTABLISHED`. This is not a chemistry `NEGATIVE`. Likewise,
`NOT_APPLICABLE` is not `EXCLUDE_FROM_TRAINING_ONLY`, and
`human_training_excluded` remains false.

The raw SG-C16 observation and second C2 endpoint remain rich structural
context. They are not projected into the generic fact. The reconciliation
creates no reactive-pair, role-partition, mask, warhead, reaction-family,
geometry, training-admission, or reusable chemistry authority.

Reconciliation is in memory only. No reconciliation CSV, JSON, summary,
manifest, or derived-data root is materialized. The next downstream action
after publication is a separate census refresh, not training.

```text
FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true
READY_FOR_TRAINING=false
```
