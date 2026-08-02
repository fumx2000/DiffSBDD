# CovaPIE repository CLI forwarding design V1

## Immutable runtime design baseline

This repository CLI document is an immutable design baseline, not a live runtime
gate. Its runtime/source evidence is read from Git commit
`f24d4bb1007986701d644c9ff3c94786b3872c21`, whose single parent and subject are
bound and which must remain an ancestor of both `HEAD` and `origin/main`.

Every mutable baseline source is read as a regular, nonempty, size-bounded Git
blob and checked against its frozen SHA256. The reads are local, network-free,
independent of the working tree and index, and do not checkout files, create a
worktree, or write to the repository. This freezes the six callers, model and
mask sources, dataset/checker, historical B3 boundary, negative-token test, and
legacy inventory as they existed before R1.

The four formal model-consumption gate files follow the same immutable rule.
Their frozen SHA256 values are read from gate commit
`dd085332c7e2cf58a6ca2e7d71cf022da010d4b4`, never from live successor bytes.
Snapshot-stability revisions to the gate source, tests, checker, or guide
therefore do not invalidate this historical repository CLI design evidence.

The baseline contains 14 active legacy-mask reference records across five
paths. Those values explain why R1/R2/R3 are required; they are not claims about
the live runtime after an implementation phase:

```text
design_evidence_mode=frozen_runtime_baseline_snapshot
design_checker_claims_live_runtime_state=false
baseline_reference_count=45
baseline_active_legacy_reference_count=14
baseline_active_legacy_reference_path_count=5
live_active_legacy_reference_count_claimed=false
legacy_four_level_retirement_selected=true
legacy_four_level_retirement_implemented=false
```

This step changes design evidence only. It does not remove a runtime API, change
a schema or dataset, modify a caller, run a model forward, or train a model.

## Final canonical target

The final active runtime has exactly five canonical tasks. Long semantic names
are the source of truth; internal long-form names are implementation mappings;
short aliases are derived only for human-readable reports.

| Canonical semantic | Generated target | Fixed context | Internal name | Report alias |
| --- | --- | --- | --- | --- |
| `warhead_only` | warhead | scaffold, linker | `A_warhead_only` | `A` |
| `linker_plus_warhead` | linker, warhead | scaffold | `B_linker_warhead` | `B` |
| `scaffold_plus_warhead` | scaffold, warhead | linker | `B2_scaffold_warhead` | `B2` |
| `scaffold_only` | scaffold | linker, warhead | `B3_scaffold_only` | `B3` |
| `scaffold_plus_linker_plus_warhead` | scaffold, linker, warhead | none | `C_scaffold_linker_warhead` | `C` |

Canonical B2 is `scaffold_plus_warhead`; canonical B3 is `scaffold_only`.
Historical B2 cannot be translated automatically because its short token lacks
enough provenance to distinguish an old four-level meaning from canonical B2.
There is no sixth or seventh task.

The target covalent-demo surface has only `--mask_semantic`, accepts only these
five long names, and uses `build_long_form_mask`. The short report aliases,
internal long-form names, unknown values, and the old `--mask_level` input fail
closed.

## What must reach zero

Full retirement means zero active legacy references, not zero textual mentions
throughout the repository. The R3 gate must eliminate active definitions,
imports, calls, registries, schema types, dataset keys/APIs, CLI options, CLI
choice sets, checker expectations, and current non-historical tests that require
positive legacy runtime behavior.

The active legacy surfaces include:

- `build_four_level_mask`;
- `MASK_BUILDERS`;
- `MaskType`;
- `mask_warhead`;
- `mask_linker_and_warhead`;
- `mask_scaffold`;
- `mask_whole_ligand`;
- `--mask_level` and short-token runtime choices.

The correct target is:

```text
target_active_legacy_reference_count=0
target_active_legacy_reference_path_count=0
historical_read_only_legacy_evidence_retained=true
```

## Baseline repository inventory

The design inventories the baseline commit tree with `git ls-tree`, baseline
`git grep`, and Git blob reads. It does not rediscover the old 45 records from a
changing R1/R2 working tree. Python references are classified with AST,
notebooks through JSON code-cell `source`, schemas through structured
inspection, and controlled text search for remaining evidence.

The frozen inventory contains 45 records:

- active runtime: 14;
- test-only: 7;
- documentation-only: 8;
- historical-freeze-only: 8;
- design-evidence-only: 8;
- unresolved active references: 0.

The five active paths and their retirement assignments are:

| Active path | Increment | Required action |
| --- | --- | --- |
| `scripts/covalent_inpaint_demo.py` | R1 | migrate the active demo consumer while the provider remains available |
| `src/covalent_ext/masking.py` | R2 | remove the legacy core builder, registry, and wrappers |
| `src/covalent_ext/schema.py` | R2 | replace the short-token schema with canonical long semantics |
| `src/covalent_ext/dataset.py` | R2 | migrate dataset mask APIs and keys while removing its provider imports |
| `scripts/check_covalent_masking.py` | R2 | check the canonical five-level runtime contract |

