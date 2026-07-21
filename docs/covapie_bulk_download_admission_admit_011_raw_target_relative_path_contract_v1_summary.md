# ADMIT_011 raw-target relative-path contract v1

This revised design gate freezes exact immutable `RawTargetRelativePathContract`
and `ExistingRawTargetRelativePathsSnapshot` objects. The candidate coordinate
system is `repository_relative_posix_lexical_path`, with the exact allowed
namespace prefix `data/raw/`; equality is case-sensitive exact lexical string
equality. No evaluator, adapter, runtime registration, provider mapping,
filesystem provider, raw read, network access, download, or mutation is implemented.

`existing_raw_target_relative_paths` is a complete immutable provider snapshot
of every occupied target namespace location under the opaque canonical raw-root
identity. Any exact occupied lexical target blocks with
`RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED`, traceably mapping to historical
`raw_target_overwrite_forbidden`. ADMIT_012/013 remain post-download concerns.

The canonical Exact11 issue inventory is preserved byte-for-byte except for the
ADMIT_011 issue transition. Coverage remains open for ADMIT_011–015. PRE_009
through PRE_014 are transitioned to
`resolved_by_raw_target_relative_path_contract_v1`; the next step is
`implement_covapie_admit_011_standalone_evaluator_interface_v1`.

The future standalone accepts only the scalar and the two exact context
objects; candidate/evaluation/batch envelopes and identity routing are future
adapter responsibilities. ADMIT_012/013 remain post-download. Feature
semantics audit remains mandatory before training, and Step12D remains smoke
legality only, not a final training-feature contract.

The design result uses the Exact10-style ten fields. Scalar-invalid outcomes
consume no context; contract-invalid outcomes consume only
`raw_target_relative_path_contract`; snapshot-invalid, mismatch, collision,
and passed outcomes consume the standalone order
`raw_target_relative_path_contract`, then
`existing_raw_target_relative_paths`. The truth matrix contains every one of
the 47 historical values, every frozen non-empty reason, and multi-invalid
precedence cases (84 rows total). Retained non-empty canonical result values
must themselves satisfy the exact `data/raw/` canonical grammar.

## revised2B1 fixed source boundary and attestation

The design evidence is derived only from an exact ordered boundary of 21
committed, tracked, regular, non-symlink repository files at
`a8cf1a8dcda6ebcdf1ddaf34233f61475686b417`. Its canonical path-list SHA256 is
`e18394c632a04531d64ed48a00ff7f90114d409c713b0f1cfa1d6a6224a13cec`; its
ordered path/SHA-pairs SHA256 is
`b1a21c1d48b0a320264801056839d0962ad23c32d1ca5676fb7735ec4859b948`.
Repository/base lineage and the structure of all 21 sources are validated
before any source bytes are read; each base-tree, filesystem, and frozen
snapshot SHA256 must agree with the frozen source map.

The frozen predecessor evidence attests Exact99 source-boundary rows, Exact172
occurrences, Exact47 observed values (47 present and zero empty/null-like), and
Exact11 issues. The source-boundary CSV records source order, all four SHA256
views, base-tree mode, and each safety predicate. Manifest v3 preserves the
semantic and readiness contract while carrying the corresponding source and
predecessor attestation. The independent checker reconstructs every boundary
row and rejects synchronized boundary/manifest as well as manifest-identity
tampering. Materializer/output-path hardening remains explicitly deferred to
revised2B2.

## revised2B1-fix1 checker live-source closure

Before it reads any derived output bytes, the independent checker now validates
the live repository root and base lineage, completes all 21 source structural
checks, and compares each base-tree and current-filesystem SHA256 with the
frozen boundary digest. It constructs the boundary rows from those live
observations rather than assigning filesystem hashes from constants. The
checker also requires `issue_inventory_count == 11`; source structure, source
byte, and base-lineage failures fail closed before output content is read.

## revised2B2 output-path and atomic-materializer hardening

Manifest v4 separates materializer safety from the evaluator/runtime safety
boundary. Its exact `materializer_safety` object attests read-only initial
preflight, pinned directory descriptors, identity revalidation, same-directory
exclusive temporary files, file and directory fsync, atomic descriptor-relative
publication, postwrite byte/SHA checks, and constrained failure cleanup.

The materializer does not create a missing root until source snapshot and
artifact construction have succeeded and all six semantic CSV payload hashes
have been checked. Parent chains, root and leaf identities are validated with
`lstat`; parent/root file descriptors are pinned with `O_DIRECTORY` and
`O_NOFOLLOW`; all later temporary, stat, publish, unlink, and verification
operations use directory-relative APIs. The checker mirrors a read-only pinned
descriptor traversal for derived output files before semantic validation.

## revised2B2-fix1 set-atomic publication

An existing output root is now immutable: after source/artifact construction,
its seven pinned leaves are read and compared with the seven payloads. An exact
match is an inode-preserving no-op; any difference fails closed without a
repair attempt or a per-file replacement. This removes the possibility of a
partial replacement sequence leaving a mixed old/new output set.

For a missing root, the seven final filenames are written and file-fsynced in a
unique hidden sibling staging directory. After complete byte/SHA and inventory
verification plus staging-directory fsync, Linux descriptor-relative
`renameat2(RENAME_NOREPLACE)` publishes the directory as one complete set and
the parent directory is fsynced. `RENAME_NOREPLACE` preserves the final-root
race rejection guarantee that ordinary replacement rename cannot provide.
Pre-publication failures clean only identities created by this call; failures
after publication leave a complete set rather than a partial one.
