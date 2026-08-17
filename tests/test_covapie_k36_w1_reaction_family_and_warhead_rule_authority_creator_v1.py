from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Callable, Mapping

import pytest

from covalent_ext import (
    covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1
    as published_review_packages,
)
from covalent_ext import (
    covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1
    as creator,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = REPO_ROOT.parent / "covapie-state"
K36_STATE = STATE_ROOT / (
    "manual-review/recovered7-targeted-chemistry-review-v1/"
    "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
    "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92"
)
COMPLETED_RECORD_PATH = K36_STATE / "completed_review_record.csv"
COMPILED_SUBMISSION_PATH = (
    K36_STATE / "compiled_direct_attachment_review_submission_v1.json"
)
PUBLISHED_EVIDENCE_PATH = REPO_ROOT / (
    "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1/"
    "covapie_recovered7_chemistry_review_package_evidence.json"
)
CURRENT11_REGISTRY_PATH = REPO_ROOT / (
    "data/derived/covalent_small/"
    "covapie_current11_reaction_family_and_approved_warhead_rule_"
    "authority_binding_v1/"
    "covapie_family_and_warhead_rule_authority_registry.csv"
)
CURRENT11_APPROVAL_WORKLIST_PATH = STATE_ROOT / (
    "manual-review/current11-family-rule-approval-v1/"
    "family_rule_approval_worklist.csv"
)
CURRENT11_EFFECTIVE_VIEW_PATH = STATE_ROOT / (
    "manual-review/covapie_current11_unified_effective_authority_view_v1.json"
)

COMPLETED_RECORD_FILE_SHA256 = (
    "4e64742c6bfc585e4ef9dd662a31ee7f35df9bf2cd3d305452647bb86392956b"
)
COMPILED_SUBMISSION_FILE_SHA256 = (
    "0fff58cdd0fdaa12c8e41376de76e0edf76b72c8bd43a08045a04681dc6ea73c"
)
EXPECTED_FAMILY_ID = "COVAPIE_CYS_SG_REACTION_FAMILY_A06FD171EB8080D8"
EXPECTED_FAMILY_SIGNATURE_SHA256 = (
    "a06fd171eb8080d8cea9caf5001f7862fd60410d53a87b908aa8cc40117db52e"
)
EXPECTED_RULE_ID = "COVAPIE_CYS_SG_WARHEAD_RULE_855163C772D500C7"
EXPECTED_RULE_SIGNATURE_SHA256 = (
    "855163c772d500c7ed5471bdf510316d2cdbd3ebbcabde9a859d5a17031ac1c9"
)

_JSON_LIST_FIELDS = (
    "review_class_member_identities",
    "reviewed_warhead_atom_ids",
    "reviewed_scaffold_atom_ids",
    "reviewed_linker_atom_ids",
    "reviewed_warhead_role_atom_ids",
    "reviewed_minimal_seed_atom_ids",
)

PROTECTED_OWNER_SHA256 = {
    (
        "src/covalent_ext/"
        "covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1.py"
    ): "cfcf09c9d593c1a299192b4d455e05e45b1f916c792352479593459b3562c681",
    (
        "src/covalent_ext/"
        "covapie_direct_attachment_optional_linker_runtime_v1.py"
    ): "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
    (
        "src/covalent_ext/"
        "covapie_recovered7_direct_attachment_completed_review_submission_"
        "successor_v1.py"
    ): "fbc716282f89f11eef63259b5f6ef008148ed369eee3a2e1bbd296e3a34672ee",
    (
        "src/covalent_ext/"
        "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
    ): "db912d62c996bc91a0f8735135883f301ad61e3a448d5574770054c7f82db364",
    (
        "src/covalent_ext/"
        "covapie_current11_reaction_family_and_approved_warhead_rule_"
        "authority_binding_v1.py"
    ): "0dd122f1587592ffae459badfa80a2807b0bbdf16e1dd1b5e4674abdebae4c3d",
    (
        "src/covalent_ext/"
        "covapie_current11_reaction_family_and_warhead_rule_approval_review_"
        "package_v1.py"
    ): "e395ef8730d7cfff756ec87f8d724ae8ff976426be41fbd7e35af37cad7230df",
    (
        "src/covalent_ext/"
        "covapie_current11_unified_effective_authority_view_v1.py"
    ): "c8f2af8fc0d5dd2f8c42e527cc3db34620b2992f567d59f32a19842254dac4f4",
    (
        "src/covalent_ext/"
        "covapie_current11_warhead_atom_set_and_attachment_boundary_review_"
        "ingestion_gate_design_v1.py"
    ): "cd726f7122edd8315079f0ac1df9d4bb24d4ee969f438ce2f41eda3fd0f7c410",
    (
        "src/covalent_ext/"
        "covapie_current11_warhead_atom_set_and_attachment_boundary_review_"
        "ingestion_interface_v1.py"
    ): "dad2bb9fffeecfd132b34f733be85ff45af089e8b8fbd2feb6a15eb924ac00b0",
    (
        "src/covalent_ext/"
        "covapie_current11_real_human_review_ingestion_execution_bundle_v1.py"
    ): "78d0124c7fba182f75542a128ee7a2707580e7f05dcbdc24103eae5bebbb969c",
    (
        "src/covalent_ext/"
        "covapie_current11_multi_boundary_human_review_ingestion_contract_"
        "design_v1.py"
    ): "91899640e89cc462aac0a28245873da12ba573b8658a30e193da7ec9fac92771",
    (
        "src/covalent_ext/"
        "covapie_current11_multi_boundary_human_review_ingestion_execution_"
        "bundle_v1.py"
    ): "ca6baf51becd354f7d78763b34c122e66a13b1f51fc7ba16cd896832a573e422",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=tuple(rows[0]), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


@pytest.fixture(scope="module")
def completed_record() -> dict[str, object]:
    with COMPLETED_RECORD_PATH.open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        record = dict(next(csv.DictReader(stream)))
    for field in _JSON_LIST_FIELDS:
        record[field] = json.loads(record[field])
    record["review_class_member_count"] = int(
        record["review_class_member_count"]
    )
    return record


@pytest.fixture(scope="module")
def published_evidence() -> dict[str, object]:
    return json.loads(PUBLISHED_EVIDENCE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def review_class(published_evidence: dict[str, object]) -> dict[str, object]:
    matches = [
        value
        for value in published_evidence["review_classes"]
        if value["review_class_id"]
        == "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
        "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92"
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture(scope="module")
def sample_applicability(
    published_evidence: dict[str, object],
) -> list[dict[str, object]]:
    rows = [
        value
        for value in published_evidence["sample_applicability"]
        if value["review_class_id"]
        == "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
        "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92"
    ]
    assert len(rows) == 5
    return rows


@pytest.fixture(scope="module")
def compiled_submission() -> dict[str, object]:
    return json.loads(COMPILED_SUBMISSION_PATH.read_text(encoding="utf-8"))


def _build(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
    *,
    baseline_source_payloads: Mapping[str, object] | None = None,
    existing_authority_records: list[dict[str, object]] | tuple[()] = (),
) -> dict[str, object]:
    if baseline_source_payloads is None:
        baseline_source_payloads = _real_baseline_source_payloads()
    return creator.build_covapie_k36_w1_reaction_family_and_warhead_rule_authority_v1(
        completed_review_record=completed_record,
        review_class=review_class,
        sample_applicability=sample_applicability,
        compiled_submission=compiled_submission,
        existing_approved_authority_baseline_source_payloads=(
            baseline_source_payloads
        ),
        existing_authority_records=existing_authority_records,
    )


def _real_baseline_source_payloads() -> dict[str, bytes]:
    payloads = {}
    for source in creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1:
        path = REPO_ROOT.parent / source["source_path"]
        if source["source_path"].startswith("data/"):
            path = REPO_ROOT / source["source_path"]
        payloads[source["source_path"]] = path.read_bytes()
    return payloads


def _rehash_review_record(record: dict[str, object]) -> None:
    record["review_record_sha256"] = ""
    record["review_record_sha256"] = (
        published_review_packages.review_record_sha256_v1(record)
    )


def test_real_formal_k36_payloads_are_exact_and_in_memory_only(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    assert _sha256(COMPLETED_RECORD_PATH) == COMPLETED_RECORD_FILE_SHA256
    assert _sha256(COMPILED_SUBMISSION_PATH) == COMPILED_SUBMISSION_FILE_SHA256
    assert completed_record["review_record_sha256"] == (
        creator.K36_SOURCE_REVIEW_RECORD_SHA256_V1
    )
    assert completed_record["reviewer_id"] == "fmx"
    assert completed_record["review_status"] == "COMPLETED"

    before = {
        COMPLETED_RECORD_PATH: COMPLETED_RECORD_PATH.read_bytes(),
        COMPILED_SUBMISSION_PATH: COMPILED_SUBMISSION_PATH.read_bytes(),
    }
    input_snapshot = copy.deepcopy(
        (completed_record, review_class, sample_applicability, compiled_submission)
    )
    result = _build(
        completed_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )
    creator.validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1(
        result
    )
    assert input_snapshot == (
        completed_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )
    assert before == {path: path.read_bytes() for path in before}

    family = result["reaction_family_authority"]
    rule = result["warhead_rule_authority"]
    summary = result["creation_provenance_readiness_summary"]
    assert family["authority_id"] == EXPECTED_FAMILY_ID
    assert family["canonical_semantic_signature_sha256"] == (
        EXPECTED_FAMILY_SIGNATURE_SHA256
    )
    assert rule["authority_id"] == EXPECTED_RULE_ID
    assert rule["canonical_semantic_signature_sha256"] == (
        EXPECTED_RULE_SIGNATURE_SHA256
    )
    assert rule["canonical_semantic_signature"][
        "reaction_family_authority_id"
    ] == family["authority_id"]

    family_signature = family["canonical_semantic_signature"]
    rule_signature = rule["canonical_semantic_signature"]
    assert family_signature["applicability_scope"] == {
        "scope_kind": "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
        "required_chemistry_signature_sha256": (
            "83e9c7b9d43444d7e50fbfd7e6c3dafef5e0dc92cf1a7c571e3f4e3fe4e08d92"
        ),
        "cross_signature_propagation_allowed": False,
    }
    family_event = family_signature["formed_protein_ligand_event"]
    assert family_event["formed_bond_order_authority_status"] == (
        "NOT_ESTABLISHED"
    )
    assert "formed_bond_order" not in family_event
    assert "bond_order" not in family_event
    assert [
        row["atom_id"]
        for row in rule_signature["active_warhead_atom_contract"]
    ] == ["C21", "O22"]
    assert rule_signature["masked_precursor_provenance"] == {
        "atom_ids": ["O1", "O2", "O3", "S1"],
        "included_in_active_warhead": False,
        "establishes_pre_reaction_graph_authority": False,
    }
    assert rule_signature["retained_role_profile"] == (
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    )
    assert rule_signature["minimal_seed_supervision_provenance"] == {
        "atom_ids": ["C20", "N19"],
        "included_in_chemistry_rule_matching": False,
    }

    component_boundary = rule_signature["retained_framework_boundary"]
    protein_event = rule_signature["formed_protein_ligand_event"]
    assert component_boundary == {
        "edge_kind": "COMPONENT_INTERNAL_RETAINED_FRAMEWORK_BOUNDARY",
        "scaffold_side_atom_id": "C20",
        "warhead_side_atom_id": "C21",
        "bond_order": "single",
        "component_internal_topology_edge": True,
    }
    assert protein_event["protein_endpoint"] == {
        "residue_component_id": "CYS",
        "atom_id": "SG",
    }
    assert protein_event["ligand_endpoint"] == {
        "ligand_component_id": "K36",
        "atom_id": "C21",
    }
    assert protein_event["formed_bond_order_authority_status"] == (
        "NOT_ESTABLISHED"
    )
    assert "formed_bond_order" not in protein_event
    assert "bond_order" not in protein_event
    assert protein_event["component_internal_topology_edge"] is False
    assert component_boundary != protein_event

    for signature in (family_signature, rule_signature):
        assert signature["pre_reaction_graph_authority_status"] == (
            "NOT_ESTABLISHED"
        )
        assert signature["pre_reaction_bond_order_authority_status"] == (
            "NOT_ESTABLISHED"
        )
        assert signature["mechanism_claim_status"] == "NOT_CLAIMED"
        assert signature["reversibility_claim_status"] == "NOT_CLAIMED"

    assert summary["reaction_family_authority_payload_ready"] is True
    assert summary["warhead_rule_authority_payload_ready"] is True
    collision = summary["existing_approved_authority_collision_check"]
    assert collision["status"] == "NO_APPROVED_AUTHORITY_COLLISION"
    assert collision["baseline_approved_authority_count"] == 0
    assert collision["baseline_source_bytes_sha_bound"] is True
    assert collision["baseline_sources_actually_parsed"] is True
    assert collision["baseline_registry_candidate_only_verified"] is True
    assert (
        collision["baseline_approval_worklist_zero_completed_verified"]
        is True
    )
    assert (
        collision[
            "baseline_effective_view_zero_family_rule_authority_verified"
        ]
        is True
    )
    for field in (
        "reaction_family_authority_materialized",
        "warhead_rule_authority_materialized",
        "effective_authority_updated",
        "ingestion_executed",
        "training_supervision_authority_complete",
        "network_request_executed",
        "raw_downloaded",
        "topology_downloaded",
        "distance_bond_inference_used",
        "PRE_geometry_reconstruction_executed",
        "model_forward",
        "backward",
        "optimizer_step",
        "Trainer.fit",
        "RL",
    ):
        assert summary[field] is False


def test_build_and_ids_are_deterministic_and_provenance_order_independent(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    first = _build(
        completed_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )
    reverse_submission = dict(reversed(tuple(compiled_submission.items())))
    reverse_baseline_payloads = dict(
        reversed(tuple(_real_baseline_source_payloads().items()))
    )
    second = _build(
        completed_record,
        review_class,
        list(reversed(list(reversed(sample_applicability)))),
        reverse_submission,
        baseline_source_payloads=reverse_baseline_payloads,
    )
    assert first == second
    assert json.dumps(
        first, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii") == json.dumps(
        second, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")

    family = first["reaction_family_authority"]
    rule = first["warhead_rule_authority"]
    reverse_family_signature = dict(
        reversed(tuple(family["canonical_semantic_signature"].items()))
    )
    assert creator.authority_id_from_semantic_signature_v1(
        "reaction_family", reverse_family_signature
    ) == family["authority_id"]
    changed_provenance = copy.deepcopy(first)
    changed_provenance["reaction_family_authority"][
        "source_human_review_provenance"
    ] = {"source_reviewer_id": "independent_reviewer"}
    changed_provenance["warhead_rule_authority"][
        "source_human_review_provenance"
    ] = {"source_review_record_sha256": "0" * 64}
    assert creator.authority_id_from_semantic_signature_v1(
        "reaction_family", family["canonical_semantic_signature"]
    ) == creator.authority_id_from_semantic_signature_v1(
        "reaction_family",
        changed_provenance["reaction_family_authority"][
            "canonical_semantic_signature"
        ],
    )
    assert creator.authority_id_from_semantic_signature_v1(
        "warhead_rule", rule["canonical_semantic_signature"]
    ) == creator.authority_id_from_semantic_signature_v1(
        "warhead_rule",
        changed_provenance["warhead_rule_authority"][
            "canonical_semantic_signature"
        ],
    )
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="REACTION_FAMILY_PAYLOAD_INVALID",
    ):
        creator.validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1(
            changed_provenance
        )


def test_baseline_authority_sources_are_exact_and_candidate_ids_are_not_approved() -> None:
    expected_sources = creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1
    for source in expected_sources:
        path = REPO_ROOT.parent / source["source_path"]
        if source["source_path"].startswith("data/"):
            path = REPO_ROOT / source["source_path"]
        assert _sha256(path) == source["source_sha256"]

    with CURRENT11_REGISTRY_PATH.open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        registry = list(csv.DictReader(stream))
    assert len(registry) == 7
    assert {
        (row["reaction_family_authority_status"], row["approval_status"])
        for row in registry
    } == {("candidate_only", "candidate_only")}
    assert EXPECTED_FAMILY_ID not in {
        row["reaction_family_id"] for row in registry
    }
    assert EXPECTED_RULE_ID not in {row["warhead_rule_id"] for row in registry}

    with CURRENT11_APPROVAL_WORKLIST_PATH.open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        worklist = list(csv.DictReader(stream))
    assert len(worklist) == 7
    assert {row["review_completed"] for row in worklist} == {""}

    effective_view = json.loads(
        CURRENT11_EFFECTIVE_VIEW_PATH.read_text(encoding="utf-8")
    )
    assert len(effective_view["effective_authority_records"]) == 11
    for record in effective_view["effective_authority_records"]:
        boundary_authority = record["effective_authority_record"]
        assert "reaction_family_authority_status" not in boundary_authority
        assert "warhead_rule_authority_status" not in boundary_authority


def test_production_build_requires_actual_baseline_source_payloads(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    with pytest.raises(
        TypeError,
        match="existing_approved_authority_baseline_source_payloads",
    ):
        creator.build_covapie_k36_w1_reaction_family_and_warhead_rule_authority_v1(
            completed_review_record=completed_record,
            review_class=review_class,
            sample_applicability=sample_applicability,
            compiled_submission=compiled_submission,
        )


@pytest.mark.parametrize("mutation", ("missing", "extra", "str_value"))
def test_baseline_source_path_inventory_and_bytes_type_fail_closed(
    mutation: str,
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    payloads: dict[str, object] = dict(_real_baseline_source_payloads())
    first_path = next(iter(payloads))
    expected_error = ""
    if mutation == "missing":
        del payloads[first_path]
        expected_error = "BASELINE_AUTHORITY_SOURCE_MISSING"
    elif mutation == "extra":
        payloads["unexpected_authority_source"] = b"unexpected"
        expected_error = "BASELINE_AUTHORITY_SOURCE_EXTRA"
    else:
        payloads[first_path] = "not bytes"
        expected_error = "BASELINE_AUTHORITY_SOURCE_BYTES_REQUIRED"
    with pytest.raises(
        creator.AuthorityCreationValidationError, match=expected_error
    ):
        _build(
            completed_record,
            review_class,
            sample_applicability,
            compiled_submission,
            baseline_source_payloads=payloads,
        )


@pytest.mark.parametrize("source_index", (0, 1, 2))
def test_each_baseline_source_is_actual_bytes_sha_bound(
    source_index: int,
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    payloads = _real_baseline_source_payloads()
    source = creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1[
        source_index
    ]
    path = source["source_path"]
    payloads[path] += b"\n"
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match=f"BASELINE_AUTHORITY_SOURCE_SHA256_MISMATCH:{path}",
    ):
        _build(
            completed_record,
            review_class,
            sample_applicability,
            compiled_submission,
            baseline_source_payloads=payloads,
        )


def test_registry_parser_rejects_formal_authority_even_without_sha_gate() -> None:
    payloads = _real_baseline_source_payloads()
    registry_path = creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1[
        0
    ]["source_path"]
    rows = list(
        csv.DictReader(
            io.StringIO(payloads[registry_path].decode("utf-8"), newline="")
        )
    )
    rows[0]["reaction_family_authority_status"] = "APPROVED"
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="BASELINE_AUTHORITY_REGISTRY_FORMAL_AUTHORITY_PRESENT",
    ):
        creator._validate_registry_authority_source_v1(
            _csv_bytes(rows),
            generated_family_id=EXPECTED_FAMILY_ID,
            generated_rule_id=EXPECTED_RULE_ID,
        )


def test_approval_worklist_parser_rejects_completed_decision_without_sha_gate() -> None:
    payloads = _real_baseline_source_payloads()
    worklist_path = creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1[
        1
    ]["source_path"]
    rows = list(
        csv.DictReader(
            io.StringIO(payloads[worklist_path].decode("utf-8"), newline="")
        )
    )
    rows[0]["reaction_family_review_decision"] = (
        "approve_reaction_family_identity"
    )
    rows[0]["review_completed"] = "true"
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="BASELINE_AUTHORITY_APPROVAL_WORKLIST_COMPLETED_DECISION_PRESENT",
    ):
        creator._validate_approval_worklist_authority_source_v1(
            _csv_bytes(rows)
        )


def test_effective_view_parser_rejects_formal_family_rule_authority_without_sha_gate() -> None:
    payloads = _real_baseline_source_payloads()
    sources = creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1
    family_ids, rule_ids = creator._validate_registry_authority_source_v1(
        payloads[sources[0]["source_path"]],
        generated_family_id=EXPECTED_FAMILY_ID,
        generated_rule_id=EXPECTED_RULE_ID,
    )
    view = json.loads(payloads[sources[2]["source_path"]])
    view["effective_authority_records"][0]["effective_authority_record"][
        "reaction_family_authority_status"
    ] = "EFFECTIVE"
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match=(
            "BASELINE_AUTHORITY_EFFECTIVE_VIEW_FORMAL_"
            "FAMILY_RULE_AUTHORITY_PRESENT"
        ),
    ):
        creator._validate_unified_effective_authority_source_v1(
            json.dumps(view, separators=(",", ":")).encode("utf-8"),
            candidate_family_ids=family_ids,
            candidate_rule_ids=rule_ids,
        )


def test_production_creation_fails_closed_for_noncompleted_record(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    record = copy.deepcopy(completed_record)
    record["review_status"] = "NOT_REVIEWED"
    _rehash_review_record(record)
    with pytest.raises(creator.AuthorityCreationValidationError):
        _build(record, review_class, sample_applicability, compiled_submission)


def test_production_creation_fails_closed_for_wrong_reviewer_binding(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    record = copy.deepcopy(completed_record)
    record["reviewer_id"] = "independent_reviewer"
    _rehash_review_record(record)
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="K36_SOURCE_REVIEWER_ID_MISMATCH",
    ):
        _build(record, review_class, sample_applicability, compiled_submission)


def test_production_creation_fails_closed_for_wrong_source_record_binding(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    record = copy.deepcopy(completed_record)
    record["review_notes"] = "Different completed decision carrier."
    _rehash_review_record(record)
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="K36_SOURCE_REVIEW_RECORD_SHA256_MISMATCH",
    ):
        _build(record, review_class, sample_applicability, compiled_submission)


def test_production_creation_fails_closed_for_wrong_review_class_signature(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    wrong_class = copy.deepcopy(review_class)
    wrong_class["chemistry_review_signature"]["ligand_component_id"] = "W2"
    wrong_sha = published_review_packages.chemistry_review_signature_sha256_v1(
        wrong_class["chemistry_review_signature"]
    )
    wrong_class["chemistry_review_signature_sha256"] = wrong_sha
    wrong_class["review_class_id"] = (
        "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_" + wrong_sha.upper()
    )
    with pytest.raises(creator.AuthorityCreationValidationError):
        _build(
            completed_record,
            wrong_class,
            sample_applicability,
            compiled_submission,
        )


def test_production_creation_fails_closed_for_incomplete_member_applicability(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    with pytest.raises(creator.AuthorityCreationValidationError):
        _build(
            completed_record,
            review_class,
            sample_applicability[:-1],
            compiled_submission,
        )


def test_production_creation_recompiles_and_rejects_noncanonical_submission(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    submission = copy.deepcopy(compiled_submission)
    submission["reviewed_warhead_atom_ids"] = ["C21", "O18"]
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="COMPILED_SUBMISSION_NOT_CANONICAL_COMPILER_OUTPUT",
    ):
        _build(
            completed_record,
            review_class,
            sample_applicability,
            submission,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record: record.__setitem__("reviewed_linker_atom_ids", ["C20"]),
        lambda record: record.__setitem__(
            "reviewed_reaction_family_id",
            "COVAPIE_CYS_SG_REACTION_FAMILY_A06FD171EB8080D8",
        ),
        lambda record: record.__setitem__(
            "reviewed_warhead_rule_id",
            "COVAPIE_CYS_SG_WARHEAD_RULE_855163C772D500C7",
        ),
    ),
)
def test_production_creation_rejects_nonempty_linker_and_prefilled_new_ids(
    mutation: Callable[[dict[str, object]], None],
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    record = copy.deepcopy(completed_record)
    mutation(record)
    _rehash_review_record(record)
    with pytest.raises(creator.AuthorityCreationValidationError):
        _build(record, review_class, sample_applicability, compiled_submission)


def _mutated_result(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> dict[str, object]:
    return copy.deepcopy(
        _build(
            completed_record,
            review_class,
            sample_applicability,
            compiled_submission,
        )
    )


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        (
            lambda rule: rule.__setitem__(
                "active_warhead_atom_contract",
                [
                    {
                        "atom_id": "C21",
                        "element": "C",
                        "atom_role": "LIGAND_REACTIVE_CENTER",
                    },
                    {
                        "atom_id": "O18",
                        "element": "O",
                        "atom_role": "ACTIVE_WARHEAD_OXYGEN",
                    },
                ],
            ),
            "ACTIVE_WARHEAD_CONTRACT_NOT_EXACT_C21_O22",
        ),
        (
            lambda rule: rule["active_warhead_atom_contract"].append(
                {
                    "atom_id": "O1",
                    "element": "O",
                    "atom_role": "MASKED_PRECURSOR_ATOM",
                }
            ),
            "ACTIVE_WARHEAD_CONTRACT_NOT_EXACT_C21_O22",
        ),
        (
            lambda rule: rule.__setitem__(
                "ligand_reactive_atom", {"atom_id": "C20", "element": "C"}
            ),
            "LIGAND_REACTIVE_ATOM_NOT_EXACT_C21",
        ),
        (
            lambda rule: rule["retained_framework_boundary"].__setitem__(
                "scaffold_side_atom_id", "SG"
            ),
            "COMPONENT_BOUNDARY_NOT_EXACT_C20_C21_SINGLE",
        ),
        (
            lambda rule: rule["retained_framework_boundary"].__setitem__(
                "scaffold_side_atom_id", "C19"
            ),
            "COMPONENT_BOUNDARY_NOT_EXACT_C20_C21_SINGLE",
        ),
        (
            lambda rule: rule["formed_protein_ligand_event"].__setitem__(
                "protein_endpoint",
                {"residue_component_id": "K36", "atom_id": "C20"},
            ),
            "PROTEIN_LIGAND_EVENT_NOT_EXACT_SG_C21",
        ),
        (
            lambda rule: rule.__setitem__(
                "masked_precursor_provenance",
                {
                    "atom_ids": ["O1", "O2", "O3"],
                    "included_in_active_warhead": False,
                    "establishes_pre_reaction_graph_authority": False,
                },
            ),
            "MASKED_PRECURSOR_PROVENANCE_NOT_EXACT",
        ),
    ),
)
def test_payload_validator_rejects_w2_active_set_boundary_and_event_confusions(
    mutation: Callable[[dict[str, object]], None],
    error: str,
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    result = _mutated_result(
        completed_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )
    rule = result["warhead_rule_authority"]["canonical_semantic_signature"]
    mutation(rule)
    with pytest.raises(creator.AuthorityCreationValidationError, match=error):
        creator.validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1(
            result
        )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        (
            "pre_reaction_graph_authority_status",
            "ESTABLISHED",
            "PRE_REACTION_GRAPH_AUTHORITY_NOT_ESTABLISHED_REQUIRED",
        ),
        (
            "pre_reaction_bond_order_authority_status",
            "C21=O22_ESTABLISHED",
            "PRE_REACTION_BOND_ORDER_AUTHORITY_NOT_ESTABLISHED_REQUIRED",
        ),
        ("mechanism_claim_status", "THIOHEMIACETAL", "MECHANISM_NOT_CLAIMED_REQUIRED"),
        ("reversibility_claim_status", "REVERSIBLE", "REVERSIBILITY_NOT_CLAIMED_REQUIRED"),
    ),
)
@pytest.mark.parametrize("authority_key", ("reaction_family_authority", "warhead_rule_authority"))
def test_payload_validator_rejects_pre_graph_mechanism_and_reversibility_claims(
    authority_key: str,
    field: str,
    value: str,
    error: str,
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    result = _mutated_result(
        completed_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )
    result[authority_key]["canonical_semantic_signature"][field] = value
    with pytest.raises(creator.AuthorityCreationValidationError, match=error):
        creator.validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1(
            result
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("formed_bond_order", "single"),
        ("formed_bond_order_authority_status", "ESTABLISHED_SINGLE"),
    ),
)
@pytest.mark.parametrize(
    "authority_key", ("reaction_family_authority", "warhead_rule_authority")
)
def test_payload_validator_rejects_protein_ligand_formed_bond_order_overclaim(
    authority_key: str,
    field: str,
    value: str,
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    result = _mutated_result(
        completed_record,
        review_class,
        sample_applicability,
        compiled_submission,
    )
    event = result[authority_key]["canonical_semantic_signature"][
        "formed_protein_ligand_event"
    ]
    event[field] = value
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match=(
            "PROTEIN_LIGAND_FORMED_BOND_ORDER_AUTHORITY_"
            "NOT_ESTABLISHED_REQUIRED"
        ),
    ):
        creator.validate_covapie_k36_w1_reaction_family_and_warhead_rule_authority_payload_v1(
            result
        )


def test_existing_authority_collision_and_stale_new_authority_fail_closed(
    completed_record: dict[str, object],
    review_class: dict[str, object],
    sample_applicability: list[dict[str, object]],
    compiled_submission: dict[str, object],
) -> None:
    collision = {
        "authority_kind": "reaction_family",
        "authority_id": EXPECTED_FAMILY_ID,
        "canonical_semantic_signature_sha256": "0" * 64,
        "authority_status": "APPROVED",
        "authority_source": "test_approved_authority",
    }
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="AUTHORITY_ID_COLLISION_DIFFERENT_SEMANTICS:reaction_family",
    ):
        _build(
            completed_record,
            review_class,
            sample_applicability,
            compiled_submission,
            existing_authority_records=[collision],
        )

    stale = {
        "authority_kind": "warhead_rule",
        "authority_id": "COVAPIE_CYS_SG_WARHEAD_RULE_AAAAAAAAAAAAAAAA",
        "canonical_semantic_signature_sha256": (
            EXPECTED_RULE_SIGNATURE_SHA256
        ),
        "authority_status": "EFFECTIVE",
        "authority_source": "test_effective_authority",
    }
    with pytest.raises(
        creator.AuthorityCreationValidationError,
        match="NEW_AUTHORITY_REQUIRED_STALE:warhead_rule",
    ):
        _build(
            completed_record,
            review_class,
            sample_applicability,
            compiled_submission,
            existing_authority_records=[stale],
        )

    candidate_only = dict(collision)
    candidate_only["authority_status"] = "CANDIDATE_ONLY"
    result = _build(
        completed_record,
        review_class,
        sample_applicability,
        compiled_submission,
        existing_authority_records=[candidate_only],
    )
    check = result["creation_provenance_readiness_summary"][
        "existing_approved_authority_collision_check"
    ]
    assert check["additional_approved_authority_count"] == 0
    assert check["candidate_only_authority_treated_as_approved"] is False


def test_protected_published_owners_are_byte_unchanged() -> None:
    assert {
        path: _sha256(REPO_ROOT / path)
        for path in PROTECTED_OWNER_SHA256
    } == PROTECTED_OWNER_SHA256
