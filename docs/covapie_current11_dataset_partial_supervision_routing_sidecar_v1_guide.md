# CovaPIE Current11 dataset partial-supervision routing sidecar v1

This increment implements a deterministic, read-only, metadata-only builder for an in-memory Current11 task-level routing sidecar. It does not materialize a formal sidecar, modify a schema or authority source, create tensors, connect a runtime consumer, or authorize training.

## Public API

`build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(*, repo_root: Path, state_root: Path) -> dict[str, bytes]`

The keyword-only API returns exactly four UTF-8 artifacts in memory: routing records, task coverage, sample coverage, and a manifest. It accepts no sample, task, eligibility, bond-order, policy, output, tensor, or training override.

## Evidence and routing boundary

The builder derives canonical Current11 order and identity from the final index and cross-checks the canonical pair matrix, exact-one atom mappings, each sample's event and observed pair table, unified boundary authority, candidate family/rule assignment and binding matrices, role authority, canonical Exact5 truth table, and formal family/transformation worklists. The frozen coverage audit is used only as lineage and drift evidence.

Published UNIT_000001 routing is called through its public API. The 000008 and 000010 Exact50 states are projected without dataset-level overrides. UNIT_000001-derived records explicitly reference the published UNIT gate source binding so candidate and state-ambiguity routes remain traceable per record. The other nine samples remain conservative: observed distances authorize observed-complex geometry only; post-state, atom-map, exact deltas, reversibility, and full transformation remain blocked; candidate formed/broken/leaving-group semantics remain non-authoritative.

The canonical masks are exactly `warhead_only/A`, `linker_plus_warhead/B`, `scaffold_plus_warhead/B2`, `scaffold_only/B3`, and `scaffold_plus_linker_plus_warhead/C`. Because complete primary-role authority is unavailable for all Current11 samples, all 55 mask routes remain blocked for human approval.

## Checker

Run the checker with the two required arguments `--repo-root` and `--state-root`. Default help is disabled: missing arguments, `-h`, `--help`, unknown options, and extra positional arguments all return `rc=1`, empty stdout, and the single unified error-token line on stderr. It builds twice-compatible in-memory bytes and prints one canonical JSON line containing identities, counts, UNIT parity, readiness, and repository lifecycle on success. It has no write, materialize, tensorize, or train interface and writes no file.

All runtime-consumer, training-loss, tensor, dataloader, model-integration, formal-materialization, and training readiness values remain false. A feature-semantics re-audit is still required before any training preparation or parameter update.
