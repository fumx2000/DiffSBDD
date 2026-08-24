from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from covalent_ext import (
    covapie_ffq_warhead_rule_authority_creator_v1 as creator,
)


REPO = Path(__file__).resolve().parents[1]
DECISION = REPO.parent / (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "project-level-warhead-rule-human-decision-v1/"
    "ffq_project_level_warhead_rule_human_decision_v1.json"
)
CHECKER_PATH = REPO / (
    "scripts/check_covapie_ffq_warhead_rule_authority_creator_v1.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_ffq_warhead_rule_authority_creator_v1", CHECKER_PATH
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)

EXACT3 = tuple(sorted(path.as_posix() for path in checker.CANDIDATE_PATHS))
EXPECTED_AUTHORITY_PAYLOAD_CANONICAL_SHA256 = (
    "1a8d8751e50ad6eb427c02fb49731e00a2d688d4dee7dd7e936f694b569953b6"
)
EXPECTED_BUILD_RESULT_CANONICAL_SHA256 = (
    "57439801145521abe0d76b18cc63ba26d8518ce7e63b8134fc9ad2670a53c4f1"
)
SEMANTIC_FIELDS = (
    "semantic_signature_version",
    "authority_kind",
    "reaction_family_authority_id",
    "applicability_scope",
    "target_condition",
    "ligand_reactive_atom_contract",
    "active_warhead_semantics",
    "active_warhead_atom_contract",
    "canonical_local_warhead_rule_contract",
    "precursor_local_reaction_evidence_contract",
    "retained_role_profile",
    "retained_framework_boundary",
    "formed_protein_ligand_event",
    "pre_reaction_graph_authority_status",
    "pre_reaction_bond_order_authority_status",
    "mechanism_claim_status",
    "reversibility_claim_status",
)
AUTHORITY_FIELDS = (
    "authority_schema_version",
    "authority_kind",
    "authority_id",
    "semantic_name",
    "canonical_semantic_signature",
    "canonical_semantic_signature_sha256",
    "source_candidate_to_authority_provenance",
    "source_human_review_provenance",
)


@pytest.fixture(scope="module")
def decision_bytes() -> bytes:
    return DECISION.read_bytes()


@pytest.fixture(scope="module")
def decision(decision_bytes: bytes) -> dict[str, object]:
    return creator.validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(
        decision_bytes
    )


@pytest.fixture(scope="module")
def result(decision_bytes: bytes) -> dict[str, object]:
    return creator.build_covapie_ffq_warhead_rule_authority_v1(decision_bytes)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _payload(result: dict[str, object]) -> dict[str, Any]:
    return copy.deepcopy(result["warhead_rule_authority"])


def _semantic(result: dict[str, object]) -> dict[str, Any]:
    return _payload(result)["canonical_semantic_signature"]


def _set_path(target: dict[str, Any], path: tuple[object, ...], value: Any) -> None:
    current: Any = target
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value


def _precommit_observation() -> dict[str, object]:
    return {
        "branch": "main",
        "head": checker.BASELINE_COMMIT,
        "origin_main": checker.BASELINE_COMMIT,
        "ahead": 0,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin_main": True,
        "modified_tracked_paths": (),
        "staged_paths": (),
        "untracked_paths": EXACT3,
        "tracked_candidate_paths": (),
    }


def _published_observation() -> dict[str, object]:
    successor = "f" * 40
    return {
        "branch": "main",
        "head": successor,
        "origin_main": successor,
        "ahead": 0,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin_main": True,
        "modified_tracked_paths": (),
        "staged_paths": (),
        "untracked_paths": (),
        "tracked_candidate_paths": EXACT3,
    }


def test_real_human_decision_is_byte_bound_and_exact(
    decision_bytes: bytes, decision: dict[str, object]
) -> None:
    assert len(decision_bytes) == creator.HUMAN_DECISION_BYTE_COUNT == 37455
    assert hashlib.sha256(decision_bytes).hexdigest() == (
        creator.HUMAN_DECISION_SHA256
    )
    assert decision["decision_status"] == (
        "HUMAN_APPROVED_PROJECT_LEVEL_WARHEAD_RULE_DECISION"
    )
    assert decision["decision_role"] == (
        "PROJECT_LEVEL_WARHEAD_RULE_HUMAN_APPROVAL_RECORD_NOT_AUTHORITY_PAYLOAD"
    )
    assert decision["project_level_warhead_rule_approval_created"] is True
    assert decision["warhead_rule_authority_created"] is False
    assert decision["warhead_rule_registration_performed"] is False


