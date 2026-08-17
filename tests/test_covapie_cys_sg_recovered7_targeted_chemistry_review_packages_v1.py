from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1 as owner,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def model() -> dict[str, object]:
    return owner.build_package_model_v1()


@pytest.fixture(scope="module")
def closure_evidence() -> dict[str, object]:
    return json.loads((owner.REPO_ROOT / owner.CLOSURE_EVIDENCE).read_bytes())


def test_published_closure_bindings_are_successor_compatible() -> None:
    assert (
        owner.PUBLISHED_CLOSURE_COMMIT
        == "68ff4ff290e6fa94d771491e05cd681f9305a661"
    )
    for relative, expected in owner.PUBLISHED_CLOSURE_SOURCE_HASHES.items():
        assert _sha256((owner.REPO_ROOT / relative).read_bytes()) == expected
    owner.validate_published_source_bindings_v1()


def test_review_population_is_exact_recovered7_and_excludes_unresolved5(
    model: dict[str, object],
) -> None:
    assert model["review_candidate_identities"] == list(owner.RECOVERED_IDENTITIES)
    assert len(model["sample_applicability"]) == 7
    assert not (
        set(model["review_candidate_identities"])
        & owner.UNRESOLVED_STRUCTURAL_REVIEW_IDENTITIES
    )


def test_signature_ignores_pdb_coordinates_altloc_and_occupancy(
    closure_evidence: dict[str, object],
) -> None:
    sample = copy.deepcopy(closure_evidence["samples"][-1])
    topology = closure_evidence["component_topology_authorities"]["K36"]
    before = owner.derive_chemistry_review_signature_v1(sample, topology)
    sample["pdb_id"] = "COORDINATE_IDENTITY_MUST_NOT_MATTER"
    sample["topology_mapping"]["selected_ligand_altloc"] = "Z"
    sample["explicit_event"]["ligand_endpoint"]["label_alt_id"] = "Z"
    sample["explicit_event"]["ligand_endpoint"]["occupancy"] = "0.01"
    sample["explicit_event"]["ligand_endpoint"]["x"] = "999.0"
    sample["canonical_model_bound_ligand_atoms"][0]["x"] = "-999.0"
    after = owner.derive_chemistry_review_signature_v1(sample, topology)
    assert before == after
    assert owner.chemistry_review_signature_sha256_v1(before) == (
        owner.chemistry_review_signature_sha256_v1(after)
    )


def test_signature_contains_required_chemistry_and_no_sample_identity(
    model: dict[str, object],
) -> None:
    required = {
        "ligand_component_id",
        "semantic_topology_sha256",
        "reactive_residue_atom",
        "reactive_ligand_atom",
        "canonical_model_bound_ligand_heavy_atom_inventory",
        "topology_heavy_atom_inventory",
        "topology_heavy_atoms_not_observed",
        "canonical_internal_heavy_heavy_bond_graph_with_bond_orders",
        "reaction_specific_post_graph_proven",
        "explicit_covalent_event",
    }
    for review_class in model["review_classes"]:
        signature = review_class["chemistry_review_signature"]
        assert required <= set(signature)
        assert signature["reactive_residue_atom"] == "SG"
        assert signature["reaction_specific_post_graph_proven"] is False
        owner._assert_signature_has_no_sample_identity(signature)


def test_exact_hash_identity_is_the_only_grouping_rule(
    model: dict[str, object],
) -> None:
    signatures = {
        member: review_class["chemistry_review_signature"]
        for review_class in model["review_classes"]
        for member in review_class["member_sample_identities"]
    }
    groups = owner.group_exact_chemistry_review_signatures_v1(signatures)
    assert sorted(len(members) for members in groups.values()) == [1, 1, 5]

    changed = copy.deepcopy(signatures["4DCD/K36"])
    changed["reaction_specific_post_graph_proven"] = True
    assert owner.chemistry_review_signature_sha256_v1(changed) != (
        owner.chemistry_review_signature_sha256_v1(signatures["4DCD/K36"])
    )

    same_component_different_reactive_atom = copy.deepcopy(signatures["4DCD/K36"])
    same_component_different_reactive_atom["reactive_ligand_atom"] = "C20"
    same_component_different_reactive_atom["explicit_covalent_event"][
        "ligand_atom_id"
    ] = "C20"
    assert same_component_different_reactive_atom["ligand_component_id"] == "K36"
    assert owner.chemistry_review_signature_sha256_v1(
        same_component_different_reactive_atom
    ) != owner.chemistry_review_signature_sha256_v1(signatures["4DCD/K36"])


