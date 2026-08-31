# CovaPIE 2A2 completed-decision source binding V2

## Scope

This is a thin additive successor to the published 2A2 V1 ingestion. It changes
only active filesystem acceptance. It does not modify or rematerialize V1,
refresh a census, execute reconciliation, create chemical or training
authority, start B2 integration, or authorize parameter updates.

The V2 publication inventory is exactly four text files: the V2 owner, checker,
targeted tests, and this guide. V2 creates no snapshot, matrix, summary,
manifest, CSV, or JSON artifact.

## Source-binding migration

The active V1 path contained two independent exact numeric mode gates:

1. the direct Exact2 formal decision and formal validator bindings; and
2. the Exact11 `formal_evidence_bindings` embedded in the formal JSON.

V2 routes every active source read through
`verify_bound_source_v2`. The combined contract requires a regular non-symlink,
owner readability, no world write, the expected executable class, exact byte
count, exact SHA256, and stable file identity across the read. Verified bytes
are parsed in memory and the source path is not reopened.

Historical `mode` fields are unchanged provenance. Their only active use is to
derive executable class with `bool(int(mode, 8) & 0o111)`; V2 never compares a
live numeric POSIX mode with the historical value.

The combined historical inventory is Exact13:

| Source group | Count | Historical modes | Expected executable |
| --- | ---: | --- | --- |
| Direct formal bindings | 2 | `0664×2` | false |
| Embedded formal evidence | 11 | `0664×8`, `0644×2`, `0600×1` | false |
| Total | 13 | `0664×10`, `0644×2`, `0600×1` | false |

The `.py` formal validator, preparation-package validator, and scientific
preview validator remain explicitly non-executable. File suffixes do not
determine executable class.

The original debt regression is the embedded published 1F8 matrix. Its frozen
mode remains `0600`; an exact-byte live copy at safe non-executable mode `0664`
fails the historical V1 embedded gate with
`FORMAL_EVIDENCE_SOURCE_DRIFT` and passes V2. Modes `0755`, `0666`, and `0777`
remain rejected by executable-class or world-write security checks.

## Active authority path

The V2 owner binds B1, the frozen 2A2 V1 owner/checker/tests, the direct Exact2,
the embedded Exact11, the semantic owners, the 1F8/F24 V1 precedents, the
historical F24 census inputs, the reconciliation owner, and the current
published 2A2 census. It also binds the published F24 V2 owner/checker and
actually calls `verify_published_f24_v1_projection_v2`.

The original formal validator is bound but never executed. Formal JSON
semantics are checked in memory with the frozen V1 pure validator. Runtime
source identity is bound and matched to the expected repository module before
the frozen pure role validation is invoked. Historical validator-report and
reconciliation values are compatibility metadata derived from the published V1
artifacts; they do not create new authority.

The projection checker derives the V1 snapshot, matrix, and summary in memory
from the B1-bound authority and proves byte equality with the four published V1
artifacts. It also independently closes the published manifest bindings and
scientific boundaries. It never calls V1 loading, subprocess, reconciliation,
materialization, mutation, or output-writing paths.

## Frozen 2A2 science

The review unit remains
`COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6`, covering ranks 507–510 in PDB
3ORZ. The observed pair remains PDK1 `CYS:148-` `SG` to ligand `SD`. D1–D5
remain `RELEVANT`, `POSITIVE`, `CONFIRM_OBSERVED_PAIR`,
`SELECT_CANDIDATE_4`, and `EXCLUDE_FROM_TRAINING_ONLY`; D6 is preserved exactly.

Candidate 4 remains `STRICT_LINKER_PRESENT_V1`:

- warhead role region: `[SD]`
- linker: `[C1,C15,C16,C17,O18]`
- scaffold: `[C20,C21,C23,C24,C25,C26,C27,C28,C29,C30,CL99,N19,N22]`
- boundaries: `C1--SD SING` and `C17--N19 SING`

All five canonical tasks apply, including `scaffold_only` / `B3`; there is no
sixth task.

`W=[SD]` is only the sample-level canonical role region. It is not a complete
PRE chemical-warhead definition. Chemical-warhead atoms remain `None`, and no
complete PRE disulfide reagent, PRE topology, PRE geometry, reconstruction,
POST-to-PRE copy, or zero-fill authority is created. The four POST observations
remain source evidence only and do not become geometry training targets.

The 1F8 record remains same-context scientific provenance and does not create a
generic all-disulfide exclusion rule. 2A2 independent human review remains
completed. All reusable chemistry, pair, role, family, and warhead authorities
remain false.

## Census and training boundary

Historical F24-prior values remain frozen at positive 108, relevant 109,
INCLUDE 44, EXCLUDE 64, pair/role 108, and A/B/B2/B3/C counts
108/48/48/108/108. The historical informational projection remains
112/113/44/68 with pair/role 112 and task counts 112/52/52/112/112.

The separately bound current published 2A2 global census has those latter
values. V2 does not refresh or reconcile it. The frozen informational
reconciliation projection remains 95 completed positive events, 13 positive
units, 24 negative events, 4 negative units, 119 total events, 17 total units,
219 unreviewed events, 114 unreviewed units, normalized INCLUDE 27, and
normalized EXCLUDE 68.

2A2 remains human-excluded from training. It is not a future admission
candidate, is not admitted, has no split or tensor target, is not runtime-model
usable, and grants no parameter-update authorization. `READY_FOR_TRAINING` is
false. A feature-semantics audit remains required before any later formal
training work; Step12D was only a smoke legality check, not a final training
feature contract.

## Validation

Run the targeted tests and checker with bytecode and pytest cache disabled:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
pytest -p no:cacheprovider -q \
tests/test_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
python scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py
```

The checker accepts exactly `CANDIDATE_UNTRACKED` and `TRACKED_CLEAN`. The
candidate profile requires baseline HEAD and `origin/main` with exactly the
untracked V2 Exact4 and no tracked or staged diff. The tracked-clean profile
requires one Exact4-only child of the frozen baseline, either one commit ahead
of `origin/main` or published at `origin/main`.
