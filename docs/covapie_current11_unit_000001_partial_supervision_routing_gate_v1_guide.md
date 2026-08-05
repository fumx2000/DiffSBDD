# CovaPIE Current11 unit 000001 partial-supervision routing gate v1

This increment is a deterministic, read-only, metadata-only gate for
`CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001`. It answers which of
25 semantic supervision tasks have usable evidence for exactly two samples:

1. `CYS_SG_SAMPLE_INDEX_000008` / `1AYU` / `INA`
2. `CYS_SG_SAMPLE_INDEX_000010` / `1AYW` / `IN3`

It does not change a schema, formal worklist, dossier, authority, dataloader,
model, forward path, loss, tensor, checkpoint, or training state.

## Public API

```python
evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, object]
```

The function is keyword-only, silent on import, stdlib-only, and fail-closed.
It accepts no sample list, eligibility override, default authority, default
bond order, or external policy. Exact2 samples and Exact25 tasks are frozen by
the gate contract.

## Evidence boundary

The evaluator verifies frozen SHA256 bindings and recomputes its routing from
direct evidence:

- official `1ayu.cif` and `1ayw.cif` `covale1` records identify CYS SG to
  ligand C21 while `_struct_conn.pdbx_value_order` remains `?`;
- the canonical pair matrix requires `validated_struct_conn`, and both pocket
  and ligand mappings must independently be exact-one;
- observed pair tables provide 1.799 and 1.794 angstrom distances, scoped only
  to observed-complex geometry;
- unified human-reviewed authority provides an active warhead atom set and
  exactly two ligand-internal boundaries per sample, but no complete,
  mutually exclusive scaffold/linker/warhead partition;
- family, rule, and warhead-type assignments remain machine-derived
  candidates, while the formal approval/full-semantics fields remain blank;
- primary-literature inventory records are projected by compound and state.
  Compound-4 evidence is not propagated to compound 8, class scope is not
  promoted to sample-complete scope, and solution state is not merged with
  crystallographic state;
- the transformation worklist remains one row with frozen Exact16 and blank
  Exact25. Blank remains distinct from an explicit empty list, `not_claimed`,
  `false`, and a negative label;
- the canonical mask truth table contains exactly the five long semantics
  `warhead_only`, `linker_plus_warhead`, `scaffold_plus_warhead`,
  `scaffold_only`, and `scaffold_plus_linker_plus_warhead`, with display aliases
  A, B, B2, B3, and C. `scaffold_only` / B3 is mandatory.

The routing audit report is SHA-bound context only. Its summary is not used as
the producer of the 50 routing states.

## Routing semantics

Each sample has four `admissible_now` tasks: sample identity, explicit binary
covalent event, ligand-residue atom pair, and warhead boundary. Each has one
`admissible_as_observed_geometry_only` task. Candidate evidence is kept
separate from authority, missing evidence is kept separate from state
ambiguity, and all five canonical mask tasks remain
`blocked_missing_human_approval` until complete primary-role authority exists.

The sample-specific differences are:

- sample 000008: broken edge and reversibility are
  `candidate_only_not_authoritative`;
- sample 000010: broken edge is `blocked_state_ambiguity`, and reversibility is
  `blocked_missing_evidence`.

Across Exact2 x Exact25, the counts are 8 `admissible_now`, 2 observed-geometry
only, 10 candidate-only, 13 blocked for missing evidence, 7 blocked for state
ambiguity, 10 blocked for missing human approval, and 0 not-applicable.

Every routing record requires a future independent availability mask. Every
record also states `current_runtime_consumer_available=false` and
`training_loss_authorized=false`. Evidence-level admissibility does not imply
loader integration, a model head, a runnable loss, parameter-update authority,
or training readiness. Checkpoint compatibility impact is
`none_metadata_only_gate`.

## Checker

```bash
python -B scripts/check_covapie_current11_unit_000001_partial_supervision_routing_gate_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

Success returns rc 0, empty stderr, and one canonical JSON line on stdout using
sorted keys and compact separators. Failure returns rc 1, empty stdout, and
`COVAPIE_CURRENT11_UNIT_000001_PARTIAL_SUPERVISION_ROUTING_GATE_V1_ERROR` on
stderr. The checker has no output, materialization, approval, write, or training
option.

## Lifecycle and readiness

The same runtime recognizes exactly three repository lifecycle profiles:

1. `partial_supervision_routing_gate_precommit_candidate`
2. `partial_supervision_routing_gate_committed_unpushed`
3. `partial_supervision_routing_gate_published_successor`

The base is `74afd2c5c8465550eff77b88afe85dd57835d143`; the future formal subject is
`add CovaPIE Current11 partial supervision routing gate v1`.

This increment sets `partial_supervision_routing_gate_implemented=true` and
`ready_for_partial_supervision_gate_validation=true`. Tensor materialization,
dataloader integration, model integration, formal worklist update, semantic
validation, and training readiness all remain false. A feature-semantics
re-audit remains mandatory before training: Step12D was a smoke legality check,
not a final training-feature contract, and the historical
`UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False` state must be
resolved or formally audited first.
