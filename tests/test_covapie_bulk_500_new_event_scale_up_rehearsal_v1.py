from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import urllib.request

import pytest

from covalent_ext import covapie_bulk_500_new_event_scale_up_rehearsal_v1 as rehearsal


ROOT = Path(__file__).resolve().parents[1]


def _synthetic_repository_observation(**overrides: object) -> dict[str, object]:
    observation: dict[str, object] = {
        "branch": "main",
        "runtime_head": rehearsal.PUBLISHED_BASELINE_COMMIT_ANCESTOR,
        "runtime_origin_main": rehearsal.PUBLISHED_BASELINE_COMMIT_ANCESTOR,
        "ahead": 0,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin_main": True,
        "baseline_subject": rehearsal.PUBLISHED_BASELINE_SUBJECT,
        "modified_tracked": [],
        "staged": [],
        "untracked": sorted(rehearsal.AUTHORIZED_REHEARSAL_PATHS),
    }
    observation.update(overrides)
    return observation


@pytest.fixture(scope="module")
def inputs() -> dict[str, object]:
    return rehearsal._load_inputs_v1(ROOT)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return rehearsal.build_artifacts_v1(repo_root=ROOT)


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, object]:
    return {
        "manifest": json.loads(artifacts[rehearsal.MANIFEST]),
        "summary": json.loads(artifacts[rehearsal.SUMMARY]),
        "requirements": json.loads(artifacts[rehearsal.ACQUISITION]),
        "rows": list(
            csv.DictReader(io.StringIO(artifacts[rehearsal.COHORT].decode("utf-8")))
        ),
    }


def test_exact_output_scope_and_schema(artifacts: dict[str, bytes]) -> None:
    assert tuple(artifacts) == rehearsal.OUTPUT_FILENAMES
    assert set(artifacts) == {
        "covapie_bulk_500_scaleup_rehearsal_manifest_v1.json",
        "covapie_bulk_500_new_event_cohort_v1.csv",
        "covapie_bulk_500_acquisition_requirements_v1.json",
        "covapie_bulk_500_scaleup_rehearsal_summary_v1.json",
    }
    assert json.loads(artifacts[rehearsal.MANIFEST])["schema_version"] == (
        rehearsal.SCHEMA_VERSION
    )


def test_frozen_bulk_inputs_and_historical_population_are_sha_bound(
    inputs: dict[str, object],
) -> None:
    assert len(inputs["events"]) == 2387
    assert len(inputs["known_event_ids"]) == 27
    assert len(inputs["new_event_ids"]) == 2360
    bindings = inputs["bindings"]
    assert bindings["frozen_bulk_source"]["sha256"] == (
        rehearsal.FROZEN_BULK_SOURCE_SHA256
    )
    assert {
        item["path"]: item["sha256"]
        for item in bindings["historical_bulk_inputs"]
    } == {
        path.as_posix(): digest
        for path, digest in rehearsal.PILOT_INPUT_SHA256.items()
    }


def test_all_historical_caps_are_verified_from_frozen_source() -> None:
    assert {
        name: getattr(rehearsal.frozen_bulk, name)
        for name in rehearsal.EXPECTED_PILOT_CONSTANTS
    } == rehearsal.EXPECTED_PILOT_CONSTANTS
    rehearsal._verify_historical_constants_v1()


def test_historical_selection_replays_direct_processed_field_exactly(
    inputs: dict[str, object],
) -> None:
    frozen_ids = [
        item["canonical_event_id"] for item in inputs["frozen_selection"]
    ]
    direct_ids = {
        event_id
        for event_id, outcome in inputs["outcome_by_id"].items()
        if outcome["stage_statuses"][rehearsal.frozen_bulk.BULK_STAGES[4]]
        != "NOT_SELECTED_BOUNDED_CAP"
    }
    assert len(frozen_ids) == 277
    assert len(set(frozen_ids) - inputs["known_event_ids"]) == 250
    assert set(frozen_ids) == direct_ids
    assert len({item["pdb_id"] for item in inputs["frozen_selection"]}) == 175


