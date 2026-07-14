# CovaPIE Canonical Final-Dataset QA Gate v1

Step14AS-B validates the committed Step 14AR canonical final-dataset
materialization through a read-only source boundary. The gate reads exactly the
twelve Step 14AR output files and the single Step 14AQ manifest. It does not
open any of the artifact paths named within the Step 14AR inventory.

The QA output root contains seven CSV audits and one manifest. The manifest
records deterministic hashes for the seven non-manifest outputs; its own hash
is checked by the check script after each materialization because a manifest
cannot contain a stable hash of its own complete bytes.

The canonical final-dataset schema remains 33 fields and 11 rows. Mask
semantics come from the Step 14AR manifest: the final index has no mask fields,
and this QA gate does not claim otherwise. The canonical mask contract remains,
in order: `warhead_only`/`A`, `linker_plus_warhead`/`B`,
`scaffold_plus_warhead`/`B2`, `scaffold_only`/`B3`, and
`scaffold_plus_linker_plus_warhead`/`C`.

Split sample and group counts are independently recomputed from final-dataset
membership. Artifact-reference counts are independently recomputed by joining
the 66 Step 14AR artifact-inventory metadata rows to membership; referenced
artifact files are never opened. The Step 14AQ manifest supplies sample and
group counts for cross-checking, but does not supply artifact-reference counts.
That unavailable evidence is recorded explicitly as
`not_available_in_source_manifest`, without inventing an AQ cross-check.

This gate does not read raw structures, use network access, import scientific
runtime libraries, generate tensors, run models, or change training readiness.
Feature-semantics audit and leakage/split design remain required before any
formal training, fine-tuning, or real parameter update.
