# CovaPIE Repository Instructions

## Scope and project baseline

- These instructions apply to the entire repository unless a more specific nested `AGENTS.md` or `AGENTS.override.md` explicitly overrides them.
- The project name is **CovaPIE**. The model base is DiffSBDD full-atom conditional.
- Preserve checkpoint compatibility by default.
- Treat the current user task as the exact authorization boundary.
- Do not modify model architecture, model forward paths, losses, dataloaders, or training-critical code unless the task explicitly authorizes that scope.
- Do not add unrelated refactors, formatting changes, dependency changes, or generated files.

## Canonical mask contract

The semantic long names are the source of truth. Short aliases are for display and reporting only.

1. `warhead_only` / `A`
2. `linker_plus_warhead` / `B`
3. `scaffold_plus_warhead` / `B2`
4. `scaffold_only` / `B3`
5. `scaffold_plus_linker_plus_warhead` / `C`

- The canonical V1 mask contract contains exactly these five tasks.
- `scaffold_only` / `B3` must never be omitted.
- Do not add a sixth or seventh mask.
- Do not use short aliases as the only semantic source.

## Default engineering boundary

- The default project phase covers data pipelines, schemas, masks, metadata gates, reports, validation scripts, and unit tests.
- Do not perform real training, fine-tuning, backward passes, optimizer steps, or parameter updates without explicit authorization.
- Do not perform real candidate evaluation, network acquisition, or bulk download unless both the current task and the relevant readiness gate explicitly authorize it.
- A smoke test proves only its stated smoke contract. It does not establish production readiness or training readiness.
- Prefer metadata-only and pure in-memory validation when the task does not require structure or runtime access.

## Training prerequisite

Before formal training, fine-tuning, real parameter updates, or training-preparation work:

- Explicitly require a feature-semantics audit.
- Preserve the warning that Step12D was a smoke legality check, not a final training-feature contract.
- Resolve or formally audit the historical `UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` state.
- Do not infer training readiness from dataset materialization, QA, sampling, checkpoint loading, or single-step smoke execution.

## Incremental workflow

- Make one small, independently verifiable change at a time.
- Resolve at most one semantics blocker unless the task explicitly authorizes a larger scope.
- Validate both the successful path and the failure path.
- Every gate must fail closed.
- Do not weaken, delete, skip, or rewrite historical tests merely to make a new implementation pass.
- Do not allow new code and new tests to serve as their only evidence. Cross-check predecessor contracts, successor contracts, committed manifests, check scripts, and historical tests.
- Stop and report when the requested scope, source boundary, or readiness state is ambiguous.

## Historical and successor policy

- Treat committed historical gate outputs as read-only by default.
- Express new effective state through a separate successor, overlay, integration, or retirement step rather than rewriting historical evidence.
- Preserve source lineage and deterministic source hashes.
- Do not execute or regenerate a retired legacy stage.
- Do not bypass a retirement registry, predecessor gate, successor gate, or manifest boundary.
- A successor may change only its explicitly authorized rows, fields, contexts, issues, or readiness values.

## File and data safety

The following artifact types and paths must not be newly tracked, staged, or committed:

- Raw structure data under `data/raw/`
- `*.pt`
- `*.ckpt`
- `*.pth`
- `*.pkl`
- `*.lmdb`
- `*.tar`
- `*.zip`
- `*.tgz`
- `*.npz`
- `*.tmp`
- `*.part`

- Existing historical tracked artifacts are legacy baseline state. Handle them only through a separate migration, retirement, or repository-hygiene task.
- Do not remove, rewrite, restage, or recommit historical artifacts during an unrelated task merely to make the repository conform retroactively to this policy.

The following locations are read-only by default and require explicit task authorization before access or modification:

- `data/raw/`
- `checkpoints/`
- `equivariant_diffusion/`
- `lightning_modules.py`
- `dataset.py`
- `data/prepare_crossdocked.py`

- Ignored raw fixtures or checkpoints may be overlaid into a detached verification worktree only when required by authorized tests.
- Runtime overlays must remain ignored and must never become candidate-tree content.
- Do not copy, archive, regenerate, or stage a checkpoint as part of verification.
- Do not follow artifact-reference paths unless the current gate explicitly authorizes those reads.

## Testing and evidence

For each engineering increment, use the applicable subset of:

- Targeted pytest for the changed step
- Predecessor and successor regression tests
- The matching check script
- Deterministic double materialization
- Successful-path and fail-closed negative-path tests
- Import smoke without output side effects
- Source SHA256 verification
- Output SHA256 verification
- Generated-file inspection
- Git-state and artifact-safety inspection

- Deterministic outputs must be byte-identical across consecutive runs.
- Check scripts must verify direct output evidence and must not trust manifest booleans alone.
- A check script must assert a readiness or safety value before printing it.
- Manifests must not contain timestamps or machine-specific absolute paths unless an explicit future contract requires them.
- A manifest must not record its own SHA256 inside itself.
- Run full regression for a final candidate tree, a training-critical change, or when the task explicitly requires it. Do not require full regression for every small truthfulness fix.

At the end of every step, inspect:

- Working-tree changes
- Staged-index changes
- Untracked files
- Generated outputs
- Raw tracked/staged counts
- Protected-source diffs
- Forbidden suffixes
- `.tmp` and `.part` files

## Git and candidate-tree policy

- Do not use `git add .`, `git add -A`, or `git add --all`.
- Stage only the exact authorized file set.
- Distinguish the working tree, staged index, committed HEAD, and `origin/main`.
- For final staged-candidate verification, prefer:
  - `git write-tree`
  - `git commit-tree`
  - a detached Git worktree
- Verify the exact staged tree rather than testing an unrelated working-tree state.
- Do not amend, reset, rebase, or reconstruct an already verified candidate unless the current task explicitly authorizes it.
- If push fails after a verified commit, preserve the local commit and use a separate push-only closure.
- Do not change remotes, credentials, or SSH keys as an incidental workaround.

## Codex collaboration and reporting

- Use high reasoning by default.
- Reserve extra-high reasoning for architecture, model forward or loss paths, dataloaders, and training-critical work.
- Confirm the exact requested scope before editing.
- Prefer fail-closed behavior over guessing.
- Do not expand the task to convenient adjacent work.
- Report skipped tests, unavailable evidence, unperformed external operations, and unresolved uncertainty honestly.
- Final reports must separately state:
  - Working-tree status
  - Staged-index status
  - Committed HEAD status
  - `origin/main` relationship
  - Tests and checks actually run
  - Generated files
  - Raw and protected-source status
  - Forbidden-file status
  - Remaining readiness blockers
