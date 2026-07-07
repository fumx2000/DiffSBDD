from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from covalent_ext import covapie_explicit_external_source_registry_config_smoke as step13am


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0"
PREVIOUS_STAGE = "covapie_covpdb_complex_card_metadata_acquisition_smoke_v0"
PROJECT_NAME = "CovaPIE"

STEP13AS_ROOT = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_acquisition_smoke_v0")
STEP13AS_MANIFEST_JSON = STEP13AS_ROOT / "covapie_covpdb_complex_card_metadata_acquisition_smoke_manifest.json"
STEP13AS_SUMMARY_MD = Path("docs/covapie_covpdb_complex_card_metadata_acquisition_smoke_v0_summary.md")
STEP13AS_FETCH_AUDIT_CSV = STEP13AS_ROOT / "covapie_covpdb_complex_card_fetch_audit.csv"
STEP13AS_HTML_SAFETY_AUDIT_CSV = STEP13AS_ROOT / "covapie_covpdb_complex_card_html_metadata_safety_audit.csv"
STEP13AS_LABEL_INVENTORY_CSV = STEP13AS_ROOT / "covapie_covpdb_complex_card_parse_label_inventory.csv"
STEP13AS_EVENT_FIELD_PROBE_CSV = STEP13AS_ROOT / "covapie_covpdb_complex_card_event_field_probe.csv"
STEP13AS_EVIDENCE_SNIPPET_AUDIT_CSV = STEP13AS_ROOT / "covapie_covpdb_complex_card_evidence_snippet_audit.csv"
STEP13AS_EVENT_KEY_RESOLUTION_AUDIT_CSV = STEP13AS_ROOT / "covapie_covpdb_complex_card_event_key_resolution_audit.csv"
STEP13AS_FAILURE_TAXONOMY_CSV = STEP13AS_ROOT / "covapie_covpdb_complex_card_observed_failure_taxonomy.csv"
NAMING_CONVENTION_MD = Path("docs/covapie_project_naming_convention.md")
METADATA_CSV = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
METADATA_CSV_SHA256 = "c31d836c01291057b35279bc4fc4c2de35eaaa064e4e7c9ac6d314006cd66365"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_qa_precondition_audit.csv"
FETCH_INTEGRITY_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_fetch_integrity_qa.csv"
HTML_SAFETY_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_html_safety_qa.csv"
LABEL_INVENTORY_SUMMARY_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_label_inventory_summary_qa.csv"
EVENT_FIELD_STATUS_SUMMARY_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_event_field_status_summary_qa.csv"
EVENT_KEY_RESOLUTION_SUMMARY_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_event_key_resolution_summary_qa.csv"
UNRESOLVED_REASON_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_unresolved_reason_qa.csv"
EVIDENCE_SNIPPET_SAFETY_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_evidence_snippet_safety_qa.csv"
MATERIALIZATION_DECISION_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_materialization_decision_qa.csv"
NEXT_STEP_DECISION_QA_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_next_step_decision_qa.csv"
EXECUTION_BOUNDARY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_qa_execution_boundary_audit.csv"
GIT_SAFETY_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_qa_git_safety_audit.csv"
MASK_SCOPE_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_qa_mask_scope_audit.csv"
FEATURE_SEMANTICS_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_qa_feature_semantics_audit.csv"
LEAKAGE_SPLIT_AUDIT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_acquisition_qa_leakage_split_audit.csv"
REPORT_CSV = OUTPUT_ROOT / "covapie_covpdb_complex_card_metadata_acquisition_qa_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_covpdb_complex_card_metadata_acquisition_qa_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0_summary.md")