def test_k36_compression_is_derived_and_5wkj_altloc_is_applicability_only(
    model: dict[str, object],
) -> None:
    assert model["review_class_count"] == 3
    assert model["k36_review_class_count"] == 1
    assert model["k36_single_chemistry_review_class"] is True
    assert model["k36_class_member_count"] == 5
    k36_rows = [
        row
        for row in model["sample_applicability"]
        if row["ligand_component_id"] == "K36"
    ]
    assert len(k36_rows) == 5
    assert len({row["chemistry_review_signature_sha256"] for row in k36_rows}) == 1
    assert len({row["review_class_id"] for row in k36_rows}) == 1
    wk = next(row for row in k36_rows if row["pdb_id"] == "5WKJ")
    assert wk["selected_altloc"] == "B"
    assert "ligand_altloc=B" in wk["altloc_occupancy_provenance"]
    component_by_class = {
        row["representative_component_id"]: row["review_class_id"]
        for row in model["review_classes"]
    }
    assert len(component_by_class) == 3
    assert component_by_class["1ZB"] != component_by_class["K36"]
    assert component_by_class["K2Z"] != component_by_class["K36"]


def test_all_blank_records_are_authority_neutral(model: dict[str, object]) -> None:
    assert len(model["blank_review_records"]) == model["review_class_count"]
    for wrapper in model["blank_review_records"]:
        record = wrapper["review_record"]
        owner.validate_unreviewed_template_v1(record)
        assert record["review_status"] == "NOT_REVIEWED"
        assert record["review_scope"] == "NOT_REVIEWED"
        assert record["reviewer_id"] == ""
        assert record["reviewed_reaction_family_id"] == ""
        assert record["reviewed_warhead_rule_id"] == ""
        assert record["reviewed_warhead_atom_ids"] == []
        assert record["reviewed_scaffold_atom_ids"] == []
        assert record["reviewed_linker_atom_ids"] == []
        assert record["reviewed_warhead_role_atom_ids"] == []
        assert record["reviewed_minimal_seed_atom_ids"] == []
        assert record["review_record_sha256"] == ""
        assert wrapper["unreviewed_template_payload_sha256"] == (
            owner.review_record_sha256_v1(record)
        )


def test_current11_search_is_non_authoritative_and_non_propagating(
    model: dict[str, object],
) -> None:
    search = model["reviewer_hint_search"]
    assert search["candidate_record_count_searched"] == 11
    assert search["effective_human_authority_record_count_searched"] == 11
    assert search["candidate_component_id_overlap"] == []
    assert search["effective_human_component_id_overlap"] == []
    assert search["exact_current11_chemistry_signature_match_count"] == 0
    assert search["prior_reference_authority_class"] == "NONE"
    for review_class in model["review_classes"]:
        assert review_class["prior_non_authoritative_review_hints"] == []
        assert review_class["prior_non_authoritative_review_hint_count"] == 0
        assert review_class["future_review_scope_options"] == list(owner.REVIEW_SCOPES)
        assert review_class["future_family_rule_authority_action_options"] == list(
            owner.AUTHORITY_ACTIONS[1:]
        )
        assert review_class["human_authority_created"] is False


def _synthetic_review_class() -> dict[str, object]:
    atoms = [
        {"atom_id": atom, "element": "C"}
        for atom in ("A", "B", "C", "L", "W", "X")
    ]
    bonds = [
        {"atom_id_1": "A", "atom_id_2": "B", "bond_order": "single"},
        {"atom_id_1": "B", "atom_id_2": "C", "bond_order": "single"},
        {"atom_id_1": "C", "atom_id_2": "L", "bond_order": "single"},
        {"atom_id_1": "L", "atom_id_2": "W", "bond_order": "single"},
        {"atom_id_1": "W", "atom_id_2": "X", "bond_order": "double"},
    ]
    signature = {
        "chemistry_review_signature_version": owner.CHEMISTRY_REVIEW_SIGNATURE_VERSION,
        "ligand_component_id": "SYN",
        "semantic_topology_sha256": "1" * 64,
        "reactive_residue": "CYS",
        "reactive_residue_atom": "SG",
        "reactive_residue_atom_element": "S",
        "reactive_ligand_atom": "W",
        "reactive_ligand_atom_element": "C",
        "canonical_model_bound_ligand_heavy_atom_inventory": atoms,
        "topology_heavy_atom_inventory": atoms,
        "topology_heavy_atoms_not_observed": [],
        "canonical_internal_heavy_heavy_bond_graph_with_bond_orders": bonds,
        "reaction_specific_post_graph_proven": False,
        "explicit_covalent_event": {
            "event_type": "CYS_SG_TO_LIGAND_REACTIVE_ATOM_EXPLICIT_COVALENT_EDGE",
            "evidence_kind": "SYNTHETIC_TEST_ONLY",
            "residue_component_id": "CYS",
            "residue_atom_id": "SG",
            "residue_atom_element": "S",
            "ligand_component_id": "SYN",
            "ligand_atom_id": "W",
            "ligand_atom_element": "C",
            "component_internal_topology_edge": False,
        },
    }
    digest = owner.chemistry_review_signature_sha256_v1(signature)
    return {
        "review_class_id": "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_" + digest.upper(),
        "chemistry_review_signature_sha256": digest,
        "chemistry_review_signature": signature,
        "member_sample_count": 1,
        "member_sample_identities": ["SYNTHETIC/SYN"],
    }