def test_historical_selection_is_priority_passes_not_sorted_ids_slice(
    inputs: dict[str, object],
) -> None:
    historical_ids = [
        item["canonical_event_id"] for item in inputs["historical_new"]
    ]
    sorted_new_ids = sorted(inputs["new_event_ids"])[:250]
    assert historical_ids != sorted_new_ids
    assert all(
        inputs["selection_pass"][event_id] == "MULTI_SOURCE_PROVENANCE"
        for event_id in historical_ids
    )
    assert [item["order"] for item in rehearsal.SELECTION_PASS_DESCRIPTIONS] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_cumulative_500_is_unique_new_universe_subset_and_known_controls_separate(
    inputs: dict[str, object],
) -> None:
    cohort_ids = [item["canonical_event_id"] for item in inputs["cohort"]]
    assert len(cohort_ids) == len(set(cohort_ids)) == 500
    assert set(cohort_ids).issubset(inputs["new_event_ids"])
    assert set(cohort_ids).isdisjoint(inputs["known_event_ids"])
    assert len(inputs["new_event_ids"] - set(cohort_ids)) == 1860


def test_historical_250_is_exact_ordered_prefix_of_500(
    inputs: dict[str, object], parsed: dict[str, object]
) -> None:
    historical_ids = [
        item["canonical_event_id"] for item in inputs["historical_new"]
    ]
    cohort_ids = [item["canonical_event_id"] for item in inputs["cohort"]]
    assert cohort_ids[:250] == historical_ids
    proof = parsed["manifest"]["prefix_parity_proof"]
    assert proof["historical_250_exact_prefix_of_500"] is True
    assert proof["historical_250_set_equal"] is True
    assert proof["historical_250_order_equal"] is True
    assert proof["historical_250_ordered_event_ids_sha256"] == (
        proof["derived_500_prefix_ordered_event_ids_sha256"]
    )


def test_old_unique_pdb_cap_is_real_configurable_scale_requirement(
    inputs: dict[str, object], parsed: dict[str, object]
) -> None:
    old_cap = rehearsal._apply_historical_caps_v1(
        inputs["priority_order"],
        known_event_ids=inputs["known_event_ids"],
        target_new_event_count=500,
        unique_pdb_cap=250,
    )
    old_cap_new = [
        item
        for item in old_cap
        if item["canonical_event_id"] in inputs["new_event_ids"]
    ]
    assert len(old_cap_new) == 402
    execution = parsed["summary"]["execution_configuration_requirements"]
    assert execution["historical_250_pdb_cap_is_insufficient_for_500"] is True
    assert execution["required_unique_pdb_capacity_for_500_new_plus_27_controls"] == 311


def test_event_inventory_has_exact_identity_and_scientific_blank_boundary(
    parsed: dict[str, object],
) -> None:
    rows = parsed["rows"]
    assert len(rows) == 500
    assert list(rows[0]) == list(rehearsal.EVENT_HEADER)
    assert [int(item["scaleup_rank"]) for item in rows] == list(range(1, 501))
    required_identity_fields = (
        "canonical_event_id",
        "pdb_id",
        "protein_label_asym_id",
        "protein_residue_name",
        "protein_residue_number",
        "protein_reactive_atom",
        "ligand_component_id",
        "ligand_instance",
        "ligand_reactive_atom",
        "source_datasets_json",
        "source_provenance_identities_json",
    )
    assert all(all(row[field] for field in required_identity_fields) for row in rows)
    assert all(row["historical_terminal_route"] for row in rows[:250])
    assert all(not row["historical_terminal_route"] for row in rows[250:])
    assert all(row["structure_execution_status"] == "NOT_YET_EXECUTED" for row in rows[250:])
    assert all(
        row["task_domain_rule_evaluation_status"] == rehearsal.INCREMENTAL_RULE_STATUS
        for row in rows[250:]
    )


