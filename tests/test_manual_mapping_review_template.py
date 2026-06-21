from pathlib import Path
import csv
import hashlib
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_manual_mapping_review_template import (
    DEFAULT_INCLUDE_CONFIDENCE,
    TEMPLATE_COLUMNS,
    build_template_rows,
    write_template,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path) -> None:
    fieldnames = [
        "sample_id",
        "extracted_atom_id",
        "extracted_element",
        "extracted_pdb_atom_name",
        "reference_candidate_atom_id",
        "reference_element",
        "graph_distance_to_reactive_atom",
        "final_role",
        "is_reactive_atom",
        "mapping_confidence",
        "mapping_warning",
    ]
    rows = [
        ("0", "high"),
        ("1", "medium"),
        ("2", "low"),
        ("3", "unresolved"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for atom_id, confidence in rows:
            writer.writerow(
                {
                    "sample_id": "toy",
                    "extracted_atom_id": atom_id,
                    "extracted_element": "C",
                    "extracted_pdb_atom_name": f"C{atom_id}",
                    "reference_candidate_atom_id": atom_id,
                    "reference_element": "C",
                    "graph_distance_to_reactive_atom": atom_id,
                    "final_role": "scaffold",
                    "is_reactive_atom": "false",
                    "mapping_confidence": confidence,
                    "mapping_warning": "",
                }
            )


def test_template_includes_default_confidence_values_without_modifying_input(tmp_path):
    report = tmp_path / "graph_repair_report.csv"
    output = tmp_path / "manual_mapping_review_template.csv"
    write_report(report)
    before_hash = sha256(report)

    rows = build_template_rows(report, set(DEFAULT_INCLUDE_CONFIDENCE))
    write_template(rows, output)

    assert sha256(report) == before_hash
    assert output.exists()

    with output.open("r", encoding="utf-8", newline="") as handle:
        parsed_rows = list(csv.DictReader(handle))

    assert len(parsed_rows) == 3
    assert set(TEMPLATE_COLUMNS).issubset(parsed_rows[0])
    assert {row["mapping_confidence"] for row in parsed_rows} == {"medium", "low", "unresolved"}
    assert "high" not in {row["mapping_confidence"] for row in parsed_rows}
    for row in parsed_rows:
        assert row["manual_reference_atom_id"] == ""
        assert row["manual_decision"] == ""
        assert row["manual_note"] == ""