def _valid_completed_record(review_class: dict[str, object]) -> dict[str, object]:
    record = owner.make_blank_review_record_v1(review_class)
    record.update(
        {
            "review_status": "COMPLETED",
            "review_scope": "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
            "reviewed_reaction_family_authority_action": "NEW_AUTHORITY_REQUIRED",
            "reviewed_warhead_rule_authority_action": "NEW_AUTHORITY_REQUIRED",
            "reviewed_warhead_atom_ids": ["W", "X"],
            "reviewed_warhead_attachment_atom_id": "W",
            "reviewed_nonwarhead_boundary_atom_id": "L",
            "reviewed_attachment_boundary_bond_order": "single",
            "reviewed_scaffold_atom_ids": ["A", "B", "C"],
            "reviewed_linker_atom_ids": ["L"],
            "reviewed_warhead_role_atom_ids": ["W", "X"],
            "reviewed_minimal_seed_atom_ids": ["A", "B"],
            "reviewer_id": "human-reviewer-001",
            "review_rationale": "Synthetic validator coverage only.",
        }
    )
    record["review_record_sha256"] = owner.review_record_sha256_v1(record)
    return record


def _rehash(record: dict[str, object]) -> None:
    record["review_record_sha256"] = ""
    record["review_record_sha256"] = owner.review_record_sha256_v1(record)


def test_future_completed_record_accepts_valid_exact3_boundary_and_seed() -> None:
    review_class = _synthetic_review_class()
    record = _valid_completed_record(review_class)
    owner.validate_completed_review_record_v1(
        record,
        review_class,
        applicability_signatures=[review_class["chemistry_review_signature_sha256"]],
    )


@pytest.mark.parametrize(
    "minimal_seed",
    (
        ["A"],
        ["A", "B", "C", "L"],
    ),
)
def test_future_completed_record_rejects_minimal_seed_size_outside_2_or_3(
    minimal_seed: list[str],
) -> None:
    review_class = _synthetic_review_class()
    record = _valid_completed_record(review_class)
    record["reviewed_minimal_seed_atom_ids"] = minimal_seed
    _rehash(record)
    with pytest.raises(
        owner.ReviewPackageValidationError,
        match="^MINIMAL_SEED_SIZE_NOT_2_OR_3$",
    ):
        owner.validate_completed_review_record_v1(
            record,
            review_class,
            applicability_signatures=[
                review_class["chemistry_review_signature_sha256"]
            ],
        )


def test_future_completed_record_accepts_connected_minimal_seed_size_3() -> None:
    review_class = _synthetic_review_class()
    record = _valid_completed_record(review_class)
    record["reviewed_minimal_seed_atom_ids"] = ["A", "B", "C"]
    _rehash(record)
    owner.validate_completed_review_record_v1(
        record,
        review_class,
        applicability_signatures=[review_class["chemistry_review_signature_sha256"]],
    )


