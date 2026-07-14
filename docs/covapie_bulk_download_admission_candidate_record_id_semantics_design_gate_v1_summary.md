# CovaPIE Candidate Record ID Semantics Design Gate v1

Step14AU-C1 freezes the pure, in-memory `candidate_record_id` contract for a
future ADMIT_001 integration. Frozen expected evidence is independent from the
actual helper observations, and every contract row is backed by a separate
probe. It accepts only exact Python `str` values that
are ASCII, one to 128 characters, and match
`^[A-Za-z0-9](?:[A-Za-z0-9._:-]{0,126}[A-Za-z0-9])?$`. Normalization is
identity: no trimming, case normalization, Unicode normalization, or coercion
is allowed. `ABC` and `abc` remain distinct.

The identifier is a stable metadata-record key supplied by a future metadata
provider. It is not a PDB, ligand, chemistry, covalent-event, leakage-group,
raw-path, download-file, or training-sample identity. It is strictly separate
from `duplicate_identity_key`; batch uniqueness does not replace ADMIT_009
deduplication. Producers must reuse the identifier for the same logical source
record and source version, without random values, timestamps, or batch-order
derivation. The evaluator neither generates nor modifies IDs and performs no
I/O.

The future batch contract accepts only exact `list` or `tuple` containers. The
batch must be non-empty, every member must pass the single-value contract, the
current candidate must occur exactly once, and all batch IDs must be globally
unique. Evaluation is order independent and case sensitive. Result fields keep
the observed batch facts even when a higher-priority candidate error determines
the primary blocking reason.

C1 normal materialization reads exactly the six frozen Step14AU-B2 metadata
outputs and does not read its own production source text. Its behavioral and
static contract probes inspect only in-memory public-function code objects.
The external check script and tests separately read production source text and
use AST validation for forbidden imports, self-introspection, identifier
generation, and helper-dependency boundaries; that verification read is not a
C1 manifest data source. C1 does not read raw structures or artifact targets,
perform candidate evaluation, create a queue, download data, or train. The B2 effective view still retains all twelve
blockers, including `CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED`; C1 merely
freezes its design layer. `candidate_record_id_semantics_integrated=false`,
`integration_applied_current_step=false`, and `admit_001_rule_logic_ready=false`.
C2 integration is required before that successor-view
blocker could be removed. The other eleven blockers remain unresolved.

The five canonical masks remain unchanged: `warhead_only`/A,
`linker_plus_warhead`/B, `scaffold_plus_warhead`/B2, `scaffold_only`/B3, and
`scaffold_plus_linker_plus_warhead`/C. Training, fine-tuning, and real
parameter updates remain disallowed; a feature semantics audit remains required
before formal training.
