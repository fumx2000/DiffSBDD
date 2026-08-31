# CovaPIE future exact-POSIX mode guard V2

## Purpose and boundary

Phase B4 is the final source-binding filesystem-mode authority V2 migration
phase. It prevents new or modified CovaPIE production, authority, checker, and
template surfaces from treating a live file's exact numeric POSIX permissions
as scientific content identity or source admit/reject identity.

The permanent forward baseline is commit
`54f98c41e2dc34d816a17242292ee2379e99783e`, tree
`ba92ef88433c8290285dacf482ed17300753fbab`, with subject
`add CovaPIE source binding historical immutability proof v2`.

Bytes at or before that baseline remain frozen history. The published Phase-B3
historical immutability proof is the only authority that permits their legacy
exact-mode debt to remain. Phase B4 neither edits those bytes nor grants a
filename exemption: if a historical `_v1.py` path changes after the baseline,
it is a future change and enters the guard's scan surface. No historical mode
field, census, validator, or `covapie-state` artifact is rewritten.

This migration phase is unrelated to the canonical task-mask set. The semantic
long names remain exactly:

1. `warhead_only` (`A`)
2. `linker_plus_warhead` (`B`)
3. `scaffold_plus_warhead` (`B2`)
4. `scaffold_only` (`B3`)
5. `scaffold_plus_linker_plus_warhead` (`C`)

There is no sixth mask.

## Guard authority

The public, read-only entry point is:

```python
verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
    *,
    repo_root: Path,
) -> dict[str, object]
```

It first binds the published B1 policy, B3 production owner, and B3 checker by
byte count, SHA256, non-executable class, and B1 security rules. It then
actually calls the published B3 proof. A B3 failure is a B4 failure.

The production API accepts any descendant of the permanent baseline. It does
not require a single child commit. On every call it derives and combines:

- committed changes from `git diff --name-status <baseline> HEAD`;
- tracked worktree/index changes from `git diff --name-status HEAD`;
- ordinary untracked paths from `git ls-files --others --exclude-standard`.

The frozen scan scope is:

```text
src/covalent_ext/**/*.py
scripts/check_covapie*.py
tests/test_covapie*.py
data/derived/covalent_small/**/*.json
```

Committed bytes come from the deterministic `HEAD:<path>` Git object.
Worktree and ordinary-untracked bytes are read through a bounded, read-only
descriptor with path-containment, regular-file, non-symlink, security,
size, UTF-8, and before/opened/after identity-stability checks. The verifier
does not write a manifest, cache, registry, allowlist, summary, or report.

## Static semantic classifier

The Phase-A implementation at commit
`26555ff6240ee53c817726331c8353dcb62dc82e` was used only as a published
classifier design precedent. B4 does not import it as mutable runtime
authority. Four pure ideas were reimplemented for the forward gate:

- parse Python with `ast` instead of deciding from raw grep counts;
- preserve the six published semantic classes;
- separate semantic classification from `TEST_ONLY` context;
- recursively inspect structured JSON binding objects.

The six semantic classes are:

```text
SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE
SECURITY_HYGIENE_MODE_CHECK
CANDIDATE_ARTIFACT_MODE_HYGIENE
GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT
REPORTING_OR_DIAGNOSTIC_MODE_METADATA
AMBIGUOUS_REQUIRES_HUMAN_REVIEW
```

The Python classifier tracks small, deterministic assignment families for
full live-mode extraction, raw `st_mode`, and executable-class projection. It
recognizes `stat.S_IMODE`, full masks such as `0o7777`, octal formatting,
binding `mode` access, exact-mode literals or membership, binding dictionaries,
security bits, executable-bit projection, Git file classes, candidate hygiene,
and reporting-only metadata. It is intentionally not a general program
verifier. Full/raw live-mode and expected-authority taints propagate through
ordinary aliases within their Python scope. Every comparison containing a
full/raw live mode is classified; an unresolved gate is ambiguous and fails
closed. Historical values such as `0600`, `0644`, `0664`, and `0755` are
regression examples, not the universe of forbidden future POSIX permissions.

The JSON classifier walks every object and list. A current object combining
`path`, `byte_count`, `sha256`, and `mode` is forbidden. A partial identity
object with `mode` or `expected_mode` is ambiguous and fails closed unless the
schema unambiguously marks historical provenance or reporting-only metadata.

Tests are scanned as `TEST_ONLY`. Embedded negative-control snippets can be
classified and counted, but they cannot become production violations.

## Forbidden and allowed meanings

Forbidden future semantics include comparing full live numeric permissions to
an expected mode, a binding's `mode`, an exact octal literal/string, or an exact
mode membership set for source content/scientific identity. A current binding
contract equivalent to `path + byte_count + sha256 + mode` is also forbidden.

The following remain distinct and allowed:

- world-writable, owner-readable, regular-file, and symlink security checks;
- executable/non-executable class checks such as `bool(mode & 0o111)`;
- Git-native `100644`/`100755` blob classes;
- candidate artifact hygiene such as accepting `0644` or `0664`;
- reporting and diagnostic preservation of historical mode metadata;
- converting historical mode provenance only to expected executable class.

Candidate wording alone cannot turn source/content/scientific identity into
candidate artifact hygiene: a positive artifact/publication/file-hygiene
context is required and source-identity context takes precedence. Executable
class requires structural executable-bit evidence such as `mode & 0o111`;
variable naming is not evidence. Likewise, `historical_mode` remains
reporting/provenance metadata only and cannot be reused in live source
accept/reject identity.

Allowed occurrences are reported in separate counters and are not required to
be zero. Success requires both future semantic exact-mode findings and
ambiguous mode findings to be exactly zero.

## Publication and future use

The publication checker has exactly two success profiles:

- `CANDIDATE_UNTRACKED`: baseline `HEAD=origin/main`, clean tracked/index state,
  and exactly the four B4 files as ordinary untracked paths;
- `TRACKED_CLEAN`: one clean Exact4-only child of the baseline, either one
  commit ahead of baseline `origin/main` or already published with
  `origin/main=HEAD`.

This strict publication lifecycle does not narrow the long-term production
API. Future source-binding, authority, checker, or template changes should call
the published B4 production guard, or an equivalent fail-closed gate, before
publication.

Phase B4 closing readiness is not training readiness. Step12D remains only a
smoke legality check, not a final training-feature contract. A separate future
feature-semantics audit must resolve or formally audit
`UNKNOWN_ATOM_FEATURE_POLICY` and `feature_semantics_known=False` before any
formal training, fine-tuning, backward pass, optimizer step, or parameter
update.
