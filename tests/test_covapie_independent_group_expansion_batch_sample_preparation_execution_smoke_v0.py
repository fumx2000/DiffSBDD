import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from covalent_ext import covapie_independent_group_expansion_batch_sample_preparation_execution_smoke as gate
from covalent_ext.covapie_independent_group_expansion_batch_sample_preparation_execution_smoke import MASK_ALIASES, MASK_NAMES, prepare_from_text


def _mmcif(atom="C2", het="E64", ligand_chain="B", reverse=False, extra=False):
    p1, p2 = (het, "CYS") if reverse else ("CYS", het)
    return f'''data_x
loop_
_struct_conn.id
_struct_conn.conn_type_id
_struct_conn.ptnr1_label_comp_id
_struct_conn.ptnr1_label_atom_id
_struct_conn.ptnr1_auth_asym_id
_struct_conn.ptnr1_auth_seq_id
_struct_conn.ptnr1_label_asym_id
_struct_conn.ptnr1_label_seq_id
_struct_conn.ptnr2_label_comp_id
_struct_conn.ptnr2_label_atom_id
_struct_conn.ptnr2_auth_asym_id
_struct_conn.ptnr2_auth_seq_id
_struct_conn.ptnr2_label_asym_id
_struct_conn.ptnr2_label_seq_id
_struct_conn.pdbx_dist_value
covale1 covale {p1} {'SG' if p1 == 'CYS' else atom} {'A' if p1 == 'CYS' else ligand_chain} {'25' if p1 == 'CYS' else '300'} {'A' if p1 == 'CYS' else ligand_chain} {'25' if p1 == 'CYS' else '300'} {p2} {'SG' if p2 == 'CYS' else atom} {'A' if p2 == 'CYS' else ligand_chain} {'25' if p2 == 'CYS' else '300'} {'A' if p2 == 'CYS' else ligand_chain} {'25' if p2 == 'CYS' else '300'} 1.800
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.auth_atom_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.label_alt_id
_atom_site.pdbx_PDB_model_num
ATOM 1 S SG CYS A 25 SG CYS A 25 0.0 0.0 0.0 1.0 . 1
ATOM 2 C CA CYS A 25 CA CYS A 25 1.0 0.0 0.0 1.0 A 1
HETATM 3 C {atom} {het} {ligand_chain} 300 {atom} {het} {ligand_chain} 300 1.8 0.0 0.0 1.0 . 1
HETATM 4 C X1 {het} {ligand_chain} 300 X1 {het} {ligand_chain} 300 2.8 0.0 0.0 1.0 . 1
{('HETATM 5 C '+atom+' '+het+' C 301 '+atom+' '+het+' C 301 9.0 0.0 0.0 1.0 . 1' if extra else '')}
'''


def _sample(atom="C2", het="E64"):
    return {"sample_preparation_input_id": "S1", "sample_execution_id": "E1", "pdb_id": "TEST", "expected_het_id": het, "selected_struct_conn_id": "covale1", "selected_ligand_atom_name": atom}


def test_dynamic_ligand_atom_and_pair_distance():
    result = prepare_from_text(_sample(), _mmcif())
    assert result["checks"] and all(result["checks"].values())
    assert result["event_rows"][0]["covalent_bond_atom_pair"] == "SG--C2"
    assert result["pair_rows"][0]["ligand_atom_name"] == "C2"
    assert result["computed_distance"] == 1.8
    assert result["distance_delta"] == 0.0


def test_dynamic_cm_and_reverse_partner_and_instance_selection():
    result = prepare_from_text(_sample("CM", "ZYA"), _mmcif("CM", "ZYA", reverse=True, extra=True))
    assert all(result["checks"].values())
    assert result["event_rows"][0]["covalent_bond_atom_pair"] == "SG--CM"
    assert len(result["ligand_rows"]) == 2
    assert sum(row["is_covalent_ligand_atom"] for row in result["ligand_rows"]) == 1


def test_failure_is_isolated_and_masks_are_canonical():
    result = prepare_from_text(_sample(), _mmcif(atom="C3"))
    assert not result["checks"]["selected_struct_conn_event_revalidated"]
    assert result["protein_rows"] == []
    assert MASK_NAMES == ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
    assert MASK_ALIASES == ["A", "B", "B2", "B3", "C"]


def test_explicit_safety_expected_status_mapping_rejects_both_mismatches():
    observed = dict(gate.SAFETY_EXPECTED)
    observed["raw_mmcif_read_current_step"] = False
    observed["network_access_used_current_step"] = True
    by_item = {row["safety_item"]: row for row in gate._safety_rows(observed)}
    assert by_item["raw_mmcif_read_current_step"]["required_status"] is True
    assert by_item["raw_mmcif_read_current_step"]["safety_passed"] is False
    assert by_item["network_access_used_current_step"]["required_status"] is False
    assert by_item["network_access_used_current_step"]["safety_passed"] is False
    assert by_item["network_access_used_current_step"]["blocking_reasons"] == "network_access_used_current_step"


def test_safety_failure_blocks_ready_and_all_checks():
    assert gate._ready(True, True, True) is True
    assert gate._ready(True, True, False) is False
    assert not (gate._ready(True, True, False))


def test_per_sample_table_presence_requires_all_six(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "REPO", tmp_path)
    paths = gate._sample_paths("TEST", "E64")
    for key in gate.SAMPLE_TABLE_KEYS:
        target = tmp_path / paths[key]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("header\n", encoding="utf-8")
    assert gate._per_sample_tables_written([paths]) is True
    (tmp_path / paths["pair"]).unlink()
    assert gate._per_sample_tables_written([paths]) is False


def test_raw_path_name_without_file_does_not_resolve(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "REPO", tmp_path)
    assert gate._raw_file_resolved(Path("raw/does_not_exist.cif"), {"raw_file_resolved": True}) is False
