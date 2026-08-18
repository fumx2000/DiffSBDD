# CovaPIE PRE/POST geometry supervision authority feasibility V1

Task: `audit_covapie_pre_post_geometry_supervision_authority_feasibility_v1`

This is a focused data/label-authority audit. It does not modify model code,
training code, loss weights, Current11/K36 data, state, raw data, or checkpoints.
No training, download, optimization, human review, commit, or push is authorized
or performed here.

## Executive decision

`engineering_conclusion=Option A: POST can be made authoritative now; PRE remains missing`

All Exact16 samples have a SHA-bound observed covalent complex, an explicit
covalent event with an exact reactive SG--ligand-atom pair, retained model-input
nodes for both endpoints, and finite coordinates. These are scientifically
sufficient source evidence for the observed post-covalent pair distance. They
are not currently POST labels: the published routing contract forbids silent
promotion, and the current two-component tensor does not publish an exact
component-index registry or an observed-complex-to-POST binding rule.

No Exact16 sample has a paired experimental or curated pre-reaction complex,
or an executed, sample-bound, scientifically qualified machine-derived PRE
reconstruction. Parent/component topology without a pre-complex placement is
not PRE geometry.

The minimal defensible implementation is a small successor that first freezes
the two-component registry and the narrow eligibility rule under which a
validated observed covalent-complex pair distance is POST authority, then
materializes POST-only partial supervision for Exact16. PRE must remain `NaN`,
invalid, and excluded from loss. This does not require PRE and must not block
subsequent data expansion.

`recommended_next_step_exactly=implement_covapie_exact16_post_geometry_partial_supervision_authority_v1`

## Frozen baseline

- `baseline_HEAD=e24cb6eb4289201fce18024a1d0145c3bb6e35ff`
- subject: `add CovaPIE expanded Cys-SG mixed-profile single-batch Trainer.fit smoke v1`
- branch: `main`
- `HEAD == origin/main`: true
- ahead/behind: `0/0`
- initial worktree clean: true
- initial staged index empty: true

## Published semantics and the remaining definition gap

Published task-level semantics are narrow scalar distances:

- `pre_geometry_formal_definition=` the distance in angstrom between the exact
  authoritative reactive protein atom and exact authoritative ligand reactive
  atom in a canonical pre-covalent state. The published routing contract calls
  this an `[S,1]` "pre-state pair distance" and requires canonical pre-state
  structure, pair, frame, and unit authority
  (`covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py:351`).
- `post_geometry_formal_definition=` the distance in angstrom between the same
  exact reactive pair in a resolved authoritative post-covalent state. The
  published routing contract calls this an `[S,1]` "authoritative post-state
  pair distance" (`...tensor_projection_contract_gate_v1.py:352`). The older
  tensor-label contract separately defined a scalar
  `post_covalent_positive_pair_bond_distance_angstrom` as the distance for the
  remapped exact positive retained-heavy pair
  (`covapie_tensor_label_and_loss_mask_contract_design_v1.py:2717-2735`).

The current production tensor and head are both width two, but their published
source contains no named component registry binding index 0 and index 1 to
PRE and POST. A non-published review-scratch design describes intended order as
PRE then POST, while also saying newer authority overrides the older component
0 = POST interpretation. Review scratch is not mainline publication authority.
The published routing contract also keeps observed complex geometry separate
and says it cannot satisfy POST without a resolved binding.

`PRE_POST_GEOMETRY_SEMANTIC_DEFINITION_INCOMPLETE`

The minimal definition decision is therefore not a new physical target. It is
to publish, in one successor contract:

1. exact names and order for the two `pre_post_geometry_*` components;
2. the requirement that PRE and POST refer to the same exact authoritative
   reactive pair, in angstrom, with explicit state and coordinate provenance;
3. whether a raw-SHA-bound, exact `_struct_conn` covalent event plus its selected
   endpoint coordinates is sufficient POST-state authority for the scalar pair
   distance independently of complete post-state graph authority.

This audit does not make that missing publication decision or mutate labels.
It finds that the existing evidence can support the narrow rule in item 3 for
all Exact16 samples.

## Frozen implementation facts

- The geometry head already exists and emits exactly two nonnegative components:
  `covapie_current11_auxiliary_model_and_loss_v1.py:133-137,362-364`.
- The geometry loss already exists, uses per-component masks, averages valid
  components within sample and valid samples across the batch, and returns a
  graph-connected exact zero when no component is valid:
  `covapie_current11_auxiliary_model_and_loss_v1.py:579-614`.
