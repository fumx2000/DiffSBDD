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
    covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ERROR_PREFIX = "COVAPIE_PYR_INGESTION_V1_ERROR:"


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return owner.build_artifacts_v1(REPO_ROOT)


@pytest.fixture(scope="module")
def snapshot(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[owner.SNAPSHOT])


@pytest.fixture(scope="module")
def formal() -> dict[str, object]:
    return json.loads((REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes())


def load_checker():
    path = REPO_ROOT / owner.CHECKER_RELATIVE
    spec = importlib.util.spec_from_file_location("check_pyr_ingestion_v1", path)
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


def assert_stage_error(token: str):
    return pytest.raises(
        owner.PYRIngestionSafetyError,
        match="^" + re.escape(ERROR_PREFIX + token),
    )


def csv_bytes(rows: list[dict[str, str]], header: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def test_public_api_and_exact7_inventory() -> None:
    assert owner.__all__ == (
        "PYRIngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert owner.OUTPUT_FILENAMES == (
        "covapie_pyr_completed_human_decision_snapshot_v1.json",
        "covapie_pyr_event_task_label_availability_v1.csv",
        "covapie_pyr_completed_decision_ingestion_summary_v1.json",
        "covapie_pyr_completed_decision_ingestion_manifest_v1.json",
    )


def test_frozen_sources_are_exact_and_validator_is_identity_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert bound["active_source_binding_count"] == 13
    assert len(bound["active_source_bindings"]) == 13
    assert len(
        {row["semantic_source_identity"] for row in bound["active_source_bindings"]}
    ) == 13
    assert bound["formal_decision_binding"]["byte_count"] == 17975
    assert bound["formal_decision_binding"]["SHA256"] == (
        "58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d"
    )
    assert bound["formal_validator_binding"]["byte_count"] == 75613
    assert bound["formal_validator_binding"]["SHA256"] == (
        "003a1e6f85616bc8d5f255bd2333f0b61ee0144afaed32a3e7ba64114cdc543c"
    )
    tree = ast.parse((REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "subprocess" not in imports
    assert "runpy" not in imports
    observed: list[str] = []
    real_import = importlib.import_module

    def guarded(name: str, package: str | None = None):
        assert "validate_pyr_formal_human_decision_v1" not in name
        observed.append(name)
        return real_import(name, package)

    monkeypatch.setattr(owner.importlib, "import_module", guarded)
    owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert set(observed) == {
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1",
        "covalent_ext.covapie_completed_human_decision_reconciliation_v1",
    }


def test_raw_and_normalized_values_are_both_preserved(
    snapshot: dict[str, object],
) -> None:
    normalization = snapshot["normalization_contract"]
    assert normalization["task_relevance"] == {
        "source_field": "D2_task_generation_domain_relevance",
        "source_formal_generation_domain_decision": "IN_DOMAIN",
        "target_field": "task_relevance_disposition",
        "normalized_task_relevance_disposition": "RELEVANT",
        "mapping": "IN_DOMAIN_TO_RELEVANT",
        "source_value_preserved": True,
    }
    assert normalization["training_disposition"] == {
        "source_field": "D6_later_training_use_disposition",
        "source_formal_training_use_decision": "EXCLUDE",
        "target_field": "training_disposition",
        "normalized_training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "mapping": "EXCLUDE_TO_EXCLUDE_FROM_TRAINING_ONLY",
        "source_value_preserved": True,
    }
    assert snapshot["legacy_completed_review_status"] == "COMPLETED_HUMAN_POSITIVE"
    for event in snapshot["events"]:
        assert event["source_formal_generation_domain_decision"] == "IN_DOMAIN"
        assert event["normalized_task_relevance_disposition"] == "RELEVANT"
        assert event["source_formal_training_use_decision"] == "EXCLUDE"
        assert (
            event["normalized_training_disposition"]
            == "EXCLUDE_FROM_TRAINING_ONLY"
        )
        assert event["chemistry_disposition"] == "POSITIVE"
        assert event["negative_chemistry"] is False
        assert event["task_domain_negative"] is False
        assert event["human_training_excluded"] is True
        assert event["future_training_admission_candidate"] is False


def test_generic_exact11_is_current_positive_training_exclusion(
    snapshot: dict[str, object],
) -> None:
    block = snapshot["generic_Exact11_compatibility"]
    assert block["accepted_fact_count"] == 4
    assert block["rich_fields_leaked"] is False
    assert block["NormalizedDecisionSource_constructed"] is True
    for fact in block["facts"]:
        assert set(fact) == set(owner.GENERIC_FACT_FIELDS)
        assert fact["legacy_completed_review_status"] == "COMPLETED_HUMAN_POSITIVE"
        assert fact["task_relevance_disposition"] == "RELEVANT"
        assert fact["chemistry_disposition"] == "POSITIVE"
        assert fact["training_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY"
        assert fact["human_training_excluded"] is True
        assert "pair" not in fact
        assert "role_profile" not in fact


def test_selected_and_unselected_runtime_boundaries(
    snapshot: dict[str, object],
) -> None:
    selected = snapshot["selected_role_partition"]
    assert selected["selected_candidate_id"] == (
        "CANDIDATE_A_DIRECT_ALPHA_KETOCARBOXYL_POST_CENTER"
    )
    assert selected["warhead_atom_ids"] == ["CB", "CA", "O3"]
    assert selected["linker_atom_ids"] == []
    assert selected["scaffold_atom_ids"] == ["C", "O", "OXT"]
    assert selected["boundary"] == {
        "scaffold_atom_id": "C",
        "warhead_atom_id": "CA",
        "bond_order": "SING",
    }
    assert selected["minimal_seed_atom_ids"] == ["C", "O"]
    assert selected["primary_anchor"] == "C"
    assert selected["published_runtime_validation"]["valid"] is True
    assert selected["published_runtime_validation"]["applicable_task_ids"] == [0, 3, 4]
    alternative = snapshot["unselected_alternatives"]
    assert alternative["alternative_candidate_id"] == (
        "CANDIDATE_B_STRICT_TERMINAL_ELECTROPHILE_POST_CENTER"
    )
    assert alternative["alternative_human_selected"] is False
    assert alternative["alternative_formal_selected"] is False
    assert alternative["alternative_authority_created"] is False
    assert alternative["authoritative_event_labels_created"] is False
    assert alternative["minimal_seed_atom_ids"] == ["C", "OXT"]


def test_exact5_and_pre_post_authority_boundaries(
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
    assert tasks["sample_applicable_task_ids"] == [0, 3, 4]
    assert tasks["task_label_authority"] is False
    assert tasks["event_task_label_rows_materialized"] is False
    assert tasks["mask_tensor_targets_created"] is False
    assert snapshot["PRE_boundary"]["supporting_adduct_source_graph_count_per_event"] == 1
    assert snapshot["PRE_boundary"]["candidate_PRE_free_source_graph_count_per_event"] == 1
    assert snapshot["PRE_boundary"]["mapping_count_per_event"] == 0
    assert (
        snapshot["PRE_boundary"]["PRE_source_mapping_status"]
        == "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
    )
    assert snapshot["PRE_boundary"]["POST_to_PRE_copy"] is False
    assert snapshot["PRE_boundary"]["PRE_zero_fill"] is False
    assert snapshot["POST_boundary"]["POST_geometry_training_authority"] is False


def test_matrix_is_availability_metadata_and_summary_is_row_derived(
    artifacts: dict[str, bytes],
) -> None:
    rows = list(csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"))))
    assert len(rows) == 4
    assert tuple(rows[0]) == owner.MATRIX_HEADER
    assert {row["artifact_role"] for row in rows} == {
        "TASK_LABEL_AVAILABILITY_METADATA_ONLY"
    }
    assert {row["source_formal_generation_domain_decision"] for row in rows} == {
        "IN_DOMAIN"
    }
    assert {row["normalized_task_relevance_disposition"] for row in rows} == {
        "RELEVANT"
    }
    assert {row["source_formal_training_use_decision"] for row in rows} == {
        "EXCLUDE"
    }
    assert {row["normalized_training_disposition"] for row in rows} == {
        "EXCLUDE_FROM_TRAINING_ONLY"
    }
    assert {row["task_label_authority"] for row in rows} == {"false"}
    summary = json.loads(artifacts[owner.SUMMARY])
    expected = {
        "event_count": 4,
        "review_unit_count": 1,
        "chemistry_positive_count": 4,
        "task_relevant_count": 4,
        "human_training_excluded_count": 4,
        "future_training_admission_candidate_count": 0,
        "generic_exact11_fact_count": 4,
        "task_label_authority_count": 0,
        "mask_tensor_target_count": 0,
        "formal_training_admitted_count": 0,
    }
    for key, value in expected.items():
        assert summary[key] == value


def test_manifest_closure_materialized_fresh_and_deterministic(
    artifacts: dict[str, bytes],
) -> None:
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
    assert manifest["matrix_header_frozen"] is True
    assert manifest["matrix_header"] == list(owner.MATRIX_HEADER)
    assert manifest["active_source_binding_count"] == 13
    assert manifest["duplicate_source_binding_identity_count"] == 0
    assert len(manifest["candidate_source_bindings"]) == 3
    assert len(manifest["output_artifact_bindings_excluding_manifest_self"]) == 3
    assert all(
        owner.MANIFEST not in row["path"]
        for row in manifest["output_artifact_bindings_excluding_manifest_self"]
    )
    assert manifest["formal_validator_imported"] is False
    assert manifest["formal_validator_executed_by_production"] is False
    assert manifest["formal_validator_subprocessed_by_production"] is False
    assert artifacts == owner.build_artifacts_v1(REPO_ROOT)
    checked = owner.check_materialized_v1(REPO_ROOT)
    assert checked["status"] == "PASS"
    assert checked["materialized_bytes_equal_fresh_build"] is True
    assert checked["deterministic_double_build"] is True


def test_current_with_6oa_census_remains_preingestion_truth() -> None:
    census = owner.load_frozen_formal_decision_v1(REPO_ROOT)[
        "current_census_boundary"
    ]
    assert census["PYR_event_count"] == 4
    assert census["PYR_current_review_status"] == "CURRENTLY_UNREVIEWED"
    assert census["PYR_human_review_completed"] is False
    assert census["PYR_chemistry"] == "UNRESOLVED"
    assert census["PYR_task_relevance"] == "UNRESOLVED"
    assert census["PYR_training_use"] == "UNRESOLVED"
    assert census["census_modified_by_ingestion"] is False


def test_checker_independent_paths_and_real_lifecycle(
    artifacts: dict[str, bytes],
) -> None:
    checker = load_checker()
    sources = checker.independently_check_sources(REPO_ROOT)
    census = checker.independently_check_current_census(REPO_ROOT)
    independent = checker.independently_check_artifacts(REPO_ROOT, artifacts)
    lifecycle = checker.check_git_lifecycle(REPO_ROOT)
    assert sources["source_count"] == 13
    assert sources["formal_validator_executed"] is False
    assert sources["runtime_revalidation_passed"] is True
    assert census["PYR_current_review_status"] == "CURRENTLY_UNREVIEWED"
    assert independent["FORMAL_SOURCE_D2"] == "IN_DOMAIN"
    assert independent["FORMAL_SOURCE_D6"] == "EXCLUDE"
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
        assert lifecycle["git_index_expected_mode"] == "100644"


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
            ("authorization_record", "platform_identity_verification_claimed"),
            True,
            "FORMAL_AUTHORIZATION_DRIFT",
        ),
        (
            ("frozen_candidate_binding", "SHA256"),
            "0" * 64,
            "FORMAL_FROZEN_CANDIDATE_DRIFT",
        ),
        (
            ("approved_D1_D6", "D1_observed_covalent_chemistry", "decision"),
            "NEGATIVE",
            "FORMAL_D1_DRIFT",
        ),
        (
            ("approved_D1_D6", "D2_task_generation_domain_relevance", "decision"),
            "RELEVANT",
            "FORMAL_D2_DRIFT",
        ),
        (
            ("approved_D1_D6", "D3_reactive_atom_pair", "pair"),
            "SG:O3",
            "FORMAL_D3_DRIFT",
        ),
        (
            ("approved_D1_D6", "D4_role_partition_and_minimal_seed", "human_approved"),
            False,
            "FORMAL_D4_DRIFT",
        ),
        (
            ("approved_D1_D6", "D5_structural_task_applicability", "selected_task_ids"),
            [0, 4],
            "FORMAL_D5_DRIFT",
        ),
        (
            ("approved_D1_D6", "D6_later_training_use_disposition", "decision"),
            "NOT_APPLICABLE",
            "FORMAL_D6_DRIFT",
        ),
        (
            (
                "approved_D1_D6",
                "D6_later_training_use_disposition",
                "human_training_excluded",
            ),
            False,
            "FORMAL_D6_DRIFT",
        ),
        (
            ("selected_role_partition", "selected_group_W"),
            ["CB"],
            "FORMAL_SELECTED_ROLE_DRIFT",
        ),
        (
            ("selected_role_partition", "selected_boundary"),
            "CB--CA/SING",
            "FORMAL_SELECTED_ROLE_DRIFT",
        ),
        (
            ("selected_seed_and_anchor", "selected_seed_atom_ids"),
            ["C", "OXT"],
            "FORMAL_SELECTED_SEED_DRIFT",
        ),
        (
            ("selected_seed_and_anchor", "selected_primary_anchor"),
            "O",
            "FORMAL_SELECTED_SEED_DRIFT",
        ),
        (
            ("selected_task_ids", "canonical_V1_contract", "B3_present"),
            False,
            "FORMAL_SELECTED_TASKS_DRIFT",
        ),
        (
            ("unselected_alternatives", "alternative_human_selected"),
            True,
            "FORMAL_UNSELECTED_ALTERNATIVE_DRIFT",
        ),
        (
            ("unselected_alternatives", "alternate_seed_formal_selected"),
            True,
            "FORMAL_UNSELECTED_ALTERNATIVE_DRIFT",
        ),
        (
            ("non_created_authority", "task_label_authority"),
            True,
            "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
        ),
        (
            ("non_created_authority", "POST_geometry_training_authority"),
            True,
            "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
        ),
        (
            ("non_created_authority", "training_materialization_allowed"),
            True,
            "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
        ),
        (
            ("source_bindings", 1, "SHA256"),
            "0" * 64,
            "FORMAL_SOURCE_BINDINGS_DRIFT",
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


@pytest.mark.parametrize("mode", ("missing", "duplicate", "wrong"))
def test_formal_exact4_missing_duplicate_or_wrong_fails_closed(
    formal: dict[str, object], mode: str
) -> None:
    mutated = copy.deepcopy(formal)
    ids = mutated["sample_identity"]["canonical_event_ids"]
    if mode == "missing":
        ids.pop()
    elif mode == "duplicate":
        ids[-1] = ids[0]
    else:
        ids[-1] = "wrong-event"
    with assert_stage_error("FORMAL_SAMPLE_IDENTITY_DRIFT"):
        owner._validate_formal(mutated)


def test_wrong_formal_and_validator_content_identities_fail_closed(
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
            owner.load_frozen_formal_decision_v1(
                REPO_ROOT, **{keyword: bad}
            )


@pytest.mark.parametrize(
    ("path", "value", "token"),
    (
        (
            ("normalization_contract", "task_relevance", "source_formal_generation_domain_decision"),
            None,
            "SNAPSHOT_NORMALIZATION_DRIFT",
        ),
        (
            ("normalization_contract", "task_relevance", "normalized_task_relevance_disposition"),
            "NOT_RELEVANT",
            "SNAPSHOT_NORMALIZATION_DRIFT",
        ),
        (
            ("normalization_contract", "training_disposition", "source_formal_training_use_decision"),
            None,
            "SNAPSHOT_NORMALIZATION_DRIFT",
        ),
        (
            ("normalization_contract", "training_disposition", "normalized_training_disposition"),
            "NOT_APPLICABLE",
            "SNAPSHOT_NORMALIZATION_DRIFT",
        ),
        (("events", 0, "chemistry_disposition"), "NEGATIVE", "SNAPSHOT_EVENT_DRIFT"),
        (
            ("events", 0, "legacy_completed_review_status"),
            "COMPLETED_HUMAN_NEGATIVE",
            "SNAPSHOT_EVENT_DRIFT",
        ),
        (
            ("events", 0, "human_training_excluded"),
            False,
            "SNAPSHOT_EVENT_DRIFT",
        ),
        (
            ("events", 0, "task_label_authority"),
            True,
            "SNAPSHOT_EVENT_DRIFT",
        ),
        (
            ("events", 0, "PRE_source_mapping_status"),
            "AVAILABLE",
            "SNAPSHOT_EVENT_DRIFT",
        ),
        (
            ("events", 0, "POST_geometry_training_authority"),
            True,
            "SNAPSHOT_EVENT_DRIFT",
        ),
        (
            ("selected_role_partition", "warhead_atom_ids"),
            ["CB"],
            "SNAPSHOT_SELECTED_ROLE_DRIFT",
        ),
        (
            ("selected_role_partition", "minimal_seed_atom_ids"),
            ["C", "OXT"],
            "SNAPSHOT_SELECTED_ROLE_DRIFT",
        ),
        (
            ("canonical_task_contract", "B3_present"),
            False,
            "SNAPSHOT_TASK_CONTRACT_DRIFT",
        ),
        (
            ("unselected_alternatives", "alternative_authority_created"),
            True,
            "SNAPSHOT_ALTERNATIVE_DRIFT",
        ),
        (
            ("training_boundary", "future_training_admission_candidate"),
            True,
            "SNAPSHOT_TRAINING_DRIFT",
        ),
        (
            ("readiness", "TRAINING_STARTED"),
            True,
            "SNAPSHOT_READINESS_DRIFT",
        ),
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


def test_generic_rich_field_and_legacy_negative_misclassification_fail_closed(
    snapshot: dict[str, object],
) -> None:
    rich = copy.deepcopy(snapshot)
    rich["generic_Exact11_compatibility"]["facts"][0]["pair"] = "SG:CB"
    with assert_stage_error("SNAPSHOT_GENERIC_FACT_NOT_EXACT11"):
        owner._validate_snapshot_semantics(rich)
    negative = copy.deepcopy(snapshot)
    negative["generic_Exact11_compatibility"]["facts"][0][
        "legacy_completed_review_status"
    ] = "COMPLETED_HUMAN_NEGATIVE"
    with assert_stage_error("SNAPSHOT_GENERIC_FACT_DRIFT"):
        owner._validate_snapshot_semantics(negative)


def test_generic_owner_accepts_exact_positive_exclusion_and_rejects_negative() -> None:
    binding = generic.SourceBinding(
        source_path=owner.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=17975,
        sha256=owner.FORMAL_BINDINGS[0][3],
        schema_version=owner.FORMAL_DECISION_SCHEMA,
        review_unit_id=owner.EXPECTED_REVIEW_UNIT_ID,
    )
    base = {
        "canonical_event_id": owner.EXPECTED_EVENT_IDS[0],
        "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
        "human_review_completed": True,
        "legacy_completed_review_status": "COMPLETED_HUMAN_POSITIVE",
        "task_relevance_disposition": "RELEVANT",
        "chemistry_disposition": "POSITIVE",
        "training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "human_training_excluded": True,
        "source_decision_schema": owner.FORMAL_DECISION_SCHEMA,
        "source_decision_sha256": owner.FORMAL_BINDINGS[0][3],
        "source_binding_path": owner.FORMAL_DECISION_RELATIVE.as_posix(),
    }
    fact = generic.NormalizedCompletedDecisionFact(**base)
    assert tuple(field.name for field in fields(fact)) == owner.GENERIC_FACT_FIELDS
    generic._validate_fact(fact, binding)
    wrong = generic.NormalizedCompletedDecisionFact(
        **{**base, "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE"}
    )
    with pytest.raises(
        generic.CompletedDecisionReconciliationError,
        match="^POSITIVE_REVIEW_DISPOSITION_INVALID:",
    ):
        generic._validate_fact(wrong, binding)


def test_manifest_source_and_output_drift_fail_closed(
    artifacts: dict[str, bytes],
) -> None:
    for path, token in (
        (("active_source_bindings", 0, "SHA256"), "MANIFEST_ACTIVE_SOURCE_BINDINGS_DRIFT"),
        (("candidate_source_bindings", 0, "SHA256"), "MANIFEST_CANDIDATE_SOURCE_BINDINGS_DRIFT"),
        (
            ("output_artifact_bindings_excluding_manifest_self", 0, "SHA256"),
            "MANIFEST_OUTPUT_BINDINGS_DRIFT",
        ),
    ):
        manifest = json.loads(artifacts[owner.MANIFEST])
        mutate_path(manifest, path, "0" * 64)
        with assert_stage_error(token):
            owner._validate_manifest_semantics(manifest, REPO_ROOT, artifacts)


def test_raw_byte_comparator_uses_normal_materialized_fresh_path(
    artifacts: dict[str, bytes],
) -> None:
    mutated = dict(artifacts)
    snapshot = json.loads(mutated[owner.SNAPSHOT])
    reordered = (
        json.dumps(snapshot, ensure_ascii=False, sort_keys=False, indent=1).encode("utf-8")
        + b"\n"
    )
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


def test_current_census_semantic_mutation_fails_closed() -> None:
    payloads = {
        relative: (REPO_ROOT / relative).read_bytes()
        for relative in (
            owner.CENSUS_MATRIX_RELATIVE,
            owner.CENSUS_SUMMARY_RELATIVE,
            owner.CENSUS_MANIFEST_RELATIVE,
        )
    }
    rows = owner._parse_csv(payloads[owner.CENSUS_MATRIX_RELATIVE], "TEST_CENSUS")
    target = next(row for row in rows if row["scaleup_rank"] == "46")
    target["current_review_status"] = "COMPLETED_HUMAN_POSITIVE"
    payloads[owner.CENSUS_MATRIX_RELATIVE] = csv_bytes(rows, list(rows[0]))
    with assert_stage_error("CURRENT_CENSUS_PYR_PRIOR_STATE_DRIFT:"):
        owner._current_census(payloads)


def test_git_index_parser_accepts_exact_stage0_100644_and_rejects_drifts() -> None:
    checker = load_checker()
    paths = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    valid = "\n".join(
        f"100644 {'0' * 40} 0\t{path}" for path in paths
    )
    parsed = checker.parse_exact7_index_records(valid, paths)
    assert len(parsed) == 7
    assert {row["mode"] for row in parsed} == {"100644"}
    probes = (
        ("\n".join(valid.splitlines()[:-1]), "RECORD_COUNT_NOT_EXACT7"),
        (valid.replace(paths[-1], paths[0]), "DUPLICATE_PATH"),
        (valid.replace("100644", "100755", 1), "MODE_NOT_100644"),
        (valid.replace("100644", "120000", 1), "MODE_NOT_100644"),
        (valid.replace(" 0\t", " 1\t", 1), "NONZERO_STAGE"),
    )
    for payload, token in probes:
        with pytest.raises(
            RuntimeError,
            match="^COVAPIE_PYR_INGESTION_CHECK_V1_ERROR:"
            "TRACKED_CLEAN_GIT_INDEX_" + token,
        ):
            checker.parse_exact7_index_records(payload, paths)


def test_real_lifecycle_rejects_unauthorized_eighth_untracked_file() -> None:
    checker = load_checker()
    rogue = REPO_ROOT / "pyr_ingestion_unauthorized_eighth_file.txt"
    assert not rogue.exists()
    try:
        rogue.write_text("negative probe\n", encoding="utf-8")
        with pytest.raises(
            RuntimeError,
            match="^COVAPIE_PYR_INGESTION_CHECK_V1_ERROR:"
            "ORDINARY_UNTRACKED_NOT_EXACT7_OR_EMPTY$",
        ):
            checker.check_git_lifecycle(REPO_ROOT)
    finally:
        rogue.unlink(missing_ok=True)
