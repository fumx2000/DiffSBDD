from pathlib import Path
import csv
import hashlib
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_warhead_local_review_markdown import build_markdown, load_templates, write_markdown


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_template(path: Path) -> None:
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
    rows = [
        {
            "sample_id": "toy_sample",
            "extracted_atom_id": "1",
            "extracted_element": "C",
            "extracted_pdb_atom_name": "C1",
            "reference_candidate_atom_id": "4",
            "reference_element": "C",
            "graph_distance_to_reactive_atom": "0",
            "final_role": "warhead",
            "is_reactive_atom": "true",
            "mapping_confidence": "high",
            "mapping_warning": "",
            "local_review_reason": "reactive_atom;warhead_atom;within_graph_distance_3",
            "manual_reference_atom_id": "",
            "manual_decision": "",
            "manual_note": "",
        }
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_markdown_summary_from_template_without_modifying_input(tmp_path):
    template = tmp_path / "template.csv"
    output = tmp_path / "summary.md"
    write_template(template)
    before_hash = sha256(template)

    content = build_markdown(load_templates([template]))
    write_markdown(content, output)

    assert sha256(template) == before_hash
    assert output.exists()

    text = output.read_text(encoding="utf-8")
    assert "toy_sample" in text
    assert "reactive atom row: 1" in text
    assert "| extracted_atom_id | extracted_pdb_atom_name | extracted_element |" in text
    assert "| 1 | C1 | C |" in text
