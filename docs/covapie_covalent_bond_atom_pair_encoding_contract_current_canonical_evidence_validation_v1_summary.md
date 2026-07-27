# CovaPIE covalent-bond atom-pair current-evidence validation V1

This gate validates the frozen structured atom-pair contract against the 11
committed Cys-SG samples at BASE
`7f432cecec8a3abed2339e4dd60dfa239cd2cbe7`.

The validation constructs role-labeled records only from explicit event-table
identity fields, preserves validated `struct_conn` authority, performs
exactly-one identity mapping into the committed pocket and ligand atom tables,
and binds each derived 0-based row index to the source path, SHA256, and exact
CSV row order. A row index is a derived view, not a permanent semantic identity.

The exact-one helper first validates the frozen locator type and schema. Every
nonempty `model_id`, `altloc`, or `insertion_code` must have and exactly match
its formal target-table column on both residue and ligand sides; unavailable
columns fail closed. The 11 current locators leave these optional fields empty,
so their 22 validated indices are unchanged.

Normal samples and executable tamper cases share one frozen sample-bundle
validation path covering event/pair cardinality, canonical record validation,
legacy and authority consistency, exact-one mappings, row counts, source
SHA/order binding, bilateral atom-site IDs, and bilateral coordinates. All
failure cases must be observed to fail closed before the atom-pair issue can
transition to resolved.

Success resolves only `COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED`. The real-provider
blocking issue remains open. No raw structure, provider, download, checkpoint,
tensor, dataloader, model, forward, loss, or training operation is used.

The next allowed step is
`audit_covapie_real_provider_export_blocking_rows_and_freeze_resolution_or_quarantine_policy_v1`.
Tensorization and training remain blocked, and the feature-semantics audit is
still required before training.
