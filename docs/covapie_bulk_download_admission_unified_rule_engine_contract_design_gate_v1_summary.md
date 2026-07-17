# CovaPIE Step14AU-E1-E4 Phase 1 summary

This phase freezes the design contract for a future single-rule unified
admission engine. It does not implement a dispatcher, evaluator adapter,
runtime registry, combined candidate verdict, candidate evaluation, download,
or training path.

## Frozen boundary

The conceptual public entry point accepts one `admission_rule_id`, one candidate
mapping, and four explicit optional context mappings. The engine may pass only
declared candidate fields and caller-provided contexts. It may not build
provider evidence or access the filesystem or network. There is no
`evaluate_all_rules` API and no cross-phase aggregation contract.

The future immutable `UnifiedAdmissionRuleEvaluation` has exactly 13 fields.
Its per-rule outcome vocabulary is `passed|blocked|invalid|rejected`.
`ADMIT_004` permits `passed|blocked|invalid`; the ADMIT_005 design evidence
permits `passed|rejected|invalid`. The local
`invalid>rejected>blocked>passed` evidence is not a global engine precedence.

The future `UnifiedAdmissionDispatchError` has exactly six fields and five
codes. Unknown identifiers and known-but-unsupported rules are distinct.
Unsupported or invalid dispatch cannot default to passed, masquerade as a rule
evaluation, invoke an evaluator after context validation fails, or participate
in candidate outcome aggregation.

## Evaluator and routing inventory

Frozen AST inspection discovers four formal public evaluators:

- `ADMIT_001`: `evaluate_admit_001_candidate_record_id`, legacy mutable dict;
- `ADMIT_002`: `evaluate_admit_002_pdb_identifier`, legacy mutable dict;
- `ADMIT_003`: `evaluate_admit_003_ligand_comp_id`, legacy mutable dict;
- `ADMIT_004`: `evaluate_admit_004`, frozen `Admit004EvaluationResult`.

The first three require unresolved adapters. ADMIT_004 has a design-ready
adapter contract and is ready only for a future minimal dispatch-shell
registration. ADMIT_005–015 have no formal public evaluator and remain known
unsupported. The 15-row routing matrix partitions batch, evaluation, download
result, and stage authorization contexts. In particular,
`covalent_residue_identity_evidence_context` is caller-provided and passed
through to ADMIT_004; the engine cannot construct or complete it.

## Git lifecycle contract

`EXPECTED_BASE_COMMIT` identifies the frozen evidence tree, not the only HEAD at
which this gate may run. The current HEAD may be that base commit or any
successor commit, provided the expected base exists as a commit object, retains
its frozen subject, and is an ancestor of the current HEAD. Exact21 filesystem
bytes must still match both the expected-base blobs and the frozen SHA256 values.
A non-descendant HEAD or any Exact21 source drift fails closed. This lineage
contract keeps the gate reproducible from the implementation base, a temporary
candidate successor commit, and the eventual formal Phase 1 successor commit.

## Evidence and readiness

The gate freezes an ordered Exact21 committed-source boundary. The independently
discovered and frozen SHA256 values for the ADMIT_001–003 callable sources are:

- `3246a131a3815aa184338637edef6d8c9020b2dc23f41794e5697812467d269b`
- `c78ed4986551913dea75dc220609f97154941ebda5afffaa84ff252e9d36df83`
- `8d616a02b5f87ea98be3029879d55acd3c06c26e7286a46cb293bd6a4a7f6e11`

All source structural checks precede the first byte read. CSV, JSON, and Python
AST parsing uses only frozen snapshot bytes, without recursively opening
artifact references or importing or executing evaluators.

The engine issue inventory preserves the predecessor Exact9 rows unchanged and
adds three blocking engine issues, for 12 active rows. The provider blocker
remains open, blocking, and has count 11.

The design contracts are frozen and ADMIT_004 is ready for a future minimal
dispatch-shell implementation. The dispatcher, runtime registry, adapters,
15-rule coverage, combined verdict, cross-rule precedence, real candidate
evaluation, bulk download readiness, and training readiness remain false. A
feature-semantics audit is still required before any training work; Step12D was
a smoke legality check, not a final training-feature contract, and the
historical `UNKNOWN_ATOM_FEATURE_POLICY` / `feature_semantics_known=False`
condition remains a readiness blocker requiring formal audit.

Recommended next step:
`implement_covapie_minimal_unified_admission_dispatch_shell_with_admit_004_v1`.
