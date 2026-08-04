# CovaPIE Current11 reaction-family and approved-warhead-rule authority binding V1

## Outcome

This metadata-only gate reaches conclusion C: the Current11 candidate identities
are structurally consistent and exact-one, but neither reaction-family authority
nor approved-warhead-rule authority is present.

- Reaction-family authority: `0/11 authoritative_resolved`, `11/11 candidate_only`.
- Approved-warhead-rule authority: `0/11 authoritative_resolved`, `11/11 candidate_only`.
- Role-proposal readiness: false.
- Minimal-seed-proposal readiness: false.

The only recommended next increment is:

```text
materialize_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1
```

This gate does not create that review package.

## Three separate questions

The gate keeps three questions independent:

1. Candidate identity is exact-one for all 11 samples.
2. Reaction-family identity is not explicitly approved for any sample.
3. Complete warhead-rule semantics are not explicitly approved for any rule.

The candidate assignment, effective boundary authority, pre-reaction graph,
reaction delta, ligand reactive atom, and target `CYS:SG` agree for all 11
samples. This proves structural consistency of the candidates. It does not
promote either candidate namespace to approved authority.

## Human-review scope

The legacy review unit is explicitly
`sample_warhead_atom_set_and_attachment_boundary`. Its frozen identity fields
include `reaction_family_id` and `warhead_rule_id`; its human-fillable fields
cover decision, selected boundary candidate, reviewed warhead atoms, reviewed
boundary, rationale, notes, reviewer provenance, and completion.

The multi-boundary schema similarly freezes family/rule IDs before the
human-fillable fields. Its decisions cover acceptance, revision, or quarantine
of a warhead atom set and exactly two attachment boundaries.

Consequently, all 11 rows have:

```text
boundary_review_completed = true
selected_candidate_identity_attested = true
reaction_family_identity_explicitly_attested = false
warhead_rule_identity_explicitly_attested = false
warhead_rule_full_semantics_explicitly_attested = false
approved_structural_pattern_attested = false
```

Reviewer identity, rationale, completion, and provenance do not widen the
declared review unit. A family/rule ID carried through a frozen identity column
is lineage, not an attestation of the referenced object's complete semantics.

## Review-state transport lineage

The gate validates the historical builder contracts and real state bytes at
every transport hop. The legacy submission S02 is linked to legacy ingestion
S03 by both filesystem SHA and canonical submission SHA. The multi-boundary
chain then links S02 and S03 into submission S04, links S02/S03/S04 into
ingestion S05, and links S03/S05 into authority bundle S06. S01 directly binds
the S02, S03, S05, and S06 filesystem bytes and their formal internal bundle
digests. S01 has no direct S04 field, so the S01 -> S05 -> S04 link is required
and validated transitively. Each formal S03--S06 and S01 self-digest is
recomputed over canonical JSON with its digest field excluded.

For formal-state source-inventory rows S01--S06, `source_commit` means the
final transitive binder commit. Each `lineage_note` therefore says
`transitively bound through unified effective authority view` and separately
records the direct producer commit. This preserves both the transitive binding
semantics and the historical builder lineage.

## Minimum family authority contract

An authoritative sample-level family requires exact sample identity, exact-one
candidate identity, agreement with the active effective boundary authority,
frozen family namespace/version and structural basis, consistency with the
pre-reaction graph/reaction delta/reactive atoms/`CYS:SG`, explicit curated or
human authority whose scope includes family identity, complete transport
lineage, and an active non-quarantined authority record.

Current evidence lacks the frozen family version/structural basis and explicit
family-identity attestation.

## Minimum approved-rule contract

The predecessor freezes these required fields:

```text
reaction_family_id
reaction_family_version
target_residue_types
target_residue_reactive_atom_name
warhead_smarts
ligand_reactive_atom_map_number
warhead_atom_map_numbers
warhead_attachment_atom_map_number
expected_pre_reaction_bond_orders
allowed_formal_charge_pattern
allowed_match_count
priority
```

In addition, this gate requires frozen identity/version, an authoritative
family, complete warhead and attachment-boundary contracts, leaving-group and
formed-bond semantics, ambiguity and tie policy, explicit full-rule approval,
and an active non-quarantined authority.

The candidate registry contains exact local graph signatures and useful
reaction-delta evidence. Every candidate rule nevertheless remains
`approved=false`, `human_gold_review_completed=false`; approved SMARTS is empty.
No committed predecessor contract declares a graph signature to be a formally
equivalent approved structural representation. Therefore the candidate graph
signature is not copied into the approved structural-representation fields.

## Artifacts and status vocabulary

The five artifacts are a source inventory, Exact11 binding matrix, seven-row
unique family/rule registry, 41-case failure matrix, and manifest. X39--X41
independently reject legacy submission/ingestion, multi submission/ingestion,
and multi ingestion/authority transport mismatches. Authority
status is a closed vocabulary:

```text
authoritative_resolved
candidate_only
missing
conflicted
```

Missing formal fields stay empty and appear in blocker columns. Candidate
semantic names are not copied into formal family/rule semantic-name fields.

## Public API and lifecycle

The only public API is:

```python
evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1(
    *,
    repo_root: Path,
) -> dict[str, object]
```

It is keyword-only, deterministic, silent on import, and read-only. The final
response field is the SHA256 of unsigned canonical JSON. The lifecycle profiles
are exactly:

```text
binding_precommit_candidate
binding_committed_unpushed
binding_published_successor
```

The live worktree blob and index blob are validated independently. The
response lifecycle is bound to eight Git-derived witness fields. The current
candidate tree is expected to report `binding_precommit_candidate` for review.
The live test is branch-aware: it validates the Exact9 untracked candidate in
precommit state, the exact formal commit identity in committed-unpushed state,
or the retained formal commit identity beneath unrelated published successors.
It does not pin the full suite permanently to precommit state.

All response integer fields use exact `int` types, so `False` cannot impersonate
zero and `True` cannot impersonate a positive count. Boolean, string, tuple,
and record-dictionary containers likewise retain exact scalar/container types.
Valid-looking committed and published lifecycle substitutions are rejected
against the frozen external Git witness even after the response digest is
recomputed.

## Execution boundary

No raw structure, PDB, SDF, network, RDKit, SMARTS matching, Murcko, BRICS,
topology restoration, role proposal, minimal seed, review package, tensor,
loader, model, loss, checkpoint, forward/backward, training, fine-tuning,
reward, or RL operation is performed.

The canonical V1 mask contract remains exactly five tasks, including
`scaffold_only` / B3. Formal training still requires the feature-semantics
audit; Step12D remains only a smoke legality check and not a final
training-feature contract.
