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
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v1 as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py"
)


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return subject.load_frozen_formal_decision_v1(
        REPO_ROOT,
        execute_formal_validator=False,
    )


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return subject.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def checker_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "covapie_f24_ingestion_checker_for_tests",
        CHECKER_PATH,
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


def validate_mutation(
    bound: dict[str, object], mutation: object
) -> None:
    document = copy.deepcopy(bound["formal"])
    mutation(document)
    recompute_semantic_digest(document)
    with pytest.raises(subject.F24IngestionSafetyError):
        subject._validate_formal_decision_v1(document, bound["preparation"])


def mutate_bytes(path: Path, old: bytes, new: bytes, destination: Path) -> Path:
    payload = path.read_bytes()
    assert old in payload
    destination.write_bytes(payload.replace(old, new, 1))
    return destination


def test_frozen_exact2_bindings_and_formal_validator() -> None:
    formal_root = REPO_ROOT.parent / subject.FORMAL_ROOT
    decision = formal_root / "f24_formal_human_decision_v1.json"
    validator = formal_root / "validate_f24_formal_human_decision_v1.py"
    assert decision.stat().st_size == 26652
    assert subject._sha(decision.read_bytes()) == subject.FORMAL_BINDINGS[0][3]
    assert validator.stat().st_size == 45469
    assert subject._sha(validator.read_bytes()) == subject.FORMAL_BINDINGS[1][3]
    report = subject._run_formal_validator(validator)
    assert report["status"] == "PASS"
    assert report["formal_validator"] == "PASS"
    assert report["published_runtime_validation"] == "PASS"


def test_formal_semantic_digest_and_real_utc_parse(bound: dict[str, object]) -> None:
    formal = bound["formal"]
    assert formal["formal_semantic_canonical_sha256"] == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    assert subject._semantic_digest(formal) == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    parsed = subject._parse_utc("2026-08-29T01:36:28Z")
    assert (parsed.year, parsed.month, parsed.day) == (2026, 8, 29)
    with pytest.raises(subject.F24IngestionSafetyError):
        subject._parse_utc("2026-02-30T01:36:28Z")


def test_exact4_identity_and_post_distances(bound: dict[str, object]) -> None:
    formal = bound["formal"]
    events = formal["event_level_human_decisions"]
    assert [event["canonical_event_id"] for event in events] == list(subject.EXPECTED_EVENT_IDS)
    assert [event["scaleup_rank"] for event in events] == [593, 594, 595, 596]
    assert [event["protein_reactive_atom"] for event in events] == ["SG"] * 4
    assert [event["ligand_reactive_atom"] for event in events] == ["C8"] * 4
    assert [event["POST_distance_angstrom"] for event in events] == [
        1.833648, 1.671136, 1.893800, 1.599498,
    ]


def test_d1_d6_revised_role_and_no_machine_selection(bound: dict[str, object]) -> None:
    approval = bound["formal"]["human_approval"]
    assert approval["D1_task_relevance"] == "RELEVANT"
    assert approval["D2_chemistry"] == "POSITIVE"
    assert approval["D3_reactive_pair"] == "CONFIRM_OBSERVED_PAIR"
    assert approval["D4_role_partition"] == "REVISE_ROLE_PARTITION"
    assert approval["D5_training_use"] == "INCLUDE"
    assert approval["D6_scientific_context"] == subject.EXPECTED_D6
    assert approval["human_selected_role_candidate_index_0based"] is None


def test_chemical_core_and_role_region_remain_distinct(bound: dict[str, object]) -> None:
    formal = bound["formal"]
    chemical = formal["chemical_warhead_annotation"]["chemical_warhead_atom_ids"]
    role = formal["selected_role_partition"]["warhead_role_atom_ids"]
    distinction = formal["chemical_warhead_vs_role_region_distinction"]
    assert chemical == ["C1", "C2", "C8", "O2", "O6"]
    assert role == ["C1", "C2", "C4", "C8", "O2", "O5", "O6"]
    assert set(chemical) != set(role)
    assert not {"C4", "O5"} & set(chemical)
    assert {"C4", "O5"} <= set(role)
    assert distinction["sets_are_intentionally_distinct"] is True


def test_published_direct_runtime_and_boundary(bound: dict[str, object]) -> None:
    result = bound["published_runtime_result"]
    assert result == {
        "validator": "validate_role_profile_v1",
        "valid": True,
        "reasons": [],
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "direct_boundary_valid": True,
        "warhead_endpoint": "C2",
        "scaffold_endpoint": "C5",
        "bond_order": "SING",
    }


