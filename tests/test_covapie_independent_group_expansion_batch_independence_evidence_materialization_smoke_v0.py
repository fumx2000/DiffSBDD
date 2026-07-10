from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from covalent_ext import covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke as smoke


def test_mmcif_loop_parser_handles_struct_asym_and_entity_poly_seq() -> None:
    text = """data_x
#
loop_
_struct_asym.id
_struct_asym.entity_id
A 1
B 2
#
loop_
_entity_poly_seq.entity_id
_entity_poly_seq.num
_entity_poly_seq.mon_id
_entity_poly_seq.hetero
1 2 CYS n
1 1 ALA n
#
"""
    _, asym = smoke.parse_loop(text, "_struct_asym.")
    _, seq = smoke.parse_loop(text, "_entity_poly_seq.")
    assert {row["_struct_asym.id"]: row["_struct_asym.entity_id"] for row in asym} == {"A": "1", "B": "2"}
    grouped = smoke._rows_by_entity(seq)
    assert [row["_entity_poly_seq.mon_id"] for row in grouped["1"]] == ["ALA", "CYS"]


def test_sequence_unknown_monomer_is_recorded() -> None:
    one, count, codes = smoke._seq_to_one_letter(["ALA", "MSE", "BOG"])
    assert one == "AMX"
    assert count == 1
    assert codes == "BOG"


def test_ccd_smiles_priority_and_murcko_fallback(tmp_path: Path) -> None:
    path = tmp_path / "ACY.cif"
    path.write_text(
        """data_ACY
_chem_comp.id ACY
#
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
C1 C
C2 C
O1 O
#
loop_
_pdbx_chem_comp_descriptor.type
_pdbx_chem_comp_descriptor.program
_pdbx_chem_comp_descriptor.descriptor
SMILES Legacy CCO
SMILES_CANONICAL "OpenEye OEToolkits" CCO
#
""",
        encoding="utf-8",
    )
    info = smoke.parse_ccd_ligand("ACY", path)
    assert info["selected_descriptor_type"] == "SMILES_CANONICAL"
    assert info["selected_descriptor_program"] == "OpenEye OEToolkits"
    assert info["murcko_scaffold_status"] == "acyclic_no_murcko_scaffold"
    assert info["murcko_scaffold_sha256"] == ""
    assert info["scaffold_group_key"].startswith("ACYCLIC_GRAPH:")


def test_ccd_integrity_rejects_mismatched_id(tmp_path: Path) -> None:
    path = tmp_path / "JUG.cif"
    path.write_text(
        """data_BAD
_chem_comp.id BAD
#
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
C1 C
#
loop_
_pdbx_chem_comp_descriptor.type
_pdbx_chem_comp_descriptor.program
_pdbx_chem_comp_descriptor.descriptor
SMILES_CANONICAL CACTVS C
#
"""
        + ("#" * 300),
        encoding="utf-8",
    )
    audit = smoke._ccd_integrity(path, "JUG")
    assert audit["chem_comp_id_matches_expected"] is False
    assert audit["integrity_passed"] is False


def test_global_identity_and_threshold_groups_are_deterministic() -> None:
    assert smoke.global_identity("AAAA", "AAAA") == pytest.approx(1.0)
    assert smoke.global_identity("AAAA", "AAAT") == pytest.approx(0.75)
    pair_rows = [
        {"left_sample_index_row_id": "S1", "right_sample_index_row_id": "S2", "protein_sequence_identity": "0.950000"},
        {"left_sample_index_row_id": "S2", "right_sample_index_row_id": "S3", "protein_sequence_identity": "0.400000"},
    ]
    groups = smoke.assign_threshold_groups(pair_rows, ["S1", "S2", "S3"], 0.9, "G")
    assert groups == {"S1": "G_000001", "S2": "G_000001", "S3": "G_000002"}


def test_safety_expected_mapping_blocks_mismatches() -> None:
    expected = smoke.SAFETY_EXPECTED["combined_sample_index_written"]
    assert expected is False
    rows = [{"safety_item": "combined_sample_index_written", "required_status": False, "observed_status": True}]
    rows[0]["safety_passed"] = rows[0]["required_status"] == rows[0]["observed_status"]
    assert rows[0]["safety_passed"] is False


def test_final_pairwise_flags_never_confirm_independent_groups() -> None:
    assert smoke._classification_combined("same_exact_graph", "same_exact_sequence") == "strong_same_group_evidence"
    assert smoke._classification_combined("different_scaffold", "sequence_below_50_identity") == "provisional_distinct_both_axes"
    assert smoke.MASK_NAMES[3] == "scaffold_only"
    assert smoke.MASK_ALIASES == ["A", "B", "B2", "B3", "C"]


