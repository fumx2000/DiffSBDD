# CovaPIE Step14AU-E0-P6-B revised4 summary

Step14AU-E0-P6-B implements the covalent residue locator real raw-source
precondition gate v1. It is a fingerprint revalidation gate only. It does not
decode or parse mmCIF, call the P5-B parser or P4 provider, materialize provider
rows, backfill samples, modify admission records, evaluate candidates, download
data, access checkpoints, or train a model.

## Boundary and authority sequence

The production gate first audits all nine frozen source paths in their fixed
order. It checks Git tracking and securely stats every source before it reads
any source content. A nonregular file, symlink, untracked source, or hash drift
prevents all source parsing and all raw access. After the complete structural
boundary passes, each source is read exactly once through a component-wise
no-follow descriptor walk. The SHA256 is computed from the retained in-memory
bytes, and CSV or JSON parsing consumes that same bytes object without reopening
the path.

Each successful source record freezes its relative path, exact content bytes,
SHA256, byte size, and pre/post descriptor-stat fingerprints. All nine records
must pass in canonical order or the snapshot is discarded. Replacement by new
content or a symlink after the snapshot cannot change the parsed evidence;
replacement between the structural boundary and descriptor open, modification
during read, partial reads, and hash drift all fail closed. All source
descriptors are closed on both success and failure.

The in-memory snapshot also freezes the originating repository root's lexical
absolute path and descriptor-derived device, inode, and mode. This identity is
never serialized, printed, or written to an output. Every snapshot validation
securely reopens the caller's explicit repository root and requires exact root
identity equality, so a snapshot cannot be reused across repository roots.
Source stat tuples are validated semantically as seven native integers with a
regular-file mode, positive inode and link count, and a size equal to both the
record size and retained bytes.

After that boundary passes, the gate validates the P6-B0 manifest and historical
3-row, 25-column authority, the P6-A 11-row, 26-column binding matrix, and the
expansion 8-row fingerprint authority. It completes and validates all eleven
one-to-one authority mappings before any raw path can be opened. A mapping
failure leaves raw stat/open/read/hash counts at zero.

The authority order is:

1. `6BV6/JUG` — `HISTORICAL_RAW_AUTHORITY_000001`
2. `6BV8/JUG` — `HISTORICAL_RAW_AUTHORITY_000002`
3. `6BV5/JUG` — `HISTORICAL_RAW_AUTHORITY_000003`
4. `1AEC/E64` — `FP_000001`
5. `1AIM/ZYA` — `FP_000002`
6. `1AU3/PCM` — `FP_000003`
7. `1AU4/INP` — `FP_000004`
8. `1AYU/INA` — `FP_000005`
9. `1AYV/IN6` — `FP_000006`
10. `1AYW/IN3` — `FP_000007`
11. `1B02/UFP` — `FP_000008`

Expected fingerprints come only from the committed authorities. Current raw
bytes never define an expected fingerprint.

## Secure raw access

Only the eleven bound relative paths are accepted. Paths must be canonical
relative POSIX paths below `data/raw/covalent_sources` with no URI scheme,
drive prefix, absolute path, outer whitespace, empty component, `?`, `.` or
`..` component. String subclasses and uppercase `.CIF` suffixes are rejected.

The Linux helper opens the repository root and walks every directory component
with `os.open(..., O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC,
dir_fd=parent_fd)`. It opens the final file with `O_RDONLY | O_NOFOLLOW |
O_CLOEXEC`, verifies the descriptor is a regular file, and hashes it through
`os.read` in fixed 1 MiB chunks. Raw bytes are not retained or decoded.

Pre- and post-hash `fstat` fingerprints cover device, inode, mode, link count,
size, mtime in nanoseconds, and ctime in nanoseconds. A final
`os.stat(..., dir_fd=parent_fd, follow_symlinks=False)` must still agree with
the descriptor. Replacement, truncation, metadata drift, partial reads,
parent symlinks, and final symlinks fail closed. All descriptors are closed in
a `finally` block.

The current gate binds every serialized matrix row to the ordered
`RawObservation` and Git-state evidence from that same run. The validator reconstructs the complete
31-column rows from those original evidence objects and requires full equality;
the matrix itself cannot serve as its own stat evidence. Fingerprints are also
parsed semantically: their size must agree with both observed and authority
sizes, mode must be regular, link count must be positive, and inode must be
positive.

Before opening a final file, the helper stats the final entry with
`follow_symlinks=False`. A final symlink is truthfully reported with
`exists=true`, `symlink=true`, and `confined=false`; its target is never opened
or read. The entry device/inode/mode must still match the first descriptor
`fstat`, closing the pre-stat/open replacement window.

Safety open/stat/read/hash counts come only from descriptor telemetry recorded
by each `RawObservation`, including successful directory component opens,
final-entry stat, final fd open, fd `fstat`, completed read, and completed hash.
An attempted call is not counted as a successful open or hash. The canonical
raw stat fingerprints remain current runtime evidence captured in this run;
the frozen metadata-source snapshot does not replace or predetermine raw-file
stat evidence.

## Current real revalidation result

All eleven raw files matched their committed expected SHA256 and positive file
size. All eleven had stable pre/post descriptor and final-path stat evidence.
The exact three historical paths are authority-backed untracked runtime files,
with canonical state `untracked_historical_authority_runtime`. This agrees with
the committed upstream availability evidence (`git_tracked=False` and
`git_staged=False`) and the current exact-path Git checks. Historical passing
does not depend on an ignore match. Their content integrity comes from the
committed expected SHA256/size combined with the current secure SHA256, size,
and stable descriptor/path stat evidence.

The eight expansion paths are untracked, ignored runtime files with canonical
state `ignored_expansion_runtime`. All eleven exact paths are index-clean. The
repository's separate baseline of 53 tracked raw files does not mean these
three historical authority paths are tracked. No raw file needs to be added to
Git to pass this gate, and adding one for that purpose is prohibited.

Revised4 preserves eleven passed and zero blocked matrix rows. The authority
audit is 2/2, the evidence-driven contract is 50/50, and safety is 20/20. The
gate therefore authorizes only the next real provider export execution smoke.
No raw file, ignore rule, hook, or Git index state was changed.

Fail-state authority counts are derived from the actual mapping and authority
audit. If source, predecessor, binding, or mapping evidence is unavailable, the
manifest reports zero available historical/expansion/binding rows and zero
observed conflicts instead of retaining canonical-success counts.

## Readiness boundary

P6-B revised4 freezes current raw-source preconditions after every contract
passes. This readiness means only that the provider execution smoke may be
implemented next; it does not mean the provider or parser has run. Real samples
remain 11 insertion-unknown and 0 absence-proven, and no sample was backfilled.
ADMIT_004, E1, candidate evaluation, bulk download, and training remain
blocked. A feature-semantics audit is still required before any formal training
or parameter update.
