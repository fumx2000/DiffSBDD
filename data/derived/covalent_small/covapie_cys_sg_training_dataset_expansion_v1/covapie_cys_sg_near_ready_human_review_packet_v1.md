# CovaPIE Exact4 near-ready human review packet V1

## Gate result

- Scope: `2DJF/1ZB`, `6DI9/GJJ`, `5F2E/5UT`, and `6OIM/MOV` only.
- `MACHINE_RESOLVABLE_NOW = 0`.
- `TRUE_HUMAN_APPROVAL_REQUIRED = 4`.
- `OTHER_BLOCKER = 0` within this Exact4 review scope.
- `2R9F/K2Z` remains deferred because its embedded-warhead topology needs a runtime profile extension; it is not part of this packet.
- Exact16 is unchanged. No Exact16+N production owner or tensorization was materialized.
- Required next step: `human_approve_covapie_near_ready_expansion_candidates_v1`.

The four candidates already have sufficient structural evidence for their exact
Cys-SG events and observed POST distances. They are not machine-resolvable now
because no approved reusable reaction-family/warhead-rule authority matches any
of their chemistry signatures. The published fail-closed policy requires
explicit human family approval, approved SMARTS semantics, and independent
sample approval. Historical `not_training_input_yet` or draft lifecycle status
is not used as evidence that a human is required.

## Frozen evidence sources

Paths are repository-relative unless prefixed with `${COVAPIE_STATE_ROOT}`.
The state root is the sibling `covapie-state` workspace root. Every digest is
SHA256 of the referenced file.

