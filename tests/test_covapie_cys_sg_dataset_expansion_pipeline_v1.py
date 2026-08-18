from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_cys_sg_dataset_expansion_pipeline_v1 as pipeline,
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source(tmp_path: Path, identity: str) -> tuple[Path, str]:
    path = tmp_path / f"{identity.replace('/', '_')}.cif"
    path.write_bytes(("data_" + identity + "\n#\n").encode())
    return path, _sha(path.read_bytes())


def _candidate(
    tmp_path: Path,
    identity: str = "9XYZ/TST",
    *,
    leakage_key: str = "LIGAND_GRAPH_TEST|PROTEIN_CLUSTER_TEST",
) -> pipeline.ExpansionCandidateV1:
    source_path, source_sha = _source(tmp_path, identity)
    candidate = pipeline.ExpansionCandidateV1(
        candidate_identity=identity,
        pdb_id=identity.split("/", 1)[0],
        ligand_comp_id=identity.split("/", 1)[1],
        source_identity=f"synthetic://{identity}",
        source_path=source_path,
        expected_source_sha256=source_sha,
        explicit_event_authoritative=True,
        conflicting_explicit_event=False,
        protein_endpoint_exact_cys_sg=True,
        ligand_endpoint_mapping_count=1,
        retained_endpoint_mapping_count=1,
        canonical_topology_valid=True,
        pocket_valid=True,
        atom_symbols=("C", "C", "O", "N", "C", "C", "S", "C"),
        chemistry_signature_sha256="0" * 64,
        chemistry_signature_authoritative=False,
        canonical_ligand_smiles="CC(=O)NCC",
        smarts_atom_ids=(0, 1, 2, 3, 4, 5),
        reactive_ligand_atom_id=0,
        reactive_atom_mapping_count=1,
        retained_heavy_atoms=(0, 1, 2, 3, 4, 5),
        scaffold_atoms=(4, 5),
        linker_atoms=(3,),
        warhead_atoms=(0, 1, 2),
        explicit_graph_bonds=((0, 1, "single"), (1, 2, "double"), (1, 3, "single"), (3, 4, "single"), (4, 5, "single")),
        seed_atoms=(4, 5),
        primary_anchor_atom=4,
        direction_anchor_atom=5,
        optional_plane_anchor_atom=None,
        role_profile=pipeline.STRICT_PROFILE,
        role_rule_id="ROLE_RULE_TEST_V1",
        role_rule_version="V1",
        role_rule_match_count=1,
        role_authority_published=True,
        baseline_leakage_evidence_complete=True,
        leakage_key=leakage_key,
        leakage_conflict=False,
        duplicate_identity=False,
        post_distance_angstrom=1.82,
        pre_reaction_graph_authoritative=True,
        formal_charge_authoritative=True,
        atom_map_numbers=((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)),
        atom_formal_charges=((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)),
        pre_reaction_bonds=((0, 1, "single"), (1, 2, "double"), (1, 3, "single"), (3, 4, "single"), (4, 5, "single")),
        protein_endpoint_atom_id="P_SG",
        source_event_protein_atom_id="P_SG",
        source_event_ligand_atom_id=0,
        retained_reactive_atom_id=0,
        ligand_atom_coordinates=((0, "C", 1.82, 0.0, 0.0), (1, "C", 2.82, 0.0, 0.0), (2, "O", 3.32, 1.0, 0.0), (3, "N", 3.32, -1.0, 0.0), (4, "C", 4.32, -1.0, 0.0), (5, "C", 5.32, -1.0, 0.0)),
        pocket_atom_coordinates=(("P_SG", "S", 0.0, 0.0, 0.0), ("P_CA", "C", -1.0, 0.0, 0.0)),
    )
    candidate = pipeline.with_computed_chemistry_signature_v1(
        candidate, authoritative=True
    )
    return pipeline.with_pre_review_evidence_digest_v1(candidate)


def _redigest(record: dict[str, object]) -> dict[str, object]:
    record["source_human_review_record_sha256"] = pipeline.approval_record_digest_v1(record)
    return record