def test_public_validator_returns_detached_decision_copy(
    decision_bytes: bytes,
) -> None:
    first = creator.validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(
        decision_bytes
    )
    first["decision_status"] = "MUTATED_CALLER_COPY"
    second = creator.validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(
        decision_bytes
    )
    assert second["decision_status"] != first["decision_status"]


def test_build_is_deterministic_and_does_not_modify_source(
    decision_bytes: bytes,
) -> None:
    before = DECISION.read_bytes()
    first = creator.build_covapie_ffq_warhead_rule_authority_v1(decision_bytes)
    second = creator.build_covapie_ffq_warhead_rule_authority_v1(decision_bytes)
    assert first == second
    assert _canonical_bytes(first) == _canonical_bytes(second)
    assert len(_canonical_bytes(first)) == 9586
    assert hashlib.sha256(_canonical_bytes(first)).hexdigest() == (
        EXPECTED_BUILD_RESULT_CANONICAL_SHA256
    )
    assert DECISION.read_bytes() == before


def test_authority_v2_wrapper_identity_and_exact8_fields(
    result: dict[str, object],
) -> None:
    payload = result["warhead_rule_authority"]
    assert tuple(payload) == AUTHORITY_FIELDS
    assert payload["authority_schema_version"] == (
        "covapie_cys_sg_warhead_rule_authority_payload_v2"
    )
    assert payload["authority_kind"] == "warhead_rule"
    assert payload["authority_id"] == creator.FINAL_AUTHORITY_ID
    assert payload["semantic_name"] == (
        "CYS_SG_FFQ_FCN_EXACT_COMPONENT_ATOM_WARHEAD_RULE_V1"
    )
    assert payload["canonical_semantic_signature_sha256"] == (
        creator.APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
    )
    creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(payload)
    assert len(_canonical_bytes(payload)) == 8130
    assert hashlib.sha256(_canonical_bytes(payload)).hexdigest() == (
        EXPECTED_AUTHORITY_PAYLOAD_CANONICAL_SHA256
    )


def test_canonical_roundtrip_reordered_exact_payload_passes_public_validator(
    result: dict[str, object],
) -> None:
    payload = result["warhead_rule_authority"]
    canonical_bytes = _canonical_bytes(payload)
    parsed = json.loads(canonical_bytes.decode("ascii"))
    assert parsed == payload
    assert tuple(parsed) != AUTHORITY_FIELDS
    assert tuple(parsed["canonical_semantic_signature"]) != SEMANTIC_FIELDS
    assert tuple(parsed["source_candidate_to_authority_provenance"]) != tuple(
        payload["source_candidate_to_authority_provenance"]
    )
    assert tuple(parsed["source_human_review_provenance"]) != tuple(
        payload["source_human_review_provenance"]
    )
    creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(parsed)


def test_approved_semantics_exact17_rehash_and_final_id(
    result: dict[str, object],
) -> None:
    semantic = result["warhead_rule_authority"]["canonical_semantic_signature"]
    assert tuple(semantic) == SEMANTIC_FIELDS
    assert creator.authority_semantic_signature_sha256_v1(semantic) == (
        "8162eff17624bd4a080e24e0a2537a840baa68c6c2f28cd78a91fbf23cc8998a"
    )
    assert creator.authority_id_from_semantic_signature_v1(semantic) == (
        "COVAPIE_CYS_SG_WARHEAD_RULE_8162EFF17624BD4A"
    )
    assert semantic["reaction_family_authority_id"] == (
        "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
    )


def test_public_api_is_minimal_and_v2_named() -> None:
    expected_functions = {
        "canonical_authority_semantic_signature_json_v1",
        "authority_semantic_signature_sha256_v1",
        "authority_id_from_semantic_signature_v1",
        "validate_covapie_ffq_project_level_warhead_rule_human_decision_v1",
        "validate_covapie_ffq_warhead_rule_authority_payload_v2",
        "build_covapie_ffq_warhead_rule_authority_v1",
    }
    assert expected_functions.issubset(creator.__all__)
    assert "validate_covapie_ffq_warhead_rule_authority_payload_v1" not in (
        creator.__all__
    )


