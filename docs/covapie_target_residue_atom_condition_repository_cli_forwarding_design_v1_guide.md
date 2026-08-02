# CovaPIE repository CLI forwarding design V1

## Current state is not the retirement target

The repository currently contains 14 active legacy-mask reference records across
five active paths. Choosing to retire those interfaces is a design decision; it
does not mean the live runtime has already been changed. Consequently this
design records:

```text
legacy_four_level_retirement_selected=true
legacy_four_level_retirement_implemented=false
current_active_legacy_reference_count=14
current_active_legacy_reference_path_count=5
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

## Current repository inventory

The design audits all tracked repository paths plus the exact four design files.
Python references are classified with AST, notebooks through JSON code-cell
`source`, schemas through structured inspection, and controlled text search for
the remaining evidence.

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
| `src/covalent_ext/masking.py` | R1 | remove legacy core builder, registry, and wrappers |
| `src/covalent_ext/schema.py` | R1 | replace the short-token schema with canonical long semantics |
| `src/covalent_ext/dataset.py` | R1 | migrate dataset mask APIs and keys |
| `scripts/check_covalent_masking.py` | R1 | check the canonical five-level runtime contract |
| `scripts/covalent_inpaint_demo.py` | R2 | remove the final active legacy CLI dependency |

Every active record has a future action and belongs to R1 or R2. Test-only
references are assigned according to the runtime surface they validate. That
complete scope makes the design ready to begin retirement implementation, but
does not make CLI forwarding ready.

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

### R1: core API, schema, dataset, and checker

R1 removes the legacy four-level core runtime interfaces in `masking.py`,
`schema.py`, and `dataset.py`, migrates `scripts/check_covalent_masking.py`, and
updates related current tests. R1 may report:

```text
legacy_four_level_core_api_retired=true
legacy_four_level_full_runtime_retired=false
```

It cannot claim full retirement because the covalent demo remains for R2.

### R2: final active CLI caller

R2 migrates `scripts/covalent_inpaint_demo.py` and related tests. It removes
`--mask_level`, adds only `--mask_semantic`, accepts only the five long names,
rejects `A/B/B2/B3/C` as input, and uses `build_long_form_mask`. Even after R2,
full retirement remains a candidate conclusion until R3 independently proves
zero active residuals.

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

1. R1 — implement core legacy four-level mask retirement.
2. R2 — migrate the final active covalent-demo mask surface.
3. R3 — formal zero-active-legacy-reference retirement gate.
4. C1 — implement the central target-residue CLI helper.
5. C2 — forward `generate_ligands.py`.
6. C3 — forward the target selector through the covalent demo.
7. C4 — formal repository CLI forwarding gate.

C1 must not start before the committed R3 gate. The immediate next step is
`implement_covapie_legacy_four_level_mask_retirement_v1`.

## Target-selector exact bool

`target_residue_atom_conditioning` accepts only a missing flag, exact `False`,
or exact `True`; its type must be exactly `bool`. Values `0`, `1`, `None`, string
booleans, and scalar tensors fail closed. Conditioned mode requires an already
stripped, nonempty chain plus an exact integer residue number that is not a
boolean. Empty, whitespace-only, padded, or tab-prefixed chains are rejected,
not automatically trimmed.

## Checkpoint and training boundary

Retirement changes mask API/schema/task semantics, not model architecture or
checkpoint parameter shapes. The real-checkpoint design smoke still constructs
the conditioned model, fills exactly one zero-initialized in-memory parameter,
and finishes with strict loading and no missing or unexpected keys. The input
mapping, tensors, and checkpoint bytes remain unchanged.

Current design state is:

```text
legacy_four_level_retirement_selected=true
legacy_four_level_retirement_implemented=false
ready_for_legacy_four_level_mask_retirement_implementation=true
ready_for_repository_cli_forwarding_implementation=false
recommended_next_step=implement_covapie_legacy_four_level_mask_retirement_v1
repository_cli_selector_forwarding_implemented=false
training_or_parameter_update=false
feature_semantics_audit_required_before_training=true
```

No retirement implementation, CLI forwarding, model forward, training,
fine-tuning, backward pass, optimizer step, parameter update, or checkpoint save
occurs here. Formal training still requires a feature-semantics audit and
resolution or formal audit of `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False`.
