from __future__ import annotations

import ast
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import stat
import sys

import pytest

from covalent_ext import (
    covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / subject.CHECKER_RELATIVE
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "four_m5_ingestion_checker", CHECKER_PATH
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _formal() -> dict[str, object]:
    return copy.deepcopy(subject.load_frozen_formal_decision_v1(ROOT)["formal"])


def _set_path(document: object, path: tuple[object, ...], value: object) -> None:
    current = document
    for key in path[:-1]:
        current = current[key]  # type: ignore[index]
    current[path[-1]] = value  # type: ignore[index]


def _mutated_formal(
    path: tuple[object, ...], value: object, *, refresh_digest: bool = True
) -> dict[str, object]:
    document = _formal()
    _set_path(document, path, value)
    if refresh_digest:
        clone = copy.deepcopy(document)
        clone.pop("formal_semantic_canonical_sha256", None)
        document["formal_semantic_canonical_sha256"] = subject._sha256(
            subject._canonical_json(clone)
        )
    return document


def _mutated_json_artifact(
    artifacts: dict[str, bytes],
    name: str,
    path: tuple[object, ...],
    value: object,
) -> dict[str, bytes]:
    mutated = dict(artifacts)
    document = json.loads(mutated[name])
    _set_path(document, path, value)
    mutated[name] = subject._json_bytes(document)
    return mutated


def _mutated_matrix_artifact(
    artifacts: dict[str, bytes], row_index: int, field: str, value: str
) -> dict[str, bytes]:
    mutated = dict(artifacts)
    rows = list(
        csv.DictReader(io.StringIO(mutated[subject.MATRIX].decode("utf-8")))
    )
    rows[row_index][field] = value
    mutated[subject.MATRIX] = subject._csv_bytes(subject.MATRIX_HEADER, rows)
    return mutated


def _expected_paths() -> tuple[str, ...]:
    return tuple(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)


def test_public_api_is_exact6() -> None:
    assert subject.__all__ == (
        "FourM5IngestionSafetyError",
        "load_frozen_formal_decision_v1",
        "validate_completed_decision_projection_v1",
        "build_artifacts_v1",
        "materialize_artifacts_v1",
        "check_materialized_v1",
    )


def test_schema_versions_and_exact7_inventory_are_exact() -> None:
    assert subject.SCHEMA_VERSION == (
        "covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1"
    )
    assert subject.SNAPSHOT_SCHEMA_VERSION == (
        "covapie_4m5_completed_human_decision_snapshot_v1"
    )
    assert subject.MATRIX_SCHEMA_VERSION == (
        "covapie_4m5_event_task_label_availability_v1"
    )
    assert subject.SUMMARY_SCHEMA_VERSION == (
        "covapie_4m5_completed_decision_ingestion_summary_v1"
    )
    assert subject.MANIFEST_SCHEMA_VERSION == (
        "covapie_4m5_completed_decision_ingestion_manifest_v1"
    )
    assert len(subject.CANDIDATE_PUBLICATION_PATHS) == 7
    assert len(set(subject.CANDIDATE_PUBLICATION_PATHS)) == 7


def test_frozen_formal_json_validator_and_semantic_digest_are_bound() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    assert bound["formal_decision_binding"] == {
        "path": subject.FORMAL_DECISION_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 29089,
        "SHA256": "5e37540220ac44b281b20bfb796f5c2994d0ab402fb5f65acc03fb6f6b1febfb",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "FOUR_M5_FROZEN_FORMAL_HUMAN_DECISION",
    }
    assert bound["formal_validator_binding"] == {
        "path": subject.FORMAL_VALIDATOR_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 56100,
        "SHA256": "098b0d783dc098632ebd7d67a4e3d74f9f61f96452c50b2e8d3cc14057bd3d84",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": (
            "FOUR_M5_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY"
        ),
    }
    formal = bound["formal"]
    assert (
        formal["formal_semantic_canonical_sha256"]
        == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    )
    assert (
        subject._semantic_digest(formal)
        == subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    )
    assert bound["formal_semantics_independently_validated"] is True