def test_historical_250_outcomes_are_exact_and_incremental_not_mixed(
    parsed: dict[str, object],
) -> None:
    outcome = parsed["summary"]["historical_pilot_outcomes_for_250_new_only"]
    assert outcome["exact_outcome_coverage_count"] == 250
    assert outcome["structural_model_eligible_count"] == 218
    assert outcome[
        "structural_evidence_incomplete_but_selected_for_processing_count"
    ] == 32
    assert outcome["leakage_existing_group_conflict_count"] == 88
    assert outcome["quarantine_representation_gap_count"] == 7
    assert outcome["terminal_route_counts"] == {
        "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY": 123,
        "LEAKAGE_EXISTING_GROUP_CONFLICT": 88,
        "QUARANTINE_REPRESENTATION_GAP": 7,
        "STRUCTURAL_EVIDENCE_INCOMPLETE": 32,
    }


def test_pdb_acquisition_requirements_are_exact_memberships(
    parsed: dict[str, object],
) -> None:
    pdb = parsed["requirements"]["pdb_requirements"]
    assert pdb["cumulative_500_unique_pdb_count"] == 290
    assert pdb["historical_250_unique_pdb_count"] == 154
    assert pdb["incremental_250_unique_pdb_count"] == 136
    assert pdb["incremental_new_unique_pdb_count"] == 136
    assert len(pdb["requirements"]) == 290
    assert sum(item["event_count"] for item in pdb["requirements"]) == 500
    assert pdb["known_control_unique_pdb_count"] == 21
    assert pdb["planning_universe_unique_pdb_count_including_controls"] == 311


def test_ccd_acquisition_requirements_and_committed_resolution_are_exact(
    parsed: dict[str, object],
) -> None:
    ccd = parsed["requirements"]["ccd_requirements"]
    assert ccd["cumulative_500_unique_ccd_count"] == 225
    assert ccd["historical_250_unique_ccd_count"] == 123
    assert ccd["incremental_250_unique_ccd_count"] == 114
    assert ccd["incremental_new_ccd_count"] == 102
    assert len(ccd["requirements"]) == 225
    assert sum(item["event_count"] for item in ccd["requirements"]) == 500
    assert sum(item["committed_pilot_resolved_payload"] for item in ccd["requirements"]) == 123
    assert ccd["known_control_unique_ccd_count"] == 15


def test_acquisition_artifact_contains_identities_not_mutable_cache_state(
    artifacts: dict[str, bytes], parsed: dict[str, object]
) -> None:
    requirements = parsed["requirements"]
    assert requirements["execution_not_performed"] is True
    assert requirements["network_performed"] is False
    assert requirements["downloaded_bytes"] == 0
    payload = artifacts[rehearsal.ACQUISITION]
    for forbidden in (
        b"current_cache_available",
        b"current_required_pdb_cache_hits",
        b"current_required_ccd_cache_hits",
        b"cache_manifest_v1.json",
    ):
        assert forbidden not in payload


def test_all_15_bulk_stages_have_real_readiness_classification(
    parsed: dict[str, object],
) -> None:
    stages = parsed["manifest"]["processing_stage_readiness"]
    assert [item["stage_name"] for item in stages] == list(
        rehearsal.frozen_bulk.BULK_STAGES
    )
    by_name = {item["stage_name"]: item for item in stages}
    assert by_name["BULK_05_STRUCTURE_ACQUISITION"]["classification"] == (
        "READY_WITH_CONFIGURABLE_CAP"
    )
    assert by_name["BULK_05_STRUCTURE_ACQUISITION"][
        "modification_required_before_500_execution"
    ] is True
    assert by_name["BULK_12_LEAKAGE_AND_SPLIT_PREDICTION"][
        "obvious_o_n_squared_or_high_memory_scale_risk"
    ] is True
    assert by_name["BULK_03_SOURCE_ADAPTER_NORMALIZATION"][
        "implementation_symbols"
    ] == [
        "adapters.normalize_covpdb_ligand_record_v1",
        "adapters.normalize_covbinderinpdb_record_v1",
        "adapters.normalize_rcsb_connection_record_v1",
    ]
    assert by_name["BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"][
        "implementation_symbols"
    ][1] == "feature_owner.project_type_symbols_to_checkpoint_heavy_v1"
    assert not any(item["classification"] == "NEEDS_MINIMAL_SCALE_FIX" for item in stages)


