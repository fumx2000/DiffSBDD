# FFQ `warhead_only` pocket-conditioning dependency probe V1

## Scope and conclusion

The first phase was a test-only, offline probe that directly called the
unchanged production `_build_checkpoint_model_input_pocket_v1` selector. It
compared that selector when seeded by all eight clean-ligand heavy atoms with a
test prototype seeded only by the Formal-owned fixed scaffold atoms `O2`,
`O3`, `O4`, and `P1`. The follow-on phase implements that seed choice behind
an explicit, default-disabled public assembler policy. Protein source, model 1,
blank/A altloc handling, standard-AA residue-level selection, strict `< 8 Å`,
source order, and exact-10 element projection remain unchanged.

The result is positive for pocket-membership dependence: moving only generated
warhead coordinates changes the full-ligand-selected pocket in the synthetic
boundary control and in 22 of the 24 predeclared real-3VCY perturbations. The
fixed-scaffold prototype is invariant in all corresponding generated-coordinate
controls. On the unperturbed four real events it selects fewer residues and
atoms than the current full-ligand path, but it retains exactly one target
CYS116 residue and exactly one SG atom in every event.

The follow-on changes one production assembler module and the existing test and
explanation files. No State file, target, loss, split, admission, model
forward, training input, consumer, or checkpoint was created or changed.

## Frozen sources

| Source | Frozen identity |
| --- | --- |
| Repository baseline | `c5cdc659c444f5a868c60b0d28d1fecbbaefd0ed` |
| Baseline production module | SHA256 `e1f52c5037396bb51288cbdca9aa9e8e5f803f587d0e6eff20d04a6f9d63ea38`; Git blob `fb4cd8c81ad499869e5a6728b63fc58621c2a654` |
| Unchanged low-level selector function | 2,395 source bytes; SHA256 `9f833301cb9c08fc49f2429596deca5ee97a734eef020cb4042f3a92e054f3ef` before and after the follow-on implementation |
| Scoped POST-use delta (problem-location evidence only) | SHA256 `fa93e448469b77f798bbcea483f2948cf49a77775f0fa02ba2130ca30939f70d` |
| Exact4 input-alignment report | 75,121 bytes; SHA256 `2497ce0600f41fb01ab8f0fcdbcd1aa9bccb21b659f077496d988307953928ef` |
| Existing role/sample Formal | SHA256 `ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149` |
| POST label-use Formal | SHA256 `8f3297435525ab68501046f811aa32ae7dbd8ab30c6bcafcafc988aada89468d` |
| Bound real structure | `covapie-state/bulk-model-usable-auto-admission-scaleup-v1/ranks-0501-1000/attempt-001/cache/rcsb/structures/3VCY.cif.gz`; 353,235 compressed bytes; SHA256 `80f00b3dfd6a743ef4cb768cb2959261920a071d362cafa7ce083fc78194bc00` |

The structure path was obtained from the frozen alignment report's source
binding. The compressed identity was proven before parsing; decompression was
in memory only. Missing, symlinked, malformed, or hash-mismatched inputs fail
closed with an explicit `BLOCKED` error. The State root may be set with
`COVAPIE_STATE_ROOT`; otherwise it defaults to the repository's sibling
`covapie-state` directory.

The four full event IDs are read from the existing Formal and must exactly
match both the POST label-use Formal and the alignment report. Each event's
own label/auth identities and source rows are checked independently:

- `3VCY A/CYS116/SG` with FFQ label asym `E`
- `3VCY B/CYS116/SG` with FFQ label asym `J`
- `3VCY C/CYS116/SG` with FFQ label asym `O`
- `3VCY D/CYS116/SG` with FFQ label asym `T`

The Formal role partition is the semantic authority: scaffold/fixed is exactly
`O2,O3,O4,P1`; warhead/generated is exactly `C1,C2,C3,O1`; linker is empty.
Those roles, fixed/generated flags, atom names, atom-site IDs, source rows,
label asym, auth asym, component, model, and exact-10 projection are
cross-checked against the structure report and raw mmCIF rows. Event A's rows
are not reused for B, C, or D.

## Synthetic controls

