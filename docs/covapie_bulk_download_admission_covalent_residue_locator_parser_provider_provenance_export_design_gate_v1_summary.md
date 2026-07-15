# CovaPIE Step14AU-E0-P4 Summary

Step14AU-E0-P3 integrated five covalent-residue locator metadata fields into
the 22-field admission schema. P4 freezes only the design for exporting the
parser evidence needed to populate those fields. It does not read raw
structures, modify either parser, implement a provider, or materialize any
candidate record or provider payload.

The design preserves three exact mmCIF source tags:

- `_atom_site.pdbx_PDB_ins_code`
- `_struct_conn.pdbx_ptnr1_PDB_ins_code`
- `_struct_conn.pdbx_ptnr2_PDB_ins_code`

Raw tokens are retained without trimming, coercion, case conversion, or
Unicode normalization. An explicit token, `.`, `?`, a missing tag, and an
empty parsed value have different meanings. Two identical explicit tokens may
resolve to `present`; two `.` tokens may resolve at design level to `absent`.
One-sided evidence cannot promote a state. Conflicts and unknown or invalid
evidence resolve to `unknown` and continue to block ADMIT_004.

Tag presence is encoded without adding a payload field. A missing tag uses an
empty source-tag value and an empty raw value. A parsed empty token uses the
exact expected source tag and an empty raw value. Therefore missing and parsed
empty evidence have different canonical bytes and SHA256 values. A non-empty
tag must exactly match the atom-site tag or the struct-conn partner-side tag.

The future provider maps the resolved evidence to exactly the five P3 fields:
the unchanged locator namespace, insertion state and value, an opaque source
ID, and a canonical evidence SHA256. The source ID template is
`covapie:residue-locator:<sample_preparation_input_id>:<conn_id>:<residue_partner_side>`.
Its sample and connection components must be non-empty ASCII strings without
outer whitespace, colons, or path separators, preventing delimiter collisions.
The provider mapping helper recomputes resolution from source tags and raw
tokens; callers cannot inject a second resolved-state truth.
It also recomputes the selected chain and residue index against explicit
`auth` or `label` struct-conn evidence. Mixing namespaces or supplying selected
values that disagree with the declared namespace fails closed. Different auth
and label values are recorded as a conflict observation but remain valid when
the selected pair consistently follows the explicit namespace.

The 20-key provenance payload also binds the unique matched atom-site row ID
and the residue atom name copied from that row. Both are opaque, exact ASCII
values; the design does not force numeric row IDs, uppercase atom names, or
`SG`. Atom-name normalization therefore remains an independent blocker.

The SHA256 covers a fixed, compact, ASCII JSON payload containing only locator
evidence tokens; it contains no timestamp, host identity, absolute path, or
raw file content. Payload dictionaries may arrive in any insertion order; the
validator checks the exact key set and reconstructs canonical key order before
serialization. Standalone validation reapplies source-ID component rules,
namespace evidence resolution, matched atom-site row validation, and insertion
resolution. Any contradiction fails closed. An admission evaluator must not
dereference the source ID.

P4 does not prove insertion-code absence for any of the 11 existing samples;
all 11 remain `unknown`. The complete grammar for a `present` insertion value
is not frozen. The parser and provider remain unimplemented, ADMIT_004 and E1
remain blocked, and the independent residue atom-name blocker is unchanged.

The canonical masks remain exactly `warhead_only/A`,
`linker_plus_warhead/B`, `scaffold_plus_warhead/B2`, `scaffold_only/B3`, and
`scaffold_plus_linker_plus_warhead/C`. Candidate evaluation, bulk download,
model execution, and training are not authorized. A feature-semantics audit
is still required before formal training, fine-tuning, or real parameter
updates.
