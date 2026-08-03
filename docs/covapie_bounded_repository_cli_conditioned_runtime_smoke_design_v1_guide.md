# CovaPIE bounded repository CLI conditioned runtime smoke design V1

This guide freezes the design of one future, tightly bounded real runtime
smoke for `generate_ligands.py`. The design step itself does not load the
checkpoint, import or construct the Torch model, execute the caller, run a
forward pass, generate a molecule, write a PDB or SDF, train, or implement
reward/RL behavior.

The evaluator is lifecycle-neutral with respect to its own four design files.
It binds published predecessor evidence and live runtime identities, but it
does not require these design files to be untracked, committed, or published.
The design is complete. The user has authorized one bounded smoke execution
after the design is formally committed and the runtime-source snapshot is
freshly revalidated. This readiness is conditional on those two prerequisites;
the current design-revision step does not execute the smoke.

## Scope and predecessor bindings

The only selected V1 caller is `generate_ligands.py`. The runtime smoke for
`scripts/covalent_inpaint_demo.py` is deferred because it additionally needs a
real ligand, exact atom groups for all five canonical masks, and an inpainting
output contract. The two callers must not be combined in this smoke.

The design binds the published C4 commit
`011b9558d4a59824e3ba51a0d896ec13100b2b1b`, its exact four files, its Exact62
published response SHA256
`b455fe78165cf13f8277a866e1bc8069c980f98080eb0026302c9047d1d8d224`, and its
checker stdout SHA256
`4526973c08805ac70442e24bdce29f256a5a48d94ab6e5f616ead3aa5a42c553`.
C4 must report `c4_published_successor`, selector forwarding complete, and
runtime-smoke planning ready.

The design also binds:

- C1 commit `142e7f72b391ceed3bbecaf22846a08f56933ea5` and the central helper SHA256
  `ff02657edd67d643bed4881b3c52df75cb950dffc45c19e5497b07dd65a52dfc`;
- the three real C1 parser, resolver, and conditioned-loader APIs;
- C2 commit `7cdaf807241e3dc4331d5c0a05eb6a63dd4d5ec4` and the exact
  `generate_ligands.py` SHA256, Git blob, and mode;
- `checkpoints/crossdocked_fullatom_cond.ckpt`, size 17,861,341 and SHA256
  `07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c`.

The design reads checkpoint bytes only to verify size and SHA256. It never
deserializes them. The future smoke must use the C1 conditioned loader with
`map_location="cpu"`; it may not copy or rewrite the checkpoint, call the
migration helper directly, or use `strict=False`.

The C2 AST audit proves one import of each C1 helper, one parser-helper call,
one resolver call, one conditioned-loader call, one mutually exclusive legacy
loader call, one selector-forwarding keyword, one real `model.generate_ligands`
call, and one `write_sdf_file` call. It also proves resolution happens before
loading, conditioned failure has no legacy fallback, and the resolver's same
selector object is forwarded inside the only batch loop.

The future execution path also depends on three live runtime sources frozen at
snapshot commit `011b9558d4a59824e3ba51a0d896ec13100b2b1b`. Their live bytes
must equal the snapshot blobs, and every file must be
ordinary, non-symlink, non-executable mode `100644` with mode stable across the
read:

- `lightning_modules.py`: SHA256
  `7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983`,
  blob `d19f18ec2841a9a3163d099f4df451d97ce795d4`;
- `equivariant_diffusion/conditional_model.py`: SHA256
  `a61dc44f376b3efc0365f558b09470f71b35dd2606c216f5abf0ba06d5a1b4a9`,
  blob `4c4ffab13830506f7442c8ccb2e7cdad5bbcfae2`;
- `utils.py`: SHA256
  `2d8fdc954f025e70717b992a1382d8a020eff9170af8e92c961e74759287793b`,
  blob `75450035d1dcd28590d487b3c5c0eaff79fced8a`.

The snapshot must remain an ancestor of both current HEAD and current
`origin/main`, but neither ref must equal the snapshot. Consequently, the same
contract works while the design is untracked, committed but unpushed,
published, or followed by unrelated successor commits. Any live-source drift
closes implementation readiness and requires design revalidation.