Every active record has a future action and belongs to R1 or R2. Test-only
positive legacy references move in R2. The negative-token rejection evidence
in `tests/test_real_covalent_feature_mapping_loader_gate_v0.py` has no
retirement increment and remains unchanged. That complete scope makes the
design ready to start R1, but neither R2 nor CLI forwarding is ready yet.

## Design-file and future-task Git lifecycle

The first design run occurs before the four design files have been committed,
so all four are ordinary-untracked files. After the design commit, those same
paths are tracked and the ordinary-untracked count normally changes from four
to zero. A later successor revision keeps the paths tracked while modifying
their working-tree contents. None of these normal transitions changes which
repository evidence the inventory must scan.

The lifecycle check accepts exactly three mutually exclusive profiles:

- `initial_design_precommit`: all four design paths are untracked, none are tracked,
  and they are the complete ordinary-untracked set;
- `design_successor_worktree`: all four design paths are tracked, none are
  untracked, and the ordinary-untracked set is empty.
- `published_design_with_known_future_task`: all four design paths are tracked,
  and ordinary-untracked paths are a nonempty subset of exact new paths declared
  by R1, R3, C1, or C4 contracts.

The known set includes the R1 demo mask test, the four R3 gate paths, the C1
helper/test paths, and the four C4 gate paths. A future R1 candidate containing
only `tests/test_covalent_inpaint_demo_mask_semantic_v1.py` is therefore valid.
An unknown path such as `scratch.txt` still fails closed.

Binding the design permanently to the first profile would make a valid commit
impossible to revalidate. The lifecycle helper instead reads both Git path sets
and fails closed for partial tracked/untracked mixtures, a missing design path,
the same design path appearing in both sets, an unknown ordinary-untracked path,
or any symlink/non-regular design or future path. Future task files do not enter
the inventory because that evidence always comes from the baseline commit tree.

This dependency-order revision keeps the Exact43 top-level field count and
order unchanged. It changes only the permitted nested contracts and the
top-level recommended next step, so the canonical Exact43 digest is recomputed.

## Historical evidence boundary

Historical Git commits, formal predecessor bundles, derived historical reports,
explicit freeze scripts/tests, explanatory documentation, and design inventory
evidence may retain old terminology. Those paths are explicitly classified and
read-only. At the target state they are not active runtime, callable runtime
interfaces, admissible schema/training values, or automatic translations.

Therefore the project cannot and should not promise that every text occurrence
of `B2` or `build_four_level_mask` disappears. Broad rules such as “ignore all
docs” or “ignore all data” are forbidden. The gate uses exact paths or explicit
frozen-artifact categories and proves that each allowed trace is non-active.

## Retirement increments

### Design versus implementation gates

The repository CLI design proves why the ordered R1/R2/R3 work and their
contracts are necessary. It deliberately does not prove a later live phase has
finished. R1 tests/checker must prove the demo canonical five-level migration;
R2 tests/checker must prove the old core API is removed and remaining consumers
are migrated; only R3 may prove the live active legacy count is zero.

Consequently R1 is allowed to change the live demo SHA and remove its old
builder import/call/flag without invalidating this design. The baseline demo SHA
remains evidence about the pre-R1 snapshot. After R1 commits, the next live step
is selected by the R1 phase checker, not by this older design checker.

### Provider and consumer dependency

A provider defines an interface; a consumer imports or calls it. Here,
`src/covalent_ext/masking.py` provides `build_four_level_mask`. The active demo
imports that symbol and calls it once, and its parser defines `--mask_level`
with `A/B/B2/C` choices. The dataset also imports and calls the builder, while
the checker consumes `MASK_BUILDERS` and iterates the same four choices. These
facts are parsed from Python AST and source; the design does not write the
readiness booleans without checking those facts.

The former order deleted the provider in R1 and migrated the demo consumer in
R2. The R1 commit would therefore leave the demo importing a symbol that no
longer exists. Importing the demo would fail with `ImportError`, so that commit
could not be treated as an independently runnable main state. Provider removal
before consumer migration is consequently unsafe.

### R1: migrate only the active demo mask surface

R1 is
`implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1`.
It changes only `scripts/covalent_inpaint_demo.py` and the new focused demo mask
test. It replaces the old builder with `build_long_form_mask`, removes the old
flag and four short choices, and adds the single `--mask_semantic` input with
the five canonical long names. Short aliases, internal implementation names,
unknown/empty/non-string masks, and the removed flag must fail closed.

R1 does not modify the provider, schema, dataset, or checker. It also does not
add target-residue CLI arguments, change checkpoint loading, or execute a model
forward. Its permitted status is:

```text
covalent_demo_canonical_mask_surface_migrated=true
legacy_four_level_demo_consumer_removed=true
legacy_four_level_core_provider_still_present=true
legacy_four_level_core_api_retired=false
legacy_four_level_full_runtime_retired=false
R2_still_required=true
R3_gate_still_required=true
```