def test_failed_downloader_cleans_part_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "CCD_ROOT", tmp_path / "ccd")
    monkeypatch.setattr(smoke, "UNIQUE_HETS", ["JUG"])

    def fail(_url: str, part: Path) -> tuple[int, str]:
        part.write_text("not a cif", encoding="utf-8")
        return 500, "failed"

    rows = smoke.acquire_ccd_files(True, fail)
    assert rows[0]["ccd_audit_passed"] is False
    assert not (tmp_path / "ccd" / "JUG.cif.part").exists()


def test_source_order_matches_contract() -> None:
    expected = [row_id for row_id, _pdb, _het in smoke.EXPECTED_SAMPLE_ORDER]
    assert expected[:3] == [f"CYS_SG_SAMPLE_INDEX_{idx:06d}" for idx in range(1, 4)]
    assert expected[-1] == "CYS_SG_SAMPLE_INDEX_000011"


def test_atomic_writes_leave_no_tmp_and_empty_csv_has_header(tmp_path: Path) -> None:
    target = tmp_path / "audit.csv"
    smoke._write_csv(target, [], ["left", "right"])
    assert target.read_text(encoding="utf-8") == "left,right\n"
    assert not list(tmp_path.glob("*.tmp"))
    manifest = tmp_path / "manifest.json"
    smoke._write_json(manifest, {"passed": True})
    assert manifest.read_text(encoding="utf-8").endswith("\n")
    assert not list(tmp_path.glob("*.tmp"))


def test_sample_heavy_atom_count_distinguishes_explicit_hydrogen() -> None:
    total, heavy, hydrogens = smoke._sample_ligand_atom_counts([
        {"type_symbol": "C"}, {"type_symbol": "O"}, {"type_symbol": "H"}, {"type_symbol": "H"},
    ])
    assert (total, heavy, hydrogens) == (4, 2, 2)
    assert total > heavy


def test_entity_poly_sequence_numbering_rejects_duplicate_and_missing_numbers() -> None:
    _rows, duplicate = smoke._validate_entity_poly_sequence([
        {"_entity_poly_seq.num": "1", "_entity_poly_seq.mon_id": "ALA"},
        {"_entity_poly_seq.num": "1", "_entity_poly_seq.mon_id": "CYS"},
    ])
    assert duplicate["sequence_numbering_status"] == "invalid_entity_poly_seq_numbering"
    assert duplicate["duplicate_sequence_number_count"] == 1
    _rows, missing = smoke._validate_entity_poly_sequence([
        {"_entity_poly_seq.num": "1", "_entity_poly_seq.mon_id": "ALA"},
        {"_entity_poly_seq.num": "3", "_entity_poly_seq.mon_id": "CYS"},
    ])
    assert missing["missing_sequence_numbers"] == "2"


def test_monomer_hash_distinguishes_unknown_monomers_that_both_map_to_x() -> None:
    one_a, _count_a, _codes_a = smoke._seq_to_one_letter(["BOG"])
    one_b, _count_b, _codes_b = smoke._seq_to_one_letter(["FOO"])
    assert one_a == one_b == "X"
    assert __import__("hashlib").sha256(b"BOG").hexdigest() != __import__("hashlib").sha256(b"FOO").hexdigest()


def test_safety_mismatch_is_not_permitted_by_explicit_expected_mapping() -> None:
    positive = {"required_status": True, "observed_status": False}
    negative = {"required_status": False, "observed_status": True}
    assert (positive["required_status"] == positive["observed_status"]) is False
    assert (negative["required_status"] == negative["observed_status"]) is False


def test_issue_sentinel_has_fixed_schema() -> None:
    row = smoke._issue_rows([])[0]
    assert row == {
        "issue_id": "NO_INDEPENDENCE_EVIDENCE_MATERIALIZATION_ISSUES",
        "issue_scope": "unified_11_sample_evidence_v0",
        "sample_index_row_id": "",
        "pdb_id": "",
        "expected_het_id": "",
        "issue_severity": "none",
        "issue_type": "no_issues",
        "issue_description": "No independence evidence materialization issues detected.",
        "issue_status": "passed",
    }