def test_future_completed_record_invariants_fail_closed() -> None:
    review_class = _synthetic_review_class()
    mutations = {
        "overlapping roles": lambda row: row.update(
            reviewed_scaffold_atom_ids=["A", "B", "C", "L"]
        ),
        "incomplete role union": lambda row: row.update(
            reviewed_warhead_role_atom_ids=["W"]
        ),
        "empty required role": lambda row: row.update(reviewed_linker_atom_ids=[]),
        "reactive atom outside warhead": lambda row: row.update(
            reviewed_linker_atom_ids=["L", "W"],
            reviewed_warhead_role_atom_ids=["X"],
        ),
        "minimal seed outside scaffold": lambda row: row.update(
            reviewed_minimal_seed_atom_ids=["A", "L"]
        ),
        "disconnected minimal seed": lambda row: row.update(
            reviewed_minimal_seed_atom_ids=["A", "C"]
        ),
        "boundary atom not in graph": lambda row: row.update(
            reviewed_nonwarhead_boundary_atom_id="Z"
        ),
        "boundary bond not in graph": lambda row: row.update(
            reviewed_warhead_attachment_atom_id="X"
        ),
        "attachment inconsistent with warhead": lambda row: row.update(
            reviewed_warhead_attachment_atom_id="B",
            reviewed_nonwarhead_boundary_atom_id="A",
        ),
    }
    for mutation in mutations.values():
        record = _valid_completed_record(review_class)
        mutation(record)
        _rehash(record)
        with pytest.raises(owner.ReviewPackageValidationError):
            owner.validate_completed_review_record_v1(
                record,
                review_class,
                applicability_signatures=[
                    review_class["chemistry_review_signature_sha256"]
                ],
            )

    record = _valid_completed_record(review_class)
    with pytest.raises(
        owner.ReviewPackageValidationError,
        match="REUSABLE_SCOPE_SIGNATURE_MISMATCH",
    ):
        owner.validate_completed_review_record_v1(
            record, review_class, applicability_signatures=["0" * 64]
        )


def test_tracked_and_manual_aid_builds_are_deterministic_and_bounded(
    tmp_path: Path,
) -> None:
    first_tracked = (
        owner.build_covapie_cys_sg_recovered7_targeted_chemistry_review_package_artifacts_v1()
    )
    second_tracked = (
        owner.build_covapie_cys_sg_recovered7_targeted_chemistry_review_package_artifacts_v1()
    )
    assert first_tracked == second_tracked
    assert tuple(first_tracked) == owner.OUTPUT_FILES
    first_aids = owner.build_manual_review_aid_artifacts_v1()
    second_aids = owner.build_manual_review_aid_artifacts_v1()
    assert first_aids == second_aids
    assert len(first_aids) == 12
    assert {Path(path).name for path in first_aids} == {
        "README.md",
        "chemistry_evidence.json",
        "atom_and_bond_review_table.csv",
        "review_decision_template.csv",
    }

    tracked_root = tmp_path / "tracked"
    manual_root = tmp_path / "manual"
    owner.materialize_covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1(
        tracked_output_root=tracked_root, manual_output_root=manual_root
    )
    assert {path.name for path in tracked_root.iterdir()} == set(owner.OUTPUT_FILES)
    assert sum(path.is_file() for path in manual_root.rglob("*")) == 12
    owner.materialize_covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1(
        tracked_output_root=tracked_root, manual_output_root=manual_root
    )


def test_serialized_products_report_no_review_or_forbidden_execution() -> None:
    artifacts = (
        owner.build_covapie_cys_sg_recovered7_targeted_chemistry_review_package_artifacts_v1()
    )
    index = _csv_rows(artifacts[owner.INDEX_FILE])
    evidence = json.loads(artifacts[owner.EVIDENCE_FILE])
    manifest = json.loads(artifacts[owner.MANIFEST_FILE])
    assert len(index) == 7
    assert len(evidence["review_classes"]) == 3
    assert len(evidence["sample_applicability"]) == 7
    assert len(evidence["blank_review_records"]) == 3
    assert manifest["completed_human_review_count"] == 0
    assert manifest["human_authority_created"] is False
    assert manifest["reusable_authority_created"] is False
    assert manifest["sample_bound_authority_created"] is False
    for field in (
        "distance_based_bond_inference_used",
        "inverse_reaction_chemistry_executed",
        "pre_geometry_reconstruction_executed",
        "leaving_group_inferred_automatically",
        "formal_charge_change_inferred_automatically",
        "proton_transfer_inferred_automatically",
        "network_request_executed",
        "raw_structure_downloaded",
        "topology_downloaded",
        "model_forward",
        "backward",
        "optimizer_step",
        "trainer_fit",
        "formal_training",
        "geometry_loss_activation",
        "rl",
        "ready_for_automated_chemistry_label_execution",
        "ready_for_geometry_loss_activation",
        "ready_for_training",
    ):
        assert manifest[field] is False
    assert manifest["ready_for_review_package_publication"] is True
    assert manifest["ready_for_human_chemistry_review_execution"] is True