def _approval(
    candidate: pipeline.ExpansionCandidateV1,
    *,
    family_action: str = "NEW_AUTHORITY_REQUIRED",
    rule_action: str = "NEW_AUTHORITY_REQUIRED",
) -> dict[str, object]:
    record: dict[str, object] = {
        "candidate_identity": candidate.candidate_identity,
        "review_status": "APPROVE",
        "review_scope": "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
        "independent_sample_assignment_decision": "APPROVE",
        "reaction_family_authority_action": family_action,
        "reaction_family_id": "REACTION_FAMILY_TEST_V1",
        "reaction_family_version": "V1",
        "warhead_rule_authority_action": rule_action,
        "warhead_rule_id": "WARHEAD_RULE_TEST_V1",
        "warhead_rule_version": "V1",
        "approved_warhead_smarts": "[C:1][C:2](=[O:3])",
        "ligand_reactive_atom_map_number": 1,
        "warhead_atom_map_numbers": [1, 2, 3],
        "expected_pre_reaction_bond_orders": [[1, 2, "single"], [2, 3, "double"], [2, 4, "single"], [4, 5, "single"], [5, 6, "single"]],
        "allowed_formal_charge_pattern": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0},
        "reviewed_warhead_atom_ids": [0, 1, 2],
        "reviewed_warhead_attachment_atom_id": 1,
        "reviewed_nonwarhead_boundary_atom_id": 3,
        "reviewed_attachment_boundary_bond_order": "single",
        "reviewed_scaffold_atom_ids": [4, 5],
        "reviewed_linker_atom_ids": [3],
        "reviewed_warhead_role_atom_ids": [0, 1, 2],
        "reviewed_minimal_seed_atom_ids": [4, 5],
        "reviewed_scaffold_linker_boundary_bond": [3, 4],
        "reviewed_linker_warhead_boundary_bond": [1, 3],
        "primary_anchor_atom": 4,
        "direction_anchor_atom": 5,
        "optional_plane_anchor_atom": None,
        "role_profile": pipeline.STRICT_PROFILE,
        "role_rule_id": "ROLE_RULE_TEST_V1",
        "role_rule_version": "V1",
        "bound_source_identity": candidate.source_identity,
        "bound_source_sha256": candidate.expected_source_sha256,
        "pre_review_evidence_digest": candidate.pre_review_evidence_digest,
        "expected_final_chemistry_signature_sha256": "",
        "source_assignment_record_sha256": pipeline._candidate_assignment_sha256_v1(candidate),
        "reviewer_id": "chemist_reviewer_02",
        "review_rationale": "test-local complete scientific approval",
        "review_notes": "test fixture only; not production authority",
    }
    return _redigest(record)


def _completed_real_5f2e_template_fixture() -> dict[str, object]:
    template = json.loads(
        pipeline.build_real_exact4_human_review_decision_template_v2(ROOT)
    )
    record = next(
        item for item in template["approval_records"]
        if item["candidate_identity"] == "5F2E/5UT"
    )
    proposal = record["machine_evidence"]["existing_role_warhead_proposal"]
    scaffold = set(proposal["scaffold_atom_ids"])
    candidate = next(
        item for item in pipeline.load_current_non_exact16_candidates_v1(ROOT)
        if item.candidate_identity == "5F2E/5UT"
    )
    seed_bond = next(
        bond for bond in candidate.explicit_graph_bonds
        if bond[0] in scaffold and bond[1] in scaffold
    )
    scaffold_linker = proposal["scaffold_linker_boundaries"][0]
    linker_warhead = proposal["linker_warhead_boundaries"][0]
    map_by_atom = dict(candidate.atom_map_numbers)
    record.update({
        "review_status": "APPROVE",
        "review_scope": "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
        "independent_sample_assignment_decision": "APPROVE",
        "reaction_family_authority_action": "NEW_AUTHORITY_REQUIRED",
        "reaction_family_id": "TEST_ONLY_ACRYLAMIDE_FAMILY",
        "reaction_family_version": "V1",
        "warhead_rule_authority_action": "NEW_AUTHORITY_REQUIRED",
        "warhead_rule_id": "TEST_ONLY_5F2E_WARHEAD",
        "warhead_rule_version": "V1",
        "approved_warhead_smarts": proposal["proposed_warhead_smarts"],
        "warhead_atom_map_numbers": [
            map_by_atom[item] for item in proposal["warhead_atom_ids"]
        ],
        "reviewed_warhead_atom_ids": proposal["warhead_atom_ids"],
        "reviewed_warhead_attachment_atom_id": linker_warhead[1],
        "reviewed_nonwarhead_boundary_atom_id": linker_warhead[0],
        "reviewed_attachment_boundary_bond_order": linker_warhead[2],
        "reviewed_scaffold_atom_ids": proposal["scaffold_atom_ids"],
        "reviewed_linker_atom_ids": proposal["linker_atom_ids"],
        "reviewed_warhead_role_atom_ids": proposal["warhead_atom_ids"],
        "reviewed_minimal_seed_atom_ids": list(seed_bond[:2]),
        "reviewed_scaffold_linker_boundary_bond": list(scaffold_linker[:2]),
        "reviewed_linker_warhead_boundary_bond": list(linker_warhead[:2]),
        "primary_anchor_atom": seed_bond[0],
        "direction_anchor_atom": seed_bond[1],
        "optional_plane_anchor_atom": None,
        "role_profile": pipeline.STRICT_PROFILE,
        "role_rule_id": "TEST_ONLY_5F2E_ROLE",
        "role_rule_version": "V1",
        "reviewer_id": "chemist_test_fixture_5f2e",
        "review_rationale": (
            "TEST-ONLY plumbing fixture; not production approval or scientific authorization"
        ),
        "review_notes": (
            "TEST ONLY; draft proposal mirrored solely for isolated resume-path validation"
        ),
    })
    return template


def _authority(candidate: pipeline.ExpansionCandidateV1) -> pipeline.ReusableChemistryAuthorityV1:
    _effective, authority = pipeline.ingest_completed_human_approval_v1(candidate, _approval(candidate))
    assert authority is not None
    return authority


def _one(
    candidate: pipeline.ExpansionCandidateV1,
    authorities: tuple[pipeline.ReusableChemistryAuthorityV1, ...] = (),
    approvals: dict[str, dict[str, object]] | None = None,
) -> pipeline.CandidateOutcomeV1:
    return pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1(
        (candidate,), reusable_authorities=authorities, approval_records=approvals,
    ).outcomes[0]