The synthetic case has an always-near ALA residue, a probe ALA atom at
`x=8.5 Å`, and all ligand seed atoms initially at `x=0`. It uses the real
production selector rather than a copied selector.

| Control | Observed result |
| --- | --- |
| A: move only generated atoms by `+1 Å` on x | Full-ligand membership changes from source row 0 only to rows 0 and 1; the probe crosses from 8.5 Å to 7.5 Å. |
| B: apply the same generated move to fixed-only selection | Fixed-scaffold membership remains source row 0 only. |
| C: move the fixed scaffold by `+1 Å` on x | Fixed-scaffold membership changes from source row 0 only to rows 0 and 1, proving that the prototype actually recomputes selection. |
| D: put NaN in generated x coordinates | Fixed-scaffold membership remains identical to its finite baseline. Full-ligand selection rejects with the existing `LIGAND_COORDINATES_INVALID` policy; this expected rejection is not treated as a business-gate failure. |

These are data-channel interventions, not new chemical structures, plausible
conformations, or experimental structural evidence.

## Real Exact4 baseline comparison

Counts below are retained heavy atoms after legal exact-10 projection and
selected standard-AA residues. `Fixed added/removed` is measured relative to
the current full-ligand result. All selections were repeated and were
byte-for-byte identical in ordered source identity.

| Event | Full atoms / residues | Fixed atoms / residues | Fixed added | Fixed removed | CYS116 atoms / SG (full; fixed) | 10D / source order |
| --- | ---: | ---: | --- | --- | --- | --- |
| A/E | 218 / 27 | 164 / 20 | none | 54 atoms in 7 residues: `A23-LYS,A113-PRO,A114-GLY,A119-GLY,A329-PHE,A332-ARG,B334-MET` | 6 / 1; 6 / 1 | legal / deterministic |
| B/J | 210 / 26 | 165 / 21 | none | 45 atoms in 5 residues: `A334-MET,B119-GLY,B329-PHE,B332-ARG,B372-ARG` | 6 / 1; 6 / 1 | legal / deterministic |
| C/O | 199 / 25 | 176 / 22 | none | 23 atoms in 3 residues: `C119-GLY,C329-PHE,D334-MET` | 6 / 1; 6 / 1 | legal / deterministic |
| D/T | 198 / 25 | 164 / 21 | none | 34 atoms in 4 residues: `D119-GLY,D329-PHE,D332-ARG,D334-MET` | 6 / 1; 6 / 1 | legal / deterministic |

The current full counts reproduce the previously passed `218,210,199,198`
heavy-node baseline. The fixed-only counts are observations, not required
baseline values. Because the fixed seed is a subset of the full seed, the
unperturbed fixed pockets add no residue and remove the explicitly identified
full-only residues above.

## Real generated-coordinate interventions

The intervention set was fixed before observing results: translate all of
`C1,C2,C3,O1` together by `+1 Å` and `-1 Å` independently on x, y, and z.
Protein rows, fixed rows, source identity, and roles remain unchanged. Every
row in the following table is a fresh call to the real selector. The fixed
prototype stayed at its event baseline membership for all 24 rows and retained
one SG; full selection also retained one SG in all rows.

