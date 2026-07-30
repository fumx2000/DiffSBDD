#!/usr/bin/env python3
"""Prepare the external Current11 warhead-boundary human-review workspace."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PACKAGE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_v1"
)
MANIFEST_FILE = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_manifest.json"
)
INDEX_FILE = "covapie_current11_warhead_boundary_review_package_index.csv"
OPTIONS_FILE = (
    "covapie_current11_warhead_boundary_candidate_review_options.csv"
)
TEMPLATES_FILE = (
    "covapie_current11_warhead_boundary_review_record_templates.csv"
)
SOURCE_FILES = (MANIFEST_FILE, INDEX_FILE, OPTIONS_FILE, TEMPLATES_FILE)
SOURCE_SHA256 = {
    MANIFEST_FILE: (
        "5eff02e8ec764e35696e83136e61151c27a1d3101f811bcfbaa79278448015ea"
    ),
    INDEX_FILE: (
        "ead184e5bd092d6b10770ebdd3688cf2b8f72b7e30a29d1957aa5e4d06b7cd33"
    ),
    OPTIONS_FILE: (
        "bdac9a806043a81aff4310f2931d4431f1d8966e21437f150b15360f281f353d"
    ),
    TEMPLATES_FILE: (
        "62a98848db9fb44f0cc597f8b78755de3e981f1ffba6985853a29e9ed90088f8"
    ),
}

INDEX_FIELDS = (
    "package_index_version",
    "package_item_order_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_proposal_record_sha256",
    "source_assignment_record_sha256",
    "source_candidate_set_sha256",
    "total_candidate_count",
    "admitted_candidate_count",
    "source_proposal_status",
    "candidate_option_row_start_0based",
    "candidate_option_row_end_exclusive",
    "review_record_version",
    "unreviewed_template_payload_sha256",
    "review_options_materialized",
    "review_template_materialized",
    "ready_for_human_review",
    "human_review_completed",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_role_proposal_generation",
    "blocking_reasons",
    "verified",
)
OPTION_FIELDS = (
    "package_option_version",
    "package_item_order_0based",
    "option_order_within_sample_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_proposal_record_sha256",
    "source_candidate_set_sha256",
    "source_bridge_candidate_index_0based",
    "source_bridge_candidate_record_sha256",
    "boundary_bond_id",
    "warhead_attachment_atom_id",
    "nonwarhead_boundary_atom_id",
    "boundary_bond_order",
    "warhead_side_atom_ids",
    "warhead_extra_atom_ids_beyond_local_center",
    "local_reaction_center_atom_ids",
    "required_leaving_group_atom_ids",
    "warhead_side_atom_count",
    "nonwarhead_side_atom_count",
    "candidate_admitted",
    "review_eligible",
    "blocking_reasons",
    "package_option_record_sha256",
)
TEMPLATE_FIELDS = (
    "review_record_version",
    "review_unit_type",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_proposal_record_sha256",
    "source_assignment_record_sha256",
    "source_candidate_set_sha256",
    "total_candidate_count",
    "admitted_candidate_count",
    "review_decision",
    "selected_bridge_candidate_index_0based",
    "selected_bridge_candidate_record_sha256",
    "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order",
    "reviewed_boundary_bond_id",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "review_record_sha256",
)
WORKLIST_IDENTITY_FIELDS = (
    "package_item_order_0based",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_proposal_record_sha256",
    "source_assignment_record_sha256",
    "source_candidate_set_sha256",
    "total_candidate_count",
    "admitted_candidate_count",
    "candidate_option_row_start_0based",
    "candidate_option_row_end_exclusive",
)
WORKLIST_HUMAN_FIELDS = (
    "review_decision",
    "selected_bridge_candidate_index_0based",
    "selected_bridge_candidate_record_sha256",
    "reviewed_warhead_atom_ids_json",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order",
    "reviewed_boundary_bond_id",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "reviewer_provenance_attested",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
    "review_completed",
)
WORKLIST_FIELDS = WORKLIST_IDENTITY_FIELDS + WORKLIST_HUMAN_FIELDS
INITIAL_HUMAN_VALUES = {
    "review_decision": "not_reviewed",
    "selected_bridge_candidate_index_0based": "",
    "selected_bridge_candidate_record_sha256": "",
    "reviewed_warhead_atom_ids_json": "[]",
    "reviewed_warhead_attachment_atom_id": "",
    "reviewed_nonwarhead_boundary_atom_id": "",
    "reviewed_attachment_boundary_bond_order": "",
    "reviewed_boundary_bond_id": "",
    "reviewer_id": "",
    "review_rationale": "",
    "review_notes": "",
    "reviewer_provenance_attested": "false",
    "reviewer_provenance_attestor_id": "",
    "submission_source_label": "",
    "review_completed": "false",
}
WORKSPACE_FILES = (
    "review_worklist.csv",
    "eligible_candidate_options.csv",
    "README.md",
)

README_TEXT = """# CovaPIE Current11 warhead atom-set and attachment-boundary review

