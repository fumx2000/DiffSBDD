# CovaPIE Exact9 audited local CCD parent graph authority v1

## Scope

This successor admits exactly the nine SHA-attested local CCD payloads `JUG`,
`E64`, `ZYA`, `PCM`, `INP`, `INA`, `IN6`, `IN3`, and `UFP`. It derives
component-level heavy-only atom, heavy-heavy bond-order, and canonical parent
graph authority. No tenth raw file is discovered or read.

The step does not materialize Current11 observed-to-parent atom projection,
observed projected graphs, reaction-family labels, warhead rules, molecular
roles, minimal seeds, masks, tensors, model changes, or training.

## Source authority and admission

The formal base is
`f8f6945c86a4258387e57691e206753d0b193793`. Expected payload SHA256 values
are loaded dynamically from the base version of
`covapie_ccd_acquisition_integrity_audit.csv`; they are not copied into the
production source.

Before payload bytes are decoded, each explicit path is checked with `lstat`
for existence, regular-file identity, absence of symlinks, a nonzero size below
5 MiB, mode `0644`, project-ignore coverage, absence from the formal base, and
absence from the staged index. Bytes are then read and hashed. Decode and parse
are reachable only after the observed SHA exactly matches the audit SHA.

Both the `data_<component>` block identifier and `_chem_comp.id` must exist and
must exactly equal the filename and audit `het_id`. Matching is case-sensitive.

## Parser and graph semantics

Atom and bond loop parsing, element canonicalization, explicit `H/D/T`
filtering, supported-element closure, and the low-level bond-order contract are
reused from
`covapie_current11_pre_reaction_graph_and_bond_order_authority_v1`.

The audited CCD payloads encode aromatic rings using alternating `SING` and
`DOUB` source orders with `_chem_comp_bond.pdbx_aromatic_flag=Y`. This stage
preserves the source order in evidence and passes a canonical `AROM/Y` pair to
the predecessor normalizer. Thus `Y + SING`, `Y + DOUB`, and `Y + AROM`
normalize to `aromatic`; `N + SING/DOUB/TRIP` normalize to
`single/double/triple`. Unknown orders, invalid flags, `TRIP/Y`, and `AROM/N`
fail closed.

Canonical component graph SHA256 serializes sorted atom triples
`(ccd_atom_id, canonical_element, formal_charge)` and sorted undirected bond
triples `(min_atom_id, max_atom_id, normalized_bond_order)`. It does not depend
on CIF row order, set order, RDKit indices, or SMILES order. RDKit is not used
as atom-name authority.

## Materialized result

- Exact9 local CCD admission: 9/9
- Exact9 component identity: 9/9
- Unique parent-heavy atom rows: 298
- Unique heavy-heavy bond rows: 309
- Normalized bonds: 184 single, 36 double, 89 aromatic, 0 triple
- Unsupported bond orders: 0
- Connected canonical parent graphs: 9/9
- Current11 component parent-graph coverage: 11/11
- Current11 component bond-order coverage: 11/11
- Current11 parent-heavy count matches: 11/11
- Sample-expanded parent-heavy atom occurrences: 324

The two-phase transaction writes nonempty atom and bond authority only if all
nine components pass admission, decode, identity, parse, normalization, graph
validation, and SHA checks, and all eleven Current11 rows pass component
coverage and heavy-count reconciliation. Any failure leaves both authority
tables header-only.

The failure matrix contains the required Exact23 mutations plus the retained
`execution boundary crossed` mutation, for Exact24 total. Every mutation is
typed, changes the baseline, has a unique canonical-JSON signature, hits its
expected reason, and keeps downstream readiness false.

## Readiness boundary

Component-level parent authority is available, but Current11 observed atom
projection and observed projected graphs remain 0/11. Reaction family, approved
warhead rule, role proposal, minimal seed, and human gold review remain 0/11.
Planned/integrated covalent model modules remain 5/0. Mask materialization,
tensorization, model integration, and training readiness all remain false.

The evidence-driven next step is
`materialize_covapie_current11_observed_to_parent_atom_projection_authority_v1`.
