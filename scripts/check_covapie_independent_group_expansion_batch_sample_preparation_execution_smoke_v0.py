import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext.covapie_independent_group_expansion_batch_sample_preparation_execution_smoke import run


if __name__ == "__main__":
    result = run()
    manifest = result["manifest"]
    if not manifest["all_checks_passed"]:
        raise SystemExit("covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0_failed")
    for key in ["input_confirmed_candidate_count", "sample_execution_count", "sample_preparation_passed_count", "sample_preparation_failed_count", "embedded_qa_passed_count", "embedded_qa_failed_count", "protein_atom_table_written_count", "ligand_atom_table_written_count", "pocket_atom_table_written_count", "covalent_event_table_written_count", "ligand_residue_atom_pair_table_written_count", "total_protein_atom_count", "total_ligand_atom_count", "total_pocket_atom_count", "batch_failure_count", "recommended_next_step"]:
        print(f"{key}={manifest[key]}")
    print(f"accepted_pdb_het_pairs={','.join(manifest['accepted_pdb_het_pairs'])}")
    print(f"covalent_bond_atom_pair_by_pdb_het={manifest['covalent_bond_atom_pair_by_pdb_het']}")
    print("covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0_passed")