## Canonical masks and target

The repository contract remains exactly five semantic masks, in order:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

No sixth mask is introduced. The future target is the explicit Exact6 value:

```text
chain_id=A
residue_sequence_number=1
residue_insertion_code=" "
residue_name=CYS
atom_name=SG
element=S
```

It must not be inferred from a reference ligand, distance, the first cysteine,
or a nearest sulfur.

## Frozen in-memory PDB fixture

The evaluator freezes the exact UTF-8 PDB text in its response. It uses LF
line endings and a terminal newline. Its byte count is 505 and SHA256 is
`ccad2ee5cd8cc2459003790d837bbdc68fede63cdb5ea575f433250048f302c3`.
The six atoms are `N`, `CA`, `C`, `O`, `CB`, and `SG`, with elements `N`, `C`,
`C`, `O`, `C`, and `S`. All belong to the single blank-altloc, blank-insertion
code residue `CYS A 1`. The file ends with `TER` and `END`.

Tests parse this text directly from memory with Bio.PDB and prove one model,
one residue, six atoms, and exactly one `CYS A 1 SG S`. This design step never
writes the PDB to the repository or filesystem. A future executor will write
the exact bytes only under its repository-external temporary input directory.

## Exact future CLI

After substituting the unique temporary directory for `<TEMP>`, `sys.argv`
must be exactly equivalent to:

```text
generate_ligands.py
checkpoints/crossdocked_fullatom_cond.ckpt
--pdbfile <TEMP>/input/minimal_cys_sg.pdb
--resi_list A:1
--outfile <TEMP>/output/generated.sdf
--n_samples 1
--batch_size 1
--num_nodes_lig 4
--timesteps 1
--target_residue_atom_conditioning
--target_chain_id A
--target_residue_sequence_number 1
```

`--ref_ligand`, `--sanitize`, `--relax`, and `--all_frags` must be absent.
Consequently, the observed generation call must have `pocket_ids=["A:1"]`
and `ref_ligand=None`.

## Isolated CPU execution

A future dedicated executor must create a child process with these exact
environment overrides:

```text
CUDA_VISIBLE_DEVICES=""
PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=".:src:scripts"
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
```

Inside the child, it must set `random.seed(0)`, `numpy.random.seed(0)`,
`torch.manual_seed(0)`, and `torch.set_num_threads(1)`. If supported and not
already initialized, it may set `torch.set_num_interop_threads(1)`. It must
prove `torch.cuda.is_available() is False`, resolve `cpu`, and disable gradient
recording for the run. A100 use is outside this CPU plumbing smoke.

The child installs observers, sets the exact `sys.argv`, and executes
`runpy.run_path("generate_ligands.py", run_name="__main__")`. It writes one
canonical evidence JSON under the temporary directory and exits. The bounds
are fixed at one sample, batch size one, four ligand nodes, and one timestep;
they may never be automatically enlarged.

The parent timeout is 300 seconds. Timeout, a nonzero child return code, or any
stderr byte fails closed. Normal stdout has no content contract, but both
streams' byte counts and SHA256 values must be reported.

## Transparent observation

The allowed call wrappers observe the C1 resolver, C1 conditioned loader,
legacy `LigandPocketDDPM.load_from_checkpoint`, `prepare_pocket`, and
`generate_ligands`. Each wrapper calls its original function, passes arguments
unchanged, and returns the original result unchanged. Wrappers may not replace
the model, mock sampling, mock the PDB, mock SDF writing, or alter a result.

A temporary `register_forward_hook` must be attached only to
`model.ddpm.dynamics`. Its callback only increments a counter, returns `None`,
and modifies neither inputs nor output; the hook is removed in `finally`. It
must not be attached to `model`, `model.ddpm`, `LigandPocketDDPM`, or
`ConditionalDDPM`, because `generate_ligands` enters `sample_given_pocket` and
the actual neural-network calls are `self.dynamics(...)`.

