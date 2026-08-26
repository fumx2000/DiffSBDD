# CovaPIE cumulative1000 current global readiness census with PRF V1

## Scope

This additive successor refreshes the published ONL census with already-published PRF authority. The ONL census is the frozen 1000-row predecessor with 58 authoritative chemistry-positive events. The PRF formal decision, completed-decision ingestion, and completed-decision reconciliation provide an exact source-derived delta of eight events. The refreshed census therefore contains 66 authoritative positives.

This step creates no human decision and no new human, chemistry, pair, role, reusable, split, tensor, training-admission, or training authority. It does not reinterpret PRF chemistry. Exactly the PRF ranks 539-542 and 587-590 change; the other 992 rows remain dictionary-equal to the ONL predecessor.

## PRF projection boundary

PRF Exact8 becomes `COMPLETED_HUMAN_POSITIVE`, chemistry `POSITIVE`, task relevance `RELEVANT`, and training use `EXCLUDE_FROM_TRAINING_ONLY`. The formal PRF decision remains the human-review authority source. The published PRF event matrix is the machine-consumable chemistry, task, pair, role, training, and positive projection source.

PRF adds eight sample-authoritative reactive pairs and eight sample-authoritative direct-attachment role partitions. It adds no model-bound pair or tensor target. Global sample-authoritative pair and role counts are both 66, while model-bound pair targets remain 41. Missing tensor integration is 25 events: G3H 8, ONL 9, and PRF 8. All 25 belong to the training-excluded population.

Training `INCLUDE` remains 29. Training-excluded chemistry-positive events increase from 29 to 37. Future admission candidates remain 12, runtime-usable events remain 17, formally admitted events remain 5, and ready-for-formal-training events remain zero.

## Canonical masks and geometry

Canonical V1 remains exactly five tasks, with semantic long names as the authority:

1. `warhead_only` / A: 66 applicable events
2. `linker_plus_warhead` / B: 31
3. `scaffold_plus_warhead` / B2: 31
4. `scaffold_only` / B3: 66
5. `scaffold_plus_linker_plus_warhead` / C: 66

The role composition is 31 `STRICT_LINKER_PRESENT_V1` and 35 `DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`. PRF uses direct applicability `[0,3,4]`; B3 is present and no sixth task exists.

Geometry authority is unchanged: POST source evidence 867, POST sample authority 21, POST training targets 17, and every PRE count zero. The refresh performs no POST-to-PRE promotion, PRE zero-fill, or precursor reconstruction.

## Current queue and readiness

The complete frozen 131-unit priority queue is reranked dynamically after PRF reconciliation. There are 265 pending events in 122 pending units. The next high-yield unit is `COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22`, ligand 2VS, with eight events across PDB entries 4NPI and 4OUB. This census does not perform that review.

`CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE=true` and `READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION=true`. The recommended mainline is `HIGH_YIELD_HUMAN_REVIEW_EXPANSION`. `READY_FOR_FORMAL_TRAINING=false`; feature semantics remain `AUDIT_REQUIRED_LATER`, and Step12D remains only `SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT`.

## Validation

Run the targeted tests:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q \
  tests/test_covapie_cumulative1000_current_global_readiness_census_with_prf_v1.py
```

Run the repository-state-neutral checker:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  scripts/check_covapie_cumulative1000_current_global_readiness_census_with_prf_v1.py
```

The checker verifies frozen identities, Exact8 overlay, 992 unchanged rows, set algebra, counts, full-queue Top10, exact semantic bindings, three frozen derived-projection digests, and two-directory byte determinism. The manifest does not record its own hash or live Git/lifecycle metadata.