| ID | Source and SHA256 | What it owns |
|---|---|---|
| E01 | `data/derived/covalent_small/covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1/covapie_cys_sg_expanded_candidate_inventory_and_eligibility.csv` — `c6ccbb6cdbfaffde501e53d03acfe11daca8bf35262e5287db5516e8952eaa28` | Stage-A canonical eligibility and exact structural identities |
| E02 | `data/derived/covalent_small/real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/real_covalent_struct_conn_confirmed_candidate_table.csv` — `981c59f1131ae8c5f1bb17680986eccda9d85a44caf0f44d1711246283f04186` | Direct3 human-confirmed covalent event and endpoint identities only |
| E03 | `data/derived/covalent_small/real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_altloc_aware/real_covalent_confirmed_candidate_coordinate_pair_sanity_table_v1_altloc_aware.csv` — `0293909b9a3ab96063eda3e5eed12609793cc8837ed7e2cd33d8681d0f8249c9` | Direct3 selected endpoint coordinates and POST distances |
| E04 | `data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0/ligand_observed_atom_topology_smoke_table.csv` — `b47d03598a077e6201e21585c683fe46a7423d99fae231b47c303657bad89c59` | Direct3 observed atom identities; smoke status is not role authority |
| E05 | `data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0/ligand_observed_bond_topology_smoke_table.csv` — `007d3b7a57b5878389e1229ceeec999442a532923e475f32cf7bcaea0e580d7f` | Direct3 observed bond evidence; smoke status is not role authority |
| E06 | `data/derived/covalent_small/pre_reaction_graph/pre_reaction_transform_manual_write_back_report.csv` — `32e7a66e8b2c1b1f87cacdd2c57d1b1dc868e3dc83cf7c843ef1585efed54aca` | Direct3 explicitly approved PRE graph transform decisions, not family/role approval |
| E07 | `data/derived/covalent_small/pre_reaction_graph/pre_reaction_training_readiness_gate_report.csv` — `a2cc8ddab41e6439e1d0b2577fdb3514aefb617881975226d6e6bd73ecad8c2d` | Direct3 derived PRE graph QA and candidate-only disposition |
| E08 | `data/raw/covalent_small/metadata/BTK_C481_6DI9_GJJ_annotation_template.csv` — `f993728c5d605bbf9e17f9db0e9dc2e7d5b0bcebe9f561e54727ca46b8249f40` | 6DI9 draft role/warhead proposal |
| E09 | `data/raw/covalent_small/metadata/KRAS_G12C_5F2E_5UT_annotation_template.csv` — `3d81e379d086662398aebb77750e3dfacd3a4b11acbe11f23abdf0f20cbeabad` | 5F2E draft role/warhead proposal |
| E10 | `data/raw/covalent_small/metadata/KRAS_G12C_6OIM_MOV_annotation_template.csv` — `c718277ba5ec2cb09edd36dbb841f4210c467fc94521fec036eb42594f95c14c` | 6OIM draft role/warhead proposal |
| E11 | `data/derived/covalent_small/covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1/covapie_cys_sg_recovered7_canonical_closure_matrix.csv` — `ee0ef9a33344f6204ebb6b54b3b6b1d6e8fe2956754efefbe76e71ba2214d796` | 1ZB event, topology mapping, Exact10, pocket, and fail-closed chemistry disposition |
| E12 | `data/derived/covalent_small/covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1/covapie_cys_sg_recovered7_canonical_model_graph_and_pocket_evidence.json` — `c0a5196f94284bc78c49f1a981798c85b1fd5869237d54f30ba239321c3eb799` | 1ZB canonical atoms, endpoints, coordinates, and pocket atoms |
| E13 | `${COVAPIE_STATE_ROOT}/manual-review-aids/recovered7-targeted-chemistry-review-v1/COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_C0E3CCE067B699C68B74C8260D5479A4D3FF5454A5B40B68EA11DDA2B147E2AD/review_decision_template.csv` — `bffac068bb54c3bfa87f44b6e0e69d359c797fca63654a96f247cb91785f7ac9` | 1ZB dedicated blank `NOT_REVIEWED` chemistry decision template |
| E14 | `data/derived/covalent_small/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/covapie_ligand_role_annotation_rule_registry.csv` — `329d739587c525d76891f3a81689e397ea088b89a142361696a36f0e58f95889` | Exact3 partition/seed gates and human-gold requirement |
| E15 | `data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1/covapie_reaction_family_and_warhead_rule_review_policy_registry.csv` — `af80255bfd507c26eeaab37a951e679edc166b2cf8f9da18aed3fb170ebc7881` | Explicit human family, SMARTS-rule, sample, and gold approval policy |
| E16 | `data/derived/covalent_small/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/covapie_family_and_warhead_rule_authority_registry.csv` — `4899d4664acf45d5ee90283e7977d62385b3a70fe41e082f4d060388be7e106b` | Existing registry; all rows are candidate-only and none matches Exact4 as approved reusable authority |
| E17 | `src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py` — `c95bac177ba2ef1dd519bb5659cb97a8367484b1e41553be56fe3b2789ceb932` | Existing strict-linker/direct-attachment runtime profiles; no Exact4 identity is registered |
| E18 | `src/covalent_ext/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke.py` — `3e0f182e192d06be5fe4baa8cfdb2687ee23856ec5cbefbdac9c6bd2b6206212` and `src/covalent_ext/covapie_unified_leakage_split_materialization_smoke.py` — `4e565e670ef09fd78c65c5aa799378f3efbd965dc896c65d37a6896d71c5212e` | Existing deterministic leakage/split machinery; no Exact4 assignment row exists |
| E19 | `src/covalent_ext/covapie_exact16_post_geometry_partial_supervision_authority_v1.py` — `6f388b42bd58ffed67ed752a9fec9f85e57050fc96a89e6f3d3e90b1281dba44` | Existing POST-only/masked-PRE contract; population is frozen to Exact16 |
| E20 | `${COVAPIE_STATE_ROOT}/manual-review/recovered7-targeted-chemistry-review-v1/COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92/reaction_family_authority_v1.json` — `5eb39ac01770dbb8721a48d7ae6bf77fc6cb07493ca00a0eb5756ebf10921461`; sibling `warhead_rule_authority_v1.json` — `1b8927693386aa8c72fed8677d59bdb3b5b56d4e89a09d88a908341fec0a19b2` | K36 approval is exact-signature-scoped (`83e9...`) and explicitly forbids cross-signature propagation; it cannot authorize Exact4 |

## Four-candidate / fourteen-dimension authority trace