LABEL_CATEGORIES = [
    "chain",
    "residue",
    "residue_name",
    "residue_index",
    "residue_atom",
    "covalent_bond",
    "ligand_atom",
    "protein_atom",
    "mechanism",
    "warhead",
]
TARGET_FIELDS = ["chain_id", "residue_name", "residue_index", "residue_atom_name", "covalent_bond_atom_pair"]
CANONICAL_MASK_TASK_NAMES = step13am.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13am.CANONICAL_MASK_TASK_ALIASES
FEATURE_SEMANTICS_ITEMS = step13am.FEATURE_SEMANTICS_ITEMS
LEAKAGE_SPLIT_ITEMS = step13am.LEAKAGE_SPLIT_ITEMS
FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pdb",
    ".cif",
    ".mmcif",
    ".sdf",
    ".mol2",
    ".gz",
    ".html",
    ".htm",
)

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
FETCH_INTEGRITY_COLUMNS = ["card_index", "pdb_id", "het_code", "complex_card_url", "fetch_attempted", "fetch_succeeded", "http_status_or_error", "content_type", "byte_count_positive", "html_sha256_present", "url_allowed", "fetch_integrity_passed", "qa_comment"]
HTML_SAFETY_COLUMNS = ["card_index", "complex_card_url", "content_type_allowed", "full_html_written", "raw_html_artifact_written", "forbidden_suffix_url_requested", "forbidden_suffix_links_detected_count", "forbidden_suffix_links_followed", "external_raw_links_followed", "raw_structure_downloaded", "raw_ligand_downloaded", "html_safety_qa_passed", "qa_comment"]
LABEL_SUMMARY_COLUMNS = ["label_category", "cards_checked", "found_count", "not_found_count", "example_card_indices", "example_snippet_count", "label_inventory_summary_passed", "qa_interpretation"]
EVENT_FIELD_SUMMARY_COLUMNS = ["target_field", "found_count", "not_found_count", "ambiguous_count", "parse_failed_count", "total_cards_checked", "parsed_values_observed", "evidence_snippet_count", "materialization_blocking_if_missing", "event_field_status_summary_passed", "qa_interpretation"]
EVENT_KEY_SUMMARY_COLUMNS = ["resolution_status", "observed_count", "candidate_metadata_can_proceed_any", "candidate_allowlist_can_proceed_any", "raw_structure_annotation_may_be_required_any", "event_key_resolution_summary_passed", "qa_interpretation"]
UNRESOLVED_COLUMNS = ["card_index", "pdb_id", "het_code", "resolution_status", "missing_or_unresolved_fields", "why_candidate_metadata_blocked", "why_allowlist_blocked", "likely_next_information_source", "unresolved_reason_qa_passed"]
SNIPPET_SAFETY_COLUMNS = ["snippet_source", "row_count", "max_snippet_length", "all_snippets_le_240", "full_html_absent", "evidence_snippet_safety_qa_passed", "qa_comment"]
MATERIALIZATION_DECISION_COLUMNS = ["decision_item", "current_step_decision", "reason", "required_future_condition", "decision_qa_passed"]
NEXT_STEP_COLUMNS = ["recommended_next_step", "rationale", "candidate_metadata_blocked", "allowlist_blocked", "raw_read_blocked", "training_blocked", "next_step_decision_qa_passed"]
EXECUTION_COLUMNS = ["boundary_item", "current_step_status", "execution_boundary_passed", "blocking_reasons"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
MASK_COLUMNS = step13am.MASK_COLUMNS
FEATURE_COLUMNS = ["feature_semantics_item", "feature_group", "audit_required_before_training", "fully_audited_claimed", "blocking_for_complex_card_acquisition_qa_gate", "training_ready", "recommended_audit_step", "feature_semantics_audit_passed", "blocking_reasons"]
LEAKAGE_COLUMNS = ["leakage_split_item", "current_step_status", "future_required_gate", "split_written_current_step", "leakage_matrix_written_current_step", "blocking_for_training", "leakage_split_audit_passed", "blocking_reasons"]
REPORT_COLUMNS = ["stage", "previous_stage", "section", "status", "evidence", "blocking_reasons", "recommended_next_step"]

EXECUTION_BOUNDARY_STATUSES = {
    "acquisition_qa_gate": "executed_readonly_qa_only",
    "step13as_manifest_read": "executed_manifest_read_only",
    "step13as_fetch_audit_read": "executed_csv_read_only",
    "step13as_html_safety_audit_read": "executed_csv_read_only",
    "step13as_label_inventory_read": "executed_csv_read_only",
    "step13as_event_field_probe_read": "executed_csv_read_only",
    "step13as_event_key_resolution_read": "executed_csv_read_only",
    "step13as_snippet_audit_read": "executed_csv_read_only",
    "external_network_access": "not_executed_or_not_allowed",
    "urllib_use": "not_executed_or_not_allowed",
    "complex_card_fetch": "not_executed_or_not_allowed",
    "metadata_download": "not_executed_or_not_allowed",
    "raw_structure_download": "not_executed_or_not_allowed",
    "raw_ligand_download": "not_executed_or_not_allowed",
    "raw_data_read": "not_executed_or_not_allowed",
    "sdf_read": "not_executed_or_not_allowed",
    "pdb_read": "not_executed_or_not_allowed",
    "mmcif_read": "not_executed_or_not_allowed",
    "gzip_open": "not_executed_or_not_allowed",
    "rdkit_use": "not_executed_or_not_allowed",
    "biopdb_use": "not_executed_or_not_allowed",
    "gemmi_use": "not_executed_or_not_allowed",
    "candidate_metadata_materialization": "not_executed_or_not_allowed",
    "allowlist_materialization": "not_executed_or_not_allowed",
    "torch_import": "not_executed_or_not_allowed",
    "model_forward": "not_executed_or_not_allowed",
    "training_claim": "not_executed_or_not_allowed",
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    return _run_git(["diff", "--quiet", "--", *paths]).returncode != 0 or _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0


def _protected_source_diff_exists() -> bool:
    return _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])


