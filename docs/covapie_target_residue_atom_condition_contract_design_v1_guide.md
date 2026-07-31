# CovaPIE target residue-atom condition contract design V1

## What this step decides

This is a private, read-only design and audit artifact. It defines what future
evidence must say before CovaPIE may claim that a Current11 sample points to one
specific protein atom. It does not create a condition authority record, a
condition tensor, an adapter, an encoder, a training label, or any model or
training change.

Knowing only that the project studies Cys-SG chemistry is not enough. A protein
structure may contain many cysteines, several chains, multiple models, insertion
codes, and alternate atom locations. A condition adapter therefore needs
sample-level evidence for which chain, which residue, which SG atom, which model,
and which altloc is intended. The V1 CYS/SG/S values must be observed in that
evidence; they are not defaults supplied from project scope.

## Canonical atom identity

V1 uses the mmCIF author namespace as its canonical external locator:

1. `protein_auth_asym_id`
2. `protein_auth_comp_id`
3. `protein_auth_seq_id`
4. `protein_pdbx_PDB_ins_code`
5. `protein_auth_atom_id`

The label namespace (`label_asym_id`, `label_comp_id`, `label_seq_id`, and
`label_atom_id`) is retained as a crosswalk to the same `_atom_site` row. Label
values cannot silently replace missing author values. Author and label sequence
or chain identifiers need not be textually equal: the point of retaining both
namespaces is to bind their different identifiers to one row. Their residue and
atom semantics must nevertheless agree with the V1 CYS-SG/S scope.

`pdbx_PDB_model_num` must be present in source evidence. The contract never
assumes model 1. Likewise, insertion code comes from
`_atom_site.pdbx_PDB_ins_code`; absence of that source column is a schema gap,
not proof that the insertion code is empty. When the explicit source token is
`.` or `?`, V1 normalizes it to the empty string while retaining the contractual
fact that normalization occurred.

Altloc comes from `label_alt_id`. Its `.` and `?` tokens normalize to empty, but
real values such as `A` or `B` are preserved. This matters because the historical
full-atom smoke selected atom-site row `659` with altloc `B` for `HR_0002`.
Discarding `B` would change which physical row the evidence selected.

`atom_site_id` identifies the exact source row. It is lineage and audit evidence,
not a model feature. If source evidence specifies an atom-site ID, V1 follows
that ID and does not reselect a conformer by occupancy. There is no
highest-occupancy fallback, spatial nearest-neighbour inference, "only CYS in the
PDB" inference, or inference from a ligand-internal warhead boundary. Zero
matching rows and multiple matching rows both fail closed.

## Unique locator is not yet materializable authority

“唯一定位到 Cys-SG atom row”仍不等于“可以物化 condition authority”。The
locator contract answers *which atom*: it requires one complete CYS/SG/S row
with explicit model, auth identity, label crosswalk, insertion-code source, and
altloc source. Authority materialization lineage answers a different question:
*which irreplaceable evidence proves that conclusion*.

For `resolved_unique`, V1 requires both layers. The evaluator must read exact
source structure bytes and independently recompute
`source_structure_filesystem_sha256`. It must also read exact sample-level
condition evidence and independently recompute its canonical SHA256. The
condition-evidence record digest excludes its own digest field and binds the
sample, PDB, ligand, selected atom-site ID, model, author residue-atom identity,
insertion code, and structure digest. A claimed 64-hex string, raw-path string,
PDB ID, atom-site ID, or merely existing locator-provider row is not sufficient.

The structure, evidence, atom table, and unified view must close around the same
sample/PDB/atom-site/model/auth identity. Missing exact bytes or evidence is
`schema_incomplete`; a referenced file that should exist but does not is
`missing_source`; a recomputed digest or identity conflict is
`lineage_mismatch`. Only a unique locator *and* complete materialization lineage
produce `resolved_unique`. The two conditions are inseparable at the authority
gate.

