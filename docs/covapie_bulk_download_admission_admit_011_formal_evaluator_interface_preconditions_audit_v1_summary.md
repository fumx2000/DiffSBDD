# CovaPIE ADMIT_011 formal evaluator interface preconditions audit v1

This metadata-only audit freezes the committed evidence needed to begin design of the `raw_target_relative_path` contract. It does not freeze rule semantics or authorize standalone evaluator-interface implementation.

- Canonical identity: `ADMIT_011` / `raw_overwrite_forbidden`, `pre_download`, candidate field `raw_target_relative_path`.
- Historical vocabulary: `target_does_not_overwrite_existing_raw` and `raw_target_overwrite_forbidden`.
- Required context names: `existing_raw_target_relative_paths` and `raw_target_relative_path_contract`.
- Primary blocker: `RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED`, still open; Exact10 coverage remains `ADMIT_011`–`ADMIT_015`.

The audit fixes its 99-source boundary to base commit `ce5323d6fce27e42cfdfa5faad198dbf0f719d19`, with frozen path-list and path/SHA-pair digests. It inventories every base-tree non-raw occurrence of `raw_target_relative_path` and direct CSV/manifest values, including empty/null-like states. Observed values are historical or fixture evidence only: they do not define a grammar or validate provider mapping.

The committed interface evidence supports a pure in-memory evaluator shape because Step14AU-A assigns no evaluator filesystem or network access. It does not define lexical versus resolved semantics; raw-root identity/allowlisting; absolute, traversal, empty-segment, dot, separator, Windows drive/UNC, NUL, or non-ASCII policy; nor existing target, overwrite, symlink, directory, FIFO, or device behavior. Context ownership among candidate, batch snapshot, download, and stage callers also remains unallocated.

ADMIT_011 remains strictly pre-download target admission. ADMIT_012 and ADMIT_013 concern post-download result fields and are not evaluated here.

`admit_011_pure_in_memory_interface_feasible=true` does not mean standalone evaluator implementation is authorized. The supported next step is only `ready_for_admit_011_raw_target_relative_path_contract_design=true`; `ready_for_admit_011_standalone_evaluator_interface_implementation=false`. Rule logic, adapter, registration, Exact11 runtime, real provider evaluation, bulk download, and training remain false. Formal training still requires a separate feature-semantics audit; Step12D remains smoke legality only.

## Revised2 closure

For a newly created output root, the materializer now revalidates immediately before its first atomic write that the root is still empty. A concurrent occupant using even an allowlisted output filename fails closed without replacing that file or beginning any atomic write. Existing roots retain the prior Exact6 regular-file inventory rule.

The historical external Exact84 allowlist was not recovered after the DSW node/image rebuild; it was not reconstructed or renamed. A full repository pytest run was used as the repository-wide strict validation superset. A new persistent test-file baseline is maintained outside the repository under the CovaPIE allowlist cache. It represents only this ADMIT_011 precondition node's current full-repository test-file scope and is neither Exact84 nor Exact85. The ADMIT_011 business conclusion, readiness, Exact99 source boundary, and six audit outputs are unchanged.
