# CovaPIE FFQ Exact4 POST source/index binding V1

## Outcome and scope

`build_covapie_ffq_exact4_post_source_index_binding_v1` is a read-only CPU API
that connects each approved FFQ Exact4 POST source event to its C1 and SG nodes
in a newly assembled fixed-scaffold structural micro-batch.

The result contains:

- the published `FFQRealStructureMicrobatchAlignmentV1` produced for this call;
- an immutable tuple of typed, event-level source/index bindings in current
  batch order.

It does not return the approved distance value or endpoint coordinate arrays.
It does not create a PRE/POST target, geometry-supervision object, valid/loss
request, split, admission, model-input metadata sidecar, or training consumer.
It never runs a model, loss, backward pass, optimizer, or parameter update.

## Public API

```python
build_covapie_ffq_exact4_post_source_index_binding_v1(
    *,
    samples,
    label_use_formal_bytes,
    post_observation_formal_bytes,
)
```

All inputs are keyword-only. The caller reads the two Formal files and the
structure payload before calling the function. The production module itself
has no filesystem, subprocess, or network operation.

There is deliberately no input for a prebuilt alignment, expected SHA
override, alternate device, alternate task, pocket-policy override, or
validation-disable switch. The function always invokes:

```python
assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
    samples=samples,
    device="cpu",
    pocket_seed_policy="fixed_scaffold_warhead_only_v1",
)
```

## Frozen inputs

The API accepts only these byte identities:

| Input | Byte count | SHA256 |
|---|---:|---|
| POST label-use Formal | 29,507 | `8f3297435525ab68501046f811aa32ae7dbd8ab30c6bcafcafc988aada89468d` |
| POST observation Formal | 86,399 | `6f63963487d4d049fd06d1723c52fc4a6408be8e0bf7af73067fdd8fc0d85955` |
| compressed 3VCY structure payload | 353,235 | `80f00b3dfd6a743ef4cb768cb2959261920a071d362cafa7ce083fc78194bc00` |

The historical `c5cdc659...` provenance in the approved Formal remains
historical provenance. V1 does not rewrite it to the current source commit.

Formal JSON parsing rejects duplicate keys, invalid JSON, and non-finite JSON
numbers. Fixed byte hashes are checked before parsing. The production API does
not import or execute a validator from external State.

## Exact4 and task boundary

Samples must contain each of these events exactly once, in any order:

1. `COVAPIE_CYS_SG_EVENT_V1:3VCY:A:CYS:116-:SG:E:FFQ:C1`
2. `COVAPIE_CYS_SG_EVENT_V1:3VCY:B:CYS:116-:SG:J:FFQ:C1`
3. `COVAPIE_CYS_SG_EVENT_V1:3VCY:C:CYS:116-:SG:O:FFQ:C1`
4. `COVAPIE_CYS_SG_EVENT_V1:3VCY:D:CYS:116-:SG:T:FFQ:C1`

Every sample must have canonical task ID `0`, whose semantic long name is
`warhead_only`. Missing, duplicate, fifth, 4R7U, or other-task samples fail
closed; no sample is silently skipped.

The canonical V1 task contract remains exactly:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

The fixed-scaffold pocket policy is not a sixth task. Selecting Task A for this
pilot does not disable the other canonical tasks.

## Validation sequence

All source validation completes before structural batch creation:

1. Validate both fixed Formal byte hashes and strict JSON syntax.
2. Validate schema, review unit, formal status, Exact5 mask contract, approved
   event population, event-specific scope, and closed execution boundaries.
3. Resolve only the actual JSON pointer shapes used by these Formals. Locator
   strings are treated as data; they are not evaluated or used as file paths.
4. Connect the two Formal documents by full canonical event ID. Verify that
   source-event and distance-field locators resolve to the same observation
   event, and that approved/readback/observation values agree. The value is
   used transiently for source consistency only and is not returned.
5. Validate model 1, angstrom units, original deposited coordinate frame,
   finite values, event-specific purpose/component, and current approved
   decision/status rather than historical `UNSET` readback.
6. Validate Exact4 sample identities, Task A, frozen structure bytes, effective
   record identity hashes, and conservative geometry/admission fields.
7. Parse each unique structure payload once for binding validation and reuse
   those in-memory rows across events. No decompressed or modified structure is
   persisted.
8. Locate endpoint source rows by actual parser row position and full raw
   atom-site identity. `_atom_site.id - 1` is never used to generate a row
   index. The published parser's explicit normalization of mmCIF `.`/`?`
   missing markers to empty text is the only accepted raw-field normalization.

Only after these checks pass does the public API call the published assembler.
It then validates the returned alignment before exposing the result:

- sample identities and Task A order match this call;
- source rows are unique within each sample segment;
- `local + segment offset == flat` for both endpoints;
- `lig_mask`, `pocket_mask`, and positive-pair indices remain in the same
  sample instance;
- C1 is valid, carbon-channel, generated, target, and non-fixed;
- SG belongs to the event's CYS 116 target residue and is sulfur-channel;
- ligand and pocket features remain 10-dimensional;
- `sample_training_admitted`, `geometry_target_available`, and
  `warhead_type_target_available` remain false;
- no field was added to `model_input_batch`.

Different samples may legitimately reuse pocket source-row identities from the
shared PDB payload. The required uniqueness is within a sample's node instance,
not a false cross-sample global source-row uniqueness rule.

## Returned binding metadata

Each `FFQExact4PostEventSourceIndexBindingV1` contains:

- full event ID and current batch ordinal;
- `warhead_only`, task ID 0, scoped purpose, component 1, and angstrom unit;
- both fixed Formal hashes and the label decision / observation event /
  observation distance-field locators;
- C1 and SG raw atom-site identity, actual parser source row, node domain,
  current local/flat index, and sample segment bounds;
- effective-supervision schema and record SHA reference;
- the explicit fixed-scaffold pocket policy.

The metadata dataclasses and binding tuple are frozen. This does not make the
Tensor objects inside the returned structural alignment permanently immutable;
callers must not infer a Tensor immutability guarantee from frozen metadata.

## Verified real indices

For the canonical event order, targeted real-data tests establish:

| Protein chain | Ligand asym | C1 source row | C1 local | C1 flat | SG source row | SG local | SG flat |
|---|---|---:|---:|---:|---:|---:|---:|
| A | E | 12535 | 0 | 0 | 867 | 64 | 64 |
| B | J | 12632 | 0 | 8 | 3990 | 84 | 248 |
| C | O | 12695 | 0 | 16 | 7114 | 84 | 413 |
| D | T | 12759 | 0 | 24 | 10257 | 83 | 588 |

These are test expectations, not hard-coded production index-generation
logic. A real reverse-order build reassembles the batch and produces SG flat
indices `[83, 248, 424, 569]` in reverse event order. Formal locators and raw
source rows remain bound to their events while ordinals, offsets, and flat
indices follow the new batch.

## Readiness boundary

This increment proves only read-only source-to-index binding for the frozen FFQ
Exact4 Task-A call. It does not materialize a target, connect a consumer, or
create training admission.

Before any actual supervision use, the applicable feature-semantics and use
audit remains required, including conditioning channels, common centering,
input distribution, and consumer purpose. Step12D remains a smoke legality
check, not a final training-feature contract. Accurate PRE is not declared a
global V1 prerequisite here.

Consequently this API does not close a global training audit and does not make
CovaPIE ready for training.
