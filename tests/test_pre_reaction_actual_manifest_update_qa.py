from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_pre_reaction_actual_manifest_update_qa import build_markdown, build_qa_rows, write_csv, write_markdown


SOURCE_IDS = ["BTK_C481_6DI9", "KRAS_G12C_5F2E", "KRAS_G12C_6OIM"]
PROPOSED_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]
LIGAND_PATHS = {
    "BTK_C481_6DI9_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf",
    "KRAS_G12C_5F2E_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf",
    "KRAS_G12C_6OIM_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _manifest_row(sample_id: str, ligand_path: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "protein_pdb_path": f"protein/{sample_id}.pdb",
        "ligand_sdf_path": ligand_path,
        "reactive_residue_chain": "A",
        "reactive_residue_id": "1",
        "reactive_residue_type": "CYS",
        "reactive_atom_name": "SG",
        "ligand_reactive_atom_id": "1",
        "warhead_type": "toy",
        "scaffold_atoms": "0",
        "linker_atoms": "1",
        "warhead_atoms": "2",
    }


def _write_inputs(tmp_path: Path) -> dict[str, Path]:
    current = tmp_path / "manifest_real_small.csv"
    backup = tmp_path / "backup.csv"
    proposed = tmp_path / "proposed_rows.csv"
    report = tmp_path / "actual_report.csv"
    qa_report = tmp_path / "qa.csv"
    summary = tmp_path / "summary.md"

    backup_rows = [_manifest_row(sample_id, f"ligand/{sample_id}.sdf") for sample_id in SOURCE_IDS]
    proposed_rows = []
    for proposed_id in PROPOSED_IDS:
        sdf = Path(LIGAND_PATHS[proposed_id])
        sdf.parent.mkdir(parents=True, exist_ok=True)
        sdf.write_text("toy sdf\n", encoding="utf-8")
        proposed_rows.append(_manifest_row(proposed_id, LIGAND_PATHS[proposed_id]))
    current_rows = backup_rows + proposed_rows
    _write_csv(backup, backup_rows)
    _write_csv(current, current_rows)
    _write_csv(proposed, proposed_rows)
    before_hash = _sha256(backup)
    after_hash = _sha256(current)
    report_rows = []
    for source_id, proposed_id in zip(SOURCE_IDS, PROPOSED_IDS):
        report_rows.append(
            {
                "sample_id": source_id,
                "proposed_manifest_sample_id": proposed_id,
                "source_sample_id": source_id,
                "current_manifest_sha256_before": before_hash,
                "backup_manifest_sha256": before_hash,
                "current_manifest_sha256_after": after_hash,
                "actual_manifest_update_status": "manifest_updated_with_3_pre_reaction_rows_after_explicit_approval",
                "manifest_updated": "true",
                "backup_created": "true",
                "new_full_manifest_created": "false",
                "sdf_modified": "false",
                "sdf_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "blocking_reasons": "",
            }
        )
    _write_csv(report, report_rows)
    return {
        "current": current,
        "backup": backup,
        "proposed": proposed,
        "report": report,
        "qa_report": qa_report,
        "summary": summary,
    }


def _run(paths: dict[str, Path]) -> list[dict[str, str]]:
    return build_qa_rows(
        current_manifest_csv=paths["current"],
        backup_manifest_csv=paths["backup"],
        proposed_rows_csv=paths["proposed"],
        actual_update_report_csv=paths["report"],
    )


def _mutate_csv(path: Path, mutator) -> None:
    rows = _read_csv(path)
    mutator(rows)
    _write_csv(path, rows)


