from __future__ import annotations

import ast
import copy
import csv
from dataclasses import fields
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path
import re

import pytest

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (
    covapie_me7_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ERROR_PREFIX = "COVAPIE_ME7_INGESTION_V1_ERROR:"


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


@pytest.fixture(scope="module")
def formal() -> dict[str, object]:
    return json.loads((REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes())


@pytest.fixture(scope="module")
def event_evidence() -> list[dict[str, object]]:
    payload = (REPO_ROOT.parent / owner.EVENT_EVIDENCE_RELATIVE).read_bytes()
    return owner._validate_event_evidence(payload)


def load_checker():
    path = REPO_ROOT / owner.CHECKER_RELATIVE
    spec = importlib.util.spec_from_file_location("check_me7_ingestion_v1", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mutate_path(
    document: dict[str, object], path: tuple[object, ...], value: object
) -> None:
    cursor: object = document
    for part in path[:-1]:
        cursor = cursor[part]  # type: ignore[index]
    cursor[path[-1]] = value  # type: ignore[index]


def delete_path(document: dict[str, object], path: tuple[object, ...]) -> None:
    cursor: object = document
    for part in path[:-1]:
        cursor = cursor[part]  # type: ignore[index]
    del cursor[path[-1]]  # type: ignore[index]


def assert_stage_error(token: str):
    return pytest.raises(
        owner.ME7IngestionSafetyError,
        match="^" + re.escape(ERROR_PREFIX + token),
    )


def csv_bytes(rows: list[dict[str, str]], header: list[str] | tuple[str, ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def test_public_api_and_exact7_inventory() -> None:
    assert owner.__all__ == (
        "ME7IngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert owner.OUTPUT_FILENAMES == (
        "covapie_me7_completed_human_decision_snapshot_v1.json",
        "covapie_me7_event_task_label_availability_v1.csv",
        "covapie_me7_completed_decision_ingestion_summary_v1.json",
        "covapie_me7_completed_decision_ingestion_manifest_v1.json",
    )


def test_frozen_sources_are_exact_and_minimal() -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert bound["active_source_binding_count"] == 9
    bindings = bound["active_source_bindings"]
    assert len(bindings) == 9
    assert len({row["semantic_source_identity"] for row in bindings}) == 9
    assert bound["formal_decision_binding"]["byte_count"] == 13344
    assert bound["formal_decision_binding"]["SHA256"] == (
        "9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407"
    )
    assert bound["formal_validator_binding"]["byte_count"] == 52865
    assert bound["formal_validator_binding"]["SHA256"] == (
        "67a68f9b1c14cb90591a6e377c4fc680cc816c53e138995adf0c1544eaf91009"
    )


def test_formal_validator_is_identity_only_and_runtime_is_not_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_text = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "subprocess" not in imports
    assert "runpy" not in imports
    assert "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1" not in source_text
    observed: list[str] = []
    real_import = importlib.import_module

    def guarded(name: str, package: str | None = None):
        assert "validate_me7_formal_human_decision_v1" not in name
        assert "direct_attachment_optional_linker_runtime" not in name
        observed.append(name)
        return real_import(name, package)

    monkeypatch.setattr(owner.importlib, "import_module", guarded)
    owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert observed == [
        "covalent_ext.covapie_completed_human_decision_reconciliation_v1"
    ]


def test_checker_subprocess_calls_are_git_only() -> None:
    checker_tree = ast.parse(
        (REPO_ROOT / owner.CHECKER_RELATIVE).read_text(encoding="utf-8")
    )
    calls = [
        node
        for node in ast.walk(checker_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    assert calls
    for call in calls:
        first = call.args[0]
        assert isinstance(first, ast.Tuple)
        assert isinstance(first.elts[0], ast.Constant)
        assert first.elts[0].value == "git"


def test_raw_normalized_and_task_domain_negative_are_separate(
    snapshot: dict[str, object],
) -> None:
    normalization = snapshot["normalization_contract"]
    assert normalization["task_relevance"]["source_formal_value"] == "OUT_OF_DOMAIN"
    assert normalization["task_relevance"]["normalized_value"] == "NOT_RELEVANT"
    assert normalization["task_relevance"]["mapping"] == (
        "OUT_OF_DOMAIN_TO_NOT_RELEVANT"
    )
    assert normalization["training_disposition"]["source_formal_value"] == (
        "NOT_APPLICABLE"
    )
    assert normalization["training_disposition"]["normalized_value"] == (
        "NOT_APPLICABLE"
    )
    assert snapshot["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
    assert snapshot["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
    separation = snapshot["chemistry_and_task_domain_separation"]
    assert separation["chemistry_disposition"] == "POSITIVE"
    assert separation["task_relevance_disposition"] == "NOT_RELEVANT"
    assert separation["task_domain_negative"] is True
    assert separation["negative_chemistry"] is False


def test_d4_d5_are_answered_while_structure_authority_remains_null(
    snapshot: dict[str, object],
) -> None:
    state = snapshot["role_seed_and_task_null_state"]
    assert state["D4_formally_answered"] is True
    assert state["D5_formally_answered"] is True
    for key in (
        "selected_role_candidate",
        "role_profile",
        "warhead_atom_ids",
        "linker_atom_ids",
        "scaffold_atom_ids",
        "minimal_seed",
        "minimal_seed_atom_ids",
        "primary_anchor",
        "structurally_applicable_task_ids",
    ):
        assert state[key] is None
    assert state["role_profile_derived_state"] == "NOT_ESTABLISHED"
    assert state["role_partition_sample_authoritative"] is False
    assert state["minimal_seed_sample_authoritative"] is False
    assert state["task_applicability_sample_authoritative"] is False
    assert state["canonical_mask_structural_labels_available"] is False
    assert state["role_runtime_executed"] is False
    assert state["seed_runtime_executed"] is False
    assert state["task_runtime_executed"] is False


def test_exact3_pair_and_context_boundary(snapshot: dict[str, object]) -> None:
    pair = snapshot["reactive_pair_authority"]
    assert pair["observed_pair"] == "SG:CAE"
    assert pair["sample_level_authoritative"] is True
    assert pair["target_pair_is_only_attachment_for_component_instance"] is False
    assert pair["reusable_pair_authority"] is False
    assert [event["canonical_event_id"] for event in snapshot["events"]] == list(
        owner.EXPECTED_EVENT_IDS
    )
    context = snapshot["context_boundary"]
    assert context["context_merged_into_target_exact3"] is False
    assert context["context_only_scaleup_ranks"] == [527, 530, 533]
    assert context["context_only_events_received_formal_decisions"] is False
    assert all(row["target_event"] is False for row in context["context_only_records"])
    assert not (
        {row["canonical_event_id"] for row in context["context_only_records"]}
        & set(owner.EXPECTED_EVENT_IDS)
    )


def test_observed_geometry_and_source_records_are_preserved(
    snapshot: dict[str, object],
) -> None:
    expected = (
        (528, "1.805", "1.804924", "0.000076"),
        (529, "1.816", "1.816389", "0.000389"),
        (531, "1.831", "1.831178", "0.000178"),
    )
    for event, values in zip(snapshot["events"], expected, strict=True):
        rank, reported, recalculated, difference = values
        frozen = event["frozen_csv_record"]
        assert event["scaleup_rank"] == rank
        assert frozen["reported_distance_angstrom"] == reported
        assert frozen["recalculated_distance_angstrom"] == recalculated
        assert frozen["absolute_difference_angstrom"] == difference
        assert json.loads(frozen["source_datasets_json"]) == [
            "SOURCE_COVBINDERINPDB",
            "SOURCE_RCSB_PDB_DIRECT",
        ]
        graph = event["frozen_graph_source_record"]
        assert graph["reported_distance_angstrom"] == float(reported)
        assert graph["recalculated_distance_angstrom"] == float(recalculated)
        assert graph["explicit_covalent_evidence"] is True
        assert graph["human_selected"] is False
        assert graph["processing_observation"]["post"]["sample_authoritative"] is False


def test_pre_post_training_and_readiness_boundaries(snapshot: dict[str, object]) -> None:
    pre = snapshot["PRE_boundary"]
    assert pre["source_graph_count_per_event"] == 1
    assert pre["mapping_count_per_event"] == 8
    assert pre["PRE_source_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"
    assert pre["PRE_mapping_auto_selected"] is False
    assert pre["PRE_authority"] is False
    assert pre["POST_to_PRE_copy"] is False
    assert pre["PRE_zero_fill"] is False
    post = snapshot["POST_boundary"]
    assert post["POST_source_evidence_available"] is True
    assert post["POST_sample_geometry_authority_created"] is False
    assert post["POST_geometry_training_authority"] is False
    training = snapshot["training_boundary"]
    assert training["human_training_excluded"] is False
    assert training["human_training_excluded_false_is_not_include_or_admission"] is True
    assert training["future_training_admission_candidate"] is False
    assert training["formal_training_admitted"] is False
    assert training["training_materialization_allowed"] is False
    assert snapshot["readiness"]["FEATURE_SEMANTICS_AUDIT_PERFORMED"] is False
    assert snapshot["readiness"]["STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK"] is True


def test_canonical_exact5_preserves_b3_without_applicability(
    snapshot: dict[str, object],
) -> None:
    tasks = snapshot["canonical_task_contract"]
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["sixth_task"] is False
    assert [row["semantic_long_name"] for row in tasks["global_canonical_tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert all(row["structurally_applicable"] is None for row in tasks["global_canonical_tasks"])
    assert tasks["sample_applicable_task_ids"] is None
    assert tasks["task_applicability_sample_authority"] is False
    assert tasks["task_label_authority"] is False


def test_generic_exact11_is_task_domain_negative_without_rich_fields(
    snapshot: dict[str, object],
) -> None:
    block = snapshot["generic_Exact11_compatibility"]
    assert block["accepted_fact_count"] == 3
    assert block["rich_fields_leaked"] is False
    assert block["NormalizedDecisionSource_constructed"] is True
    assert block["path_namespace_conversion"] == {
        "ingestion_binding_namespace": "project_parent_relative",
        "generic_binding_namespace": "repository_parent_relative",
        "stable_source_path": owner.FORMAL_DECISION_RELATIVE.as_posix(),
        "strings_not_interchanged_without_explicit_conversion": True,
    }
    for fact in block["facts"]:
        assert set(fact) == set(owner.GENERIC_FACT_FIELDS)
        assert fact["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert fact["task_relevance_disposition"] == "NOT_RELEVANT"
        assert fact["chemistry_disposition"] == "POSITIVE"
        assert fact["training_disposition"] == "NOT_APPLICABLE"
        assert fact["human_training_excluded"] is False
        assert "pair" not in fact
        assert "role_profile" not in fact
        assert "context" not in fact


def test_matrix_null_serialization_and_summary_counts(
    artifacts: dict[str, bytes],
) -> None:
    rows = list(csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"))))
    assert len(rows) == 3
    assert tuple(rows[0]) == owner.MATRIX_HEADER
    null_columns = (
        "selected_role_candidate_json",
        "role_profile_raw_json",
        "warhead_atom_ids_json",
        "linker_atom_ids_json",
        "scaffold_atom_ids_json",
        "minimal_seed_json",
        "minimal_seed_atom_ids_json",
        "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    )
    for row in rows:
        assert all(row[column] == "null" for column in null_columns)
        assert row["role_profile_derived_state"] == "NOT_ESTABLISHED"
        assert row["task_label_authority"] == "false"
        assert row["event_task_label_rows_materialized"] == "false"
    summary = json.loads(artifacts[owner.SUMMARY])
    expected = {
        "event_count": 3,
        "review_unit_count": 1,
        "human_review_completed_count": 3,
        "chemistry_positive_count": 3,
        "task_not_relevant_count": 3,
        "training_not_applicable_count": 3,
        "human_training_excluded_count": 0,
        "future_training_admission_candidate_count": 0,
        "pair_sample_authority_count": 3,
        "role_partition_sample_authority_count": 0,
        "minimal_seed_sample_authority_count": 0,
        "task_applicability_sample_authority_count": 0,
        "canonical_structural_label_available_count": 0,
        "generic_exact11_fact_count": 3,
        "formal_training_admitted_count": 0,
    }
    for key, value in expected.items():
        assert summary[key] == value


def test_manifest_closure_header_types_and_determinism(
    artifacts: dict[str, bytes],
) -> None:
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    assert manifest["active_source_binding_count"] == 9
    assert manifest["duplicate_source_binding_identity_count"] == 0
    assert len(manifest["candidate_source_bindings"]) == 3
    assert len(manifest["output_artifact_bindings_excluding_manifest_self"]) == 3
    assert all(
        owner.MANIFEST not in row["path"]
        for row in manifest["output_artifact_bindings_excluding_manifest_self"]
    )
    contract = manifest["matrix_contract"]
    assert contract["header"] == list(owner.MATRIX_HEADER)
    assert contract["column_count"] == len(owner.MATRIX_HEADER)
    assert len(contract["column_types"]) == len(owner.MATRIX_HEADER)
    assert contract["null_json_serialization"] == "null"
    assert contract["rows_are_availability_metadata_not_event_task_label_rows"] is True
    assert manifest["formal_validator_imported"] is False
    assert manifest["formal_validator_executed_by_production"] is False
    assert manifest["formal_validator_subprocessed_by_production"] is False
    assert artifacts == owner.build_artifacts_v1(REPO_ROOT)


def test_current_with_pyr_census_and_queue_remain_historical_pending() -> None:
    current = owner.load_frozen_formal_decision_v1(REPO_ROOT)[
        "current_census_and_queue_boundary"
    ]
    assert current["ME7_event_count"] == 3
    assert current["ME7_current_review_status"] == "CURRENTLY_UNREVIEWED"
    assert current["ME7_human_review_completed"] is False
    assert current["ME7_structurally_applicable_task_ids"] is None
    assert current["ME7_priority_rank"] == 32
    assert current["census_refresh_performed"] is False
    assert current["queue_refresh_performed"] is False
    assert current["historical_pending_state_is_expected_until_refresh"] is True


def test_checker_independent_paths_and_real_lifecycle(
    artifacts: dict[str, bytes],
) -> None:
    checker = load_checker()
    sources = checker.independently_check_sources(REPO_ROOT)
    independent = checker.independently_check_artifacts(REPO_ROOT, artifacts)
    lifecycle = checker.check_git_lifecycle(REPO_ROOT)
    assert sources["source_count"] == 9
    assert sources["formal_validator_executed"] is False
    assert sources["role_seed_task_runtime_executed"] is False
    assert sources["generic_exact11_fact_count"] == 3
    assert independent["FORMAL_SOURCE_D2"] == "OUT_OF_DOMAIN"
    assert independent["NORMALIZED_TASK_RELEVANCE"] == "NOT_RELEVANT"
    assert independent["STRUCTURALLY_APPLICABLE_TASK_IDS"] is None
    assert lifecycle["profile"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }
    if lifecycle["profile"] == checker.CANDIDATE_UNTRACKED:
        assert lifecycle["git_index_mode_checked"] is False
        assert lifecycle["git_index_record_count"] == 0
    else:
        assert lifecycle["git_index_mode_checked"] is True
        assert lifecycle["git_index_record_count"] == 7


@pytest.mark.parametrize(
    ("path", "value", "token"),
    (
        (("schema_version",), "wrong", "FORMAL_SCHEMA_DRIFT"),
        (
            ("authorization_record", "authorization_origin"),
            "MACHINE",
            "FORMAL_AUTHORIZATION_DRIFT",
        ),
        (
            ("authorization_record", "reviewer_id"),
            "other",
            "FORMAL_AUTHORIZATION_DRIFT",
        ),
        (
            ("authorization_record", "attestor_id"),
            "other",
            "FORMAL_AUTHORIZATION_DRIFT",
        ),
        (
            ("frozen_candidate_binding", "SHA256"),
            "0" * 64,
            "FORMAL_FROZEN_CANDIDATE_DRIFT",
        ),
        (
            ("approved_D1_D6", "D1_observation_record_judgment", "decision"),
            "NEGATIVE",
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            ("approved_D1_D6", "D2_project_domain_relevance", "decision"),
            "NOT_RELEVANT",
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            ("approved_D1_D6", "D3_recorded_endpoint_confirmation", "pair"),
            "SG:CAH",
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            (
                "approved_D1_D6",
                "D3_recorded_endpoint_confirmation",
                "target_pair_is_only_attachment_for_component_instance",
            ),
            True,
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            (
                "approved_D1_D6",
                "D4_role_partition_and_retained_information",
                "decision",
            ),
            "PROVIDE_ROLE_PARTITION",
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            (
                "approved_D1_D6",
                "D4_role_partition_and_retained_information",
                "selected_candidate_id",
            ),
            "FABRICATED",
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            (
                "approved_D1_D6",
                "D5_structural_task_applicability",
                "task_ids",
            ),
            [],
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            ("approved_D1_D6", "D6_later_use_disposition", "decision"),
            "EXCLUDE",
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            (
                "approved_D1_D6",
                "D6_later_use_disposition",
                "human_training_excluded",
            ),
            True,
            "FORMAL_APPROVED_D1_D6_DRIFT",
        ),
        (
            ("role_and_task_disposition", "role_profile"),
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "FORMAL_ROLE_TASK_DISPOSITION_DRIFT",
        ),
        (
            ("role_and_task_disposition", "warhead_atom_ids"),
            [],
            "FORMAL_ROLE_TASK_DISPOSITION_DRIFT",
        ),
        (
            ("role_and_task_disposition", "applicable_task_ids"),
            [0, 3, 4],
            "FORMAL_ROLE_TASK_DISPOSITION_DRIFT",
        ),
        (
            ("role_and_task_disposition", "B3_present"),
            False,
            "FORMAL_ROLE_TASK_DISPOSITION_DRIFT",
        ),
        (
            ("role_and_task_disposition", "sixth_task_created"),
            True,
            "FORMAL_ROLE_TASK_DISPOSITION_DRIFT",
        ),
        (
            ("non_created_authority", "TASK_LABEL_AUTHORITY"),
            True,
            "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
        ),
        (
            ("readiness", "READY_FOR_TRAINING"),
            True,
            "FORMAL_READINESS_DRIFT",
        ),
    ),
)
def test_formal_semantic_mutations_fail_with_exact_stage_token(
    formal: dict[str, object],
    path: tuple[object, ...],
    value: object,
    token: str,
) -> None:
    mutated = copy.deepcopy(formal)
    mutate_path(mutated, path, value)
    with assert_stage_error(token):
        owner._validate_formal(mutated)


@pytest.mark.parametrize(
    ("path", "token"),
    (
        (("authorization_record", "authorization_message_id"), "FORMAL_AUTHORIZATION_DRIFT:MISSING"),
        (("sample_level_authority", "role_partition_sample_authoritative"), "FORMAL_SAMPLE_AUTHORITY_DRIFT:MISSING"),
        (("role_and_task_disposition", "role_profile"), "FORMAL_ROLE_TASK_DISPOSITION_DRIFT:MISSING"),
        (("role_and_task_disposition", "applicable_task_ids"), "FORMAL_ROLE_TASK_DISPOSITION_DRIFT:MISSING"),
        (("non_created_authority", "TASK_LABEL_AUTHORITY"), "FORMAL_NON_CREATED_AUTHORITY_DRIFT:MISSING"),
    ),
)
def test_required_null_and_false_fields_cannot_be_missing(
    formal: dict[str, object], path: tuple[object, ...], token: str
) -> None:
    mutated = copy.deepcopy(formal)
    delete_path(mutated, path)
    with assert_stage_error(token):
        owner._validate_formal(mutated)


def test_strict_json_and_csv_reject_duplicate_fields() -> None:
    with assert_stage_error("JSON_DUPLICATE_KEY:DUP:key"):
        owner._strict_json(b'{"key":1,"key":2}\n', "DUP")
    with assert_stage_error("CSV_HEADER_DUPLICATE_OR_EMPTY:DUP"):
        owner._parse_csv(b"a,a\n1,2\n", "DUP")


def test_wrong_formal_validator_and_direct_source_identities_fail_closed(
    tmp_path: Path,
) -> None:
    for relative, keyword in (
        (owner.FORMAL_DECISION_RELATIVE, "formal_decision_path"),
        (owner.FORMAL_VALIDATOR_RELATIVE, "formal_validator_path"),
    ):
        source = REPO_ROOT.parent / relative
        bad = tmp_path / source.name
        bad.write_bytes(source.read_bytes() + b"\n")
        with assert_stage_error("SOURCE_BINDING_FAILED:"):
            owner.load_frozen_formal_decision_v1(REPO_ROOT, **{keyword: bad})


def test_event_evidence_wrong_event_unit_pdb_and_context_fail_semantically() -> None:
    source = REPO_ROOT.parent / owner.EVENT_EVIDENCE_RELATIVE
    header, rows = owner._parse_csv(source.read_bytes(), "TEST_EVENT")
    for key, value, token in (
        ("canonical_event_id", owner.EXPECTED_CONTEXT[0][1], "EVENT_EVIDENCE_DRIFT:528:canonical_event_id"),
        ("review_unit_id", "wrong", "EVENT_EVIDENCE_DRIFT:528:review_unit_id"),
        ("pdb_id", "3QVZ", "EVENT_EVIDENCE_DRIFT:528:pdb_id"),
        ("target_event", "false", "EVENT_EVIDENCE_DRIFT:528:target_event"),
    ):
        mutated = copy.deepcopy(rows)
        mutated[0][key] = str(value)
        with assert_stage_error(token):
            owner._validate_event_evidence(csv_bytes(mutated, header))


def test_graph_target_context_and_pre_mapping_mutations_fail_semantically(
    event_evidence: list[dict[str, object]],
) -> None:
    path = REPO_ROOT.parent / owner.GRAPH_EVIDENCE_RELATIVE
    original = json.loads(path.read_bytes())
    probes = (
        (("target_events", 0, "canonical_event_id"), owner.EXPECTED_CONTEXT[0][1], "GRAPH_TARGET_EVENT_DRIFT:528"),
        (("target_events", 0, "human_selected"), True, "GRAPH_TARGET_EVENT_DRIFT:528"),
        (("target_events", 0, "processing_observation", "pre", "pre_source_graph_mapping_count"), 0, "GRAPH_PRE_DRIFT:528"),
        (("additional_instance_connection_context", 0, "target_event"), True, "GRAPH_CONTEXT_EVENT_DRIFT:527"),
        (("canonical_Exact5", "B3_present"), False, "GRAPH_CANONICAL_EXACT5_DRIFT"),
        (("canonical_Exact5", "sixth_task_present"), True, "GRAPH_CANONICAL_EXACT5_DRIFT"),
    )
    for mutation, value, token in probes:
        mutated = copy.deepcopy(original)
        mutate_path(mutated, mutation, value)
        with assert_stage_error(token):
            owner._validate_graph_evidence(owner._json_bytes(mutated), event_evidence)


@pytest.mark.parametrize(
    ("path", "value", "token"),
    (
        (("events", 0, "chemistry_disposition"), "NEGATIVE", "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "legacy_completed_review_status"), "COMPLETED_HUMAN_POSITIVE", "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "training_disposition"), "INCLUDE", "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "human_training_excluded"), True, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "future_training_admission_candidate"), True, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "D4_formally_answered"), False, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "D5_formally_answered"), False, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "role_profile"), "FABRICATED", "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "minimal_seed_atom_ids"), [], "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "structurally_applicable_task_ids"), [0, 3, 4], "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "pair_sample_authority"), False, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "target_pair_is_only_attachment_for_component_instance"), True, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "role_partition_sample_authoritative"), True, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "task_applicability_sample_authoritative"), True, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "POST_geometry_training_authority"), True, "SNAPSHOT_EVENT_DRIFT"),
        (("events", 0, "formal_training_admitted"), True, "SNAPSHOT_EVENT_DRIFT"),
        (("role_seed_and_task_null_state", "role_profile"), [], "SNAPSHOT_NULL_AUTHORITY_DRIFT"),
        (("role_seed_and_task_null_state", "structurally_applicable_task_ids"), [], "SNAPSHOT_NULL_AUTHORITY_DRIFT"),
        (("canonical_task_contract", "B3_present"), False, "SNAPSHOT_TASK_CONTRACT_DRIFT"),
        (("canonical_task_contract", "sixth_task"), True, "SNAPSHOT_TASK_CONTRACT_DRIFT"),
        (("PRE_boundary", "PRE_mapping_auto_selected"), True, "SNAPSHOT_PRE_DRIFT"),
        (("training_boundary", "future_training_admission_candidate"), True, "SNAPSHOT_TRAINING_DRIFT"),
        (("readiness", "TRAINING_STARTED"), True, "SNAPSHOT_READINESS_DRIFT"),
    ),
)
def test_snapshot_semantic_mutations_fail_with_exact_stage_token(
    snapshot: dict[str, object],
    path: tuple[object, ...],
    value: object,
    token: str,
) -> None:
    mutated = copy.deepcopy(snapshot)
    mutate_path(mutated, path, value)
    with assert_stage_error(token):
        owner._validate_snapshot_semantics(mutated)


def test_generic_owner_accepts_exact_task_domain_negative_and_rejects_promotions() -> None:
    binding = generic.SourceBinding(
        source_path=owner.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=13344,
        sha256=owner.FORMAL_BINDINGS[0][3],
        schema_version=owner.FORMAL_DECISION_SCHEMA,
        review_unit_id=owner.EXPECTED_REVIEW_UNIT_ID,
    )
    base = {
        "canonical_event_id": owner.EXPECTED_EVENT_IDS[0],
        "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
        "human_review_completed": True,
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "task_relevance_disposition": "NOT_RELEVANT",
        "chemistry_disposition": "POSITIVE",
        "training_disposition": "NOT_APPLICABLE",
        "human_training_excluded": False,
        "source_decision_schema": owner.FORMAL_DECISION_SCHEMA,
        "source_decision_sha256": owner.FORMAL_BINDINGS[0][3],
        "source_binding_path": owner.FORMAL_DECISION_RELATIVE.as_posix(),
    }
    fact = generic.NormalizedCompletedDecisionFact(**base)
    assert tuple(field.name for field in fields(fact)) == owner.GENERIC_FACT_FIELDS
    generic._validate_fact(fact, binding)
    for key, value in (
        ("legacy_completed_review_status", "COMPLETED_HUMAN_POSITIVE"),
        ("task_relevance_disposition", "RELEVANT"),
        ("training_disposition", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("human_training_excluded", True),
    ):
        wrong = generic.NormalizedCompletedDecisionFact(**{**base, key: value})
        with pytest.raises(generic.CompletedDecisionReconciliationError):
            generic._validate_fact(wrong, binding)


def test_generic_rich_field_leak_fails_closed(snapshot: dict[str, object]) -> None:
    mutated = copy.deepcopy(snapshot)
    mutated["generic_Exact11_compatibility"]["facts"][0]["pair"] = "SG:CAE"
    with assert_stage_error("SNAPSHOT_GENERIC_FACT_NOT_EXACT11"):
        owner._validate_snapshot_semantics(mutated)


def test_manifest_source_output_header_and_dynamic_drift_fail_closed(
    artifacts: dict[str, bytes],
) -> None:
    probes = (
        (("active_source_bindings", 0, "SHA256"), "0" * 64, "MANIFEST_ACTIVE_SOURCE_BINDINGS_DRIFT"),
        (("candidate_source_bindings", 0, "SHA256"), "0" * 64, "MANIFEST_CANDIDATE_SOURCE_BINDINGS_DRIFT"),
        (("output_artifact_bindings_excluding_manifest_self", 0, "SHA256"), "0" * 64, "MANIFEST_OUTPUT_BINDINGS_DRIFT"),
        (("matrix_contract", "header"), [], "MANIFEST_MATRIX_CONTRACT_DRIFT"),
    )
    for path, value, token in probes:
        manifest = json.loads(artifacts[owner.MANIFEST])
        mutate_path(manifest, path, value)
        with assert_stage_error(token):
            owner._validate_manifest_semantics(manifest, REPO_ROOT, artifacts)
    manifest = json.loads(artifacts[owner.MANIFEST])
    manifest["timestamp"] = "forbidden"
    with assert_stage_error("MANIFEST_DYNAMIC_METADATA_KEY"):
        owner._validate_manifest_semantics(manifest, REPO_ROOT, artifacts)


def test_raw_byte_comparator_uses_normal_materialized_fresh_path(
    artifacts: dict[str, bytes],
) -> None:
    mutated = dict(artifacts)
    snapshot = json.loads(mutated[owner.SNAPSHOT])
    reordered = json.dumps(snapshot, ensure_ascii=False, sort_keys=False).encode("utf-8") + b"\n"
    assert json.loads(reordered) == snapshot
    mutated[owner.SNAPSHOT] = reordered
    manifest = json.loads(mutated[owner.MANIFEST])
    record = next(
        row
        for row in manifest["output_artifact_bindings_excluding_manifest_self"]
        if row["path"].endswith(owner.SNAPSHOT)
    )
    record["byte_count"] = len(reordered)
    record["SHA256"] = hashlib.sha256(reordered).hexdigest()
    mutated[owner.MANIFEST] = owner._json_bytes(manifest)
    with assert_stage_error("ARTIFACT_PROJECTION_DRIFT:" + owner.SNAPSHOT):
        owner.validate_completed_decision_projection_v1(mutated, REPO_ROOT)


def test_git_index_parser_accepts_exact_stage0_100644_and_rejects_drifts() -> None:
    checker = load_checker()
    paths = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    valid = "\n".join(f"100644 {'0' * 40} 0\t{path}" for path in reversed(paths))
    parsed = checker.parse_exact7_index_records(valid, paths)
    assert len(parsed) == 7
    assert {row["mode"] for row in parsed} == {"100644"}
    probes = (
        ("\n".join(valid.splitlines()[:-1]), "RECORD_COUNT_NOT_EXACT7"),
        (valid.replace(paths[0], paths[1]), "DUPLICATE_PATH"),
        (valid.replace("100644", "100755", 1), "MODE_NOT_100644"),
        (valid.replace("100644", "120000", 1), "MODE_NOT_100644"),
        (valid.replace(" 0\t", " 1\t", 1), "NONZERO_STAGE"),
    )
    for payload, token in probes:
        with pytest.raises(
            RuntimeError,
            match="^COVAPIE_ME7_INGESTION_CHECK_V1_ERROR:"
            "TRACKED_CLEAN_GIT_INDEX_" + token,
        ):
            checker.parse_exact7_index_records(payload, paths)


def test_real_lifecycle_rejects_unauthorized_eighth_untracked_file() -> None:
    checker = load_checker()
    rogue = REPO_ROOT / "me7_ingestion_unauthorized_eighth_file.txt"
    assert not rogue.exists()
    try:
        rogue.write_text("negative probe\n", encoding="utf-8")
        with pytest.raises(
            RuntimeError,
            match="^COVAPIE_ME7_INGESTION_CHECK_V1_ERROR:"
            "ORDINARY_UNTRACKED_NOT_EXACT7_OR_EMPTY$",
        ):
            checker.check_git_lifecycle(REPO_ROOT)
    finally:
        rogue.unlink(missing_ok=True)