For the frozen `ConditionalDDPM` source and `timesteps=1`, the required dynamics
forward count is exactly two, not merely greater than zero. The single reverse
loop iteration calls `sample_p_zs_given_zt`, which calls `self.dynamics(...)`
once. Final decoding then calls `sample_p_xh_given_z0`, which calls it once
more. The future smoke fails closed unless `ddpm_type == "ConditionalDDPM"`,
`dynamics_forward_call_count == 2`, and `model_forward_executed == true`.
A call profiler records any training-step, backward, optimizer, scheduler, or
save API use without changing behavior. The smoke fails unless the real
conditioned loader and real generation path each run once, a real forward is
observed, and all forbidden training/update/save counts remain zero.

The required resolver evidence is one call and the exact selector above. The
loader evidence is one conditioned call, zero legacy calls, the frozen
checkpoint path, and `map_location="cpu"`. The loaded model must expose
conditioning enabled at both model and dynamics levels, a `[32]` all-zero new
embedding, and 123 state keys.

`prepare_pocket` must run once and produce pocket size `[6]` with a bool
indicator of shape `[6]`, exactly one true value, and that true value must
correspond to `CYS A 1 SG S`. Generation must run once with one sample,
`["A:1"]`, no reference ligand, one timestep, and the identical resolver
selector object.

## Zero-update and checkpoint immutability

The future smoke allows a real denoising forward but no training. It requires
no training step, backward, optimizer creation or step, or scheduler step, and
all parameter gradients must remain `None`.

Before and after generation, the executor computes a read-only state digest
over sorted keys, tensor dtypes, shapes, and tensor bytes. Digests must match.
Parameter values and tensor version counters must also remain unchanged.

Checkpoint bytes, size, `mtime_ns`, and SHA256 must match before and after.
`torch.save`, `save_checkpoint`, and state-dict disk writes are forbidden. The
checkpoint remains the existing read-only repository input; every generated
fixture, output, log, and evidence artifact is outside the repository.

## Output acceptance

This smoke validates runtime plumbing, not molecular quality. It accepts a
generated molecule count of zero or one. With such a tiny stochastic sample,
requiring a chemically valid molecule would conflate conditional routing with
sampling quality. It therefore does not require sanitize success, a specific
SMILES, atom types, geometry, or a nonempty SDF record.

The evidence still records whether the SDF exists, is regular, is not a
symlink, its size, and its record count. Even if one molecule is produced, the
claim remains `chemical_generation_quality_validated=false`.

## Temporary workspace and safe cleanup

The future executor creates a previously nonexistent directory matching:

```text
/tmp/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1_<timestamp>_<random>/
```

It records the root directory's `st_dev` and `st_ino`. The closed path set is:

```text
input/minimal_cys_sg.pdb
output/generated.sdf
evidence/runtime_smoke_evidence.json
logs/stdout.bin                 # optional
logs/stderr.bin                 # optional
```

No other path is allowed. Cleanup runs after success, failure, and timeout,
but only if the current root still has the recorded device and inode. Cleanup
must not follow symlinks and must never delete a competitor path that replaced
the original directory.

## Claims and next step

Passing this design gate means the bounded smoke design is complete. Once it is
formally committed and the runtime sources are freshly revalidated, the user
has authorized implementation and exactly one execution. It does not mean the
runtime smoke, model forward, covalent demo smoke, chemical-quality validation,
training, or RL has already occurred.

Before any training or parameter update, a feature-semantics audit remains
mandatory. Step12D was a smoke legality check, not a final training-feature
contract; `UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False`
remain unresolved until formally audited.

The current mainline priority and recommended next step is
`implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1`.
This authorization is for one plumbing smoke only. Repetition requires new
explicit user authorization. Smoke success does not establish training
readiness, five-module completion, feature-semantics completion, or molecular
quality. Smoke failure does not authorize architecture expansion.

Immediately after the one execution succeeds or fails and is reported, the
mainline returns to
`audit_covapie_five_module_training_path_completion_gaps_v1`. This design
revision neither starts that audit nor claims training readiness.