def test_actual_manifest_update_qa_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    hashes = {name: _sha256(path) for name, path in paths.items() if path.exists() and path.suffix == ".csv"}

    rows = _run(paths)
    write_csv(rows, paths["qa_report"])
    write_markdown(build_markdown(rows), paths["summary"])

    assert {row["actual_manifest_update_qa_status"] for row in rows} == {"actual_manifest_update_qa_passed"}
    assert {row["backup_matches_report_before_hash"] for row in rows} == {"true"}
    assert {row["current_matches_report_after_hash"] for row in rows} == {"true"}
    assert {row["row_count_current_equals_backup_plus_3"] for row in rows} == {"true"}
    assert {row["existing_rows_preserved"] for row in rows} == {"true"}
    assert {row["appended_rows_match_proposed_rows"] for row in rows} == {"true"}
    assert {row["proposed_row_present_once"] for row in rows} == {"true"}
    assert {row["source_row_still_present"] for row in rows} == {"true"}
    assert {row["proposed_ligand_sdf_exists"] for row in rows} == {"true"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert "Pre-Reaction Actual Manifest Update QA Summary" in paths["summary"].read_text(encoding="utf-8")
    for name, old_hash in hashes.items():
        if name not in {"qa_report"}:
            assert _sha256(paths[name]) == old_hash
    assert len(list(tmp_path.rglob("*.sdf"))) == 3


def test_backup_hash_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["report"], lambda rows: rows[0].update({"current_manifest_sha256_before": "bad"}))

    rows = _run(paths)

    assert rows[0]["actual_manifest_update_qa_status"] == "blocked"
    assert "backup_hash_mismatch_report_before_hash" in rows[0]["blocking_reasons"]


def test_current_manifest_hash_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["report"], lambda rows: rows[0].update({"current_manifest_sha256_after": "bad"}))

    rows = _run(paths)

    assert rows[0]["actual_manifest_update_qa_status"] == "blocked"
    assert "current_manifest_hash_mismatch_report_after_hash" in rows[0]["blocking_reasons"]


def test_current_manifest_not_backup_plus_three_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["current"])[:-1]
    _write_csv(paths["current"], rows)

    qa_rows = _run(paths)

    assert {row["actual_manifest_update_qa_status"] for row in qa_rows} == {"blocked"}
    assert any("current_manifest_not_backup_plus_3_rows" in row["blocking_reasons"] for row in qa_rows)


def test_existing_rows_modified_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["current"])
    rows[0]["protein_pdb_path"] = "changed.pdb"
    _write_csv(paths["current"], rows)

    qa_rows = _run(paths)

    assert {row["actual_manifest_update_qa_status"] for row in qa_rows} == {"blocked"}
    assert any("existing_manifest_rows_not_preserved" in row["blocking_reasons"] for row in qa_rows)


def test_appended_rows_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["current"])
    rows[-1]["warhead_type"] = "changed"
    _write_csv(paths["current"], rows)

    qa_rows = _run(paths)

    assert {row["actual_manifest_update_qa_status"] for row in qa_rows} == {"blocked"}
    assert any("appended_rows_do_not_match_proposed_rows" in row["blocking_reasons"] for row in qa_rows)


def test_schema_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["proposed"])
    rows[0]["extra"] = "bad"
    with paths["proposed"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    qa_rows = _run(paths)

    assert {row["actual_manifest_update_qa_status"] for row in qa_rows} == {"blocked"}
    assert any("proposed_schema_mismatch_manifest" in row["blocking_reasons"] for row in qa_rows)


def test_duplicate_proposed_sample_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["current"])
    rows.append(rows[-1])
    _write_csv(paths["current"], rows)

    qa_rows = _run(paths)

    assert any(row["proposed_manifest_sample_id"] == "KRAS_G12C_6OIM_pre_reaction" and row["actual_manifest_update_qa_status"] == "blocked" for row in qa_rows)
    assert any("proposed_sample_not_present_once" in row["blocking_reasons"] for row in qa_rows)


def test_ligand_sdf_path_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["proposed"], lambda rows: rows[0].update({"ligand_sdf_path": "wrong.sdf"}))

    qa_rows = _run(paths)

    assert qa_rows[0]["actual_manifest_update_qa_status"] == "blocked"
    assert "proposed_ligand_sdf_path_incorrect" in qa_rows[0]["blocking_reasons"]


def test_actual_update_report_sdf_modified_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["report"], lambda rows: rows[0].update({"sdf_modified": "true"}))

    qa_rows = _run(paths)

    assert qa_rows[0]["actual_manifest_update_qa_status"] == "blocked"
    assert "sdf_modified_not_false" in qa_rows[0]["blocking_reasons"]


def test_actual_update_report_training_ready_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["report"], lambda rows: rows[0].update({"training_ready": "true"}))

    qa_rows = _run(paths)

    assert qa_rows[0]["actual_manifest_update_qa_status"] == "blocked"
    assert "training_ready_not_false" in qa_rows[0]["blocking_reasons"]