def test_human_authorization_d1_d6_and_provenance_are_exact() -> None:
    formal = _formal()
    human = formal["human_authorization"]
    assert human["reviewer_id"] == human["attestor_id"] == "fmx"
    assert human["authorization_origin"] == "EXTERNAL_HUMAN_CHAT_AUTHORIZATION"
    assert human["formal_decision_authority_is_human"] is True
    assert human["human_choices_externally_authorized"] is True
    assert human["machine_approval_claimed"] is False
    assert human["machine_scientific_authority_created"] is False
    assert [
        human["D1_task_relevance"],
        human["D2_chemistry"],
        human["D3_reactive_pair"],
        human["D4_role_candidate"],
        human["D5_training_use"],
    ] == [
        "RELEVANT", "POSITIVE", "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_0", "INCLUDE",
    ]
    context = formal["human_approved_context"]
    assert context["D6_scientific_context"] == subject.EXPECTED_D6
    assert len(subject.EXPECTED_D6.encode("utf-8")) == 699
    assert subject._sha256(subject.EXPECTED_D6.encode("utf-8")) == (
        "21d0c0558174f2da548a1430333b639da273399bd020d2a64cde8a8e1511a254"
    )


@pytest.mark.parametrize(
    "payload",
    (
        b'\xef\xbb\xbf{"x":1}',
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b'[]',
    ),
)
def test_strict_json_rejects_bom_duplicate_nonfinite_and_nonobject(
    payload: bytes,
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._strict_json_loads(payload, "TAMPER")


@pytest.mark.parametrize(
    "field", ("human_authored_free_text", "machine_generated_token")
)
def test_ambiguous_legacy_formal_fields_fail_closed(field: str) -> None:
    formal = _formal()
    formal["human_approved_context"][field] = "forbidden"
    with pytest.raises(
        subject.FourM5IngestionSafetyError,
        match="AMBIGUOUS_PROVENANCE_FIELD",
    ):
        subject._validate_formal_document(formal)


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("human_authorization", "D1_task_relevance"), "NOT_RELEVANT"),
        (("human_authorization", "D2_chemistry"), "NEGATIVE"),
        (("human_authorization", "D3_reactive_pair"), "REJECT_OBSERVED_PAIR"),
        (("human_authorization", "D4_role_candidate"), "SELECT_CANDIDATE_1"),
        (("human_authorization", "D5_training_use"), "EXCLUDE"),
        (("human_authorization", "D6_scientific_context"), "changed"),
    ),
)
def test_d1_through_d6_mutation_fails_even_with_refreshed_digest(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("identity", "canonical_event_ids"), list(subject.EXPECTED_EVENT_IDS[:-1])),
        (
            ("identity", "canonical_event_ids"),
            [*subject.EXPECTED_EVENT_IDS[:-1], subject.EXPECTED_EVENT_IDS[0]],
        ),
        (
            ("identity", "canonical_event_ids"),
            [*subject.EXPECTED_EVENT_IDS, "unexpected"],
        ),
        (("identity", "scaleup_ranks", 0), 972),
        (("identity", "contexts_collapsed"), True),
        (("context_preservation", "contexts", 0, "protein_context"), "wrong"),
        (("event_level_formal_human_decisions", 0, "canonical_event_id"), "wrong"),
        (("event_level_formal_human_decisions", 0, "protein_reactive_atom"), "CB"),
        (("event_level_formal_human_decisions", 0, "ligand_reactive_atom"), "C14"),
    ),
)
def test_exact4_missing_duplicate_extra_rank_context_and_pair_mutations_fail(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


def test_exact4_pair_scope_and_contexts_are_exact() -> None:
    formal = _formal()
    identity = formal["identity"]
    assert identity["canonical_event_ids"] == list(subject.EXPECTED_EVENT_IDS)
    assert identity["scaleup_ranks"] == [973, 974, 975, 976]
    assert len(set(identity["canonical_event_ids"])) == 4
    assert identity["contexts_collapsed"] is False
    contexts = formal["context_preservation"]["contexts"]
    assert [
        (
            row["pdb_id"], row["protein_context"], row["cys_residue"],
            row["event_count"],
        )
        for row in contexts
    ] == [
        ("5AZT", "PPARalpha", "Cys275", 2),
        ("5AZV", "PPARgamma", "Cys285", 2),
    ]
    pair = formal["reactive_pair_authority"]
    assert pair["protein_reactive_atom"] == "SG"
    assert pair["ligand_reactive_atom"] == "C15"
    assert pair["authority_scope"] == subject.PAIR_AUTHORITY_SCOPE


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("reactive_pair_authority", "authority_scope"), "ALL_4M5"),
        (
            (
                "reactive_pair_authority",
                "cross_structure_regiochemistry_generalization",
            ),
            True,
        ),
        (("reactive_pair_authority", "all_4M5_uses_C15_authority_created"), True),
        (
            (
                "reactive_pair_authority",
                "all_17_oxoDHA_uses_C15_authority_created",
            ),
            True,
        ),
        (
            (
                "reactive_pair_authority",
                "all_PPAR_17_oxoDHA_pairs_use_C15_authority_created",
            ),
            True,
        ),
        (("reactive_pair_authority", "reusable_pair_rule_created"), True),
    ),
)
def test_pair_scope_widening_fails_closed(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("selected_role_partition", "W", 0), "C14"),
        (("selected_role_partition", "L"), ["C14"]),
        (("selected_role_partition", "S", 0), "C99"),
        (("selected_role_partition", "boundary_bonds", 0, "atom_id_1"), "C13"),
        (("selected_role_partition", "selected_candidate_index_0based"), 1),
        (("selected_role_partition", "role_profile"), "STRICT_LINKER_PRESENT_V1"),
        (
            ("selected_role_partition", "independent_structural_validation", "W_connected"),
            False,
        ),
    ),
)
def test_candidate0_w_l_s_boundary_and_connectivity_mutations_fail(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


def test_bound_graph_independent_exact25_and_direct_runtime_validation() -> None:
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    assert bound["structural_graph_binding"]["byte_count"] == 42741
    assert bound["structural_validation"] == {
        "Exact25_count": 25,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "missing_atom_ids": [],
        "extra_atom_ids": [],
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "C15_in_W": True,
        "boundary": "C14-C15 SING S-W",
    }
    runtime = bound["published_DIRECT_runtime_validation"]
    assert runtime["validator"] == "validate_role_profile_v1"
    assert runtime["valid"] is True
    assert runtime["reasons"] == []
    assert runtime["applicable_task_ids"] == [0, 3, 4]
    assert runtime["direct_scaffold_warhead_boundary"] == {
        "scaffold_atom_id": "C14",
        "warhead_atom_id": "C15",
        "bond_order": "SING",
        "boundary_valid": True,
    }


def test_global_exact5_b3_no_sixth_and_applicability_are_exact() -> None:
    tasks = _formal()["canonical_Exact5_and_sample_applicability"]
    assert [row["task_id"] for row in tasks["global_canonical_Exact5"]] == [
        0, 1, 2, 3, 4,
    ]
    assert [row["semantic_name"] for row in tasks["global_canonical_Exact5"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_present"] is False
    assert tasks["sample_applicable_task_ids"] == [0, 3, 4]
    assert tasks["sample_not_applicable_tasks"] == [
        {
            "reason": "not_applicable_empty_linker_redundant_with_A",
            "semantic_name": "linker_plus_warhead",
            "task_id": 1,
        },
        {
            "reason": "not_applicable_empty_non_C_fixed_context",
            "semantic_name": "scaffold_plus_warhead",
            "task_id": 2,
        },
    ]
    assert tasks["authoritative_task_labels_created"] is False
    assert tasks["event_task_label_rows_materialized"] is False


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("canonical_Exact5_and_sample_applicability", "B3_present"), False),
        (("canonical_Exact5_and_sample_applicability", "sixth_task_present"), True),
        (
            ("canonical_Exact5_and_sample_applicability", "global_canonical_task_count"),
            6,
        ),
        (
            ("canonical_Exact5_and_sample_applicability", "sample_applicable_task_ids"),
            [0, 4],
        ),
        (
            (
                "canonical_Exact5_and_sample_applicability",
                "authoritative_task_labels_created",
            ),
            True,
        ),
        (
            (
                "canonical_Exact5_and_sample_applicability",
                "event_task_label_rows_materialized",
            ),
            True,
        ),
    ),
)
def test_exact5_and_task_label_boundary_mutations_fail(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


def test_pre_source_graph_present_mapping_incompatible_boundary_is_exact() -> None:
    pre = _formal()["PRE_POST_boundary"]
    assert pre == {
        "POST_to_PRE_copy_performed": False,
        "PRE_coordinates_authority": False,
        "PRE_geometry_authority": False,
        "PRE_mapping_count_per_event": 0,
        "PRE_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "PRE_reconstruction_performed": False,
        "PRE_source_graph_count_per_event": 1,
        "PRE_source_graph_present": True,
        "PRE_status": "PRE_REACTION_UNRESOLVED",
        "PRE_topology_authority": False,
        "PRE_zero_fill_performed": False,
        "leaving_group_inferred": False,
        "pre_reaction_bond_edit_inferred": False,
        "reagent_inferred": False,
        "supporting_PRE_source_graph_count_per_event": 1,
    }


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("PRE_POST_boundary", "PRE_source_graph_present"), False),
        (("PRE_POST_boundary", "PRE_source_graph_count_per_event"), 0),
        (("PRE_POST_boundary", "supporting_PRE_source_graph_count_per_event"), 0),
        (("PRE_POST_boundary", "PRE_mapping_count_per_event"), 1),
        (("PRE_POST_boundary", "PRE_mapping_status"), "MAPPED"),
        (("PRE_POST_boundary", "PRE_status"), "READY"),
        (("PRE_POST_boundary", "PRE_topology_authority"), True),
        (("PRE_POST_boundary", "PRE_geometry_authority"), True),
        (("PRE_POST_boundary", "PRE_coordinates_authority"), True),
        (("PRE_POST_boundary", "PRE_reconstruction_performed"), True),
        (("PRE_POST_boundary", "POST_to_PRE_copy_performed"), True),
        (("PRE_POST_boundary", "PRE_zero_fill_performed"), True),
    ),
)
def test_pre_boundary_mutations_fail_closed(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


def test_free_ligand_and_post_boundaries_are_exact() -> None:
    formal = _formal()
    assert formal["free_ligand_PDB_component_boundary"] == {
        "PDB_component_representation_is_not_authoritative_PRE_free_ligand_topology": True,
        "corrected_PRE_graph_synthesized": False,
        "frozen_CCD_modified": False,
        "observed_C15_pair_authority_altered": False,
    }
    assert formal["POST_evidence_boundary"] == {
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "distance_only_inference": False,
        "explicit_covalent_evidence": True,
        "observed_distances_angstrom": [
            1.785022, 1.829385, 1.766225, 1.755127,
        ],
    }


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("POST_evidence_boundary", "POST_geometry_training_authority"), True),
        (
            ("POST_evidence_boundary", "POST_geometry_training_target_created"),
            True,
        ),
        (
            (
                "chemistry_authority_boundary",
                "reusable_chemistry_authority_created",
            ),
            True,
        ),
        (("selected_role_partition", "reusable_role_rule_created"), True),
        (("training_use_boundary", "formal_training_admitted"), True),
        (("training_use_boundary", "training_materialization_allowed"), True),
        (("training_use_boundary", "parameter_update_authorization"), True),
    ),
)
def test_post_reusable_and_training_authority_mutations_fail(
    path: tuple[object, ...], value: object
) -> None:
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject._validate_formal_document(_mutated_formal(path, value))