def test_two_rule_routing_is_bound_as_baseline_not_prediction(
    parsed: dict[str, object],
) -> None:
    routing = parsed["summary"]["two_rule_live_routing_baseline"]
    assert routing["integrated_rule_ids"] == [
        "NEG_V1_TS_DUMP_CATALYTIC_ADDUCT_EXACT",
        "NEG_V2_DTT_CRYSTALLIZATION_REDUCING_ADDUCT_EXACT",
    ]
    assert (routing["candidate_events"], routing["candidate_units"]) == (123, 36)
    assert (
        routing["effective_auto_negative_events"],
        routing["effective_auto_negative_units"],
    ) == (32, 2)
    assert (
        routing["human_review_required_units"],
        routing["human_review_required_events"],
    ) == (24, 56)
    assert routing["baseline_is_not_prediction_for_incremental_250"] is True
    assert parsed["summary"]["incremental_tranche_scientific_status"][
        "auto_negative_rate_extrapolated_from_current_123"
    ] is False


def test_network_and_all_acquisition_paths_can_be_monkeypatched_to_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("NETWORK_OR_ACQUISITION_CALLED")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(rehearsal.frozen_bulk, "urlopen", forbidden)
    monkeypatch.setattr(rehearsal.frozen_bulk.BulkCacheV1, "fetch", forbidden)
    for name in (
        "discover_covpdb_v1",
        "discover_covbinder_v1",
        "discover_rcsb_direct_v1",
        "discover_rcsb_specialist_seeded_v1",
        "_acquire_structures_v1",
        "acquire_ccd_components_v1",
    ):
        monkeypatch.setattr(rehearsal.frozen_bulk, name, forbidden)
    built = rehearsal.build_artifacts_v1(repo_root=ROOT)
    assert json.loads(built[rehearsal.SUMMARY])["network_performed"] is False


def test_bound_input_sha_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    path = next(iter(rehearsal.PILOT_INPUT_SHA256))
    monkeypatch.setitem(rehearsal.PILOT_INPUT_SHA256, path, "0" * 64)
    with pytest.raises(ValueError, match="BOUND_INPUT_SHA256_MISMATCH"):
        rehearsal.build_artifacts_v1(repo_root=ROOT)


def test_cache_absence_does_not_block_deterministic_plan(
    tmp_path: Path, artifacts: dict[str, bytes]
) -> None:
    observation = rehearsal.observe_current_cache_v1(
        repo_root=ROOT,
        cache_root=tmp_path / "absent",
        acquisition_requirements=json.loads(artifacts[rehearsal.ACQUISITION]),
    )
    assert observation["current_cache_available"] is False
    assert observation["current_required_pdb_cache_hits"] is None
    assert observation["current_required_ccd_cache_misses"] is None
    assert observation["cache_modified"] is False