- A missing component must be `NaN`, `valid=false`, and cannot have loss true.
  Finite observed/zero/mean substitution into an invalid component fails closed:
  `covapie_current11_trainable_supervision_materializer_v1.py:441-466` and
  `covapie_current11_training_tensorizer_v1.py:551-577`.
- Observed complex distance is a distinct `[B,1]` field; PRE/POST targets and
  masks are distinct `[B,2]` fields:
  `covapie_current11_training_tensorizer_v1.py:154-158,999-1043`.
- The focused loss test changes observed distance to 999/777 without changing
  geometry loss, proving it is not consumed as PRE/POST:
  `tests/test_covapie_current11_auxiliary_model_and_loss_v1.py:253-280`.
- Current11 materialization records the observed distance but emits
  `[NaN,NaN]`, `[false,false]`, `[false,false]` for geometry:
  `covapie_current11_trainable_supervision_materializer_v1.py:1274-1290,1360-1364`.
- K36 directly computes observed SG--C21 distance from retained coordinates but
  likewise emits both geometry components missing:
  `covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py:829-841,900-912`.
- The current loss weight defaults to zero
  (`covapie_current11_auxiliary_model_and_loss_v1.py:30-35`) and the published
  Exact16 Trainer.fit smoke fixes it to zero
  (`covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1.py:919-923`).
- The published Exact16 smoke asserts geometry valid samples = 0, geometry loss
  = 0, and geometry-head nonzero gradient = false:
  `covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1.py:1344-1357,1394-1421`
  and
  `tests/test_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1.py:1030-1064`.

Therefore `geometry_code_plumbing_already_present=true`, but the current real
training path does not train geometry.

## Exact16 authority matrix

Status vocabulary used below:

- `EXACT_COVALENT_ENDPOINT`: an exact, source-identity-bound reactive endpoint
  from a validated covalent event, mapped uniquely into a retained model node.
- `SOURCE_QUALIFIED_BINDING_PENDING`: the observed covalent-complex pair and
  coordinates are sufficient source evidence for scalar POST, but the current
  mainline two-component index and observed-to-POST rule are not published.
- `MISSING`: no source supplies sample-bound PRE geometry.
- `recommended_post_valid=true_after_successor` is a recommendation for the
  named next implementation, not current product state. Current masks remain
  false for every row.

| sample_identity | profile | pdb_id | ligand_comp_id | reactive_protein_atom_authority | reactive_ligand_atom_authority | observed_complex_distance_available | observed_complex_distance_value | post_geometry_source_candidate | post_geometry_authority_status | post_geometry_blocker | pre_geometry_source_candidate | pre_geometry_authority_status | pre_geometry_blocker | recommended_pre_valid | recommended_post_valid |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|
| CYS_SG_SAMPLE_INDEX_000001 | CURRENT11_STRICT_LINKER_PRESENT | 6BV6 | JUG | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT JUG:CAG | true | 1.670 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | two-component index and observed-to-POST binding not published | none; parent topology is not placement | MISSING | no sample-bound pre-state coordinates | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000002 | CURRENT11_STRICT_LINKER_PRESENT | 6BV8 | JUG | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT JUG:CAG | true | 1.800 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000003 | CURRENT11_STRICT_LINKER_PRESENT | 6BV5 | JUG | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT JUG:CAG | true | 1.718 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000004 | CURRENT11_STRICT_LINKER_PRESENT | 1AEC | E64 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT E64:C2 | true | 1.802 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000005 | CURRENT11_STRICT_LINKER_PRESENT | 1AIM | ZYA | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT ZYA:CM | true | 1.809 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000006 | CURRENT11_STRICT_LINKER_PRESENT | 1AU3 | PCM | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT PCM:C22 | true | 1.762 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000007 | CURRENT11_STRICT_LINKER_PRESENT | 1AU4 | INP | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT INP:C17 | true | 1.807 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000008 | CURRENT11_STRICT_LINKER_PRESENT | 1AYU | INA | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT INA:C21 | true | 1.799 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000009 | CURRENT11_STRICT_LINKER_PRESENT | 1AYV | IN6 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT IN6:C21 | true | 1.806 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000010 | CURRENT11_STRICT_LINKER_PRESENT | 1AYW | IN3 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT IN3:C21 | true | 1.794 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| CYS_SG_SAMPLE_INDEX_000011 | CURRENT11_STRICT_LINKER_PRESENT | 1B02 | UFP | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT UFP:C6 | true | 1.717 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; parent topology is not placement | MISSING | same | false | true_after_successor |
| 4DCD/K36 | K36_DIRECT_ATTACHMENT_OPTIONAL_LINKER | 4DCD | K36 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT K36:C21 | true | 1.887900 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; component topology and post coordinates are not PRE placement | MISSING | no sample-bound pre-state coordinates | false | true_after_successor |
| 4F49/K36 | K36_DIRECT_ATTACHMENT_OPTIONAL_LINKER | 4F49 | K36 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT K36:C21 | true | 1.894489 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; component topology and post coordinates are not PRE placement | MISSING | same | false | true_after_successor |
| 5WKJ/K36 | K36_DIRECT_ATTACHMENT_OPTIONAL_LINKER | 5WKJ | K36 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT K36:C21, event-selected altloc B | true | 1.809903 | observed exact-pair complex distance with explicit altloc provenance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; component topology and post coordinates are not PRE placement | MISSING | same | false | true_after_successor |
| 6L70/K36 | K36_DIRECT_ATTACHMENT_OPTIONAL_LINKER | 6L70 | K36 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT K36:C21 | true | 1.765181 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; component topology and post coordinates are not PRE placement | MISSING | same | false | true_after_successor |
| 6WTT/K36 | K36_DIRECT_ATTACHMENT_OPTIONAL_LINKER | 6WTT | K36 | EXACT_COVALENT_ENDPOINT CYS:SG | EXACT_COVALENT_ENDPOINT K36:C21 | true | 1.638083 | observed exact-pair complex distance | SOURCE_QUALIFIED_BINDING_PENDING | same | none; component topology and post coordinates are not PRE placement | MISSING | same | false | true_after_successor |

