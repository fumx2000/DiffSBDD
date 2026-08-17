from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import socket
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1
    as closure,
)
from covalent_ext import (
    real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun
    as atom_site_owner,
)


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return closure.build_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_artifacts_v1()


@pytest.fixture(scope="module")
def matrix(artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(artifacts[closure.MATRIX_FILE].decode())))


@pytest.fixture(scope="module")
def evidence(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[closure.EVIDENCE_FILE])


@pytest.fixture(scope="module")
def manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[closure.MANIFEST_FILE])


def _synthetic_atom(symbol: str, atom_id: str, atom_name: str) -> dict[str, str]:
    return {
        "_atom_site.id": atom_id,
        "_atom_site.group_PDB": "HETATM",
        "_atom_site.type_symbol": symbol,
        "_atom_site.label_atom_id": atom_name,
        "_atom_site.label_comp_id": "SYN",
        "_atom_site.auth_comp_id": "SYN",
        "_atom_site.label_asym_id": "L",
        "_atom_site.auth_asym_id": "L",
        "_atom_site.label_seq_id": "1",
        "_atom_site.auth_seq_id": "1",
        "_atom_site.label_alt_id": "",
        "_atom_site.pdbx_PDB_model_num": "1",
        "_atom_site.occupancy": "1.00",
        "_atom_site.Cartn_x": "0.0",
        "_atom_site.Cartn_y": "0.0",
        "_atom_site.Cartn_z": "0.0",
    }


def _synthetic_authority_audits(
    status: str = "APPROVED_REUSABLE_RULE_MATCH",
    match_count: int = 1,
    rule_scope: str = "REUSABLE_APPROVED_RULE",
) -> dict[str, dict[str, object]]:
    audits: dict[str, dict[str, object]] = {}
    for dimension in closure.REQUIRED_DOWNSTREAM_DIMENSIONS:
        audit = closure._authority_dimension_v1(
            authority_status=status,
            source_path=None,
            authority_id=f"SYNTHETIC_{dimension.upper()}_V1",
            rule_scope=rule_scope,
            match_count=match_count,
            applicability_reason="synthetic exact rule-matching result",
        )
        audit.update({
            "authority_source_path_or_NONE": f"synthetic/{dimension}_v1.json",
            "authority_source_sha256_or_NONE": "a" * 64,
            "published": True,
            "approved": True,
            "version_bound": True,
            "exact_sample_applicability": True,
            "deterministic_unique_result": True,
            "invariants_pass": True,
            "reactive_ligand_atom_compatible": True,
            "cys_sg_event_compatible": True,
            "sample_identity_exact": status == "SAMPLE_BOUND_AUTHORITY_MATCH",
            "complete_dimension_authority": (
                status == "SAMPLE_BOUND_AUTHORITY_MATCH"
            ),
        })
        audits[dimension] = audit
    return audits


def test_published_execution_commit_and_artifact_sha_bindings() -> None:
    assert closure.PUBLISHED_EXECUTION_COMMIT == (
        "5cabada8264e1a3243f629b186f4ed3208f7a249"
    )
    assert closure.validate_published_execution_v1()["acquisition_valid_count"] == 12
    for path, expected in closure.PUBLISHED_EXECUTION_SHA256.items():
        assert hashlib.sha256((closure.REPO_ROOT / path).read_bytes()).hexdigest() == expected


def test_exact_recovered7_is_derived_and_unresolved5_is_excluded() -> None:
    rows = closure.derive_recovered7_rows_v1()
    identities = [(row["pdb_id"], row["ligand_component_id"]) for row in rows]
    assert identities == list(closure.RECOVERED_IDENTITIES)
    assert not (set(identities) & set(closure.UNRESOLVED_STRUCTURAL_REVIEW_IDENTITIES))


def test_raw_sha_identity_unique_components_and_k36_count(matrix: list[dict[str, str]]) -> None:
    assert len(matrix) == 7
    assert {row["ligand_component_id"] for row in matrix} == {"1ZB", "K2Z", "K36"}
    assert sum(row["ligand_component_id"] == "K36" for row in matrix) == 5
    for row in matrix:
        assert row["raw_sha256"] == closure.RAW_SHA256_BY_PDB[row["pdb_id"]]