def test_component_bound_scope_is_exact_conjunction(
    result: dict[str, object],
) -> None:
    scope = _semantic(result)["applicability_scope"]
    assert scope["scope_kind"] == (
        "EXACT_CANONICAL_WARHEAD_RULE_SIGNATURE_PLUS_EXACT_COMPONENT_ATOM_CONTRACT"
    )
    assert scope["all_applicability_constraints_conjunctive"] is True
    assert scope["canonical_local_rule_signature_alone_sufficient"] is False
    assert scope["component_identity_alone_sufficient"] is False
    assert scope["exact_local_rule_signature_required"] is True
    assert scope["exact_component_atom_contract_required"] is True
    assert scope[
        "require_exact_precursor_local_reaction_evidence_contract"
    ] is True
    assert scope["cross_signature_propagation_allowed"] is False


def test_b96d_local_rule_rehash_and_material_dimensions(
    result: dict[str, object],
) -> None:
    semantic = _semantic(result)
    contract = semantic["canonical_local_warhead_rule_contract"]
    local = contract["canonical_local_rule"]
    digest = creator.authority_semantic_signature_sha256_v1(local)
    assert digest == creator.CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
    assert digest == contract["canonical_local_rule_sha256"]
    assert digest == semantic["applicability_scope"][
        "required_canonical_local_rule_sha256"
    ]
    assert local["rule_kind"] == "canonical_local_graph_exact_match_v1"
    assert local["selected_signature_radius"] == 1
    assert local["center_atom"] == {
        "canonical_local_atom_id": "center",
        "element": "C",
        "formal_charge": 0,
        "reactive": True,
    }
    assert [atom["element"] for atom in local["local_atoms"]] == [
        "C",
        "C",
        "C",
        "O",
    ]
    assert len(local["local_bonds"]) == 4
    assert local["reaction_delta"]["leaving_group_count"] == 0
    assert local["reaction_delta"]["reaction_delta_class"] == (
        "intact_parent_atom_inventory_match"
    )
    assert local["target_condition"] == {
        "formed_bond_order": "single",
        "residue": "CYS",
        "residue_atom": "SG",
    }


def test_ffq_fcn_atom_exact_active_warhead_and_boundary(
    result: dict[str, object],
) -> None:
    semantic = _semantic(result)
    assert semantic["ligand_reactive_atom_contract"] == {
        "atom_id": "C1",
        "atom_role": "LIGAND_REACTIVE_CENTER",
        "element": "C",
        "ligand_component_id": "FFQ",
    }
    assert [item["atom_id"] for item in semantic["active_warhead_atom_contract"]] == [
        "C1",
        "C2",
        "C3",
        "O1",
    ]
    assert semantic["active_warhead_semantics"] == (
        "REACTION_COMPETENT_ACTIVE_WARHEAD_V1"
    )
    assert semantic["retained_role_profile"] == (
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    )
    assert semantic["retained_framework_boundary"] == {
        "edge_kind": "COMPONENT_INTERNAL_RETAINED_FRAMEWORK_BOUNDARY",
        "ligand_component_id": "FFQ",
        "scaffold_side_atom_id": "P1",
        "warhead_side_atom_id": "C2",
        "bond_order": "single",
        "component_internal_topology_edge": True,
    }


def test_precursor_reaction_delta_is_exact_and_non_authoritative(
    result: dict[str, object],
) -> None:
    precursor = _semantic(result)["precursor_local_reaction_evidence_contract"]
    assert precursor["precursor_component_id"] == "FCN"
    assert precursor["precursor_reactive_atom"] == {
        "atom_id": "C2",
        "element": "C",
        "formal_charge": 0,
    }
    assert precursor["mapped_post_ligand_atom"] == {
        "atom_id": "C1",
        "element": "C",
        "ligand_component_id": "FFQ",
    }
    assert precursor["mapping_status_requirement"] == (
        "UNIQUE_REACTIVE_CENTER_MAPPING_WITH_SYMMETRY_EQUIVALENT_FULL_ATOM_MAPPINGS"
    )
    delta = precursor["reaction_delta"]
    assert delta["removed_precursor_internal_heavy_bond_count"] == 1
    assert delta["removed_precursor_internal_heavy_bonds"] == [
        {
            "mapped_absent_post_atom_id_1": "C1",
            "mapped_absent_post_atom_id_2": "O1",
            "normalized_bond_order": "single",
            "precursor_atom_id_1": "C2",
            "precursor_atom_id_2": "O",
        }
    ]
    for field in (
        "added_post_internal_heavy_bond_count",
        "bond_order_change_count",
        "formal_charge_change_count",
        "heavy_atom_addition_count",
        "heavy_atom_removal_count",
        "leaving_group_count",
    ):
        assert delta[field] == 0
    assert precursor["establishes_pre_reaction_graph_authority"] is False
    assert precursor["establishes_pre_reaction_bond_order_authority"] is False
    assert precursor["establishes_mechanism_authority"] is False