`HUMAN` means a published policy requires a human decision. `MACHINE-LATER`
means an existing deterministic mechanism can run only after the chemistry
record is approved; it is not a human decision. `EVIDENCE-COMPLETE` means the
fact is ready to be rebound by an Exact16+N successor but is not itself a new
production member.

| Dimension | 2DJF/1ZB | 6DI9/GJJ | 5F2E/5UT | 6OIM/MOV |
|---|---|---|---|---|
| 1. Exact event | EVIDENCE-COMPLETE: exact mmCIF `struct_conn` (E11/E12) | EVIDENCE-COMPLETE: human-confirmed exact event (E02) | Same, candidate-specific E02 row | Same, candidate-specific E02 row |
| 2. Protein endpoint | `B:CYS:234:SG`, retained, E11/E12 | `A:CYS:481:SG`, selected altloc B, E02/E03 | `A:CYS:12:SG`, E02/E03 | `A:CYS:12:SG`, E02/E03 |
| 3. Ligand endpoint | `B:1ZB:801:C2`, retained, E11/E12 | `A:GJJ:701:C33`, E02/E03 | `A:5UT:204:C15`, E02/E03 | `A:MOV:303:C25`, E02/E03 |
| 4. Canonical topology | EVIDENCE-COMPLETE: 18-heavy-atom component topology mapped to 16 observed atoms; E11/E12 | PUBLISHED: approved PRE transform and QA; E06/E07, SDF SHA below | Same, candidate-specific E06/E07 and SDF | Same, candidate-specific E06/E07 and SDF |
| 5. Role partition | HUMAN: `APPROVED_DETERMINISTIC_RULE_NO_MATCH`; E11/E14, E13 blank | HUMAN: E08 is proposal-only and has two scaffold-linker cross-role bonds | HUMAN: E09 is proposal-only; E14/E15 require gold authority | HUMAN: E10 is proposal-only; E14/E15 require gold authority |
| 6. Minimal seed / anchors | HUMAN: no proposal; dedicated E13 asks reviewer to decide | HUMAN after role revision: no published seed/anchor proposal | HUMAN after role approval: no published seed/anchor proposal | HUMAN after role approval: no published seed/anchor proposal |
| 7. Warhead members / boundary | HUMAN: `SAMPLE_BOUND_AUTHORITY_NO_MATCH`; E11/E13 | HUMAN: E08/E06 give draft atoms and transform evidence but no sample role authority | HUMAN: E09/E06 give draft atoms and transform evidence but no sample role authority | HUMAN: E10/E06 give draft atoms and transform evidence but no sample role authority |
| 8. Reaction family | HUMAN: `APPROVED_REUSABLE_RULE_NO_MATCH`; E11/E15/E16 | HUMAN: E02 label is only a hint; E15 policy 002 requires explicit approval | HUMAN: same | HUMAN: same |
| 9. Reusable warhead rule | HUMAN: `APPROVED_REUSABLE_RULE_NO_MATCH`; E11/E15/E16 | HUMAN: no approved SMARTS; E15 policies 003-007 | HUMAN: same | HUMAN: same |
| 10. Profile eligibility | MACHINE-LATER after approved roles; no current E17 identity | Blocked under draft roles because scaffold-linker boundary count is 2; human revision then MACHINE-LATER | Draft is strict-linker-shaped; human approval then MACHINE-LATER | Draft is strict-linker-shaped; human approval then MACHINE-LATER |
| 11. Leakage group | MACHINE-LATER: no assignment row; E18 | MACHINE-LATER: no assignment row; E18 | MACHINE-LATER: no assignment row; E18 | MACHINE-LATER: no assignment row; E18 |
| 12. Split | MACHINE-LATER after group assignment; no split row; E18 | MACHINE-LATER after group assignment; no split row; E18 | MACHINE-LATER after group assignment; no split row; E18 | MACHINE-LATER after group assignment; no split row; E18 |
| 13. POST geometry | EVIDENCE-COMPLETE: `1.859979032 A`; E11/E12 | EVIDENCE-COMPLETE: `1.8053 A`; E03 | EVIDENCE-COMPLETE: `1.7554 A`; E03 | EVIDENCE-COMPLETE: `1.8054 A`; E03 |
| 14. PRE geometry | `MISSING_MASKED`; component topology is not PRE distance authority, E19 | `MISSING_MASKED`; approved PRE graph is not PRE distance authority, E19 | Same | Same |