def test_current_with_cer_census_pre_ingestion_state_is_read_only() -> None:
    boundary = subject.load_frozen_formal_decision_v1(ROOT)[
        "current_census_boundary"
    ]
    assert boundary == subject._standalone_bound()["current_census_boundary"]
    assert boundary["FOUR_M5_current_status"] == "CURRENTLY_UNREVIEWED"
    assert boundary["FOUR_M5_human_review_completed"] is False
    assert boundary["FOUR_M5_chemistry_disposition"] == "UNRESOLVED"
    assert boundary["FOUR_M5_task_relevance_disposition"] == "UNRESOLVED"
    assert boundary["FOUR_M5_training_use_disposition"] == "UNRESOLVED"
    assert boundary["FOUR_M5_formal_training_admitted"] is False


def test_current_census_selection_uses_exact_event_identity() -> None:
    source = (ROOT / subject.SOURCE_RELATIVE).read_text(encoding="utf-8")
    assert 'row.get("canonical_event_id") in expected_set' in source
    assert 'row.get("ligand_component_id") == "4M5"' not in source


@pytest.mark.parametrize(
    "relative",
    (
        subject.FORMAL_DECISION_RELATIVE,
        subject.FORMAL_VALIDATOR_RELATIVE,
        subject.STRUCTURAL_GRAPH_RELATIVE,
    ),
)
def test_frozen_input_byte_drift_fails_closed(
    tmp_path: Path, relative: Path
) -> None:
    source = ROOT.parent / relative
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    if relative == subject.FORMAL_DECISION_RELATIVE:
        kwargs = {"formal_decision_path": tampered}
    elif relative == subject.FORMAL_VALIDATOR_RELATIVE:
        kwargs = {"formal_validator_path": tampered}
    else:
        kwargs = {"repository_path_overrides": {relative: tampered}}
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **kwargs)


