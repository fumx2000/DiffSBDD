from pathlib import Path
import csv
import hashlib
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from summarize_warhead_local_manual_decisions import build_markdown, summarize_drafts, write_csv, write_markdown


FIELDNAMES = [
    "sample_id",
    "extracted_atom_id",
    "final_role",
    "is_reactive_atom",
    "local_review_reason",
    "manual_decision",
    "review_status",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_draft(path: Path) -> None:
    rows = [
        {
            "sample_id": "toy",
            "extracted_atom_id": "1",
            "final_role": "warhead",
            "is_reactive_atom": "true",
            "local_review_reason": "reactive_atom;warhead_atom",
            "manual_decision": "accept_candidate",
            "review_status": "reviewed",
        },
        {
            "sample_id": "toy",
            "extracted_atom_id": "2",
            "final_role": "linker",
            "is_reactive_atom": "false",
            "local_review_reason": "low_confidence_warhead_or_linker",
            "manual_decision": "unresolved",
            "review_status": "needs_followup",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def test_manual_decision_summary_counts_and_readiness_without_modifying_input(tmp_path):
    draft = tmp_path / "draft.csv"
    output_csv = tmp_path / "summary.csv"
    output_md = tmp_path / "summary.md"
    write_draft(draft)
    before_hash = sha256(draft)

    rows = summarize_drafts([draft])
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    assert sha256(draft) == before_hash
    assert output_csv.exists()
    assert output_md.exists()

    row = rows[0]
    assert row["sample_id"] == "toy"
    assert row["accept_candidate_count"] == "1"
    assert row["unresolved_count"] == "1"
    assert row["has_empty_manual_decision"] == "false"
    assert row["all_warhead_atoms_accepted"] == "true"
    assert row["has_unresolved_boundary"] == "true"
    assert row["local_bond_order_transfer_ready"] == "false"

    text = output_md.read_text(encoding="utf-8")
    assert "Warhead-Local Manual Decision Summary" in text
    assert "No sample is ready for cross-boundary local bond-order transfer" in text