This intermediate commit remains runnable because the demo no longer imports
the old provider, while the provider remains for the dataset and checker.

### R2: remove the core provider and remaining consumers

R2 is `implement_covapie_legacy_four_level_core_api_retirement_r2_v1`. Only
after committed R1 has removed the demo dependency may R2 delete the legacy
core provider, schema, dataset API, and checker interfaces and migrate the
remaining positive legacy-behavior tests. The canonical `LongFormMaskLevel`,
`LONG_FORM_MASK_COMPONENTS`, `build_long_form_mask`, and all five long semantics
remain. The dataset returns exactly the five canonical tasks and the checker
validates that contract.

The R2 commit remains runnable because provider deletion and migration of every
remaining active provider consumer occur together. R2 can report a zero-active
candidate, but it still cannot declare full retirement; only R3 can do that.

The historical B3 implementation module and its historical checker remain
read-only and are not modified to follow the current runtime. Once the old core
API is gone, that historical module is explicitly non-active and need not be
importable. Its current test must stop importing it or running its checker,
preserve history through frozen bytes/SHA or reports, and independently verify
canonical B2 and B3 through `build_long_form_mask`.

Negative legacy-token tests are different from positive legacy runtime
dependencies. The real-feature mapping loader test keeps `B3`, `B2`,
`mask_scaffold`, and `legacy_short_B2` specifically as rejected inputs. R1 and
R2 leave that test unchanged; deleting those strings would destroy negative
evidence rather than advance retirement.

### R3: formal zero-active-reference gate

R3 requires both active and unresolved counts to be zero. It independently
proves that the legacy builder is not importable or callable by active runtime,
the old schema type and CLI flag are absent, short tokens are not runtime inputs,
and the canonical five-level runtime is complete.

Its scan covers all tracked Python, current non-historical tests, active scripts,
Notebook JSON code-cell source, schema/type aliases, imports, definitions, calls,
registries, CLI definitions/choices, short-token string comparisons, and dataset
keys/APIs. It combines Python AST, notebook-source AST, structured schema
inspection, and controlled text search. Historical allowances use an exact
whitelist and cannot be broad directory ignores.

R3 must pass and be committed before any CLI-forwarding implementation begins.

## Required total order

The work is split across independent increments and gates:

1. R1 — migrate the active covalent-demo mask consumer to canonical five-level semantics.
2. R2 — remove the legacy core provider/interfaces and migrate remaining consumers/tests.
3. R3 — formal zero-active-legacy-reference retirement gate.
4. C1 — implement the central target-residue CLI helper.
5. C2 — forward `generate_ligands.py`.
6. C3 — forward the target selector through the covalent demo.
7. C4 — formal repository CLI forwarding gate.

C1 must not start before the committed R3 gate. The immediate next step is
`implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1` as
the baseline design recommendation. It is not a perpetual live-state claim.

## Target-selector exact bool

`target_residue_atom_conditioning` accepts only a missing flag, exact `False`,
or exact `True`; its type must be exactly `bool`. Values `0`, `1`, `None`, string
booleans, and scalar tensors fail closed. Conditioned mode requires an already
stripped, nonempty chain plus an exact integer residue number that is not a
boolean. Empty, whitespace-only, padded, or tab-prefixed chains are rejected,
not automatically trimmed.

## Checkpoint and training boundary

Retirement changes mask API/schema/task semantics, not model architecture or
checkpoint parameter shapes, so checkpoint compatibility is unchanged. The
real-checkpoint design smoke still constructs
the conditioned model, fills exactly one zero-initialized in-memory parameter,
and finishes with strict loading and no missing or unexpected keys. The input
mapping, tensors, and checkpoint bytes remain unchanged.

Current design state is:

```text
design_evidence_mode=frozen_runtime_baseline_snapshot
runtime_design_baseline_commit=f24d4bb1007986701d644c9ff3c94786b3872c21
design_baseline_snapshot_immutable=true
design_checker_claims_live_runtime_state=false
implementation_phase_live_state_requires_phase_specific_gate=true
recommended_next_step_is_design_baseline_recommendation=true
R1_candidate_will_not_invalidate_design_tests=true
legacy_four_level_retirement_selected=true
legacy_four_level_retirement_implemented=false
retirement_dependency_order_valid=true
ready_for_covalent_demo_canonical_mask_migration_R1=true
ready_for_legacy_core_api_retirement_R2=false
ready_for_repository_cli_forwarding_implementation=false
recommended_next_step=implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1
repository_cli_selector_forwarding_implemented=false
training_or_parameter_update=false
feature_semantics_audit_required_before_training=true
```

No retirement implementation, CLI forwarding, model forward, training,
fine-tuning, backward pass, optimizer step, parameter update, or checkpoint save
occurs here. Formal training still requires a feature-semantics audit and
resolution or formal audit of `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False`. Step12D was only a smoke legality check, not a
final training-feature contract, so none of this design evidence establishes
training readiness.