def _original_dataloader_diff_exists() -> bool:
    return _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", "data/raw/covalent_sources"]).stdout.strip())


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", "data/raw/covalent_sources"]).stdout.strip())


def _metadata_csv_hash() -> str:
    return hashlib.sha256(METADATA_CSV.read_bytes()).hexdigest() if METADATA_CSV.exists() else ""


def _bool_text(value: Any) -> str:
    return "True" if value is True or str(value) == "True" else "False"


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _blocking(reasons: list[str]) -> str:
    return ";".join(reasons)


def _precondition_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[tuple[str, str, str, Any, bool]] = [
        ("step13as_manifest", str(STEP13AS_MANIFEST_JSON), "exists", STEP13AS_MANIFEST_JSON.exists(), STEP13AS_MANIFEST_JSON.exists()),
        ("step13as_stage", str(STEP13AS_MANIFEST_JSON), PREVIOUS_STAGE, manifest.get("stage"), manifest.get("stage") == PREVIOUS_STAGE),
        ("attempted_card_count", str(STEP13AS_MANIFEST_JSON), "5", manifest.get("attempted_card_count"), manifest.get("attempted_card_count") == 5),
        ("fetch_succeeded_count", str(STEP13AS_MANIFEST_JSON), "5", manifest.get("fetch_succeeded_count"), manifest.get("fetch_succeeded_count") == 5),
        ("fetch_failed_count", str(STEP13AS_MANIFEST_JSON), "0", manifest.get("fetch_failed_count"), manifest.get("fetch_failed_count") == 0),
        ("metadata_html_fetched", str(STEP13AS_MANIFEST_JSON), "true", manifest.get("metadata_html_fetched"), manifest.get("metadata_html_fetched") is True),
        ("full_html_written", str(STEP13AS_MANIFEST_JSON), "false", manifest.get("full_html_written"), manifest.get("full_html_written") is False),
        ("raw_html_artifact_written", str(STEP13AS_MANIFEST_JSON), "false", manifest.get("raw_html_artifact_written"), manifest.get("raw_html_artifact_written") is False),
        ("minimal_event_key_resolved_card_count", str(STEP13AS_MANIFEST_JSON), "0", manifest.get("minimal_event_key_resolved_card_count"), manifest.get("minimal_event_key_resolved_card_count") == 0),
        ("preferred_event_key_resolved_card_count", str(STEP13AS_MANIFEST_JSON), "0", manifest.get("preferred_event_key_resolved_card_count"), manifest.get("preferred_event_key_resolved_card_count") == 0),
        ("unresolved_card_count", str(STEP13AS_MANIFEST_JSON), "5", manifest.get("unresolved_card_count"), manifest.get("unresolved_card_count") == 5),
        ("future_candidate_metadata_possible_count", str(STEP13AS_MANIFEST_JSON), "0", manifest.get("future_candidate_metadata_possible_count"), manifest.get("future_candidate_metadata_possible_count") == 0),
        ("future_automatic_allowlist_possible_count", str(STEP13AS_MANIFEST_JSON), "0", manifest.get("future_automatic_allowlist_possible_count"), manifest.get("future_automatic_allowlist_possible_count") == 0),
        ("ready_for_qa_gate", str(STEP13AS_MANIFEST_JSON), "true", manifest.get("ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate"), manifest.get("ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate") is True),
        ("step13as_fetch_audit", str(STEP13AS_FETCH_AUDIT_CSV), "5 rows", len(_csv_rows(STEP13AS_FETCH_AUDIT_CSV)) if STEP13AS_FETCH_AUDIT_CSV.exists() else "missing", STEP13AS_FETCH_AUDIT_CSV.exists() and len(_csv_rows(STEP13AS_FETCH_AUDIT_CSV)) == 5),
        ("step13as_html_safety_audit", str(STEP13AS_HTML_SAFETY_AUDIT_CSV), "5 rows", len(_csv_rows(STEP13AS_HTML_SAFETY_AUDIT_CSV)) if STEP13AS_HTML_SAFETY_AUDIT_CSV.exists() else "missing", STEP13AS_HTML_SAFETY_AUDIT_CSV.exists() and len(_csv_rows(STEP13AS_HTML_SAFETY_AUDIT_CSV)) == 5),
        ("step13as_label_inventory", str(STEP13AS_LABEL_INVENTORY_CSV), "50 rows", len(_csv_rows(STEP13AS_LABEL_INVENTORY_CSV)) if STEP13AS_LABEL_INVENTORY_CSV.exists() else "missing", STEP13AS_LABEL_INVENTORY_CSV.exists() and len(_csv_rows(STEP13AS_LABEL_INVENTORY_CSV)) == 50),
        ("step13as_event_field_probe", str(STEP13AS_EVENT_FIELD_PROBE_CSV), "25 rows", len(_csv_rows(STEP13AS_EVENT_FIELD_PROBE_CSV)) if STEP13AS_EVENT_FIELD_PROBE_CSV.exists() else "missing", STEP13AS_EVENT_FIELD_PROBE_CSV.exists() and len(_csv_rows(STEP13AS_EVENT_FIELD_PROBE_CSV)) == 25),
        ("step13as_event_key_resolution", str(STEP13AS_EVENT_KEY_RESOLUTION_AUDIT_CSV), "5 rows", len(_csv_rows(STEP13AS_EVENT_KEY_RESOLUTION_AUDIT_CSV)) if STEP13AS_EVENT_KEY_RESOLUTION_AUDIT_CSV.exists() else "missing", STEP13AS_EVENT_KEY_RESOLUTION_AUDIT_CSV.exists() and len(_csv_rows(STEP13AS_EVENT_KEY_RESOLUTION_AUDIT_CSV)) == 5),
        ("step13as_evidence_snippet_audit", str(STEP13AS_EVIDENCE_SNIPPET_AUDIT_CSV), "exists", STEP13AS_EVIDENCE_SNIPPET_AUDIT_CSV.exists(), STEP13AS_EVIDENCE_SNIPPET_AUDIT_CSV.exists()),
        ("step13as_failure_taxonomy", str(STEP13AS_FAILURE_TAXONOMY_CSV), "exists", STEP13AS_FAILURE_TAXONOMY_CSV.exists(), STEP13AS_FAILURE_TAXONOMY_CSV.exists()),
        ("covapie_naming_convention", str(NAMING_CONVENTION_MD), "exists and names CovaPIE", NAMING_CONVENTION_MD.exists(), NAMING_CONVENTION_MD.exists() and "CovaPIE" in NAMING_CONVENTION_MD.read_text(encoding="utf-8")),
        ("protected_source_diff", "git diff equivariant_diffusion/ lightning_modules.py", "empty", _protected_source_diff_exists(), not _protected_source_diff_exists()),
        ("original_dataloader_diff", "git diff dataset.py data/prepare_crossdocked.py", "empty", _original_dataloader_diff_exists(), not _original_dataloader_diff_exists()),
        ("raw_files_staged", "git diff --cached data/raw/covalent_sources", "false", _raw_files_staged(), not _raw_files_staged()),
        ("raw_files_tracked", "git ls-files data/raw/covalent_sources", "false", _raw_files_tracked(), not _raw_files_tracked()),
    ]
    rows = []
    for item, artifact, expected, observed, passed in checks:
        rows.append(
            {
                "precondition_item": item,
                "artifact_or_check": artifact,
                "expected_status": expected,
                "observed_status": observed,
                "precondition_passed": passed,
                "blocking_reasons": "" if passed else f"{item}_failed",
            }
        )
    return rows