## Existing proposals and reviewer cautions

### 2DJF/1ZB

- Canonical candidate: `COVAPIE_CYS_SG_CANDIDATE_V1_COVPDB_CYS_SG_NEXT_ACQ_ANNOT_000002`.
- Endpoint: `B:CYS:234:SG -- B:1ZB:801:C2`; POST distance `1.859979032 A`.
- Canonical topology atoms: `C,C1,C2,CA,CA1,CB,CD1,CD2,CE1,CE2,CG,CZ,N,N1,N3,N4,O,O1`.
- Observed model-bound atoms: the same list except `N3,N4`; those two absences do not establish a leaving group or PRE chemistry.
- Existing role, warhead, boundary, seed, family, and rule proposal: `NONE_PUBLISHED`.
- Existing dedicated template E13 is blank (`review_status=NOT_REVIEWED`, `review_scope=NOT_REVIEWED`). Component topology is structural evidence, not reaction-specific chemistry authority.

### 6DI9/GJJ

- Endpoint: `A:CYS:481:SG -- A:GJJ:701:C33`; POST distance `1.8053 A`.
- Approved PRE transform: remove `CYS:SG-19:C33`; retain/restore `18:C32-19:C33` as double. PRE SDF: `data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf`, SHA256 `004ec8e1ccb4552156762180137f092ae745179a2ae7b9ea06ff5632e62eb126`.
- Draft warhead: `17:C30,18:C32,19:C33,32:O31`.
- Draft linker: `13:C22,14:C24,15:N26,23:C6,24:N7,28:C23,29:C25`.
- Draft scaffold: `0:C2,1:C3,2:C9,3:C10,4:C11,5:C12,6:C13,7:C14,8:C15,9:O17,10:C19,11:C20,12:C21,16:C27,20:N1,21:C4,22:C5,25:N8,26:N16,27:C18,30:N28,31:O29`.
- Cross-role bonds deterministically read from E08: linker-warhead `15:N26-17:C30`; scaffold-linker `22:C5-23:C6` and `20:N1-23:C6`. The two scaffold-linker bonds violate E14's exact-one boundary rule, so the draft cannot be approved unchanged.
- Existing family hint: `unknown_covalent_warhead` from E02. It is not a formal family ID. Existing reusable rule: `NONE_PUBLISHED`.
- Existing seed/anchor proposal: `NONE_PUBLISHED`.

### 5F2E/5UT

- Endpoint: `A:CYS:12:SG -- A:5UT:204:C15`; POST distance `1.7554 A`.
- Approved PRE transform: remove `CYS:SG-29:C15`; retain/restore `8:C14-29:C15` as double. PRE SDF: `data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf`, SHA256 `4015047b42b77f1f8e785c10eb073fb01d60198245d5e76b1db7db73781eeb9b`.
- Draft warhead: `8:C14,27:C13,28:O1,29:C15`.
- Draft linker: `7:C11,24:C16,25:N3,26:C12`.
- Draft scaffold: `0:C1,1:C2,2:C3,3:C4,4:C5,5:C6,6:C10,9:C18,10:C20,11:O2,12:C8,13:C7,14:N,15:O,16:CL,17:C19,18:C21,19:C,20:N1,21:C17,22:N2,23:C9`.
- Draft cross-role bonds from E09: scaffold-linker `7:C11-22:N2`; linker-warhead `25:N3-27:C13`.
- Existing family hint: `acrylamide_like_or_unknown_manual_check` from E02. It is not a formal family ID. Existing reusable rule: `NONE_PUBLISHED`.
- Existing seed/anchor proposal: `NONE_PUBLISHED`.

### 6OIM/MOV

