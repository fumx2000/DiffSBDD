# CovaPIE Current11 review submission adapter v1

## Implemented capability

The public, keyword-only in-memory API is:

```python
def adapt_current11_warhead_boundary_review_submission_bundle_v1(
    *,
    source_payload: bytes,
) -> dict[str, Any]:
```

It snapshots an exact `bytes` input, delegates exactly once to the committed
design reference evaluator, checks that the input remains unchanged, and
returns the deterministic Exact9 response. The adapter accepts no repository
root, path, filename, pre-parsed object, or other input channel. It performs
no filesystem, Git, lifecycle, ingestion, or authority operation.

The runtime authority is the committed design at
`84375060a0ddd9b281d17719331a316716bffd85`, whose production SHA256 is
`55080fef4932d13be5fa063d3545c1120cb1e2bcaba20ab3cbe04a50b8838a58`.
No parser, precedence, Exact25, Exact9, or Exact12 logic is duplicated.

## Verified synthetic scope

All Exact28 committed synthetic truth cases have exact public/reference object
parity: 4 adapt and 24 fail closed. The successful select, revise, quarantine,
and partial two-sample cases pass the committed ingestion-interface public
authority-context builder, evaluator, and response validator. Inputs remain
unchanged and no repository or lifecycle artifact is materialized.

This establishes:

- `formal_submission_adapter_implemented=true`
- `public_adapter_available=true`
- `synthetic_submission_adaptation_verified=true`
- `ready_for_real_submission_adaptation=true`
- `real_submission_payload_available=false`
- `real_submission_adaptation_executed=false`
- `ready_for_real_review_ingestion_execution=false`

Actual payload, completed-review, provenance-envelope, adapted-submission,
ingestion-result, and authority counts remain zero.

## Unchanged readiness boundary

SMARTS, role, seed, mask, tensor, model, and training remain closed. Canonical
masks remain exactly `warhead_only`, `linker_plus_warhead`,
`scaffold_plus_warhead`, `scaffold_only`, and
`scaffold_plus_linker_plus_warhead`. Integrated/planned covalent model modules
remain 0/5 and training is not ready.

Formal training still requires a feature-semantics audit. Step12D remains a
smoke legality check, not a final training-feature contract.

## Recommended next step

`prepare_covapie_current11_real_human_review_submission_bundle_v1`