def test_formed_bond_pre_and_claim_boundaries(result: dict[str, object]) -> None:
    semantic = _semantic(result)
    formed = semantic["formed_protein_ligand_event"]
    assert formed["formed_bond_order_authority_status"] == "NOT_ESTABLISHED"
    assert formed["component_internal_topology_edge"] is False
    local_target = semantic["canonical_local_warhead_rule_contract"][
        "canonical_local_rule"
    ]["target_condition"]
    assert local_target["formed_bond_order"] == "single"
    assert semantic["pre_reaction_graph_authority_status"] == "NOT_ESTABLISHED"
    assert semantic["pre_reaction_bond_order_authority_status"] == (
        "NOT_ESTABLISHED"
    )
    assert semantic["mechanism_claim_status"] == "NOT_CLAIMED"
    assert semantic["reversibility_claim_status"] == "NOT_CLAIMED"


def test_candidate_family_and_human_provenance_are_outside_semantics(
    result: dict[str, object],
) -> None:
    payload = result["warhead_rule_authority"]
    provenance = payload["source_candidate_to_authority_provenance"]
    semantic_bytes = _canonical_bytes(payload["canonical_semantic_signature"])
    assert provenance["source_candidate_warhead_rule_id"] == (
        "COVAPIE_CYS_SG_WARHEAD_RULE_B96D4E846C704691"
    )
    assert provenance["final_warhead_rule_authority_id"] == (
        "COVAPIE_CYS_SG_WARHEAD_RULE_8162EFF17624BD4A"
    )
    assert provenance["source_candidate_reaction_family_id"] == (
        "COVAPIE_CYS_SG_REACTION_FAMILY_B1FD795D4D442304"
    )
    assert provenance["final_reaction_family_authority_id"] == (
        "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
    )
    assert provenance[
        "project_level_warhead_rule_human_decision_record_sha256"
    ] == creator.HUMAN_DECISION_SHA256
    assert creator.SOURCE_CANDIDATE_WARHEAD_RULE_ID.encode() not in semantic_bytes
    assert b"source_candidate" not in semantic_bytes
    assert b"provenance" not in semantic_bytes


def test_creation_summary_preserves_all_authority_and_training_boundaries(
    result: dict[str, object],
) -> None:
    summary = result["creation_readiness_summary"]
    for field in (
        "project_level_warhead_rule_human_decision_consumed",
        "reaction_family_authority_dependency_verified",
        "warhead_rule_authority_payload_ready",
        "warhead_rule_authority_payload_built_in_memory",
        "warhead_rule_creator_implemented",
        "feature_semantics_audit_required_before_formal_training",
    ):
        assert summary[field] is True
    for field in (
        "human_decision_modified",
        "reaction_family_registration_performed",
        "persisted_warhead_rule_authority_created",
        "warhead_rule_authority_created",
        "warhead_rule_registration_performed",
        "authority_file_materialized",
        "effective_authority_updated",
        "runtime_authority_created",
        "runtime_auto_admission_authorized",
        "generic_warhead_rule_identity_policy_published",
        "generic_warhead_rule_scope_contract_published",
        "SMARTS_generation_performed",
        "reusable_chemistry_authority_created",
        "reconciliation_changed",
        "tensorizer_integration_performed",
        "training_admission_created",
        "training_dataset_changed",
        "runtime_admission_changed",
        "split_changed",
        "feature_semantics_audit_performed",
        "ready_for_training",
        "training_performed",
        "commit_performed",
        "push_performed",
        "network_performed",
    ):
        assert summary[field] is False