@pytest.mark.parametrize(
    "relative", (subject.FORMAL_DECISION_RELATIVE, subject.FORMAL_VALIDATOR_RELATIVE)
)
def test_frozen_formal_exact2_symlink_and_executable_drift_fail_closed(
    tmp_path: Path, relative: Path
) -> None:
    source = ROOT.parent / relative
    argument = (
        "formal_decision_path"
        if relative == subject.FORMAL_DECISION_RELATIVE
        else "formal_validator_path"
    )
    symlink = tmp_path / ("link-" + source.name)
    symlink.symlink_to(source)
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **{argument: symlink})
    executable = tmp_path / ("exec-" + source.name)
    executable.write_bytes(source.read_bytes())
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(ROOT, **{argument: executable})


def test_semantic_owner_byte_drift_is_rejected(tmp_path: Path) -> None:
    source = ROOT / subject.DIRECT_RUNTIME_OWNER_RELATIVE
    tampered = tmp_path / source.name
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.load_frozen_formal_decision_v1(
            ROOT,
            repository_path_overrides={
                subject.DIRECT_RUNTIME_OWNER_RELATIVE: tampered
            },
        )


def test_formal_validator_is_never_imported_or_executed(monkeypatch: pytest.MonkeyPatch) -> None:
    imported: list[str] = []
    original = subject.importlib.import_module

    def recording_import(name: str):
        imported.append(name)
        return original(name)

    monkeypatch.setattr(subject.importlib, "import_module", recording_import)
    subject.load_frozen_formal_decision_v1(ROOT)
    assert imported == [
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
    ]
    assert not any(
        name.startswith("validate_4m5_formal_human_decision_v1")
        for name in sys.modules
    )
    checker.check_formal_validator_lifecycle()