This workspace contains 11 samples awaiting real human review. No sample has
been reviewed, approved, or submitted by creation of this workspace.

## Files and matching samples

- `review_worklist.csv` has one row per sample. Enter review results only in
  the human-fillable columns.
- `eligible_candidate_options.csv` contains the 185 options whose frozen
  `review_eligible` value is `true`.
- Match the two CSV files with `sample_index_row_id`.

For each worklist row, `candidate_option_row_start_0based` is inclusive and
`candidate_option_row_end_exclusive` is exclusive. These values describe the
sample's range in the original complete 200-row candidate-options file. They
are not physical row numbers in this filtered 185-row workspace copy. Within a
matched sample, use `option_order_within_sample_0based` to read the preserved
option order.

The original complete 200-row options file, including 15 review-ineligible
options, remains in the committed package directory:

`data/derived/covalent_small/covapie_current11_warhead_atom_set_and_attachment_boundary_review_packages_v1/covapie_current11_warhead_boundary_candidate_review_options.csv`

The workspace copies only the 185 review-eligible options to make manual
review easier. Atom IDs, boundaries, candidate SHA256 values, and option order
are frozen source values and have not been recalculated.

## Completing one review

The only allowed final values for `review_decision` are:

- `select_admitted_candidate`
- `revise_atom_set_and_boundary`
- `quarantine`

`not_reviewed` means the review is unfinished and cannot be submitted.

For `select_admitted_candidate`, fill in
`selected_bridge_candidate_index_0based` from
`source_bridge_candidate_index_0based`, fill in
`selected_bridge_candidate_record_sha256` from
`source_bridge_candidate_record_sha256`, and fill every reviewed atom and
boundary field from the human-reviewed result.

For `revise_atom_set_and_boundary`, leave both selected-candidate fields empty
and manually fill the reviewed atom set and boundary fields.

For `quarantine`, leave both selected-candidate fields and all reviewed
boundary fields empty. Keep `reviewed_warhead_atom_ids_json` as `[]`.

For every completed review, a real reviewer must fill `reviewer_id` and
`review_rationale`. `review_notes` may be used for additional context. A real
human must change `reviewer_provenance_attested` to `true` after the review and
identify the attestor in `reviewer_provenance_attestor_id`. Only after all
required fields are correct should the reviewer change `review_completed` to
`true`.

Do not modify the identity columns from
`package_item_order_0based` through
`candidate_option_row_end_exclusive`.

## What happens next