@pytest.mark.parametrize(
    "bad_payload",
    (
        b"",
        b"x" * creator.HUMAN_DECISION_BYTE_COUNT,
        bytearray(b"x" * creator.HUMAN_DECISION_BYTE_COUNT),
    ),
    ids=("byte-count", "sha256", "non-bytes"),
)
def test_human_decision_byte_binding_fails_closed(bad_payload: object) -> None:
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(  # type: ignore[arg-type]
            bad_payload
        )


@pytest.mark.parametrize(
    "bad_payload",
    (
        b'{"x":1,"x":2}\n',
        b'{"x":NaN}\n',
        b'{"x":"\xff"}\n',
        b'{"x":}\n',
        b'\xef\xbb\xbf{"x":1}\n',
        b'{"x":"x\x00y"}\n',
        b'{"x":1}\r\n',
    ),
    ids=("duplicate", "nonfinite", "utf8", "json", "bom", "nul", "cr"),
)
def test_human_decision_strict_parser_rejects_invalid_text(
    monkeypatch: pytest.MonkeyPatch, bad_payload: bytes
) -> None:
    monkeypatch.setattr(creator, "HUMAN_DECISION_BYTE_COUNT", len(bad_payload))
    monkeypatch.setattr(
        creator, "HUMAN_DECISION_SHA256", hashlib.sha256(bad_payload).hexdigest()
    )
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(
            bad_payload
        )


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("schema_version",), "SCHEMA_DRIFT"),
        (("decision_status",), "STATUS_DRIFT"),
        (("decision_role",), "ROLE_DRIFT"),
        (("human_approval", "human_reviewer_id"), "reviewer-drift"),
        (("human_approval", "human_attestation"), "attestation-drift"),
        (("human_approval", "approval_scope"), "SCOPE_DRIFT"),
        (("human_approval", "approved_at_utc"), "2026-08-24T05:35:01Z"),
        (
            ("source_candidate_identity", "source_candidate_warhead_rule_id"),
            "COVAPIE_CYS_SG_WARHEAD_RULE_0000000000000000",
        ),
        (
            ("source_candidate_identity", "candidate_canonical_local_rule_sha256"),
            "0" * 64,
        ),
        (
            (
                "approved_family_authority_linkage",
                "reaction_family_authority_id_human_approved_for_rule_linkage",
            ),
            "COVAPIE_CYS_SG_REACTION_FAMILY_B1FD795D4D442304",
        ),
        (
            (
                "approved_family_authority_linkage",
                "materialized_family_authority_file_sha256",
            ),
            "0" * 64,
        ),
        (
            ("approved_warhead_rule_semantic_signature_sha256",),
            "0" * 64,
        ),
        (("approved_future_final_warhead_rule_authority_id",), "WRONG_FINAL_ID"),
    ),
    ids=(
        "schema",
        "status",
        "role",
        "reviewer",
        "attestation",
        "approval-scope",
        "approval-time",
        "candidate-id",
        "local-sha",
        "family-id",
        "family-file-sha",
        "semantic-sha",
        "future-id",
    ),
)
def test_human_decision_invariant_drift_fails_closed(
    decision: dict[str, object], path: tuple[object, ...], value: object
) -> None:
    mutated = copy.deepcopy(decision)
    _set_path(mutated, path, value)
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator._validate_human_decision_document_v1(mutated)


@pytest.mark.parametrize("mutation", ("missing", "non-approve"))
def test_human_review_exact14_fails_closed(
    decision: dict[str, object], mutation: str
) -> None:
    mutated = copy.deepcopy(decision)
    if mutation == "missing":
        mutated["human_review_items"].pop()
    else:
        mutated["human_review_items"][7]["human_response"] = "REJECT"
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator._validate_human_decision_document_v1(mutated)