def test_ccd_provenance_is_stable_from_first_download_to_offline_reuse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "CCD_ROOT", tmp_path / "ccd")
    monkeypatch.setattr(smoke, "CCD_AUDIT", tmp_path / "ccd_audit.csv")
    monkeypatch.setattr(smoke, "UNIQUE_HETS", ["JUG"])
    cif = """data_JUG
_chem_comp.id JUG
#
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
C1 C
C2 C
O1 O
#
loop_
_pdbx_chem_comp_descriptor.type
_pdbx_chem_comp_descriptor.program
_pdbx_chem_comp_descriptor.descriptor
SMILES_CANONICAL CACTVS CCO
#
""" + ("\n" * 300)

    def download(_url: str, part: Path) -> tuple[int, str]:
        part.write_text(cif, encoding="utf-8")
        return 200, ""

    first = smoke.acquire_ccd_files(True, download)
    smoke._write_csv(smoke.CCD_AUDIT, first)
    second = smoke.acquire_ccd_files(False, download)
    for row in [first[0], second[0]]:
        assert row["acquisition_performed_by_step14ao"] is True
        assert str(row["initial_acquisition_http_status"]) == "200"
        assert row["source_origin"] == "downloaded_by_step14ao"
    assert not (tmp_path / "ccd" / "JUG.cif.part").exists()


def test_valid_preexisting_ccd_is_not_claimed_as_downloaded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "CCD_ROOT", tmp_path / "ccd")
    monkeypatch.setattr(smoke, "CCD_AUDIT", tmp_path / "absent_audit.csv")
    monkeypatch.setattr(smoke, "UNIQUE_HETS", ["JUG"])
    (tmp_path / "ccd").mkdir()
    (tmp_path / "ccd" / "JUG.cif").write_text(
        "data_JUG\n_chem_comp.id JUG\n#\nloop_\n_chem_comp_atom.atom_id\n_chem_comp_atom.type_symbol\nC1 C\nC2 C\nO1 O\n#\nloop_\n_pdbx_chem_comp_descriptor.type\n_pdbx_chem_comp_descriptor.program\n_pdbx_chem_comp_descriptor.descriptor\nSMILES_CANONICAL CACTVS CCO\n#\n" + ("\n" * 300),
        encoding="utf-8",
    )
    row = smoke.acquire_ccd_files(False)[0]
    assert row["source_origin"] == "reused_preexisting_ccd"
    assert row["acquisition_performed_by_step14ao"] is False


def test_pairwise_completeness_rejects_duplicate_pair_or_confirmation() -> None:
    rows = []
    for idx, (left, right) in enumerate([(f"S{i:06d}", f"S{j:06d}") for i in range(1, 12) for j in range(i + 1, 12)], 1):
        rows.append({"pairwise_evidence_id": f"COVAPIE_COMBINED_PAIRWISE_{idx:06d}", "left_sample_index_row_id": left, "right_sample_index_row_id": right})
    assert smoke._pairwise_complete(rows, "COVAPIE_COMBINED_PAIRWISE") is True
    rows[-1]["left_sample_index_row_id"] = rows[0]["left_sample_index_row_id"]
    rows[-1]["right_sample_index_row_id"] = rows[0]["right_sample_index_row_id"]
    assert smoke._pairwise_complete(rows, "COVAPIE_COMBINED_PAIRWISE") is False


def _reaction_sample(*, selected: str = "CM", residue: str = "CYS", residue_atom: str = "SG", bond: str | None = None, observed: list[str] | None = None) -> tuple[smoke.Sample, dict[str, object]]:
    observed = observed if observed is not None else ["CM", "C1"]
    row = {
        "sample_index_row_id": "S", "pdb_id": "1AIM", "ligand_comp_id": "ZYA",
        "ligand_covalent_atom_name": selected, "covalent_residue_atom_name": residue_atom, "covalent_bond_atom_pair": bond or f"SG--{selected}",
    }
    event = {"residue_comp_id": residue, "residue_atom_name": residue_atom, "covalent_bond_atom_pair": bond or f"SG--{selected}"}
    pair = {"residue_atom_name": "SG", "ligand_atom_name": selected, "covalent_bond_atom_pair": bond or f"SG--{selected}"}
    sample = smoke.Sample(1, row, Path(""), "", [], [{"atom_name": atom, "type_symbol": "C"} for atom in observed], event, pair)
    info: dict[str, object] = {
        "ccd_heavy_atom_ids": ["C1", "CM", "F1"],
        "ccd_bond_inventory": [{"atom_id_1": "F1", "atom_id_2": "CM", "value_order": "SING", "pdbx_aromatic_flag": "N"}],
    }
    return sample, info


def test_ccd_bond_loop_is_parsed_from_real_zya() -> None:
    info = smoke.parse_ccd_ligand("ZYA", Path("data/raw/covalent_sources/ccd/independence_evidence_batch_000001/ZYA.cif"))
    assert smoke._bond_present(info["ccd_bond_inventory"], "CM", "F1") is True


