from __future__ import annotations

import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import subprocess

import pytest

from covalent_ext import (
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / subject.CHECKER_RELATIVE


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return subject.load_frozen_formal_decision_v1(
        REPO_ROOT, execute_formal_validator=False
    )


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return subject.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def checker_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "covapie_2a2_ingestion_checker_for_tests", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_candidate_paths() -> tuple[str, ...]:
    return tuple(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)


def candidate_status_lines(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple("?? " + path for path in paths)


def recompute_semantic_digest(document: dict[str, object]) -> None:
    clone = copy.deepcopy(document)
    clone.pop("formal_semantic_canonical_sha256")
    document["formal_semantic_canonical_sha256"] = subject._sha(
        subject._canonical_json(clone)
    )


def validate_formal_mutation(
    bound: dict[str, object], mutation: object
) -> None:
    document = copy.deepcopy(bound["formal"])
    mutation(document)
    recompute_semantic_digest(document)
    with pytest.raises(subject.TwoA2IngestionSafetyError):
        subject._validate_formal_decision_v1(document)


def mutate_bytes(path: Path, old: bytes, new: bytes, destination: Path) -> Path:
    payload = path.read_bytes()
    assert old in payload and len(old) == len(new)
    destination.write_bytes(payload.replace(old, new, 1))
    return destination


def test_frozen_formal_exact2_sha_mode_and_validator() -> None:
    root = REPO_ROOT.parent / subject.FORMAL_ROOT
    decision = root / subject.FORMAL_DECISION_RELATIVE.name
    validator = root / subject.FORMAL_VALIDATOR_RELATIVE.name
    assert decision.stat().st_size == 26532
    assert subject._sha(decision.read_bytes()) == subject.FORMAL_BINDINGS[0][3]
    assert validator.stat().st_size == 69082
    assert subject._sha(validator.read_bytes()) == subject.FORMAL_BINDINGS[1][3]
    assert oct(decision.stat().st_mode & 0o777) == "0o664"
    assert oct(validator.stat().st_mode & 0o777) == "0o664"
    report = subject._run_formal_validator(validator)
    assert report["status"] == "PASS"
    assert report["formal_human_decision_valid"] is True


def test_semantic_digest_independent_recompute_and_strict_utc(
    bound: dict[str, object]
) -> None:
    formal = bound["formal"]
    assert formal["formal_semantic_canonical_sha256"] == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert subject._semantic_digest(formal) == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    parsed = subject._parse_utc(subject.EXPECTED_APPROVED_AT_UTC)
    assert parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == subject.EXPECTED_APPROVED_AT_UTC
    with pytest.raises(subject.TwoA2IngestionSafetyError):
        subject._parse_utc("2026-02-30T07:29:33Z")


def test_revised1_precedent_state_is_current(bound: dict[str, object]) -> None:
    precedent = bound["formal"]["published_1F8_same_context_precedent"]
    assert "2A2_independent_human_review_still_required" not in precedent
    assert precedent["2A2_independent_human_review_completed"] is True
    assert precedent["precedent_did_not_substitute_for_2A2_independent_review"] is True
    assert precedent["generic_disulfide_trapping_exclusion_rule_created"] is False


def test_exact4_identity_pairs_and_distances(bound: dict[str, object]) -> None:
    events = bound["formal"]["event_level_human_decisions"]
    assert [row["canonical_event_id"] for row in events] == list(subject.EXPECTED_EVENT_IDS)
    assert [row["scaleup_rank"] for row in events] == [507, 508, 509, 510]
    assert [row["protein_reactive_atom"] for row in events] == ["SG"] * 4
    assert [row["ligand_reactive_atom"] for row in events] == ["SD"] * 4
    assert [row["POST_distance_angstrom"] for row in events] == [
        2.022434, 2.025631, 2.020764, 2.024483,
    ]


def test_d1_d6_are_consumed_without_reinterpretation(bound: dict[str, object]) -> None:
    formal = bound["formal"]
    approval = formal["human_approval"]
    assert [
        approval["D1_task_relevance"], approval["D2_chemistry"],
        approval["D3_reactive_pair"], approval["D4_role_partition"],
        approval["D5_training_use"],
    ] == [
        "RELEVANT", "POSITIVE", "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_4", "EXCLUDE_FROM_TRAINING_ONLY",
    ]
    assert approval["D6_scientific_context"] == formal["human_approved_context"]["D6_scientific_context"]
    assert formal["human_approved_context"]["formal_D6_equals_preview_proposed_D6"] is True


def test_candidate4_strict_role_partition_and_runtime(bound: dict[str, object]) -> None:
    role = subject._role_projection(bound["formal"])
    assert role["selected_candidate_index_0based"] == 4
    assert role["machine_selected"] is False
    assert role["machine_recommended"] is False
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["warhead_role_atom_ids"] == ["SD"]
    assert role["linker_atom_ids"] == ["C1", "C15", "C16", "C17", "O18"]
    assert role["scaffold_atom_ids"] == list(subject.SCAFFOLD_ROLE)
    assert role["boundary_bonds"] == list(subject.BOUNDARY_BONDS)
    assert bound["published_runtime_result"]["valid"] is True
    assert bound["published_runtime_result"]["applicable_task_ids"] == [0, 1, 2, 3, 4]


def test_exact5_b3_and_all_five_applicability() -> None:
    contract = subject._canonical_task_contract()
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task_present"] is False
    assert contract["strict_profile_applicable_task_ids"] == [0, 1, 2, 3, 4]
    assert [row["semantic_long_name"] for row in contract["global_canonical_tasks"]] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]


def test_chemical_pre_post_seed_training_and_reusable_boundaries(
    bound: dict[str, object]
) -> None:
    formal = bound["formal"]
    assert formal["chemical_warhead_boundary"]["chemical_warhead_atom_ids"] is None
    assert formal["chemical_warhead_boundary"]["chemical_warhead_human_authoritative"] is False
    assert set(subject._geometry_boundary().values()) >= {False, True, 4}
    assert formal["minimal_seed"] == {
        "minimal_seed_atom_ids": None, "minimal_seed_authority_created": False,
    }
    training = subject._training_boundary()
    assert training["human_training_excluded"] is True
    assert training["training_use_allowed"] is False
    assert training["candidate_for_future_training_admission"] is False
    assert training["future_training_candidate_derived_by_ingestion"] is False
    assert training["training_admitted"] is False
    assert training["current_runtime_model_usable"] is False
    assert set(subject._reusable_boundary().values()) == {False}


def test_current_published_census_and_informational_deltas(
    bound: dict[str, object]
) -> None:
    current = bound["current_published_census_boundary"]
    assert [
        current["positive"], current["relevant"], current["training_INCLUDE"],
        current["training_EXCLUDE"], current["future_candidates"],
        current["pair_sample_authority"], current["role_sample_authority"],
    ] == [108, 109, 44, 64, 27, 108, 108]
    assert current["current_2A2_status"] == "CURRENTLY_UNREVIEWED"
    future = bound["future_census_informational"]
    assert future["status"] == "INFORMATIONAL_ONLY"
    assert [future[k] for k in ("positive", "relevant", "training_INCLUDE", "training_EXCLUDE", "future_candidates", "pair_sample_authority", "role_sample_authority")] == [112, 113, 44, 68, 27, 112, 112]
    assert [future[k] for k in ("strict_profile", "direct_profile", "A", "B", "B2", "B3", "C")] == [52, 60, 112, 52, 52, 112, 112]
    reconciliation = bound["reconciliation_informational"]
    assert reconciliation["reconciled_this_step"] is False
    assert reconciliation["future_after_reconciliation"] == {
        "completed_positive_event_count": 95, "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24, "completed_negative_unit_count": 4,
        "completed_total_event_count": 119, "completed_total_unit_count": 17,
        "unreviewed_event_count": 219, "unreviewed_unit_count": 114,
        "in_progress_event_count": 0, "in_progress_unit_count": 0,
        "normalized_INCLUDE": 27,
        "normalized_EXCLUDE_FROM_TRAINING_ONLY": 68,
    }


def test_snapshot_matrix_summary_manifest_closure(artifacts: dict[str, bytes]) -> None:
    assert tuple(artifacts) == subject.OUTPUT_FILENAMES
    subject.validate_completed_decision_projection_v1(artifacts, repo_root=REPO_ROOT)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert snapshot["snapshot_created_by_ingestion"] is True
    assert snapshot["snapshot_is_new_human_authority"] is False
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    assert manifest["manifest_self_sha256_recorded"] is False
    assert manifest["informational_future_values_materialized"] is False
    assert manifest["ready_for_training"] is False


def test_matrix_exact4_and_role_chemical_distinction(artifacts: dict[str, bytes]) -> None:
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode())))
    assert len(rows) == 4
    assert list(rows[0]) == list(subject.MATRIX_HEADER)
    assert [row["canonical_event_id"] for row in rows] == list(subject.EXPECTED_EVENT_IDS)
    for row in rows:
        assert row["selected_role_candidate_index_0based"] == "4"
        assert json.loads(row["warhead_atoms_json"]) == ["SD"]
        assert json.loads(row["chemical_warhead_atoms_json"]) is None
        assert row["chemical_warhead_human_authoritative"] == "false"
        assert row["formal_event_training_use_decision"] == "EXCLUDE_FROM_TRAINING_ONLY"
        assert row["human_training_excluded"] == "true"
        assert row["candidate_for_future_training_admission"] == "false"


