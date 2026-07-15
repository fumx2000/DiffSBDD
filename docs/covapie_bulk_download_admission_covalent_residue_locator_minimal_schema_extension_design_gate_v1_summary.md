# CovaPIE covalent residue locator minimal schema extension design gate v1

Step14AU-E0-P2 freezes a metadata-only design for five candidate fields needed
before covalent residue identity semantics can be completed. It does not modify
the current 17-field admission schema, the 18 evaluation contexts, ADMIT_004, a
sample-index producer, or the structure parser.

## Why the extension is required

The tracked producers prefer `auth` chain and residue-index values and fall back
to `label` values independently. The resulting chain and index do not preserve
which PDBx/mmCIF namespace supplied each value, so a downstream evaluator cannot
prove that both locator components came from one namespace. Independent fallback
can therefore create a mixed locator even when both output strings are present.

The tracked parser also does not read an insertion-code tag. Not reading a tag,
receiving an empty value, or observing a numeric residue index does not prove
that an insertion code is absent. All 11 tracked samples consequently retain an
`unknown` insertion-code state.

The backfill audit is grounded in two committed sample-index CSV files and the
11 exact committed covalent-event tables referenced by those rows. Sample IDs,
PDB IDs, selected values, auth/label values, and conflicts are joined and checked
from those files. Python source-name occurrence and hard-coded conflict booleans
are not accepted as row evidence.

## Proposed fields

The design proposes exactly these five candidate metadata fields:

1. `covalent_residue_locator_namespace`
2. `covalent_residue_insertion_code_state`
3. `covalent_residue_insertion_code`
4. `covalent_residue_locator_provenance_source_id`
5. `covalent_residue_locator_provenance_sha256`

The namespace is exactly `auth` or `label` and must govern both chain and residue
index. Mixed namespaces are forbidden. Insertion state is exactly `absent`,
`present`, or `unknown`: `absent` and `unknown` require an empty value, while
`present` requires a nonempty basic value. The complete grammar for a present
value is intentionally not frozen. `unknown` remains blocking for ADMIT_004.

The source ID and lowercase SHA256 fields preserve evidence provenance without
requiring the evaluator to dereference a path. They are paired, caller-supplied
metadata and are distinct from candidate, PDB, and duplicate identities.

## Existing-sample audit

The fixed 11-row audit finds three `AUTH_LABEL_CONFLICT` samples and eight
`NAMESPACE_PROVABLE_INSERTION_UNKNOWN` samples. All 11 rows use the `auth`
locator selected by tracked evidence, all 11 insertion states remain `unknown`,
and none is admissible for E1 merely because this schema design exists. No sample
has proven insertion-code absence and no sample is fully provable pre-download.

## Boundaries and readiness

The D2 effective schema remains unchanged. The five fields are not integrated,
ADMIT_004 is not ready, E1 residue identity semantics design is not ready, and
the independent atom-name normalization blocker remains open. The gate permits a
future schema-integration step only; it does not authorize candidate evaluation,
bulk download, model execution, or training.

The integration recommendation is conditional on every source, predecessor,
representation, contract, backfill, safety, and issue check passing. A failed
gate recommends resolving the schema-extension design blockers instead of
continuing to integration.

The canonical mask scope remains exactly `warhead_only / A`,
`linker_plus_warhead / B`, `scaffold_plus_warhead / B2`,
`scaffold_only / B3`, and `scaffold_plus_linker_plus_warhead / C`. Formal
training, fine-tuning, or real parameter updates still require a separate feature
semantics audit.
