# Current11 multi-boundary authority materialization precondition and unified precedence design v1

## Current stage

This design follows durable no-clobber materialization of the Current11
multi-boundary ingestion execution receipt. It validates, in memory, whether
the existing execution evidence is sufficient for two later and separate
implementation stages:

1. a durable multi-boundary authority bundle; and
2. a derived unified effective-authority view.

This stage does not materialize either output. The module is a private design
artifact with `__all__ = ()`; it exposes no production materializer API and
writes no files.

## Frozen authority namespaces

The source authorities remain in two distinct namespaces:

- `legacy_exact_one_boundary_v1` contains the 11 legacy V1 authority records;
- `exact_two_boundaries_multi_boundary_v1` contains exactly the five
  multi-boundary authority records for samples `000006` through `000010`.

The legacy namespace is immutable. Its records are neither edited nor deleted,
and they are not marked as source-level superseded. The new namespace preserves
the same-sample backlink to the legacy V1 quarantine authority and review.

The unified result is only a derived resolution view. It does not rewrite either
source namespace.

## Deterministic precedence

The effective profile is six legacy exact-one authorities plus five
multi-boundary exact-two authorities:

- samples `000001` through `000005` select the active legacy exact-one
  authority with reason `ACTIVE_LEGACY_EXACT_ONE_ONLY`;
- samples `000006` through `000010` select the active exact-two authority over
  the quarantined exact-one record with reason
  `ACTIVE_EXACT_TWO_SELECTED_OVER_QUARANTINED_EXACT_ONE_FOR_EFFECTIVE_VIEW`;
- sample `000011` selects the active legacy exact-one authority with reason
  `ACTIVE_LEGACY_EXACT_ONE_ONLY`.

For `000006` through `000010`, selection of exact-two evidence does not delete,
modify, unquarantine, or source-level-supersede the V1 record. The V1 quarantine
remains historical source evidence; the derived view applies the frozen
precedence rule.

The design fails closed on incomplete or duplicate Current11 coverage, sample
order drift, unexpected or missing multi-boundary authorities, source digest or
lineage drift, invalid legacy quarantine or multi-boundary active state,
same-sample predecessor backlink drift, unresolved active-active ambiguity, or
any outcome that selects other than exactly one effective authority per sample.

## Scope and readiness

The in-memory reference evaluator produces 11 Exact12 resolution records and
one Exact10 design response. It validates exact bytes, execution digests,
record linkage, namespace state, source immutability, and the 6+5 effective
profile. A successful response establishes only the precondition for later
authority-bundle and unified-view implementation.

This stage:

- does not create an authority JSON or CSV;
- does not create unified gold or human gold;
- does not create training labels, SMARTS, or masks;
- does not modify legacy V1 authority or either execution receipt;
- does not run ingestion, training, backpropagation, optimization, or parameter
  updates.

The canonical mask contract remains exactly:

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

This design evidence must not be used for training. Formal training still
requires a feature-semantics audit, including resolution or formal audit of the
historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state. Step12D remains only a smoke legality
check, not a final training-feature contract.

## Only recommended next step

`implement_covapie_current11_multi_boundary_authority_bundle_v1`
