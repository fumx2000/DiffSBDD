# CovaPIE final training feature-semantics and unknown-atom audit v1

This audit is bound to commit
`66d488ba829dad29d17e8a0ec07fa9798bae90b2`. It is a static,
metadata-only audit. It did not read raw structures or checkpoints, construct
training tensors, call a model, modify the dataloader/model/forward/loss path,
or perform training.

## Decision

- audit outcome: `audited_with_blockers`
- feature-semantics audit completed: `true`
- all current model-input semantics frozen: `true`
- feature semantics known: `false`
- protein unknown-atom policy: `unknown_atom_policy_unresolved`
- ligand unknown-atom policy: `unknown_atom_policy_unresolved`
- unknown-atom feature policy resolved: `false`
- checkpoint compatibility preserved: `true`
- ready for tensor/label/loss-mask contract design: `false`
- ready for tensorization: `false`
- ready for model integration: `false`
- ready for training: `false`
- recommended next step:
  `resolve_covapie_training_feature_semantics_and_unknown_atom_policy_gaps_v1`

The registry contains 30 normalized feature groups: 10 current model inputs,
10 current-data metadata-only groups, six future-not-integrated groups, and
four groups that are not training features. Sixteen semantics are explicitly
defined and seven are deterministically derived; there are no ambiguous,
missing, or contradictory registry entries. The final semantics verdict
remains false because both domain-specific unknown-atom policies are
unresolved.

## Current model inputs

The committed checkpoint-compatible path consumes:

1. ligand atom categorical one-hot, `float32 [N,10]`;
2. pocket atom categorical one-hot, `float32 [N,10]`;
3. ligand Cartesian coordinates, `float32 [N,3]`;
4. pocket Cartesian coordinates, `float32 [N,3]`;
5. ligand batch membership, `int64 [N]`;
6. pocket batch membership, `int64 [N]`;
7. ligand node counts, `int64 [B]`;
8. pocket node counts, `int64 [B]`;
9. normalized diffusion time, `float32 [B,1]`, broadcast by batch membership;
10. the generic inpainting fixed-ligand mask, `bool [N,1]`, which has an
    inference consumer but is not consumed by the training forward.

The categorical channel order is exactly:

```text
C:0 | N:1 | O:2 | S:3 | B:4 | Br:5 | Cl:6 | P:7 | I:8 | F:9
```

The coordinate producer subtracts, per sample, the unweighted centroid of all
valid ligand and pocket atoms. Coordinates remain in angstrom and are divided
by `normalize_factors[0]=1` at the diffusion boundary. Validity padding is
removed before the flattened model boundary. Batch membership is zero-based
and drives time broadcast, scatter grouping, and same-sample edge
construction. No external edge-mask tensor is consumed; `EGNNDynamics`
constructs edges internally from batch membership and coordinates.

The original `crossdock_full` preprocessing schema with an `others` channel at
index 10 is an explicit 11-channel legacy schema. It is not the current
checkpoint-compatible 10-channel input and must not be substituted for it.

## Current metadata-only boundary

The following remain metadata-only for the current 11-sample final canonical
dataset: pocket and ligand `type_symbol`; pocket and ligand `x/y/z`; the five
canonical covalent task masks; target-residue locator; structured covalent
atom pair and row indices; warhead type; pre/post covalent geometry; and
quarantine/control-plane metadata. None has a current final-dataset
dataloader/tensor/model consumer.

The canonical mask contract remains exactly:

```text
warhead_only / A
linker_plus_warhead / B
scaffold_plus_warhead / B2
scaffold_only / B3
scaffold_plus_linker_plus_warhead / C
```

Long semantic names remain authoritative. These masks are data/task semantics,
not evidence that model-side role/mask encoding is integrated.

## Unknown-atom audit and current coverage

Neither current checkpoint-compatible domain has a dedicated unknown or
`other` channel. The Step12D helper silently emits an all-zero 10-vector for
unsupported atomic numbers. That observed behavior is not an allowed final
training policy.

The audit used only the explicit `type_symbol` column in 11 pocket tables and
11 ligand tables; it did not infer elements from `atom_name`.

- pocket: 2,531 rows; vocabulary `C=1323,H=329,N=405,O=442,S=32`;
  2,202 supported and 329 unsupported rows;
- ligand: 339 rows; vocabulary
  `C=227,F=1,H=16,N=34,O=59,P=1,S=1`;
  323 supported and 16 unsupported rows;
- missing explicit token values: zero in both domains.

Thus, “current data has no unknown” is false. The `H` rows are explicit and
unsupported by the frozen 10-channel checkpoint vocabulary. Because current
admitted data contains unsupported tokens and the current helper silently
uses a zero vector, neither domain qualifies for the checkpoint-compatible
fail-closed rejection outcome. This audit freezes the blocker; it does not
implement a filter or rejection gate.

## Step12D and future modules

Step12D proved smoke legality only:

```text
step12d_smoke_legality_verified=true
step12d_final_feature_semantics_contract=false
step12d_training_readiness_authority=false
```

The five planned covalent model modules remain 0/5 integrated:

1. target residue/atom condition adapter;
2. role/mask/anchor-distance encoding;
3. ligand atom ↔ residue atom pair prediction head;
4. covalent geometry prediction head;
5. pair contrastive loss.

## Fail-closed evidence and issue state

All 34 required failure cases were executed through the formal scenario
validator and returned `invalid`. The predecessor Exact30 issue rows are
preserved byte-for-byte, followed by exactly two audit identities:

- `FINAL_TRAINING_FEATURE_SEMANTICS_UNRESOLVED`: `resolved`;
- `UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED`: `open`.

The sole effective open issue is therefore
`UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED`. A later resolution step must define
and enforce separate protein/pocket and ligand fail-closed handling, verify the
current `H` rows' disposition, and preserve the 10-channel checkpoint width
before tensor/label/loss-mask contract design can begin.