def test_local_topology_preflight_finds_explicit_atom_bond_authority() -> None:
    authorities = closure.load_component_topology_authorities_v1()
    expected = {
        "1ZB": (32, 18, 32),
        "K2Z": (82, 37, 83),
        "K36": (64, 33, 65),
    }
    assert set(authorities) == set(expected)
    for component, authority in authorities.items():
        assert (authority.atom_count, authority.heavy_atom_count, authority.bond_count) == expected[component]
        assert authority.source_kind == closure.TOPOLOGY_SOURCE_KIND
        assert authority.bond_order_available is True


def test_explicit_event_endpoints_map_exactly(matrix: list[dict[str, str]], evidence: dict[str, object]) -> None:
    assert all(row["event_mapping_status"] == "EXACT_EVENT_ENDPOINT_MAPPING_PASS" for row in matrix)
    for sample in evidence["samples"]:  # type: ignore[index,union-attr]
        event = sample["explicit_event"]
        assert event["protein_endpoint"]["auth_atom_id"] == "SG"
        assert event["ligand_endpoint"]["label_atom_id"] == event[
            "protein_ligand_covalent_event_edge"
        ]["ligand_atom_name"]
        assert event["protein_ligand_covalent_event_edge"][
            "part_of_ligand_internal_topology"
        ] is False


def test_wrong_ligand_instance_fails_closed() -> None:
    pdb_id = "2R9F"
    text = (closure.REPO_ROOT / closure._raw_path(pdb_id)).read_text()
    indexed = list(enumerate(atom_site_owner.extract_atom_site_loop_rows_v0(text)))
    with pytest.raises(closure.ClosureValidationError, match="WRONG_OR_MISSING"):
        closure.select_ligand_instance_atoms_v1(
            indexed, "K2Z", "A", "999999", "1", "",
        )


def test_duplicate_observed_atom_mapping_fails_closed() -> None:
    topology = closure.load_component_topology_authorities_v1()["K2Z"]
    text = (closure.REPO_ROOT / closure._raw_path("2R9F")).read_text()
    rows = atom_site_owner.extract_atom_site_loop_rows_v0(text)
    selected = closure.select_ligand_instance_atoms_v1(
        list(enumerate(rows)), "K2Z", "A", "367", "1", "",
    )
    with pytest.raises(closure.ClosureValidationError, match="DUPLICATE_OR_EMPTY"):
        closure.map_observed_heavy_to_topology_v1(
            [*selected, selected[0]], topology, "CBM",
        )


def test_missing_retained_heavy_topology_atom_fails_closed() -> None:
    topology = closure.load_component_topology_authorities_v1()["K2Z"]
    text = (closure.REPO_ROOT / closure._raw_path("2R9F")).read_text()
    rows = atom_site_owner.extract_atom_site_loop_rows_v0(text)
    selected = closure.select_ligand_instance_atoms_v1(
        list(enumerate(rows)), "K2Z", "A", "367", "1", "",
    )
    missing = closure._atom_value(selected[0][1], "label_atom_id")
    mutated = dataclasses.replace(
        topology, atoms=tuple(atom for atom in topology.atoms if atom["atom_id"] != missing),
    )
    with pytest.raises(closure.ClosureValidationError, match="MISSING_RETAINED_HEAVY"):
        closure.map_observed_heavy_to_topology_v1(selected, mutated, "CBM")


def test_component_atoms_absent_from_observation_are_exposed_not_reconstructed(
    evidence: dict[str, object],
) -> None:
    samples = {sample["pdb_id"]: sample for sample in evidence["samples"]}  # type: ignore[index,union-attr]
    assert samples["2DJF"]["topology_mapping"]["topology_heavy_atoms_not_observed"] == [
        "N3", "N4"
    ]
    assert samples["4DCD"]["topology_mapping"]["topology_heavy_atoms_not_observed"] == [
        "O1", "O2", "O3", "S1"
    ]