| Event | Generated translation | Full atoms / residues | Membership | Added source identities | Removed source identities |
| --- | --- | ---: | --- | --- | --- |
| A/E | x +1 Å | 226 / 28 | changed | `A306-ASP` | none |
| A/E | x -1 Å | 207 / 26 | changed | none | `A329-PHE` |
| A/E | y +1 Å | 218 / 27 | changed | `B338-GLU` | `A23-LYS` |
| A/E | y -1 Å | 226 / 28 | changed | `A306-ASP` | none |
| A/E | z +1 Å | 200 / 25 | changed | none | `A113-PRO,A329-PHE` |
| A/E | z -1 Å | 218 / 27 | unchanged | none | none |
| B/J | x +1 Å | 204 / 26 | changed | `B120-ALA` | `B372-ARG` |
| B/J | x -1 Å | 207 / 26 | changed | `B334-MET` | `B329-PHE` |
| B/J | y +1 Å | 202 / 25 | changed | none | `A334-MET` |
| B/J | y -1 Å | 196 / 25 | changed | `B334-MET` | `B329-PHE,B372-ARG` |
| B/J | z +1 Å | 199 / 25 | changed | none | `B372-ARG` |
| B/J | z -1 Å | 223 / 28 | changed | `B334-MET,B373-ALA` | none |
| C/O | x +1 Å | 205 / 26 | changed | `D338-GLU,D367-MET` | `C329-PHE` |
| C/O | x -1 Å | 223 / 28 | changed | `C120-ALA,C306-ASP,C372-ARG` | none |
| C/O | y +1 Å | 226 / 28 | changed | `C334-MET,C372-ARG,D367-MET` | none |
| C/O | y -1 Å | 199 / 25 | unchanged | none | none |
| C/O | z +1 Å | 228 / 29 | changed | `C120-ALA,D337-PRO,D338-GLU,D367-MET` | none |
| C/O | z -1 Å | 210 / 26 | changed | `C372-ARG` | none |
| D/T | x +1 Å | 179 / 23 | changed | none | `D329-PHE,D334-MET` |
| D/T | x -1 Å | 211 / 27 | changed | `D120-ALA,D331-ASN` | none |
| D/T | y +1 Å | 190 / 24 | changed | none | `D334-MET` |
| D/T | y -1 Å | 206 / 26 | changed | `D331-ASN` | none |
| D/T | z +1 Å | 209 / 26 | changed | `D372-ARG` | none |
| D/T | z -1 Å | 176 / 23 | changed | none | `D329-PHE,D332-ARG` |

### Source-identity catalog for all reported deltas

Every catalog entry is a model-1, blank-altloc standard-AA residue with no
insertion code. A row range is zero-based; an ID range is the corresponding
`_atom_site.id` range. Atom names are in mmCIF source order. Together these
fields identify the actual source atoms compared by the test, rather than only
their counts.

| Shorthand | Source rows / atom-site IDs | Atom identities |
| --- | --- | --- |
| `A23-LYS` | 162-170 / 163-171 | N, CA, C, O, CB, CG, CD, CE, NZ |
| `A113-PRO` | 847-853 / 848-854 | N, CA, C, O, CB, CG, CD |
| `A114-GLY` | 854-857 / 855-858 | N, CA, C, O |
| `A119-GLY` | 881-884 / 882-885 | N, CA, C, O |
| `A306-ASP` | 2254-2261 / 2255-2262 | N, CA, C, O, CB, CG, OD1, OD2 |
| `A329-PHE` | 2426-2436 / 2427-2437 | N, CA, C, O, CB, CG, CD1, CD2, CE1, CE2, CZ |
| `A332-ARG` | 2454-2464 / 2455-2465 | N, CA, C, O, CB, CG, CD, NE, CZ, NH1, NH2 |
| `A334-MET` | 2476-2483 / 2477-2484 | N, CA, C, O, CB, CG, SD, CE |
| `B119-GLY` | 4004-4007 / 4005-4008 | N, CA, C, O |
| `B120-ALA` | 4008-4012 / 4009-4013 | N, CA, C, O, CB |
| `B329-PHE` | 5556-5566 / 5557-5567 | N, CA, C, O, CB, CG, CD1, CD2, CE1, CE2, CZ |
| `B332-ARG` | 5584-5594 / 5585-5595 | N, CA, C, O, CB, CG, CD, NE, CZ, NH1, NH2 |
| `B334-MET` | 5606-5613 / 5607-5614 | N, CA, C, O, CB, CG, SD, CE |
| `B338-GLU` | 5639-5647 / 5640-5648 | N, CA, C, O, CB, CG, CD, OE1, OE2 |
| `B372-ARG` | 5878-5888 / 5879-5889 | N, CA, C, O, CB, CG, CD, NE, CZ, NH1, NH2 |
| `B373-ALA` | 5889-5893 / 5890-5894 | N, CA, C, O, CB |
| `C119-GLY` | 7128-7131 / 7129-7132 | N, CA, C, O |
| `C120-ALA` | 7132-7136 / 7133-7137 | N, CA, C, O, CB |
| `C306-ASP` | 8520-8527 / 8521-8528 | N, CA, C, O, CB, CG, OD1, OD2 |
| `C329-PHE` | 8692-8702 / 8693-8703 | N, CA, C, O, CB, CG, CD1, CD2, CE1, CE2, CZ |
| `C334-MET` | 8742-8749 / 8743-8750 | N, CA, C, O, CB, CG, SD, CE |
| `C372-ARG` | 9020-9030 / 9021-9031 | N, CA, C, O, CB, CG, CD, NE, CZ, NH1, NH2 |
| `D119-GLY` | 10271-10274 / 10272-10275 | N, CA, C, O |
| `D120-ALA` | 10275-10279 / 10276-10280 | N, CA, C, O, CB |
| `D329-PHE` | 11838-11848 / 11839-11849 | N, CA, C, O, CB, CG, CD1, CD2, CE1, CE2, CZ |
| `D331-ASN` | 11858-11865 / 11859-11866 | N, CA, C, O, CB, CG, OD1, ND2 |
| `D332-ARG` | 11866-11876 / 11867-11877 | N, CA, C, O, CB, CG, CD, NE, CZ, NH1, NH2 |
| `D334-MET` | 11888-11895 / 11889-11896 | N, CA, C, O, CB, CG, SD, CE |
| `D337-PRO` | 11914-11920 / 11915-11921 | N, CA, C, O, CB, CG, CD |
| `D338-GLU` | 11921-11929 / 11922-11930 | N, CA, C, O, CB, CG, CD, OE1, OE2 |
| `D367-MET` | 12124-12131 / 12125-12132 | N, CA, C, O, CB, CG, SD, CE |
| `D372-ARG` | 12160-12170 / 12161-12171 | N, CA, C, O, CB, CG, CD, NE, CZ, NH1, NH2 |

