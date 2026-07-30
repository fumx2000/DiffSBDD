"""Compile a completed Current11 human-review workspace in memory."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_design_v1
    as adapter_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1
    as submission_adapter,
)


__all__ = (
    "compile_covapie_current11_real_human_review_submission_bundle_v1",
)


_PACKAGE_INDEX_SHA256 = (
    "ead184e5bd092d6b10770ebdd3688cf2b8f72b7e30a29d1957aa5e4d06b7cd33"
)
_PACKAGE_OPTIONS_SHA256 = (
    "bdac9a806043a81aff4310f2931d4431f1d8966e21437f150b15360f281f353d"
)
_REVIEW_TEMPLATES_SHA256 = (
    "62a98848db9fb44f0cc597f8b78755de3e981f1ffba6985853a29e9ed90088f8"
)
_INDEX_FIELDS = tuple(ingestion_design.INDEX_FIELDS)
_OPTION_FIELDS = tuple(ingestion_design.OPTION_FIELDS)
_TEMPLATE_FIELDS = tuple(ingestion_design.REVIEW_RECORD_FIELDS)
_WORKLIST_IDENTITY_FIELDS = (
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
_WORKLIST_HUMAN_FIELDS = (
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
_WORKLIST_FIELDS = _WORKLIST_IDENTITY_FIELDS + _WORKLIST_HUMAN_FIELDS
_COMPLETED_DECISIONS = (
    "select_admitted_candidate",
    "revise_atom_set_and_boundary",
    "quarantine",
)
_IDENTITY_TEMPLATE_FIELDS = (
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
)
_OPTION_IDENTITY_FIELDS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "source_proposal_record_sha256",
    "source_candidate_set_sha256",
)
_EMPTY_TEMPLATE_FIELDS = {
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
_MULTI_BOUNDARY_QUARANTINE_SAMPLES = frozenset(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(6, 11)
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_NONNEGATIVE_INT = re.compile(r"(?:0|[1-9][0-9]*)")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _meaningful(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and "\x00" not in value
    )


def _parse_csv(
    payload: bytes,
    *,
    expected_fields: Sequence[str],
    label: str,
) -> list[dict[str, str]]:
    if type(payload) is not bytes:
        raise ValueError(f"{label}: exact bytes required")
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{label}: UTF-8 BOM forbidden")
    if b"\x00" in payload:
        raise ValueError(f"{label}: NUL forbidden")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label}: valid UTF-8 required") from exc
    try:
        with io.StringIO(text, newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != tuple(expected_fields):
                raise ValueError(f"{label}: field inventory mismatch")
            rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"{label}: malformed CSV") from exc
    if any(
        None in row
        or tuple(row) != tuple(expected_fields)
        or any(type(value) is not str for value in row.values())
        for row in rows
    ):
        raise ValueError(f"{label}: malformed CSV row")
    return rows


def _parse_nonnegative_int(value: str, *, label: str) -> int:
    if type(value) is not str or _NONNEGATIVE_INT.fullmatch(value) is None:
        raise ValueError(f"{label}: canonical nonnegative integer required")
    return int(value)


def _parse_true(value: str, *, label: str) -> bool:
    if value != "true":
        raise ValueError(f"{label}: exact boolean true required")
    return True


def _parse_atom_ids(value: str, *, label: str, allow_empty: bool) -> list[str]:
    if type(value) is not str or "\x00" in value:
        raise ValueError(f"{label}: JSON list[str] required")
    try:
        result = json.loads(
            value,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant: {constant}")
            ),
        )
    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
        RecursionError,
        OverflowError,
    ) as exc:
        raise ValueError(f"{label}: JSON list[str] required") from exc
    if (
        type(result) is not list
        or any(not _meaningful(atom) for atom in result)
        or (not allow_empty and not result)
    ):
        raise ValueError(f"{label}: JSON list[str] contract invalid")
    try:
        ordered = sorted(result, key=lambda atom: atom.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label}: atom IDs must be valid UTF-8") from exc
    if result != ordered or len(result) != len(set(result)):
        raise ValueError(f"{label}: atom IDs must be UTF-8 sorted and unique")
    return result


def _require_sha(value: str, *, label: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label}: lowercase SHA256 required")


def _validate_frozen_package(
    *,
    package_index_csv: bytes,
    package_candidate_options_csv: bytes,
    review_record_templates_csv: bytes,
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    expected_hashes = (
        (package_index_csv, _PACKAGE_INDEX_SHA256, "package index"),
        (
            package_candidate_options_csv,
            _PACKAGE_OPTIONS_SHA256,
            "package candidate options",
        ),
        (
            review_record_templates_csv,
            _REVIEW_TEMPLATES_SHA256,
            "review record templates",
        ),
    )
    for payload, expected, label in expected_hashes:
        if _sha256(payload) != expected:
            raise ValueError(f"{label}: frozen source SHA256 mismatch")

    index_rows = _parse_csv(
        package_index_csv,
        expected_fields=_INDEX_FIELDS,
        label="package index",
    )
    option_rows = _parse_csv(
        package_candidate_options_csv,
        expected_fields=_OPTION_FIELDS,
        label="package candidate options",
    )
    template_rows = _parse_csv(
        review_record_templates_csv,
        expected_fields=_TEMPLATE_FIELDS,
        label="review record templates",
    )
    if len(index_rows) != 11:
        raise ValueError("package index: exactly 11 rows required")
    if len(option_rows) != 200:
        raise ValueError("package candidate options: exactly 200 rows required")
    if len(template_rows) != 11:
        raise ValueError("review record templates: exactly 11 rows required")

    expected_orders = [str(index) for index in range(11)]
    if [
        row["package_item_order_0based"] for row in index_rows
    ] != expected_orders:
        raise ValueError("package index: exact item order 0-10 required")
    samples = [row["sample_index_row_id"] for row in index_rows]
    if (
        any(not _meaningful(sample) for sample in samples)
        or len(samples) != len(set(samples))
    ):
        raise ValueError("package index: unique meaningful sample IDs required")
    if [row["sample_index_row_id"] for row in template_rows] != samples:
        raise ValueError("review templates: sample order/linkage mismatch")

    cursor = 0
    eligible_count = 0
    option_keys: set[tuple[str, str, str]] = set()
    for position, (index_row, template_row) in enumerate(
        zip(index_rows, template_rows)
    ):
        if _parse_nonnegative_int(
            index_row["package_item_order_0based"],
            label="package item order",
        ) != position:
            raise ValueError("package index: non-canonical item order")
        if (
            index_row["review_record_version"]
            != ingestion_design.REVIEW_RECORD_VERSION
            or template_row["review_record_version"]
            != ingestion_design.REVIEW_RECORD_VERSION
            or template_row["review_unit_type"]
            != ingestion_design.REVIEW_UNIT_TYPE
        ):
            raise ValueError("review templates: canonical constants mismatch")
        if any(
            index_row[field] != template_row[field]
            for field in _IDENTITY_TEMPLATE_FIELDS
        ):
            raise ValueError("package index/template identity mismatch")
        if any(
            template_row[field] != expected
            for field, expected in _EMPTY_TEMPLATE_FIELDS.items()
        ):
            raise ValueError("review template: frozen blank content mismatch")
        try:
            typed_template = ingestion_design.parse_review_record_csv(
                template_row
            )
            template_sha = ingestion_design.review_record_sha256(
                typed_template
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("review template: frozen content invalid") from exc
        if template_sha != index_row["unreviewed_template_payload_sha256"]:
            raise ValueError("review template: frozen content SHA256 mismatch")

        total = _parse_nonnegative_int(
            index_row["total_candidate_count"],
            label="package total candidate count",
        )
        admitted = _parse_nonnegative_int(
            index_row["admitted_candidate_count"],
            label="package admitted candidate count",
        )
        start = _parse_nonnegative_int(
            index_row["candidate_option_row_start_0based"],
            label="package option start",
        )
        end = _parse_nonnegative_int(
            index_row["candidate_option_row_end_exclusive"],
            label="package option end",
        )
        if (
            start != cursor
            or end - start != total
            or admitted > total
            or not 0 <= start <= end <= 200
        ):
            raise ValueError("package candidate option span/linkage mismatch")
        sample_options = option_rows[start:end]
        if [
            row["option_order_within_sample_0based"]
            for row in sample_options
        ] != [str(index) for index in range(total)]:
            raise ValueError("package option within-sample order mismatch")
        for source_position, option in enumerate(sample_options, start=start):
            if option["package_item_order_0based"] != str(source_position):
                raise ValueError("package option global order mismatch")
            if any(
                option[field] != index_row[field]
                for field in _OPTION_IDENTITY_FIELDS
            ):
                raise ValueError("package option sample identity mismatch")
            _parse_nonnegative_int(
                option["source_bridge_candidate_index_0based"],
                label="package option candidate index",
            )
            _require_sha(
                option["source_bridge_candidate_record_sha256"],
                label="package option candidate SHA256",
            )
            if option["candidate_admitted"] not in {"true", "false"}:
                raise ValueError("package option admitted flag invalid")
            if option["review_eligible"] not in {"true", "false"}:
                raise ValueError("package option eligibility flag invalid")
            if option["candidate_admitted"] != option["review_eligible"]:
                raise ValueError("package option admitted/eligible mismatch")
            _parse_atom_ids(
                option["warhead_side_atom_ids"],
                label="package option warhead atom IDs",
                allow_empty=False,
            )
            if any(
                not _meaningful(option[field])
                for field in (
                    "boundary_bond_id",
                    "warhead_attachment_atom_id",
                    "nonwarhead_boundary_atom_id",
                    "boundary_bond_order",
                )
            ):
                raise ValueError("package option boundary evidence invalid")
            key = (
                option["sample_index_row_id"],
                option["source_bridge_candidate_index_0based"],
                option["source_bridge_candidate_record_sha256"],
            )
            if key in option_keys:
                raise ValueError("package option selection key is not unique")
            option_keys.add(key)
            eligible_count += option["review_eligible"] == "true"
        cursor = end
    if cursor != 200 or eligible_count != 185:
        raise ValueError("package option coverage/eligibility count mismatch")
    return index_rows, option_rows, template_rows


def _validate_eligible_options(
    *,
    eligible_candidate_options_csv: bytes,
    option_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    eligible_rows = _parse_csv(
        eligible_candidate_options_csv,
        expected_fields=_OPTION_FIELDS,
        label="eligible candidate options",
    )
    if len(eligible_rows) != 185:
        raise ValueError("eligible candidate options: exactly 185 rows required")
    if any(row["review_eligible"] != "true" for row in eligible_rows):
        raise ValueError("eligible candidate options: every row must be eligible")
    expected = [
        dict(row) for row in option_rows if row["review_eligible"] == "true"
    ]
    if eligible_rows != expected:
        raise ValueError(
            "eligible candidate options: frozen ordered projection mismatch"
        )
    return eligible_rows


def _require_human_fields(row: Mapping[str, str]) -> None:
    for field in (
        "reviewer_id",
        "review_rationale",
        "reviewer_provenance_attestor_id",
        "submission_source_label",
    ):
        if not _meaningful(row[field]):
            raise ValueError(f"review worklist: {field} must be meaningful")
    if row["review_notes"] and not _meaningful(row["review_notes"]):
        raise ValueError("review worklist: nonempty review_notes must be meaningful")
    _parse_true(
        row["reviewer_provenance_attested"],
        label="reviewer provenance attestation",
    )
    _parse_true(row["review_completed"], label="review completion")


def _validate_revised_boundary(
    row: Mapping[str, str],
    atoms: Sequence[str],
) -> None:
    if row["selected_bridge_candidate_index_0based"] != "":
        raise ValueError("revise decision: selected candidate index must be empty")
    if row["selected_bridge_candidate_record_sha256"] != "":
        raise ValueError("revise decision: selected candidate SHA256 must be empty")
    boundary_fields = (
        "reviewed_warhead_attachment_atom_id",
        "reviewed_nonwarhead_boundary_atom_id",
        "reviewed_attachment_boundary_bond_order",
        "reviewed_boundary_bond_id",
    )
    if any(not _meaningful(row[field]) for field in boundary_fields):
        raise ValueError("revise decision: exact-one boundary evidence required")
    attachment = row["reviewed_warhead_attachment_atom_id"]
    nonwarhead = row["reviewed_nonwarhead_boundary_atom_id"]
    order = row["reviewed_attachment_boundary_bond_order"]
    if attachment not in atoms or nonwarhead in atoms or attachment == nonwarhead:
        raise ValueError("revise decision: boundary endpoint contract invalid")
    endpoints = sorted(
        (attachment, nonwarhead),
        key=lambda atom: atom.encode("utf-8"),
    )
    if row["reviewed_boundary_bond_id"] != (
        f"{endpoints[0]}|{endpoints[1]}|{order}"
    ):
        raise ValueError("revise decision: boundary bond ID contract invalid")


def _build_submission_items(
    *,
    worklist_rows: Sequence[Mapping[str, str]],
    index_rows: Sequence[Mapping[str, str]],
    option_rows: Sequence[Mapping[str, str]],
    eligible_rows: Sequence[Mapping[str, str]],
    template_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    if len(worklist_rows) != 11:
        raise ValueError("review worklist: exactly 11 rows required")
    expected_orders = [str(index) for index in range(11)]
    if [
        row["package_item_order_0based"] for row in worklist_rows
    ] != expected_orders:
        raise ValueError("review worklist: exact item order 0-10 required")
    samples = [row["sample_index_row_id"] for row in worklist_rows]
    expected_samples = [row["sample_index_row_id"] for row in index_rows]
    if samples != expected_samples or len(samples) != len(set(samples)):
        raise ValueError("review worklist: sample order/uniqueness mismatch")

    full_by_key: dict[tuple[str, str, str], list[Mapping[str, str]]] = {}
    eligible_by_key: dict[tuple[str, str, str], list[Mapping[str, str]]] = {}
    for source, destination in (
        (option_rows, full_by_key),
        (eligible_rows, eligible_by_key),
    ):
        for option in source:
            key = (
                option["sample_index_row_id"],
                option["source_bridge_candidate_index_0based"],
                option["source_bridge_candidate_record_sha256"],
            )
            destination.setdefault(key, []).append(option)

    items: list[dict[str, Any]] = []
    for position, (row, index_row, template) in enumerate(
        zip(worklist_rows, index_rows, template_rows)
    ):
        expected_identity = {
            field: (
                index_row[field]
                if field
                in {
                    "package_item_order_0based",
                    "candidate_option_row_start_0based",
                    "candidate_option_row_end_exclusive",
                }
                else template[field]
            )
            for field in _WORKLIST_IDENTITY_FIELDS
        }
        if any(row[field] != expected_identity[field] for field in expected_identity):
            raise ValueError(
                f"review worklist row {position}: frozen identity mismatch"
            )
        _require_human_fields(row)
        decision = row["review_decision"]
        if decision not in _COMPLETED_DECISIONS:
            raise ValueError(
                f"review worklist row {position}: completed decision required"
            )
        if (
            row["sample_index_row_id"] in _MULTI_BOUNDARY_QUARANTINE_SAMPLES
            and decision != "quarantine"
        ):
            raise ValueError(
                f"review worklist row {position}: Current11 multi-boundary "
                "sample must remain quarantine"
            )

        atoms = _parse_atom_ids(
            row["reviewed_warhead_atom_ids_json"],
            label=f"review worklist row {position} reviewed atom IDs",
            allow_empty=decision == "quarantine",
        )
        selected_index: int | None = None
        selected_sha = row["selected_bridge_candidate_record_sha256"]
        if decision == "select_admitted_candidate":
            selected_index = _parse_nonnegative_int(
                row["selected_bridge_candidate_index_0based"],
                label=f"review worklist row {position} selected candidate index",
            )
            _require_sha(
                selected_sha,
                label=f"review worklist row {position} selected candidate SHA256",
            )
            key = (
                row["sample_index_row_id"],
                row["selected_bridge_candidate_index_0based"],
                selected_sha,
            )
            full_matches = full_by_key.get(key, [])
            eligible_matches = eligible_by_key.get(key, [])
            if len(full_matches) != 1 or len(eligible_matches) != 1:
                raise ValueError(
                    f"review worklist row {position}: selected candidate "
                    "must match full and eligible options exactly once"
                )
            option = full_matches[0]
            if (
                option != eligible_matches[0]
                or option["candidate_admitted"] != "true"
                or option["review_eligible"] != "true"
            ):
                raise ValueError(
                    f"review worklist row {position}: selected option is not "
                    "admitted and review-eligible"
                )
            expected_atoms = _parse_atom_ids(
                option["warhead_side_atom_ids"],
                label=f"review worklist row {position} selected option atoms",
                allow_empty=False,
            )
            expected_review = (
                option["warhead_side_atom_ids"],
                expected_atoms,
                option["warhead_attachment_atom_id"],
                option["nonwarhead_boundary_atom_id"],
                option["boundary_bond_order"],
                option["boundary_bond_id"],
            )
            observed_review = (
                row["reviewed_warhead_atom_ids_json"],
                atoms,
                row["reviewed_warhead_attachment_atom_id"],
                row["reviewed_nonwarhead_boundary_atom_id"],
                row["reviewed_attachment_boundary_bond_order"],
                row["reviewed_boundary_bond_id"],
            )
            if observed_review != expected_review:
                raise ValueError(
                    f"review worklist row {position}: reviewed evidence does "
                    "not exactly match selected frozen option"
                )
        elif decision == "revise_atom_set_and_boundary":
            _validate_revised_boundary(row, atoms)
            selected_sha = ""
        else:
            if (
                row["selected_bridge_candidate_index_0based"] != ""
                or selected_sha != ""
                or row["reviewed_warhead_atom_ids_json"] != "[]"
                or atoms != []
                or any(
                    row[field] != ""
                    for field in (
                        "reviewed_warhead_attachment_atom_id",
                        "reviewed_nonwarhead_boundary_atom_id",
                        "reviewed_attachment_boundary_bond_order",
                        "reviewed_boundary_bond_id",
                    )
                )
            ):
                raise ValueError(
                    f"review worklist row {position}: quarantine evidence "
                    "must be exactly blank"
                )
            selected_sha = ""

        payload_values: dict[str, Any] = {
            "review_record_version": template["review_record_version"],
            "review_unit_type": template["review_unit_type"],
            "sample_index_row_id": row["sample_index_row_id"],
            "pdb_id": row["pdb_id"],
            "ligand_comp_id": row["ligand_comp_id"],
            "warhead_type_candidate_class_index_0based":
                _parse_nonnegative_int(
                    row["warhead_type_candidate_class_index_0based"],
                    label=f"review worklist row {position} class index",
                ),
            "warhead_type_candidate_class_id":
                row["warhead_type_candidate_class_id"],
            "reaction_family_id": row["reaction_family_id"],
            "warhead_rule_id": row["warhead_rule_id"],
            "source_proposal_record_sha256":
                row["source_proposal_record_sha256"],
            "source_assignment_record_sha256":
                row["source_assignment_record_sha256"],
            "source_candidate_set_sha256":
                row["source_candidate_set_sha256"],
            "total_candidate_count": _parse_nonnegative_int(
                row["total_candidate_count"],
                label=f"review worklist row {position} total candidate count",
            ),
            "admitted_candidate_count": _parse_nonnegative_int(
                row["admitted_candidate_count"],
                label=f"review worklist row {position} admitted candidate count",
            ),
            "review_decision": decision,
            "selected_bridge_candidate_index_0based": selected_index,
            "selected_bridge_candidate_record_sha256": selected_sha,
            "reviewed_warhead_atom_ids": atoms,
            "reviewed_warhead_attachment_atom_id":
                row["reviewed_warhead_attachment_atom_id"],
            "reviewed_nonwarhead_boundary_atom_id":
                row["reviewed_nonwarhead_boundary_atom_id"],
            "reviewed_attachment_boundary_bond_order":
                row["reviewed_attachment_boundary_bond_order"],
            "reviewed_boundary_bond_id": row["reviewed_boundary_bond_id"],
            "reviewer_id": row["reviewer_id"],
            "review_rationale": row["review_rationale"],
            "review_notes": row["review_notes"],
        }
        if tuple(payload_values) != tuple(adapter_design.REVIEW_PAYLOAD_FIELDS):
            raise AssertionError("review payload field order drifted")
        payload = {
            field: payload_values[field]
            for field in adapter_design.REVIEW_PAYLOAD_FIELDS
        }
        item_values: dict[str, Any] = {
            "submission_item_version": adapter_design.SUBMISSION_ITEM_VERSION,
            "review_record_payload": payload,
            "reviewer_provenance_attested": True,
            "reviewer_provenance_attestor_id":
                row["reviewer_provenance_attestor_id"],
            "submission_source_label": row["submission_source_label"],
        }
        if tuple(item_values) != tuple(adapter_design.SUBMISSION_ITEM_FIELDS):
            raise AssertionError("submission item field order drifted")
        items.append(item_values)
    return items


def _validate_adapter_response(
    response: object,
    *,
    expected_samples: Sequence[str],
) -> None:
    if type(response) is not dict:
        raise ValueError("compiled bundle rejected: adapter response invalid")
    try:
        results = response["adapter_result_records"]
        submissions = response["adapted_submissions"]
        adapter_passed = response["adapter_passed"]
        reason = response["reason"]
        response_invalid = (
            adapter_passed is not True
            or reason != "PASSED"
            or type(results) is not tuple
            or type(submissions) is not tuple
            or len(results) != len(expected_samples)
            or len(submissions) != len(expected_samples)
            or any(
                type(result) is not dict
                or result.get("outcome") != "adapted"
                or result.get("passed") is not True
                or result.get("reason") != "PASSED"
                for result in results
            )
            or [result["sample_index_row_id"] for result in results]
            != list(expected_samples)
            or [
                submission[0]["sample_index_row_id"]
                for submission in submissions
            ]
            != list(expected_samples)
        )
    except (IndexError, KeyError, TypeError) as exc:
        raise ValueError("compiled bundle rejected: adapter response invalid") from exc
    if response_invalid:
        raise ValueError("compiled bundle rejected by public adapter")


def compile_covapie_current11_real_human_review_submission_bundle_v1(
    *,
    review_worklist_csv: bytes,
    eligible_candidate_options_csv: bytes,
    package_index_csv: bytes,
    package_candidate_options_csv: bytes,
    review_record_templates_csv: bytes,
    submission_batch_id: str,
) -> bytes:
    """Compile exact Current11 CSV bytes into strict adapter-accepted JSON."""

    byte_inputs = (
        ("review_worklist_csv", review_worklist_csv),
        ("eligible_candidate_options_csv", eligible_candidate_options_csv),
        ("package_index_csv", package_index_csv),
        ("package_candidate_options_csv", package_candidate_options_csv),
        ("review_record_templates_csv", review_record_templates_csv),
    )
    if any(type(payload) is not bytes for _, payload in byte_inputs):
        raise ValueError("all CSV inputs must be exact bytes")
    if type(submission_batch_id) is not str or not _meaningful(
        submission_batch_id
    ):
        raise ValueError("submission_batch_id must be an exact meaningful str")
    snapshots = tuple(payload for _, payload in byte_inputs)

    index_rows, option_rows, template_rows = _validate_frozen_package(
        package_index_csv=package_index_csv,
        package_candidate_options_csv=package_candidate_options_csv,
        review_record_templates_csv=review_record_templates_csv,
    )
    eligible_rows = _validate_eligible_options(
        eligible_candidate_options_csv=eligible_candidate_options_csv,
        option_rows=option_rows,
    )
    worklist_rows = _parse_csv(
        review_worklist_csv,
        expected_fields=_WORKLIST_FIELDS,
        label="review worklist",
    )
    items = _build_submission_items(
        worklist_rows=worklist_rows,
        index_rows=index_rows,
        option_rows=option_rows,
        eligible_rows=eligible_rows,
        template_rows=template_rows,
    )
    bundle_values: dict[str, Any] = {
        "submission_bundle_version": adapter_design.SUBMISSION_BUNDLE_VERSION,
        "submission_batch_id": submission_batch_id,
        "submission_items": items,
    }
    if tuple(bundle_values) != tuple(adapter_design.SUBMISSION_BUNDLE_FIELDS):
        raise AssertionError("submission bundle field order drifted")
    try:
        compiled = json.dumps(
            bundle_values,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("compiled bundle is not strict UTF-8 JSON") from exc
    if (
        not compiled
        or len(compiled) > adapter_design.MAX_SOURCE_PAYLOAD_BYTES
        or compiled.startswith(b"\xef\xbb\xbf")
        or b"\x00" in compiled
    ):
        raise ValueError("compiled bundle byte contract invalid")

    response = (
        submission_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1(
            source_payload=compiled,
        )
    )
    _validate_adapter_response(
        response,
        expected_samples=[row["sample_index_row_id"] for row in worklist_rows],
    )
    if snapshots != tuple(payload for _, payload in byte_inputs):
        raise ValueError("compiler input mutation detected")
    return compiled