def test_summary_all_required_local_counts_are_derived(artifacts: dict[str, bytes]) -> None:
    summary = json.loads(artifacts[subject.SUMMARY])
    expected = {
        "event_count": 4, "completed_human_positive_count": 4,
        "chemistry_positive_count": 4, "task_relevant_count": 4,
        "reactive_pair_human_authority_count": 4,
        "role_partition_human_authority_count": 4,
        "chemical_warhead_human_authority_count": 0,
        "human_training_INCLUDE_count": 0, "human_training_EXCLUDE_count": 4,
        "strict_profile_count": 4, "direct_profile_count": 0,
        "future_training_admission_candidate_count": 0,
        "future_training_candidate_derived_by_ingestion_count": 0,
        "training_admitted_count": 0, "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0, "minimal_seed_authority_count": 0,
        "PRE_topology_authority_count": 0, "PRE_geometry_authority_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
        "reaction_family_target_count": 0, "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
    }
    assert all(summary[key] == value for key, value in expected.items())
    assert summary["training_exclusion_is_chemistry_negative"] is False
    assert summary["training_exclusion_is_task_irrelevance"] is False


def test_live_outputs_and_double_temp_materialization_are_deterministic(
    artifacts: dict[str, bytes], tmp_path: Path
) -> None:
    live = {
        name: (REPO_ROOT / subject.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in subject.OUTPUT_FILENAMES
    }
    assert live == artifacts
    first = subject.materialize_artifacts_v1(REPO_ROOT, output_root=tmp_path / "first")
    second = subject.materialize_artifacts_v1(REPO_ROOT, output_root=tmp_path / "second")
    assert live == first == second
    assert all(
        (tmp_path / "first" / name).read_bytes()
        == (tmp_path / "second" / name).read_bytes()
        for name in subject.OUTPUT_FILENAMES
    )


FORMAL_MUTATIONS = (
    ("stale_precedent", lambda d: d["published_1F8_same_context_precedent"].__setitem__("2A2_independent_human_review_still_required", True)),
    ("review_completed_false", lambda d: d["published_1F8_same_context_precedent"].__setitem__("2A2_independent_human_review_completed", False)),
    ("precedent_substitute_false", lambda d: d["published_1F8_same_context_precedent"].__setitem__("precedent_did_not_substitute_for_2A2_independent_review", False)),
    ("D1", lambda d: d["human_approval"].__setitem__("D1_task_relevance", "NOT_RELEVANT")),
    ("D2", lambda d: d["human_approval"].__setitem__("D2_chemistry", "NEGATIVE")),
    ("D3", lambda d: d["human_approval"].__setitem__("D3_reactive_pair", "REVISE_PAIR")),
    ("D4", lambda d: d["human_approval"].__setitem__("D4_role_partition", "SELECT_CANDIDATE_3")),
    ("D5", lambda d: d["human_approval"].__setitem__("D5_training_use", "INCLUDE")),
    ("D6", lambda d: d["human_approval"].__setitem__("D6_scientific_context", "drift")),
    ("event_missing", lambda d: d["event_level_human_decisions"].pop()),
    ("event_extra", lambda d: d["event_level_human_decisions"].append({})),
    ("event_duplicate", lambda d: d["event_level_human_decisions"][1].__setitem__("canonical_event_id", d["event_level_human_decisions"][0]["canonical_event_id"])),
    ("rank", lambda d: d["event_level_human_decisions"][0].__setitem__("scaleup_rank", 506)),
    ("pair_SG", lambda d: d["event_level_human_decisions"][0].__setitem__("protein_reactive_atom", "CB")),
    ("pair_SD", lambda d: d["event_level_human_decisions"][0].__setitem__("ligand_reactive_atom", "C1")),
    ("candidate", lambda d: d["selected_role_partition"].__setitem__("selected_candidate_index_0based", 3)),
    ("machine_selected", lambda d: d["selected_role_partition"].__setitem__("machine_selected", True)),
    ("machine_recommended", lambda d: d["selected_role_partition"].__setitem__("machine_recommended", True)),
    ("profile", lambda d: d["selected_role_partition"].__setitem__("role_profile", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1")),
    ("W", lambda d: d["selected_role_partition"]["warhead_role_atom_ids"].append("C1")),
    ("L", lambda d: d["selected_role_partition"]["linker_atom_ids"].pop()),
    ("S", lambda d: d["selected_role_partition"]["scaffold_atom_ids"].pop()),
    ("boundary", lambda d: d["selected_role_partition"]["boundary_bonds"][0].__setitem__("bond_order", "DOUB")),
    ("B3", lambda d: d["canonical_Exact5_and_sample_applicability"].__setitem__("B3_present", False)),
    ("sixth", lambda d: d["canonical_Exact5_and_sample_applicability"].__setitem__("sixth_task_present", True)),
    ("applicability", lambda d: d["canonical_Exact5_and_sample_applicability"]["sample_applicable_task_ids"].pop()),
    ("chemical_atoms", lambda d: d["chemical_warhead_boundary"].__setitem__("chemical_warhead_atom_ids", ["SD"])),
    ("chemical_authority", lambda d: d["chemical_warhead_boundary"].__setitem__("chemical_warhead_human_authoritative", True)),
    ("PRE_topology", lambda d: d["experimental_context_and_PRE_boundary"].__setitem__("PRE_topology_authority_created", True)),
    ("PRE_geometry", lambda d: d["experimental_context_and_PRE_boundary"].__setitem__("PRE_geometry_authority_created", True)),
    ("seed", lambda d: d["minimal_seed"].__setitem__("minimal_seed_atom_ids", ["SD"])),
    ("POST_training", lambda d: d["POST_evidence_boundary"].__setitem__("POST_geometry_training_authority_created", True)),
    ("excluded_false", lambda d: d["training_use_human_decision"].__setitem__("human_training_excluded", False)),
    ("future", lambda d: d["training_use_human_decision"].__setitem__("candidate_for_future_training_admission", True)),
    ("admission", lambda d: d["training_use_human_decision"].__setitem__("formal_training_admitted", True)),
    ("runtime", lambda d: d["training_use_human_decision"].__setitem__("current_runtime_model_usable", True)),
    ("reusable", lambda d: d["reusable_authority_boundary"].__setitem__("reaction_family_authority_created", True)),
)


@pytest.mark.parametrize(("name", "mutation"), FORMAL_MUTATIONS)
def test_formal_semantic_mutations_fail_closed(
    bound: dict[str, object], name: str, mutation: object
) -> None:
    del name
    validate_formal_mutation(bound, mutation)


def test_formal_json_sha_drift_fails_closed(tmp_path: Path) -> None:
    source = REPO_ROOT.parent / subject.FORMAL_DECISION_RELATIVE
    changed = mutate_bytes(source, b'"approved": true', b'"approved": fals', tmp_path / "formal.json")
    with pytest.raises(subject.TwoA2IngestionSafetyError, match="SOURCE_SHA256_DRIFT"):
        subject.load_frozen_formal_decision_v1(
            REPO_ROOT, formal_decision_path=changed, execute_formal_validator=False
        )


def test_formal_validator_sha_drift_fails_closed(tmp_path: Path) -> None:
    source = REPO_ROOT.parent / subject.FORMAL_VALIDATOR_RELATIVE
    changed = mutate_bytes(source, b"2A2", b"2B2", tmp_path / "validator.py")
    with pytest.raises(subject.TwoA2IngestionSafetyError, match="SOURCE_SHA256_DRIFT"):
        subject.load_frozen_formal_decision_v1(
            REPO_ROOT, formal_validator_path=changed, execute_formal_validator=False
        )


def current_census_payloads() -> dict[Path, bytes]:
    return {binding[0]: (REPO_ROOT / binding[0]).read_bytes() for binding in subject.CENSUS_BINDINGS}


def test_current_census_count_drift_fails_closed() -> None:
    payloads = current_census_payloads()
    path = subject.CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_f24_v1.json"
    summary = json.loads(payloads[path])
    summary["chemistry"]["POSITIVE"]["count"] = 109
    payloads[path] = subject._json_bytes(summary)
    with pytest.raises(subject.TwoA2IngestionSafetyError):
        subject._current_census_boundary(payloads)


def test_current_census_2a2_completed_fails_closed() -> None:
    payloads = current_census_payloads()
    path = subject.CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_f24_v1.csv"
    rows = list(csv.DictReader(io.StringIO(payloads[path].decode())))
    next(row for row in rows if row["scaleup_rank"] == "507")["human_review_completed"] = "true"
    payloads[path] = subject._csv_bytes(tuple(rows[0]), rows)
    with pytest.raises(subject.TwoA2IngestionSafetyError):
        subject._current_census_boundary(payloads)


def mutate_matrix(
    artifacts: dict[str, bytes], mutation: object
) -> dict[str, bytes]:
    changed = dict(artifacts)
    rows = list(csv.DictReader(io.StringIO(changed[subject.MATRIX].decode())))
    mutation(rows)
    changed[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows)
    return changed


MATRIX_MUTATIONS = (
    ("missing", lambda rows: rows.pop()),
    ("extra", lambda rows: rows.append(copy.deepcopy(rows[-1]))),
    ("duplicate", lambda rows: rows[1].__setitem__("canonical_event_id", rows[0]["canonical_event_id"])),
    ("candidate", lambda rows: rows[0].__setitem__("selected_role_candidate_index_0based", "3")),
    ("W", lambda rows: rows[0].__setitem__("warhead_atoms_json", "[]")),
    ("chemical", lambda rows: rows[0].__setitem__("chemical_warhead_atoms_json", '["SD"]')),
    ("exclude_count", lambda rows: rows[0].__setitem__("formal_event_training_use_decision", "INCLUDE")),
    ("included", lambda rows: rows[0].__setitem__("training_use_allowed", "true")),
    ("future", lambda rows: rows[0].__setitem__("candidate_for_future_training_admission", "true")),
    ("admission", lambda rows: rows[0].__setitem__("training_admitted", "true")),
    ("runtime", lambda rows: rows[0].__setitem__("current_runtime_model_usable", "true")),
    ("PRE", lambda rows: rows[0].__setitem__("PRE_topology_authority_available", "true")),
    ("seed", lambda rows: rows[0].__setitem__("minimal_seed_authority_available", "true")),
    ("POST", lambda rows: rows[0].__setitem__("POST_geometry_training_authority_available", "true")),
)


@pytest.mark.parametrize(("name", "mutation"), MATRIX_MUTATIONS)
def test_matrix_tampering_fails_closed(
    artifacts: dict[str, bytes], name: str, mutation: object
) -> None:
    del name
    with pytest.raises(subject.TwoA2IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(
            mutate_matrix(artifacts, mutation)
        )


def test_manifest_self_sha_insertion_fails_closed(artifacts: dict[str, bytes]) -> None:
    changed = dict(artifacts)
    manifest = json.loads(changed[subject.MANIFEST])
    manifest["manifest_self_sha256"] = "0" * 64
    changed[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.TwoA2IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(changed)


def test_dynamic_metadata_fails_closed() -> None:
    with pytest.raises(subject.TwoA2IngestionSafetyError, match="DYNAMIC_METADATA_KEY"):
        subject._reject_dynamic_metadata({"generated_at": "now"})
    with pytest.raises(subject.TwoA2IngestionSafetyError, match="ABSOLUTE_OR_MACHINE_PATH"):
        subject._reject_dynamic_metadata({"path": "/tmp/drift"})


@pytest.mark.parametrize("exception", [KeyboardInterrupt(), SystemExit(7)])
def test_interrupts_and_system_exit_propagate(
    monkeypatch: pytest.MonkeyPatch, exception: BaseException
) -> None:
    def raising_run(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise exception

    monkeypatch.setattr(subprocess, "run", raising_run)
    with pytest.raises(type(exception)):
        subject._run_formal_validator(Path("validator.py"))


def test_checker_accepts_exact_two_repository_profiles(checker_module: object) -> None:
    paths = expected_candidate_paths()
    candidate = checker_module._classify_repository_profile(
        expected_paths=paths, tracked_paths=set(),
        status_lines=candidate_status_lines(paths),
        working_tree_diff_paths=(), cached_diff_paths=(),
    )
    tracked = checker_module._classify_repository_profile(
        expected_paths=paths, tracked_paths=set(paths), status_lines=(),
        working_tree_diff_paths=(), cached_diff_paths=(),
    )
    assert [candidate, tracked] == ["CANDIDATE_UNTRACKED", "TRACKED_CLEAN"]


@pytest.mark.parametrize(
    ("tracked_kind", "status_kind", "working", "cached", "error"),
    [
        ("partial", "candidate", (), (), "CANDIDATE_TRACKING_PROFILE_MIXED"),
        ("none", "extra", (), (), "CANDIDATE_UNTRACKED_STATUS_EXTRA"),
        ("all", "modified", ("x",), (), "TRACKED_WORKTREE_MODIFICATION_PRESENT"),
        ("all", "staged", (), ("x",), "STAGED_INDEX_CHANGE_PRESENT"),
        ("none", "missing", (), (), "CANDIDATE_UNTRACKED_STATUS_MISSING"),
        ("all", "unexpected", (), (), "TRACKED_CLEAN_STATUS_NOT_EMPTY"),
    ],
)
def test_checker_mixed_staged_extra_and_dirty_states_fail_closed(
    checker_module: object, tracked_kind: str, status_kind: str,
    working: tuple[str, ...], cached: tuple[str, ...], error: str,
) -> None:
    paths = expected_candidate_paths()
    tracked = {"none": set(), "partial": {paths[0]}, "all": set(paths)}[tracked_kind]
    statuses = {
        "candidate": candidate_status_lines(paths),
        "extra": (*candidate_status_lines(paths), "?? unrelated.txt"),
        "modified": (" M " + paths[0],), "staged": ("M  " + paths[0],),
        "missing": candidate_status_lines(paths[1:]),
        "unexpected": ("?? unrelated.txt",),
    }[status_kind]
    with pytest.raises(SystemExit, match=error):
        checker_module._classify_repository_profile(
            expected_paths=paths, tracked_paths=tracked, status_lines=statuses,
            working_tree_diff_paths=working, cached_diff_paths=cached,
        )
