# CovaPIE Current11 tensor-projection payload builder V1

## Scope

This step implements a read-only, deterministic, standard-library-only builder for the five semantic tasks whose source-level extraction preconditions passed for all Current11 samples:

1. task 0, `sample_identity_supervision`;
2. task 1, `explicit_covalent_event_supervision`;
3. task 2, `ligand_residue_atom_pair_supervision`;
4. task 6, `warhead_boundary_supervision`;
5. task 12, `observed_complex_geometry_supervision`.

The result covers 11 samples in frozen Current11 order and 55 sample/task cells. “Exact5” in this step means these five audited semantic tasks. It does not mean the five canonical generation masks, and the builder does not create generation-mask sample labels.

The builder returns bytes only in memory. It does not write a formal payload, projection instance, availability matrix, tensor, NumPy artifact, candidate payload, checkpoint, or any other runtime artifact. It does not integrate with a dataloader, model, forward path, loss, optimizer, or training loop.

## Public API

The module exports one keyword-only API:

```python
build_covapie_current11_tensor_projection_payload_bundle_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]
```

Both roots must be absolute, resolved, existing non-symlink directories. The formal canonical path is derived only from `state_root`. There are no source, path, task, payload, dtype, shape, validity, digest, availability, loss, or schema overrides.

Every call verifies the frozen published contract-gate module SHA256, invokes its public API twice, requires byte-identical gate Exact4 outputs, and checks the published contract digest and non-materialization boundaries. The predecessor gate predates this successor Exact4, so a compatibility observation filters exactly the four authorized untracked successor paths from the predecessor's Git-status view. All other repository changes remain visible to that gate and fail closed. The payload builder defines no Git lifecycle profile and serializes no repository lifecycle data.

The builder independently snapshots and reads the formal routing sidecar, validates its Exact4 identities, selects exactly 55 sample-major/task-minor cells, resolves exactly 27 routing source IDs, validates 22 mapping-bound secondary atom tables, builds the stable artifacts twice, and requires byte identity. The formal sidecar snapshot must be unchanged at return.

The payload extraction preconditions Markdown report is recorded only as implementation lineage. Runtime never reads or parses it and never treats it as payload authority.

## In-memory Exact8

The returned built-in dictionary has this fixed order:

1. `current11_tensor_projection_payload_bundle_manifest.json`
2. `current11_tensor_projection_payload_sample_identity.json`
3. `current11_tensor_projection_payload_explicit_covalent_event.json`
4. `current11_tensor_projection_payload_ligand_residue_atom_pair.json`
5. `current11_tensor_projection_payload_warhead_boundary.json`
6. `current11_tensor_projection_payload_observed_complex_geometry.json`
7. `current11_tensor_projection_payload_provenance.json`
8. `current11_tensor_projection_payload_builder_report.json`

Each value is canonical UTF-8 JSON bytes with sorted keys, two-space indentation, ASCII escaping, no NaN or infinity, LF newlines, and exactly one terminal LF. Each artifact is smaller than 1 MiB.

The stable bundle digest covers only the first seven artifacts, in the order above, using domain tag `COVAPIE_CURRENT11_TENSOR_PROJECTION_PAYLOAD_BUNDLE_V1` followed by a NUL byte. Every artifact name and payload is framed by an unsigned 8-byte big-endian length. The builder report, filesystem identities, mtimes, absolute paths, and Git lifecycle are excluded.

## Payload semantics

Task 0 contains three independent UTF-8 `uint8` byte buffers with `int64` offsets: sample row ID, PDB ID, and ligand component ID. These are metadata/join values, not model inputs or loss targets.

Task 1 contains 11 true event values, 11 true sample-validity values, and event metadata extracted from unique validated `_struct_conn` records. It represents explicit event presence only. It does not encode bond order, pre-state, post-state, or a distance-derived event.

Task 2 contains 11 `[pocket_row_index_0based, ligand_row_index_0based]` pairs, offsets `0..11`, and true entry/sample validity. Every row locator is rebound to the exact atom-table bytes, SHA256, order, atom-site ID, and cross-source identity. These derived row indices are not permanent chemical identifiers and cannot enter a model without a separately authorized batch-index remap adapter.

Task 6 preserves source-native atom tokens. For each sample, reviewed warhead atoms are inserted in authority order; unseen attachment-boundary endpoints are appended in boundary-record order. The result has 118 sample-local tokens, 102 reviewed-warhead entries, and 16 boundary pairs. The reviewed warhead set, ligand-internal attachment boundary, and ligand-protein covalent pair are distinct concepts. `1AIM/ZYA` token `F1` remains a valid raw UTF-8 token; numeric ligand-table mapping for `F1` remains unavailable.

Task 12 serializes the 11 source-recorded decimal distances as a contiguous 44-byte little-endian IEEE-754 float32 buffer represented by lowercase hexadecimal text. Coordinates are used only for consistency checking. No coordinate-derived value replaces the source value. The payload is observed-complex geometry only, not pre-covalent or post-covalent geometry, and it contains no angle, dihedral, bond-order, transformation, or post-state promotion.

The provenance artifact has exactly 55 records in sample-major/task-minor order. Source paths are root-relative. Each record binds source IDs, source SHA256 values, source record locators, payload entry locators, and task-specific secondary evidence. Candidate promotion, inference, and semantic promotion are false for every cell.

## Checker

Run the read-only checker with both required roots:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
python -B scripts/check_covapie_current11_tensor_projection_payload_builder_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

Success returns code 0, empty stderr, and one compact canonical JSON line containing only the builder report. Failure returns code 1, empty stdout, and the uniform error token on stderr. Help, output, materialization, tensor, NumPy, task, source, availability, loss, training, schema-override, and positional interfaces are deliberately unavailable.

## Readiness boundary

Passing this builder proves only that the audited five-task, 55-cell payload bundle can be reconstructed deterministically in memory from the frozen authorities. It does not materialize the full 25-task projection instance or authorize any runtime consumer or loss.

Before any training-preparation work, the historical feature-semantics uncertainty must be explicitly re-audited. Step12D was a smoke legality check, not a final training-feature contract. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` state remain blockers. `ready_for_training` remains false.