def test_owner_map_modes_and_historical_policy_ceiling_are_truthful() -> None:
    owners = {item.stage: item for item in pipeline.AUTOMATION_OWNER_MAP_V1}
    assert len(owners) == 19
    for stage in ("candidate discovery", "endpoint mapping", "topology", "pocket", "POST", "leakage", "split"):
        assert owners[stage].pipeline_invoked is False
        assert owners[stage].pipeline_consumes_published_artifact is True
    assert owners["materialization"].pipeline_invoked is True
    assert owners["tensorization"].pipeline_invoked is True
    assert pipeline.REVIEW_ONLY == "review-only"
    assert pipeline.MATERIALIZE_APPROVED == "materialize-approved"
    assert pipeline.CURRENT_POLICY_REQUIRES_EVERY_NEW_SAMPLE_HUMAN_ASSIGNMENT is True
    policy_rows = list(csv.DictReader((ROOT / "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1/covapie_reaction_family_and_warhead_rule_review_policy_registry.csv").open()))
    assert {row["policy_id"]: row for row in policy_rows}["REVIEW_POLICY_008"]["semantic_name"] == "sample assignment requires independent sample review"


def test_chemistry_signature_is_identity_independent_and_chemistry_sensitive(tmp_path: Path) -> None:
    first = _candidate(tmp_path, "9XA1/TST")
    second = _candidate(tmp_path, "9XA2/TST")
    assert first.chemistry_signature_sha256 == second.chemistry_signature_sha256
    assert pipeline.build_exact_chemistry_signature_v1(replace(second, reactive_ligand_atom_id=1)) != first.chemistry_signature_sha256
    assert pipeline.build_exact_chemistry_signature_v1(replace(second, warhead_atoms=(0, 1, 2, 3))) != first.chemistry_signature_sha256
    changed_bond = replace(second, pre_reaction_bonds=second.pre_reaction_bonds[:-1] + ((4, 5, "double"),))
    assert pipeline.build_exact_chemistry_signature_v1(changed_bond) != first.chemistry_signature_sha256
    equivalent_rule_metadata = replace(
        second, role_rule_id="EQUIVALENT_RULE_RENAMED_V9",
        role_rule_version="V9",
    )
    assert (
        pipeline.build_exact_chemistry_signature_v1(equivalent_rule_metadata)
        == first.chemistry_signature_sha256
    )
    source = (ROOT / "src/covalent_ext/covapie_cys_sg_dataset_expansion_pipeline_v1.py").read_text()
    assert "UNAPPROVED_CANDIDATE_SIGNATURE_V1" not in source


def test_same_call_new_authority_propagates_and_actual_materialization_tensorization_run(tmp_path: Path) -> None:
    approved = replace(_candidate(tmp_path, "9XB1/TST"), role_authority_published=False, role_rule_match_count=0)
    follower = _candidate(tmp_path, "9XB2/TST")
    output = tmp_path / "materialized"
    run = pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1(
        (follower, approved), approval_records={approved.candidate_identity: _approval(approved)},
        execution_mode=pipeline.MATERIALIZE_APPROVED, output_root=output,
    )
    outcomes = {item.candidate_identity: item for item in run.outcomes}
    assert outcomes[approved.candidate_identity].terminal_disposition == pipeline.HUMAN_APPROVED
    assert outcomes[follower.candidate_identity].terminal_disposition == pipeline.AUTO_ADMITTED
    assert outcomes[follower.candidate_identity].human_sample_decision_consumed is False
    assert all(item.materialization_performed and item.tensorization_performed for item in outcomes.values())
    assert all(item.post_geometry_authority for item in outcomes.values())
    assert (output / "reusable_authority_registry_v1.json").is_file()
    tensor_files = sorted((output / "samples").glob("*.tensorized.json"))
    assert len(tensor_files) == 2
    tensor = json.loads(tensor_files[0].read_text())
    assert tensor["tensorization_performed"] is True
    assert len(tensor["canonical_task_masks"]) == 5
    assert tensor["geometry_component_authority_mask"] == [False, True]
    assert not list(tmp_path.rglob("*.tmp")) and not list(tmp_path.rglob("*.part"))


