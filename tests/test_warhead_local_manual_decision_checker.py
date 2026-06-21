from pathlib import Path
import csv
import hashlib
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from check_warhead_local_manual_decision_draft import validate_draft


FIELDNAMES = [
    "sample_id",
    "extracted_atom_id",
    "reference_candidate_atom_id",
    "final_role",
    "is_reactive_atom",
    "mapping_confidence",
    "local_review_reason",
    "manual_reference_atom_id",
    "manual_decision",
    "manual_note",
    "review_status",
    "decision_source",
    "decision_warning",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base_row(**overrides: str) -> dict[str, str]:
    row = {
        "sample_id": "toy",
        "extracted_atom_id": "1",
        "reference_candidate_atom_id": "4",
        "final_role": "warhead",
        "is_reactive_atom": "true",
        "mapping_confidence": "high",
        "local_review_reason": "reactive_atom;warhead_atom",
        "manual_reference_atom_id": "",
        "manual_decision": "",
        "manual_note": "",
        "review_status": "not_reviewed",
        "decision_source": "empty_manual_draft",
        "decision_warning": "manual draft only",
    }
    row.update(overrides)
    return row


def write_draft(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def errors_for(path: Path) -> list[str]:
    summaries = validate_draft(path)
    return [error for summary in summaries for error in summary.errors]


def test_empty_manual_decision_not_reviewed_passes_without_modifying_input(tmp_path):
    draft = tmp_path / "draft.csv"
    write_draft(draft, [base_row()])
    before_hash = sha256(draft)

    summaries = validate_draft(draft)

    assert sha256(draft) == before_hash
    assert len(summaries) == 1
    assert summaries[0].errors == []
    assert summaries[0].warnings == ["manual decisions are still empty for one or more rows"]


def test_accept_candidate_requires_reference_candidate_atom_id(tmp_path):
    draft = tmp_path / "draft.csv"
    write_draft(
        draft,
        [
            base_row(
                reference_candidate_atom_id="",
                manual_decision="accept_candidate",
                review_status="reviewed",
            )
        ],
    )

    assert any("accept_candidate requires reference_candidate_atom_id" in error for error in errors_for(draft))


def test_replace_candidate_requires_manual_reference_atom_id(tmp_path):
    draft = tmp_path / "draft.csv"
    write_draft(
        draft,
        [
            base_row(
                manual_decision="replace_candidate",
                review_status="reviewed",
            )
        ],
    )

    assert any("replace_candidate requires manual_reference_atom_id" in error for error in errors_for(draft))


def test_unresolved_reviewed_fails(tmp_path):
    draft = tmp_path / "draft.csv"
    write_draft(
        draft,
        [
            base_row(
                manual_decision="unresolved",
                review_status="reviewed",
            )
        ],
    )

    assert any("unresolved requires review_status needs_followup or excluded" in error for error in errors_for(draft))


def test_exclude_sample_excluded_passes(tmp_path):
    draft = tmp_path / "draft.csv"
    write_draft(
        draft,
        [
            base_row(
                manual_decision="exclude_sample",
                review_status="excluded",
            )
        ],
    )

    assert errors_for(draft) == []