@pytest.mark.parametrize(
    "mutation",
    ("add", "remove", "rename"),
)
def test_human_decision_semantic_exact17_inventory_fails_closed(
    decision: dict[str, object], mutation: str
) -> None:
    mutated = copy.deepcopy(decision)
    semantic = mutated["approved_canonical_warhead_rule_semantic_signature"]
    if mutation == "add":
        semantic["extra"] = False
    elif mutation == "remove":
        semantic.pop("mechanism_claim_status")
    else:
        semantic["mechanism_status"] = semantic.pop("mechanism_claim_status")
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator._validate_human_decision_document_v1(mutated)


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("applicability_scope", "scope_kind"), "SIGNATURE_ONLY"),
        (
            (
                "applicability_scope",
                "canonical_local_rule_signature_alone_sufficient",
            ),
            True,
        ),
        (("applicability_scope", "component_identity_alone_sufficient"), True),
        (
            ("applicability_scope", "all_applicability_constraints_conjunctive"),
            False,
        ),
        (("applicability_scope", "exact_local_rule_signature_required"), False),
        (("applicability_scope", "exact_component_atom_contract_required"), False),
        (("applicability_scope", "cross_signature_propagation_allowed"), True),
        (("applicability_scope", "required_ligand_component_id"), "OTHER"),
        (("applicability_scope", "required_ligand_reactive_atom_id"), "C2"),
        (("applicability_scope", "required_precursor_component_id"), "OTHER"),
        (("applicability_scope", "required_precursor_reactive_atom_id"), "C1"),
        (
            ("applicability_scope", "required_active_warhead_atom_ids"),
            ["C1", "O1"],
        ),
        (("applicability_scope", "required_retained_role_profile"), "DRIFT"),
        (
            (
                "applicability_scope",
                "required_retained_framework_boundary",
                "scaffold_side_atom_id",
            ),
            "O2",
        ),
        (
            (
                "applicability_scope",
                "required_retained_framework_boundary",
                "warhead_side_atom_id",
            ),
            "C1",
        ),
        (
            (
                "applicability_scope",
                "require_exact_precursor_local_reaction_evidence_contract",
            ),
            False,
        ),
    ),
    ids=(
        "scope-kind",
        "local-alone",
        "component-alone",
        "not-conjunctive",
        "local-not-required",
        "component-not-required",
        "cross-signature",
        "ffq-component",
        "c1-reactive",
        "fcn-component",
        "fcn-c2",
        "active-atoms",
        "role-profile",
        "boundary-p1",
        "boundary-c2",
        "precursor-contract-required",
    ),
)
def test_component_bound_scope_drift_fails_closed(
    result: dict[str, object], path: tuple[object, ...], value: object
) -> None:
    payload = _payload(result)
    _set_path(payload["canonical_semantic_signature"], path, value)
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(payload)


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (
            (
                "canonical_local_warhead_rule_contract",
                "canonical_local_rule",
                "selected_signature_radius",
            ),
            2,
        ),
        (
            (
                "canonical_local_warhead_rule_contract",
                "canonical_local_rule",
                "center_atom",
                "element",
            ),
            "N",
        ),
        (
            (
                "canonical_local_warhead_rule_contract",
                "canonical_local_rule",
                "center_atom",
                "formal_charge",
            ),
            1,
        ),
        (
            (
                "canonical_local_warhead_rule_contract",
                "canonical_local_rule",
                "center_atom",
                "reactive",
            ),
            False,
        ),
        (
            (
                "canonical_local_warhead_rule_contract",
                "canonical_local_rule",
                "local_bonds",
                0,
                "normalized_bond_order",
            ),
            "double",
        ),
        (
            (
                "canonical_local_warhead_rule_contract",
                "canonical_local_rule",
                "reaction_delta",
                "reaction_delta_class",
            ),
            "changed",
        ),
        (
            (
                "precursor_local_reaction_evidence_contract",
                "reaction_delta",
                "removed_precursor_internal_heavy_bond_count",
            ),
            0,
        ),
        (
            (
                "precursor_local_reaction_evidence_contract",
                "reaction_delta",
                "removed_precursor_internal_heavy_bonds",
                0,
                "normalized_bond_order",
            ),
            "double",
        ),
        (
            (
                "formed_protein_ligand_event",
                "formed_bond_order_authority_status",
            ),
            "ESTABLISHED_SINGLE",
        ),
        (("pre_reaction_graph_authority_status",), "ESTABLISHED"),
        (("pre_reaction_bond_order_authority_status",), "ESTABLISHED"),
        (("mechanism_claim_status",), "CLAIMED"),
        (("reversibility_claim_status",), "REVERSIBLE"),
    ),
    ids=(
        "radius",
        "center-element",
        "center-charge",
        "center-reactive",
        "local-bond",
        "reaction-delta",
        "removed-bond-count",
        "removed-bond-order",
        "formed-authority",
        "pre-graph",
        "pre-bond-order",
        "mechanism",
        "reversibility",
    ),
)
def test_scientific_semantic_drift_fails_closed(
    result: dict[str, object], path: tuple[object, ...], value: object
) -> None:
    payload = _payload(result)
    _set_path(payload["canonical_semantic_signature"], path, value)
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(payload)


