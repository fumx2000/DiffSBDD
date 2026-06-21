from pathlib import Path
import csv
import hashlib
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from summarize_graph_repair_readiness import SUMMARY_COLUMNS, summarize_report, write_summary


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path, confidences: list[tuple[str, bool]]) -> None:
    fieldnames = [
        "sample_id",
        "extracted_atom_id",
        "is_reactive_atom",
        "mapping_confidence",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for atom_idx, (confidence, is_reactive) in enumerate(confidences):
            writer.writerow(
                {
                    "sample_id": "toy",
                    "extracted_atom_id": atom_idx,
                    "is_reactive_atom": str(is_reactive).lower(),
                    "mapping_confidence": confidence,
                }
            )


def test_summary_flags_manual_review_without_modifying_input(tmp_path):
    report = tmp_path / "toy_graph_repair_report.csv"
    output = tmp_path / "summary.csv"
    write_report(report, [("high", True), ("medium", False), ("low", False)])
    before_hash = sha256(report)

    summary = summarize_report(report)
    write_summary([summary], output)

    assert sha256(report) == before_hash
    assert output.exists()

    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    assert set(SUMMARY_COLUMNS).issubset(row)
    assert row["sample_id"] == "toy"
    assert row["total_atoms"] == "3"
    assert row["reactive_atom_confidence"] == "high"
    assert row["reactive_atom_ready"] == "true"
    assert row["low_count"] == "1"
    assert row["whole_graph_auto_repair_ready"] == "false"
    assert row["needs_manual_mapping_review"] == "true"
    assert row["recommended_next_action"] == "manual_mapping_review_before_bond_order_transfer"
    assert "does not repair bond orders" in row["summary_warning"]
