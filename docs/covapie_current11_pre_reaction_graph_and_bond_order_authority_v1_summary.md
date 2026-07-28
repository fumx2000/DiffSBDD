# CovaPIE Current11 Pre-reaction Graph and Bond-order Authority V1

## Outcome

This small authority stage fails closed with
`blocked_BASE_tracked_atom_named_CCD_authority_absent`.

Current11 contains 11 samples and 9 evidence-derived ligand components:
JUG, E64, ZYA, PCM, INP, INA, IN6, IN3, and UFP. The committed descriptor,
graph-hash, atom-inventory, sample atom-table, reactive-atom mapping, and
heavy-projection evidence remains useful supporting evidence. It does not
contain a complete atom-named parent CCD atom table plus atom-named,
bond-order-bearing CCD bond table.

The nine CCD component paths recorded by the committed acquisition audit are
not present in the BASE tree. Their ignored local payloads were not read.
Consequently, no ignored cache was promoted to formal authority and no
atom-name mapping was guessed from SMILES order, element, degree, coordinates,
RDKit atom order, or canonical rank.

## Source decision

The source inventory audits 25 candidate sources:

- 16 committed predecessor, metadata, projection, descriptor, or historical
  topology artifacts;
- 9 CCD paths attested by a committed audit but absent from the BASE tree.

No candidate is classified as `authoritative`. Descriptor SMILES and graph
hashes are `supporting_only`. The Step 8 RDKit atom/bond topology artifacts
cover a different three-sample family and do not provide Current11 CCD atom
names. The historical topology policy explicitly wrote no topology table.

## Parent graph and observed projection

The supporting inventory contains 324 per-sample parent-heavy atom
occurrences and 323 observed retained-heavy atom occurrences. These counts are
not atom/bond authority. The authoritative parent-atom table and the
parent/projected-bond table therefore contain their fixed headers and zero data
rows.

For ZYA, supporting evidence records parent F1, its absence from the
post-covalent observed inventory, the leaving-group class, and the claimed
CM--F1 relationship. Because the CM--F1 parent bond is not available from a
BASE-tracked atom-named bond authority, F1 is not materialized into a false
parent graph and the leaving-group projection remains unavailable.

## Validation contract

The implementation provides a pure in-memory validator for atom-named CCD
atoms, CCD bond orders, exact atom-name projection, leaving-group evidence,
graph connectivity, and deterministic canonical graph SHA256. The normalized
bond-order vocabulary is exactly `single`, `double`, `triple`, and
`aromatic`. Unsupported orders and aromatic flag/order conflicts fail closed.
RDKit status may validate a graph but cannot create atom-name authority.

The public parser and validator now reject unstable containers, duck-typed or
subclass records, Python boolean/integer impersonation, malformed atom and
bond fields, duplicate or non-contiguous row/index spaces, malformed
leaving-group arguments, and non-exact control arguments before graph business
logic runs. Unknown, missing, or non-integer CCD formal charge is rejected
rather than silently replaced with zero. Invalid inputs emit empty graph SHA
sentinels.

Leaving-group approval booleans are not sufficient evidence by themselves.
For every missing leaving-group atom, the validator independently reconstructs
at least one normalized legal parent bond to a non-leaving parent atom.
Unsupported or otherwise invalid bonds do not participate in connectivity,
leaving-group verification, or canonical graph serialization.

`parse_ccd_component` now defines its returned parent graph as heavy-only.
Every source atom field is validated before projection, element symbols are
canonicalized, and explicit H, D, and T atoms are removed. Bonds involving at
least one explicit hydrogen endpoint are removed only after every source bond
endpoint has been verified against the complete source atom loop. Remaining
heavy atoms are reindexed contiguously in source-loop order. F, Cl, Br, I, and
other supported non-hydrogen elements remain heavy atoms; atom IDs are never
renamed.

The companion parsing helper exposes source atom, explicit-hydrogen, heavy
atom, source bond, hydrogen-involving bond, and heavy-heavy bond counts without
creating an additional evidence file. An all-hydrogen parent component fails
closed. Empty or whitespace atom IDs/type symbols, empty bond fields, and bond
endpoints absent from the source atom loop are rejected in the parser rather
than deferred to downstream validation.

Parser output, validator element comparison, and graph SHA serialization use
one canonical element-symbol helper. Lowercase and uppercase representations
of the same valid element therefore produce identical parent and observed
graph SHA values. Atom IDs remain case-sensitive. Direct public injection of
H, D, or T into parent or observed heavy graphs is rejected with a specific
reason and empty graph SHA sentinels.

The failure matrix contains 28 explicit dataclass mutations covering every
required failure scenario. Mutated fields have exact types, differ from the
valid baseline, are stored as canonical JSON dictionaries, have unique
signatures, and hit their explicit expected reasons. Each row's `verified`
value is derived from its reason and fail-closed readiness observations rather
than assigned as a constant. Runtime bypass probes independently exercise the
public validation surface. Every invalid case disables reaction-family rule
design, role proposal generation, mask materialization, model integration,
and training.

## Readiness

All 11 rows retain descriptor graph support, but all 11 remain false for:

- atom-named parent graph and parent bond-order authority;
- exact observed-to-parent projection and leaving-group projection;
- parent and observed graph validity;
- pre-reaction connectivity and bond-order availability;
- reaction-family label and approved warhead rule;
- role and minimal-seed proposal generation;
- human gold review, masks, tensorization, model integration, and training.

No reaction-family label, warhead SMARTS rule, role, seed, mask, tensor,
module, dataloader, forward path, loss, checkpoint, or training output is
created. Planned/integrated covalent model modules remain 5/0. The historical
formal training feature-semantics audit and unknown-atom policy resolution
were completed in their historical formal stages. Runtime enforcement,
role/seed authority, geometry authority, model integration, and the training
path remain incomplete. Step12D established smoke legality only; it does not
establish current training readiness.

The evidence-driven next step is
`resolve_covapie_current11_pre_reaction_graph_authority_blockers_v1`, not
reaction-family design or training.
