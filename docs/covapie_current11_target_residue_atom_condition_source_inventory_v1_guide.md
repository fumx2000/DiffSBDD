# Current11 target-residue atom-condition source inventory V1

## What this step does

This step answers a narrow audit question: for each Current11 sample, what target-residue atom-condition source material is already declared, what can be read and independently verified, and what is still missing or inconsistent?

The builder combines the committed unified effective authority view, unified sample index, residue-locator sidecar, referenced protein atom tables, declared structure/evidence locators and SHA256 claims, and the committed target-condition contract-design audit. It returns one deterministic JSON byte string. It does not write that byte string to a file.

The inventory is not a condition authority. An inventory observes source availability and preserves the contract design's coverage decision; it does not select a new authoritative atom, fill a missing chain/residue/model/insertion/altloc value, or authorize an adapter. The only coverage authority in this step is the committed contract design at `fb59a976f6faaa58829f9a761ae4634bcb05a273`.

The source inventory must also be bound to the exact sample-index and locator-sidecar bytes audited by that committed design call. Validating the design response and the currently readable files separately is not enough: the exact source-candidate SHA256 values must prove that both reads belong to the same snapshot. The builder does not create a filesystem transaction, but it compares the design-declared source path and SHA256 with the bytes it reads. If either source changes between those reads, or locator presence changes, the builder fails closed instead of combining provenance from two snapshots.

This snapshot binding does not create authority and does not add training logic. It only prevents old design coverage or source-candidate lineage from being mixed with new observations, row digests, or artifact statuses.

## The 21 required source fields

Every sample gets one field-observation record for each of these fields, in this order:

1. `sample_index_row_id`
2. `pdb_id`
3. `ligand_comp_id`
4. `source_structure_path`
5. `source_structure_filesystem_sha256`
6. `protein_atom_table_path`
7. `source_atom_site_id`
8. `source_condition_evidence_path_or_record`
9. `source_condition_evidence_sha256`
10. `protein_model_num`
11. `protein_auth_asym_id`
12. `protein_auth_comp_id`
13. `protein_auth_seq_id`
14. `protein_pdbx_PDB_ins_code`
15. `protein_auth_atom_id`
16. `protein_type_symbol`
17. `protein_label_alt_id`
18. `protein_label_asym_id`
19. `protein_label_comp_id`
20. `protein_label_seq_id`
21. `protein_label_atom_id`

No project-level Cys-SG scope is used to fill any of them. In particular, the builder never supplies model `1`, chain `A`, residue `CYS`, atom `SG`, an empty insertion code, or an empty altloc merely because those values might look plausible.

## Field observations and artifact statuses

A field observation distinguishes a missing column from a present-but-empty value. It also records the raw value, normalized value, provenance, blocking reasons, and its own canonical digest. This makes it possible to audit why a field counted as complete without treating an atom-table value or locator hint as an undeclared sample-index authority.

Only insertion code and altloc may normalize to an empty string. That empty value is accepted only when an actual atom row or locator source preserves an explicit mmCIF `.` or `?` token. An unexplained empty string is `missing_normalisation_provenance`. A nonempty altloc such as `B` is preserved exactly; there is no occupancy fallback.

Each sample also has exactly three artifact-status records: source structure, protein atom table, and condition evidence. Relative paths must stay inside `repo_root`; absolute paths, traversal, backslash escape, and symlinks are rejected. Missing declarations and missing files remain visibly different. Inline condition evidence is parsed as strict JSON.

Claimed SHA256 strings are not evidence by themselves. Structure SHA256 is recomputed from exact file bytes. Protein atom-table SHA256 is recorded from exact CSV bytes. Condition-evidence SHA256 is recomputed from the canonical evidence record with its own digest field omitted. This detects stale claims, altered bytes, malformed evidence, and lineage drift.

## Why the locator sidecar is not authority

The locator sidecar can show how many matching rows exist and which `atom_site_id` values they name. That is useful blocking evidence and selection provenance. It does not contain the complete condition identity or close the structure/evidence lineage, so a locator match cannot by itself change a sample to `resolved_unique` or ready.

## Current formal Current11 state

The formal in-memory preflight at the contract commit still reports:

- `resolved_unique=0`
- `missing_source=0`
- `schema_incomplete=11`
- `ambiguous_atom=0`
- `lineage_mismatch=0`
- `ready_for_target_condition_authority_implementation=false`

This `0/11` is not an implementation failure. It is a truthful inventory result: all 11 sample identities join correctly, but every referenced protein table still lacks the same seven contract columns (`label_atom_id`, `label_comp_id`, `label_alt_id`, `auth_atom_id`, `auth_comp_id`, `pdbx_PDB_model_num`, and `pdbx_PDB_ins_code`). The sample index also lacks declared structure path/SHA, atom-site identity, condition-evidence locator/SHA, and the future protein identity fields. The affected PDB entries are `6BV6`, `6BV8`, `6BV5`, `1AEC`, `1AIM`, `1AU3`, `1AU4`, `1AYU`, `1AYV`, `1AYW`, and `1B02` in sample order.

The builder reports the actual committed-design response on every call. If source state changes, it does not force these historical counts; it validates and reports the new result fail closed.

## Deliberate non-goals

This step does not download structures, make network requests, parse or regenerate raw mmCIF, modify any source table or sidecar, materialize a formal inventory file, create condition authority, implement an adapter, or generate a label, tensor, manifest, training input, or model change.

Formal training is still blocked on the feature-semantics audit. Step12D remains a smoke legality check, not the final training-feature contract; dataset materialization, checkpoint loading, sampling, or this source inventory cannot change that conclusion.

The single recommended next step is:

```text
materialize_covapie_current11_target_residue_atom_condition_source_inventory_v1
```

That materialization is intentionally not performed here.
