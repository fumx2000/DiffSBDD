# CovaPIE Current11 family/rule approval review package v1

## Scope

This increment materializes an initially blank, metadata-only human review
workspace for the seven unique Current11 candidate reaction-family/warhead-rule
pairs. The seven units cover all eleven Current11 samples exactly once and are
ordered by `warhead_rule_id`.

It does not approve a reaction family or warhead rule. It does not derive or
guess SMARTS. Candidate canonical local-graph JSON remains supporting evidence
only and is neither approved SMARTS nor a formally equivalent approved
structural pattern. The increment does not compile or ingest a review, create
an authority bundle, propose roles or minimal seeds, tensorize, access a
checkpoint, execute a model, or train.

## Frozen evidence lineage

The builder fail-closes on formal binding commit
`2e07b7b094e2dccc69eaf29b5f51db0f9af2e81b` and reads its binding matrix,
registry, source inventory, and manifest as Git objects with exact SHA256
verification. Candidate assignments and rule-registry evidence are read from
commits `0c8d1d10260a028360357b8c309f22676fc81645` and
`dc1222503dcec83220a28df2abdae898a0855864`.

The formal binding evaluator revalidates the SHA-bound S02 legacy submission →
S03 legacy ingestion → S04 multi-boundary submission → S05 multi-boundary
ingestion → S06 multi-boundary authority → S01 unified effective authority
lineage, including filesystem SHA, internal record digests, direct producers,
and the transitive state binder. The review package then freezes S01 reviewed
warhead atom sets and effective attachment boundaries without changing their
meaning.

No raw structure path is read.

## Exact5 external workspace

The canonical workspace entry is
`<covapie-state>/manual-review/current11-family-rule-approval-v1`. Under the
`relative_symlink_to_immutable_sibling_v1` publication scheme it is a relative
symlink to a same-parent hidden object directory named
`.current11-family-rule-approval-v1.object-<unique-token>`. That immutable
object directory contains exactly:

1. `README.md`
2. `family_rule_approval_worklist.csv`
3. `family_rule_candidate_evidence.json`
4. `sample_support_evidence.csv`
5. `review_package_manifest.json`

The object-directory mode is `0755`; every file mode is `0644`; internal
subdirectories, symlinks, and special files are forbidden. The canonical link
target is one basename, contains no slash or `..`, starts with the exact object
prefix, and resolves only within the same `manual-review` parent. All payloads
are deterministic UTF-8 bytes under 1 MiB. The manifest binds the other four
files and does not record its own hash.

Every human-fillable family, rule, attestation, decision, rationale, reviewer,
attestor, notes, and completion field is the empty string at materialization.
An empty field means “not reviewed”; no machine-generated negative or pending
decision is prefilled.

## Future decision contracts

Family decisions form the closed vocabulary:

- `approve_reaction_family_identity`
- `revise_reaction_family_identity`
- `quarantine_reaction_family`

A future family approval requires reviewed version, semantic name, structural
basis, explicit identity attestation, rationale, reviewer, attestor, and a
completed review.

Rule decisions form the closed vocabulary:

- `approve_complete_warhead_rule`
- `revise_warhead_rule`
- `quarantine_warhead_rule`

A future complete-rule approval requires the predecessor family/version,
target residue and atom, mapped SMARTS and atom-map contracts, expected
pre-reaction bond orders, charge policy, match count, and priority. It also
requires a leaving-group contract, formed-bond order, ambiguity and tie
policies, identity/full-semantics/structural-pattern attestations, rationale,
reviewer, attestor, and a completed review. This increment only documents these
future rules; it does not validate a filled submission.

## CPFS-compatible no-replace materialization

The CLI requires an absent canonical entry. It writes Exact5 to a unique hidden
object sibling, verifies bytes, SHA256, types, modes, and the recorded object
inode, then atomically creates the canonical relative symlink with
`os.symlink`. Symlink creation has native no-replace behavior: any existing
file, directory, or symlink, including a target created in a race, produces
`EEXIST` and is preserved.

Ordinary `rename` is forbidden because it can replace an existing empty
competitor directory. `renameat2(RENAME_NOREPLACE)` is not a publication
prerequisite because the target CPFS returns `EINVAL` for that operation.

Before link publication, failure cleanup checks every created file inode and
the object-directory inode before unlinking. A replaced inode is preserved and
causes fail-closed behavior. After link publication, the materializer records
the canonical symlink inode, checks exact `readlink` text, rechecks the object
inode, and performs complete read-only validation. Any post-publication drift
is preserved for investigation rather than deleted.

After materialization, `--check` is read-only. Its deterministic JSON report
includes workspace file hashes, lifecycle profile, and response digest.

## Candidate lifecycle

The exact nine repository candidate files support and are exercised through:

- `review_package_precommit_candidate`
- `review_package_committed_unpushed`
- `review_package_published_successor`

The frozen future commit subject is
`add CovaPIE Current11 family and rule approval review package v1`. Lifecycle
validation independently checks commit blobs, index blobs, actual worktree
blobs, the exact parent and path set, live porcelain state, and an Exact8
external witness derived from Git before response construction. Responses use
a frozen field order and exact int/bool/string/dict types; extra or missing
fields and valid-looking witness substitutions fail closed even after digest
recalculation. The Exact5 workspace hashes are independently derived from the
payload bytes before response construction, copied into the response without
sharing the witness dictionary, and compared against that external witness by
the validator. X49 proves that replacing the README digest with a different
valid lowercase 64-hex value and recalculating the response digest still fails
closed. This task stops in the precommit profile and creates no commit or push.
