from pathlib import Path
import csv
import hashlib
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_warhead_local_mapping_review_template import TEMPLATE_COLUMNS, build_template_rows, write_template


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
        {"atom_id": "0", "distance": "0", "role": "warhead", "reactive": "true", "confidence": "high"},
        {"atom_id": "1", "distance": "5", "role": "warhead", "reactive": "false", "confidence": "medium"},
        {"atom_id": "2", "distance": "3", "role": "scaffold", "reactive": "false", "confidence": "medium"},
        {"atom_id": "3", "distance": "4", "role": "scaffold", "reactive": "false", "confidence": "medium"},
        {"atom_id": "4", "distance": "9", "role": "linker", "reactive": "false", "confidence": "low"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            atom_id = row["atom_id"]
            writer.writerow(
                {
                    "sample_id": "toy",
                    "extracted_atom_id": atom_id,
                    "extracted_element": "C",
                    "extracted_pdb_atom_name": f"C{atom_id}",
                    "reference_candidate_atom_id": atom_id,
                    "reference_element": "C",
                    "graph_distance_to_reactive_atom": row["distance"],
                    "final_role": row["role"],
                    "is_reactive_atom": row["reactive"],
                    "mapping_confidence": row["confidence"],
                    "mapping_warning": "",
                }
            )


def test_warhead_local_template_selection_without_modifying_input(tmp_path):
    report = tmp_path / "graph_repair_report.csv"
    output = tmp_path / "warhead_local_template.csv"
    write_report(report)
    before_hash = sha256(report)

    rows = build_template_rows(report, max_graph_distance=3)
    write_template(rows, output)

    assert sha256(report) == before_hash
    assert output.exists()

    with output.open("r", encoding="utf-8", newline="") as handle:
        parsed_rows = list(csv.DictReader(handle))

    included_atom_ids = {row["extracted_atom_id"] for row in parsed_rows}
    assert "0" in included_atom_ids  # reactive atom, even with high confidence.
    assert "1" in included_atom_ids  # final_role=warhead.
    assert "2" in included_atom_ids  # graph distance <= 3.
    assert "3" not in included_atom_ids  # far scaffold with no low confidence.
    assert "4" in included_atom_ids  # low confidence linker.

    assert set(TEMPLATE_COLUMNS).issubset(parsed_rows[0])
    by_atom_id = {row["extracted_atom_id"]: row for row in parsed_rows}
    assert "reactive_atom" in by_atom_id["0"]["local_review_reason"]
    assert "warhead_atom" in by_atom_id["1"]["local_review_reason"]
    assert "within_graph_distance_3" in by_atom_id["2"]["local_review_reason"]
    assert "low_confidence_warhead_or_linker" in by_atom_id["4"]["local_review_reason"]
    for row in parsed_rows:
        assert row["manual_reference_atom_id"] == ""
        assert row["manual_decision"] == ""
        assert row["manual_note"] == ""