### Source trace

For Current11, the canonical index records the exact PDB/component/reactive
atoms and observed distances. The materializer cross-checks those values to the
retained ligand/pocket coordinate rows within 0.0015 angstrom, requires observed
geometry routing to be observed-only, and requires PRE and POST routing to stay
blocked (`covapie_current11_trainable_supervision_materializer_v1.py:1244-1290`).
Exact atom-table mappings are SHA-bound and unique for both endpoint roles.

For K36, the structural tensorizer verifies a raw source file against its
recorded SHA, requires `MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR` for CYS:SG--K36:C21,
maps both endpoints uniquely into retained ligand/pocket rows, and computes the
observed distance directly from those coordinates
(`covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py:572-579,649-728,829-841`).
The K36 carrier explicitly records PRE authority as `NOT_ESTABLISHED`
(`...mixed_profile_tensorizer_v1.py:535-558`).

The Exact16 extraction was executed twice in memory. It re-read all Current11
atom tables and K36 structural/raw sources, verified source SHA256 values,
unique endpoint mappings, retained endpoints, and coordinate distances. Both
runs were identical:

- `deterministic_double_extraction_equal=true`
- `canonical_extraction_sha256=1d1d3569a49e64823c50d700f337b906b1d47cd4694bcf8011c61d7d69349dd2`
- `observed_complex_distance_available_count=16`

## PRE source audit

Exact16 classification:

- `AUTHORITATIVE_EXPERIMENTAL=0`
- `AUTHORITATIVE_CURATED=0`
- `AUTHORITATIVE_MACHINE_DERIVED_CANDIDATE=0`
- `MISSING=16`

Current11 now has authoritative parent/component graph and bond-order evidence,
but a parent ligand graph does not place the ligand relative to the sample's
protein SG in a pre-covalent complex. K36 similarly has authoritative component
topology and observed covalent-complex coordinates, not pre-state placement.

The repository's three historical `*_pre_reaction.sdf` artifacts belong to
BTK/KRAS samples outside Exact16. Their own QA says their coordinate blocks are
identical to source, `pre_reaction_transform_ready=false`, and
`training_ready=false`. They cannot provide PRE authority here and exemplify why
bond deletion/topology repair alone is not a pre-complex geometry label.

No existing evidence was found for an Exact16 paired noncovalent precursor
complex, same protein/ligand unreacted experimental structure, explicit curated
pre-state coordinates, downloaded paired structural record, or already executed
qualified machine reconstruction.

## Future machine-derived PRE approaches (not implemented)

