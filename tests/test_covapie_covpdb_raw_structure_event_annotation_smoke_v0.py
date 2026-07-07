from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_covpdb_raw_structure_event_annotation_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_raw_structure_event_annotation_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13AV check script before artifact tests"
    return json.loads(path.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def _synthetic_mmcif(two_links: bool = False, no_struct_conn: bool = False) -> str:
    struct = "" if no_struct_conn else """loop_
_struct_conn.conn_type_id
_struct_conn.ptnr1_label_atom_id
_struct_conn.ptnr1_label_comp_id
_struct_conn.ptnr1_auth_asym_id
_struct_conn.ptnr1_auth_seq_id
_struct_conn.ptnr2_label_atom_id
_struct_conn.ptnr2_label_comp_id
_struct_conn.ptnr2_auth_asym_id
_struct_conn.ptnr2_auth_seq_id
_struct_conn.pdbx_dist_value
covale SG CYS A 145 C10 T29 B 1 1.80
"""
    if two_links:
        struct += "covale ND1 HIS A 41 C11 T29 B 1 1.90\n"
    return f"""data_TEST
{struct}
loop_
_atom_site.label_atom_id
_atom_site.label_comp_id
_atom_site.auth_asym_id
_atom_site.auth_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
SG CYS A 145 0.0 0.0 0.0
C10 T29 B 1 1.0 1.0 1.0
ND1 HIS A 41 2.0 2.0 2.0
C11 T29 B 1 3.0 3.0 3.0
"""


def _pdb_link_line(atom1: str, res1: str, chain1: str, seq1: str, atom2: str, res2: str, chain2: str, seq2: str) -> str:
    chars = list(" " * 80)
    chars[0:6] = list("LINK  ")
    chars[12:16] = list(f"{atom1:>4}")
    chars[17:20] = list(f"{res1:>3}")
    chars[21:22] = list(chain1)
    chars[22:26] = list(f"{seq1:>4}")
    chars[42:46] = list(f"{atom2:>4}")
    chars[47:50] = list(f"{res2:>3}")
    chars[51:52] = list(chain2)
    chars[52:56] = list(f"{seq2:>4}")
    chars[73:78] = list(" 1.80")
    return "".join(chars)


def test_synthetic_mmcif_struct_conn_resolves_preferred_event_key() -> None:
    loops = smoke.parse_mmcif_loops(_synthetic_mmcif(), {"struct_conn", "atom_site"})
    candidates = smoke.extract_mmcif_candidates("TEST", "T29", loops["struct_conn"], loops["atom_site"])
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["chain_id"] == "A"
    assert candidate["residue_name"] == "CYS"
    assert candidate["residue_index"] == "145"
    assert candidate["residue_atom_name"] == "SG"
    assert candidate["ligand_atom_name"] == "C10"
    assert candidate["covalent_bond_atom_pair"] == "SG-C10"
    status = smoke._resolution_for_candidates(candidates, het_found=True, connectivity_found=True)
    assert status == "raw_resolves_preferred_event_key"


def test_synthetic_mmcif_missing_struct_conn_is_no_connectivity() -> None:
    loops = smoke.parse_mmcif_loops(_synthetic_mmcif(no_struct_conn=True), {"struct_conn", "atom_site"})
    candidates = smoke.extract_mmcif_candidates("TEST", "T29", loops.get("struct_conn", []), loops["atom_site"])
    assert candidates == []
    status = smoke._resolution_for_candidates(candidates, het_found=True, connectivity_found=False)
    assert status == "raw_no_connectivity_records_found"


def test_synthetic_mmcif_two_het_links_requires_manual_review() -> None:
    loops = smoke.parse_mmcif_loops(_synthetic_mmcif(two_links=True), {"struct_conn", "atom_site"})
    candidates = smoke.extract_mmcif_candidates("TEST", "T29", loops["struct_conn"], loops["atom_site"])
    assert len(candidates) == 2
    status = smoke._resolution_for_candidates(candidates, het_found=True, connectivity_found=True)
    assert status == "raw_multiple_candidate_links"


def test_synthetic_pdb_link_resolves_preferred_event_key_and_missing_link_blocks() -> None:
    text = _pdb_link_line("SG", "CYS", "A", "145", "C10", "T29", "B", "1")
    links, conect, atoms = smoke.parse_pdb_records(text)
    assert len(links) == 1
    assert conect == []
    assert atoms == {}
    candidates = smoke.extract_pdb_link_candidates("TEST", "T29", links)
    assert len(candidates) == 1
    assert candidates[0]["covalent_bond_atom_pair"] == "SG-C10"
    assert smoke._resolution_for_candidates(candidates, het_found=True, connectivity_found=True) == "raw_resolves_preferred_event_key"
    assert smoke._resolution_for_candidates([], het_found=True, connectivity_found=False) == "raw_no_connectivity_records_found"


def test_artifacts_are_read_only_and_raw_files_are_untracked() -> None:
    manifest = _manifest()
    storage = _csv_rows(ROOT / "covapie_raw_structure_storage_safety_audit.csv")
    assert manifest["stage"] == smoke.STAGE
    assert manifest["attempted_structure_count"] == 5
    assert manifest["raw_structure_download_succeeded_count"] >= 1
    assert manifest["raw_files_created"] is True
    assert manifest["raw_files_tracked"] is False
    assert manifest["raw_files_staged"] is False
    assert manifest["raw_files_committed"] is False
    assert manifest["raw_files_copied_to_derived"] is False
    assert storage
    assert {row["under_allowed_raw_storage_root"] for row in storage} == {"True"}
    assert {row["suffix_allowed"] for row in storage} == {"True"}
    assert {row["raw_file_untracked"] for row in storage} == {"True"}
    assert {row["raw_file_not_staged"] for row in storage} == {"True"}
    assert {row["raw_file_not_committed"] for row in storage} == {"True"}


def test_generated_artifacts_capture_download_and_resolution_boundaries() -> None:
    manifest = _manifest()
    download = _csv_rows(ROOT / "covapie_raw_structure_download_audit.csv")
    resolution = _csv_rows(ROOT / "covapie_raw_structure_event_key_resolution_audit.csv")
    candidates = _csv_rows(ROOT / "covapie_raw_structure_event_candidate_annotation.csv")
    assert len(download) == 5
    assert len(resolution) == 5
    assert len(candidates) >= 5
    assert {row["raw_ligand_downloaded"] for row in download} == {"False"}
    assert {row["archive_downloaded"] for row in download} == {"False"}
    assert {row["candidate_metadata_can_materialize_current_step"] for row in resolution} == {"False"}
    assert {row["allowlist_can_materialize_current_step"] for row in resolution} == {"False"}
    assert manifest["candidate_metadata_materialized"] is False
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["ready_for_covapie_covpdb_raw_structure_event_annotation_qa_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False


def test_no_forbidden_imports_and_canonical_masks() -> None:
    module_path = Path("src/covalent_ext/covapie_covpdb_raw_structure_event_annotation_smoke.py")
    script_path = Path("scripts/check_covapie_covpdb_raw_structure_event_annotation_smoke_v0.py")
    assert _imports_name(module_path, "urllib")
    for name in ["requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    manifest = _manifest()
    mask = _csv_rows(ROOT / "covapie_raw_structure_mask_scope_audit.csv")
    assert [row["canonical_mask_task_name"] for row in mask] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_data_derived_has_no_raw_suffix_artifacts_and_training_blockers_remain() -> None:
    manifest = _manifest()
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    bad = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden]
    assert bad == []
    assert manifest["sdf_read"] is False
    assert manifest["gzip_open_used"] is False
    assert manifest["rdkit_used"] is False
    assert manifest["biopdb_parser_used"] is False
    assert manifest["gemmi_used"] is False
    assert manifest["torch_imported"] is False
    assert manifest["model_forward_called"] is False
    assert manifest["training_allowed"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