def _write_synthetic_cache(
    root: Path, *, relative_payloads: dict[str, bytes]
) -> None:
    entries = []
    for relative, payload in sorted(relative_payloads.items()):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entries.append(
            {
                "relative_path": relative,
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    root.mkdir(parents=True, exist_ok=True)
    (root / "cache_manifest_v1.json").write_text(
        json.dumps(
            {
                "schema_version": "covapie_bulk_cache_manifest_v1",
                "snapshot_date": "synthetic-test-only",
                "payloads": entries,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def test_synthetic_cache_drift_changes_observation_not_artifact_bytes(
    tmp_path: Path,
) -> None:
    before_artifacts = rehearsal.build_artifacts_v1(repo_root=ROOT)
    requirements = json.loads(before_artifacts[rehearsal.ACQUISITION])
    first_pdb = requirements["pdb_requirements"]["requirements"][0]["pdb_id"]
    first_ccd = requirements["ccd_requirements"]["requirements"][0]["ccd_id"]
    empty_cache = tmp_path / "empty"
    populated_cache = tmp_path / "populated"
    _write_synthetic_cache(empty_cache, relative_payloads={})
    _write_synthetic_cache(
        populated_cache,
        relative_payloads={
            f"rcsb/structures/{first_pdb}.cif.gz": b"synthetic-structure",
            f"rcsb/ccd/{first_ccd}.cif": b"synthetic-ccd",
        },
    )
    empty = rehearsal.observe_current_cache_v1(
        repo_root=ROOT,
        cache_root=empty_cache,
        acquisition_requirements=requirements,
    )
    populated = rehearsal.observe_current_cache_v1(
        repo_root=ROOT,
        cache_root=populated_cache,
        acquisition_requirements=requirements,
    )
    after_artifacts = rehearsal.build_artifacts_v1(repo_root=ROOT)
    assert empty["current_required_pdb_cache_hits"] == 0
    assert empty["current_required_ccd_cache_hits"] == 0
    assert populated["current_required_pdb_cache_hits"] == 1
    assert populated["current_required_ccd_cache_hits"] == 1
    assert before_artifacts == after_artifacts


def test_materialization_is_byte_deterministic_and_temp_root_bounded(
    tmp_path: Path, artifacts: dict[str, bytes]
) -> None:
    target = tmp_path / "rehearsal"
    summary = rehearsal.materialize_v1(repo_root=ROOT, output_root=target)
    assert summary["ready_for_controlled_500_event_execution"] is True
    assert {path.name for path in target.iterdir()} == set(rehearsal.OUTPUT_FILENAMES)
    assert {
        name: (target / name).read_bytes() for name in rehearsal.OUTPUT_FILENAMES
    } == artifacts


def test_persisted_artifacts_exclude_mutable_git_cache_and_time_state(
    artifacts: dict[str, bytes], parsed: dict[str, object]
) -> None:
    combined = b"".join(artifacts.values())
    for forbidden in (
        b'"current_head"',
        b'"origin_main"',
        b'"ahead"',
        b'"behind"',
        b'"execution_timestamp"',
        b'"current_cache_available"',
        b'"current_cache_total_bytes"',
    ):
        assert forbidden not in combined
    manifest = parsed["manifest"]
    assert rehearsal.MANIFEST not in manifest["output_sha256_excluding_manifest"]


def test_readiness_and_safety_flags_are_fail_closed_and_non_authoritative(
    parsed: dict[str, object],
) -> None:
    summary = parsed["summary"]
    assert all(summary["readiness_checks"].values())
    assert summary["execution_blockers"] == []
    assert summary["ready_for_controlled_500_event_execution"] is True
    assert summary["ready_for_gpt_review"] is True
    for field in (
        "network_performed",
        "external_cache_modified",
        "frozen_bulk_pilot_modified",
        "successor_routing_modified",
        "human_overlay_modified",
        "production_authority_created",
        "training_materialization_performed",
        "structural_processing_execution_performed",
    ):
        assert summary[field] is False
    assert summary["recommended_next_step_exactly"] == (
        "gpt_audit_500_event_scaleup_rehearsal_then_authorize_controlled_"
        "500_event_bulk_execution_v1"
    )


def test_current_synchronized_repository_state_is_accepted() -> None:
    def git(*arguments: str) -> str:
        return subprocess.run(
            ("git", *arguments),
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def baseline_is_ancestor_of(reference: str) -> bool:
        result = subprocess.run(
            (
                "git",
                "merge-base",
                "--is-ancestor",
                rehearsal.PUBLISHED_BASELINE_COMMIT_ANCESTOR,
                reference,
            ),
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert result.returncode in (0, 1)
        return result.returncode == 0

    self_path = "tests/test_covapie_bulk_500_new_event_scale_up_rehearsal_v1.py"
    modified_tracked = git("diff", "--name-only").splitlines()
    assert modified_tracked in ([], [self_path])
    staged = git("diff", "--cached", "--name-only").splitlines()
    ahead, behind = git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    observation = rehearsal.validate_task_repository_observation_v1(
        {
            "branch": git("branch", "--show-current"),
            "runtime_head": git("rev-parse", "HEAD"),
            "runtime_origin_main": git("rev-parse", "origin/main"),
            "ahead": int(ahead),
            "behind": int(behind),
            "baseline_ancestor_of_head": baseline_is_ancestor_of("HEAD"),
            "baseline_ancestor_of_origin_main": baseline_is_ancestor_of(
                "origin/main"
            ),
            "baseline_subject": git(
                "show",
                "-s",
                "--format=%s",
                rehearsal.PUBLISHED_BASELINE_COMMIT_ANCESTOR,
            ),
            # The only permitted dirty path is this test candidate itself;
            # validate the clean state that exact candidate will publish.
            "modified_tracked": [],
            "staged": staged,
            "untracked": git(
                "ls-files", "--others", "--exclude-standard"
            ).splitlines(),
        }
    )
    assert observation["branch"] == "main"
    assert observation["runtime_head"] == observation["runtime_origin_main"]
    assert observation["ahead"] == 0
    assert observation["behind"] == 0
    assert observation["baseline_ancestor_of_head"] is True
    assert observation["baseline_ancestor_of_origin_main"] is True
    assert observation["baseline_subject"] == rehearsal.PUBLISHED_BASELINE_SUBJECT
    assert observation["modified_tracked"] == []
    assert observation["staged"] == []


def test_synthetic_synchronized_descendant_repository_is_accepted() -> None:
    descendant = "d" * 40
    observation = rehearsal.validate_task_repository_observation_v1(
        _synthetic_repository_observation(
            runtime_head=descendant, runtime_origin_main=descendant
        )
    )
    assert observation["runtime_head"] == descendant
    assert observation["runtime_origin_main"] == descendant


def test_head_origin_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="HEAD_ORIGIN_MISMATCH"):
        rehearsal.validate_task_repository_observation_v1(
            _synthetic_repository_observation(runtime_origin_main="e" * 40)
        )


@pytest.mark.parametrize(
    ("ahead", "behind"),
    ((1, 0), (0, 1)),
)
def test_ahead_or_behind_repository_is_rejected(ahead: int, behind: int) -> None:
    with pytest.raises(ValueError, match="AHEAD_BEHIND_MISMATCH"):
        rehearsal.validate_task_repository_observation_v1(
            _synthetic_repository_observation(ahead=ahead, behind=behind)
        )


@pytest.mark.parametrize(
    ("field", "message"),
    (
        ("baseline_ancestor_of_head", "NOT_ANCESTOR_OF_HEAD"),
        (
            "baseline_ancestor_of_origin_main",
            "NOT_ANCESTOR_OF_ORIGIN_MAIN",
        ),
    ),
)
def test_baseline_ancestry_failures_are_rejected(field: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        rehearsal.validate_task_repository_observation_v1(
            _synthetic_repository_observation(**{field: False})
        )


def test_wrong_baseline_subject_is_rejected() -> None:
    with pytest.raises(ValueError, match="BASELINE_SUBJECT_MISMATCH"):
        rehearsal.validate_task_repository_observation_v1(
            _synthetic_repository_observation(baseline_subject="wrong subject")
        )


def test_exact_precommit_and_published_clean_profiles_are_accepted() -> None:
    assert rehearsal.classify_rehearsal_worktree_profile_v1(
        modified_tracked=[],
        staged=[],
        untracked=sorted(rehearsal.AUTHORIZED_REHEARSAL_PATHS),
    ) == rehearsal.REHEARSAL_500_PRECOMMIT_CANDIDATE
    assert rehearsal.classify_rehearsal_worktree_profile_v1(
        modified_tracked=[], staged=[], untracked=[]
    ) == rehearsal.REHEARSAL_500_PUBLISHED_CLEAN_DESCENDANT


@pytest.mark.parametrize(
    ("modified", "staged", "untracked"),
    (
        (["tracked.py"], [], []),
        ([], ["staged.py"], []),
        ([], [], ["arbitrary.txt"]),
        (
            [],
            [],
            [*sorted(rehearsal.AUTHORIZED_REHEARSAL_PATHS), "arbitrary.txt"],
        ),
    ),
)
def test_arbitrary_worktree_profiles_are_rejected(
    modified: list[str], staged: list[str], untracked: list[str]
) -> None:
    with pytest.raises(ValueError, match="WORKTREE_PROFILE_INVALID"):
        rehearsal.classify_rehearsal_worktree_profile_v1(
            modified_tracked=modified, staged=staged, untracked=untracked
        )


def test_base_and_synthetic_descendant_artifacts_are_byte_identical() -> None:
    rehearsal.validate_task_repository_observation_v1(
        _synthetic_repository_observation()
    )
    base_artifacts = rehearsal.build_artifacts_v1(repo_root=ROOT)
    descendant = "d" * 40
    rehearsal.validate_task_repository_observation_v1(
        _synthetic_repository_observation(
            runtime_head=descendant, runtime_origin_main=descendant, untracked=[]
        )
    )
    descendant_artifacts = rehearsal.build_artifacts_v1(repo_root=ROOT)
    assert base_artifacts == descendant_artifacts


def test_authoritative_resolved_feature_state_is_sha_bound(
    inputs: dict[str, object], parsed: dict[str, object]
) -> None:
    assert inputs["resolved_feature_state"] == {
        "feature_semantics_audit_completed": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
    }
    binding = inputs["bindings"]["published_feature_semantics_resolution"]
    assert binding == {
        "path": rehearsal.FEATURE_RESOLUTION_MANIFEST_RELATIVE.as_posix(),
        "byte_count": (
            ROOT / rehearsal.FEATURE_RESOLUTION_MANIFEST_RELATIVE
        ).stat().st_size,
        "sha256": rehearsal.FEATURE_RESOLUTION_MANIFEST_SHA256,
    }
    state = parsed["manifest"]["authoritative_resolved_feature_state"]
    assert all(state[field] is True for field in inputs["resolved_feature_state"])
    assert state["training_performed_or_authorized_by_rehearsal"] is False
    assert "NOT_UNFINISHED_FEATURE_SEMANTICS" in state["training_status_reason"]


def test_bulk_09_does_not_reintroduce_pending_feature_audit(
    parsed: dict[str, object], artifacts: dict[str, bytes]
) -> None:
    stages = {
        item["stage_name"]: item
        for item in parsed["manifest"]["processing_stage_readiness"]
    }
    bulk_09 = stages["BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"]
    assert bulk_09["classification"] == "READY_UNCHANGED"
    assert "already resolved" in bulk_09["audit_basis"]
    assert "feature-semantics audit remains" not in bulk_09["audit_basis"]
    assert b"unfinished feature-semantics audit" not in artifacts[rehearsal.MANIFEST]


def test_accepted_cohort_acquisition_and_summary_bytes_are_unchanged(
    artifacts: dict[str, bytes],
) -> None:
    expected = {
        rehearsal.COHORT: (
            232178,
            "0bc006f417604ea17e530e884c1148c99713224eb9726e15dc661f3e41bbbb4c",
        ),
        rehearsal.ACQUISITION: (
            219699,
            "03f8d0db72e59a6eba340fc718ed1c1e1ffcf7aebbcb96a1435c64b923851ccd",
        ),
        rehearsal.SUMMARY: (
            5051,
            "253b8829cd7437b6bb379fed0bf19acdb18fa8df9effa5f4aebe6b125134e1fa",
        ),
    }
    for name, (byte_count, digest) in expected.items():
        assert len(artifacts[name]) == byte_count
        assert hashlib.sha256(artifacts[name]).hexdigest() == digest
