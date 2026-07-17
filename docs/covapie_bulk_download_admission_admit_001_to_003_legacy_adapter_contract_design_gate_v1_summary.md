# CovaPIE Step14AU-E1-E4 Phase 3 summary

This design gate freezes the future unified-admission adapter contracts for
`ADMIT_001`, `ADMIT_002`, and `ADMIT_003`. It does not implement an adapter,
execute a legacy evaluator, or modify the Phase 2 dispatch runtime. The Phase 2
registry remains exactly `ADMIT_004`.

The revised1 increment closes five review gaps in the original design evidence:
exact dispatch-error reasons, legacy value-consistency invariants, complete
adapter-side invalid result payloads, an explicit global execution precedence,
and unambiguous singleton-tuple text. It changes design metadata only.

The final revised2 semantic increment closes the remaining gap: an allowed
reason and a plausible canonical shape do not prove that a legacy result is
correct for the original candidate and caller context. A future adapter must
recompute the expected legacy dictionary with the corresponding frozen pure
semantic oracle and require exact field-by-field equality before mapping an
outcome or constructing a unified result.

## Frozen source boundary

The gate reads exactly 16 committed sources in a fixed order. Every source must
be tracked, a blob in base commit
`dfa3dbf06046b6db3b05f15a7dec79b96db61106`, a regular non-symlink filesystem
entry, and byte-identical to its expected SHA256 in both the base tree and the
filesystem. All 16 structural checks finish before the first source-byte read.
AST, CSV, and JSON parsing use only the resulting `FrozenSourceSnapshot`; linked
artifact references are not followed.

The three newly frozen committed-example SHA256 values are:

- candidate-record examples: `1654d36a42cd405866ed152750508dbc46ed78371b7ebb25e47e8bfe9c8bbb9e`
- PDB-identifier examples: `35ea09ae36ddf2311b1dcf5a313d18e62888c68e542eb068bd98c04900379ce9`
- ligand-component examples: `64a5ef19ceb0d37f37af65a5638d844e33de997ccfa3af4df61de0779ab75af6`

## Legacy schemas and adapter identities

The legacy callables and exact ordered result keys are:

- `ADMIT_001`: `evaluate_admit_001_candidate_record_id` →
  `admission_rule_id|passed|normalized_candidate_record_id|blocking_reason`;
  adapter `covapie_admit_001_unified_adapter_v1`; outcomes
  `passed|blocked|invalid`.
- `ADMIT_002`: `evaluate_admit_002_pdb_identifier` →
  `admission_rule_id|passed|canonical_pdb_id|input_form|blocking_reason`;
  adapter `covapie_admit_002_unified_adapter_v1`; outcomes `passed|invalid`.
- `ADMIT_003`: `evaluate_admit_003_ligand_comp_id` →
  `admission_rule_id|passed|canonical_ligand_comp_id|blocking_reason`;
  adapter `covapie_admit_003_unified_adapter_v1`; outcomes `passed|invalid`.

A future adapter must require an exact `dict`, the exact ordered keyset, the
corresponding exact rule ID, exact `bool` for `passed`, and exact `str` for every
declared string field. A passed result has an empty reason; a failed result has
a nonempty reason. Malformed results and unknown nonempty reasons fail closed as
`UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY`, with no partial unified result and
no guessed outcome. PDB `input_form` is an adapter invariant only and is not
projected into a unified result field.

The exact adapter failure reasons are frozen per rule as
`ADMIT_NNN_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID`,
`ADMIT_NNN_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID`, and
`ADMIT_NNN_UNIFIED_ADAPTER_REASON_UNMAPPED`. All three categories raise
`UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY` and return no unified result.

Value consistency is also explicit. ADMIT_001 requires a passed or blocked
normalized ID to equal the original candidate ID, while syntax-invalid results
must have an empty normalized ID. ADMIT_002 requires passed canonical IDs to
match `^pdb_[a-z0-9]{8}$` with one of the two accepted input forms; invalid
results have empty canonical ID and `input_form=invalid`. ADMIT_003 requires a
passed canonical value to equal the uppercase exact-string input and match
`^[A-Z0-9]{1,32}$`; invalid results have an empty canonical value. In every
rule, legacy `passed` must agree with the mapped outcome.

The frozen pure semantic oracles are:

