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
    covapie_ffq_reaction_family_authority_creator_v1 as creator,
)


REPO = Path(__file__).resolve().parents[1]
DECISION = REPO.parent / (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "project-level-reaction-family-human-decision-v1/"
    "ffq_project_level_reaction_family_human_decision_v1.json"
)
CHECKER_PATH = REPO / (
    "scripts/check_covapie_ffq_reaction_family_authority_creator_v1.py"
)
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_ffq_reaction_family_authority_creator_v1", CHECKER_PATH
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)

EXACT3 = tuple(
    sorted(path.as_posix() for path in checker.CANDIDATE_PATHS)
)
EXPECTED_AUTHORITY_PAYLOAD_CANONICAL_SHA256 = (
    "6007c9419d51799f33e5cd948a9228abc34f4a6fbea283f94375b1e9b126a6ca"
)
SEMANTIC_FIELDS = (
    "semantic_signature_version",
    "authority_kind",
    "applicability_scope",
    "target_condition",
    "ligand_reactive_atom_contract",
    "formed_protein_ligand_event",
    "canonical_local_reaction_family_scope_contract",
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
    return creator.validate_covapie_ffq_project_level_reaction_family_human_decision_v1(
        decision_bytes
    )


@pytest.fixture(scope="module")
def result(decision_bytes: bytes) -> dict[str, object]:
    return creator.build_covapie_ffq_reaction_family_authority_v1(
        decision_bytes
    )


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


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


def _payload(result: dict[str, object]) -> dict[str, object]:
    return copy.deepcopy(result["reaction_family_authority"])


def _semantic(result: dict[str, object]) -> dict[str, Any]:
    payload = _payload(result)
    return payload["canonical_semantic_signature"]  # type: ignore[return-value]


def _set_path(target: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    current = target
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value


def test_real_human_decision_is_byte_bound_and_exact(
    decision_bytes: bytes, decision: dict[str, object]
) -> None:
    assert len(decision_bytes) == creator.HUMAN_DECISION_BYTE_COUNT == 32668
    assert hashlib.sha256(decision_bytes).hexdigest() == (
        creator.HUMAN_DECISION_SHA256
    )
    assert decision["decision_status"] == (
        "HUMAN_APPROVED_PROJECT_LEVEL_REACTION_FAMILY_DECISION"
    )
    assert decision["decision_role"] == (
        "PROJECT_LEVEL_REACTION_FAMILY_HUMAN_APPROVAL_RECORD_"
        "NOT_AUTHORITY_PAYLOAD"
    )
    assert decision["reaction_family_authority_created"] is False
    assert decision["reaction_family_registration_performed"] is False


def test_public_validator_returns_detached_decision_copy(
    decision_bytes: bytes,
) -> None:
    first = creator.validate_covapie_ffq_project_level_reaction_family_human_decision_v1(
        decision_bytes
    )
    first["decision_status"] = "MUTATED_CALLER_COPY"
    second = creator.validate_covapie_ffq_project_level_reaction_family_human_decision_v1(
        decision_bytes
    )
    assert second["decision_status"] != first["decision_status"]


def test_build_is_deterministic_and_does_not_modify_source(
    decision_bytes: bytes,
) -> None:
    before = DECISION.read_bytes()
    first = creator.build_covapie_ffq_reaction_family_authority_v1(
        decision_bytes
    )
    second = creator.build_covapie_ffq_reaction_family_authority_v1(
        decision_bytes
    )
    assert first == second
    assert _canonical_bytes(first) == _canonical_bytes(second)
    assert DECISION.read_bytes() == before


def test_authority_v2_wrapper_identity_and_exact_fields(
    result: dict[str, object],
) -> None:
    payload = result["reaction_family_authority"]
    assert tuple(payload) == AUTHORITY_FIELDS
    assert payload["authority_schema_version"] == (
        "covapie_cys_sg_reaction_family_authority_payload_v2"
    )
    assert payload["authority_kind"] == "reaction_family"
    assert payload["authority_id"] == creator.FINAL_AUTHORITY_ID
    assert payload["semantic_name"] == creator.SEMANTIC_NAME
    assert payload["canonical_semantic_signature_sha256"] == (
        creator.APPROVED_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
    )
    creator.validate_covapie_ffq_reaction_family_authority_payload_v2(payload)
    assert hashlib.sha256(_canonical_bytes(payload)).hexdigest() == (
        EXPECTED_AUTHORITY_PAYLOAD_CANONICAL_SHA256
    )


def test_approved_semantics_exact11_rehash_and_final_id(
    result: dict[str, object],
) -> None:
    payload = result["reaction_family_authority"]
    semantic = payload["canonical_semantic_signature"]
    assert tuple(semantic) == SEMANTIC_FIELDS
    assert creator.authority_semantic_signature_sha256_v1(semantic) == (
        "2fef2eddfc385c78f9386b5973984fd6df992416a950d5fa9cdfd6a07d485bc7"
    )
    assert creator.authority_id_from_semantic_signature_v1(semantic) == (
        "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
    )


def test_public_payload_validator_name_matches_v2_wrapper_schema() -> None:
    current_name = "validate_covapie_ffq_reaction_family_authority_payload_v2"
    stale_name = (
        "validate_covapie_ffq_reaction_family_authority_payload_" + "v1"
    )
    assert current_name in creator.__all__
    assert stale_name not in creator.__all__
    assert hasattr(creator, current_name)
    assert not hasattr(creator, stale_name)


def test_full_local_scope_rehashes_to_source_candidate_family(
    result: dict[str, object],
) -> None:
    semantic = result["reaction_family_authority"][
        "canonical_semantic_signature"
    ]
    scope = semantic["canonical_local_reaction_family_scope_contract"]
    local = scope["required_canonical_family_signature_object"]
    material = scope["material_scope_match_dimensions"]
    digest = creator.authority_semantic_signature_sha256_v1(local)
    assert digest == creator.CANDIDATE_CANONICAL_FAMILY_SIGNATURE_SHA256
    assert digest == semantic["applicability_scope"][
        "required_canonical_family_signature_sha256"
    ]
    assert material["radius_1_neighbor_element_multiset"] == ["C", "C", "O"]
    assert len(material["local_bonds"]) == 4
    assert material["removed_precursor_internal_heavy_bond_count"] == 1
    assert material["leaving_group_disposition"] == {
        "allowed_elements": [],
        "required_count": 0,
    }


def test_candidate_to_final_dual_id_provenance_is_outside_semantics(
    result: dict[str, object],
) -> None:
    payload = result["reaction_family_authority"]
    provenance = payload["source_candidate_to_authority_provenance"]
    semantic_bytes = _canonical_bytes(payload["canonical_semantic_signature"])
    assert provenance["source_candidate_reaction_family_id"] == (
        "COVAPIE_CYS_SG_REACTION_FAMILY_B1FD795D4D442304"
    )
    assert provenance["final_authority_id"] == (
        "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
    )
    assert provenance["project_level_family_human_decision_record_sha256"] == (
        creator.HUMAN_DECISION_SHA256
    )
    assert provenance["source_candidate_reaction_family_id"].encode() not in (
        semantic_bytes
    )
    assert b"source_candidate" not in semantic_bytes
    assert b"provenance" not in semantic_bytes


def test_single_is_non_authoritative_discriminator_and_formed_authority_absent(
    result: dict[str, object],
) -> None:
    semantic = result["reaction_family_authority"][
        "canonical_semantic_signature"
    ]
    material = semantic[
        "canonical_local_reaction_family_scope_contract"
    ]["material_scope_match_dimensions"]
    assert material["formed_bond_order_scope_match_value"] == "single"
    assert material["formed_bond_order_scope_match_role"] == (
        "NON_AUTHORITATIVE_CLASSIFICATION_DISCRIMINATOR"
    )
    assert material["formed_bond_order_scope_match_required"] is True
    assert material[
        "formed_bond_order_independent_project_authority_status"
    ] == "NOT_ESTABLISHED"
    assert semantic["formed_protein_ligand_event"][
        "formed_bond_order_authority_status"
    ] == "NOT_ESTABLISHED"


def test_pre_mechanism_reversibility_and_creation_boundaries(
    result: dict[str, object],
) -> None:
    semantic = result["reaction_family_authority"][
        "canonical_semantic_signature"
    ]
    assert semantic["pre_reaction_graph_authority_status"] == "NOT_ESTABLISHED"
    assert semantic["pre_reaction_bond_order_authority_status"] == (
        "NOT_ESTABLISHED"
    )
    assert semantic["mechanism_claim_status"] == "NOT_CLAIMED"
    assert semantic["reversibility_claim_status"] == "NOT_CLAIMED"
    summary = result["creation_readiness_summary"]
    assert summary["reaction_family_authority_payload_ready"] is True
    assert summary["reaction_family_authority_payload_built_in_memory"] is True
    assert summary["persisted_reaction_family_authority_created"] is False
    assert summary["reaction_family_registration_performed"] is False
    assert summary["effective_authority_updated"] is False
    assert summary["runtime_authority_created"] is False
    assert summary["authority_file_materialized"] is False
    assert summary["warhead_rule_authority_created"] is False
    assert summary["SMARTS_generation_performed"] is False
    assert summary["ready_for_training"] is False
    assert summary[
        "feature_semantics_audit_required_before_formal_training"
    ] is True


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
        creator.FFQReactionFamilyAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_project_level_reaction_family_human_decision_v1(  # type: ignore[arg-type]
            bad_payload
        )


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("decision_status",), "STATUS_DRIFT"),
        (("decision_role",), "ROLE_DRIFT"),
        (("human_approval", "human_reviewer_id"), "reviewer-drift"),
        (("human_approval", "human_attestation"), "attestation-drift"),
        (("human_approval", "approval_scope"), "SCOPE_DRIFT"),
        (
            ("source_candidate_identity", "source_candidate_reaction_family_id"),
            "COVAPIE_CYS_SG_REACTION_FAMILY_0000000000000000",
        ),
        (
            (
                "source_candidate_identity",
                "candidate_canonical_family_signature_sha256",
            ),
            "0" * 64,
        ),
        (("approved_future_final_authority_id",), "WRONG_FINAL_ID"),
    ),
    ids=(
        "decision-status",
        "decision-role",
        "reviewer",
        "attestation",
        "approval-scope",
        "candidate-id",
        "candidate-family-sha",
        "future-authority-id",
    ),
)
def test_human_decision_semantic_invariant_drift_fails_closed(
    decision: dict[str, object], path: tuple[str, ...], value: object
) -> None:
    mutated = copy.deepcopy(decision)
    _set_path(mutated, path, value)
    with pytest.raises(
        creator.FFQReactionFamilyAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator._validate_human_decision_document_v1(mutated)


def test_missing_approval_item_fails_closed(
    decision: dict[str, object],
) -> None:
    mutated = copy.deepcopy(decision)
    mutated["human_review_items"].pop()
    with pytest.raises(
        creator.FFQReactionFamilyAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator._validate_human_decision_document_v1(mutated)


def test_non_approve_item_fails_closed(decision: dict[str, object]) -> None:
    mutated = copy.deepcopy(decision)
    mutated["human_review_items"][6]["human_response"] = "REJECT"
    with pytest.raises(
        creator.FFQReactionFamilyAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator._validate_human_decision_document_v1(mutated)


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("applicability_scope", "scope_kind"), "REUSABLE"),
        (
            ("applicability_scope", "cross_signature_propagation_allowed"),
            True,
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "selected_signature_radius",
            ),
            2,
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "center_reactive_atom",
                "element",
            ),
            "N",
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "center_reactive_atom",
                "formal_charge",
            ),
            1,
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "center_reactive_atom",
                "reactive",
            ),
            False,
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "radius_1_neighbor_element_multiset",
            ),
            ["C", "N", "O"],
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "removed_precursor_internal_heavy_bond_count",
            ),
            0,
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "formed_bond_order_scope_match_role",
            ),
            "AUTHORITATIVE_BOND_ORDER",
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "formed_bond_order_scope_match_required",
            ),
            False,
        ),
        (
            (
                "canonical_local_reaction_family_scope_contract",
                "material_scope_match_dimensions",
                "leaving_group_disposition",
                "allowed_elements",
            ),
            ["Cl"],
        ),
        (
            ("formed_protein_ligand_event", "formed_bond_order_authority_status"),
            "ESTABLISHED_SINGLE",
        ),
        (("pre_reaction_graph_authority_status",), "ESTABLISHED"),
        (("pre_reaction_bond_order_authority_status",), "ESTABLISHED"),
        (("mechanism_claim_status",), "CLAIMED"),
        (("reversibility_claim_status",), "REVERSIBLE"),
    ),
    ids=(
        "scope-kind",
        "cross-signature",
        "radius",
        "center-element",
        "center-charge",
        "center-reactive",
        "local-context",
        "removed-bond-count",
        "single-role",
        "single-required",
        "leaving-elements",
        "formed-authority-upgrade",
        "pre-graph",
        "pre-bond-order",
        "mechanism",
        "reversibility",
    ),
)
def test_semantic_scope_and_claim_drift_fails_closed(
    result: dict[str, object], path: tuple[str, ...], value: object
) -> None:
    payload = _payload(result)
    semantic = payload["canonical_semantic_signature"]
    _set_path(semantic, path, value)
    with pytest.raises(
        creator.FFQReactionFamilyAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_reaction_family_authority_payload_v2(
            payload
        )


def test_reaction_delta_and_local_bond_drift_fail_closed(
    result: dict[str, object],
) -> None:
    for mutator in (
        lambda material: material["reaction_delta"].__setitem__(
            "reaction_delta_class", "changed"
        ),
        lambda material: material["local_bonds"].pop(),
        lambda material: material["leaving_group_disposition"].__setitem__(
            "required_count", 1
        ),
    ):
        payload = _payload(result)
        material = payload["canonical_semantic_signature"][
            "canonical_local_reaction_family_scope_contract"
        ]["material_scope_match_dimensions"]
        mutator(material)
        with pytest.raises(
            creator.FFQReactionFamilyAuthorityValidationError,
            match=creator.ERROR_TOKEN,
        ):
            creator.validate_covapie_ffq_reaction_family_authority_payload_v2(
                payload
            )


@pytest.mark.parametrize(
    "mutation",
    (
        "semantic-added",
        "semantic-removed",
        "semantic-renamed",
        "semantic-sha",
        "provenance-in-semantic",
        "candidate-equals-final",
        "decision-sha-provenance-missing",
        "warhead-authority",
        "smarts",
    ),
)
def test_payload_schema_identity_and_provenance_drift_fails_closed(
    result: dict[str, object], mutation: str
) -> None:
    payload = _payload(result)
    semantic = payload["canonical_semantic_signature"]
    if mutation == "semantic-added":
        semantic["extra"] = False
    elif mutation == "semantic-removed":
        semantic.pop("mechanism_claim_status")
    elif mutation == "semantic-renamed":
        semantic["mechanism_status"] = semantic.pop("mechanism_claim_status")
    elif mutation == "semantic-sha":
        payload["canonical_semantic_signature_sha256"] = "0" * 64
    elif mutation == "provenance-in-semantic":
        semantic["source_candidate_to_authority_provenance"] = copy.deepcopy(
            payload["source_candidate_to_authority_provenance"]
        )
    elif mutation == "candidate-equals-final":
        payload["source_candidate_to_authority_provenance"][
            "source_candidate_reaction_family_id"
        ] = creator.FINAL_AUTHORITY_ID
    elif mutation == "decision-sha-provenance-missing":
        payload["source_candidate_to_authority_provenance"].pop(
            "project_level_family_human_decision_record_sha256"
        )
    elif mutation == "warhead-authority":
        payload["warhead_rule_authority"] = {}
    elif mutation == "smarts":
        payload["SMARTS"] = "[*]"
    with pytest.raises(
        creator.FFQReactionFamilyAuthorityValidationError,
        match=creator.ERROR_TOKEN,
    ):
        creator.validate_covapie_ffq_reaction_family_authority_payload_v2(
            payload
        )


def test_creator_exposes_no_disk_registration_or_runtime_write_api() -> None:
    forbidden = {
        "materialize_to_disk",
        "write_authority",
        "update_registry",
        "register_authority",
    }
    assert forbidden.isdisjoint(vars(creator))
    source = Path(creator.__file__).read_text(encoding="utf-8")
    assert "import requests" not in source
    assert "subprocess" not in source
    assert "datetime" not in source
    assert "uuid" not in source


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
            "covapie_ffq_reaction_family_authority_creator_v1",
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()


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
        observation["untracked_paths"] = tuple(
            sorted((*EXACT3, "unexpected.txt"))
        )
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


def test_checker_runs_real_build_and_reports_precommit_profile() -> None:
    checked = checker.run_check_v1(REPO)
    observed = checker.observe_repository_state_v1(REPO)
    expected = checker.validate_repository_observation_v1(observed)
    assert checked["lifecycle_profile"] == expected
    assert checked["authority_payload_canonical_sha256"] == (
        EXPECTED_AUTHORITY_PAYLOAD_CANONICAL_SHA256
    )
    assert checked["deterministic_double_build_deep_equal"] is True
    assert checked["reaction_family_authority_payload_ready"] is True
    assert checked["persisted_reaction_family_authority_created"] is False
