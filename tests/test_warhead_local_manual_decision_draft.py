from pathlib import Path
import csv
import hashlib
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from init_warhead_local_manual_decision_draft import (
    DECISION_WARNING,
    EXTRA_COLUMNS,
    build_decision_draft_rows,
    write_decision_draft,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_template(path: Path) -> list[str]:
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
        "local_review_reason",
        "manual_reference_atom_id",
        "manual_decision",
        "manual_note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "sample_id": "toy",
                "extracted_atom_id": "1",
                "extracted_element": "C",
                "extracted_pdb_atom_name": "C1",
                "reference_candidate_atom_id": "1",
                "reference_element": "C",
                "graph_distance_to_reactive_atom": "0",
                "final_role": "warhead",
                "is_reactive_atom": "true",
                "mapping_confidence": "high",
                "mapping_warning": "",
                "local_review_reason": "reactive_atom;warhead_atom",
                "manual_reference_atom_id": "",
                "manual_decision": "",
                "manual_note": "",
            }
        )
    return fieldnames


def test_decision_draft_defaults_without_modifying_template(tmp_path):
    template = tmp_path / "template.csv"
    output = tmp_path / "decision_draft.csv"
    original_fieldnames = write_template(template)
    before_hash = sha256(template)

    fieldnames, rows = build_decision_draft_rows(template)
    write_decision_draft(fieldnames, rows, output)

    assert sha256(template) == before_hash
    assert output.exists()
    assert fieldnames[: len(original_fieldnames)] == original_fieldnames
    for extra_column in EXTRA_COLUMNS:
        assert extra_column in fieldnames

    with output.open("r", encoding="utf-8", newline="") as handle:
        parsed_rows = list(csv.DictReader(handle))

    assert len(parsed_rows) == 1
    row = parsed_rows[0]
    assert row["manual_reference_atom_id"] == ""
    assert row["manual_decision"] == ""
    assert row["manual_note"] == ""
    assert row["review_status"] == "not_reviewed"
    assert row["decision_source"] == "empty_manual_draft"
    assert row["decision_warning"] == DECISION_WARNING
