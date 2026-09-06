from __future__ import annotations

import ast
import copy
import csv
import importlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as generic,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


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
    spec = importlib.util.spec_from_file_location("check_6oa_ingestion_v1", REPO_ROOT / owner.CHECKER_RELATIVE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mutate_path(document: dict[str, object], path: tuple[object, ...], value: object) -> None:
    cursor: object = document
    for part in path[:-1]:
        cursor = cursor[part]  # type: ignore[index]
    cursor[path[-1]] = value  # type: ignore[index]


def csv_bytes(rows: list[dict[str, str]], header: tuple[str, ...] | list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def test_public_api_and_exact7_inventory() -> None:
    assert owner.__all__ == (
        "SixOAIngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )
    assert len(owner.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(owner.CANDIDATE_PUBLICATION_PATHS)) == 7
    assert owner.OUTPUT_FILENAMES == (
        "covapie_6oa_completed_human_decision_snapshot_v1.json",
        "covapie_6oa_event_task_label_availability_v1.csv",
        "covapie_6oa_completed_decision_ingestion_summary_v1.json",
        "covapie_6oa_completed_decision_ingestion_manifest_v1.json",
    )


def test_frozen_sources_and_active_binding_set_are_exact() -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert bound["active_source_binding_count"] == 13
    bindings = bound["active_source_bindings"]
    assert len(bindings) == 13
    assert len({row["semantic_source_identity"] for row in bindings}) == 13
    assert bound["formal_decision_binding"]["byte_count"] == 33043
    assert bound["formal_decision_binding"]["SHA256"] == (
        "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218"
    )
    assert bound["formal_validator_binding"]["byte_count"] == 96246
    assert bound["formal_validator_binding"]["SHA256"] == (
        "77800ac2056df2b0770967be15bb89c67d2be089d6c54180361f4922ee73731e"
    )


def test_formal_validator_is_identity_only_and_never_an_executable_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "subprocess" not in imported
    observed: list[str] = []
    original = importlib.import_module

    def guarded(name: str, package: str | None = None):
        assert "validate_6oa_formal_human_decision_v1" not in name
        observed.append(name)
        return original(name, package)

    monkeypatch.setattr(owner.importlib, "import_module", guarded)
    owner.load_frozen_formal_decision_v1(REPO_ROOT)
    assert set(observed) == {
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1",
        "covalent_ext.covapie_completed_human_decision_reconciliation_v1",
    }


def test_exact4_normalization_lane_and_generic_exact11(snapshot: dict[str, object]) -> None:
    assert snapshot["task_relevance_normalization"] == {
        "source_field": "D2_task_generation_domain_relevance",
        "source_formal_generation_domain_decision": "OUT_OF_DOMAIN",
        "target_field": "task_relevance_disposition",
        "normalized_task_relevance_disposition": "NOT_RELEVANT",
        "mapping": "OUT_OF_DOMAIN_TO_NOT_RELEVANT",
        "direction": "FORMAL_SOURCE_TO_GENERIC_RECONCILIATION_VOCABULARY",
        "source_value_preserved": True,
        "chemistry_disposition_changed_by_normalization": False,
        "training_exclusion_created_by_normalization": False,
    }
    assert snapshot["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
    assert snapshot["legacy_completed_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
    generic_block = snapshot["generic_Exact11_compatibility"]
    assert generic_block["accepted_fact_count"] == 4
    assert generic_block["rich_fields_leaked"] is False
    assert generic_block["NormalizedDecisionSource_constructed"] is True
    for fact in generic_block["facts"]:
        assert set(fact) == set(owner.GENERIC_FACT_FIELDS)
        assert fact["task_relevance_disposition"] == "NOT_RELEVANT"
        assert fact["chemistry_disposition"] == "POSITIVE"
        assert fact["training_disposition"] == "NOT_APPLICABLE"
        assert fact["human_training_excluded"] is False


def test_pair_role_seed_tasks_and_runtime_are_sample_authority(
    snapshot: dict[str, object],
) -> None:
    assert snapshot["reactive_pair_authority"] == {
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C5",
        "observed_pair": "SG:C5",
        "scope": owner.EXPECTED_SCOPE,
        "sample_level_authoritative": True,
        "reusable_pair_authority": False,
        "ligand_wide_authority": False,
        "cross_structure_generalization": False,
    }
    role = snapshot["selected_role_partition"]
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["warhead_atom_ids"] == ["C5", "O3"]
    assert role["linker_atom_ids"] == []
    assert role["scaffold_atom_ids"] == ["C", "C1", "C2", "C3", "C4", "O", "O1", "O2"]
    assert role["boundary"] == {
        "scaffold_atom_id": "C4",
        "warhead_atom_id": "C5",
        "bond_order": "SING",
    }
    assert role["minimal_seed_atom_ids"] == ["C3", "C4"]
    assert role["primary_anchor"] == "C4"
    runtime = role["published_runtime_validation"]
    assert runtime["valid"] is True
    assert runtime["applicable_task_ids"] == [0, 3, 4]
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


def test_geometry_pre_and_training_boundaries(snapshot: dict[str, object]) -> None:
    events = snapshot["events"]
    assert [(row["scaleup_rank"], row["POST_distance_frozen_lexeme"]) for row in events] == [
        (855, "1.853206"),
        (856, "1.674652"),
        (857, "1.347977"),
        (858, "1.677347"),
    ]
    outlier = events[2]
    assert outlier["geometry_outlier"] is True
    assert outlier["distance_normalized"] is False
    assert outlier["event_removed"] is False
    assert outlier["new_bond_order_inferred"] is False
    for event in events:
        assert event["POST_source_evidence_available"] is True
        assert event["explicit_covalent_evidence"] is True
        assert event["POST_geometry_training_authority"] is False
        assert event["supporting_adduct_source_graph_count"] == 0
        assert event["candidate_PRE_free_source_graph_count"] == 0
        assert event["mapping_count"] == 0
        assert event["PRE_source_mapping_status"] == "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
        assert event["final_PRE_reaction_status"] == "PRE_REACTION_UNRESOLVED"
        assert event["formal_event_training_use_decision"] == "NOT_APPLICABLE"
        assert event["human_training_excluded"] is False
        assert event["future_training_admission_candidate"] is False
        assert event["training_materialization_allowed"] is False
        assert event["model_supervision_usable"] is False
    assert snapshot["PRE_boundary"]["C5_O3_free_precursor_double_bond_authority"] is False
    assert snapshot["PRE_boundary"]["2VS_substituted_for_sample_specific_PRE"] is False
    assert snapshot["POST_boundary"]["POST_geometry_training_target_created"] is False


def test_matrix_preserves_source_and_normalized_vocabularies(
    artifacts: dict[str, bytes],
) -> None:
    rows = list(csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"))))
    assert len(rows) == 4
    assert tuple(rows[0]) == owner.MATRIX_HEADER
    assert "source_formal_generation_domain_decision" in owner.MATRIX_HEADER
    assert "normalized_task_relevance_disposition" in owner.MATRIX_HEADER
    assert {row["source_formal_generation_domain_decision"] for row in rows} == {"OUT_OF_DOMAIN"}
    assert {row["normalized_task_relevance_disposition"] for row in rows} == {"NOT_RELEVANT"}


def test_summary_counts_and_operation_boundary(artifacts: dict[str, bytes]) -> None:
    summary = json.loads(artifacts[owner.SUMMARY])
    assert summary["event_count"] == 4
    assert summary["completed_review_unit_count"] == 1
    assert summary["task_not_relevant_count"] == 4
    assert summary["chemistry_positive_count"] == 4
    assert summary["negative_chemistry_count"] == 0
    assert summary["pair_authority_event_count"] == 4
    assert summary["role_authority_event_count"] == 4
    assert summary["task_applicability_determined_event_count"] == 4
    assert summary["authoritative_task_label_event_count"] == 0
    assert summary["event_task_label_rows_materialized_count"] == 0
    assert summary["mask_tensor_target_count"] == 0
    assert summary["training_NOT_APPLICABLE_event_count"] == 4
    assert summary["human_training_excluded_count"] == 0
    assert summary["future_training_admission_candidate_count"] == 0
    assert summary["formal_training_admitted_count"] == 0
    assert summary["PRE_authority_count"] == 0
    assert summary["POST_training_authority_count"] == 0
    assert summary["generic_exact11_accepted_count"] == 4
    assert all(
        value is False
        for key, value in summary["operation_boundary"].items()
        if key != "metadata_only_ingestion"
    )


def test_manifest_closure_and_no_self_hash(artifacts: dict[str, bytes]) -> None:
    manifest = json.loads(artifacts[owner.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["output_artifact_count"] == 4
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


def test_materialized_is_fresh_and_build_is_deterministic(
    artifacts: dict[str, bytes],
) -> None:
    assert artifacts == owner.build_artifacts_v1(REPO_ROOT)
    checked = owner.check_materialized_v1(REPO_ROOT)
    assert checked["status"] == "PASS"
    assert checked["materialized_bytes_equal_fresh_build"] is True
    assert checked["deterministic_double_build"] is True


def test_current_with_nwj_census_is_unchanged_preingestion_truth() -> None:
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    census = bound["current_census_boundary"]
    assert census["6OA_event_count"] == 4
    assert census["6OA_current_review_status"] == "CURRENTLY_UNREVIEWED"
    assert census["6OA_human_review_completed"] is False
    assert census["6OA_chemistry"] == "UNRESOLVED"
    assert census["6OA_task_relevance"] == "UNRESOLVED"
    assert census["6OA_training_use"] == "UNRESOLVED"
    assert census["current_pending_rank"] == 1
    assert census["census_modified_by_ingestion"] is False


def test_checker_independently_validates_and_real_lifecycle_is_supported(
    artifacts: dict[str, bytes],
) -> None:
    checker = load_checker()
    sources = checker.independently_check_sources(REPO_ROOT)
    census = checker.independently_check_current_census(REPO_ROOT)
    result = checker.independently_check_artifacts(REPO_ROOT, artifacts)
    lifecycle = checker.check_git_lifecycle(REPO_ROOT)
    assert sources["source_count"] == 13
    assert census["current_pending_rank"] == 1
    assert result["FORMAL_SOURCE_D2"] == "OUT_OF_DOMAIN"
    assert result["NORMALIZED_TASK_RELEVANCE"] == "NOT_RELEVANT"
    assert lifecycle["profile"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("formal_state", "authorization_origin"), "MACHINE"),
        (("formal_state", "reviewer_id"), "other"),
        (("formal_state", "attestor_id"), "other"),
        (("human_authorization", "candidate_binding", "SHA256"), "0" * 64),
        (("external_human_decision_input", "D2_task_generation_domain_relevance"), None),
        (("formal_decisions", "D2_task_generation_domain_relevance", "decision"), "NOT_RELEVANT"),
        (("formal_decisions", "D1_observed_covalent_chemistry", "decision"), "NEGATIVE"),
        (("formal_decisions", "D3_reactive_atom_pair_confirmation_or_revision", "ligand_reactive_atom"), "O3"),
        (("formal_decisions", "D4_role_partition_and_minimal_seed", "role_profile"), "STRICT_LINKER_PRESENT_V1"),
        (("selected_role_context", "warhead_atom_ids"), ["C5"]),
        (("selected_role_context", "linker_atom_ids"), ["C4"]),
        (("selected_role_context", "scaffold_atom_ids"), ["C", "C1"]),
        (("selected_role_context", "boundary"), "C3--C5/SING"),
        (("selected_role_context", "minimal_seed", "atom_ids"), ["C4"]),
        (("selected_role_context", "minimal_seed", "primary_scaffold_side_anchor"), "C3"),
        (("selected_role_context", "task_ids"), [0, 4]),
        (("canonical_Exact5", "B3_present"), False),
        (("canonical_Exact5", "sixth_task"), True),
        (("formal_decisions", "D6_later_training_use_disposition", "decision"), "EXCLUDE_FROM_TRAINING_ONLY"),
        (("training_boundary", "future_training_admission_candidate"), True),
        (("canonical_Exact5", "task_label_authority"), True),
        (("geometry_boundary", "events", 2, "geometry_outlier"), False),
        (("geometry_boundary", "events", 2, "exact_POST_distance_angstrom"), 1.8),
        (("geometry_boundary", "rank857_caveat", "event_removed"), True),
        (("PRE_boundary", "candidate_PRE_free_source_graph_count_per_event"), 1),
        (("PRE_boundary", "POST_to_PRE_copy"), True),
        (("PRE_boundary", "C5_O3_free_precursor_double_bond_authority"), True),
        (("PRE_boundary", "2VS_substituted_for_6OA_PRE"), True),
        (("same_enzyme_2VS_precedent_boundary", "2VS_authority_applies_to_6OA"), True),
        (("reusable_authority_map", "reaction_family_authority"), True),
        (("readiness", "PARAMETER_UPDATE_AUTHORIZATION"), True),
    ),
)
def test_formal_semantic_mutations_fail_closed(
    formal: dict[str, object], path: tuple[object, ...], value: object
) -> None:
    mutated = copy.deepcopy(formal)
    mutate_path(mutated, path, value)
    with pytest.raises(owner.SixOAIngestionSafetyError):
        owner._validate_formal(mutated)


def test_formal_missing_duplicate_and_wrong_exact4_fail_closed(
    formal: dict[str, object],
) -> None:
    for mode in ("missing", "duplicate", "wrong"):
        mutated = copy.deepcopy(formal)
        ids = mutated["sample_identity"]["canonical_event_ids"]
        if mode == "missing":
            ids.pop()
        elif mode == "duplicate":
            ids[-1] = ids[0]
        else:
            ids[-1] = "wrong-event"
        with pytest.raises(owner.SixOAIngestionSafetyError):
            owner._validate_formal(mutated)


def test_wrong_formal_and_validator_identities_fail_closed(tmp_path: Path) -> None:
    for relative, keyword in (
        (owner.FORMAL_DECISION_RELATIVE, "formal_decision_path"),
        (owner.FORMAL_VALIDATOR_RELATIVE, "formal_validator_path"),
    ):
        source = REPO_ROOT.parent / relative
        bad = tmp_path / source.name
        bad.write_bytes(source.read_bytes() + b"\n")
        with pytest.raises(owner.SixOAIngestionSafetyError, match="SOURCE_BINDING_FAILED"):
            owner.load_frozen_formal_decision_v1(REPO_ROOT, **{keyword: bad})


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("task_relevance_normalization", "source_formal_generation_domain_decision"), None),
        (("task_relevance_normalization", "normalized_task_relevance_disposition"), "RELEVANT"),
        (("events", 0, "chemistry_disposition"), "NEGATIVE"),
        (("events", 0, "legacy_completed_review_status"), "COMPLETED_HUMAN_POSITIVE"),
        (("events", 0, "formal_event_training_use_decision"), "EXCLUDE_FROM_TRAINING_ONLY"),
        (("events", 0, "human_training_excluded"), True),
        (("events", 0, "future_training_admission_candidate"), True),
        (("events", 0, "task_label_authority"), True),
        (("events", 2, "geometry_outlier"), False),
        (("events", 2, "POST_distance_frozen_lexeme"), "1.800000"),
        (("events", 2, "event_removed"), True),
        (("events", 0, "POST_geometry_training_authority"), True),
        (("events", 0, "PRE_source_mapping_status"), "AVAILABLE"),
        (("selected_role_partition", "warhead_atom_ids"), ["C5"]),
        (("selected_role_partition", "boundary", "scaffold_atom_id"), "C3"),
        (("selected_role_partition", "minimal_seed_atom_ids"), ["C4"]),
        (("selected_role_partition", "primary_anchor"), "C3"),
        (("canonical_task_contract", "B3_present"), False),
        (("canonical_task_contract", "sixth_task"), True),
        (("canonical_task_contract", "sample_applicable_task_ids"), [0, 4]),
        (("PRE_boundary", "candidate_PRE_free_source_graph_count_per_event"), 1),
        (("POST_boundary", "POST_geometry_training_authority"), True),
        (("reusable_authority_boundary", "2VS_authority_extended_to_6OA"), True),
        (("reusable_authority_boundary", "reaction_family_authority"), True),
        (("training_boundary", "parameter_update_authorization"), True),
        (("readiness", "TRAINING_STARTED"), True),
    ),
)
def test_snapshot_semantic_mutations_fail_closed(
    snapshot: dict[str, object], path: tuple[object, ...], value: object
) -> None:
    mutated = copy.deepcopy(snapshot)
    mutate_path(mutated, path, value)
    with pytest.raises(owner.SixOAIngestionSafetyError):
        owner._validate_snapshot_semantics(mutated)


def test_generic_owner_rejects_wrong_task_domain_negative_projection() -> None:
    binding = generic.SourceBinding(
        source_path=owner.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=33043,
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
    for key, value in (
        ("legacy_completed_review_status", "COMPLETED_HUMAN_POSITIVE"),
        ("task_relevance_disposition", "RELEVANT"),
        ("training_disposition", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("human_training_excluded", True),
    ):
        mutated = {**base, key: value}
        fact = generic.NormalizedCompletedDecisionFact(**mutated)
        with pytest.raises(generic.CompletedDecisionReconciliationError):
            generic._validate_fact(fact, binding)


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
    target = next(row for row in rows if row["scaleup_rank"] == "855")
    target["current_review_status"] = "COMPLETED_HUMAN_NEGATIVE"
    payloads[owner.CENSUS_MATRIX_RELATIVE] = csv_bytes(rows, list(rows[0]))
    with pytest.raises(owner.SixOAIngestionSafetyError, match="CURRENT_CENSUS"):
        owner._current_census(payloads)


def test_manifest_candidate_source_sha_drift_and_eighth_file_fail_closed(
    artifacts: dict[str, bytes],
) -> None:
    manifest = json.loads(artifacts[owner.MANIFEST])
    manifest["candidate_source_bindings"][0]["SHA256"] = "0" * 64
    with pytest.raises(owner.SixOAIngestionSafetyError, match="CANDIDATE_SOURCE"):
        owner._validate_manifest_semantics(manifest, REPO_ROOT, artifacts)

    checker = load_checker()
    rogue = REPO_ROOT / "6oa_ingestion_unauthorized_eighth_file.txt"
    assert not rogue.exists()
    try:
        rogue.write_text("negative probe\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="ORDINARY_UNTRACKED_NOT_EXACT7_OR_EMPTY"):
            checker.check_git_lifecycle(REPO_ROOT)
    finally:
        rogue.unlink(missing_ok=True)


def test_owner_and_checker_reject_artifact_tamper(
    artifacts: dict[str, bytes],
) -> None:
    checker = load_checker()
    for name, path, value in (
        (
            owner.SNAPSHOT,
            ("task_relevance_normalization", "normalized_task_relevance_disposition"),
            "RELEVANT",
        ),
        (owner.SNAPSHOT, ("events", 2, "geometry_outlier"), False),
        (owner.SUMMARY, ("generic_exact11_accepted_count",), 3),
        (owner.MANIFEST, ("active_source_bindings", 0, "SHA256"), "0" * 64),
    ):
        mutated = dict(artifacts)
        document = json.loads(mutated[name])
        mutate_path(document, path, value)
        mutated[name] = owner._json_bytes(document)
        with pytest.raises(owner.SixOAIngestionSafetyError):
            owner.validate_completed_decision_projection_v1(mutated, REPO_ROOT)
        with pytest.raises(RuntimeError):
            checker.independently_check_artifacts(REPO_ROOT, mutated)