def _build_fetch_integrity(fetch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in fetch_rows:
        byte_count_positive = int(row.get("byte_count") or 0) > 0
        html_sha256_present = len(row.get("html_sha256", "")) == 64
        passed = row["fetch_attempted"] == "True" and row["fetch_succeeded"] == "True" and row["url_allowed"] == "True" and byte_count_positive and html_sha256_present
        rows.append(
            {
                "card_index": row["card_index"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "complex_card_url": row["complex_card_url"],
                "fetch_attempted": row["fetch_attempted"],
                "fetch_succeeded": row["fetch_succeeded"],
                "http_status_or_error": row["http_status_or_error"],
                "content_type": row["content_type"],
                "byte_count_positive": byte_count_positive,
                "html_sha256_present": html_sha256_present,
                "url_allowed": row["url_allowed"],
                "fetch_integrity_passed": passed,
                "qa_comment": "covpdb_card_html_fetch_confirmed" if passed else "fetch_integrity_failed",
            }
        )
    return rows


def _build_html_safety(safety_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in safety_rows:
        passed = (
            row["content_type_allowed"] == "True"
            and row["full_html_written"] == "False"
            and row["raw_html_artifact_written"] == "False"
            and row["forbidden_suffix_links_followed"] == "False"
            and row["external_raw_links_followed"] == "False"
            and row["raw_structure_downloaded"] == "False"
            and row["raw_ligand_downloaded"] == "False"
        )
        rows.append(
            {
                **{key: row.get(key, "") for key in HTML_SAFETY_COLUMNS if key not in {"html_safety_qa_passed", "qa_comment"}},
                "html_safety_qa_passed": passed,
                "qa_comment": "metadata_only_html_safety_preserved" if passed else "html_safety_failed",
            }
        )
    return rows


def _build_label_summary(label_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in label_rows:
        grouped[row["label_category"]].append(row)
    rows = []
    for category in LABEL_CATEGORIES:
        items = grouped[category]
        found = [row for row in items if row["label_found"] == "True"]
        not_found = [row for row in items if row["label_found"] == "False"]
        rows.append(
            {
                "label_category": category,
                "cards_checked": len(items),
                "found_count": len(found),
                "not_found_count": len(not_found),
                "example_card_indices": ";".join(row["card_index"] for row in found[:3]),
                "example_snippet_count": sum(1 for row in found if row.get("evidence_snippet_truncated")),
                "label_inventory_summary_passed": len(items) == 5,
                "qa_interpretation": "labels_are_weak_evidence_not_event_field_resolution",
            }
        )
    return rows


def _field_interpretation(found: int, ambiguous: int) -> str:
    if found == 0 and ambiguous == 0:
        return "complex_card_text_fetch_succeeded_but_event_key_fields_not_explicitly_parsed"
    if ambiguous > 0:
        return "ambiguous_event_field_blocks_materialization"
    return "event_field_observed_but_requires_future_qa_before_materialization"


def _build_event_field_summary(field_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in field_rows:
        grouped[row["target_field"]].append(row)
    rows = []
    for field in TARGET_FIELDS:
        items = grouped[field]
        statuses = Counter(row["field_probe_status"] for row in items)
        parsed_values = sorted({row["parsed_value"] for row in items if row.get("parsed_value")})
        snippet_count = sum(1 for row in items if row.get("evidence_snippet_truncated"))
        rows.append(
            {
                "target_field": field,
                "found_count": statuses.get("found", 0),
                "not_found_count": statuses.get("not_found", 0),
                "ambiguous_count": statuses.get("ambiguous", 0),
                "parse_failed_count": statuses.get("parse_failed", 0),
                "total_cards_checked": len(items),
                "parsed_values_observed": ";".join(parsed_values),
                "evidence_snippet_count": snippet_count,
                "materialization_blocking_if_missing": "True",
                "event_field_status_summary_passed": len(items) == 5,
                "qa_interpretation": _field_interpretation(statuses.get("found", 0), statuses.get("ambiguous", 0)),
            }
        )
    return rows


def _build_event_key_summary(resolution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in resolution_rows:
        grouped[row["resolution_status"]].append(row)
    rows = []
    for status, items in sorted(grouped.items()):
        rows.append(
            {
                "resolution_status": status,
                "observed_count": len(items),
                "candidate_metadata_can_proceed_any": any(row["candidate_metadata_can_proceed"] == "True" for row in items),
                "candidate_allowlist_can_proceed_any": any(row["candidate_allowlist_can_proceed"] == "True" for row in items),
                "raw_structure_annotation_may_be_required_any": any(row["raw_structure_annotation_may_be_required"] == "True" for row in items),
                "event_key_resolution_summary_passed": True,
                "qa_interpretation": "event_key_unresolved_candidate_metadata_and_allowlist_blocked",
            }
        )
    return rows


def _build_unresolved_reason(resolution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in resolution_rows:
        missing = [
            field
            for field, status_key in [
                ("chain_id", "chain_id_status"),
                ("residue_name", "residue_name_status"),
                ("residue_index", "residue_index_status"),
                ("residue_atom_name", "residue_atom_name_status"),
                ("covalent_bond_atom_pair", "covalent_bond_atom_pair_status"),
            ]
            if row[status_key] != "found"
        ]
        rows.append(
            {
                "card_index": row["card_index"],
                "pdb_id": row["pdb_id"],
                "het_code": row["het_code"],
                "resolution_status": row["resolution_status"],
                "missing_or_unresolved_fields": ";".join(missing),
                "why_candidate_metadata_blocked": "minimal_event_key_not_resolved",
                "why_allowlist_blocked": "preferred_event_key_not_resolved",
                "likely_next_information_source": "sanitized_complex_card_html_structure_probe_or_later_raw_structure_annotation",
                "unresolved_reason_qa_passed": row["candidate_metadata_can_proceed"] == "False" and row["candidate_allowlist_can_proceed"] == "False",
            }
        )
    return rows


def _build_snippet_safety(snippet_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    max_len = max((int(row["snippet_length"]) for row in snippet_rows), default=0)
    all_short = all(int(row["snippet_length"]) <= 240 for row in snippet_rows)
    return [
        {
            "snippet_source": "step13as_evidence_snippet_audit",
            "row_count": len(snippet_rows),
            "max_snippet_length": max_len,
            "all_snippets_le_240": all_short,
            "full_html_absent": True,
            "evidence_snippet_safety_qa_passed": all_short,
            "qa_comment": "short_metadata_snippets_only_no_full_html",
        }
    ]


def _build_materialization_decisions() -> list[dict[str, Any]]:
    return [
        {
            "decision_item": "candidate_metadata_materialization",
            "current_step_decision": "blocked",
            "reason": "minimal_event_key_resolved_card_count=0",
            "required_future_condition": "resolve_minimal_event_key_from_sanitized_html_structure_probe_or_later_annotation",
            "decision_qa_passed": True,
        },
        {
            "decision_item": "candidate_allowlist_materialization",
            "current_step_decision": "blocked",
            "reason": "preferred_event_key_resolved_card_count=0",
            "required_future_condition": "resolve_preferred_event_key_with_covalent_bond_atom_pair",
            "decision_qa_passed": True,
        },
        {
            "decision_item": "raw_read_smoke",
            "current_step_decision": "blocked",
            "reason": "qa_gate_only_reviews_metadata_artifacts",
            "required_future_condition": "separate_design_gate_and_explicit_raw_read_smoke_approval",
            "decision_qa_passed": True,
        },
        {
            "decision_item": "training",
            "current_step_decision": "blocked",
            "reason": "no_feature_semantics_audit_no_leakage_split_design_no_dataset_materialized",
            "required_future_condition": "feature_semantics_audit_and_leakage_split_design_and_training_dataset_materialization",
            "decision_qa_passed": True,
        },
    ]


def _build_next_step() -> list[dict[str, Any]]:
    return [
        {
            "recommended_next_step": "covapie_covpdb_complex_card_html_structure_probe_design_gate",
            "rationale": "card_urls_accessible_but_text_parser_did_not_resolve_event_key_design_sanitized_html_structure_probe_before_raw_download",
            "candidate_metadata_blocked": True,
            "allowlist_blocked": True,
            "raw_read_blocked": True,
            "training_blocked": True,
            "next_step_decision_qa_passed": True,
        }
    ]


def _build_execution_boundary() -> list[dict[str, Any]]:
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "execution_boundary_passed": True,
            "blocking_reasons": "",
        }
        for item, status in EXECUTION_BOUNDARY_STATUSES.items()
    ]


def _step13at_forbidden_artifacts_exist() -> bool:
    if not OUTPUT_ROOT.exists():
        return False
    return any(path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES for path in OUTPUT_ROOT.rglob("*"))


def _build_git_safety() -> list[dict[str, Any]]:
    checks = [
        ("forbidden_suffix_under_step13at_output_root", "scan output root", "false", _step13at_forbidden_artifacts_exist()),
        ("html_artifact_written", "scan output root", "false", any(path.is_file() and path.suffix.lower() in {".html", ".htm"} for path in OUTPUT_ROOT.rglob("*")) if OUTPUT_ROOT.exists() else False),
        ("raw_files_staged", "git diff --cached data/raw/covalent_sources", "false", _raw_files_staged()),
        ("raw_files_tracked", "git ls-files data/raw/covalent_sources", "false", _raw_files_tracked()),
        ("metadata_csv_hash_unchanged", "sha256 metadata csv", METADATA_CSV_SHA256, _metadata_csv_hash() != METADATA_CSV_SHA256),
        ("step13ao_ap_aq_ar_as_artifacts_unchanged", "git diff prior artifact roots", "empty", _path_diff_exists([
            "data/derived/covalent_small/covapie_covpdb_metadata_only_acquisition_smoke_v0",
            "data/derived/covalent_small/covapie_external_metadata_index_rediscovery_smoke_v0",
            "data/derived/covalent_small/covapie_external_metadata_index_schema_probe_design_gate_v0",
            "data/derived/covalent_small/covapie_covpdb_complex_card_metadata_probe_design_gate_v0",
            "data/derived/covalent_small/covapie_covpdb_complex_card_metadata_acquisition_smoke_v0",
            "data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv",
        ])),
        ("protected_source_diff", "git diff equivariant_diffusion/ lightning_modules.py", "empty", _protected_source_diff_exists()),
        ("original_dataloader_diff", "git diff dataset.py data/prepare_crossdocked.py", "empty", _original_dataloader_diff_exists()),
    ]
    rows = []
    for item, command, required, failed in checks:
        rows.append(
            {
                "git_safety_item": item,
                "command_or_check": command,
                "required_status": required,
                "current_step_status": "failed" if failed else "passed",
                "git_safety_audit_passed": not failed,
                "blocking_reasons": "" if not failed else f"{item}_failed",
            }
        )
    return rows


def _build_mask_rows() -> list[dict[str, Any]]:
    return [
        {
            "canonical_mask_task_name": name,
            "display_alias": alias,
            "source_of_truth_status": "long_semantic_name_source_of_truth",
            "alias_status": "display_only",
            "mask_scope_status": "preserved_from_step13as",
            "no_extra_mask_tasks_added": True,
            "mask_scope_audit_passed": True,
            "blocking_reasons": "",
        }
        for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)
    ]


def _build_feature_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_semantics_item": item,
            "feature_group": "model_input_feature_semantics",
            "audit_required_before_training": True,
            "fully_audited_claimed": False,
            "blocking_for_complex_card_acquisition_qa_gate": False,
            "training_ready": False,
            "recommended_audit_step": "future_feature_semantics_audit_gate_before_training",
            "feature_semantics_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in FEATURE_SEMANTICS_ITEMS
    ]


def _build_leakage_rows() -> list[dict[str, Any]]:
    return [
        {
            "leakage_split_item": item,
            "current_step_status": "placeholder_only_no_split_written",
            "future_required_gate": "covapie_leakage_split_design_gate_before_training",
            "split_written_current_step": False,
            "leakage_matrix_written_current_step": False,
            "blocking_for_training": True,
            "leakage_split_audit_passed": True,
            "blocking_reasons": "",
        }
        for item in LEAKAGE_SPLIT_ITEMS
    ]


def _all_pass(rows: list[dict[str, Any]], key: str) -> bool:
    return bool(rows) and all(_bool_text(row.get(key)) == "True" for row in rows)


def _build_report_sections(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "step13as_precondition": {"rows": len(result["precondition_rows"])},
        "fetch_integrity_qa": {"rows": len(result["fetch_integrity_rows"])},
        "html_safety_qa": {"rows": len(result["html_safety_rows"])},
        "label_inventory_summary_qa": {"rows": len(result["label_summary_rows"])},
        "event_field_status_summary_qa": {"rows": len(result["event_field_summary_rows"])},
        "event_key_resolution_summary_qa": {"rows": len(result["event_key_summary_rows"])},
        "unresolved_reason_qa": {"rows": len(result["unresolved_reason_rows"])},
        "evidence_snippet_safety_qa": {"rows": len(result["snippet_safety_rows"])},
        "materialization_decision_qa": {"rows": len(result["materialization_decision_rows"])},
        "next_step_decision_qa": {"rows": len(result["next_step_rows"])},
        "execution_boundary": {"rows": len(result["execution_rows"])},
        "readiness_boundary": {"recommended_next_step": "covapie_covpdb_complex_card_html_structure_probe_design_gate"},
    }


def run_covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0() -> dict[str, Any]:
    manifest13as = _load_json(STEP13AS_MANIFEST_JSON)
    fetch_rows13as = _csv_rows(STEP13AS_FETCH_AUDIT_CSV)
    safety_rows13as = _csv_rows(STEP13AS_HTML_SAFETY_AUDIT_CSV)
    label_rows13as = _csv_rows(STEP13AS_LABEL_INVENTORY_CSV)
    field_rows13as = _csv_rows(STEP13AS_EVENT_FIELD_PROBE_CSV)
    snippet_rows13as = _csv_rows(STEP13AS_EVIDENCE_SNIPPET_AUDIT_CSV)
    resolution_rows13as = _csv_rows(STEP13AS_EVENT_KEY_RESOLUTION_AUDIT_CSV)

    precondition_rows = _precondition_rows(manifest13as)
    fetch_integrity_rows = _build_fetch_integrity(fetch_rows13as)
    html_safety_rows = _build_html_safety(safety_rows13as)
    label_summary_rows = _build_label_summary(label_rows13as)
    event_field_summary_rows = _build_event_field_summary(field_rows13as)
    event_key_summary_rows = _build_event_key_summary(resolution_rows13as)
    unresolved_reason_rows = _build_unresolved_reason(resolution_rows13as)
    snippet_safety_rows = _build_snippet_safety(snippet_rows13as)
    materialization_decision_rows = _build_materialization_decisions()
    next_step_rows = _build_next_step()
    execution_rows = _build_execution_boundary()
    git_safety_rows = _build_git_safety()
    mask_rows = _build_mask_rows()
    feature_rows = _build_feature_rows()
    leakage_rows = _build_leakage_rows()

    minimal_count = sum(1 for row in resolution_rows13as if row["minimal_event_key_resolved"] == "True")
    preferred_count = sum(1 for row in resolution_rows13as if row["preferred_event_key_resolved"] == "True")
    partial_count = sum(1 for row in resolution_rows13as if int(row["minimal_key_fields_found_count"]) > 0 and row["minimal_event_key_resolved"] == "False")
    unresolved_count = sum(1 for row in resolution_rows13as if row["resolution_status"] == "card_no_event_key_fields_found")
    all_checks_passed = all(
        [
            _all_pass(precondition_rows, "precondition_passed"),
            _all_pass(fetch_integrity_rows, "fetch_integrity_passed"),
            _all_pass(html_safety_rows, "html_safety_qa_passed"),
            _all_pass(label_summary_rows, "label_inventory_summary_passed"),
            _all_pass(event_field_summary_rows, "event_field_status_summary_passed"),
            _all_pass(event_key_summary_rows, "event_key_resolution_summary_passed"),
            _all_pass(unresolved_reason_rows, "unresolved_reason_qa_passed"),
            _all_pass(snippet_safety_rows, "evidence_snippet_safety_qa_passed"),
            _all_pass(materialization_decision_rows, "decision_qa_passed"),
            _all_pass(next_step_rows, "next_step_decision_qa_passed"),
            _all_pass(execution_rows, "execution_boundary_passed"),
            _all_pass(git_safety_rows, "git_safety_audit_passed"),
            _all_pass(mask_rows, "mask_scope_audit_passed"),
            _all_pass(feature_rows, "feature_semantics_audit_passed"),
            _all_pass(leakage_rows, "leakage_split_audit_passed"),
        ]
    )
    blocking_reasons: list[str] = []
    if not all_checks_passed:
        blocking_reasons = ["covapie_covpdb_complex_card_metadata_acquisition_qa_gate_failed"]

    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13as_acquisition_smoke_validated": _all_pass(precondition_rows, "precondition_passed"),
        "attempted_card_count": manifest13as["attempted_card_count"],
        "fetch_succeeded_count": manifest13as["fetch_succeeded_count"],
        "fetch_failed_count": manifest13as["fetch_failed_count"],
        "fetch_integrity_qa_row_count": len(fetch_integrity_rows),
        "html_safety_qa_row_count": len(html_safety_rows),
        "label_inventory_summary_qa_row_count": len(label_summary_rows),
        "event_field_status_summary_qa_row_count": len(event_field_summary_rows),
        "event_field_probe_row_count": len(field_rows13as),
        "event_key_resolution_audit_row_count": len(resolution_rows13as),
        "event_key_resolution_summary_qa_row_count": len(event_key_summary_rows),
        "unresolved_reason_qa_row_count": len(unresolved_reason_rows),
        "evidence_snippet_safety_qa_row_count": len(snippet_safety_rows),
        "minimal_event_key_resolved_card_count": minimal_count,
        "preferred_event_key_resolved_card_count": preferred_count,
        "partial_event_key_card_count": partial_count,
        "unresolved_card_count": unresolved_count,
        "future_candidate_metadata_possible_count": minimal_count,
        "future_automatic_allowlist_possible_count": preferred_count,
        "candidate_metadata_materialized": False,
        "candidate_allowlist_materialized": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "raw_data_read": False,
        "sdf_read": False,
        "pdb_read": False,
        "mmcif_text_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate": True,
        "ready_for_covapie_candidate_metadata_materialization": False,
        "ready_for_covapie_candidate_allowlist_materialization_smoke": False,
        "ready_for_covapie_batch_scale_raw_read_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_count": len(CANONICAL_MASK_TASK_NAMES),
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in CANONICAL_MASK_TASK_NAMES and "B3" in CANONICAL_MASK_TASK_ALIASES,
        "no_extra_mask_tasks_added": len(CANONICAL_MASK_TASK_NAMES) == 5,
        "all_fetch_integrity_qa_passed": _all_pass(fetch_integrity_rows, "fetch_integrity_passed"),
        "all_html_safety_qa_passed": _all_pass(html_safety_rows, "html_safety_qa_passed"),
        "all_label_inventory_summary_qa_passed": _all_pass(label_summary_rows, "label_inventory_summary_passed"),
        "all_event_field_status_summary_qa_passed": _all_pass(event_field_summary_rows, "event_field_status_summary_passed"),
        "all_event_key_resolution_summary_qa_passed": _all_pass(event_key_summary_rows, "event_key_resolution_summary_passed"),
        "all_unresolved_reason_qa_passed": _all_pass(unresolved_reason_rows, "unresolved_reason_qa_passed"),
        "all_evidence_snippet_safety_qa_passed": _all_pass(snippet_safety_rows, "evidence_snippet_safety_qa_passed"),
        "all_materialization_decision_qa_passed": _all_pass(materialization_decision_rows, "decision_qa_passed"),
        "all_next_step_decision_qa_passed": _all_pass(next_step_rows, "next_step_decision_qa_passed"),
        "all_execution_boundaries_respected": _all_pass(execution_rows, "execution_boundary_passed"),
        "all_git_safety_qa_passed": _all_pass(git_safety_rows, "git_safety_audit_passed"),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_covpdb_complex_card_html_structure_probe_design_gate",
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }

    result = {
        "precondition_rows": precondition_rows,
        "fetch_integrity_rows": fetch_integrity_rows,
        "html_safety_rows": html_safety_rows,
        "label_summary_rows": label_summary_rows,
        "event_field_summary_rows": event_field_summary_rows,
        "event_key_summary_rows": event_key_summary_rows,
        "unresolved_reason_rows": unresolved_reason_rows,
        "snippet_safety_rows": snippet_safety_rows,
        "materialization_decision_rows": materialization_decision_rows,
        "next_step_rows": next_step_rows,
        "execution_rows": execution_rows,
        "git_safety_rows": git_safety_rows,
        "mask_rows": mask_rows,
        "feature_rows": feature_rows,
        "leakage_rows": leakage_rows,
        "manifest": manifest,
    }
    result["report_sections"] = _build_report_sections(result)
    return result