## What this proves and does not prove

This proves an algorithmic data dependency in current pocket membership: the
full-clean-ligand selector is allowed to use generated `warhead_only` atom
coordinates, and the controlled boundary input demonstrates that this channel
can change selected source identities. The real results establish actual
sensitivity for these four bound 3VCY events under this fixed, finite set of
interventions. The two unchanged real interventions are reported as unchanged;
they do not establish global independence. The fixed-scaffold test prototype
does not read generated coordinates and preserves target SG coverage for these
four events.

This does not show that a model exploited leakage, change a prediction, measure
generalization, validate a loss or target, establish that all conditioning
channels are safe, or prove global behavior for other structures, tasks, or
perturbations. Membership is compared by raw source identity and original
protein coordinates; no centered-coordinate byte comparison is used. Both
tested pockets are reselected from the current bound 3VCY structure. The
fixed-scaffold prototype is generated-coordinate-independent for the tested
membership channel, but it is not an externally and independently supplied
pocket. This pilot is not a general prohibition for all DiffSBDD tasks and does
not require an apo structure or accurate PRE.

Exact-10 dimensional legality does not imply unchanged pocket membership or
model behavior. The prototype removes 23-54 atoms on the unperturbed events,
so it should not be wired directly into production without a separately
authorized integration and distribution review.

## Explicit assembler policy implemented in the follow-on

The public function now has this keyword-only interface:

```python
assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
    *,
    samples,
    device="cpu",
    pocket_seed_policy="full_ligand_v1",
)
```

Exactly two policy strings are accepted:

- `full_ligand_v1` is the default and passes all retained ligand heavy rows to
  the unchanged selector. An explicit value is tensor-for-tensor identical to
  omitting the argument, and the historical `218,210,199,198` Exact4 counts
  remain unchanged.
- `fixed_scaffold_warhead_only_v1` is accepted only for canonical
  `warhead_only`, task ID 0. It passes only the validated fixed scaffold rows to
  the same selector. It is not a sixth task, a new mask, or new human
  authority.

