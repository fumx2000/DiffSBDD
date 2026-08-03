# CovaPIE repository CLI forwarding gate C4 V1

This guide describes the independent formal C4 gate for target-residue atom
conditioning at repository CLI entry points. The evaluator is the lifecycle
source of truth; this document does not claim that C4 is committed or
published.

## Predecessor responsibilities

C1 introduced the one central CLI helper. It owns the three target flags, the
Exact6 selector compiler, the conditioned checkpoint loader, and normalization
to `COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_INVALID`. C2 forwards
the compiled selector through `generate_ligands.py`. C3 forwards the same
selector through the covalent demo's three layers: `main` to
`run_covalent_inpaint`, then `prepare_single_pocket`, then
`model.prepare_pocket`.

C4 does not reimplement any of those runtime changes. It independently binds
the R3/C1/C2/C3 commits and live bytes, invokes the existing R3 evaluator,
checks the existing model-consumption formal bundle, validates the lightweight
C1 parser/resolver contract, and audits both live callers with AST evidence.
Keeping C4 separate means repository CLI selector forwarding becomes a formal
completion claim only after the C4 gate itself is committed. Runtime-smoke
planning becomes ready only after C4 is published.

## Supported and deferred callers

V1 supports exactly:

- `generate_ligands.py`
- `scripts/covalent_inpaint_demo.py`

The following callers remain explicitly deferred and are not claimed to
support the selector:

- `test.py`: distinct samples need a canonical per-sample target manifest;
  reuse of one global selector is not allowed.
- `optimize.py`: multi-round diversification needs an audit of static-target
  reuse through every population generation.
- `inpaint.py`: the generic inpaint entry point needs the same central parser
  and error contract before a second inpaint surface is enabled.
- `colab/DiffSBDD.ipynb`: the notebook clones upstream and uses another
  checkpoint, so source, checkpoint, migration-helper distribution, and UI
  behavior must be bound together by a successor contract.

## Exact6 and loader contract

The three central options are
`--target_residue_atom_conditioning`, `--target_chain_id`, and
`--target_residue_sequence_number`. Legacy arguments compile to `None`.
Conditioned arguments compile, in exact order, to:

1. `chain_id`
2. `residue_sequence_number`
3. `residue_insertion_code`
4. `residue_name`
5. `atom_name`
6. `element`

The four fixed values are blank insertion code (`" "`), `CYS`, `SG`, and `S`.
The selector is never inferred from `resi_list`, `ref_ligand`, distance,
nearest sulfur, first cysteine, insertion code, residue name, atom name, or
element.

The legacy loader remains `LigandPocketDDPM.load_from_checkpoint`. The
conditioned branch must use the C1 conditioned loader. The two branches are
mutually exclusive, and a conditioned-loader failure has no legacy fallback.
C4 checks loader source structure and binds the existing model-consumption
formal gate; it never calls the loader or reads/deserializes the checkpoint.

## Canonical mask contract

The semantic long names remain the source of truth, in exact order:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

B2 is `scaffold_plus_warhead`; B3 is `scaffold_only`. There is no sixth mask.
The demo still obtains pocket residues through `get_pocket_from_ligand`; the
target selector is passed only to `model.prepare_pocket`, not to the mask
builder or DDPM calls.

## Failure contract

Partial selectors, target fields without the enable flag, unknown `target_*`
fields, a non-boolean enable value, an unstripped chain ID, and a boolean
residue number all fail closed with the C1 canonical error. C4 itself
normalizes failures to
`COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_FORWARDING_GATE_INVALID`.

## Lifecycle profiles

The evaluator accepts exactly three mutually exclusive profiles:

- `c4_precommit_candidate`: the four C4 files are the only ordinary untracked
  files, tracked files are unchanged, and the index is empty. Commit review is
  ready, but repository forwarding is not yet formally complete and runtime
  smoke planning is not ready.
- `c4_committed_unpushed`: one exact clean C4 commit is one ahead and zero
  behind `origin/main`. Repository forwarding is formally complete, but the
  commit is unpublished and runtime smoke planning remains closed.
- `c4_published_successor`: the exact C4 commit is an ancestor of both HEAD and
  `origin/main`, and its four live files remain regular, unmodified, unstaged,
  and byte-identical to that commit. Later unrelated successor work is allowed.
  Only this profile permits planning a bounded conditioned runtime smoke.

The checker and tests validate all three profiles. They do not assume that the
current repository must remain in the precommit profile, and they recompute the
canonical response digest for synthetic lifecycle responses.

## Runtime, checkpoint, and training boundary

C4 performs read-only Git object queries, AST parsing, C1 parser/resolver calls,
formal-bundle validation, file hashing, and a direct R3 evaluator call. It does
not execute caller `main`, load a checkpoint, run a model forward, sample or
inpaint, read or write real PDB/SDF data, train, update parameters, implement a
reward, or start RL. The test-only runtime harnesses use repository-external
temporary directories and mocks.

Before any future training or parameter update, a feature-semantics audit is
still mandatory. Step12D was a smoke legality check, not a final training
feature contract; the historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state must be resolved or formally audited.
