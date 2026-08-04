from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import stat
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1
    as gate,
)


@pytest.fixture(scope="session")
def response() -> dict[str, object]:
    return gate.evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1(
        repo_root=REPO_ROOT,
    )


@pytest.fixture(scope="session")
def derived() -> tuple[
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
    tuple[dict[str, object], ...],
]:
    for evidence_id, *_rest in gate._GIT_EVIDENCE:
        gate._git_blob(REPO_ROOT, evidence_id)
    return gate._derive_binding(REPO_ROOT, gate._read_state_evidence(REPO_ROOT))


def _expected_lifecycle(response: dict[str, object]) -> dict[str, object]:
    return {field: response[field] for field in gate._RESPONSE_LIFECYCLE_FIELDS}


def _git_text(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT,
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    return result.stdout


def _synthetic_response_for_profile(
    response: dict[str, object], profile: str,
    matrix: tuple[dict[str, str], ...],
    registry: tuple[dict[str, str], ...],
) -> tuple[dict[str, object], dict[str, object]]:
    facts = gate._synthetic_lifecycle_facts_v1(profile)
    lifecycle = gate._derive_binding_lifecycle_v1(facts)
    witness = gate._expected_response_lifecycle(
        origin=facts["origin"], ahead=facts["ahead"], behind=facts["behind"],
        lifecycle=lifecycle,
    )
    projected = copy.deepcopy(response)
    projected.update(witness)
    gate._rehash_response_v1(projected)
    gate._validate_response_v1(
        projected, matrix, registry, expected_lifecycle=witness,
    )
    return projected, witness


def _assert_formal_commit_identity(commit: str) -> None:
    assert _git_text("show", "-s", "--format=%s", commit).strip() == gate._FORMAL_COMMIT_SUBJECT
    assert _git_text("show", "-s", "--format=%P", commit).split() == [gate._BASE]
    status_lines = _git_text(
        "diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit,
    ).splitlines()
    statuses = {parts[1]: parts[0] for parts in (
        line.split("\t") for line in status_lines
    ) if len(parts) == 2}
    assert tuple(sorted(statuses)) == gate._CANDIDATE_PATHS
    assert statuses == {path: "A" for path in gate._CANDIDATE_PATHS}
    for path in gate._CANDIDATE_PATHS:
        tree_metadata, listed = _git_text("ls-tree", commit, "--", path).strip().split("\t", 1)
        tree_mode, kind, commit_blob = tree_metadata.split()
        index_metadata, indexed = _git_text("ls-files", "--stage", "--", path).strip().split("\t", 1)
        index_mode, index_blob, stage = index_metadata.split()
        actual_blob = _git_text("hash-object", "--no-filters", "--", path).strip()
        assert listed == indexed == path
        assert (tree_mode, kind, index_mode, stage) == ("100644", "blob", "100644", "0")
        assert commit_blob == index_blob == actual_blob
        metadata = (REPO_ROOT / path).lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644


def test_public_api_is_keyword_only_and_conclusion_c(
    response: dict[str, object],
) -> None:
    function = gate.evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1
    assert tuple(inspect.signature(function).parameters) == ("repo_root",)
    assert inspect.signature(function).parameters["repo_root"].kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        function(REPO_ROOT)  # type: ignore[misc]
    assert response["binding_conclusion"] == "family_and_rule_not_authoritative"
    assert response["reaction_family_authority_bound_count"] == 0
    assert response["approved_warhead_rule_authority_bound_count"] == 0
    assert response["recommended_next_increment"] == (
        "materialize_covapie_current11_reaction_family_and_warhead_rule_"
        "approval_review_package_v1"
    )


def test_response_is_byte_deterministic_and_fixed_order(
    response: dict[str, object],
) -> None:
    second = gate.evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1(
        repo_root=REPO_ROOT,
    )
    assert tuple(response) == gate._RESPONSE_FIELDS
    assert tuple(second) == gate._RESPONSE_FIELDS
    assert gate._canonical_json_bytes(response) == gate._canonical_json_bytes(second)
    assert next(reversed(response)) == "response_unsigned_canonical_json_sha256"


def test_exact11_matrix_separates_candidate_boundary_and_approval_scope(
    response: dict[str, object],
) -> None:
    matrix = response["current11_family_rule_authority_binding_matrix"]
    assert isinstance(matrix, tuple) and len(matrix) == 11
    assert [row["sample_index_row_id"] for row in matrix] == list(gate._EXPECTED_SAMPLES)
    for row in matrix:
        assert row["candidate_assignment_exact_one"] == "true"
        assert row["candidate_matches_effective_boundary_authority"] == "true"
        assert row["candidate_matches_pre_reaction_graph"] == "true"
        assert row["candidate_matches_reaction_delta"] == "true"
        assert row["candidate_matches_reactive_atoms"] == "true"
        assert row["boundary_review_completed"] == "true"
        assert row["selected_candidate_identity_attested"] == "true"
        assert row["reaction_family_identity_explicitly_attested"] == "false"
        assert row["warhead_rule_identity_explicitly_attested"] == "false"
        assert row["warhead_rule_full_semantics_explicitly_attested"] == "false"
        assert row["approved_structural_pattern_attested"] == "false"
        assert row["reaction_family_authority_status"] == "candidate_only"
        assert row["warhead_rule_approval_status"] == "candidate_only"
        assert row["binding_conflicts"] == ""
        assert row["binding_blockers"] == gate._BLOCKERS


def test_unique_registry_is_evidence_derived_and_formal_gaps_stay_empty(
    response: dict[str, object],
) -> None:
    registry = response["family_and_warhead_rule_authority_registry"]
    assert isinstance(registry, tuple) and len(registry) == 7
    rules = [row["warhead_rule_id"] for row in registry]
    assert rules == sorted(rules)
    assert len(rules) == len(set(rules))
    assert sum(int(row["sample_count"]) for row in registry) == 11
    for row in registry:
        assert row["reaction_family_version"] == ""
        assert row["reaction_family_semantic_name"] == ""
        assert row["reaction_family_structural_basis"] == ""
        assert row["warhead_rule_version"] == ""
        assert row["warhead_rule_semantic_name"] == ""
        assert row["expected_pre_reaction_bond_orders"] == ""
        assert row["allowed_formal_charge_pattern"] == ""
        assert row["allowed_match_count"] == ""
        assert row["priority"] == ""
        assert row["structural_representation_type"] == ""
        assert row["structural_representation"] == ""
        assert row["approval_scope"] == "boundary_only_not_family_or_rule"
        assert row["approval_status"] == "candidate_only"
        assert row["blocking_fields"] == gate._REGISTRY_BLOCKERS


def test_predecessor_requires_complete_mapped_smarts_contract() -> None:
    manifest = gate._strict_json(gate._git_blob(REPO_ROOT, "E10"))
    assert tuple(manifest["warhead_rule_fields"]) == gate._REQUIRED_WARHEAD_RULE_FIELDS
    rule_rows = gate._csv_rows(gate._git_blob(REPO_ROOT, "E05"))
    assert len(rule_rows) == 7
    for row in rule_rows:
        assert row["approved"] == "false"
        assert row["human_gold_review_completed"] == "false"
        assert row["approved_warhead_smarts"] == ""
        assert row["SMARTS_status"] == "not_materialized_in_design_stage"
    predecessor_source = gate._git_blob(REPO_ROOT, "E09")
    predecessor_guide = gate._git_blob(REPO_ROOT, "E18")
    assert b"warhead_smarts" in predecessor_source
    assert b"mapped SMARTS" in predecessor_guide
    assert b"equivalent structural contract" not in predecessor_source + predecessor_guide


def test_review_schemas_do_not_attest_family_or_full_rule() -> None:
    state = gate._read_state_evidence(REPO_ROOT)
    effective = gate._validate_review_scope(state)
    assert tuple(effective) == gate._EXPECTED_SAMPLES
    assert sum(item["namespace"] == "legacy_exact_one_boundary_v1" for item in effective.values()) == 6
    assert sum(item["namespace"] == "exact_two_boundaries_multi_boundary_v1" for item in effective.values()) == 5
    legacy = gate._strict_json(state["S02"])["submission_items"][0]
    payload = legacy["review_record_payload"]
    assert payload["review_unit_type"] == "sample_warhead_atom_set_and_attachment_boundary"
    for field in (
        "reaction_family_identity_explicitly_attested",
        "warhead_rule_identity_explicitly_attested",
        "warhead_rule_full_semantics_explicitly_attested",
        "approved_structural_pattern_attested",
    ):
        assert field not in payload


def test_review_transport_lineage_closes_direct_and_transitive_sha_links() -> None:
    state = gate._read_state_evidence(REPO_ROOT)
    gate._validate_review_transport_lineage_v1(state)
    records = {evidence_id: gate._strict_json(state[evidence_id])
               for evidence_id in ("S01", "S02", "S03", "S04", "S05", "S06")}
    assert records["S03"]["source_submission_bundle_sha256"] == gate._sha256(state["S02"])
    assert records["S04"]["source_ingestion_execution_bundle_filesystem_sha256"] == gate._sha256(state["S03"])
    assert records["S05"]["source_multi_boundary_submission_bundle_filesystem_sha256"] == gate._sha256(state["S04"])
    assert records["S06"]["source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"] == gate._sha256(state["S05"])
    assert records["S01"]["source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"] == gate._sha256(state["S05"])
    assert records["S01"]["source_multi_boundary_authority_bundle_filesystem_sha256"] == gate._sha256(state["S06"])


def _assert_review_lineage_mutation_fails(
    case_id: str, evidence_id: str, source_field: str, digest_field: str,
) -> None:
    state = gate._read_state_evidence(REPO_ROOT)
    gate._validate_review_transport_lineage_v1(state)
    original = state[evidence_id]
    mutated = copy.deepcopy(state)
    gate._apply_failure_mutation_v1(case_id, mutated)
    assert mutated[evidence_id] != original
    assert type(mutated[evidence_id]) is bytes
    record = gate._strict_json(mutated[evidence_id])
    assert record[source_field] == "a" * 64
    gate._validate_embedded_record_digest_v1(record, digest_field)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._validate_review_transport_lineage_v1(mutated)


def test_legacy_submission_ingestion_transport_mismatch() -> None:
    _assert_review_lineage_mutation_fails(
        "X39", "S03", "source_submission_bundle_sha256",
        "ingestion_execution_bundle_sha256",
    )


def test_multi_submission_ingestion_transport_mismatch() -> None:
    _assert_review_lineage_mutation_fails(
        "X40", "S05",
        "source_multi_boundary_submission_bundle_filesystem_sha256",
        "multi_boundary_ingestion_execution_bundle_sha256",
    )


def test_multi_ingestion_authority_transport_mismatch() -> None:
    _assert_review_lineage_mutation_fails(
        "X41", "S06",
        "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256",
        "multi_boundary_authority_bundle_sha256",
    )


def test_readiness_materialization_and_training_boundaries_remain_closed(
    response: dict[str, object],
) -> None:
    assert response["ready_for_current11_role_annotation_proposal_generation"] is False
    assert response["ready_for_current11_minimal_seed_proposal_generation"] is False
    for field in gate._SAFETY_FIELDS:
        assert response[field] is False


@pytest.mark.parametrize(
    "case_id", [item[0] for item in gate._FAILURE_SPECS],
    ids=[item[0] for item in gate._FAILURE_SPECS],
)
def test_failure_matrix_case_fails_closed(
    case_id: str, response: dict[str, object],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    matrix, registry, facts = derived
    target = next(item[3] for item in gate._FAILURE_SPECS if item[0] == case_id)
    if target == "binding_state":
        baseline: object = gate._build_failure_state_v1(matrix, registry, facts)
        validator = gate._validate_binding_state_v1
    elif target == "lifecycle":
        baseline = gate._synthetic_lifecycle_facts_v1("binding_committed_unpushed")
        validator = gate._derive_binding_lifecycle_v1
    elif target == "review_lineage":
        baseline = gate._read_state_evidence(REPO_ROOT)
        validator = gate._validate_review_transport_lineage_v1
    else:
        baseline = copy.deepcopy(response)
        validator = lambda value: gate._validate_response_v1(
            value, matrix, registry,
            expected_lifecycle=_expected_lifecycle(response),
        )
    validator(baseline)
    before = copy.deepcopy(baseline)
    mutated = copy.deepcopy(baseline)
    gate._apply_failure_mutation_v1(case_id, mutated)
    assert mutated != before
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        validator(mutated)


def test_response_has_exact_scalar_container_and_record_types(
    response: dict[str, object],
) -> None:
    assert all(type(response[field]) is int for field in gate._RESPONSE_INT_FIELDS)
    assert all(type(response[field]) is bool for field in gate._RESPONSE_BOOL_FIELDS)
    assert all(type(response[field]) is str for field in gate._RESPONSE_STRING_FIELDS)
    assert all(type(response[field]) is tuple for field in gate._RESPONSE_TUPLE_FIELDS)
    assert response["binding_commit"] is None or type(response["binding_commit"]) is str
    for field in (
        "source_records", "current11_family_rule_authority_binding_matrix",
        "family_and_warhead_rule_authority_registry",
    ):
        assert all(type(record) is dict for record in response[field])


_ZERO_COUNT_FIELDS = (
    "reaction_family_identity_explicitly_attested_count",
    "warhead_rule_identity_explicitly_attested_count",
    "warhead_rule_full_semantics_explicitly_attested_count",
    "approved_structural_pattern_attested_count",
    "reaction_family_authority_bound_count",
    "approved_warhead_rule_authority_bound_count",
)


@pytest.mark.parametrize("field", _ZERO_COUNT_FIELDS)
def test_zero_count_fields_reject_bool_with_recomputed_digest(
    field: str, response: dict[str, object],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    matrix, registry, _facts = derived
    external_witness = copy.deepcopy(_expected_lifecycle(response))
    before = gate._canonical_json_bytes(response)
    mutated = copy.deepcopy(response)
    mutated[field] = False
    assert gate._canonical_json_bytes(mutated) != before
    gate._rehash_response_v1(mutated)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._validate_response_v1(
            mutated, matrix, registry, expected_lifecycle=external_witness,
        )


def test_positive_count_rejects_bool_with_recomputed_digest(
    response: dict[str, object],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    matrix, registry, _facts = derived
    external_witness = copy.deepcopy(_expected_lifecycle(response))
    before = gate._canonical_json_bytes(response)
    mutated = copy.deepcopy(response)
    mutated["current11_sample_count"] = True
    assert gate._canonical_json_bytes(mutated) != before
    gate._rehash_response_v1(mutated)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._validate_response_v1(
            mutated, matrix, registry, expected_lifecycle=external_witness,
        )


_CRITICAL_FIELDS = (
    "candidate_paths", "source_records", "authority_status_vocabulary",
    "current11_family_rule_authority_binding_matrix",
    "family_and_warhead_rule_authority_registry", "current11_sample_count",
    "boundary_review_completed_count", "reaction_family_authority_bound_count",
    "approved_warhead_rule_authority_bound_count", "binding_conclusion",
    "missing_authority_fields", "recommended_next_increment",
)


@pytest.mark.parametrize("field", _CRITICAL_FIELDS)
def test_critical_response_tampering_fails_with_recomputed_digest(
    field: str, response: dict[str, object],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    matrix, registry, _facts = derived
    mutated = copy.deepcopy(response)
    if field == "candidate_paths":
        mutated[field] = mutated[field][:-1]
    elif field == "source_records":
        mutated[field] = mutated[field][:-1]
    elif field == "authority_status_vocabulary":
        mutated[field] = ("authoritative_resolved",)
    elif field == "current11_family_rule_authority_binding_matrix":
        rows = list(mutated[field])
        rows[0] = dict(rows[0], verified="false")
        mutated[field] = tuple(rows)
    elif field == "family_and_warhead_rule_authority_registry":
        rows = list(mutated[field])
        rows[0] = dict(rows[0], approval_status="authoritative_resolved")
        mutated[field] = tuple(rows)
    elif field in {
        "current11_sample_count", "boundary_review_completed_count",
        "reaction_family_authority_bound_count",
        "approved_warhead_rule_authority_bound_count",
    }:
        mutated[field] = int(mutated[field]) + 1
    elif field == "binding_conclusion":
        mutated[field] = "authoritative"
    elif field == "missing_authority_fields":
        mutated[field] = ()
    else:
        mutated[field] = "wrong"
    gate._rehash_response_v1(mutated)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._validate_response_v1(
            mutated, matrix, registry,
            expected_lifecycle=_expected_lifecycle(response),
        )


@pytest.mark.parametrize("profile", gate._LIFECYCLE_PROFILES)
def test_lifecycle_profiles_are_commit_survivable(profile: str) -> None:
    facts = gate._synthetic_lifecycle_facts_v1(profile)
    lifecycle = gate._derive_binding_lifecycle_v1(facts)
    assert lifecycle["binding_lifecycle_profile"] == profile
    witness = gate._expected_response_lifecycle(
        origin=facts["origin"], ahead=facts["ahead"], behind=facts["behind"],
        lifecycle=lifecycle,
    )
    gate._validate_response_lifecycle_v1(witness)


def test_lifecycle_external_witness_contract_is_static_exact8() -> None:
    assert gate._RESPONSE_LIFECYCLE_FIELDS == (
        "origin_main", "ahead", "behind", "binding_lifecycle_profile",
        "binding_commit", "binding_committed", "binding_published",
        "ready_for_binding_commit_review",
    )
    for profile in gate._LIFECYCLE_PROFILES:
        facts = gate._synthetic_lifecycle_facts_v1(profile)
        lifecycle = gate._derive_binding_lifecycle_v1(facts)
        witness = gate._expected_response_lifecycle(
            origin=facts["origin"], ahead=facts["ahead"], behind=facts["behind"],
            lifecycle=lifecycle,
        )
        assert tuple(witness) == gate._RESPONSE_LIFECYCLE_FIELDS
        assert type(witness["origin_main"]) is str
        assert type(witness["ahead"]) is type(witness["behind"]) is int
        assert type(witness["binding_lifecycle_profile"]) is str
        assert witness["binding_commit"] is None or type(witness["binding_commit"]) is str
        assert all(type(witness[field]) is bool for field in (
            "binding_committed", "binding_published",
            "ready_for_binding_commit_review",
        ))


def test_live_tree_binding_lifecycle_matches_repository_state(
    response: dict[str, object],
) -> None:
    head = _git_text("rev-parse", "HEAD").strip()
    origin = _git_text("rev-parse", "refs/remotes/origin/main").strip()
    ahead, behind = map(int, _git_text(
        "rev-list", "--left-right", "--count",
        "HEAD...refs/remotes/origin/main",
    ).split())
    tracked = tuple(sorted(_git_text("diff", "--name-only").splitlines()))
    staged = tuple(sorted(_git_text("diff", "--cached", "--name-only").splitlines()))
    untracked = tuple(sorted(_git_text(
        "ls-files", "--others", "--exclude-standard",
    ).splitlines()))
    porcelain = tuple(_git_text(
        "status", "--porcelain=v1", "--untracked-files=all",
    ).splitlines())
    assert (response["origin_main"], response["ahead"], response["behind"]) == (
        origin, ahead, behind,
    )
    profile = response["binding_lifecycle_profile"]
    if profile == "binding_precommit_candidate":
        assert head == origin == gate._BASE
        assert (ahead, behind) == (0, 0)
        assert tracked == staged == ()
        assert untracked == gate._CANDIDATE_PATHS
        assert porcelain == tuple(f"?? {path}" for path in gate._CANDIDATE_PATHS)
        for path in gate._CANDIDATE_PATHS:
            metadata = (REPO_ROOT / path).lstat()
            assert stat.S_ISREG(metadata.st_mode)
            assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert response["binding_commit"] is None
        assert response["binding_committed"] is False
        assert response["binding_published"] is False
        assert response["ready_for_binding_commit_review"] is True
    elif profile == "binding_committed_unpushed":
        commit = response["binding_commit"]
        assert type(commit) is str
        assert head == commit and origin == gate._BASE
        assert (ahead, behind) == (1, 0)
        assert tracked == staged == untracked == porcelain == ()
        assert response["binding_committed"] is True
        assert response["binding_published"] is False
        assert response["ready_for_binding_commit_review"] is False
        _assert_formal_commit_identity(commit)
    elif profile == "binding_published_successor":
        commit = response["binding_commit"]
        assert type(commit) is str and commit != gate._BASE
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, head],
            cwd=REPO_ROOT, check=False, capture_output=True,
        ).returncode == 0
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, origin],
            cwd=REPO_ROOT, check=False, capture_output=True,
        ).returncode == 0
        assert not set(gate._CANDIDATE_PATHS).intersection(tracked, staged, untracked)
        assert response["binding_committed"] is True
        assert response["binding_published"] is True
        assert response["ready_for_binding_commit_review"] is False
        _assert_formal_commit_identity(commit)
    else:
        pytest.fail(f"unknown binding lifecycle profile: {profile!r}")


def test_precommit_origin_witness_substitution_fails_closed(
    response: dict[str, object],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    matrix, registry, _facts = derived
    baseline, external_witness = _synthetic_response_for_profile(
        response, "binding_precommit_candidate", matrix, registry,
    )
    mutated = copy.deepcopy(baseline)
    mutated["origin_main"] = "a" * 40
    gate._rehash_response_v1(mutated)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._validate_response_v1(
            mutated, matrix, registry,
            expected_lifecycle=external_witness,
        )


@pytest.mark.parametrize(
    ("profile", "field", "replacement"),
    (
        ("binding_committed_unpushed", "binding_commit", "a" * 40),
        ("binding_published_successor", "binding_commit", "a" * 40),
        ("binding_published_successor", "origin_main", "c" * 40),
        ("binding_published_successor", "ahead", 4),
        ("binding_published_successor", "behind", 5),
    ),
)
def test_valid_looking_committed_and_published_witness_substitution_fails_closed(
    profile: str, field: str, replacement: object,
    response: dict[str, object],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    matrix, registry, _facts = derived
    baseline, external_witness = _synthetic_response_for_profile(
        response, profile, matrix, registry,
    )
    mutated = copy.deepcopy(baseline)
    mutated[field] = replacement
    assert mutated[field] != baseline[field]
    gate._rehash_response_v1(mutated)
    substituted_witness = _expected_lifecycle(mutated)
    gate._validate_response_v1(
        mutated, matrix, registry, expected_lifecycle=substituted_witness,
    )
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._validate_response_v1(
            mutated, matrix, registry, expected_lifecycle=external_witness,
        )


@pytest.mark.parametrize(
    "profile", ("binding_committed_unpushed", "binding_published_successor"),
)
def test_committed_and_published_binding_commit_cannot_equal_base(
    profile: str, response: dict[str, object],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    matrix, registry, _facts = derived
    baseline, external_witness = _synthetic_response_for_profile(
        response, profile, matrix, registry,
    )
    mutated = copy.deepcopy(baseline)
    mutated["binding_commit"] = gate._BASE
    gate._rehash_response_v1(mutated)
    with pytest.raises(ValueError, match=f"^{gate._ERROR}$"):
        gate._validate_response_v1(
            mutated, matrix, registry, expected_lifecycle=external_witness,
        )


@pytest.mark.parametrize("profile", gate._LIFECYCLE_PROFILES)
def test_checker_supports_exact3_profiles(
    profile: str, response: dict[str, object], monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    derived: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]],
) -> None:
    path = REPO_ROOT / "scripts/check_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1.py"
    spec = importlib.util.spec_from_file_location("binding_checker_under_test", path)
    assert spec and spec.loader
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    matrix, registry, _facts = derived
    projected, witness = _synthetic_response_for_profile(
        response, profile, matrix, registry,
    )
    gate._validate_response_v1(
        projected, matrix, registry, expected_lifecycle=witness,
    )
    monkeypatch.setattr(
        checker,
        "evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1",
        lambda *, repo_root: copy.deepcopy(projected),
    )
    assert checker.main() == 0
    assert capsys.readouterr().err == ""


def test_failure_matrix_binds_every_case_to_real_parameterized_node() -> None:
    rows = gate._strict_csv((REPO_ROOT / gate._FAILURE_PATH).read_bytes(), gate._FAILURE_COLUMNS)
    assert [row["case_id"] for row in rows] == [f"X{number:02d}" for number in range(1, 42)]
    assert len({row["mutation_signature"] for row in rows}) == 41
    assert {row["validator_target"] for row in rows} == {
        "binding_state", "response", "lifecycle", "review_lineage",
    }
    for row in rows:
        assert row["test_node_id"].endswith(f"[{row['case_id']}]")
        assert row["expected_error"] == gate._ERROR
        assert row["fails_closed"] == row["verified"] == "true"


def test_state_source_commit_semantics_preserve_direct_producers() -> None:
    assert gate._SOURCE_COMMIT_SEMANTICS == (
        "state source_commit is the final transitive binder; direct producer "
        "lineage remains explicit in lineage_note"
    )
    records = {record["evidence_id"]: record for record in gate._source_records()}
    for evidence_id, direct_commit in gate._STATE_DIRECT_PRODUCER_COMMITS.items():
        record = records[evidence_id]
        assert record["source_commit"] == gate._TRANSITIVE_STATE_BINDER_COMMIT
        assert "transitively bound through unified effective authority view" in record["lineage_note"]
        assert f"direct_producer_commit={direct_commit}" in record["lineage_note"]


def test_manifest_hashes_direct_artifact_bytes() -> None:
    manifest = gate._strict_json((REPO_ROOT / gate._MANIFEST_PATH).read_bytes())
    for path in (gate._SOURCE_PATH, gate._MATRIX_PATH, gate._REGISTRY_PATH, gate._FAILURE_PATH):
        payload = (REPO_ROOT / path).read_bytes()
        assert manifest["evidence_sha256"][Path(path).name] == hashlib.sha256(payload).hexdigest()
    assert Path(gate._MANIFEST_PATH).name not in manifest["evidence_sha256"]


def test_import_is_silent_and_does_not_import_torch_or_rdkit() -> None:
    code = (
        "import sys;"
        "import covalent_ext.covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1 as m;"
        "assert 'torch' not in sys.modules;"
        "assert 'rdkit' not in sys.modules;"
        "assert len(m.__all__)==1"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=REPO_ROOT,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(SRC)},
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_module_has_exactly_one_public_api() -> None:
    assert gate.__all__ == (
        "evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1",
    )
    assert not any(name in {"torch", "rdkit"} for name in sys.modules)


def test_response_unsigned_and_full_canonical_sha_are_well_formed(
    response: dict[str, object],
) -> None:
    unsigned = {
        field: response[field] for field in gate._RESPONSE_FIELDS
        if field != "response_unsigned_canonical_json_sha256"
    }
    payload = gate._canonical_json_bytes(unsigned)
    assert len(payload) == response["response_unsigned_canonical_json_byte_count"]
    assert hashlib.sha256(payload).hexdigest() == response["response_unsigned_canonical_json_sha256"]
    full_sha = hashlib.sha256(gate._canonical_json_bytes(response)).hexdigest()
    assert len(full_sha) == 64