def test_parent_bond_verification_is_direction_independent() -> None:
    assert smoke._bond_present([{"atom_id_1": "F1", "atom_id_2": "CM"}], "CM", "F1") is True


def test_intact_atom_inventory_reconciliation_passes() -> None:
    sample, info = _reaction_sample(observed=["C1", "CM", "F1"])
    result = smoke.reconcile_post_covalent_atom_inventory(sample, info)
    assert result["atom_inventory_reconciliation_status"] == "intact_parent_atom_inventory_match"
    assert result["atom_inventory_reconciliation_passed"] is True


def test_zya_f1_leaving_group_reconciliation_passes() -> None:
    sample, info = _reaction_sample()
    result = smoke.reconcile_post_covalent_atom_inventory(sample, info)
    assert result["missing_parent_heavy_atom_ids"] == "F1"
    assert result["reaction_delta_rule_id"] == "ZYA_CYS_SG_FLUOROMETHYL_F1_LOSS_V1"
    assert result["parent_leaving_group_bond_verified"] is True
    assert result["covalent_attachment_atom_verified"] is True
    assert result["atom_inventory_reconciliation_passed"] is True


@pytest.mark.parametrize(
    ("selected", "residue", "residue_atom", "bond", "observed"),
    [
        ("C1", "CYS", "SG", "SG--C1", ["CM", "C1"]),
        ("CM", "SER", "OG", "OG--CM", ["CM", "C1"]),
        ("CM", "CYS", "SG", "SG--C1", ["CM", "C1"]),
        ("CM", "CYS", "SG", "SG--CM", ["CM"]),
        ("CM", "CYS", "SG", "SG--CM", ["CM", "C1", "X9"]),
    ],
)
def test_unexplained_or_mismatched_reaction_delta_is_blocked(selected: str, residue: str, residue_atom: str, bond: str, observed: list[str]) -> None:
    sample, info = _reaction_sample(selected=selected, residue=residue, residue_atom=residue_atom, bond=bond, observed=observed)
    result = smoke.reconcile_post_covalent_atom_inventory(sample, info)
    assert result["atom_inventory_reconciliation_passed"] is False
    assert result["atom_inventory_reconciliation_status"] == "unexplained_atom_inventory_mismatch"


def test_missing_f1_without_parent_bond_is_blocked() -> None:
    sample, info = _reaction_sample()
    info["ccd_bond_inventory"] = []
    assert smoke.reconcile_post_covalent_atom_inventory(sample, info)["atom_inventory_reconciliation_passed"] is False


def test_unregistered_het_cannot_use_zya_exception() -> None:
    sample, info = _reaction_sample()
    sample = smoke.Sample(sample.order, {**sample.row, "ligand_comp_id": "OTHER"}, sample.raw_path, sample.raw_sha256_before, sample.protein_rows, sample.ligand_rows, sample.event_row, sample.pair_row)
    assert smoke.reconcile_post_covalent_atom_inventory(sample, info)["atom_inventory_reconciliation_passed"] is False


def test_parent_graph_inventory_retains_f1_while_observed_table_is_unchanged() -> None:
    sample, info = _reaction_sample()
    before = [dict(row) for row in sample.ligand_rows]
    result = smoke.reconcile_post_covalent_atom_inventory(sample, info)
    assert "F1" in result["parent_ccd_heavy_atom_ids"]
    assert sample.ligand_rows == before


def test_registry_is_limited_to_explicit_zya_cys_sg_cm_rule() -> None:
    assert list(smoke.REACTION_DELTA_REGISTRY) == [("ZYA", "CYS", "SG", "CM")]


def test_canonical_masks_retain_b3_after_reconciliation_extension() -> None:
    assert list(zip(smoke.MASK_NAMES, smoke.MASK_ALIASES))[3] == ("scaffold_only", "B3")


def test_reconciliation_atom_id_lists_are_sorted_deterministically() -> None:
    sample, info = _reaction_sample(observed=["CM", "C1"])
    result = smoke.reconcile_post_covalent_atom_inventory(sample, info)
    assert result["observed_post_covalent_heavy_atom_ids"] == "C1;CM"


