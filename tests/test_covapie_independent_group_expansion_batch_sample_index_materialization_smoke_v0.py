import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from covalent_ext import covapie_independent_group_expansion_batch_sample_index_materialization_smoke as gate


ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0")


def _rows(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest():
    return json.loads((ROOT / "covapie_independent_group_expansion_batch_sample_index_materialization_smoke_manifest.json").read_text())


def test_canonical_schema_and_expansion_namespace():
    rows = _rows("expansion_batch_sample_index.csv")
    assert list(rows[0]) == gate.SAMPLE_INDEX_FIELDS
    assert [r["sample_index_row_id"] for r in rows] == [f"CYS_SG_SAMPLE_INDEX_{n:06d}" for n in range(4, 12)]
    assert gate.CANONICAL_MASK_TASK_NAMES[3] == "scaffold_only"
    assert gate.CANONICAL_MASK_TASK_ALIASES == ["A", "B", "B2", "B3", "C"]


def test_csv_json_types_and_dynamic_ligand_pairs():
    csv_rows = _rows("expansion_batch_sample_index.csv")
    json_rows = json.loads((ROOT / "expansion_batch_sample_index.json").read_text())
    assert len(csv_rows) == len(json_rows) == 8
    expected = {"1AEC": ("E64", "C2", "SG--C2"), "1AIM": ("ZYA", "CM", "SG--CM"), "1B02": ("UFP", "C6", "SG--C6")}
    for row in json_rows:
        assert isinstance(row["protein_atom_count"], int)
        assert isinstance(row["bond_distance_angstrom"], float)
        assert isinstance(row["ready_for_training_current_step"], bool)
        assert "JUG" not in row.values() and "CAG" not in row.values() and "SG--CAG" not in row.values()
    for pdb, (het, atom, pair) in expected.items():
        row = next(r for r in json_rows if r["pdb_id"] == pdb)
        assert (row["expected_het_id"], row["ligand_covalent_atom_name"], row["covalent_bond_atom_pair"]) == (het, atom, pair)


def test_traceability_counts_distances_and_cys_1b02():
    rows = _rows("expansion_batch_sample_index.csv")
    for row in rows:
        for field in gate.rpath_fields():
            assert Path(row[field]).is_file()
        assert int(row["covalent_event_count"]) == int(row["ligand_residue_atom_pair_count"]) == 1
    b02 = next(r for r in rows if r["pdb_id"] == "1B02")
    assert b02["covalent_residue_index"] == "161"
    trace = _rows("covapie_expansion_batch_sample_index_row_traceability_audit.csv")
    assert len(trace) == 8 and {r["row_traceability_status"] for r in trace} == {"passed"}


def test_collision_and_safety_mismatches_block_readiness():
    existing = [{"sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000004", "pdb_id": "OLD", "expected_het_id": "OLD"}]
    rows = [{"sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000004", "pdb_id": "X", "expected_het_id": "Y"}]
    collision = gate._collision_rows(rows, existing)[0]
    assert collision["collision_audit_passed"] is False
    observed = dict(gate.SAFETY_EXPECTED); observed["network_access_used_current_step"] = True
    assert next(r for r in gate._safety_rows(observed) if r["safety_item"] == "network_access_used_current_step")["safety_passed"] is False
    assert gate._ready(True, True, True, True, True, True, False) is False


def test_existing_index_hashes_and_final_boundaries():
    manifest = _manifest()
    assert manifest["existing_sample_index_csv_sha256"] == gate.EXISTING_HASHES[gate.EXISTING_CSV]
    assert manifest["existing_sample_index_json_sha256"] == gate.EXISTING_HASHES[gate.EXISTING_JSON]
    assert manifest["combined_sample_index_written"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["confirmed_new_independent_group_count_current_step"] == 0


def test_csv_normalization_detects_count_and_boolean_changes():
    csv_rows = _rows("expansion_batch_sample_index.csv")
    json_rows = json.loads((ROOT / "expansion_batch_sample_index.json").read_text())
    assert gate.normalize_csv_index_rows_for_json_comparison(csv_rows) == json_rows
    changed_count = [dict(row) for row in csv_rows]
    changed_count[0]["protein_atom_count"] = "0"
    assert gate.normalize_csv_index_rows_for_json_comparison(changed_count) != json_rows
    changed_bool = [dict(row) for row in csv_rows]
    changed_bool[0]["ready_for_training_current_step"] = "True"
    assert gate.normalize_csv_index_rows_for_json_comparison(changed_bool) != json_rows


def test_schema_non_null_and_dynamic_semantics_failures_are_blocking():
    rows = json.loads((ROOT / "expansion_batch_sample_index.json").read_text())
    altered = [dict(row) for row in rows]
    altered[0]["ligand_comp_id"] = "WRONG"
    altered[1]["sample_index_status"] = "wrong_status"
    altered[2]["sample_qa_id"] = "CYS_SG_EXPANSION_EMBEDDED_QA_999999"
    altered[3]["conn_id"] = ""
    audits = gate._schema_rows(altered, gate.SAMPLE_INDEX_FIELDS, altered)
    by_field = {row["sample_index_field"]: row for row in audits}
    for field in ["ligand_comp_id", "sample_index_status", "sample_qa_id", "conn_id"]:
        assert by_field[field]["schema_validation_status"] == "failed"
    assert by_field["conn_id"]["non_null_rule_passed"] is False


def test_missing_sources_are_reported_without_uncaught_exception():
    rows, details, blockers = gate._materialize([], [])
    assert rows == details == []
    assert len(blockers) == 8
    assert blockers[0].endswith("missing_execution_source_row")


def test_missing_source_table_is_reported_without_uncaught_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "REPO", tmp_path)
    execution = [{"pdb_id": "1AEC", "expected_het_id": "E64", "sample_artifact_root": "missing/sample"}]
    inventory = [{"pdb_id": "1AEC", "expected_het_id": "E64"}]
    _, _, blockers = gate._materialize(execution, inventory)
    assert any(item.startswith("1AEC/E64:missing_source_table:") for item in blockers)


def test_safety_rows_record_combined_and_hash_style_mismatch():
    observed = dict(gate.SAFETY_EXPECTED)
    observed["combined_sample_index_written"] = True
    observed["existing_sample_index_files_unchanged"] = False
    audit = {row["safety_item"]: row for row in gate._safety_rows(observed)}
    assert audit["combined_sample_index_written"]["safety_passed"] is False
    assert audit["existing_sample_index_files_unchanged"]["safety_passed"] is False
    assert gate._ready(True, True, True, True, True, True, False) is False