def test_build_is_byte_deterministic_and_projection_is_exact() -> None:
    first = subject.build_artifacts_v1(ROOT)
    second = subject.build_artifacts_v1(ROOT)
    assert first == second
    assert tuple(first) == subject.OUTPUT_FILENAMES
    subject.validate_completed_decision_projection_v1(first, repo_root=ROOT)


def test_snapshot_exact4_authority_and_boundaries() -> None:
    snapshot = json.loads(subject.build_artifacts_v1(ROOT)[subject.SNAPSHOT])
    assert snapshot["schema_version"] == subject.SNAPSHOT_SCHEMA_VERSION
    assert snapshot["review_unit_id"] == subject.EXPECTED_REVIEW_UNIT_ID
    assert snapshot["formal_semantic_canonical_sha256"] == (
        subject.FORMAL_SEMANTIC_CANONICAL_SHA256
    )
    assert [row["canonical_event_id"] for row in snapshot["events"]] == list(
        subject.EXPECTED_EVENT_IDS
    )
    assert [row["scaleup_rank"] for row in snapshot["events"]] == [
        973, 974, 975, 976,
    ]
    assert snapshot["reactive_pair_authority"] == subject._pair_authority_boundary()
    assert snapshot["PRE_boundary"] == subject._pre_boundary()
    assert snapshot["POST_boundary"] == subject._post_boundary()
    assert snapshot["free_ligand_PDB_component_boundary"] == (
        subject._free_ligand_boundary()
    )
    assert snapshot["training_boundary"]["formal_training_admitted"] is False
    assert (
        snapshot["canonical_task_contract"]["authoritative_task_labels_created"]
        is False
    )
    assert (
        snapshot["canonical_task_contract"]["event_task_label_rows_materialized"]
        is False
    )


def test_matrix_exact4_fields_task_availability_pre_and_post_are_exact() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    assert len(rows) == 4
    assert [row["POST_distance_angstrom"] for row in rows] == [
        "1.785022", "1.829385", "1.766225", "1.755127",
    ]
    assert [row["protein_context"] for row in rows] == [
        "PPARalpha", "PPARalpha", "PPARgamma", "PPARgamma",
    ]
    for row in rows:
        assert row["protein_reactive_atom"] == "SG"
        assert row["ligand_reactive_atom"] == "C15"
        assert row["selected_role_candidate_index_0based"] == "0"
        assert json.loads(row["warhead_atoms_json"]) == list(subject.WARHEAD_ROLE)
        assert json.loads(row["linker_atoms_json"]) == []
        assert json.loads(row["scaffold_atoms_json"]) == list(
            subject.SCAFFOLD_ROLE
        )
        assert row["direct_profile_applicable_task_ids_json"] == "[0,3,4]"
        assert row["authoritative_task_labels_created"] == "false"
        assert row["event_task_label_rows_materialized"] == "false"
        assert row["PRE_source_graph_present"] == "true"
        assert row["PRE_source_graph_count_per_event"] == "1"
        assert row["PRE_mapping_count_per_event"] == "0"
        assert row["PRE_mapping_status"] == subject.PRE_MAPPING_STATUS
        assert row["PRE_status"] == subject.PRE_STATUS
        assert row["POST_source_evidence_available"] == "true"
        assert row["POST_geometry_training_authority"] == "false"
        assert row["formal_training_admitted"] == "false"


