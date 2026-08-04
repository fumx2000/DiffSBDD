# CovaPIE Current11 reaction-transformation evidence overlay contract v1

## Scope

This increment is a metadata-only, read-only, fail-closed schema overlay for
`CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_000001`. It designs the evidence
shape needed by a future reaction-transformation review. It does not fill a
transformation answer, construct a post-reaction state, generate or match
SMARTS, modify the formal family/rule worklist, modify the UNIT_000001 dossier,
compile a submission, ingest a review, generate authority, create role or seed
records, materialize tensors, execute a model, or train.

The public API is:

```python
evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, object]
```

It reads only formal Git objects, SHA-bound state, the frozen formal review
workspace, the non-authoritative dossier crosscheck, and the five generated
repository artifacts. It has no write path.

## Frozen audit conclusion

- family identity review readiness: `evidence_ready_for_human_decision`
- complete rule review readiness: `blocked_missing_post_reaction_semantics`
- `schema_gap_detected=true`
- `formal_post_reaction_authority_count=0`
- `feature_semantics_reaudit_required_before_training=true`
- `ready_for_training=false`

The two samples are:

| Sample | PDB | Ligand | Ligand atom | Target atom | Boundaries |
| --- | --- | --- | --- | --- | ---: |
| `CYS_SG_SAMPLE_INDEX_000008` | `1AYU` | `INA` | `C21` | `CYS:SG` | 2 |
| `CYS_SG_SAMPLE_INDEX_000010` | `1AYW` | `IN3` | `C21` | `CYS:SG` | 2 |

The candidate local graph records two C–N single bonds and one C–O double
bond around the reactive carbon. Their normalized order sum is 4. Adding only
the candidate SG–C single bond while holding all internal bonds unchanged
would produce a conditional sum of 5. This ledger is a gap signal only. It is
not reaction authority and does not choose an internal bond-order change,
broken bond, formal-charge change, proton transfer, leaving-group mechanism,
reversibility state, or product graph.

## Source authority boundary

The source inventory binds the formal review-package Exact9, binding
matrix/registry/manifest/inventory, candidate assignments, family/rule
registries and design matrix, observed-to-parent mapping, projected bonds,
canonical covalent atom-pair records, the two pair-geometry tables, unified
effective boundary authority, formal 30-field review contract, formal
workspace Exact5, and dossier Exact6.

Authority scopes are closed. The dossier Exact6 is always
`non_authoritative_review_aid` with lineage note
`non_authoritative_human_review_aid_crosscheck`. Geometry is
`formal_pair_geometry_only`; it is not bond-order or transformation evidence.
No source is marked `formal_post_reaction_transformation_authority`, and every
source row has `authoritative_for_transformation=false`.

## Exact41 overlay fields

The order is frozen as Exact16 derived fields followed by Exact25 future
human/authority fields.

### Exact16 frozen/derived fields

1. `transformation_review_unit_id`
2. `parent_review_unit_id`
3. `reaction_family_id`
4. `warhead_rule_id`
5. `sample_index_row_ids_json`
6. `sample_count`
7. `target_residue_types_json`
8. `target_residue_reactive_atom_name`
9. `ligand_reactive_atom_ids_by_sample_json`
10. `effective_attachment_boundaries_by_sample_json`
11. `candidate_local_graph_rule_sha256`
12. `candidate_formed_bond_order`
13. `pre_reaction_center_bond_order_sum`
14. `conditional_post_bond_order_sum_if_internal_bonds_unchanged`
15. `post_reaction_authority_status`
16. `schema_gap_detected`

### Exact25 future fields

1. `reviewed_transformation_version`
2. `reviewed_transformation_class`
3. `reviewed_transformation_scope`
4. `reviewed_atom_map_contract_json`
5. `reviewed_attachment_boundary_map_numbers_by_sample_json`
6. `reviewed_pre_atom_state_contract_json`
7. `reviewed_post_atom_state_contract_json`
8. `reviewed_formed_edges_json`
9. `reviewed_broken_edges_json`
10. `reviewed_bond_order_changes_json`
11. `reviewed_formal_charge_changes_json`
12. `reviewed_protonation_transfer_contract_json`
13. `reviewed_leaving_group_contract_json`
14. `reviewed_reversibility_semantics`
15. `reviewed_post_state_evidence_type`
16. `reviewed_post_state_evidence_source`
17. `reviewed_post_state_evidence_sha256`
18. `transformation_identity_explicitly_attested`
19. `transformation_full_semantics_explicitly_attested`
20. `transformation_review_decision`
21. `review_rationale`
22. `review_notes`
23. `reviewer_id`
24. `attestor_id`
25. `review_completed`

Every future field has an empty-string initial value and `prefilled=false`.
Empty means unreviewed. It is not `false`, `pending`, `unknown`, `N/A`, an
empty JSON list, or a candidate answer.

## Future canonical JSON contracts

All future JSON must use sorted keys, compact separators, ASCII escaping, and
must reject NaN. Map numbers are positive integers and unique within each
sample.

The atom-map contract supports:

```json
{"samples":{"<sample_id>":{"atom_records":[{"element":"<string>","map_number":"<positive int>","sample_atom_id":"<string>"}],"ligand_reactive_atom_map_number":"<positive int>","target_residue_atom_map_number":"<positive int>","warhead_atom_map_numbers":["<positive int>"]}}}
```