def test_distance_based_bond_inference_is_absent(
    evidence: dict[str, object], manifest: dict[str, object],
) -> None:
    assert evidence["distance_based_bond_inference_used"] is False
    assert manifest["distance_based_bond_inference_used"] is False
    for authority in evidence["component_topology_authorities"].values():  # type: ignore[union-attr]
        assert authority["component_internal_bonds"]
        assert all(bond["source_value_order"] for bond in authority["component_internal_bonds"])


def test_explicit_hydrogen_is_excluded_before_model_projection(
    matrix: list[dict[str, str]], evidence: dict[str, object], manifest: dict[str, object],
) -> None:
    assert int(manifest["explicit_hydrogen_excluded_total"]) > 0
    assert sum(int(row["explicit_hydrogen_excluded_count"]) for row in matrix) == int(
        manifest["explicit_hydrogen_excluded_total"]
    )
    for sample in evidence["samples"]:  # type: ignore[index,union-attr]
        assert all(
            atom["type_symbol"] != "H"
            for atom in sample["canonical_model_bound_ligand_atoms"]
        )
        assert all(
            atom["type_symbol"] != "H"
            for atom in sample["canonical_pocket"]["retained_atoms"]
        )


def test_supported_exact10_channel_identity_is_exact() -> None:
    tokens = ["C", "N", "O", "S", "B", "BR", "CL", "P", "I", "F", "H"]
    rows = [(index, _synthetic_atom(token, str(index + 1), f"A{index}")) for index, token in enumerate(tokens)]
    retained, rejected, hydrogen_count = closure.realize_exact10_v1(rows, "ligand")
    assert rejected == []
    assert hydrogen_count == 1
    assert [atom["exact10_channel_index"] for atom in retained] == list(range(10))


@pytest.mark.parametrize("symbol", ["Xe", "", "not-an-element"])
def test_unsupported_or_invalid_nonh_rejects_whole_sample(symbol: str) -> None:
    rows = [
        (0, _synthetic_atom("C", "1", "C1")),
        (1, _synthetic_atom(symbol, "2", "X1")),
    ]
    retained, rejected, _ = closure.realize_exact10_v1(rows, "ligand")
    assert retained == []
    assert len(rejected) == 1
    assert rejected[0]["exact10_rejection"] in {
        "unsupported_nonhydrogen", "missing_or_invalid",
    }


def test_no_unknown_other_or_zero_vector_fallback(evidence: dict[str, object]) -> None:
    for sample in evidence["samples"]:  # type: ignore[index,union-attr]
        exact10 = sample["exact10"]
        assert exact10["unknown_or_other_channel_present"] is False
        assert exact10["zero_vector_fallback_used"] is False
        channels = [
            atom["exact10_channel_index"]
            for atom in sample["canonical_model_bound_ligand_atoms"]
            + sample["canonical_pocket"]["retained_atoms"]
        ]
        assert channels and set(channels) <= set(range(10))


def test_pockets_are_nonempty_and_retain_target_cys_sg(matrix: list[dict[str, str]]) -> None:
    assert all(int(row["pocket_atom_count"]) > 0 for row in matrix)
    assert all(row["target_cys_present"] == "true" for row in matrix)
    assert all(row["target_sg_present"] == "true" for row in matrix)
    assert all(row["pocket_status"] == "POCKET_PASS" for row in matrix)


def test_empty_pocket_seed_fails_closed() -> None:
    with pytest.raises(closure.ClosureValidationError, match="EMPTY_LIGAND_POCKET_SEED"):
        closure.build_canonical_pocket_v1([], [])


def test_k36_shared_topology_does_not_bypass_independent_mapping(
    matrix: list[dict[str, str]], evidence: dict[str, object], manifest: dict[str, object],
) -> None:
    k36 = [row for row in matrix if row["ligand_component_id"] == "K36"]
    assert manifest["k36_shared_topology_reuse"] is True
    assert manifest["k36_independent_sample_mapping_count"] == 5
    assert len({row["topology_source_sha256"] for row in k36}) == 1
    assert len({row["raw_sha256"] for row in k36}) == 5
    assert all(row["event_mapping_status"].endswith("PASS") for row in k36)
    assert all(row["topology_atom_mapping_status"].endswith("PASS") for row in k36)
    assert len([s for s in evidence["samples"] if s["ligand_component_id"] == "K36"]) == 5  # type: ignore[index,union-attr]