A future source inventory therefore needs, at minimum, sample/PDB/ligand IDs,
safe references to exact structure bytes and the protein atom table,
independently verified structure and evidence SHA256 values, selected
atom-site ID, exact condition evidence, and the complete selected
model/auth/label identity. These are future requirements, not fields claimed to
exist in the current Current11 sample index.

The seven locator semantics reserved for a future condition adapter are model
number, the five author-namespace identity parts, and label altloc. Even those
values are locators, not ready-made numeric or categorical features. In
particular, raw `auth_seq_id` is not a numeric model feature. `pdb_id`, label
crosswalk values, atom-site ID, status, and source digests are audit/lineage only.

## What the historical full-atom smoke proves

Commit `efe213bae26d30b98272973ff557e7fbf3dc577d` and its production, schema,
tests, and generated protein table prove that the repository can parse and
report atom-site ID, element, author and label identities, model number, altloc,
and protein/residue/endpoint flags. They also provide the important altloc-B
case.

That was an early extraction smoke, not Current11 authority. Its `HR_0002` to
`HR_0004` samples are `6DI9`, `5F2E`, and `6OIM`, not the Current11 samples, so
they contribute 0/11 Current11 coverage. Its table also does not explicitly
provide `pdbx_PDB_ins_code`; this contract records that as a schema gap and does
not assume insertion codes are always empty.

## Formal Current11 audit result

The formal unified effective authority view was read as exact bytes and checked
against its frozen filesystem and internal SHA256 values. Its Exact16 envelope,
11 ordered Exact10 records, embedded authority validators, 6 legacy plus 5
multi-boundary split, record digests, and sample/PDB/ligand identities passed.
The builder was not rerun.

The repository also contains an 11-row unified sample index, its referenced
protein atom tables, and an 11-row residue-locator provider sidecar. These are
useful candidate evidence, but not a complete condition authority. The existing
protein tables use reduced/generic atom and residue columns instead of the full
explicit mmCIF author/label contract and omit an explicit
`pdbx_PDB_ins_code`. The sidecar is itself marked blocking and reports insertion
provenance as unknown. Current11 also lacks a complete source inventory that
provides exact structure bytes, independently verified structure digests,
canonical sample-level condition evidence, and independently verified evidence
digests. Thus neither locator completeness nor materialization lineage is fully
closed for the formal 11. Combining the current artifacts must not be promoted
silently into an Exact20 authority record.

The formal result is consequently:

- Current11 samples audited: 11
- `resolved_unique`: 0
- `schema_incomplete`: 11
- blocked: 11
- ready to implement target-condition authority: false
- next step: `implement_covapie_current11_target_residue_atom_condition_source_inventory_v1`

This is an evidence result, not a preset count. A future complete source can
reach `resolved_unique` only when one same-sample atom-site row has all explicit
model, author, label, insertion, altloc, element, source-ID, and lineage
semantics, and when exact structure/evidence bytes independently reproduce their
claimed digests and bind back to that same atom. The future materialization gate
must admit only
`resolved_authoritative`; missing, ambiguous, lineage-mismatched, and
schema-incomplete cases remain blocked.

## Frozen future record and remaining boundaries

The design freezes an Exact20 future condition record, 19 Exact12 semantic
field-contract records (the twentieth field is the record digest), Exact12
source-candidate audit records, 11 Exact10 coverage records, and an Exact14
design response. These objects exist only in memory in this step. No formal
condition JSON/CSV, manifest, label, tensor, or derived asset was materialized.

The next source-inventory step must close these source-evidence gaps. It is not a
model-code, adapter, tensor, or training task.

Completing target residue-atom condition authority would still not create the
ligand-to-residue atom-pair label. That pair label is a separate next contract;
pre/post covalent geometry is separate again. Formal training remains blocked
until a feature-semantics audit is completed, including the historical unknown
atom-feature policy. Step12D remains only a smoke-legality check, not the final
training-feature contract.