- ADMIT_001: `evaluate_candidate_record_id_batch_uniqueness`, called with the
  original candidate-record ID and original batch ID collection.
- ADMIT_002: `normalize_pdb_identifier`, called with the original PDB ID. Its
  `isinstance(value, str)` behavior, including string subclasses, remains the
  source of truth.
- ADMIT_003: `normalize_ligand_comp_id`, called with the original ligand
  component value.

Each oracle has an exact expected-legacy-result projection in the adapter
contract matrix. Equivalence is required for all three rules. The legacy
evaluator itself is not an oracle; runtime CSV/JSON lookup and inference from a
reason set are forbidden. A mismatch is a source-invariant failure using
`UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY` and the rule-specific
`*_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID` reason. The future adapter may not
correct the legacy result and continue, and it may not return a partial result.

## Projection and context boundary

Candidate records accept `Mapping` instances and subclasses. A non-mapping or
missing required field produces an adapter-side `invalid` rule result and does
not call the legacy evaluator. When present, the original field value object is
passed unchanged: no trimming, coercion, normalization, or copying. Extra
candidate fields are not passed and the candidate is not mutated.

Both adapter-side invalid paths now have complete frozen
`UnifiedAdmissionRuleEvaluation` payloads: schema/rule identity, `invalid`,
`passed=false`, `blocks_candidate=true`, the exact projection reason, empty
normalized and validated tuples, exact consumed candidate/context tuples,
`evaluator_io_used=false`, the exact adapter ID, and no legacy call.

Singleton tuple text is unambiguous: `("candidate_record_id",)`,
`("batch_candidate_record_ids",)`, `("pdb_id",)`, and
`("ligand_comp_id",)`. Empty consumed context remains `()`.

`candidate_record_id_contract`, `pdb_id_format_contract`, and
`ligand_comp_id_contract` are static policy dependencies frozen through source
SHA and future adapter implementation. They are not caller-provided record
evidence. Runtime `evaluation_context` is therefore `None` for all three rules;
the engine may neither load these policies dynamically nor fabricate policy
context. The only consumed caller context is
`ADMIT_001`'s `batch_candidate_record_ids`.

For `ADMIT_001`, context validation order is batch mapping, key presence, exact
list/tuple, nonempty, member syntax, evaluation context, download context, and
stage context. For `ADMIT_002` and `ADMIT_003`, order is batch, evaluation,
download, and stage; each must be `None`. Rule-ID and registration checks occur
first. Context failures use `UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID` and do
not call a legacy evaluator.

The routing matrix freezes all 16 context branches with their rule-specific
dispatch reason. It also contains one explicit `execution_precedence` row per
rule: rule-ID; known/registered/adapter-ready; contexts; candidate Mapping;
required field; legacy call; exact result shape; semantic invariants; reason
mapping; unified-result construction. Thus registration failure precedes
context failure, context failure precedes candidate projection failure, and
adapter failures cannot return partial results. The revised routing/projection
matrix has exactly 74 rows and includes the `dispatch_error_reason` column.
Step 8 specifically covers both legacy semantic invariants and semantic-oracle
equivalence; the sequence remains exactly 10 steps.

## Reason mapping and issues

The reason matrix has exactly 23 passing rows in fixed order: 9 for
`ADMIT_001`, 8 for `ADMIT_002`, and 6 for `ADMIT_003`. The three legacy
batch-shape reasons handled by future context prevalidation are deliberately
absent from the adapter mapping.

The Phase 2 issue inventory remains at 12 active issues. In the same position,
`UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED` is replaced by
`UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING`. The other
11 rows are unchanged, including the provider blocker count of 11, incomplete
rule coverage, and unresolved cross-rule aggregation.

## Readiness boundary

The contracts are ready for the next implementation step:
`implement_covapie_unified_admission_legacy_adapters_and_register_admit_001_to_003_v1`.
The adapters are not implemented and `ADMIT_001`–`ADMIT_003` are not registered.
There is no all-rules evaluator, combined candidate verdict, cross-rule
precedence, real candidate evaluation, Exact11 evaluation, download permission,
or training readiness. Formal training still requires the feature-semantics
audit; Step12D remains only a smoke legality check, not a final training-feature
contract, and historical unknown feature semantics must be resolved or formally
audited first.

This design gate still neither implements nor executes a runtime adapter, and
it does not execute any legacy evaluator.
