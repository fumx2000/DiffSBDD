from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1
    as stage_a,
)
from covalent_ext import (
    covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1
    as stage_b0,
)


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return (
        stage_b0.build_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_artifacts_v1()
    )


@pytest.fixture(scope="module")
def recovery(artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return _rows(artifacts[stage_b0.RECOVERY_FILE])


@pytest.fixture(scope="module")
def worklist(artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return _rows(artifacts[stage_b0.WORKLIST_FILE])


@pytest.fixture(scope="module")
def manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[stage_b0.MANIFEST_FILE])


def _stage_a_row(ligand: str = "LIG") -> dict[str, str]:
    return {
        "canonical_candidate_id": "SYNTHETIC_STAGE_B0",
        "pdb_id": "9ZZZ",
        "protein_chain": "A",
        "cys_residue_sequence": "10",
        "cys_insertion_code": "NONE",
        "ligand_component_id": ligand,
    }


def _synthetic_mmcif(
    *, ligand: str = "LIG", include_struct_conn: bool = True,
    ambiguous_altloc: bool = False,
) -> str:
    struct_conn = ""
    if include_struct_conn:
        struct_conn = f"""\
loop_
_struct_conn.id
_struct_conn.conn_type_id
_struct_conn.ptnr1_label_asym_id
_struct_conn.ptnr1_label_comp_id
_struct_conn.ptnr1_label_seq_id
_struct_conn.ptnr1_label_atom_id
_struct_conn.ptnr1_auth_asym_id
_struct_conn.ptnr1_auth_seq_id
_struct_conn.ptnr2_label_asym_id
_struct_conn.ptnr2_label_comp_id
_struct_conn.ptnr2_label_seq_id
_struct_conn.ptnr2_label_atom_id
_struct_conn.ptnr2_auth_asym_id
_struct_conn.ptnr2_auth_seq_id
_struct_conn.pdbx_ptnr1_PDB_ins_code
_struct_conn.pdbx_ptnr2_PDB_ins_code
_struct_conn.pdbx_dist_value
covale1 covale A CYS 10 SG A 10 B {ligand} 201 C1 B 201 ? ? 1.800
#
"""
    protein_rows = (
        "1 ATOM S SG . CYS A 1 10 10 CYS A SG 1 0.0 0.0 0.0 1.00 20.0\n"
    )
    if ambiguous_altloc:
        protein_rows = (
            "1 ATOM S SG A CYS A 1 10 10 CYS A SG 1 0.0 0.0 0.0 0.50 20.0\n"
            "2 ATOM S SG B CYS A 1 10 10 CYS A SG 1 0.0 0.0 0.0 0.50 20.0\n"
        )
    ligand_id = 3 if ambiguous_altloc else 2
    return f"""\
data_9ZZZ
{struct_conn}loop_
_atom_site.id
_atom_site.group_PDB
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
{protein_rows}{ligand_id} HETATM C C1 . {ligand} B 2 201 201 {ligand} B C1 1 1.8 0.0 0.0 1.00 20.0
#
"""


def test_published_stage_a_hashes_and_exact_12_cohort(
    recovery: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    for path, expected in stage_b0.PUBLISHED_STAGE_A_SHA256.items():
        assert hashlib.sha256((stage_b0.REPO_ROOT / path).read_bytes()).hexdigest() == expected
    assert stage_b0.PUBLISHED_STAGE_A_COMMIT == (
        "19d07143c41026bb5a54bc1e02d81ac1d649dd76"
    )
    identities = tuple(
        (row["pdb_id"], row["ligand_component_id"]) for row in recovery
    )
    assert identities == stage_b0.RECOVERY_IDENTITIES
    assert len(recovery) == manifest["recovery_candidate_count"] == 12
    assert len({row["canonical_candidate_id"] for row in recovery}) == 12


def test_gold_eligible_and_reject_rows_are_frozen_and_not_emitted(
    recovery: list[dict[str, str]],
) -> None:
    registry = _rows((stage_b0.REPO_ROOT / stage_b0.STAGE_A_CANDIDATE).read_bytes())
    assert sum(row["registry_disposition"] == "GOLD_REFERENCE" for row in registry) == 11
    assert {
        (row["pdb_id"], row["ligand_component_id"])
        for row in registry if row["registry_disposition"] == "ELIGIBLE_FOR_STAGE_B"
    } == stage_b0.ELIGIBLE_CONTROL_IDENTITIES
    assert {
        (row["pdb_id"], row["ligand_component_id"])
        for row in registry if row["registry_disposition"] == "REJECT"
    } == stage_b0.REJECT_IDENTITIES
    emitted = {(row["pdb_id"], row["ligand_component_id"]) for row in recovery}
    assert emitted.isdisjoint(stage_b0.ELIGIBLE_CONTROL_IDENTITIES)
    assert emitted.isdisjoint(stage_b0.REJECT_IDENTITIES)


def test_local_evidence_lookup_is_deterministic_and_identity_bounded(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    state = tmp_path / "state"
    raw = repo / "data/raw/candidate"
    derived = repo / "data/derived/candidate"
    raw.mkdir(parents=True)
    derived.mkdir(parents=True)
    state.mkdir()
    (raw / "9zzz.cif").write_text("data_9ZZZ\n", encoding="utf-8")
    (derived / "9ZZZ_protein.pdb").write_text("HEADER\n", encoding="utf-8")
    (raw / "9ZZZ_LIG.sdf").write_text("LIG\n", encoding="utf-8")
    (raw / "19ZZZ.cif").write_text("data_19ZZZ\n", encoding="utf-8")
    first = stage_b0.lookup_local_evidence_v1(
        "9ZZZ", "LIG", repo_root=repo, state_root=state,
    )
    second = stage_b0.lookup_local_evidence_v1(
        "9ZZZ", "LIG", repo_root=repo, state_root=state,
    )
    assert first == second
    assert [path.name for path in first.raw_structure_paths] == ["9zzz.cif"]
    assert [path.name for path in first.derived_structure_paths] == ["9ZZZ_protein.pdb"]
    assert [path.name for path in first.topology_paths] == ["9ZZZ_LIG.sdf"]


def test_struct_conn_exact_pair_positive_path() -> None:
    decision = stage_b0.recover_exact_struct_conn_event_v1(
        _synthetic_mmcif(), _stage_a_row(),
    )
    assert decision.recovered is True
    assert decision.status == "STRUCT_CONN_EXACT_CYS_SG_EVENT_AND_COORDINATES_RECOVERED"
    assert decision.explicit_connection_evidence_status == (
        "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
    )
    assert decision.protein_chain == "A"
    assert decision.cys_residue_sequence == "10"
    assert decision.ligand_chain_or_instance == "B"
    assert decision.ligand_sequence_or_instance == "201"
    assert decision.reactive_ligand_atom == "C1"
    assert decision.protein_coordinates == (0.0, 0.0, 0.0)
    assert decision.ligand_coordinates == (1.8, 0.0, 0.0)


def test_complete_production_path_does_not_reacquire_recovered_local_raw(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    state = tmp_path / "state"
    raw_root = repo / "data/raw/candidate"
    raw_root.mkdir(parents=True)
    state.mkdir()
    raw_path = raw_root / "9zzz.cif"
    raw_path.write_text(_synthetic_mmcif(), encoding="utf-8")
    source = {
        **_stage_a_row(),
        "registry_disposition": "HUMAN_REVIEW_REQUIRED",
        "primary_issue_code_or_NONE": "SG_EVENT_EVIDENCE_MISSING",
        "parent_post_topology_status": "PARENT_POST_TOPOLOGY_EVIDENCE_MISSING",
        "exact10_status": "EXACT10_MODEL_GRAPH_EVIDENCE_MISSING",
    }
    lookup = stage_b0.lookup_local_evidence_v1(
        "9ZZZ", "LIG", repo_root=repo, state_root=state,
    )
    recovered = stage_b0._missing_matrix_row(
        source, lookup, repo, state,
    )
    assert recovered["local_raw_structure_found"] is True
    assert recovered["cys_sg_event_recovered"] is True
    assert recovered["explicit_connection_evidence_status"] == (
        "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
    )
    assert recovered["recovery_disposition"] == (
        "AUTO_RECOVERED_BUT_DOWNSTREAM_LABEL_REVIEW_REQUIRED"
    )
    assert recovered["recovery_disposition"] != (
        "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
    )
    assert recovered["acquisition_authorization_status"] == (
        "NOT_APPLICABLE_LOCAL_RAW_EXACT_EVENT_ALREADY_RECOVERED"
    )
    worklist = stage_b0._worklist_rows([recovered])
    assert len(worklist) == 1
    assert worklist[0]["worklist_category"] == (
        "DOWNSTREAM_CHEMISTRY_LABEL_REVIEW_REQUIRED"
    )
    assert "RAW_MMCIF" not in worklist[0][
        "required_missing_artifact_or_evidence"
    ]
    assert worklist[0]["authorization_evidence_authority"] == (
        "NOT_APPLICABLE_RAW_ALREADY_LOCAL"
    )
    assert "ACQUISITION_STAGE" not in worklist[0][
        "next_manual_or_acquisition_action"
    ]


def test_distance_alone_never_infers_event_and_missing_loop_fails_closed() -> None:
    decision = stage_b0.recover_exact_struct_conn_event_v1(
        _synthetic_mmcif(include_struct_conn=False), _stage_a_row(),
    )
    assert decision.recovered is False
    assert decision.status == "STRUCT_CONN_EXACT_PAIR_MISSING"
    assert decision.explicit_connection_evidence_status == "STRUCT_CONN_LOOP_ABSENT"


def test_ligand_component_mismatch_is_fundamental_negative_path() -> None:
    decision = stage_b0.recover_exact_struct_conn_event_v1(
        _synthetic_mmcif(ligand="XYZ"), _stage_a_row(ligand="LIG"),
    )
    assert decision.recovered is False
    assert decision.status == "LIGAND_COMPONENT_MISMATCH"
    assert decision.fundamental_reject is True


def test_altloc_ambiguity_fails_closed() -> None:
    decision = stage_b0.recover_exact_struct_conn_event_v1(
        _synthetic_mmcif(ambiguous_altloc=True), _stage_a_row(),
    )
    assert decision.recovered is False
    assert decision.status == "ALTLOC_AMBIGUOUS_FAIL_CLOSED"


def test_exact10_formula_rh_hydrogen_and_unsupported_node_contract() -> None:
    formula_only = stage_a.evaluate_exact10_model_bound_graph_v1(
        None, source_formula_unsupported_elements=("Rh",),
    )
    assert formula_only.sample_rejected is False
    assert formula_only.canonical_graph_evidence_available is False
    graph_rh = stage_a.evaluate_exact10_model_bound_graph_v1(("C", "Rh"))
    assert graph_rh.sample_rejected is True
    assert graph_rh.status == "EXACT10_MODEL_BOUND_GRAPH_REJECTED"
    hydrogen = stage_a.evaluate_exact10_model_bound_graph_v1(("H", "C"))
    assert hydrogen.sample_rejected is False
    assert hydrogen.excluded_explicit_hydrogen_count == 1
    unsupported = stage_a.evaluate_exact10_model_bound_graph_v1(("C", "Fe"))
    assert unsupported.sample_rejected is True


def test_external_acquisition_is_distinct_from_true_human_review(
    recovery: list[dict[str, str]], worklist: list[dict[str, str]],
) -> None:
    assert stage_b0.classify_unrecovered_evidence_v1(
        local_raw_structure_found=False,
    ) == "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
    assert stage_b0.classify_unrecovered_evidence_v1(
        local_raw_structure_found=True, exact_event_ambiguous=True,
    ) == "HUMAN_STRUCTURAL_REVIEW_REQUIRED"
    assert {row["recovery_disposition"] for row in recovery} == {
        "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
    }
    assert len(worklist) == 12
    assert {row["worklist_category"] for row in worklist} == {
        "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
    }
    by_identity = {
        (row["pdb_id"], row["ligand_component_id"]): row for row in worklist
    }
    assert "AUTHORIZED_FOR_IDENTITY" in by_identity[("1A54", "MDC")][
        "existing_project_acquisition_authorization_status"
    ]
    assert all(
        "NEW_BOUNDED_AUTHORIZATION_REQUIRED"
        in by_identity[identity]["existing_project_acquisition_authorization_status"]
        for identity in stage_b0.RECOVERY_IDENTITIES[1:]
    )


def test_k36_ued_reuses_mechanism_without_sample_authority(
    recovery: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    series = [
        row for row in recovery
        if (row["pdb_id"], row["ligand_component_id"])
        in stage_b0.K36_UED_IDENTITIES
    ]
    assert len(series) == 8
    assert {row["recovery_mechanism_group"] for row in series} == {
        "K36_UED_SHARED_BOUNDED_MMCIF_STRUCT_CONN_ATOM_SITE_PATH"
    }
    assert all(row["canonical_sample_authority_created"] == "false" for row in series)
    assert manifest["k36_ued_recovery_reuse_possible"] is True
    assert manifest["k36_ued_duplicate_sample_authority_created"] is False


def test_manifest_metrics_are_derived_from_rows(
    artifacts: dict[str, bytes], recovery: list[dict[str, str]],
    worklist: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    dispositions = {value: 0 for value in stage_b0.RECOVERY_DISPOSITIONS}
    for row in recovery:
        dispositions[row["recovery_disposition"]] += 1
    assert manifest["auto_recovered_structural_count"] == sum(
        row["cys_sg_event_recovered"] == "true" for row in recovery
    ) == 0
    assert manifest["auto_recovered_stage_b_eligible_count"] == dispositions[
        "AUTO_RECOVERED_STAGE_B_ELIGIBLE"
    ] == 0
    assert manifest["auto_recovered_downstream_label_review_count"] == 0
    assert manifest["human_structural_review_count"] == 0
    assert manifest["targeted_external_acquisition_required_count"] == 12
    assert manifest["new_reject_count"] == 0
    assert manifest["local_raw_structure_available_count"] == 0
    assert manifest["missing_raw_structure_count"] == 12
    assert manifest["recovery_worklist_row_count"] == len(worklist) == 12
    assert manifest["structural_evidence_recovery_fraction"] == {
        "denominator": 12, "numerator": 0, "value": 0.0,
    }
    assert manifest["remaining_true_human_structural_review_fraction"] == {
        "denominator": 12, "numerator": 0, "value": 0.0,
    }
    for filename in (stage_b0.RECOVERY_FILE, stage_b0.WORKLIST_FILE):
        assert manifest["deterministic_output_hashes"][filename] == hashlib.sha256(
            artifacts[filename]
        ).hexdigest()


def test_1a54_and_6vwe_are_truthfully_bounded(
    recovery: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    by_identity = {
        (row["pdb_id"], row["ligand_component_id"]): row for row in recovery
    }
    one_a54 = by_identity[("1A54", "MDC")]
    assert one_a54["local_raw_structure_found"] == "false"
    assert one_a54["raw_structure_sha256_or_NONE"] == (
        stage_b0.HISTORICAL_1A54_RAW_SHA256
    )
    assert one_a54["explicit_connection_evidence_status"] == (
        "HISTORICAL_MMCIF_STRUCT_CONN_LOOP_ABSENT_AND_PDB_LINK_CONECT_ABSENT"
    )
    six_vwe = by_identity[("6VWE", "JY1")]
    assert six_vwe["exact10_status"] == (
        "EXACT10_FORMULA_UNSUPPORTED_NODE_INCLUSION_UNRESOLVED"
    )
    assert six_vwe["recovery_disposition"] != "REJECT"
    assert manifest["six_vwe_rh_final_status"] == (
        "FORMULA_RH_PRESENT_MODEL_GRAPH_MEMBERSHIP_UNRESOLVED_NO_REJECT"
    )


def test_double_build_and_materialization_are_byte_identical(
    artifacts: dict[str, bytes], tmp_path: Path,
) -> None:
    second = (
        stage_b0.build_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_artifacts_v1()
    )
    assert second == artifacts
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    stage_b0.materialize_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1(
        first_root,
    )
    stage_b0.materialize_covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1(
        second_root,
    )
    for filename in stage_b0.OUTPUT_FILES:
        first = first_root / filename
        second_path = second_root / filename
        assert first.read_bytes() == second_path.read_bytes() == artifacts[filename]
        assert stat.S_IMODE(first.stat().st_mode) == 0o644
    assert stat.S_IMODE(first_root.stat().st_mode) == 0o755


def test_import_has_no_write_network_geometry_model_or_training_side_effect(
    tmp_path: Path, manifest: dict[str, object],
) -> None:
    module_name = (
        "covalent_ext."
        "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1"
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join((
        str(stage_b0.REPO_ROOT), str(stage_b0.REPO_ROOT / "src"),
    ))
    result = subprocess.run(
        (sys.executable, "-c", f"import {module_name}"),
        cwd=tmp_path,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []
    for field in (
        "inverse_reaction_chemistry_executed", "pre_reconstruction_executed",
        "torsion_sampling_executed", "geometry_executed",
        "rdkit_minimization_executed", "model_forward", "backward",
        "optimizer_step", "trainer_fit", "rl", "bulk_acquisition_executed",
        "targeted_acquisition_executed",
    ):
        assert manifest[field] is False
    assert manifest["published_stage_a_modified"] is False
    assert manifest["current11_modified"] is False
    assert manifest["raw_modified"] is False
    assert manifest["ready_for_evidence_recovery_publication"] is True
    assert manifest["ready_for_stage_b_automated_label_and_geometry_pilot"] is True
    assert manifest["ready_for_bulk_expansion"] is False
    assert manifest["ready_for_geometry_loss_activation"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["recommended_next_step_exactly"] == stage_b0.RECOMMENDED_NEXT_STEP
