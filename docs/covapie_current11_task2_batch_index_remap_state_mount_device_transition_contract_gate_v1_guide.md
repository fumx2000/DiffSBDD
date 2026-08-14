# CovaPIE Current11 Task2 remap state mount-device transition contract gate V1

This additive B2 increment is a narrow, read-only transition authority for the
three state objects reachable from the Current11 Task2 remap predecessor chain.
It accepts only the fully evidenced lifecycle transition from historical device
49 to current device 50. It does not change or call either historical gate, the
remap contract gate, `_contract_exact6`, the remap adapter, the compiler,
compiler context, extractor, dataset, DataLoader, model, loss, checkpoint, or
training code. It does not implement the later B3 predecessor successor.

## Public API and failure contract

The module exports exactly one keyword-only API:

```python
build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]
```

Every rejected input or drift raises:

```text
COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_GATE_V1_ERROR
```

There is no device, path, transition, allow-list, ignore-device, mount-ID,
training, output, or materialization override. The three paths and the exact
49-to-50 mappings are contract constants.

## Exact transition scope

The frozen transition order is:

1. `unit_000001_dossier`: `(49,196008339793)` to
   `(50,196008339793)` at
   `manual-review-aids/current11-reaction-transformation-review-v1/CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001`.
2. `routing_canonical`: `(49,69442074366)` to `(50,69442074366)` at
   `formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1`.
3. `routing_object`: `(49,69442074217)` to `(50,69442074217)` at the
   exact hidden object named by the canonical readlink.

A fourth object, an omitted or reordered object, current device 49 or 51, an
alternative historical device, or a wildcard device fails closed. The
`transition_authorized=true` value means only that one exact device transition
is accepted when every other lineage check is equal. It does not make `st_dev`
optional or ignorable.

The dossier must remain a real `0755` directory with Exact8 non-symlink `0644`
regular leaves and their frozen sizes and SHA256 values. Its parsed
`dossier_manifest.json` must identify the exact review unit and parent, two
samples, and `question_count=25`; it must remain a non-authoritative review aid
with blank or incomplete review content not promoted to authority and
`ready_for_training=false`.

The canonical routing entry must remain a symlink with the exact basename-only
relative readlink. Symlink permission bits are deliberately not semantic
identity. The target must be the exact real `0755` hidden directory containing
the frozen Exact4 non-symlink `0644` leaves. The aggregate is recomputed with
the already published routing V2 domain and name/payload uint64 big-endian
framing and must equal
`24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c`.

The routing manifest and records are independently parsed. They must preserve
Exact11 sample identity/order, Exact25 long semantic task order, Exact275
sample-major/task-minor record identity, and the Exact5 canonical masks:

1. `warhead_only` / A
2. `linker_plus_warhead` / B
3. `scaffold_plus_warhead` / B2
4. `scaffold_only` / B3
5. `scaffold_plus_linker_plus_warhead` / C

The frozen routing manifest publishes `training_loss_authorized=false` rather
than a field literally named `ready_for_loss_integration`; the transition
evidence records that published source key and derives no loss-integration
readiness from it. DataLoader, model, loss, and training readiness remain
false, and the feature-semantics re-audit remains required.

The task prompt's displayed SHA256 for
`sample_transformation_gap_evidence.csv` omitted one `c`. The gate uses the
64-hex identity independently shared by the actual state leaf, the frozen
historical source, the dossier manifest, and the reviewed precondition report:
`599c75f0f97896c0eea73dbde5041a446f23cb5d30e7da36c186a908561e1134`.

## Historical and mount lineage

The gate byte-freezes the current HEAD identities of the unit-routing Exact4
and projection-contract Exact4: bytes, LF count, SHA256, Git blob, and mode
`100644`. It verifies the exact introduction commits, parents, subjects,
addition statuses, and the device identity constants in both the introduction
source and current frozen source. It never calls their public evaluators.