def test_exact5_b3_no_sixth_and_direct_applicability() -> None:
    contract = subject._canonical_task_contract()
    assert contract["global_canonical_task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task_present"] is False
    assert [row["semantic_long_name"] for row in contract["global_canonical_tasks"]] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]
    assert contract["direct_profile_applicable_task_ids"] == [0, 3, 4]


def test_seed_future_candidacy_admission_and_authority_boundaries() -> None:
    role = subject._role_projection()
    training = subject._training_boundary()
    authority = subject._authority_boundary()
    assert role["minimal_seed_authority_available"] is False
    assert role["minimal_seed_status"] == "UNRESOLVED_NOT_CREATED"
    assert training["candidate_for_future_training_admission"] is True
    assert training["future_training_candidate_derived_by_ingestion"] is True
    assert training["future_training_candidate_is_training_admission"] is False
    assert training["training_admitted"] is False
    assert training["tensor_target_created"] is False
    assert training["current_runtime_model_usable"] is False
    assert authority["human_authority_ingested"] is True
    assert authority["human_authority_created_by_ingestion"] is False
    assert authority["new_human_authority_created"] is False


def test_pre_post_and_no_reusable_authority_boundaries() -> None:
    geometry = subject._geometry_boundary()
    reusable = subject._reusable_boundary()
    assert geometry["POST_source_evidence_count"] == 4
    assert geometry["POST_geometry_training_authority_created"] is False
    assert geometry["PRE_topology_authority_available"] is False
    assert geometry["PRE_geometry_authority_available"] is False
    assert geometry["PRE_reconstruction_performed"] is False
    assert geometry["POST_to_PRE_copy_performed"] is False
    assert geometry["PRE_zero_fill_performed"] is False
    assert set(reusable.values()) == {False}


def test_current_published_census_is_unchanged(bound: dict[str, object]) -> None:
    census = bound["current_published_census_boundary"]
    assert [
        census["positive"], census["relevant"], census["training_INCLUDE"],
        census["training_EXCLUDE"], census["future_candidates"],
        census["pair_sample_authority"], census["role_sample_authority"],
    ] == [104, 105, 40, 64, 23, 104, 104]
    assert census["current_F24_status"] == "CURRENTLY_UNREVIEWED"
    assert census["next_priority_review_ligand"] == "F24"
    assert census["next_priority_review_unit"] == subject.EXPECTED_REVIEW_UNIT_ID
    assert census["global_census_updated"] is False


def test_matrix_exact4_compatibility_and_f24_semantics(artifacts: dict[str, bytes]) -> None:
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    assert len(rows) == 4
    assert list(rows[0]) == list(subject.MATRIX_HEADER)
    assert [row["canonical_event_id"] for row in rows] == list(subject.EXPECTED_EVENT_IDS)
    assert [row["selected_role_candidate_index_0based"] for row in rows] == [""] * 4
    for row in rows:
        assert row["role_partition_human_choice"] == "REVISE_ROLE_PARTITION"
        assert json.loads(row["warhead_atoms_json"]) == list(subject.WARHEAD_ROLE)
        assert json.loads(row["chemical_warhead_atoms_json"]) == list(subject.CHEMICAL_WARHEAD)
        assert json.loads(row["linker_atoms_json"]) == []
        assert json.loads(row["scaffold_atoms_json"]) == list(subject.SCAFFOLD_ROLE)
        assert row["direct_profile_applicable_task_ids_json"] == "[0,3,4]"
        assert row["minimal_seed_authority_available"] == "false"
        assert row["candidate_for_future_training_admission"] == "true"
        assert row["training_admitted"] == "false"


def test_source_local_counts_and_authority_boundary(artifacts: dict[str, bytes]) -> None:
    summary = json.loads(artifacts[subject.SUMMARY])
    expected = {
        "event_count": 4,
        "completed_human_positive_count": 4,
        "chemistry_positive_count": 4,
        "task_relevant_count": 4,
        "reactive_pair_human_authority_count": 4,
        "role_partition_human_authority_count": 4,
        "chemical_warhead_human_authority_count": 4,
        "human_training_INCLUDE_count": 4,
        "human_training_EXCLUDE_count": 0,
        "direct_profile_count": 4,
        "strict_profile_count": 0,
        "future_training_admission_candidate_count": 4,
        "future_training_candidate_derived_by_ingestion_count": 4,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "minimal_seed_authority_count": 0,
        "PRE_topology_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
    }
    assert all(summary[key] == value for key, value in expected.items())
    assert summary["global_census_update_status"] == "NOT_DONE_THIS_STEP"
    assert summary["ready_for_training"] is False


