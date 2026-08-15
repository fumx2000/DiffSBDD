# CovaPIE Current11 Task2 Output17 semantic reconciliation contract gate V1

This additive, read-only gate defines how two existing Output17 producers are compared. It does not create a new Output17 schema and does not modify either producer.

The historical private reference evaluator and the current public runtime adapter have different producer identities. On published successful reference cases, the first 15 Output17 fields (`Core15`) must match exactly by field order, built-in type, value, boolean/integer distinction, and null semantics. The shared successful provenance facts `joint_layout_descriptor` and `joint_index_status` must also match exactly. The remaining `provenance` and `readiness` content is validated against separate, closed producer-specific schemas; it is not normalized into one cross-producer metadata schema.

The current public adapter is the runtime whole-Output17 golden producer: `current_public_adapter_output17_v1`. A future runtime fast path must be byte-identical to that target for the same exact input on both success and deterministic fail-closed outputs, including runtime provenance and readiness. The old adapter report is neither successor authority nor a compatibility target.

Historical private failure output is lineage and diagnostic evidence, not the runtime golden. Its fixed `[0]` sample offsets, empty sample validity, entry-zero hard-failure placement, and absent failure descriptor are self-validated as historical behavior. They must not be silently normalized to runtime offsets, runtime validity, the actual runtime failing entry, or a null descriptor. Universal failure Core15 parity is therefore false.

The gate freezes the historical stable5, historical reference vectors, historical remap contract gate, current adapter, and published successor by exact source identity. It calls only the frozen private pure helpers needed for three successful cases (joint, no-joint, and subset with `NOT_IN_BATCH`) and two failures (schema mismatch and a nonzero-entry hard failure). It does not call the public adapter, historical public remap gate, successor public build, B2 public build, compiler context, DataLoader, model, forward path, loss, or training.

The next authorized increment is a lightweight Output17 semantic parity probe. The remap hot-loop gate is still not ready until that probe passes. The current adapter still does not directly accept successor Exact6, the compiler context still does not use successor authority, and compiler-context rebuild device identity remains a risk.

Canonical V1 remains exactly five masks: `warhead_only/A`, `linker_plus_warhead/B`, `scaffold_plus_warhead/B2`, `scaffold_only/B3`, and `scaffold_plus_linker_plus_warhead/C`. In particular, B3 always means `scaffold_only`; this gate is not B3 and changes no mask.

Step12D remains a smoke legality check, not a final training-feature contract. A feature-semantics re-audit, including resolution or formal audit of the historical unknown-atom policy state, is still required before training. DataLoader, model, loss, and training readiness all remain false.

Run the gate checker without writing artifacts:

```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 python -B \
  scripts/check_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1.py \
  --repo-root /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/DiffSBDD-base \
  --state-root /cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state
```

Success prints one compact JSON line with status `PASS_OUTPUT17_SEMANTIC_RECONCILIATION_CONTRACT_ONLY`. The public build returns six deterministic in-memory JSON byte payloads; the first five form the stable framed digest and the report is self-excluded.
