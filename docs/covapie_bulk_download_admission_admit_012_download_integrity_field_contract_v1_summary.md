# CovaPIE ADMIT_012 download-integrity field contract v1

This design-only successor freezes the shared Exact4 post-download field
contract for `ADMIT_012` and future `ADMIT_013`. It does not implement either
rule. The four required fields remain, in exact order,
`download_result_status`, `observed_http_status`,
`observed_content_length_bytes`, and `observed_sha256`; their producer scope is
the future `download_execution_result`, not candidate metadata or fabricated
pre-download placeholders.

`download_result_status` requires exact built-in `str` and uses the closed,
ordered V1 enum `success | failure`. The exact success subset is `success`.
Fourteen historical status literals were statically collected as naming
evidence, but none is automatically promoted or accepted as an alias. The
classifier does not strip, lowercase, or otherwise normalize status values.

`observed_http_status` requires exact built-in `int` in the inclusive
structural range 100 through 599; `bool`, integer subclasses, strings, 99, and
600 are invalid. The future success range is 200 through 299, but ADMIT_012
does not apply that success judgment: structurally valid 4xx and 5xx values
remain field-contract-valid and are reserved for future ADMIT_013 fail-closed
handling. Zero is not a no-response placeholder.

`observed_content_length_bytes` requires exact built-in `int` greater than or
equal to zero. Zero and arbitrarily large nonnegative integers are valid in
V1; no business upper bound is invented. The design classifier does not read
a file or compare the observation with a header, actual file, or expected
metadata. `observed_sha256` requires exact built-in `str` matching ASCII
lowercase `[0-9a-f]{64}`. Uppercase, mixed case, whitespace, prefixes, wrong
lengths, nonhex characters, bytes, and subclasses are rejected without repair.
This is a representation contract for an observed digest, not an expected
digest match.

Presence is evaluated before every type/value check. The presence scan and
the later validation scan both use Exact4 order; within one field, exact type
precedes enum/range/grammar validation. Only the private design sentinel means
missing. `None`, empty string, zero, and `False` are present and then evaluated
under the field contract. The 52-row truth matrix freezes all canonical,
missing, scalar-invalid, multi-invalid precedence, and ADMIT_013-boundary
cases with the exact field-level reason vocabulary and the rule-level blocker
`download_integrity_fields_missing`.

ADMIT_012 owns Exact4 presence, exact types, enum membership, structural
ranges, SHA representation grammar, and deterministic reason precedence. It
does not own success status, 2xx judgment, header/file length agreement,
expected-digest agreement, or candidate materialization admission. Those
fail-closed download verdicts remain future ADMIT_013 work and are not
implemented here.

The successor preserves the predecessor Exact16 issue inventory. It resolves
only `DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED`,
`DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED`,
`ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED`, and
`ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED`, using transition
`admit_012_download_integrity_field_contract_frozen_v1`. Routing,
standalone-signature, formal-result, unified-coverage, and cross-rule
aggregation issues remain open; coverage still includes
`ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015`.

The source boundary is a fixed, base-pinned 29-source set with tracked-blob,
non-symlink, containment, pinned-descriptor, and triple-SHA verification. The
independent checker reconstructs semantics without importing the production
builder and rejects synchronized-SHA semantic tampering. GPFS rejected the
single formal `RENAME_NOREPLACE` publish attempt with `EINVAL`; the attempt
failed closed and left no staging residue. Exact6 outputs were generated once
on a supporting temporary filesystem, SHA-verified, and added through a
controlled patch. No `os.replace` fallback is used.

The next recommended stage is
`design_covapie_admit_012_formal_evaluator_interface_contract_v1`. Routing,
the public standalone signature, a formal `Admit012EvaluationResult`, unified
adapter/runtime integration, provider mapping, download execution, ADMIT_013,
model/checkpoint work, and training all remain unimplemented. Step12D remains
only a smoke-legality check, and a feature-semantics audit remains mandatory
before training.