def test_5wkj_altloc_b_is_selected_from_exact_event(evidence: dict[str, object]) -> None:
    sample = next(sample for sample in evidence["samples"] if sample["pdb_id"] == "5WKJ")  # type: ignore[index,union-attr]
    assert sample["topology_mapping"]["selected_ligand_altloc"] == "B"
    assert sample["explicit_event"]["ligand_endpoint"]["label_alt_id"] == "B"


def test_all_recovered7_authority_audits_are_complete_and_derive_final_status(
    matrix: list[dict[str, str]], evidence: dict[str, object],
    manifest: dict[str, object],
) -> None:
    assert all(row["mechanical_closure_status"] == "MECHANICAL_CLOSURE_PASS" for row in matrix)
    rows = {row["canonical_candidate_id"]: row for row in matrix}
    for sample in evidence["samples"]:  # type: ignore[index,union-attr]
        audit = sample["downstream_chemistry_authority_audit"]
        dimensions = {
            dimension: audit[dimension]
            for dimension in closure.REQUIRED_DOWNSTREAM_DIMENSIONS
        }
        derived_status, derived_issue = (
            closure.derive_downstream_chemistry_classification_v1(dimensions)
        )
        row = rows[sample["canonical_candidate_id"]]
        assert audit["audit_complete"] is True
        assert audit["combined_status"] == derived_status
        assert audit["primary_remaining_issue"] == derived_issue
        assert sample["downstream_chemistry_label_status"] == derived_status
        assert row["downstream_chemistry_label_status"] == derived_status
        assert row["primary_remaining_issue"] == derived_issue
    assert manifest["mechanical_closure_pass_count"] == 7
    assert manifest["downstream_chemistry_authority_audit_complete"] is True
    assert manifest["downstream_authority_audited_candidate_count"] == 7
    assert sum(
        manifest[field] for field in (
            "downstream_already_authoritative_count",
            "downstream_automatic_rule_available_count",
            "downstream_human_chemistry_review_required_count",
        )
    ) == 7


def test_current_authority_sources_are_sha_bound_and_not_reusable_approved() -> None:
    context = closure.load_downstream_authority_context_v1()
    assert len(context["binding_rows"]) == 7
    assert len(context["sample_bound_records"]) == 11
    assert context["approved_family_rows"] == []
    assert context["approved_warhead_rows"] == []
    assert context["approved_role_rows"] == []
    for path, expected in closure.DOWNSTREAM_AUTHORITY_SOURCE_SHA256.items():
        actual = closure._downstream_source_path(closure.REPO_ROOT, path)
        assert hashlib.sha256(actual.read_bytes()).hexdigest() == expected


def test_downstream_authority_source_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        closure.DOWNSTREAM_AUTHORITY_SOURCE_SHA256,
        closure.FAMILY_WARHEAD_AUTHORITY_REGISTRY,
        "0" * 64,
    )
    with pytest.raises(
        closure.ClosureValidationError,
        match="DOWNSTREAM_AUTHORITY_SOURCE_SHA256_MISMATCH",
    ):
        closure.load_downstream_authority_context_v1()


def test_build_sample_has_no_unconditional_human_default() -> None:
    source = Path(closure.__file__).read_text()
    build_sample_source = source[source.index("def _build_sample("):source.index(
        "def build_covapie_cys_sg_recovered7_"
    )]
    assert 'downstream = "HUMAN_CHEMISTRY_REVIEW_REQUIRED"' not in build_sample_source
    assert "build_downstream_chemistry_authority_audit_v1" in build_sample_source
    assert 'downstream = downstream_authority_audit["combined_status"]' in build_sample_source


