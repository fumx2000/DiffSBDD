# CovaPIE Step14AU-E0-P6-C summary

Step14AU-E0-P6-C is an additive real parser/provider execution smoke. It
validates P6-B before raw access, securely reads only the eleven bound raw
paths, strictly decodes the retained bytes, parses the `_struct_conn.` and
`_atom_site.` loops with the frozen P5-B raw-preserving parser, and calls the
frozen P4 provider. It does not scan a raw directory, modify raw data, merge an
admission record, backfill a sample, evaluate a candidate, use a network,
download data, access a checkpoint, import model/training dependencies, or run
training.

## Revised1 runtime import and telemetry boundary

P6-C never imports the P6-A real integration design module or the P6-B raw
precondition module at runtime. Their committed modules remain frozen source
inputs, but P6-C obtains `FUTURE_REAL_SIDECAR_COLUMNS`, `BINDING_COLUMNS`, and
`MATRIX_COLUMNS` by strictly decoding and statically parsing their already
validated `FrozenSourceSnapshot` bytes. The extractor accepts only unique
module-level tuple/list assignments containing exact strings, plus static
unpacking of other uniquely assigned literal string tuples. It never executes
the source, evaluates an expression, imports a referenced module, accesses the
filesystem, or follows an artifact reference.

Consequently, P6-A's import-time construction of `_CANONICAL_BINDING_ROWS` does
not run and its historical execution CSV, sample-index CSV, and expansion
execution CSV are not read by P6-C. Runtime import is limited to the frozen P4
provider and P5-B parser modules. Their module names, non-symlink `__file__`
paths, current source bytes/SHA, and required callables are checked against the
frozen source snapshot before any raw access.

P5-B retains its historical import-time construction of sixteen synthetic
in-memory self-check cases; revised1 does not change P5-B. The P6-C manifest
raw, decode, struct-parse, atom-parse, and provider counters count only actions
performed by `execute_one_binding` for the real exact11. They are not totals
for P5-B's synthetic import work or for every call made by the Python process.
This closure changes no real sidecar, evidence, issue, safety, contract, or
readiness result.

## Frozen source boundary and predecessor

The executor accepts these exact tracked, regular, non-symlink source inputs in
this order. Their retained bytes must have these SHA256 values:

1. P4 production module — `b1a874e402180a361b6940541c95710797ed10cabfdb19f7426c0b04d0532537`
2. P5-B production module — `21be5237736a55fe87da9763c939a228bb81c52b2481602c9bcb4dd425b338bd`
3. P6-A production module — `7d43c30f87b3e4c8a44d27b63ec51ba63307dcf23c16571be1d562d0b737c650`
4. P6-A binding matrix — `61a1e77c81a8a0d335bbafd454d2926be442c2dd794bce8b75dc8a1451f78e98`
5. P6-B production module — `bb5264affc9545189b616c549370522ea9b8628bd9b8a18dbb9edb69d17d5a19`
6. P6-B contract — `6386463c17df0041c9fe4dea248c74095d4534babec17ce6c088d6cb13286b37`
7. P6-B 11×31 matrix — `ddebe9fd671400bb3508408ba0f5e38b13c83cc1e125f37bc98ac572daa2ed0d`
8. P6-B authority audit — `53cf7fd4b8fc47bab67cfb443891c4b0e8f1464d8bf324edb686ba7b64c710be`
9. P6-B safety audit — `d5d1cec05d154b85f4bd597f7a06d86c901f66193a8083566644a1c60e02ac29`
10. P6-B issue inventory — `4164ac59a2d3a16a0ee9de7996ea02b3d6cb52b563c51dfb80e9ca7f4515299e`
11. P6-B manifest — `64c87a64002dc6dcc773a1540e54f54574265d8e6a080e1b2c2024292602a3f4`

Every structural source check completes before the first source content read.
CSV and JSON parsing uses the same retained source bytes. P6-B is then checked
from direct output evidence and its manifest: exact six outputs, 11 bindings,
11 passed and zero blocked raw preconditions, 11 SHA/size/stat matches, the
3/8 Git-state split, zero exact raw paths tracked, execution-smoke readiness
true, broader execution readiness false, and no earlier parser/provider call.
The ordered P6-A/P6-B join must match all eleven binding and raw identities
before any raw path is opened.

## Same-bytes raw execution contract

