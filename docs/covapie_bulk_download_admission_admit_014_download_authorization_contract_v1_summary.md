# CovaPIE ADMIT_014 download authorization contract v1

This metadata-only design freezes the stage-level download-authorization
contract for `ADMIT_014` (`current_gate_grants_no_download_permission`). It is
based on commit `30bbfaba4df0843d1f028e695d3dc499079a9b36`, with exact parent
`3ec07b2daa7e6fc2d51df2641e85c13be2196ff3` and tree
`72390570480b5b81680acccc2db3250ad71a942c`.

The design does not implement `evaluate_admit_014`,
`Admit014EvaluationResult`, an adapter, registry entry, Exact14 runtime,
provider, download orchestration, combined verdict, cross-rule aggregation,
raw-data operation, or training.

## Authority and value

The sole authoritative envelope is `stage_authorization_context`; the sole
authoritative key is `current_stage_download_authorized`. Candidate, batch,
evaluation, and download-result envelopes, provider results, candidate
self-report, environment variables, filesystem markers, raw files, manifests,
fixtures, artifact hashes, and Git identities cannot authorize or override.

The value contract is exact: `type(value) is bool`, with the closed vocabulary
`False | True`. `False` blocks with `BULK_DOWNLOAD_NOT_AUTHORIZED`; `True`
passes this permission verdict with an empty reason. Integers, floats, strings,
`None`, containers, subclasses, NumPy booleans, and arbitrary truthy/falsy
objects are invalid. Coercion and normalization are forbidden.

The mapping may contain unrelated future stage fields. The classifier performs
one ordered `stage_authorization_context["current_stage_download_authorized"]`
lookup and does not iterate the mapping, call `len`, `.get`, or `in`.

## Trust, provenance, and freshness

Only a future trusted stage orchestrator may construct the context. Trust comes
from that invocation boundary, not from a producer string inside the mapping.
The context is invocation-local and must be reconstructed explicitly for every
stage invocation. Reuse from artifacts, caches, raw files, or a previous stage
invocation is forbidden.

The design classifier validates only the received exact bool. Identity
authentication, signature verification, cryptographic authentication, and
orchestration enforcement remain outside the classifier:

- evaluator responsibility: consume and validate one target value without I/O;
- trusted caller responsibility: construct a fresh invocation-local context;
- future orchestration responsibility: enforce the trusted boundary and the
  pre-download hard guard.

## Failure precedence

The closed precedence and reason vocabulary is:

1. missing envelope:
   `STAGE_AUTHORIZATION_CONTEXT_REQUIRED`;
2. non-mapping envelope:
   `STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID`;
3. first target-key `KeyError`:
   `CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING`;
4. non-`KeyError` lookup exception:
   `STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED`;
5. non-exact-bool value:
   `CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID`;
6. exact `False`:
   `BULK_DOWNLOAD_NOT_AUTHORIZED`;
7. exact `True`: passed with an empty reason.

The only outcomes are `passed` and `blocked`. `passed` is true exactly when the
outcome is `passed` and the reason is empty; `blocks_candidate` is true exactly
when the outcome is `blocked`; `evaluator_io_used` is always false.

## Mandatory pre-download enforcement contract

ADMIT_014 is a stage-global guard. A future real-download stage must evaluate
it once per invocation before any provider network call, remote metadata
fetch, file download, raw write, or download-result materialization. Only a
passed ADMIT_014 permission verdict may continue to those actions.

A blocked result requires provider, network, download, and raw-write counts to
remain zero. This hard block does not depend on a combined verdict, and a
future combined verdict may not override it.

A pass means only that the permission verdict passed. It does not prove
provider readiness, candidate eligibility, download success, ADMIT_012 or
ADMIT_013 success, or current bulk-download readiness. The mandatory
enforcement contract is frozen here but not implemented.

## Evidence and transitions

The committed source boundary is an ordered Exact11 set:

- five ADMIT_014 precondition sources;
- two Step14AU-A sources;
- the Step14AT rule registry;
- the Exact13 runtime production source, manifest, and issue inventory.

Each source must be a safe current-index stage-0 tracked base-tree blob with
matching current, base, and frozen SHA256 bytes. Reads use pinned no-follow
directory descriptors and full device/inode/mode/size/mtime/ctime identity
checks before and after traversal.

The deterministic Exact6 contains:

- a 20-row value/trust contract;
- a 25-row routing/enforcement contract;
- a seven-row closed failure taxonomy;
- an Exact40 truth matrix across six groups;
- the inherited Exact30 issue inventory;
- a manifest with lineage, source, schema, transition, readiness, safety, and
  output evidence.

All truth cases use zero forbidden-envelope access. ADMIT_014 and ADMIT_015
can coexist in the same `stage_authorization_context` under the canonical
`current_stage_download_authorized` and `current_stage_training_authorized`
keys. ADMIT_014 reads only `current_stage_download_authorized`. Extra keys and
mappings whose iteration, length, `get`, or containment operations raise do
not affect the target-only lookup.

Of the Exact51 predecessor preconditions, 46 are now complete and five remain
open: public standalone signature, formal result contract, result
representation, adapter boundary, and registration/runtime implementation.

The Exact30 issue identities and order are retained. Exact23 inherited rows are
unchanged. Five ADMIT_014 issues transition to effective `resolved`: authority
source, stage-envelope routing, exact value vocabulary, permission
transition/precedence, and enforcement without aggregation. The standalone
signature and result-contract issues remain open. Unified coverage remains
`ADMIT_014|ADMIT_015`.

## Current readiness and safety

The synthetic exact-`True` design case does not grant current real download
permission. Current permission and `ready_for_bulk_download_now` remain false.
ADMIT_014 is not implemented or registered; the Exact13 runtime remains the
latest runtime. Mandatory enforcement, provider mapping, real provider
evaluation, combined verdict, aggregation, and training readiness remain
false.

Canonical artifact building and checking require CPython 3.10.4. Noncanonical
Python is allowed only for evaluator-semantic smoke; artifact building,
checking, and frozen AST evidence require an explicit contract refresh.

Materialization builds every byte before mutation, uses exclusive leaves,
fsync, pinned parent/root descriptors, and `RENAME_NOREPLACE`. An existing
byte-identical set is an inode-preserving no-op. Mismatch and GPFS `EINVAL`
fail closed; there is no `os.replace` fallback.

Step12D remains a smoke-legality check, not a final training-feature contract.
The historical unknown-atom policy and `feature_semantics_known=false` state
still require a feature-semantics audit before any training.

Recommended next step:
`design_covapie_admit_014_formal_evaluator_interface_contract_v1`.