def test_current11_sample_bound_authority_cannot_authorize_recovered7() -> None:
    context = closure.load_downstream_authority_context_v1()
    current11 = {
        (row["pdb_id"], row["ligand_comp_id"])
        for row in context["sample_bound_records"]
    }
    assert not (current11 & set(closure.RECOVERED_IDENTITIES))
    for snapshot_row in closure.derive_recovered7_rows_v1():
        audit = closure.build_downstream_chemistry_authority_audit_v1(
            snapshot_row, context,
        )
        for dimension in ("warhead_atom_set", "attachment_boundary"):
            assert audit[dimension]["authority_status"] == (
                "SAMPLE_BOUND_AUTHORITY_NO_MATCH"
            )
            assert audit[dimension]["match_count"] == 0
            assert audit[dimension]["rule_scope"] == (
                "SAMPLE_BOUND_CURRENT11_BOUNDARY_AUTHORITY"
            )


def test_synthetic_exact_one_approved_reusable_rules_are_automatic() -> None:
    audits = _synthetic_authority_audits()
    assert closure.derive_downstream_chemistry_classification_v1(audits) == (
        "AUTOMATIC_RULE_AVAILABLE",
        "AUTOMATIC_CHEMISTRY_LABEL_EXECUTION_NOT_PERFORMED",
    )


def test_claimed_exact_one_rule_without_version_binding_fails_closed() -> None:
    audits = _synthetic_authority_audits()
    audits["warhead_rule"]["version_bound"] = False
    assert closure.derive_downstream_chemistry_classification_v1(audits) == (
        "HUMAN_CHEMISTRY_REVIEW_REQUIRED",
        "WARHEAD_RULE_APPROVED_RULE_NO_MATCH",
    )


def test_synthetic_zero_match_requires_human_review() -> None:
    audits = _synthetic_authority_audits()
    audits["reaction_family"] = closure._authority_dimension_v1(
        authority_status="APPROVED_REUSABLE_RULE_NO_MATCH",
        source_path=None,
        authority_id=None,
        rule_scope="REUSABLE_APPROVED_RULE",
        match_count=0,
        applicability_reason="synthetic zero-match result",
    )
    assert closure.derive_downstream_chemistry_classification_v1(audits) == (
        "HUMAN_CHEMISTRY_REVIEW_REQUIRED",
        "REACTION_FAMILY_APPROVED_RULE_NO_MATCH",
    )


def test_synthetic_multi_match_requires_human_review() -> None:
    audits = _synthetic_authority_audits()
    audits["warhead_rule"] = closure._authority_dimension_v1(
        authority_status="APPROVED_REUSABLE_RULE_MATCH",
        source_path=None,
        authority_id="SYNTHETIC_NON_UNIQUE_RULES",
        rule_scope="REUSABLE_APPROVED_RULE",
        match_count=2,
        applicability_reason="synthetic multi-match result",
    )
    assert closure.derive_downstream_chemistry_classification_v1(audits) == (
        "HUMAN_CHEMISTRY_REVIEW_REQUIRED", "WARHEAD_RULE_MULTI_MATCH",
    )


@pytest.mark.parametrize(
    "status", ["CANDIDATE_ONLY_RULE_MATCH", "UNAPPROVED_RULE_MATCH"],
)
def test_synthetic_nonapproved_rule_requires_human_review(status: str) -> None:
    audits = _synthetic_authority_audits()
    audits["reaction_family"] = closure._authority_dimension_v1(
        authority_status=status,
        source_path=None,
        authority_id="SYNTHETIC_NONAPPROVED_RULE",
        rule_scope="CANDIDATE_OR_UNAPPROVED_RULE",
        match_count=1,
        applicability_reason="synthetic non-approved rule result",
    )
    assert closure.derive_downstream_chemistry_classification_v1(audits) == (
        "HUMAN_CHEMISTRY_REVIEW_REQUIRED",
        "REACTION_FAMILY_RULE_NOT_APPROVED",
    )