- Endpoint: `A:CYS:12:SG -- A:MOV:303:C25`; POST distance `1.8054 A`.
- Approved PRE transform: remove `CYS:SG-7:C25`; restore `6:C24-7:C25` as double. PRE SDF: `data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf`, SHA256 `09e366d2e8d7b761b23c0e0f8efb86173f9b5815bc84e53d29c8d465c445dfe1`.
- Draft warhead: `4:C23,5:O2,6:C24,7:C25`.
- Draft linker: `0:C21,1:C20,2:C19,3:N6,8:C18,9:C17,10:N2`.
- Draft scaffold: `11:C7,12:N3,13:C8,14:O1,15:N4,16:C9,17:C13,18:C22,19:C12,20:C11,21:N5,22:C10,23:C14,24:C16,25:C15,26:C2,27:N1,28:C1,29:C5,30:C4,31:F1,32:C3,33:C6,34:C30,35:F2,36:C29,37:C28,38:C27,39:C26,40:O3`.
- Draft cross-role bonds from E10: scaffold-linker `10:N2-11:C7`; linker-warhead `3:N6-4:C23`.
- Existing family hint: `acrylamide_like_or_unknown_manual_check` from E02. It is not a formal family ID. Existing reusable rule: `NONE_PUBLISHED`.
- Existing seed/anchor proposal: `NONE_PUBLISHED`.

The Direct3 `final_role` values are review proposals only: every affected E08-E10
row says `workflow smoke test draft` and requires future curated/pre-reaction
scientific authority. E06 approved the inverse graph transform, not these role
partitions, a reaction-family identity, or reusable SMARTS semantics.

## Decision records — leave blank until human review

Atom namespace for 1ZB is the component atom ID. Atom namespace for Direct3 is
`0-based-SDF-index:PDB-atom-name`; reviewers should record indices to avoid
ambiguous generic names such as `C` or `N`. `review_status=APPROVE` must fail
closed unless every applicable field below is complete and consistent with
E14/E15. Use `NEW_AUTHORITY_REQUIRED` where no existing ID is suitable.

### Decision: 2DJF/1ZB

```yaml
candidate_identity: "2DJF/1ZB"
review_status: ""  # APPROVE | REJECT | QUARANTINE
review_scope: ""  # EXACT_CHEMISTRY_SIGNATURE_REUSABLE | SAMPLE_BOUND_ONLY | QUARANTINE
independent_sample_assignment_decision: ""  # APPROVE | REJECT | QUARANTINE
reaction_family_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
reaction_family_id: ""
reaction_family_version: ""
warhead_rule_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
warhead_rule_id: ""
warhead_rule_version: ""
approved_warhead_smarts: ""
ligand_reactive_atom_map_number: ""
warhead_atom_map_numbers: ""
expected_pre_reaction_bond_orders: ""
allowed_formal_charge_pattern: ""
reviewed_warhead_atom_ids: ""
reviewed_warhead_attachment_atom_id: ""
reviewed_nonwarhead_boundary_atom_id: ""
reviewed_attachment_boundary_bond_order: ""
reviewed_scaffold_atom_ids: ""
reviewed_linker_atom_ids: ""
reviewed_warhead_role_atom_ids: ""
reviewed_scaffold_linker_boundary_bond: ""
reviewed_linker_warhead_boundary_bond: ""
reviewed_minimal_seed_atom_ids: ""
primary_anchor_atom: ""
direction_anchor_atom: ""
optional_plane_anchor_atom: ""
reviewer_id: ""
review_rationale: ""
review_notes: ""
```

### Decision: 6DI9/GJJ

