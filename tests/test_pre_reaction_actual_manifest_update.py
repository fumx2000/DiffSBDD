from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_pre_reaction_actual_manifest_update import APPROVAL_PHRASE, EXPECTED_PROPOSED_IDS, apply_update


SOURCE_IDS = ["BTK_C481_6DI9", "KRAS_G12C_5F2E", "KRAS_G12C_6OIM"]
PROPOSED_IDS = [
    "BTK_C481_6DI9_pre_reaction",
    "KRAS_G12C_5F2E_pre_reaction",
    "KRAS_G12C_6OIM_pre_reaction",
]


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
    current_manifest = tmp_path / "manifest_real_small.csv"
    proposed_rows = tmp_path / "proposed_rows.csv"
    dry_run_report = tmp_path / "dry_run_report.csv"
    backup = tmp_path / "backup.csv"
    report = tmp_path / "report.csv"
    summary = tmp_path / "summary.md"
    source_rows = [_manifest_row(sample_id, f"ligand/{sample_id}.sdf") for sample_id in SOURCE_IDS]
    _write_csv(current_manifest, source_rows)

    proposed_manifest_rows: list[dict[str, str]] = []
    dry_rows: list[dict[str, str]] = []
    for source_id, proposed_id in zip(SOURCE_IDS, PROPOSED_IDS):
        ligand_path = Path(EXPECTED_PROPOSED_IDS[proposed_id])
        ligand_path.parent.mkdir(parents=True, exist_ok=True)
        ligand_path.write_text("toy sdf\n", encoding="utf-8")
        proposed_manifest_rows.append(_manifest_row(proposed_id, EXPECTED_PROPOSED_IDS[proposed_id]))
        dry_rows.append(
            {
                "sample_id": source_id,
                "proposed_manifest_sample_id": proposed_id,
                "source_sample_id": source_id,
                "manifest_update_dry_run_status": "passed_manifest_update_dry_run_not_written",
                "would_add_manifest_row_later": "true",
                "manifest_updated": "false",
                "new_manifest_created": "false",
                "training_ready": "false",
                "blocking_reasons": "",
            }
        )
    _write_csv(proposed_rows, proposed_manifest_rows)
    _write_csv(dry_run_report, dry_rows)
    return {
        "current_manifest": current_manifest,
        "proposed_rows": proposed_rows,
        "dry_run_report": dry_run_report,
        "backup": backup,
        "report": report,
        "summary": summary,
    }


def _run(paths: dict[str, Path], approval_phrase: str = APPROVAL_PHRASE) -> list[dict[str, str]]:
    return apply_update(
        current_manifest_csv=paths["current_manifest"],
        proposed_rows_csv=paths["proposed_rows"],
        dry_run_report_csv=paths["dry_run_report"],
        approval_phrase=approval_phrase,
        backup_manifest_csv=paths["backup"],
        output_report_csv=paths["report"],
        output_md=paths["summary"],
    )


def test_actual_manifest_update_appends_three_rows_after_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])
    before_rows = _read_csv(paths["current_manifest"])

    report_rows = _run(paths)

    after_rows = _read_csv(paths["current_manifest"])
    backup_rows = _read_csv(paths["backup"])
    proposed_rows = _read_csv(paths["proposed_rows"])
    assert paths["backup"].exists()
    assert _sha256(paths["backup"]) == before_hash
    assert _sha256(paths["current_manifest"]) != before_hash
    assert len(after_rows) == len(before_rows) + 3
    assert backup_rows == before_rows
    assert after_rows[: len(before_rows)] == before_rows
    assert after_rows[len(before_rows) :] == proposed_rows
    assert len(report_rows) == 3
    assert {row["actual_manifest_update_status"] for row in report_rows} == {
        "manifest_updated_with_3_pre_reaction_rows_after_explicit_approval"
    }
    assert {row["manifest_updated"] for row in report_rows} == {"true"}
    assert {row["backup_created"] for row in report_rows} == {"true"}
    assert {row["new_full_manifest_created"] for row in report_rows} == {"false"}
    assert {row["sdf_modified"] for row in report_rows} == {"false"}
    assert {row["sdf_generated"] for row in report_rows} == {"false"}
    assert {row["training_ready"] for row in report_rows} == {"false"}
    assert paths["report"].exists()
    assert paths["summary"].exists()
    assert "Pre-Reaction Actual Manifest Update Summary" in paths["summary"].read_text(encoding="utf-8")


def test_wrong_approval_phrase_does_not_modify_manifest_or_create_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])

    with pytest.raises(ValueError, match="approval_phrase_mismatch"):
        _run(paths, approval_phrase="WRONG")

    assert _sha256(paths["current_manifest"]) == before_hash
    assert not paths["backup"].exists()
    assert not paths["report"].exists()


def test_existing_backup_blocks_without_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])
    paths["backup"].write_text("existing backup\n", encoding="utf-8")
    backup_hash = _sha256(paths["backup"])

    with pytest.raises(FileExistsError):
        _run(paths)

    assert _sha256(paths["current_manifest"]) == before_hash
    assert _sha256(paths["backup"]) == backup_hash


def test_proposed_schema_mismatch_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])
    rows = _read_csv(paths["proposed_rows"])
    rows[0]["extra_column"] = "bad"
    with paths["proposed_rows"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="proposed_rows_schema_does_not_match_manifest"):
        _run(paths)

    assert _sha256(paths["current_manifest"]) == before_hash
    assert not paths["backup"].exists()


def test_proposed_row_count_not_three_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])
    rows = _read_csv(paths["proposed_rows"])[:2]
    _write_csv(paths["proposed_rows"], rows)

    with pytest.raises(ValueError, match="proposed_rows_count_not_3"):
        _run(paths)

    assert _sha256(paths["current_manifest"]) == before_hash
    assert not paths["backup"].exists()


def test_current_manifest_already_contains_proposed_sample_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])
    manifest_rows = _read_csv(paths["current_manifest"])
    manifest_rows.append(_read_csv(paths["proposed_rows"])[0])
    _write_csv(paths["current_manifest"], manifest_rows)
    before_hash = _sha256(paths["current_manifest"])

    with pytest.raises(ValueError, match="current_manifest_already_contains_proposed_sample"):
        _run(paths)

    assert _sha256(paths["current_manifest"]) == before_hash
    assert not paths["backup"].exists()


def test_dry_run_not_passed_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])
    dry_rows = _read_csv(paths["dry_run_report"])
    dry_rows[0]["manifest_update_dry_run_status"] = "blocked"
    _write_csv(paths["dry_run_report"], dry_rows)

    with pytest.raises(ValueError, match="dry_run_report_field_not_expected"):
        _run(paths)

    assert _sha256(paths["current_manifest"]) == before_hash
    assert not paths["backup"].exists()


def test_missing_proposed_ligand_sdf_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    before_hash = _sha256(paths["current_manifest"])
    missing_path = Path(_read_csv(paths["proposed_rows"])[0]["ligand_sdf_path"])
    missing_path.unlink()

    with pytest.raises(FileNotFoundError, match="proposed ligand SDF does not exist"):
        _run(paths)

    assert _sha256(paths["current_manifest"]) == before_hash
    assert not paths["backup"].exists()