@pytest.mark.parametrize(
    "mutation",
    (
        "schema",
        "authority-id",
        "semantic-sha",
        "candidate-equals-final",
        "b96d-missing",
        "family-lineage-missing",
        "family-file-sha",
        "human-decision-sha-missing",
        "human-provenance-drift",
        "provenance-in-semantic",
        "smarts-in-semantic",
        "reusable-in-semantic",
        "extra-top-level",
    ),
)
def test_payload_identity_and_provenance_drift_fails_closed(
    result: dict[str, object], mutation: str
) -> None:
    payload = _payload(result)
    provenance = payload["source_candidate_to_authority_provenance"]
    semantic = payload["canonical_semantic_signature"]
    if mutation == "schema":
        payload["authority_schema_version"] = "v1"
    elif mutation == "authority-id":
        payload["authority_id"] = "WRONG"
    elif mutation == "semantic-sha":
        payload["canonical_semantic_signature_sha256"] = "0" * 64
    elif mutation == "candidate-equals-final":
        provenance["source_candidate_warhead_rule_id"] = creator.FINAL_AUTHORITY_ID
    elif mutation == "b96d-missing":
        provenance.pop("source_candidate_warhead_rule_id")
    elif mutation == "family-lineage-missing":
        provenance.pop("source_candidate_reaction_family_id")
    elif mutation == "family-file-sha":
        provenance["source_materialized_family_authority_file_sha256"] = "0" * 64
    elif mutation == "human-decision-sha-missing":
        provenance.pop("project_level_warhead_rule_human_decision_record_sha256")
    elif mutation == "human-provenance-drift":
        payload["source_human_review_provenance"]["source_reviewer_id"] = (
            "reviewer-drift"
        )
    elif mutation == "provenance-in-semantic":
        semantic["source_candidate_to_authority_provenance"] = copy.deepcopy(
            provenance
        )
    elif mutation == "smarts-in-semantic":
        semantic["SMARTS"] = "[*]"
    elif mutation == "reusable-in-semantic":
        semantic["reusable_chemistry_authority"] = True
    elif mutation == "extra-top-level":
        payload["extra"] = False
    with pytest.raises(
        creator.FFQWarheadRuleAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(payload)


def test_single_scope_discriminator_cannot_be_upgraded_in_human_decision(
    decision: dict[str, object],
) -> None:
    for path, value in (
        (
            (
                "approved_formed_bond_scope_semantics",
                "formed_bond_order_scope_match_role",
            ),
            "AUTHORITATIVE_BOND_ORDER",
        ),
        (
            (
                "approved_formed_bond_scope_semantics",
                "formed_bond_order_independent_project_authority_status",
            ),
            "ESTABLISHED_SINGLE",
        ),
    ):
        mutated = copy.deepcopy(decision)
        _set_path(mutated, path, value)
        with pytest.raises(
            creator.FFQWarheadRuleAuthorityValidationError,
            match=creator.ERROR_TOKEN,
        ):
            creator._validate_human_decision_document_v1(mutated)


def test_creator_exposes_no_disk_registration_or_runtime_write_api() -> None:
    forbidden = {
        "materialize_to_disk",
        "write_authority",
        "register_authority",
        "update_registry",
        "update_effective_authority",
        "runtime_admit",
    }
    assert forbidden.isdisjoint(vars(creator))
    source = Path(creator.__file__).read_text(encoding="utf-8")
    assert "import requests" not in source
    assert "subprocess" not in source
    assert "datetime" not in source
    assert "uuid" not in source
    assert "from pathlib" not in source


def test_import_smoke_has_no_output_or_filesystem_side_effects(
    tmp_path: Path,
) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from covalent_ext import "
            "covapie_ffq_warhead_rule_authority_creator_v1",
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()


@pytest.mark.parametrize(
    "payload",
    (
        b'\xef\xbb\xbf{"a":1}\n',
        b'{"a":"x\x00y"}\n',
        b'{"a":1}\r\n',
        b'{"a":1,"a":2}\n',
        b'{"a":NaN}\n',
    ),
    ids=("bom", "nul", "cr", "duplicate", "nonfinite"),
)
def test_checker_strict_family_parser_fails_closed(payload: bytes) -> None:
    with pytest.raises(ValueError):
        checker.strict_parse_canonical_json_file_v1(
            payload,
            expected_byte_count=len(payload),
            expected_file_sha256=hashlib.sha256(payload).hexdigest(),
            source_name="SYNTHETIC",
        )


def test_valid_synthetic_precommit_lifecycle_profile() -> None:
    assert checker.validate_repository_observation_v1(_precommit_observation()) == (
        checker.PRECOMMIT_PROFILE
    )


def test_valid_synthetic_published_clean_descendant_lifecycle_profile() -> None:
    observation = _published_observation()
    assert observation["head"] != checker.BASELINE_COMMIT
    assert checker.validate_repository_observation_v1(observation) == (
        checker.PUBLISHED_PROFILE
    )


@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("mixed", None),
        ("extra-untracked", None),
        ("missing-tracked", None),
        ("modified_tracked_paths", ("tracked.py",)),
        ("staged_paths", ("staged.py",)),
        ("origin_main", "e" * 40),
        ("ahead", 1),
        ("behind", 1),
        ("branch", "feature"),
        ("baseline_ancestor_of_head", False),
        ("baseline_ancestor_of_origin_main", False),
    ),
    ids=(
        "mixed",
        "extra-untracked",
        "missing-tracked",
        "dirty",
        "staged",
        "diverged-head-origin",
        "ahead",
        "behind",
        "wrong-branch",
        "baseline-not-head-ancestor",
        "baseline-not-origin-ancestor",
    ),
)
def test_invalid_synthetic_lifecycle_fails_closed(
    mutation: str, value: object
) -> None:
    observation = _published_observation()
    if mutation == "mixed":
        observation["tracked_candidate_paths"] = EXACT3[:1]
        observation["untracked_paths"] = EXACT3[1:]
    elif mutation == "extra-untracked":
        observation = _precommit_observation()
        observation["untracked_paths"] = tuple(sorted((*EXACT3, "unexpected.txt")))
    elif mutation == "missing-tracked":
        observation["tracked_candidate_paths"] = EXACT3[:-1]
    else:
        observation[mutation] = value
    with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
        checker.validate_repository_observation_v1(observation)