```yaml
candidate_identity: "6DI9/GJJ"
review_status: ""  # APPROVE | REJECT | QUARANTINE
review_scope: ""  # EXACT_CHEMISTRY_SIGNATURE_REUSABLE | SAMPLE_BOUND_ONLY | QUARANTINE
independent_sample_assignment_decision: ""  # APPROVE | REJECT | QUARANTINE
reaction_family_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
reaction_family_id: ""
reaction_family_version: ""
warhead_rule_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
warhead_rule_id: ""
warhead_rule_version: ""
approved_warhead_smarts: ""
ligand_reactive_atom_map_number: ""
warhead_atom_map_numbers: ""
expected_pre_reaction_bond_orders: ""
allowed_formal_charge_pattern: ""
reviewed_warhead_atom_ids: ""
reviewed_warhead_attachment_atom_id: ""
reviewed_nonwarhead_boundary_atom_id: ""
reviewed_attachment_boundary_bond_order: ""
reviewed_scaffold_atom_ids: ""
reviewed_linker_atom_ids: ""
reviewed_warhead_role_atom_ids: ""
reviewed_scaffold_linker_boundary_bond: ""
reviewed_linker_warhead_boundary_bond: ""
reviewed_minimal_seed_atom_ids: ""
primary_anchor_atom: ""
direction_anchor_atom: ""
optional_plane_anchor_atom: ""
reviewer_id: ""
review_rationale: ""
review_notes: ""
```

### Decision: 5F2E/5UT

```yaml
candidate_identity: "5F2E/5UT"
review_status: ""  # APPROVE | REJECT | QUARANTINE
review_scope: ""  # EXACT_CHEMISTRY_SIGNATURE_REUSABLE | SAMPLE_BOUND_ONLY | QUARANTINE
independent_sample_assignment_decision: ""  # APPROVE | REJECT | QUARANTINE
reaction_family_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
reaction_family_id: ""
reaction_family_version: ""
warhead_rule_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
warhead_rule_id: ""
warhead_rule_version: ""
approved_warhead_smarts: ""
ligand_reactive_atom_map_number: ""
warhead_atom_map_numbers: ""
expected_pre_reaction_bond_orders: ""
allowed_formal_charge_pattern: ""
reviewed_warhead_atom_ids: ""
reviewed_warhead_attachment_atom_id: ""
reviewed_nonwarhead_boundary_atom_id: ""
reviewed_attachment_boundary_bond_order: ""
reviewed_scaffold_atom_ids: ""
reviewed_linker_atom_ids: ""
reviewed_warhead_role_atom_ids: ""
reviewed_scaffold_linker_boundary_bond: ""
reviewed_linker_warhead_boundary_bond: ""
reviewed_minimal_seed_atom_ids: ""
primary_anchor_atom: ""
direction_anchor_atom: ""
optional_plane_anchor_atom: ""
reviewer_id: ""
review_rationale: ""
review_notes: ""
```

### Decision: 6OIM/MOV

```yaml
candidate_identity: "6OIM/MOV"
review_status: ""  # APPROVE | REJECT | QUARANTINE
review_scope: ""  # EXACT_CHEMISTRY_SIGNATURE_REUSABLE | SAMPLE_BOUND_ONLY | QUARANTINE
independent_sample_assignment_decision: ""  # APPROVE | REJECT | QUARANTINE
reaction_family_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
reaction_family_id: ""
reaction_family_version: ""
warhead_rule_authority_action: ""  # BIND_EXISTING | NEW_AUTHORITY_REQUIRED | QUARANTINE
warhead_rule_id: ""
warhead_rule_version: ""
approved_warhead_smarts: ""
ligand_reactive_atom_map_number: ""
warhead_atom_map_numbers: ""
expected_pre_reaction_bond_orders: ""
allowed_formal_charge_pattern: ""
reviewed_warhead_atom_ids: ""
reviewed_warhead_attachment_atom_id: ""
reviewed_nonwarhead_boundary_atom_id: ""
reviewed_attachment_boundary_bond_order: ""
reviewed_scaffold_atom_ids: ""
reviewed_linker_atom_ids: ""
reviewed_warhead_role_atom_ids: ""
reviewed_scaffold_linker_boundary_bond: ""
reviewed_linker_warhead_boundary_bond: ""
reviewed_minimal_seed_atom_ids: ""
primary_anchor_atom: ""
direction_anchor_atom: ""
optional_plane_anchor_atom: ""
reviewer_id: ""
review_rationale: ""
review_notes: ""
```

Approval of a record does not itself write a production dataset member. A
successor must verify the completed record, bind sample-scoped or exact-signature
authority, derive the profile and seed gates, assign leakage group and split,
and only then materialize and tensorize Exact16+N with POST-only / PRE-masked
geometry supervision.