Unknown strings, case/space variants, `None`, bools, integers, and string
subclasses fail closed. The new branch validates record-to-role binding,
scaffold/warhead projected indices, exact tensor dtype and shape, range,
uniqueness, fixed/generated complement and non-overlap, parser-local mapping,
retained node order, source row and atom-site identity, and scaffold atom
identity before using any seed index. Empty or contradictory seeds do not fall
back to the full ligand. The seed is emitted in retained source order, so a
permuted ligand with an explicit hydrogen removed still selects `O2,O3,O4,P1`
by identity rather than by position.

Altloc relevance is evaluated by the unchanged selector using exactly the
chosen seed. A synthetic non-A alternate residue near generated atoms but not
the fixed scaffold rejects the full policy and does not reject the fixed
policy. Invalid fixed coordinates still reject at selector level. Invalid
generated coordinates are not read by fixed-seed selection, but the public
assembler continues to reject them later when it validates and constructs the
complete ligand tensor.

## Public Exact4 execution and index reconstruction

The real four-sample public call uses the published input reader, receipt and
canonical-authority validator, pure effective-supervision successor builder,
and successor validator. It selects the four complete 3VCY event records by
full event ID. It does not call `_expected_record`, run the old diagnostic CLI,
rewrite a report, or materialize effective supervision.

| Event | Default/full nodes | Fixed nodes | Fixed pocket span | SG source row | SG local / flat | Target coverage |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| A/E | 218 | 164 | `[0,164)` | 867 | 64 / 64 | one CYS116 (6 atoms), one SG |
| B/J | 210 | 165 | `[164,329)` | 3990 | 84 / 248 | one CYS116 (6 atoms), one SG |
| C/O | 199 | 176 | `[329,505)` | 7114 | 84 / 413 | one CYS116 (6 atoms), one SG |
| D/T | 198 | 164 | `[505,669)` | 10257 | 83 / 588 | one CYS116 (6 atoms), one SG |

The reconstructed ligand offsets are `(0,8,16,24,32)` and pocket offsets are
`(0,164,329,505,669)`. Ligand C1 local indices are `(0,0,0,0)` and flat indices
are `(0,8,16,24)`. Positive-pair local and flat indices equal the independently
recomputed ligand C1 and pocket SG indices, every mask segment belongs to its
own sample, each SG is sulfur channel 3 in the unchanged
`C,N,O,S,B,Br,Cl,P,I,F` order, and all 669 pocket rows are exact one-hot. All
training-admission, geometry-target, and warhead-type-target flags remain
false. A synthetic 4R7U task-0 fixed-policy call retains its historical human
training exclusion and remains unadmitted.

## Selector probe versus public-entry evidence

The earlier 24 real interventions remain low-level selector evidence: six
predeclared generated-coordinate translations for each of four 3VCY events,
with 22/24 full-ligand membership changes and 24/24 fixed-prototype membership
invariances. They are not relabeled as public assembler executions.

The new public-entry real intervention is deliberately smaller: event A/E with
all generated `C1,C2,C3,O1` coordinates translated by `+1 Å` on x, entirely in
memory. Through the public assembler, fixed-policy source membership remains
164 nodes and identical, while full-policy membership changes from 218 to 226.
The complete fixed-policy model input is not invariant: retained ligand
coordinates and joint centering still change. Additional synthetic public tests
cover default-versus-explicit-full equality, ligand permutation plus legal H
removal, seed-sensitive altloc handling, missing target SG, generated NaN
rejection by the complete assembler, and precise policy/role/mapping failures.

This follow-on handles only the pocket-membership seed dependency. It changes
pocket membership and the checkpoint input distribution. Preserving the 10D
schema and return interface is not checkpoint-behavior equivalence or a
performance guarantee. No production training caller was automatically
migrated to the new policy. Consumer migration, distribution acceptance,
split/admission, target/loss activation, model regression, and training remain
separate closed gates. An externally specified independent pocket, if later
used, must remain a distinct input mode and authority path; the implemented
fixed seed still reselects from the bound structure.

This probe does not establish training readiness. Before any formal training or
training-preparation work, the required feature-semantics audit still applies;
Step12D remains a smoke-legality check rather than a final training-feature
contract, and the historical `UNKNOWN_ATOM_FEATURE_POLICY` /
`feature_semantics_known=False` state must be resolved or formally audited.