The plural attachment-boundary contract supports exactly two records for each
UNIT_000001 sample:

```json
{"samples":{"<sample_id>":[{"bond_order":"<normalized order>","nonwarhead_boundary_atom_map_number":"<positive int>","warhead_attachment_atom_map_number":"<positive int>"},{"bond_order":"<normalized order>","nonwarhead_boundary_atom_map_number":"<positive int>","warhead_attachment_atom_map_number":"<positive int>"}]}}
```

Both list elements are real record objects with the same exact three-field
shape. The former explanatory string in the second list position has been
removed. A future review submission for each UNIT_000001 sample must provide
two attachment mapping records; this template contains no real map-number
answer.

This is why the historical singular attachment-map field is insufficient: one
map pair cannot cover the two formally reviewed attachment boundaries in each
sample.

Pre- and post-atom-state records support `map_number`, `element`, integer
`formal_charge`, and nonnegative integer or null
`explicit_hydrogen_count`. Formed and broken edges use map-number endpoints.
Bond-order changes contain `map_number_1`, `map_number_2`, `pre_bond_order`,
and `post_bond_order`. Formal-charge changes contain `map_number`,
`pre_formal_charge`, and `post_formal_charge`.

The protonation-transfer contract has an explicit status vocabulary that
distinguishes `explicitly_attested` from `not_claimed`. Missing data must never
be converted automatically to `not_claimed`.

The leaving-group contract uses the same explicit status distinction and
map-number-based broken-edge records:

```json
{"samples":{"<sample_id>":{"leaving_group_records":[{"broken_edge":{"map_number_1":"<positive int>","map_number_2":"<positive int>","pre_bond_order":"<normalized order>"},"leaving_atom_map_numbers":["<positive int>"]}],"status":"<explicitly_attested or not_claimed>"}}}
```

For a future `explicitly_attested` instance, applicable leaving-group records
must be nonempty, use positive atom-map numbers, and agree with the reviewed
atom map and broken-edge contract. A future explicit no-claim must use
`status=not_claimed` with `leaving_group_records=[]`. The field's current empty
string remains unreviewed and must not be interpreted or converted as that
explicit no-claim.

An explicitly reviewed canonical empty list is semantically different from an
empty string. For example, an explicit empty list means the reviewer examined
that delta class and attested that no records apply. An empty string means the
field has not been reviewed.

This schema-only revision does not select addition, substitution, a broken
bond, or any other mechanism. It establishes no post-state authority, generates
no SMARTS, and makes no approval decision.

## Fail-closed approval invariants

`approve_reaction_transformation_contract` is legal only when all of these are
true:

1. family identity authority formally exists;
2. Exact2 sample scope is explicit;
3. the atom-map contract is complete;
4. map numbers are positive and unique per sample;
5. target SG and ligand C21 are mapped;
6. both attachment boundaries in each sample are covered by plural mapping;
7. pre-atom state is complete;
8. post-atom state is complete;
9. formed-edge state is complete;
10. broken edges are explicitly reviewed, allowing an explicit empty list;
11. bond-order changes are explicitly reviewed, allowing an explicit empty list;
12. formal-charge changes are explicitly reviewed, allowing an explicit empty list;
13. protonation transfer is explicitly reviewed;
14. leaving-group semantics are explicitly reviewed;
15. reversibility semantics are explicitly reviewed;
16. post-state evidence type, source, and SHA are complete;
17. every referenced edge endpoint exists in the atom map;
18. the formed edge exactly covers CYS-SG to the ligand reactive center;
19. transformation class agrees with the explicit delta;
20. a bond-order-change class has a nonempty change list;
21. a broken-bond class has a nonempty broken-edge list;
22. the conditional center bond-order conflict is explicitly resolved by reviewed post-state evidence;
23. identity attestation is `true`;
24. full-semantics attestation is `true`;
25. reviewer, attestor, rationale, and completion provenance are complete;
26. `review_completed=true`;
27. approved SMARTS is not derived automatically from the candidate graph;
28. the formal worklist and historical authority remain unchanged.

The Exact28 failure registry mutates canonical baseline bytes for every case
and routes every mutation through one fail-closed validator. X16 rejects a
singular map for an Exact2 boundary set. X20 and X21 preserve the distinction
between an explicit list field and an unreviewed empty string. X28 rejects a
valid-looking substituted external artifact-SHA witness even if a response
digest is recomputed.

## Lifecycle and response witnesses

The lifecycle profiles are:

- `transformation_overlay_precommit_candidate`
- `transformation_overlay_committed_unpushed`
- `transformation_overlay_published_successor`

Precommit requires HEAD and `origin/main` at the frozen base and Exact9 as
ordinary untracked mode-0644 files. Committed-unpushed requires one single-
parent commit over the base, the frozen subject, and Exact9 added as 100644.
Published-successor requires that formal commit to be an ancestor of both HEAD
and `origin/main`, with commit/index/worktree blobs identical for Exact9.

Response construction freezes two external witnesses before building the
response: a Git-derived lifecycle witness and the SHA map of all five generated
data artifacts. Response validation rejects extra or missing fields, booleans
masquerading as integers, lifecycle substitutions, artifact substitutions, and
rehashed substituted responses.

## Next step

The recommended next step is
`materialize_covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1`.
It is not executed by this increment.
