# CovaPIE Current11 routing tensor-projection contract gate V1

This Exact4 increment implements the approved metadata-only projection contract as a deterministic, read-only, standard-library gate. It does not materialize a projection instance, tensor, authoritative task payload, candidate payload, payload-validity matrix, availability matrix, runtime consumer, or loss cell.

The only public API is:

```python
build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]
```

It derives the canonical sidecar solely from `state_root`, verifies the frozen V2 module hash, runs the published V2 read-only check twice, requires identical summaries, independently validates the canonical symlink, hidden object, Exact4 bytes, formal schemas, Exact11 sample order, Exact25 task order, Exact275 sample-major/task-minor records, Exact7 states, closed evidence and blocking vocabularies, and Exact5 mask semantics including `scaffold_only/B3` at index 3. Formal state is snapshotted before and after and any identity, mode, mtime, content, link, or inventory drift fails the gate.

The returned exact built-in `dict` contains four ordered in-memory byte artifacts:

1. `current11_routing_tensor_projection_contract_manifest.json`
2. `current11_routing_tensor_projection_task_schema.csv`
3. `current11_routing_tensor_projection_state_encoding.csv`
4. `current11_routing_tensor_projection_gate_report.json`

Nothing writes these artifacts. JSON is canonical pretty JSON with sorted keys and one final LF. CSV uses fixed columns, RFC-compatible quoting, LF, and one final LF. A second independent build of the stable first three artifacts must be byte-identical.

The contract digest is SHA-256 over domain tag `COVAPIE_CURRENT11_ROUTING_TENSOR_PROJECTION_CONTRACT_GATE_V1` followed by a NUL byte. Each of the first three artifacts is framed in fixed order by an unsigned eight-byte big-endian name length, UTF-8 name, unsigned eight-byte big-endian payload length, and payload. The lifecycle-varying gate report, repository lifecycle, inode, mtime, and absolute temporary paths are excluded.

State codes are routing metadata, never labels: `0 admissible_now`, `1 admissible_as_observed_geometry_only`, `2 candidate_only_not_authoritative`, `3 blocked_missing_evidence`, `4 blocked_state_ambiguity`, `5 blocked_missing_human_approval`, and `6 not_applicable`. Codes 0 and 1 permit availability only after future payload extraction and validation. Code 2 permits only a physically separate candidate payload. Code 4 remains distinct from missing, code 5 cannot be satisfied by a candidate, and code 6 means applicability false. Loss always comes from explicit authority and all 275 current cells remain false.

The permitted authoritative-or-observed count of 55 means only that 44 code-0 and 11 code-1 cells may become available after later extraction and validation. It is not an available-payload count. The candidate-eligible count of 55 means only that code-2 cells may enter future candidate buffers; no candidate payload has been extracted.

Run the fail-closed checker with both required roots:

```text
PYTHONDONTWRITEBYTECODE=1 python -B scripts/check_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py --repo-root /absolute/repository --state-root /absolute/covapie-state
```

Success prints one compact JSON gate report and exits zero. Failure prints only `COVAPIE_CURRENT11_DATASET_ROUTING_SIDECAR_TENSOR_PROJECTION_CONTRACT_GATE_V1_ERROR` to stderr and exits one. Help, output, materialization, tensorization, payload, availability, loss, training, approval, schema override, and positional interfaces are intentionally absent.

The gate status is `PASS_CONTRACT_ONLY`. It supports precommit-candidate, committed-unpushed, and published-successor repository lifecycles without changing the stable contract digest. It never means ready for projection materialization, tensor materialization, dataloader or model integration, or training.

Step12D remains only a smoke-legality check, not a final feature contract. `UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED` and `feature_semantics_known=false` remain blockers. A separate feature-semantics re-audit is mandatory before training preparation or any parameter update.
