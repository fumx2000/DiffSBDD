# CovaPIE cumulative1000 current global readiness census with ONL V1

## Purpose and authority boundary

This additive successor refreshes the published cumulative1000 current-state census after publication of the ONL Exact9 formal decision, completed-decision ingestion, and completed-decision reconciliation. The frozen predecessor remains valid historical evidence with 49 authoritative chemistry-positive events. The ONL publication supplies an exact, disjoint +9 delta, so this successor reports 58 current authoritative positives.

This is a derived refresh. It does not create a human decision or new chemistry, pair, role, reusable, split, tensor, or training authority. It does not modify model or training code and does not perform a loader call, batch construction, model forward, loss, backward pass, optimizer step, admission, fine-tune, or parameter update.

## Thin successor construction

The production owner calls `compute_covapie_cumulative1000_current_global_readiness_census_v1(repo_root)` and accepts its SHA-closed 1000-row result only after the predecessor has re-proven the old 49-positive projection. It then calls `reconcile_real_completed_human_decisions_with_onl_v1(repo_root)`, SHA-validates the published ONL event-task-label matrix, deep-copies the predecessor rows, and overlays exactly the nine ONL event identities at ranks 24, 25, 26, 27, 134, 434, 435, 436, and 437.

Exactly nine dictionaries differ. The remaining 991 dictionaries are field-for-field equal to the predecessor. ONL raw structure, exact event, explicit covalent evidence, full-coordinate POST evidence, CCD completeness, feature compatibility, structural success, POST source evidence, representation-gap state, and feature-incompatibility state are unchanged. No structure is downloaded or recomputed.

## Refreshed current state

Chemistry is 58 positive, 0 negative, 86 not established, and 856 unresolved. Positive source composition is runtime 17, FFQ 8, POA 16, G3H 8, and ONL 9. Task relevance is 59 relevant, 86 not relevant, and 855 unresolved: the 58 positive events plus one legacy partial task-relevant event. Training use is 29 include, 29 exclude-from-training-only, 86 not applicable, and 856 unresolved. Training exclusion is not negative chemistry, and ONL contributes nine excluded positives without increasing the include population.

The refreshed Exact11 presentation is:

- 273 `CURRENTLY_UNREVIEWED`
- 0 `CURRENTLY_IN_PROGRESS`
- 41 `COMPLETED_HUMAN_POSITIVE`
- 54 `COMPLETED_HUMAN_NEGATIVE`
- 1 `COMPLETED_PARTIAL_AUTHORITY`
- 17 `CURRENT_RUNTIME_MODEL_USABLE`
- 32 `PUBLISHED_EXACT_AUTO_NEGATIVE`
- 369 `LEAKAGE_EXISTING_GROUP_CONFLICT`
- 133 `STRUCTURAL_EVIDENCE_INCOMPLETE`
- 78 `QUARANTINE_REPRESENTATION_GAP`
- 2 `REJECTED_FEATURE_INCOMPATIBLE`

The 41 completed-human-positive and 17 current-runtime buckets are disjoint presentation buckets whose union is the 58 authoritative chemistry-positive events.

## Pair, role, mask, and geometry state

Raw structural pair evidence remains 865. Sample-level authoritative pair and role populations increase from 49 to 58 because ONL contributes nine published human pair/role decisions. ONL does not create a model-bound pair target or tensor integration, so the model-bound pair target population remains 41 and the current-runtime-bound population remains 17. All 58 positives have sample-level pair and role authority.

Role profiles are 31 `STRICT_LINKER_PRESENT_V1` and 27 `DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1`; ONL changes the direct population from 18 to 27. The other 942 rows remain unknown with `role_profile=NOT_ESTABLISHED` and structural applicability `null`, not an all-false list.

The canonical V1 mask contract remains exactly five semantic tasks:

1. `warhead_only` / A: 58 applicable authoritative roles
2. `linker_plus_warhead` / B: 31
3. `scaffold_plus_warhead` / B2: 31
4. `scaffold_only` / B3: 58
5. `scaffold_plus_linker_plus_warhead` / C: 58

There is no sixth task. The strict all-five population is 31; the direct A/B3/C population is 27.

Geometry is unchanged: POST source evidence 867, POST sample authority 21, and POST training targets 17. PRE source, sample authority, and training targets remain zero. This successor performs neither POST-to-PRE promotion nor PRE zero-fill or precursor reconstruction.

## Training state and blockers

Training remains non-ready. Include remains 29; future admission candidates remain 12 (FFQ 4 and POA 8); current runtime usable remains 17; formal admitted remains 5; and ready-for-formal-training events remain zero. Global materialization remains `NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY`.

The 17 positives missing model-bound pair/tensor integration are G3H 8 plus ONL 9, and all are training-excluded. This replaces the predecessor-only statement that every missing event was G3H. Other non-exclusive blockers are chemistry unresolved 856; pair and role authority absent 942 globally and zero within positives; human training exclusion 29 within positives; missing split 17 within positives and 4 within include; missing POST training authority 41 within positives and 12 within include; missing admission 53 within positives and 24 within include; and feature semantics pending for all 58 positives.

Step12D remains `SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT`. The historical `UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` issue still requires a future feature-semantics audit. This step is not that audit and does not establish training readiness.

## Human-review continuation

The current priority population contains 338 events in 131 units: 41 positive events in 4 units, 24 negative events in 4 units, 65 completed events in 8 units, and 273 unreviewed/pending events in 123 units. In-progress is zero.

The pending-unit ranking is recomputed from the full frozen 131-unit queue and refreshed reconciliation state, sorted by event count descending, raw priority rank ascending, then stable review-unit ID. The next unit is `COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58`: PRF, eight events, PDBs 3S19 and 3UXJ. The next recommended mainline is PRF Exact8 high-yield human-review expansion, but this census does not perform that decision.

## Validation and determinism

The public validator and repository-state-neutral checker independently verify the frozen predecessor/ONL SHA bindings, exact 1000-row identity and order, Exact9 overlay, 991 unchanged rows, exact set algebra, all refreshed counts, full-queue Top10, authority non-actions, and exact derived digests for the refreshed CSV, summary, and semantic-binding inventory. Those three digests close the deterministic derived projection; they are not authority. The manifest binds the candidate Exact4 source files, semantic inputs, CSV, and summary, and never records its own SHA256.

The Exact3 outputs are UTF-8, LF-only, single-final-LF, free of timestamps and machine-specific paths, byte-identical across two output directories, and each candidate file remains below 1 MiB.