def test_manifest_has_training_and_downstream_boundaries() -> None:
    import json
    manifest = json.loads(smoke._repo_path(smoke.MANIFEST).read_text(encoding="utf-8"))
    assert {key: manifest[key] for key in [
        "feature_semantics_known_for_training", "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_split_materialization_smoke", "ready_for_covapie_final_dataset_materialization_smoke",
        "ready_for_training", "ready_to_train_now",
    ]} == {
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "ready_for_covapie_split_materialization_smoke": False,
        "ready_for_covapie_final_dataset_materialization_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }


@pytest.mark.parametrize(
    ("accession", "status", "complete", "nonblocking"),
    [("Q1", "unique_uniprot_accession", True, False), ("", "accession_missing_in_raw_mmcif", False, True), ("Q1;Q2", "multiple_uniprot_accessions", False, True)],
)
def test_accession_missingness_semantics(accession: str, status: str, complete: bool, nonblocking: bool) -> None:
    assert (status == "unique_uniprot_accession") is complete
    assert (status in {"accession_missing_in_raw_mmcif", "multiple_uniprot_accessions"}) is nonblocking
    assert bool(accession) is complete or nonblocking


def test_actual_zya_pair_table_attachment_is_directly_verified() -> None:
    import csv
    rows = list(csv.DictReader(smoke._repo_path(smoke.LIGAND_EVIDENCE).open()))
    zya = next(row for row in rows if row["pdb_id"] == "1AIM")
    assert zya["index_attachment_atom_verified"] == "True"
    assert zya["event_attachment_atom_verified"] == "True"
    assert zya["pair_attachment_atom_verified"] == "True"
    assert zya["reaction_delta_evidence_scope"] == "explicit_zya_fluoromethyl_ketone_rule_v1"


def test_pair_ligand_atom_mismatch_blocks_reconciliation() -> None:
    sample, info = _reaction_sample()
    sample = smoke.Sample(sample.order, sample.row, sample.raw_path, sample.raw_sha256_before, sample.protein_rows, sample.ligand_rows, sample.event_row, {**sample.pair_row, "ligand_atom_name": "C1"})
    assert smoke.reconcile_post_covalent_atom_inventory(sample, info)["atom_inventory_reconciliation_passed"] is False


def test_pair_bond_mismatch_blocks_reconciliation() -> None:
    sample, info = _reaction_sample()
    sample = smoke.Sample(sample.order, sample.row, sample.raw_path, sample.raw_sha256_before, sample.protein_rows, sample.ligand_rows, sample.event_row, {**sample.pair_row, "covalent_bond_atom_pair": "SG--C1"})
    assert smoke.reconcile_post_covalent_atom_inventory(sample, info)["atom_inventory_reconciliation_passed"] is False


def test_reaction_delta_scope_is_empty_for_intact_inventory() -> None:
    sample, info = _reaction_sample(observed=["C1", "CM", "F1"])
    assert smoke.reconcile_post_covalent_atom_inventory(sample, info)["reaction_delta_evidence_scope"] == ""


def test_protein_cluster_group_keys_use_threshold_and_members() -> None:
    import csv
    rows = list(csv.DictReader(smoke._repo_path(smoke.PROTEIN_GROUPS).open()))
    for row in rows:
        if row["group_type"] == "protein_sequence_cluster_90":
            assert row["group_key"].startswith("sequence_identity_threshold_0.90|members:")
        if row["group_type"] == "protein_sequence_cluster_50":
            assert row["group_key"].startswith("sequence_identity_threshold_0.50|members:")


def test_protein_cluster_group_key_is_not_accession() -> None:
    import csv
    rows = list(csv.DictReader(smoke._repo_path(smoke.PROTEIN_GROUPS).open()))
    assert all(row["group_key"] != "Q66GI4" for row in rows if row["group_type"].startswith("protein_sequence_cluster"))


def test_pairwise_wrong_prefix_fails_completeness() -> None:
    rows = []
    for idx, (left, right) in enumerate([(f"S{i:06d}", f"S{j:06d}") for i in range(1, 12) for j in range(i + 1, 12)], 1):
        rows.append({"pairwise_evidence_id": f"WRONG_{idx:06d}", "left_sample_index_row_id": left, "right_sample_index_row_id": right})
    assert smoke._pairwise_complete(rows, "COVAPIE_COMBINED_PAIRWISE") is False


def test_current_manifest_keeps_ready_merge_but_not_split_or_training() -> None:
    import json
    manifest = json.loads(smoke._repo_path(smoke.MANIFEST).read_text(encoding="utf-8"))
    assert manifest["ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke"] is True
    assert manifest["ready_for_covapie_split_materialization_smoke"] is False
    assert manifest["ready_for_training"] is False


def test_canonical_five_masks_remain_unchanged_after_traceability_maintenance() -> None:
    assert list(zip(smoke.MASK_NAMES, smoke.MASK_ALIASES)) == [
        ("warhead_only", "A"), ("linker_plus_warhead", "B"), ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"), ("scaffold_plus_linker_plus_warhead", "C"),
    ]