def test_synthetic_complete_sample_bound_authority_is_already_authoritative() -> None:
    audits = _synthetic_authority_audits(
        status="SAMPLE_BOUND_AUTHORITY_MATCH",
        rule_scope="SAMPLE_BOUND_AUTHORITY",
    )
    assert closure.derive_downstream_chemistry_classification_v1(audits) == (
        "ALREADY_AUTHORITATIVE", "NONE",
    )


def test_partial_automatic_coverage_retained_when_boundary_is_ambiguous() -> None:
    audits = _synthetic_authority_audits()
    audits["attachment_boundary"] = closure._authority_dimension_v1(
        authority_status="AMBIGUOUS",
        source_path=None,
        authority_id=None,
        rule_scope="REUSABLE_APPROVED_DETERMINISTIC_RULE",
        match_count=2,
        applicability_reason="synthetic boundary candidates",
        ambiguity_reason="two invariant-passing boundaries remain",
    )
    assert audits["reaction_family"]["authority_status"] == (
        "APPROVED_REUSABLE_RULE_MATCH"
    )
    assert audits["warhead_rule"]["authority_status"] == (
        "APPROVED_REUSABLE_RULE_MATCH"
    )
    assert closure.derive_downstream_chemistry_classification_v1(audits) == (
        "HUMAN_CHEMISTRY_REVIEW_REQUIRED", "ATTACHMENT_BOUNDARY_MULTI_MATCH",
    )


def test_k36_downstream_authority_is_audited_independently(
    evidence: dict[str, object], manifest: dict[str, object],
) -> None:
    k36 = [
        sample for sample in evidence["samples"]  # type: ignore[index,union-attr]
        if sample["ligand_component_id"] == "K36"
    ]
    assert len(k36) == 5
    assert manifest["k36_independent_downstream_authority_audit_count"] == 5
    assert {sample["pdb_id"] for sample in k36} == {
        "4DCD", "6WTT", "4F49", "6L70", "5WKJ",
    }
    assert {
        sample["downstream_chemistry_authority_audit"]["audited_sample_identity"]
        for sample in k36
    } == {f'{sample["pdb_id"]}/K36' for sample in k36}


def test_future_chemistry_readiness_paths_are_not_conflated(
    manifest: dict[str, object],
) -> None:
    assert manifest["ready_for_automated_chemistry_label_execution"] == (
        manifest["downstream_automatic_rule_available_count"] > 0
    )
    assert manifest["ready_for_targeted_chemistry_review_package_generation"] == (
        manifest["downstream_human_chemistry_review_required_count"] > 0
    )


def test_build_executes_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network access forbidden")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    built = closure.build_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_artifacts_v1()
    assert set(built) == set(closure.OUTPUT_FILES)


def test_no_geometry_minimization_model_or_training(manifest: dict[str, object]) -> None:
    false_fields = (
        "network_request_executed", "raw_structure_downloaded", "ccd_downloaded",
        "topology_downloaded", "inverse_reaction_chemistry_executed",
        "pre_geometry_reconstruction_executed", "torsion_sampling_executed",
        "mmff_executed", "uff_executed", "rdkit_minimization_executed",
        "geometry_loss_activation", "model_forward", "backward", "optimizer_step",
        "trainer_fit", "formal_training", "rl",
    )
    assert all(manifest[field] is False for field in false_fields)


def test_double_build_is_byte_identical(artifacts: dict[str, bytes]) -> None:
    second = closure.build_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_artifacts_v1()
    assert second == artifacts


def test_materializer_writes_only_three_deterministic_artifacts(
    tmp_path: Path, artifacts: dict[str, bytes],
) -> None:
    hashes = closure.materialize_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1(
        output_root=tmp_path,
    )
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(closure.OUTPUT_FILES)
    assert hashes == {
        name: hashlib.sha256(artifacts[name]).hexdigest() for name in closure.OUTPUT_FILES
    }


def test_successor_runtime_has_no_live_head_baseline_gate() -> None:
    source = Path(closure.__file__).read_text()
    assert "rev-parse" not in source
    assert "git rev-list" not in source
    assert "HEAD ==" not in source
    assert "urllib" not in source
    assert "requests" not in source
    assert "DetermineBonds" not in source