def test_summary_exact_counts_and_operation_boundary() -> None:
    summary = json.loads(subject.build_artifacts_v1(ROOT)[subject.SUMMARY])
    assert [
        summary["ingested_event_count"],
        summary["human_completed_event_count"],
        summary["positive_chemistry_event_count"],
        summary["sample_pair_authority_event_count"],
        summary["role_authority_event_count"],
        summary["DIRECT_event_count"],
        summary["training_use_INCLUDE_event_count"],
        summary["future_training_admission_candidate_count"],
    ] == [4, 4, 4, 4, 4, 4, 4, 4]
    assert summary["formal_training_admitted_count"] == 0
    assert summary["canonical_Exact5_applicable_event_counts"] == {
        "warhead_only": 4,
        "linker_plus_warhead": 0,
        "scaffold_plus_warhead": 0,
        "scaffold_only": 4,
        "scaffold_plus_linker_plus_warhead": 4,
    }
    assert summary["PRE_source_graph_present_event_count"] == 4
    assert summary["PRE_mapping_available_event_count"] == 0
    assert summary["PRE_authority_event_count"] == 0
    assert summary["POST_source_evidence_event_count"] == 4
    assert summary["POST_training_authority_event_count"] == 0
    assert summary["RECONCILIATION"] is False
    assert summary["CENSUS_REFRESH"] is False
    assert summary["QUEUE_REFRESH"] is False
    assert summary["READY_FOR_TRAINING"] is False


@pytest.mark.parametrize(
    ("name", "path", "value"),
    (
        (subject.SNAPSHOT, ("reactive_pair_authority", "reusable_pair_rule_created"), True),
        (subject.SNAPSHOT, ("selected_role_partition", "reusable"), True),
        (subject.SNAPSHOT, ("canonical_task_contract", "B3_present"), False),
        (
            subject.SNAPSHOT,
            ("canonical_task_contract", "authoritative_task_labels_created"),
            True,
        ),
        (subject.SNAPSHOT, ("PRE_boundary", "PRE_source_graph_present"), False),
        (subject.SNAPSHOT, ("PRE_boundary", "PRE_topology_authority"), True),
        (subject.SNAPSHOT, ("POST_boundary", "POST_geometry_training_authority"), True),
        (subject.SNAPSHOT, ("training_boundary", "formal_training_admitted"), True),
        (subject.SUMMARY, ("ingested_event_count",), 5),
        (subject.MANIFEST, ("frozen_formal_validator_executed",), True),
        (subject.MANIFEST, ("FORMAL_TRAINING_ADMITTED",), True),
        (subject.MANIFEST, ("READY_FOR_TRAINING",), True),
    ),
)
def test_projection_authority_tamper_fails_closed(
    name: str, path: tuple[object, ...], value: object
) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(
            _mutated_json_artifact(artifacts, name, path, value)
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("canonical_event_id", "wrong"),
        ("protein_reactive_atom", "CB"),
        ("ligand_reactive_atom", "C14"),
        ("pair_authority_scope", "ALL"),
        ("warhead_atoms_json", '["C15"]'),
        ("linker_atoms_json", '["C14"]'),
        ("scaffold_atoms_json", '["C1"]'),
        ("boundary_bonds_json", "[]"),
        ("direct_profile_applicable_task_ids_json", "[0,4]"),
        ("authoritative_task_labels_created", "true"),
        ("event_task_label_rows_materialized", "true"),
        ("PRE_source_graph_present", "false"),
        ("PRE_source_graph_count_per_event", "0"),
        ("PRE_mapping_count_per_event", "1"),
        ("PRE_mapping_status", "MAPPED"),
        ("PRE_topology_authority", "true"),
        ("POST_geometry_training_authority", "true"),
        ("reusable_chemistry_authority", "true"),
        ("reusable_pair_rule_created", "true"),
        ("reusable_role_authority", "true"),
        ("formal_training_admitted", "true"),
    ),
)
def test_matrix_row_tamper_fails_closed(field: str, value: str) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(
            _mutated_matrix_artifact(artifacts, 0, field, value)
        )


def test_matrix_row_count_and_output_inventory_drift_fail_closed() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    row_drift = dict(artifacts)
    row_drift[subject.MATRIX] = subject._csv_bytes(
        subject.MATRIX_HEADER, rows[:-1]
    )
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(row_drift)
    inventory_drift = dict(artifacts)
    inventory_drift.pop(subject.SUMMARY)
    with pytest.raises(subject.FourM5IngestionSafetyError):
        subject.validate_completed_decision_projection_v1(inventory_drift)


