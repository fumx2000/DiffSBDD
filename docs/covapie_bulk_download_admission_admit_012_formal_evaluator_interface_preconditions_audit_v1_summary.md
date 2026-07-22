# CovaPIE ADMIT_012 formal evaluator interface preconditions audit v1 — revised1

The audit remains fail-closed. `ADMIT_012` is the post-download
`future_download_integrity_fields_required` rule over
`download_result_status`, `observed_http_status`,
`observed_content_length_bytes`, and `observed_sha256`. Their future producer
is download execution, not candidate metadata or a pre-download placeholder.

The frozen evidence does not define types, status vocabulary, numeric ranges,
SHA256 grammar/case, presence semantics, multi-invalid precedence, envelope
routing, a public signature, or a result contract. Standalone implementation
is therefore not ready. The only recommended follow-up remains
`design_covapie_admit_012_download_integrity_field_contract_v1`.

Revised1 pins the 129-source base boundary before any source bytes are read,
uses no-follow pinned file descriptors for triple-SHA attestation, and records
the resulting proof per source. Occurrences distinguish primary lifecycle
authority from non-promoted references. Observed values distinguish schema
declarations, test fixtures, unrelated source-attestation digests, and
historical non-ADMIT_012 integrity observations; none is an authorized
ADMIT_012 download execution or semantic contract.

The six-output materializer is set-atomic: it builds all payloads before
mutation, writes a same-parent hidden staging set with `O_EXCL|O_NOFOLLOW` and
fsync, publishes only with `renameat2(RENAME_NOREPLACE)`, and preserves an
already exact set as an inode-preserving no-op. A mismatch or GPFS `EINVAL`
fails closed without an `os.replace` fallback.

Revised2 tightens identity safety without changing any audit output: source
reads and checker output reads revalidate preflight, FD, and lexical identities
explicitly (without chained inequality); checker also verifies that `HEAD`
descends from the pinned base before it reads output bytes.

ADMIT_013 remains a separate future fail-closed download-failure rule. This
stage does not implement an evaluator, result class, adapter, registry,
dispatcher, provider mapping, real download, raw access, model/checkpoint
work, or training.
