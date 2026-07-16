# Step14AU-E0-P6-B0 historical authority consolidation

This metadata-only gate consolidates three committed evidence roles for 6BV6/JUG, 6BV8/JUG, and 6BV5/JUG:

- controlled raw availability is the frozen expected SHA256 and file-size snapshot;
- controlled raw integrity is the prior observed SHA256 and file-size verification, joined to each binding by exact PDB ID and raw relative path;
- unified independence evidence is the cross-stage before/after SHA256 and unchanged corroboration.

The three source headers and their exact order are frozen. Target rows also require exact source-specific status values: availability must record available, untracked, unstaged, parse-permitted, and not candidate/training ready; integrity must record the expected data-block marker, no HTML/error page, no parse, a passed byte-integrity audit, and the canonical QA comment; independence must record the pilot stage, consistent/existing/named raw evidence, unchanged SHA256, a passed inventory, and no blocking reason.

Availability and integrity have no native row identifier. Their canonical locators therefore use the frozen CSV's one-based data-row ordinal (`AVAILABILITY_ROW_nnnnnn` and `INTEGRITY_ROW_nnnnnn`). Because each source content SHA256 is frozen at the same gate boundary, these ordinal locators are auditable and cannot be mistaken for authority-output row numbers. Independence retains its native `sample_index_row_id`.

The resulting 3×25 authority is consensus among independent committed metadata records, not current-raw self-certification. This step performs no raw traversal, stat, read, hash, or parse. It does not execute P6-B, the real parser/provider, candidate evaluation, download, or training, and it does not backfill real samples. Existing real-sample truth remains 11/11/0; ADMIT_004 and E1 remain false. The canonical mask contract remains exactly five tasks and includes `scaffold_only / B3`. Feature-semantics audit remains mandatory before any formal training.

The source audit is an access gate, not merely a failure report. Any tracked, regular-file, non-symlink, or frozen-hash boundary failure short-circuits before CSV/JSON content parsing, blocks all dependent sections, and prevents metadata-source symlink dereference.

The checker uses the same source audit as its content-access gate. It no longer calls its output-file `read_bytes` hash helper on `SOURCE_PATHS`; before/after source stability is compared through validated canonical source-audit snapshots. A source boundary failure therefore stops the checker before materialization, and a metadata-source symlink cannot bypass the production boundary through checker code.
