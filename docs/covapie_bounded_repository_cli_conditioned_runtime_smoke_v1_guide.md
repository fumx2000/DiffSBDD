# CovaPIE bounded repository CLI conditioned runtime smoke V1

This increment is terminalized. The one-time bounded runtime-smoke execution
authorization was consumed by exactly one execution, and that execution failed
closed. There was no automatic retry and no second execution is authorized.
The implementation still consists of only the production module, targeted
tests, checker, and this guide; no tracked runtime or training source changed.

## Terminal execution result

The frozen result is:

- `one_time_execution_authorization_consumed=true`
- `bounded_runtime_smoke_execution_count=1`
- `bounded_runtime_smoke_passed=false`
- `automatic_retry_performed=false`
- `architecture_expansion_authorized=false`
- `exact67_runtime_evidence_available=false`
- `ready_for_one_time_bounded_runtime_smoke_execution=false`
- `reexecution_requires_new_explicit_user_authorization=true`

The checker returned 1 and its single child returned 1 without timing out.
No Exact67 evidence was produced: its field count and byte count are both zero,
and its SHA256 is `None`.

The first fail-closed stage was
`child_internal_stderr_gate_before_exact67_evidence`. A `UserWarning` was
observed during the child import stage with the exact message:

```text
"import openbabel" is deprecated, instead use "from openbabel import openbabel"
```

This is an OpenBabel-related deprecation warning observed at the child import
boundary. The evidence does not prove that any particular line in
`generate_ligands.py` directly emitted it. It proves only that the strict
stderr gate was triggered before Exact67 evidence became available. Therefore
this result does not establish a model runtime failure or a conditioned
plumbing failure. The reviewed root-cause severity is low relative to a model
or conditioned-plumbing runtime defect: the observed blocker was the strict
import-stage stderr policy, while the underlying runtime path remains unproven.

## Closed execution surfaces

The repeatable default checker remains static only:

```bash
python -B scripts/check_covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py
```

It validates the published design, the frozen runtime-source snapshot, the
checkpoint identity without deserializing it, all four implementation-file
identities, and the terminal Exact36 response. It does not construct a model,
run a forward, invoke `generate_ligands.py`, start the smoke child, or create a
runtime workspace.

The checker still recognizes `--execute-once`, but that flag now immediately
raises:

```text
COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_EXECUTION_AUTHORIZATION_CONSUMED
```

The public execute API is independently guarded by the same consumed state and
error. Its guard runs before the static evaluator, Git queries, checkpoint
reads, workspace creation, child-command construction, subprocess launch,
Torch import, or file writes. The checker is not the sole replay barrier.

## Repository lifecycle

The static evaluator is lifecycle-neutral across four repository situations:

- `terminal_precommit_candidate`: the exact four files are ordinary untracked
  files on the published design commit;
- `terminal_committed_unpushed`: one exact terminal commit is HEAD, one commit
  ahead of `origin/main`;
- `terminal_published_successor`: the exact terminal commit is published;
- a future unrelated successor: the terminal commit remains an ancestor of
  both HEAD and `origin/main`, and its four files retain the committed bytes.

The frozen future commit subject is
`record CovaPIE bounded repository CLI conditioned smoke terminal result v1`.
Its parent must be the published design commit, its body must be empty, it must
have one parent, and it must add exactly these four mode-`100644` files. The
evaluator fails closed for parent, subject, body, path, mode, blob, live-byte,
or terminal-file drift and for multiple matching terminal commits.

The published design-response SHA is retained as historical snapshot evidence.
The current design response is independently canonicalized and may acquire a
different SHA when HEAD or `origin/main` advances. The two SHA values are not
required to remain equal. This terminal implementation remains Exact36 in all
supported lifecycle profiles.

Any future re-execution requires new explicit user authorization. Before such
authorization is exercised, warning classification must be reviewed as a
separate task. A future policy must not silently discard the warning, move it
to stdout, weaken the zero-stderr contract, or add an unreviewed warning
suppression.

## Frozen source and safety evidence

The execution record distinguishes the four source identities actually used by
the one execution from the four current terminalized source identities. The
executed identities remain bound to the pre-terminalization SHA256 values; the
current identities are computed from the terminalized files and are not
misrepresented as executed bytes.

The frozen safety result records:

- checkpoint unchanged, including size 17,861,341 bytes and SHA256
  `07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c`;
- Git unchanged;
- temporary workspace device 66,307 and inode 7,380,511,365 matched the cleanup
  guard, was removed, does not remain, and no competitor path was deleted;
- no training or parameter update, no RL implementation, no commit, and no
  push.

No repository PDB, SDF, evidence JSON, runtime log, checkpoint copy, model dump,
or tensor dump belongs to this terminalization.

## Claim boundary and next mainline

This terminal result does not establish training readiness. It also does not
establish five-module completion, feature-semantics readiness, chemical
quality, conditioned plumbing failure, model runtime failure, covalent demo
completion, or RL readiness.

Before any training or training-preparation work, the feature-semantics audit
remains mandatory. Step12D was a smoke legality check, not a final
training-feature contract. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state remains unresolved until formally
audited.

The next mainline is
`audit_covapie_five_module_training_path_completion_gaps_v1`. That audit is not
started by this terminalization.