def test_manifest_closes_sources_outputs_without_self_sha() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert manifest["candidate_publication_file_count"] == 7
    assert manifest["candidate_publication_paths"] == list(_expected_paths())
    assert manifest["formal_semantics_independently_validated"] is True
    assert manifest["frozen_formal_validator_provenance_identity_only"] is True
    assert manifest["frozen_formal_validator_imported"] is False
    assert manifest["frozen_formal_validator_executed"] is False
    assert manifest["authoritative_task_labels_created"] is False
    assert manifest["event_task_label_rows_materialized"] is False
    assert manifest["manifest_self_SHA256_recorded"] is False
    assert manifest["MANIFEST_SELF_SHA256_PROHIBITED"] is True
    assert subject.MANIFEST not in manifest["output_artifact_bindings"]
    for name in (subject.SNAPSHOT, subject.MATRIX, subject.SUMMARY):
        binding = manifest["output_artifact_bindings"][name]
        assert binding["byte_count"] == len(artifacts[name])
        assert binding["SHA256"] == subject._sha256(artifacts[name])


@pytest.mark.parametrize(
    "forbidden_field",
    ("mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode"),
)
def test_numeric_posix_semantic_identity_fields_are_rejected(
    forbidden_field: str,
) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["formal_decision_binding"][forbidden_field] = "0644"
    tampered = dict(artifacts)
    tampered[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(
        subject.FourM5IngestionSafetyError, match="NUMERIC_POSIX"
    ):
        subject.validate_completed_decision_projection_v1(tampered)


def test_materialization_double_run_and_contamination_fail_closed(
    tmp_path: Path,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = subject.materialize_artifacts_v1(ROOT, output_root=first_root)
    second = subject.materialize_artifacts_v1(ROOT, output_root=second_root)
    assert first == second
    assert {path.name for path in first_root.iterdir()} == set(
        subject.OUTPUT_FILENAMES
    )
    assert {path.name for path in second_root.iterdir()} == set(
        subject.OUTPUT_FILENAMES
    )
    subject.materialize_artifacts_v1(ROOT, output_root=first_root)
    contaminated = tmp_path / "contaminated"
    contaminated.mkdir()
    sentinel = contaminated / "unexpected.txt"
    sentinel.write_bytes(b"sentinel\n")
    with pytest.raises(
        subject.FourM5IngestionSafetyError,
        match="OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES",
    ):
        subject.materialize_artifacts_v1(ROOT, output_root=contaminated)
    assert sentinel.read_bytes() == b"sentinel\n"


def test_materialization_destination_symlink_fails_before_write(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"platform cannot create directory symlink: {error}")
    with pytest.raises(
        subject.FourM5IngestionSafetyError,
        match="OUTPUT_ROOT_SYMLINK_FORBIDDEN",
    ):
        subject.materialize_artifacts_v1(ROOT, output_root=link)
    assert tuple(target.iterdir()) == ()


def test_materialized_repository_outputs_match_fresh_build() -> None:
    report = subject.check_materialized_v1(ROOT)
    assert report["status"] == "PASS"
    assert report["exact_output_count"] == 4
    assert report["event_count"] == 4
    assert report["deterministic"] is True
    assert report["FOUR_M5_COMPLETED_DECISION_INGESTED"] is True
    assert report["FOUR_M5_FORMAL_VALIDATOR_PROVENANCE_ONLY"] is True
    assert report["authoritative_task_labels_created"] is False
    assert report["event_task_label_rows_materialized"] is False
    assert report["FORMAL_TRAINING_ADMITTED"] is False
    assert report["RECONCILIATION"] is False
    assert report["READY_FOR_TRAINING"] is False


def test_production_owner_never_imports_or_executes_frozen_validator() -> None:
    source = (ROOT / subject.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(
                alias.name.split(".")[0] in {"subprocess", "runpy"}
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in {
                "subprocess", "runpy",
            }
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"exec", "eval", "compile", "__import__"}
    assert "execute_formal_validator" not in source
    assert "_run_formal_validator" not in source
    assert "subprocess_formal_validator" not in source
    assert "git rev-parse" not in source
    assert "git status" not in source


def _validate_tracked_relation(**overrides: object) -> None:
    expected_set = set(_expected_paths())
    facts: dict[str, object] = {
        "profile": checker.TRACKED_CLEAN,
        "expected_paths": expected_set,
        "head": "synthetic-four-m5-local-commit",
        "origin_main": checker.BASELINE_HEAD,
        "ahead": 1,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": expected_set,
    }
    facts.update(overrides)
    checker.validate_repository_relation_values(**facts)  # type: ignore[arg-type]


def test_candidate_and_tracked_clean_profiles_pass() -> None:
    expected = _expected_paths()
    expected_set = set(expected)
    assert checker.classify_repository_profile(
        expected_paths=expected,
        tracked_paths=set(),
        ordinary_untracked=expected_set,
        status_lines=tuple("?? " + path for path in expected),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=expected,
        tracked_paths=expected_set,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.TRACKED_CLEAN
    checker.validate_repository_relation_values(
        profile=checker.CANDIDATE_UNTRACKED,
        expected_paths=expected_set,
        head=checker.BASELINE_HEAD,
        origin_main=checker.BASELINE_HEAD,
        ahead=0,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=set(),
    )


def test_future_tracked_clean_lifecycle_accepts_permitted_descendants() -> None:
    _validate_tracked_relation()
    _validate_tracked_relation(
        head="synthetic-immediate-pushed",
        origin_main="synthetic-immediate-pushed",
        ahead=0,
    )
    _validate_tracked_relation(head="synthetic-multi-commit", ahead=3)
    expected_set = set(_expected_paths())
    successors = {
        "src/covalent_ext/synthetic_future_reconciliation_v1.py",
        "data/derived/covalent_small/synthetic_future_census_v1.json",
    }
    _validate_tracked_relation(
        head="synthetic-future-successor",
        ahead=5,
        changed_since_baseline=expected_set | successors,
    )
    _validate_tracked_relation(
        head="synthetic-local-successor",
        origin_main="synthetic-published-ingestion",
        ahead=1,
        changed_since_baseline=expected_set | successors,
    )


@pytest.mark.parametrize(
    "overrides",
    (
        {"baseline_is_ancestor_of_head": False},
        {"baseline_is_ancestor_of_origin": False},
        {"origin_is_ancestor_of_head": False},
        {"behind": 1},
    ),
)
def test_tracked_clean_rewind_divergence_and_behind_fail_closed(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(
        SystemExit, match="TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID"
    ):
        _validate_tracked_relation(**overrides)


def test_tracked_clean_missing_candidate_path_fails_with_successors() -> None:
    expected = _expected_paths()
    expected_set = set(expected)
    with pytest.raises(
        SystemExit, match="TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID"
    ):
        _validate_tracked_relation(
            head="synthetic-incomplete",
            ahead=4,
            changed_since_baseline=(
                expected_set - {expected[0]}
            ) | {"src/covalent_ext/synthetic_successor.py"},
        )


def test_mixed_dirty_staged_and_unrelated_untracked_fail_closed() -> None:
    expected = _expected_paths()
    expected_set = set(expected)
    cases = (
        (
            {expected[0]}, set(expected[1:]),
            tuple("?? " + path for path in expected[1:]),
            set(), set(), "MIXED_TRACKING_STATE",
        ),
        (
            expected_set, set(), (), {expected[0]}, set(),
            "TRACKED_WORKTREE_MODIFICATION_PRESENT",
        ),
        (
            expected_set, set(), (), set(), {expected[0]},
            "STAGED_INDEX_CHANGE_PRESENT",
        ),
        (
            expected_set, {"unrelated.txt"}, ("?? unrelated.txt",),
            set(), set(), "TRACKED_CLEAN_STATE_DIRTY",
        ),
    )
    for tracked, untracked, status_lines, working, staged, message in cases:
        with pytest.raises(SystemExit, match=message):
            checker.classify_repository_profile(
                expected_paths=expected,
                tracked_paths=tracked,
                ordinary_untracked=untracked,
                status_lines=status_lines,
                working_diff=working,
                cached_diff=staged,
            )


def test_no_dynamic_metadata_absolute_paths_or_forbidden_suffixes() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    for name in (subject.SNAPSHOT, subject.SUMMARY, subject.MANIFEST):
        text = artifacts[name].decode("utf-8")
        assert '"created_at"' not in text
        assert '"generated_at"' not in text
        assert '"validated_at"' not in text
        assert "/cpfs" not in text
        assert "/tmp/" not in text
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part", ".pyc", ".log",
    }
    assert not any(
        path.suffix.lower() in forbidden
        for path in subject.CANDIDATE_PUBLICATION_PATHS
    )
