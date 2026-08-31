# CovaPIE source-binding active-consumer integration V2

## Scope

This additive, read-only overlay integrates the six published filesystem-mode
source-binding V2 successors in the fixed semantic order:

1. YUN
2. NEQ
3. CHT
4. OZJ
5. F24
6. 2A2

It is migration Phase B2 integration work. The phase name is unrelated to the
canonical `scaffold_plus_warhead` / B2 mask. The canonical mask vocabulary
remains exactly five tasks and includes `scaffold_only` / B3.

The overlay does not create a seventh consumer, another ligand-specific
successor, a V2 census, or a materialized effective-state artifact.

## Authority boundary

The integration keeps three authorities separate:

```text
filesystem source acceptance = SOURCE_BINDING_POLICY_V2
sample scientific projection = PUBLISHED_V1_ARTIFACTS
current global state          = PUBLISHED_2A2_V1_GLOBAL_CENSUS
```

Source-binding V2 accepts filesystem objects and bytes. It does not reinterpret
chemistry, labels, masks, review decisions, training admission, or global census
state. The six already-published V1 Exact4 artifact sets remain the scientific
projection authority. The existing 2A2 V1 census remains the current global
state authority.

## Public API

The production module exports exactly:

```python
SourceBindingActiveConsumerIntegrationV2Error

verify_covapie_source_binding_active_consumer_integration_v2(
    *,
    repo_root: Path,
) -> dict[str, object]
```

There is no public path override, writer, cache, registry, census refresh,
reconciliation, or materialization API.

## Verification order

The verifier performs these operations in order:

1. B1-binds the published source-binding policy V2 file.
2. B1-binds all six V2 owner/checker pairs with
   `expected_executable=False`.
3. B1-binds the published 2A2 V1 census CSV, summary, and manifest.
4. Calls each of six integration-owned projection wrappers exactly once.
5. Hashes the 24 returned in-memory V1 artifact payloads and compares their
   filenames, byte counts, and SHA256 values with the published identities.
6. Parses only the B1-returned census bytes and validates the published summary,
   CSV counts, canonical tasks, and manifest bindings.
7. Returns a deterministic in-memory effective-state record.

The production module imports B1 and the six V2 successor modules. It does not
directly import a ligand V1 ingestion module or call a direct file-read API.

## Frozen global state

The integration proves the following current values without refreshing the
census:

```text
positive=112
relevant=113
INCLUDE=44
EXCLUDE_FROM_TRAINING_ONLY=68
future_training_admission_candidate=27
sample-level pair authority=112
sample-level role authority=112

warhead_only / A=112
linker_plus_warhead / B=52
scaffold_plus_warhead / B2=52
scaffold_only / B3=112
scaffold_plus_linker_plus_warhead / C=112
```

The task count is exactly five, B3 is present, and a sixth task is absent.

The existing review and runtime boundaries remain:

```text
completed positive events/units=95/13
completed negative events/units=24/4
completed total events/units=119/17
unreviewed events/units=219/114
formal training admitted=5
current runtime usable=17
```

The geometry boundary remains:

```text
POST source evidence=867
POST sample authority=21
POST training target=17
PRE source evidence=0
PRE sample authority=0
PRE training target=0
```

The exact geometry result keys are:

```text
POST_source_evidence_available_count
POST_sample_authoritative_count
POST_training_target_available_count
PRE_source_evidence_available_count
PRE_sample_authoritative_count
PRE_training_target_available_count
```

POST source evidence, sample authority, and training target are cross-checked
between their dedicated census CSV columns and the published summary. The
current census CSV has no dedicated `pre_geometry_source_evidence_available`
column, so PRE source evidence is frozen from
`geometry.PRE_source_evidence_available_count` in the B1-bound published
summary; it is not inferred from sample-level authority. PRE sample authority is
cross-checked from `pre_geometry_authoritative`, and PRE training target is
cross-checked from `pre_geometry_training_target_available`.

No POST-to-PRE promotion or PRE zero fill occurs. PRE remains not a V1 hard
requirement.

## Failure behavior

Every source is accepted only by the combined B1 filesystem-security and
content-identity gate. A missing, unsafe, executable-class-mismatched,
byte-count-mismatched, or SHA256-mismatched dependency fails closed before its
projection is trusted. Projection inventory or digest drift and census schema or
count drift also fail closed with
`SourceBindingActiveConsumerIntegrationV2Error`.

The six published successors retain responsibility for their own source-path
override tests. The integration intentionally exposes no override mechanism.

## Checker lifecycle

The checker accepts exactly two lifecycle profiles:

- `CANDIDATE_UNTRACKED`: the baseline HEAD and origin are unchanged, no Exact4
  file is tracked, and the ordinary untracked inventory is exactly the Exact4.
- `TRACKED_CLEAN`: one clean Exact4-only child commit of the baseline, either one
  commit ahead of the baseline origin or already published at origin.

Partial, staged, dirty, extra-file, multi-commit, divergent, and other repository
states fail closed.

Run the targeted validation with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_source_binding_active_consumer_integration_v2.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_source_binding_active_consumer_integration_v2.py
```

The checker directly verifies Exact4 hygiene, lifecycle, B1 and successor
identities, publication ancestry, production AST restrictions, behavioral call
order, all 24 projection payload identities, and current census bytes and
counts. It does not invoke pytest as a substitute for those checks.

## Readiness

Passing this integration establishes readiness only for external review and the
future migration Phase B3 historical-immutability proof. It does not complete
Phase B2 publication and does not start Phase B3, I12 review, tensorization,
training, fine-tuning, or parameter updates.

`READY_FOR_TRAINING` remains false. Before any formal training or
training-preparation work, the feature-semantics audit remains mandatory. The
historical Step12D result was a smoke legality check, not a final
training-feature contract.