def test_real_current_repository_uses_observation_determined_lifecycle() -> None:
    observation = checker.observe_repository_state_v1(REPO)
    expected = checker.validate_repository_observation_v1(observation)
    verified = checker.verify_candidate_exact3_v1(REPO)
    assert verified["lifecycle_profile"] == expected
    if observation["head"] == checker.BASELINE_COMMIT:
        assert expected == checker.PRECOMMIT_PROFILE
    else:
        assert expected == checker.PUBLISHED_PROFILE
    assert verified["candidate_exact3_paths"] == list(EXACT3)


def test_checker_verifies_family_dependency_and_real_build() -> None:
    checked = checker.run_check_v1(REPO)
    assert checked["reaction_family_authority_dependency_verified"] is True
    assert checked["family_authority_file_sha256"] == (
        checker.FAMILY_AUTHORITY_FILE_SHA256
    )
    assert checked["family_authority_receipt_sha256"] == (
        checker.FAMILY_RECEIPT_FILE_SHA256
    )
    assert checked["family_authority_canonical_payload_sha256"] == (
        checker.FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256
    )
    assert checked["disk_family_authority_equals_fresh_creator_output"] is True
    assert checked["fresh_family_creator_payload_validator_passed"] is True
    assert checked[
        "disk_family_authority_key_order_treated_as_semantically_irrelevant"
    ] is True
    assert checked["family_authority_id"] == (
        "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
    )
    assert checked["authority_payload_canonical_sha256"] == (
        EXPECTED_AUTHORITY_PAYLOAD_CANONICAL_SHA256
    )
    assert checked["build_result_canonical_sha256"] == (
        EXPECTED_BUILD_RESULT_CANONICAL_SHA256
    )
    assert checked["deterministic_double_build_deep_equal"] is True
    assert checked["warhead_rule_authority_payload_ready"] is True
    assert checked["persisted_warhead_rule_authority_created"] is False