| approach | physical quantity represented | POST leakage / circularity | reproducibility | cost | training-authority suitability | disposition |
|---|---|---|---|---|---|---|
| A. Delete covalent bond, keep coordinates | post-crystal pose with only a graph edge removed | complete POST coordinate leakage; target remains the observed post distance; circular | high | low | not PRE geometry | forbidden |
| B. Delete bond + local restrained minimization | a nearby force-field local minimum seeded by the post complex | high leakage through starting coordinates/restraints; model-dependent pseudo-label | high only with frozen software, typing, restraints, convergence and seeds | low to moderate | insufficient without independent validation; not experimental | candidate-only and human-review-required |
| C. Delete bond + protein-fixed/pocket-restrained ligand relaxation | a constrained, post-pose-seeded unbound local surrogate | moderate/high leakage; scaffold/pocket restraints can preserve the answer; not independent ground truth | achievable with a fully versioned deterministic protocol | moderate | potentially a future machine-derived candidate, never automatic authority | candidate-only; human review and external validation required |
| D. Generate precursor ligand geometry, then locally dock/relax | a modeled precursor bound pose in the observed pocket | lower direct pair-distance leakage if the POST pair target is excluded, but pocket/pose choice still derives from POST; scoring-model bias replaces ground truth | achievable but sensitive to search/scoring/version/seed | high | potentially useful candidate generation; weak as sole authority | candidate-only; human review required |
| E. Use a paired noncovalent structure | experimentally observed pre-covalent bound pair distance | no POST-coordinate leakage when independently determined; not circular | high after exact identity, alignment, altloc and atom-map freezing | acquisition/mapping moderate; computation low | strongest defensible PRE authority | human-review-required mapping; then AUTHORITATIVE_EXPERIMENTAL |

No RDKit minimization, docking, molecular dynamics, or optimization was run.

## Counts, complexity, and expansion decision

Counts below are current published authority, not the proposed successor state:

| population | pre_authoritative_count | post_authoritative_count | observed_complex_distance_available_count | post_source_qualified_pending_binding_count |
|---|---:|---:|---:|---:|
| Current11 | 0 | 0 | 11 | 11 |
| K36 | 0 | 0 | 5 | 5 |
| Exact16 | 0 | 0 | 16 | 16 |

- `Current11.pre_authoritative_count=0`
- `Current11.post_authoritative_count=0`
- `K36.pre_authoritative_count=0`
- `K36.post_authoritative_count=0`
- `Exact16.pre_authoritative_count=0`
- `Exact16.post_authoritative_count=0`
- `experimental_pre_source_count=0`
- `curated_pre_source_count=0`
- `machine_derived_pre_candidate_count=0`
- `post_geometry_authority_can_be_established_now=true`
- `pre_geometry_authority_can_be_established_now=false`
- `geometry_code_plumbing_already_present=true`
- `geometry_activation_code_complexity=low`
- `geometry_label_authority_complexity=high` (POST low; PRE high)
- `should_geometry_block_data_expansion=false`

POST-only authority is a low-code, low-label-complexity increment once the
minimal semantic binding is published. PRE would require new experimental
pairing or substantial scientific reconstruction and validation machinery.
Unavailable PRE must not delay data expansion.

## Targeted validation

No backward pass, optimizer step, Trainer.fit, or model/data mutation was used
for this audit.

- The Exact16 authority extraction was materialized twice in memory and was
  byte-canonically identical, as recorded above.
- Six focused pytest cases passed: Current11 observed-substitution and partial
  component-mask guards; the component-aware loss/observed-field separation;
  K36 Exact15 real structural tensorization; K36 determinism/no-source-mutation;
  and Current11 all-sample/all-task delegated parity.
- Two Current11 materializer cases failed during shared fixture setup before
  their test bodies. The fail-closed cause was pre-existing physical mode
  `0664` on six committed pilot event/pair CSVs while their published payload
  contract requires `0644`. Bytes and SHA256 values matched. This audit did not
  change permissions or revisit the known physical-mode portability issue.
- A separate pure forward loss check with all geometry masks false returned
  `pre_post_geometry_valid_sample_count=0` and
  `loss_pre_post_geometry=0.0`, without backward or an optimizer.
- The published Exact16 Trainer.fit smoke was not rerun because it performs a
  real backward/optimizer step outside this audit's authorization. Its source
  and focused historical test provide the frozen
  `geometry_head_nonzero_gradient=false` evidence cited above.

## Scope and safety record

- production model/data mutations: none
- model architecture/forward/loss/weight changes: none
- `Trainer.fit` changes or execution: none
- data/raw/checkpoint/protected-state mutations: none
- an independently owned active GPU-steady run updated only its declared
  volatile `heartbeat.json` and `control_summary.json`; these exact paths are
  excluded by the published state-ownership contract and were not touched by
  this audit
- synthetic PRE labels: none
- external acquisition/network use: none
- human review: none
- full training/regression: not run; unnecessary and outside this audit
- generated product artifacts: none; this report is the sole audit artifact
- commit/push: not performed