def test_review_only_known_authority_is_ready_but_performs_no_write(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    outcome = _one(candidate, (_authority(candidate),))
    assert outcome.terminal_disposition == pipeline.AUTO_ADMITTED
    assert outcome.materialization_ready and outcome.tensorization_ready
    assert not outcome.materialization_performed and not outcome.tensorization_performed


def test_expanded_population_tensorizer_delegates_historical_exact16(monkeypatch: pytest.MonkeyPatch) -> None:
    from covalent_ext import covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as historical

    observed: dict[str, object] = {}
    def delegated(**kwargs: object) -> str:
        observed.update(kwargs)
        return "HISTORICAL_DELEGATION_PROVED"
    monkeypatch.setattr(
        historical, "tensorize_covapie_expanded_cys_sg_sample_v1", delegated
    )
    identity = historical.CURRENT11_MEMBER_IDENTITIES_V1[0]
    result = pipeline.tensorize_covapie_expanded_population_successor_v1(
        sample_identity=identity,
        historical_tensorizer_kwargs={"task_id": 0},
    )
    assert result == "HISTORICAL_DELEGATION_PROVED"
    assert observed == {"sample_identity": identity, "task_id": 0}


def test_cross_signature_authority_propagation_is_forbidden(tmp_path: Path) -> None:
    approved = _candidate(tmp_path, "9XCS/TST")
    changed = replace(
        _candidate(tmp_path, "9XCT/TST"),
        pre_reaction_bonds=((0, 1, "double"),) + _candidate(
            tmp_path, "9XCU/TST"
        ).pre_reaction_bonds[1:],
    )
    changed = pipeline.with_computed_chemistry_signature_v1(
        changed, authoritative=True
    )
    outcome = _one(changed, (_authority(approved),))
    assert outcome.terminal_disposition == pipeline.HUMAN_REQUIRED
    assert outcome.human_sample_decision_consumed is False
    with pytest.raises(ValueError, match="CROSS_SIGNATURE_PROPAGATION_FORBIDDEN"):
        pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1(
            (approved,), reusable_authorities=(
                replace(
                    _authority(approved),
                    cross_signature_propagation_allowed=True,
                ),
            ),
        )


def test_subsequent_cli_run_loads_persisted_registry(tmp_path: Path) -> None:
    approved = _candidate(tmp_path, "9XC1/TST")
    first_root = tmp_path / "first-materialization"
    pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1(
        (approved,), approval_records={approved.candidate_identity: _approval(approved)},
        execution_mode=pipeline.MATERIALIZE_APPROVED, output_root=first_root,
    )
    later = _candidate(tmp_path, "9XC2/TST")
    candidate_json = tmp_path / "candidate-batch.json"
    candidate_json.write_bytes(pipeline.serialize_candidate_batch_v1((later,)))
    later_root = tmp_path / "later-materialization"
    completed = subprocess.run(
        (sys.executable, "scripts/run_covapie_cys_sg_dataset_expansion_pipeline_v1.py", "--repo-root", str(ROOT), "--candidate-batch-json", str(candidate_json), "--reusable-authority-registry-json", str(first_root / "reusable_authority_registry_v1.json"), "--mode", pipeline.MATERIALIZE_APPROVED, "--materialization-output-root", str(later_root)),
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    summary = json.loads(completed.stdout)
    assert summary["aggregate"]["auto_admitted_count"] == 1
    assert summary["materialization_performed_count"] == 1
    assert summary["tensorization_performed_count"] == 1
    assert (later_root / "pipeline_run_v1.json").is_file()
    assert json.loads((later_root / "pipeline_run_v1.json").read_text())["outcomes"][0]["human_sample_decision_consumed"] is False
    tampered = json.loads((first_root / "reusable_authority_registry_v1.json").read_text())
    tampered["authorities"][0]["reviewer_id"] = "forged_reviewer"
    tampered_path = tmp_path / "tampered-registry.json"
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="REUSABLE_AUTHORITY_REGISTRY_RECORD_INVALID"):
        pipeline.load_reusable_authority_registry_v1(tampered_path)


def test_approval_digest_is_computed_and_tamper_sensitive(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    record = _approval(candidate)
    _effective, authority = pipeline.ingest_completed_human_approval_v1(candidate, record)
    assert authority is not None
    assert authority.source_human_review_record_sha256 == pipeline.approval_record_digest_v1(record)
    tampered = dict(record)
    tampered["role_rule_version"] = "V2"
    outcome = _one(candidate, approvals={candidate.candidate_identity: tampered})
    assert "HUMAN_REVIEW_RECORD_DIGEST_MISMATCH" in outcome.blocking_reasons
    wrong_evidence = _approval(candidate)
    wrong_evidence["pre_review_evidence_digest"] = "f" * 64
    _redigest(wrong_evidence)
    outcome = _one(candidate, approvals={candidate.candidate_identity: wrong_evidence})
    assert "APPROVAL_PRE_REVIEW_EVIDENCE_BINDING_MISMATCH" in outcome.blocking_reasons
    effective, _authority_result, reasons = (
        pipeline._approval_effective_candidate_and_authority_v1(
            candidate, _approval(candidate), (),
        )
    )
    assert reasons == () and effective is not None
    expected_final = _approval(candidate)
    expected_final["expected_final_chemistry_signature_sha256"] = (
        effective.chemistry_signature_sha256
    )
    _redigest(expected_final)
    pipeline.ingest_completed_human_approval_v1(candidate, expected_final)
    expected_final["expected_final_chemistry_signature_sha256"] = "f" * 64
    _redigest(expected_final)
    outcome = _one(candidate, approvals={candidate.candidate_identity: expected_final})
    assert (
        "APPROVAL_EXPECTED_FINAL_CHEMISTRY_SIGNATURE_MISMATCH"
        in outcome.blocking_reasons
    )


def test_human_record_can_establish_pre_chemistry_when_machine_authority_is_absent(
    tmp_path: Path,
) -> None:
    baseline = _candidate(tmp_path)
    unresolved = replace(
        baseline,
        pre_reaction_graph_authoritative=False,
        formal_charge_authoritative=False,
        pre_reaction_bonds=(),
        atom_formal_charges=(),
        chemistry_signature_authoritative=False,
    )
    unresolved = pipeline.with_pre_review_evidence_digest_v1(unresolved)
    record = _approval(unresolved)
    effective, authority = pipeline.ingest_completed_human_approval_v1(
        unresolved, record,
    )
    assert authority is not None
    assert effective.pre_reaction_graph_authoritative is True
    assert effective.formal_charge_authoritative is True
    assert effective.pre_reaction_bonds == baseline.pre_reaction_bonds
    assert effective.atom_formal_charges == baseline.atom_formal_charges
    assert effective.chemistry_signature_authoritative is True
    assert authority.pre_review_evidence_digest == unresolved.pre_review_evidence_digest


def test_bind_existing_success(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    authority = _authority(candidate)
    record = _approval(candidate, family_action="BIND_EXISTING", rule_action="BIND_EXISTING")
    outcome = _one(candidate, (authority,), {candidate.candidate_identity: record})
    assert outcome.terminal_disposition == pipeline.HUMAN_APPROVED
    assert outcome.chemistry_authority_id == authority.authority_id


@pytest.mark.parametrize("case", ("unknown", "wrong_version", "wrong_signature", "ambiguous"))
def test_bind_existing_failures_are_closed(tmp_path: Path, case: str) -> None:
    candidate = _candidate(tmp_path)
    authority = _authority(candidate)
    authorities = (authority,)
    record = _approval(candidate, family_action="BIND_EXISTING", rule_action="BIND_EXISTING")
    if case == "unknown":
        record["reaction_family_id"] = "UNKNOWN_FAMILY_V1"
    elif case == "wrong_version":
        record["reaction_family_version"] = "V99"
    elif case == "wrong_signature":
        authorities = (replace(
            authority,
            chemistry_signature_sha256="f" * 64,
        ),)
    else:
        authorities = (authority, replace(authority, authority_id="COVAPIE_REUSABLE_SECOND_V1"))
    _redigest(record)
    outcome = _one(candidate, authorities, {candidate.candidate_identity: record})
    assert outcome.terminal_disposition == pipeline.HUMAN_REQUIRED
    assert any("BIND_EXISTING" in reason for reason in outcome.blocking_reasons)


def test_bind_existing_candidate_only_id_fails(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    candidate_only = replace(_authority(candidate), approved=False)
    record = _approval(candidate, family_action="BIND_EXISTING", rule_action="BIND_EXISTING")
    _effective, _result, reasons = pipeline._approval_effective_candidate_and_authority_v1(candidate, record, (candidate_only,))
    assert any("BIND_EXISTING_CANDIDATE_ONLY" in reason for reason in reasons)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (("ligand_reactive_atom_map_number", 2, "LIGAND_REACTIVE_ATOM_MAP_NUMBER_MISMATCH"), ("warhead_atom_map_numbers", [1, 2, 4], "WARHEAD_ATOM_MAP_NUMBERS_MISMATCH"), ("expected_pre_reaction_bond_orders", [[1, 2, "double"]], "EXPECTED_PRE_REACTION_BOND_ORDERS_MISMATCH"), ("allowed_formal_charge_pattern", {"1": 1}, "ALLOWED_FORMAL_CHARGE_PATTERN_MISMATCH")),
)
def test_scientific_approval_fields_are_semantically_validated(tmp_path: Path, field: str, value: object, reason: str) -> None:
    candidate = _candidate(tmp_path)
    record = _approval(candidate)
    record[field] = value
    _redigest(record)
    outcome = _one(candidate, approvals={candidate.candidate_identity: record})
    assert outcome.terminal_disposition == pipeline.HUMAN_REQUIRED
    assert reason in outcome.blocking_reasons


def test_existing_group_inherits_split_and_new_successor_is_order_independent(tmp_path: Path) -> None:
    existing = pipeline.load_published_leakage_group_population_v1(ROOT)
    inherited = _candidate(tmp_path, "9XD1/TST", leakage_key="COVAPIE_LEAKAGE_GROUP_000002")
    outcome = _one(inherited, (_authority(inherited),))
    assert outcome.leakage_group_id == "COVAPIE_LEAKAGE_GROUP_000002"
    assert outcome.assigned_split == "validation"
    first = _candidate(tmp_path, "9XD2/TST", leakage_key="NEW_GROUP_A")
    second = _candidate(tmp_path, "9XD3/TST", leakage_key="NEW_GROUP_B")
    left = pipeline.assign_expansion_leakage_splits_v1((first, second), existing_groups=existing)
    right = pipeline.assign_expansion_leakage_splits_v1((second, first), existing_groups=existing)
    assert left == right
    published = {item.final_leakage_group_id: item.assigned_split for item in existing}
    assert published == {"COVAPIE_LEAKAGE_GROUP_000001": "train", "COVAPIE_LEAKAGE_GROUP_000002": "validation", "COVAPIE_LEAKAGE_GROUP_000003": "validation", "COVAPIE_LEAKAGE_GROUP_000004": "train", "COVAPIE_LEAKAGE_GROUP_000005": "test"}
    source = (ROOT / "src/covalent_ext/covapie_cys_sg_dataset_expansion_pipeline_v1.py").read_text()
    assert "% 20" not in source and "hash_modulo" not in source


def test_post_authority_is_recomputed_from_exact_source_pair(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    valid, reasons, recomputed = pipeline.validate_post_geometry_authority_v1(candidate)
    assert valid is True and reasons == () and recomputed == pytest.approx(1.82)
    wrong_distance = replace(candidate, post_distance_angstrom=1.90)
    outcome = _one(wrong_distance, (_authority(candidate),))
    assert outcome.terminal_disposition == pipeline.POST_AUTHORITY_INVALID
    assert outcome.post_geometry_authority is False
    wrong_endpoint = replace(candidate, retained_reactive_atom_id=1)
    outcome = _one(wrong_endpoint, (_authority(candidate),))
    assert outcome.terminal_disposition == pipeline.POST_AUTHORITY_INVALID
    source = (ROOT / "src/covalent_ext/covapie_cys_sg_dataset_expansion_pipeline_v1.py").read_text()
    assert "post_geometry_authority=materialization_ready" not in source


def test_materialization_rerun_is_byte_identical_and_conflict_detecting(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    output = tmp_path / "stable-output"
    first = pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1((candidate,), approval_records={candidate.candidate_identity: _approval(candidate)}, execution_mode=pipeline.MATERIALIZE_APPROVED, output_root=output)
    before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
    second = pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1((candidate,), approval_records={candidate.candidate_identity: _approval(candidate)}, execution_mode=pipeline.MATERIALIZE_APPROVED, output_root=output)
    after = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
    assert pipeline.serialize_pipeline_run_v1(first) == pipeline.serialize_pipeline_run_v1(second)
    assert before == after
    changed = _approval(candidate)
    changed["review_rationale"] = "different but otherwise valid approval rationale"
    _redigest(changed)
    with pytest.raises(ValueError, match="EXISTING_MATERIALIZATION_BYTES_DIFFER"):
        pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1((candidate,), approval_records={candidate.candidate_identity: changed}, execution_mode=pipeline.MATERIALIZE_APPROVED, output_root=output)


def test_current_replay_counts_blank_packet_and_review_only_safety() -> None:
    records = pipeline.parse_human_review_packet_v1((ROOT / pipeline.REVIEW_PACKET_RELATIVE).read_bytes())
    assert len(records) == 4 and all(record["review_status"] == "" for record in records)
    run = pipeline.run_current_non_exact16_replay_v1(ROOT)
    assert run.aggregate == {"candidate_count": 12, "source_verified_count": 12, "mechanically_eligible_count": 5, "auto_admitted_count": 0, "human_review_required_count": 4, "runtime_extension_required_count": 1, "missing_source_authority_count": 5, "rejected_count": 2, "materialization_ready_count": 0}
    outcomes = {item.candidate_identity: item for item in run.outcomes}
    assert set(run.review_queue_identities) == {"2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV"}
    assert outcomes["2R9F/K2Z"].terminal_disposition == pipeline.RUNTIME_EXTENSION
    assert "DRAFT_ROLE_PARTITION_HAS_TWO_SCAFFOLD_LINKER_BOUNDARIES" in outcomes["6DI9/GJJ"].blocking_reasons
    assert all(not item.materialization_performed and not item.tensorization_performed for item in run.outcomes)


def test_real_exact4_loader_machine_evidence_and_v2_template_are_complete() -> None:
    candidates = {
        item.candidate_identity: item
        for item in pipeline.load_current_non_exact16_candidates_v1(ROOT)
    }
    for identity in ("2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV"):
        candidate = candidates[identity]
        assert candidate.pre_review_evidence_digest == (
            pipeline.build_pre_review_evidence_digest_v1(candidate)
        )
        assert candidate.atom_map_numbers
        assert candidate.source_event_protein_atom_id == candidate.protein_endpoint_atom_id
        assert candidate.source_event_ligand_atom_id == candidate.reactive_ligand_atom_id
        assert candidate.retained_reactive_atom_id == candidate.reactive_ligand_atom_id
        assert candidate.source_event_protein_endpoint_descriptor
        assert candidate.source_event_ligand_endpoint_descriptor
        assert len(candidate.ligand_atom_coordinates) == len(candidate.retained_heavy_atoms)
        assert candidate.pocket_atom_coordinates
        assert candidate.baseline_leakage_evidence_complete is True
        assert candidate.leakage_key
        valid, reasons, recomputed = pipeline.validate_post_geometry_authority_v1(candidate)
        assert valid is True and reasons == () and recomputed is not None
    for identity in ("6DI9/GJJ", "5F2E/5UT", "6OIM/MOV"):
        assert candidates[identity].pre_reaction_graph_authoritative is True
        assert candidates[identity].formal_charge_authoritative is True
    assert candidates["2DJF/1ZB"].pre_reaction_graph_authoritative is False
    assert candidates["2DJF/1ZB"].formal_charge_authoritative is False
    assert candidates["5F2E/5UT"].leakage_key == candidates["6OIM/MOV"].leakage_key

    generated_first = pipeline.build_real_exact4_human_review_decision_template_v2(ROOT)
    generated_second = pipeline.build_real_exact4_human_review_decision_template_v2(ROOT)
    published = (ROOT / pipeline.REVIEW_TEMPLATE_V2_RELATIVE).read_bytes()
    assert generated_first == generated_second == published
    template = json.loads(published)
    assert template["schema_version"] == pipeline.REVIEW_TEMPLATE_V2_SCHEMA
    assert [item["candidate_identity"] for item in template["approval_records"]] == [
        "2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV",
    ]
    human_blank_fields = (
        "review_status", "review_scope", "independent_sample_assignment_decision",
        "reaction_family_id", "approved_warhead_smarts", "reviewed_scaffold_atom_ids",
        "reviewed_linker_atom_ids", "reviewed_warhead_role_atom_ids",
        "reviewed_minimal_seed_atom_ids", "reviewer_id", "review_rationale",
    )
    for record in template["approval_records"]:
        assert record["bound_source_identity"]
        assert len(record["bound_source_sha256"]) == 64
        assert len(record["pre_review_evidence_digest"]) == 64
        assert record["machine_evidence"]["exact_event_endpoints"]
        assert record["machine_evidence"]["exact_event_endpoints"]["protein_endpoint_descriptor"]
        assert record["machine_evidence"]["exact_event_endpoints"]["ligand_endpoint_descriptor"]
        assert record["machine_evidence"]["canonical_ligand_atom_namespace"]
        assert record["machine_evidence"]["observed_post_distance_angstrom"] > 0
        assert record["machine_evidence"]["leakage_evidence"]["machine_derived"] is True
        for field in human_blank_fields:
            assert record[field] in ("", [])
    one_zb = template["approval_records"][0]
    assert one_zb["expected_pre_reaction_bond_orders"] == []
    assert one_zb["allowed_formal_charge_pattern"] == {}
    assert one_zb["machine_evidence"]["pre_reaction_graph_authoritative"] is False
    assert "HUMAN_MUST_ESTABLISH_PRE_REACTION_GRAPH_AND_FORMAL_CHARGES" in one_zb["machine_evidence"]["candidate_warnings"]
    six_di9 = template["approval_records"][1]
    proposal = six_di9["machine_evidence"]["existing_role_warhead_proposal"]
    assert len(proposal["scaffold_linker_boundaries"]) == 2
    assert "DRAFT_HAS_TWO_SCAFFOLD_LINKER_BOUNDARIES_DO_NOT_APPROVE_UNCHANGED" in six_di9["machine_evidence"]["candidate_warnings"]


def test_real_5f2e_test_only_approval_resumes_through_cli_materialization_and_tensorization(
    tmp_path: Path,
) -> None:
    protected = (
        ROOT / pipeline.REVIEW_TEMPLATE_V2_RELATIVE,
        ROOT / pipeline.INVENTORY_RELATIVE,
        ROOT / pipeline.RECOVERED7_EVIDENCE_RELATIVE,
        ROOT / "data/raw/covalent_sources/pdb_mmcif_direct/structures/5F2E.cif.gz",
    )
    before = {path: _sha(path.read_bytes()) for path in protected}
    candidate = next(
        item for item in pipeline.load_current_non_exact16_candidates_v1(ROOT)
        if item.candidate_identity == "5F2E/5UT"
    )
    completed_template = _completed_real_5f2e_template_fixture()
    approval_path = tmp_path / "completed-v2-test-only.json"
    approval_path.write_text(
        json.dumps(completed_template, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "real-5f2e-materialized"
    completed = subprocess.run(
        (
            sys.executable,
            "scripts/run_covapie_cys_sg_dataset_expansion_pipeline_v1.py",
            "--repo-root", str(ROOT),
            "--approval-records-json", str(approval_path),
            "--mode", pipeline.MATERIALIZE_APPROVED,
            "--materialization-output-root", str(output),
        ),
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=True,
    )
    summary = json.loads(completed.stdout)
    assert summary["aggregate"]["materialization_ready_count"] == 1
    assert summary["materialization_performed_count"] == 1
    assert summary["tensorization_performed_count"] == 1
    run = json.loads((output / "pipeline_run_v1.json").read_text())
    real = next(
        item for item in run["outcomes"] if item["candidate_identity"] == "5F2E/5UT"
    )
    assert real["source_verified"] is True
    assert real["human_sample_decision_consumed"] is True
    assert real["terminal_disposition"] == pipeline.HUMAN_APPROVED
    assert real["leakage_group_id"].startswith("COVAPIE_EXPANSION_LEAKAGE_GROUP_")
    assert real["assigned_split"] in {"train", "validation", "test"}
    assert real["post_geometry_authority"] is True
    assert real["pre_geometry_authority"] is False
    assert real["pre_geometry_masked"] is True
    assert real["materialization_performed"] is True
    assert real["tensorization_performed"] is True
    materialized_file = next((output / "samples").glob("*.materialized.json"))
    tensorized_file = next((output / "samples").glob("*.tensorized.json"))
    materialized = json.loads(materialized_file.read_text())
    tensorized = json.loads(tensorized_file.read_text())
    registry = json.loads((output / "reusable_authority_registry_v1.json").read_text())
    authority = registry["authorities"][0]
    assert materialized["source_sha256"] == candidate.expected_source_sha256
    assert materialized["chemistry_signature_sha256"] != candidate.chemistry_signature_sha256
    assert authority["chemistry_signature_sha256"] == materialized["chemistry_signature_sha256"]
    assert authority["pre_review_evidence_digest"] == candidate.pre_review_evidence_digest
    assert authority["source_identity"] == candidate.source_identity
    assert authority["source_sha256"] == candidate.expected_source_sha256
    assert authority["reviewer_id"] == "chemist_test_fixture_5f2e"
    assert tensorized["tensorization_performed"] is True
    assert tensorized["geometry_component_authority_mask"] == [False, True]
    assert tensorized["pre_geometry_masked"] is True
    assert len(tensorized["canonical_task_masks"]) == 5
    assert before == {path: _sha(path.read_bytes()) for path in protected}
    assert not (ROOT / pipeline.REVIEW_TEMPLATE_V2_RELATIVE.parent / "reusable_authority_registry_v1.json").exists()
    assert not list(tmp_path.rglob("*.tmp")) and not list(tmp_path.rglob("*.part"))


def test_candidate_local_failure_isolation_preserved(tmp_path: Path) -> None:
    admitted = _candidate(tmp_path, "9XE1/TST")
    missing = replace(_candidate(tmp_path, "9XE2/TST"), source_path=tmp_path / "missing.cif")
    run = pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1((missing, admitted), reusable_authorities=(_authority(admitted),))
    outcomes = {item.candidate_identity: item for item in run.outcomes}
    assert outcomes[admitted.candidate_identity].terminal_disposition == pipeline.AUTO_ADMITTED
    assert outcomes[missing.candidate_identity].terminal_disposition == pipeline.MISSING_SOURCE


def test_existing_verified_source_avoids_redownload(tmp_path: Path) -> None:
    _, request = pipeline._published_acquisition_request_v1("2DJF/1ZB", ROOT)
    source = ROOT / request["destination_identity"]
    destination = tmp_path / request["destination_identity"]
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source.read_bytes())
    calls = 0
    def forbidden(_url: str, _timeout: int):
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not run")
    result = pipeline.acquire_or_verify_published_source_v1(candidate_identity="2DJF/1ZB", destination_root=tmp_path, authority_repo_root=ROOT, expected_source_sha256=_sha(source.read_bytes()), transport=forbidden)
    assert calls == 0 and result.source_status == "SOURCE_ALREADY_PRESENT_AND_VERIFIED"
    assert result.exact_event_recovered is True


@pytest.mark.parametrize(("identity", "event"), (("2DJF/1ZB", True), ("1A54/MDC", False)))
def test_offline_acquisition_regressions(tmp_path: Path, identity: str, event: bool) -> None:
    _, request = pipeline._published_acquisition_request_v1(identity, ROOT)
    payload = (ROOT / request["destination_identity"]).read_bytes()
    def transport(url: str, _timeout: int):
        return pipeline.acquisition_owner.TransportResponse(payload, 200, url)
    result = pipeline.acquire_or_verify_published_source_v1(candidate_identity=identity, destination_root=tmp_path / identity.replace("/", "_"), authority_repo_root=ROOT, expected_source_sha256=_sha(payload), transport=transport)
    assert result.source_status == "ACQUIRED_AND_VERIFIED"
    assert result.exact_event_recovered is event
    if not event:
        assert result.explicit_connection_evidence_status == "STRUCT_CONN_LOOP_ABSENT"
    assert not list(tmp_path.rglob("*.part"))


def test_cli_current_replay_and_protected_model_boundaries(tmp_path: Path) -> None:
    protected = [ROOT / pipeline.INVENTORY_RELATIVE, ROOT / pipeline.REVIEW_PACKET_RELATIVE, ROOT / "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py"]
    before = {path: _sha(path.read_bytes()) for path in protected}
    output = tmp_path / "current.json"
    completed = subprocess.run((sys.executable, "scripts/run_covapie_cys_sg_dataset_expansion_pipeline_v1.py", "--repo-root", str(ROOT), "--output-json", str(output)), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    summary = json.loads(completed.stdout)
    assert summary["execution_mode"] == pipeline.REVIEW_ONLY
    assert summary["aggregate"]["human_review_required_count"] == 4
    assert before == {path: _sha(path.read_bytes()) for path in protected}
    source = (ROOT / "src/covalent_ext/covapie_cys_sg_dataset_expansion_pipeline_v1.py").read_text()
    assert ".backward(" not in source and "optimizer.step(" not in source and "Trainer.fit(" not in source


def test_materialization_protected_path_and_mode_boundaries(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    authority = _authority(candidate)
    with pytest.raises(ValueError, match="REVIEW_ONLY_MODE_FORBIDS"):
        pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1((candidate,), reusable_authorities=(authority,), output_root=tmp_path / "x")
    with pytest.raises(ValueError, match="MATERIALIZE_APPROVED_MODE_REQUIRES"):
        pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1((candidate,), reusable_authorities=(authority,), execution_mode=pipeline.MATERIALIZE_APPROVED)
    with pytest.raises(ValueError, match="MATERIALIZATION_OUTPUT_ROOT_PROTECTED"):
        pipeline.run_covapie_cys_sg_dataset_expansion_pipeline_v1((candidate,), reusable_authorities=(authority,), execution_mode=pipeline.MATERIALIZE_APPROVED, output_root=(ROOT / "data/raw/forbidden-output").resolve())