def test_exact4_outputs_manifest_closure_and_no_dynamic_metadata(
    artifacts: dict[str, bytes],
) -> None:
    assert tuple(artifacts) == subject.OUTPUT_FILENAMES
    subject.validate_completed_decision_projection_v1(artifacts, repo_root=REPO_ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    assert manifest["manifest_self_sha256_recorded"] is False
    assert manifest["expected_future_census_derivation_materialized"] is False
    assert manifest["ready_for_training"] is False
    for document_name in (subject.SNAPSHOT, subject.SUMMARY, subject.MANIFEST):
        subject._reject_dynamic_metadata(json.loads(artifacts[document_name]))


def test_live_outputs_are_exact_and_deterministic(artifacts: dict[str, bytes], tmp_path: Path) -> None:
    live = {
        name: (REPO_ROOT / subject.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in subject.OUTPUT_FILENAMES
    }
    assert live == artifacts
    first = subject.materialize_artifacts_v1(REPO_ROOT, output_root=tmp_path / "first")
    second = subject.materialize_artifacts_v1(REPO_ROOT, output_root=tmp_path / "second")
    assert live == first == second
    assert all(
        (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
        for name in subject.OUTPUT_FILENAMES
    )


@pytest.mark.parametrize(
    ("name", "mutation"),
    [
        ("D1", lambda d: d["human_approval"].__setitem__("D1_task_relevance", "NOT_RELEVANT")),
        ("D2", lambda d: d["human_approval"].__setitem__("D2_chemistry", "NEGATIVE")),
        ("D3", lambda d: d["human_approval"].__setitem__("D3_reactive_pair", "REVISE_PAIR")),
        ("D4", lambda d: d["human_approval"].__setitem__("D4_role_partition", "SELECT_CANDIDATE")),
        ("D5", lambda d: d["human_approval"].__setitem__("D5_training_use", "EXCLUDE_FROM_TRAINING_ONLY")),
        ("D6", lambda d: d["human_approval"].__setitem__("D6_scientific_context", "drift")),
        ("event_missing", lambda d: d["event_level_human_decisions"].pop()),
        ("event_extra", lambda d: d["event_level_human_decisions"].append(copy.deepcopy(d["event_level_human_decisions"][0]))),
        ("SG_drift", lambda d: d["event_level_human_decisions"][0].__setitem__("protein_reactive_atom", "S")),
        ("C8_drift", lambda d: d["event_level_human_decisions"][0].__setitem__("ligand_reactive_atom", "C1")),
        ("chemical_add_C4", lambda d: d["chemical_warhead_annotation"]["chemical_warhead_atom_ids"].append("C4")),
        ("chemical_lose_O6", lambda d: d["chemical_warhead_annotation"]["chemical_warhead_atom_ids"].remove("O6")),
        ("role_lose_C4", lambda d: d["selected_role_partition"]["warhead_role_atom_ids"].remove("C4")),
        ("role_lose_O5", lambda d: d["selected_role_partition"]["warhead_role_atom_ids"].remove("O5")),
        ("sets_equal", lambda d: d["chemical_warhead_vs_role_region_distinction"].__setitem__("warhead_role_atom_ids", list(subject.CHEMICAL_WARHEAD))),
        ("selected_candidate_8", lambda d: d["selected_role_partition"].__setitem__("selected_candidate_index_0based", 8)),
        ("machine_selected", lambda d: d["selected_role_partition"].__setitem__("machine_selected", True)),
        ("boundary", lambda d: d["selected_role_partition"]["direct_scaffold_warhead_boundary"].__setitem__("scaffold_atom_id", "C3")),
        ("STRICT", lambda d: d["selected_role_partition"].__setitem__("role_profile", "STRICT_LINKER_PRESENT_V1")),
        ("B3_absent", lambda d: d["canonical_Exact5_and_sample_applicability"].__setitem__("B3_present", False)),
        ("sixth_task", lambda d: d["canonical_Exact5_and_sample_applicability"]["tasks"].append({"task_id": 5})),
        ("all_five", lambda d: d["canonical_Exact5_and_sample_applicability"].__setitem__("sample_applicable_task_ids", [0, 1, 2, 3, 4])),
        ("minimal_seed", lambda d: d["minimal_seed"].__setitem__("minimal_seed_atom_ids", ["C5"])),
        ("training_admitted", lambda d: d["training_use_human_decision"].__setitem__("formal_training_admitted", True)),
        ("tensor", lambda d: d["training_use_human_decision"].__setitem__("tensor_target_created", True)),
        ("runtime", lambda d: d["training_use_human_decision"].__setitem__("runtime_model_usable", True)),
        ("PRE", lambda d: d["geometry_boundary"].__setitem__("PRE_topology_authority_created", True)),
        ("reusable_family", lambda d: d["reusable_authority_boundary"].__setitem__("reaction_family_authority_created", True)),
    ],
)
def test_formal_semantic_mutations_fail_closed(
    bound: dict[str, object], name: str, mutation: object
) -> None:
    del name
    validate_mutation(bound, mutation)


def test_formal_json_sha_drift_fails_closed(tmp_path: Path) -> None:
    source = REPO_ROOT.parent / subject.FORMAL_DECISION_RELATIVE
    changed = mutate_bytes(source, b'"approved": true', b'"approved":false', tmp_path / "formal.json")
    assert changed.stat().st_size == source.stat().st_size
    with pytest.raises(subject.F24IngestionSafetyError, match="SOURCE_SHA256_DRIFT"):
        subject.load_frozen_formal_decision_v1(
            REPO_ROOT,
            formal_decision_path=changed,
            execute_formal_validator=False,
        )


def test_formal_validator_sha_drift_fails_closed(tmp_path: Path) -> None:
    source = REPO_ROOT.parent / subject.FORMAL_VALIDATOR_RELATIVE
    changed = mutate_bytes(source, b"F24", b"G24", tmp_path / "validator.py")
    assert changed.stat().st_size == source.stat().st_size
    with pytest.raises(subject.F24IngestionSafetyError, match="SOURCE_SHA256_DRIFT"):
        subject.load_frozen_formal_decision_v1(
            REPO_ROOT,
            formal_validator_path=changed,
            execute_formal_validator=False,
        )


def test_preparation_source_sha_drift_fails_closed(tmp_path: Path) -> None:
    relative = subject.PREPARATION_ROOT / "f24_graph_and_role_candidates_v1.json"
    source = REPO_ROOT.parent / relative
    changed = mutate_bytes(source, b'"heavy_atom_count": 23', b'"heavy_atom_count": 24', tmp_path / "graph.json")
    with pytest.raises(subject.F24IngestionSafetyError, match="SOURCE_SHA256_DRIFT"):
        subject.load_frozen_formal_decision_v1(
            REPO_ROOT,
            repository_path_overrides={relative: changed},
            execute_formal_validator=False,
        )


def current_census_payloads() -> dict[Path, bytes]:
    return {
        binding[0]: (REPO_ROOT / binding[0]).read_bytes()
        for binding in subject.CENSUS_BINDINGS
    }


def test_current_census_f24_prior_state_change_fails_closed() -> None:
    payloads = current_census_payloads()
    csv_path = subject.CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_ozj_v1.csv"
    rows = list(
        csv.DictReader(io.StringIO(payloads[csv_path].decode("utf-8")))
    )
    target = next(row for row in rows if row["scaleup_rank"] == "593")
    target["current_global_status"] = "COMPLETED_HUMAN_POSITIVE"
    payloads[csv_path] = subject._csv_bytes(tuple(rows[0]), rows)
    with pytest.raises(subject.F24IngestionSafetyError):
        subject._current_census_boundary(REPO_ROOT, payloads)


def test_current_census_priority_head_change_fails_closed() -> None:
    payloads = current_census_payloads()
    summary_path = subject.CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_ozj_v1.json"
    summary = json.loads(payloads[summary_path])
    summary["authority_boundary"]["next_priority_review_ligand"] = "ZZZ"
    payloads[summary_path] = subject._json_bytes(summary)
    with pytest.raises(subject.F24IngestionSafetyError, match="PRIORITY_HEAD_DRIFT"):
        subject._current_census_boundary(REPO_ROOT, payloads)


def mutate_matrix_artifact(
    artifacts: dict[str, bytes], mutation: object
) -> dict[str, bytes]:
    changed = dict(artifacts)
    rows = list(csv.DictReader(io.StringIO(changed[subject.MATRIX].decode("utf-8"))))
    mutation(rows)
    changed[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows)
    return changed


@pytest.mark.parametrize(
    ("name", "mutation"),
    [
        ("extra", lambda rows: rows.append(copy.deepcopy(rows[-1]))),
        ("duplicate", lambda rows: rows[1].__setitem__("canonical_event_id", rows[0]["canonical_event_id"])),
        ("swap", lambda rows: rows[0].update({"warhead_atoms_json": rows[0]["chemical_warhead_atoms_json"], "chemical_warhead_atoms_json": rows[0]["warhead_atoms_json"]})),
        ("legacy_chemical_five", lambda rows: rows[0].__setitem__("warhead_atoms_json", subject._json_cell(list(subject.CHEMICAL_WARHEAD)))),
        ("candidate_8", lambda rows: rows[0].__setitem__("selected_role_candidate_index_0based", "8")),
        ("future_candidate_false", lambda rows: rows[0].__setitem__("candidate_for_future_training_admission", "false")),
        ("admission", lambda rows: rows[0].__setitem__("training_admitted", "true")),
        ("seed", lambda rows: rows[0].__setitem__("minimal_seed_authority_available", "true")),
        ("all_five", lambda rows: rows[0].__setitem__("direct_profile_applicable_task_ids_json", "[0,1,2,3,4]")),
    ],
)
def test_output_matrix_tampering_fails_closed(
    artifacts: dict[str, bytes], name: str, mutation: object
) -> None:
    del name
    changed = mutate_matrix_artifact(artifacts, mutation)
    with pytest.raises(subject.F24IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(changed)


def test_dynamic_metadata_fails_closed() -> None:
    with pytest.raises(subject.F24IngestionSafetyError, match="DYNAMIC_METADATA_KEY"):
        subject._reject_dynamic_metadata({"generated_at": "2026-08-29T02:00:00Z"})
    with pytest.raises(subject.F24IngestionSafetyError, match="ABSOLUTE_OR_MACHINE_PATH"):
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
        expected_paths=paths,
        tracked_paths=set(),
        status_lines=candidate_status_lines(paths),
        working_tree_diff_paths=(),
        cached_diff_paths=(),
    )
    tracked = checker_module._classify_repository_profile(
        expected_paths=paths,
        tracked_paths=set(paths),
        status_lines=(),
        working_tree_diff_paths=(),
        cached_diff_paths=(),
    )
    assert candidate == "CANDIDATE_UNTRACKED"
    assert tracked == "TRACKED_CLEAN"
    assert {candidate, tracked} == {
        checker_module._CANDIDATE_UNTRACKED,
        checker_module._TRACKED_CLEAN,
    }


@pytest.mark.parametrize(
    ("tracked_kind", "status_kind", "working_diff", "cached_diff", "error"),
    [
        ("partial", "candidate", (), (), "CANDIDATE_TRACKING_PROFILE_MIXED"),
        ("none", "extra_untracked", (), (), "CANDIDATE_UNTRACKED_STATUS_EXTRA"),
        ("all", "tracked_modified", ("tracked.txt",), (), "TRACKED_WORKTREE_MODIFICATION_PRESENT"),
        ("all", "tracked_staged", (), ("staged.txt",), "STAGED_INDEX_CHANGE_PRESENT"),
        ("none", "missing_candidate", (), (), "CANDIDATE_UNTRACKED_STATUS_MISSING"),
        ("all", "unexpected_status", (), (), "TRACKED_CLEAN_STATUS_NOT_EMPTY"),
    ],
)
def test_checker_repository_profile_mixed_states_fail_closed(
    checker_module: object,
    tracked_kind: str,
    status_kind: str,
    working_diff: tuple[str, ...],
    cached_diff: tuple[str, ...],
    error: str,
) -> None:
    paths = expected_candidate_paths()
    tracked = {
        "none": set(),
        "partial": {paths[0]},
        "all": set(paths),
    }[tracked_kind]
    statuses = {
        "candidate": candidate_status_lines(paths),
        "extra_untracked": (*candidate_status_lines(paths), "?? unrelated.txt"),
        "tracked_modified": (" M " + paths[0],),
        "tracked_staged": ("M  " + paths[0],),
        "missing_candidate": candidate_status_lines(paths[1:]),
        "unexpected_status": ("?? unrelated.txt",),
    }[status_kind]
    with pytest.raises(SystemExit, match=error):
        checker_module._classify_repository_profile(
            expected_paths=paths,
            tracked_paths=tracked,
            status_lines=statuses,
            working_tree_diff_paths=working_diff,
            cached_diff_paths=cached_diff,
        )