`secure_read_expected_raw_source()` accepts only a canonical relative path
under `data/raw/covalent_sources`, a committed expected SHA256, and a positive
expected size. It opens each directory component with
`O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, opens the final entry with
`O_NOFOLLOW|O_CLOEXEC`, proves entry/descriptor identity and regular-file type,
reads in fixed chunks, and requires identical pre/post descriptor and final
path fingerprints. It also requires exact size and SHA equality. Every file
descriptor is closed in `finally`.

The successful `VerifiedRawSource` retains the one `content_bytes` object in
memory. Those bytes determine observed SHA and size and are decoded exactly
once with UTF-8 strict error handling. The resulting one text object is passed
to both P5-B loop parser calls. The raw path is never reopened for either
parser, and raw or decoded content is never serialized into an output.

## Real selection and provider result

Each exact `_struct_conn.id` selected one unique case-insensitive `covale` row.
All eleven covalent CYS/SG residues were `ptnr1`; all eleven selected the
`auth` locator namespace. Rows 1–3 also contained complete unequal label
evidence, so `auth_label_conflict_observed=true`; the selected pair matched only
the auth pair, which follows the frozen auth-only decision. No mixed namespace
selection was used. Each selected namespace resolved exactly one CYS/SG
`_atom_site` row with a valid exact atom-site ID.

| Case | PDB/ligand | partner | namespace | struct row | atom row |
|---|---|---:|---:|---:|---:|
| P6C_REAL_000001 | 6BV6/JUG | ptnr1 | auth | 1 | 3934 |
| P6C_REAL_000002 | 6BV8/JUG | ptnr1 | auth | 1 | 4089 |
| P6C_REAL_000003 | 6BV5/JUG | ptnr1 | auth | 1 | 4089 |
| P6C_REAL_000004 | 1AEC/E64 | ptnr1 | auth | 4 | 222 |
| P6C_REAL_000005 | 1AIM/ZYA | ptnr1 | auth | 4 | 219 |
| P6C_REAL_000006 | 1AU3/PCM | ptnr1 | auth | 4 | 187 |
| P6C_REAL_000007 | 1AU4/INP | ptnr1 | auth | 4 | 187 |
| P6C_REAL_000008 | 1AYU/INA | ptnr1 | auth | 4 | 187 |
| P6C_REAL_000009 | 1AYV/IN6 | ptnr1 | auth | 4 | 187 |
| P6C_REAL_000010 | 1AYW/IN3 | ptnr1 | auth | 4 | 187 |
| P6C_REAL_000011 | 1B02/UFP | ptnr1 | auth | 1 | 1314 |

Both insertion sources preserved `?` on every row. The P4 provider therefore
materialized eleven valid and unique source IDs and eleven canonical payload
SHA256 values, with zero present, zero absent, and eleven unknown insertion
states. The result is zero `exported_pass`, eleven `exported_blocking`, and zero
`rejected`. The blocking reason on every row is
`COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN`. This is a successful
execution smoke, not ADMIT_004 readiness.

## Exact sidecar contract

The sidecar is exactly 11 rows by the following 41 columns, in P6-A order:

1. `binding_row_id`
2. `source_pipeline`
3. `sample_execution_id`
4. `raw_target_relative_path`
5. `expected_raw_sha256`
6. `observed_raw_sha256`
7. `raw_source_precondition_status`
8. `raw_source_precondition_blocking_reason`
9. `smoke_case_id`
10. `sample_preparation_input_id`
11. `pdb_id`
12. `conn_id`
13. `residue_partner_side`
14. `locator_namespace`
15. `struct_conn_residue_auth_asym_id`
16. `struct_conn_residue_auth_seq_id`
17. `struct_conn_residue_label_asym_id`
18. `struct_conn_residue_label_seq_id`
19. `selected_chain_id`
20. `selected_residue_index`
21. `auth_label_conflict_observed`
22. `matched_atom_site_id`
23. `matched_residue_atom_name`
24. `struct_conn_insertion_source_tag`
25. `struct_conn_insertion_raw_value`
26. `struct_conn_token_class`
27. `atom_site_insertion_source_tag`
28. `atom_site_insertion_raw_value`
29. `atom_site_token_class`
30. `resolved_insertion_state`
31. `resolved_insertion_value`
32. `insertion_evidence_agreement`
33. `insertion_blocks_admit_004`
34. `insertion_blocking_reason`
35. `covalent_residue_locator_namespace`
36. `covalent_residue_insertion_code_state`
37. `covalent_residue_insertion_code`
38. `covalent_residue_locator_provenance_source_id`
39. `covalent_residue_locator_provenance_sha256`
40. `provider_export_status`
41. `provider_export_blocking_reason`

Rows are in `REAL_LOCATOR_BINDING_000001` through `000011` order and use
`P6C_REAL_000001` through `000011`. Prefix identity and expected raw evidence
come from the binding/P6-B join. Observed raw SHA comes from the one retained
raw byte sequence. Event, namespace, atom identity, and insertion raw evidence
come from P5-B parsed rows plus the P6-C selectors. Resolved insertion fields,
the five provider fields, source ID, and canonical payload SHA come from the P4
contract. The evidence audit independently records raw size/SHA, parse status,
loop row counts, selected row ordinals, unique match counts, partner,
namespace, provider status, and its pass result.

## Readiness boundary

The six outputs are only a real provider export execution-smoke sidecar and its
direct contract/evidence/safety/issue/manifest evidence. They are not merged
into the admission schema and do not backfill any real sample. ADMIT_004 and E1
remain not ready. Real candidate evaluation, bulk download, formal training,
fine-tuning, backward passes, optimizer steps, and parameter updates remain
prohibited. A feature-semantics audit, including the historical unknown atom
feature policy, is still required before formal training.
