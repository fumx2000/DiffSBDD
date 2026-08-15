# CovaPIE Current11 Task2 remap predecessor successor V1

`remap_predecessor_successor_v1` is the additive successor for the Current11
Task2 batch-index remap predecessor chain. It is unrelated to the canonical
mask semantic `scaffold_only` / B3. The canonical V1 mask contract remains
exactly `warhead_only` / A, `linker_plus_warhead` / B,
`scaffold_plus_warhead` / B2, `scaffold_only` / B3, and
`scaffold_plus_linker_plus_warhead` / C.

## Product boundary

The module exports exactly one keyword-only API:

```python
build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]
```

Every rejection is normalized to:

```text
COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_PREDECESSOR_SUCCESSOR_V1_ERROR
```

The production path calls the published B2 mount-device transition authority
exactly once per build and independently validates its Exact5, framed stable4
digest, Exact3 transition, and readiness boundary. It then byte- and
signature-freezes the historical payload, projection-instance, and remap helper
owners before directly calling their private pure reconstruction helpers.

Production monkeypatching is false. The product does not replace a historical
function, hide Git status, call a historical public builder or gate, invoke the
public remap adapter, use a cache, or write an output file.

## Reconstructed artifacts

The returned built-in dictionary has this Exact6 order:

1. `current11_task2_batch_index_remap_contract_manifest.json`
2. `current11_task2_batch_index_remap_input_schema.json`
3. `current11_task2_batch_index_remap_output_schema.json`
4. `current11_task2_batch_index_remap_status_vocabulary.csv`
5. `current11_task2_batch_index_remap_reference_vectors.json`
6. `current11_task2_batch_index_remap_predecessor_successor_report.json`

The first five are byte-identical to the historical remap stable5 and retain
digest
`2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6`.
The sixth is a new report with schema
`covapie_current11_task2_batch_index_remap_predecessor_successor_report_v1`
and status `PASS_REMAP_PREDECESSOR_SUCCESSOR_ONLY`.

The payload stable7 retains digest
`95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d`.
The projection instance remains 251,433 bytes, 10,468 LF bytes, SHA256
`ac191d0fa8b6855fd01247c4c93cce2901c91f5862de923f66855315655cf23b`,
and framed digest
`b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255`.

The historical payload report cannot be reused: its serialized canonical and
object filesystem tuples contain the device number, so device 49 and device 50
produce different report SHA256 values even though stable7 is unchanged. No
historical payload or projection-instance report is emitted. Historical report
hashes embedded in the preserved stable instance and manifest are frozen
lineage only; they do not claim that those reports were produced during the
successor invocation.

The historical stable manifest is intentionally byte-preserved, so its own
`artifact_names` still mentions
`current11_task2_batch_index_remap_contract_gate_report.json`. That old report
is not a current Exact6 output. The successor report names both identities and
records that historical report byte parity is not required.

## Repository lifecycle

The public production API succeeds only for a clean, tracked successor. This is
required because the published B2 gate observes repository status and correctly
rejects the four new successor paths while they are untracked.

During `precommit-untracked`, the checker does not call the public B3 API. It
uses a narrowly scoped checker-only compatibility replacement for B2's
repository-lifecycle observation to obtain a real B2 Exact5 fixture, restores
the function immediately, and calls only the successor's internal fixture
reconstruction path. This changes no B2 transition, device, path, content, or
mount semantics. The checker reports
`PASS_REMAP_PREDECESSOR_SUCCESSOR_PRECOMMIT_CANDIDATE_ONLY`,
`real_public_B3_build_performed=false`, and
`clean_successor_live_validation_pending=true`.

After a later authorized commit makes Exact4 clean and tracked, the checker
calls the real public B3 API twice, requires Exact6 byte identity, and therefore
observes two B2 calls total: one per independent B3 build. Only that later live
proof may set `clean_successor_live_validation_pending=false` and
`ready_for_one_heavy_parity_timing_probe=true`.

Run the current candidate checker with:

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B \
  scripts/check_covapie_current11_task2_batch_index_remap_predecessor_successor_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

## Readiness boundary

The current public adapter still requires the historical report-sensitive
Exact6 and does not directly accept this successor Exact6. The compiler context
still rebuilds the historical chain and has a device-identity risk. The next
separately authorized step is one heavy parity/timing probe; it is not part of
this implementation candidate.

No DataLoader, model, forward path, loss, checkpoint, or training code is
changed or executed. The public remap adapter hot-loop product is not ready.
Step12D remains a smoke legality check rather than a final training-feature
contract. The historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=false` state still requires a feature-semantics
re-audit before training preparation or parameter updates.
