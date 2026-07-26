# CovaPIE shared hermetic Git lifecycle harness V1

This increment adds one reusable test-infrastructure harness for CovaPIE Git
lifecycle checks. It does not modify any committed runtime, checker, business
test, or historical evidence. It performs no provider access, network access,
download, raw-data access, model or checkpoint access, dataloader work,
forward/loss/backward execution, optimization, parameter update, or training.

## Public API and explicit BASE

The only public lifecycle operation is:

```python
exercise_hermetic_git_lifecycle_matrix(
    source_repository,
    workspace_root,
    *,
    base_commit,
    formal_commit_subject,
    exact_paths,
)
```

`base_commit` is mandatory and must be exactly 40 lowercase hexadecimal
characters. There is no fallback from ambient `HEAD`, `main`, or
`origin/main`. The harness pushes only that explicit commit to
`refs/heads/main` in a temporary bare remote, sets the remote HEAD to
`refs/heads/main`, and clones only from that temporary bare remote.

The exact-path input is a nonempty exact tuple; lists and tuple subclasses are
rejected. Paths must be unique, relative, nonempty, free of `..` and `.git`,
and use no forbidden artifact suffix. Each source leaf must be a regular,
non-symlink, non-executable file that is absent from the explicit BASE.

## Exact4 lifecycle matrix

The harness constructs and validates:

1. `pre_commit`: a one-worktree main clone at BASE, with every exact path
   untracked and nothing staged.
2. `detached_candidate_post_commit`: a real second detached worktree whose
   candidate parent is BASE, while main and origin/main remain at BASE.
3. `formal_main_post_commit_unpushed`: an independent one-worktree clone whose
   main is one commit ahead of origin/main.
4. `formal_main_post_push`: the same formal clone after an ordinary local Git
   push, with main, origin/main, and resolved origin/HEAD at the candidate.

Both independent candidate commits use controlled local identity and commit
dates and must have the same OID. Candidate parent, exact subject, exact
changed-file inventory, and `100644` modes are checked directly. Extra refs,
branches, tags, files, worktrees, staging residue, mode drift, and
origin/HEAD drift fail closed.

## Ambient independence and cleanup

Tests and the checker create a source repository with an ambient commit above
the explicit BASE. Even there, the generated pre-commit HEAD, main, and
origin/main remain at BASE, and the candidate parent remains BASE.

Before any lifecycle work, the harness freezes source HEAD, index bytes,
porcelain status bytes, refs, and worktree listing. All lifecycle resources
are created below the caller's external workspace. Success and exception
paths both remove the temporary bare remote, clones, detached worktree
metadata, objects, and refs. The source snapshot must then be byte-identical.
Cleanup failure is itself a closed failure.

All subprocesses use argument tuples, `shell=False`, captured stdout/stderr,
and explicit return-code checks. Only local Git, Python filesystem APIs,
`tempfile`, and `subprocess` are used.

## Mandatory reuse policy

All later CovaPIE stages that verify these lifecycle states must call this
shared harness. They must not copy Git lifecycle fixtures or independently
repeat bare initialization, cloning, worktree construction, BASE seeding,
candidate commit, push, or cleanup flows. They must not clone from ambient
ROOT/main/HEAD, and expected lifecycle semantics must never change according
to the real repository's current commit or push state.

The stage-global in-memory integration smoke and every later lifecycle-aware
stage must reuse this harness first. This increment intentionally does not
retrofit the already committed runtime stage.

## Readiness

This is test infrastructure only. `ready_for_training=false`. Step12D was a
smoke legality check, not a final training-feature contract. The historical
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` blockers
remain unresolved, and a feature-semantics audit is mandatory before formal
training, fine-tuning, backward passes, optimizer steps, or parameter
updates.

The recommended next step is
`run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1`.