The reviewed precondition report is independently checked at
`review-scratch/current11-state-mount-device-identity-transition-precondition-v1/state_mount_device_identity_transition_precondition_report.md` as mode
`0644`, 31,396 bytes, 619 LF bytes, and SHA256
`ea4583db1101cf19b78e10ad7c28a99f330d140150c2362231f312c21b2cf345`.
The report is predecessor evidence, not a substitute for direct current-state
validation.

`/proc/self/mountinfo` is parsed with octal path-field unescaping. The gate
requires the unique most-specific record covering `state_root` and freezes only
these transition semantics:

- filesystem type `gpfs`;
- source `cpfs01`;
- root `/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037`;
- target `/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037`;
- historical major:minor `0:49` and current major:minor `0:50`;
- historical `st_dev=49` and current `st_dev=50`.

The current mount ID and parent mount ID are namespace-local diagnostics. They
appear only in the self-excluded report with `diagnostic_only=true`; they are
not gate-admission identity and do not participate in the stable digest.
Namespace inode, mtime, ctime, atime, directory size, timestamps, and random
nonces are likewise excluded from stable semantics.

## In-memory artifacts and digest

The returned built-in dictionary contains this deterministic Exact5 order:

1. `current11_task2_batch_index_remap_state_mount_device_transition_contract_manifest.json`
2. `current11_task2_batch_index_remap_state_mount_device_transition_objects.json`
3. `current11_task2_batch_index_remap_state_mount_device_transition_lineage_evidence.json`
4. `current11_task2_batch_index_remap_state_mount_device_transition_negative_matrix.json`
5. `current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_report.json`

All are canonical UTF-8 JSON bytes with sorted keys, two-space indentation,
ASCII escaping, finite values, and exactly one terminal LF. Nothing writes
them. The first four participate in the stable digest; the lifecycle-varying
report is self-excluded.

The digest starts with the ASCII domain
`COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_GATE_V1`
and a NUL byte. Each stable artifact in exact order is framed by unsigned
eight-byte big-endian name length, UTF-8 name, unsigned eight-byte big-endian
payload length, and payload.

For the frozen V1 semantics, the stable digest is
`d39d40b634a3cdd38c43c3636dda57ffb5540ae3a9c9a4b30dfaca70e56b4cb1`.

The negative matrix contains 24 frozen fail-closed cases covering wrong old or
current devices, current 49 and 51, inode/path/type/mode/readlink drift,
missing/extra leaves or objects, size/hash/aggregate drift, mount topology
drift, historical source or precondition drift, semantic-manifest drift, and
forbidden wildcard or allow-list behavior.

## Checker and lifecycle

Run the lightweight checker with only the two roots:

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B \
  scripts/check_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1.py \
  --repo-root /absolute/path/to/DiffSBDD-base \
  --state-root /absolute/path/to/covapie-state
```

The checker accepts only `precommit-untracked` and
`clean-tracked-successor`. Admission requires branch `main`, existence of base
`83beddbcd468caeb38a6b8a86c15f31dfd430d79`, and base ancestry/equality to
HEAD; `origin/main` is not used for semantic admission. It snapshots the
relevant repository and state objects, performs two public builds, requires
Exact5 byte identity, independently recomputes the stable digest and direct
summary checks, asserts readiness before output, and requires both snapshots
unchanged.

Success returns rc 0, empty stderr, and one compact canonical JSON line with
status `PASS_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_ONLY`. Failure returns rc
1, empty stdout, and the unified error token on stderr.

## Readiness boundary

A pass establishes
`ready_for_remap_predecessor_successor_integration=true`. It does not repair
the old remap chain. The separate B3 integration and a separately authorized
one-heavy parity/timing probe are still required before any remap hot-loop
contract work.

Accordingly,
`ready_for_public_remap_adapter_hot_loop_contract_implementation=false`,
`compiler_context_rebuild_device_identity_risk=true`, and DataLoader, model,
loss, and training readiness remain false. Step12D remains a smoke legality
check, not a final training-feature contract; the historical
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=false` state still
requires a formal feature-semantics re-audit before training.