This workspace is not a formal submission bundle and must not be added to Git.
After real human review is complete,
`compile_covapie_current11_real_human_review_submission_bundle_v1` will compile
the completed worklist into a strict JSON bundle. Creating this workspace does
not run that compiler, the public submission adapter, ingestion, or any
authority-producing operation.
"""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _parse_csv(
    payload: bytes,
    *,
    expected_fields: Sequence[str],
    label: str,
) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} is not valid UTF-8") from exc
    with io.StringIO(text, newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(expected_fields):
            raise ValueError(f"{label} field contract does not match")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{label} contains a malformed CSV row")
    return rows


def _require_manifest_contract(manifest: Mapping[str, Any]) -> None:
    expected = {
        "package_index_count": 11,
        "review_template_count": 11,
        "package_option_record_count": 200,
        "review_eligible_option_count": 185,
        "review_ineligible_option_count": 15,
        "warhead_boundary_human_review_completed_count": 0,
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            raise ValueError(f"manifest {field} must equal {value!r}")
    if manifest.get("ready_for_warhead_boundary_human_review") is not True:
        raise ValueError(
            "manifest ready_for_warhead_boundary_human_review must be true"
        )
    if tuple(manifest.get("package_option_fields", ())) != OPTION_FIELDS:
        raise ValueError("manifest package option fields do not match")
    output_sha = manifest.get("output_sha256")
    if not isinstance(output_sha, dict):
        raise ValueError("manifest output_sha256 must be an object")
    for name in (INDEX_FILE, OPTIONS_FILE, TEMPLATES_FILE):
        if output_sha.get(name) != SOURCE_SHA256[name]:
            raise ValueError(f"manifest source hash does not match for {name}")


def _require_package_contract(
    index_rows: Sequence[Mapping[str, str]],
    option_rows: Sequence[Mapping[str, str]],
    template_rows: Sequence[Mapping[str, str]],
) -> None:
    if len(index_rows) != 11 or len(template_rows) != 11:
        raise ValueError("package index and review template counts must both be 11")
    if len(option_rows) != 200:
        raise ValueError("candidate option count must be 200")

    expected_orders = [str(value) for value in range(11)]
    if [row["package_item_order_0based"] for row in index_rows] != expected_orders:
        raise ValueError("package index must be sorted in exact 0-based order")
    sample_ids = [row["sample_index_row_id"] for row in index_rows]
    if len(set(sample_ids)) != 11:
        raise ValueError("package index sample IDs must be unique")
    templates_by_sample = {
        row["sample_index_row_id"]: row for row in template_rows
    }
    if len(templates_by_sample) != 11 or set(templates_by_sample) != set(sample_ids):
        raise ValueError("review templates must match all package samples exactly")

    shared_identity = tuple(
        field for field in WORKLIST_IDENTITY_FIELDS
        if field not in {
            "package_item_order_0based",
            "candidate_option_row_start_0based",
            "candidate_option_row_end_exclusive",
        }
    )
    expected_template_initial = {
        "review_decision": "not_reviewed",
        "selected_bridge_candidate_index_0based": "",
        "selected_bridge_candidate_record_sha256": "",
        "reviewed_warhead_atom_ids": "[]",
        "reviewed_warhead_attachment_atom_id": "",
        "reviewed_nonwarhead_boundary_atom_id": "",
        "reviewed_attachment_boundary_bond_order": "",
        "reviewed_boundary_bond_id": "",
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        "review_record_sha256": "",
    }
    cursor = 0
    for package_row in index_rows:
        template = templates_by_sample[package_row["sample_index_row_id"]]
        if any(template[field] != package_row[field] for field in shared_identity):
            raise ValueError("package index/template identity mismatch")
        if any(
            template[field] != value
            for field, value in expected_template_initial.items()
        ):
            raise ValueError("review templates must remain unreviewed and unfilled")
        if package_row["human_review_completed"] != "false":
            raise ValueError("package human review completed state must be false")
        if package_row["ready_for_human_review"] != "true":
            raise ValueError("every package item must be ready for human review")

        start = int(package_row["candidate_option_row_start_0based"])
        end = int(package_row["candidate_option_row_end_exclusive"])
        total = int(package_row["total_candidate_count"])
        if start != cursor or end - start != total or not 0 <= start <= end <= 200:
            raise ValueError("candidate option spans must cover source rows exactly")
        sample_options = option_rows[start:end]
        expected_option_orders = [str(value) for value in range(total)]
        if [
            row["option_order_within_sample_0based"] for row in sample_options
        ] != expected_option_orders:
            raise ValueError("candidate option order within a sample is invalid")
        for source_row_index, option in enumerate(sample_options, start=start):
            if (
                option["package_item_order_0based"] != str(source_row_index)
                or option["sample_index_row_id"]
                != package_row["sample_index_row_id"]
            ):
                raise ValueError("candidate option package identity mismatch")
        cursor = end
    if cursor != 200:
        raise ValueError("candidate option spans must end at row 200")

    flags = [row["review_eligible"] for row in option_rows]
    if any(flag not in {"true", "false"} for flag in flags):
        raise ValueError("candidate review eligibility must be true or false")
    if flags.count("true") != 185 or flags.count("false") != 15:
        raise ValueError("candidate review eligibility counts must be 185/15")


def load_frozen_package(
    repo_root: Path,
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    """Load and validate only the four committed Current11 package sources."""
    root = repo_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"repo root is not a directory: {root}")
    package_root = root / PACKAGE_ROOT
    payloads: dict[str, bytes] = {}
    for name in SOURCE_FILES:
        path = package_root / name
        if not path.is_file():
            raise ValueError(f"required committed package source is missing: {path}")
        payload = path.read_bytes()
        if _sha256(payload) != SOURCE_SHA256[name]:
            raise ValueError(f"committed package source SHA256 mismatch: {path}")
        payloads[name] = payload
    try:
        manifest = json.loads(payloads[MANIFEST_FILE])
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("package manifest is not valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict):
        raise ValueError("package manifest must be a JSON object")
    _require_manifest_contract(manifest)
    index_rows = _parse_csv(
        payloads[INDEX_FILE],
        expected_fields=INDEX_FIELDS,
        label=INDEX_FILE,
    )
    option_rows = _parse_csv(
        payloads[OPTIONS_FILE],
        expected_fields=OPTION_FIELDS,
        label=OPTIONS_FILE,
    )
    template_rows = _parse_csv(
        payloads[TEMPLATES_FILE],
        expected_fields=TEMPLATE_FIELDS,
        label=TEMPLATES_FILE,
    )
    _require_package_contract(index_rows, option_rows, template_rows)
    return index_rows, option_rows, template_rows


def _csv_bytes(
    fields: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def build_workspace_payloads(repo_root: Path) -> dict[str, bytes]:
    """Build the deterministic Exact3 workspace entirely in memory."""
    index_rows, option_rows, template_rows = load_frozen_package(repo_root)
    templates_by_sample = {
        row["sample_index_row_id"]: row for row in template_rows
    }
    worklist_rows = []
    for package_row in index_rows:
        template = templates_by_sample[package_row["sample_index_row_id"]]
        row = {
            field: (
                package_row[field]
                if field in {
                    "package_item_order_0based",
                    "candidate_option_row_start_0based",
                    "candidate_option_row_end_exclusive",
                }
                else template[field]
            )
            for field in WORKLIST_IDENTITY_FIELDS
        }
        row.update(INITIAL_HUMAN_VALUES)
        worklist_rows.append(row)
    eligible_rows = [
        dict(row) for row in option_rows if row["review_eligible"] == "true"
    ]
    if len(worklist_rows) != 11 or len(eligible_rows) != 185:
        raise AssertionError("validated workspace row counts changed unexpectedly")
    return {
        "review_worklist.csv": _csv_bytes(WORKLIST_FIELDS, worklist_rows),
        "eligible_candidate_options.csv": _csv_bytes(
            OPTION_FIELDS, eligible_rows
        ),
        "README.md": README_TEXT.encode("utf-8"),
    }


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def prepare_workspace(repo_root: Path, output_dir: Path) -> dict[str, object]:
    """Validate frozen inputs and write an external, initially empty workspace."""
    root = repo_root.expanduser().resolve()
    destination = output_dir.expanduser().resolve()
    if _is_within(destination, root):
        raise ValueError("output directory must be outside the repository")
    if destination.exists():
        if not destination.is_dir():
            raise FileExistsError(
                f"output path exists and is not a directory: {destination}"
            )
        if any(destination.iterdir()):
            raise FileExistsError(
                f"output directory exists and is non-empty; refusing to overwrite: "
                f"{destination}"
            )

    payloads = build_workspace_payloads(root)
    if tuple(payloads) != WORKSPACE_FILES:
        raise AssertionError("workspace payload set is not Exact3")
    if not destination.exists():
        destination.mkdir(parents=True)
    created: list[Path] = []
    try:
        for name in WORKSPACE_FILES:
            path = destination / name
            with path.open("xb") as handle:
                handle.write(payloads[name])
            created.append(path)
    except BaseException:
        for path in reversed(created):
            path.unlink()
        raise
    return {
        "workspace": str(destination),
        "workspace_files": WORKSPACE_FILES,
        "worklist_rows": 11,
        "eligible_option_rows": 185,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the external Current11 warhead atom-set and "
            "attachment-boundary human-review workspace v1."
        )
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = prepare_workspace(args.repo_root, args.output_dir)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"workspace={result['workspace']}")
    print("workspace_files=3")
    print("worklist_rows=11")
    print("eligible_option_rows=185")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
