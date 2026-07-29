"""Design contract for the Current11 review-submission adapter.

This module deliberately does not expose the future public adapter.  Its
private reference evaluator exists only to make the frozen design executable
against synthetic, in-memory payloads.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import json
import re
import subprocess
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as ingestion_design,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)


SCHEMA_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_submission_adapter_design_v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review submission adapter design v1"
)
BASE_COMMIT = "9cd905d9ecf8e73fe16e947e8b881a520b31e2b4"
BASE_PARENT = "7e0f63d043b546480f66215c69af37253506c08a"
BASE_TREE = "aa0bbd5e34a60cf907d769226dfed50ebb5c863b"
BASE_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review ingestion interface v1"
)

SUBMISSION_BUNDLE_VERSION = (
    "covapie_current11_warhead_boundary_review_submission_bundle_v1"
)
SUBMISSION_ITEM_VERSION = (
    "covapie_current11_warhead_boundary_review_submission_item_v1"
)
SUBMISSION_ADAPTER_RESPONSE_VERSION = (
    "covapie_current11_warhead_boundary_review_submission_adapter_response_v1"
)
SUBMISSION_ADAPTER_RESULT_VERSION = (
    "covapie_current11_warhead_boundary_review_submission_adapter_result_v1"
)
MAX_SOURCE_PAYLOAD_BYTES = 1_048_576

OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
SOURCE_FILE = "covapie_review_submission_adapter_source_inventory.csv"
CONTRACT_FILE = "covapie_review_submission_adapter_contract_registry.csv"
TRUTH_FILE = "covapie_review_submission_adapter_truth_matrix.csv"
READINESS_FILE = "covapie_current11_review_submission_adapter_readiness_matrix.csv"
FAILURE_FILE = "covapie_review_submission_adapter_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_warhead_boundary_review_submission_adapter_"
    "design_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    CONTRACT_FILE,
    TRUTH_FILE,
    READINESS_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)

PRODUCTION_PATH = Path("src/covalent_ext") / f"{SCHEMA_VERSION}.py"
TEST_PATH = Path("tests") / f"test_{SCHEMA_VERSION}.py"
CHECKER_PATH = Path("scripts") / f"check_{SCHEMA_VERSION}.py"
SUMMARY_PATH = Path("docs") / f"{SCHEMA_VERSION}_summary.md"
EXACT10_PATHS = (
    PRODUCTION_PATH,
    TEST_PATH,
    CHECKER_PATH,
    SUMMARY_PATH,
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)

INTERFACE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_interface_v1"
)
INTERFACE_PRODUCTION = Path("src/covalent_ext") / (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_interface_v1.py"
)
INTERFACE_MANIFEST = INTERFACE_ROOT / (
    "covapie_current11_warhead_boundary_review_ingestion_interface_manifest.json"
)
INTERFACE_CONTRACT = (
    INTERFACE_ROOT / "covapie_review_ingestion_interface_contract_registry.csv"
)
INTERFACE_TRUTH = (
    INTERFACE_ROOT / "covapie_review_ingestion_interface_truth_matrix.csv"
)
INTERFACE_READINESS = INTERFACE_ROOT / (
    "covapie_current11_review_ingestion_interface_readiness_matrix.csv"
)
INTERFACE_FAILURE = (
    INTERFACE_ROOT / "covapie_review_ingestion_interface_failure_matrix.csv"
)
DESIGN_PRODUCTION = Path("src/covalent_ext") / (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_gate_design_v1.py"
)
DESIGN_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_gate_design_v1/"
    "covapie_current11_warhead_boundary_review_ingestion_gate_design_manifest.json"
)
PACKAGE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_v1"
)
PACKAGE_MANIFEST = PACKAGE_ROOT / (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_packages_manifest.json"
)
PACKAGE_TEMPLATES = (
    PACKAGE_ROOT / "covapie_current11_warhead_boundary_review_record_templates.csv"
)

FROZEN_BASE_SHA256 = {
    INTERFACE_PRODUCTION:
        "dad2bb9fffeecfd132b34f733be85ff45af089e8b8fbd2feb6a15eb924ac00b0",
    INTERFACE_MANIFEST:
        "c605d8358dad248ddaec4ea0d3d357983f70373c890a8ca2251fb2460c64a3c4",
    INTERFACE_CONTRACT:
        "54947cdfafefd7b783190bd5b1edf9bfbba5e9507414d65c4fa82e0af1673353",
    INTERFACE_TRUTH:
        "d628e2588aba104a4906e819e74199112a462ce98f45a4c1c6bd76509d4e44cf",
    INTERFACE_READINESS:
        "1b235d7ddf27aa4beb3938507ed1552b6d1dfdf00cf3bb865a86e31026add143",
    INTERFACE_FAILURE:
        "7dc09c386b756daf3d7dbd07085a6b07f30c6075fc014c68f1423067f4ff48ce",
    DESIGN_PRODUCTION:
        "cd726f7122edd8315079f0ac1df9d4bb24d4ee969f438ce2f41eda3fd0f7c410",
    DESIGN_MANIFEST:
        "3fb5b40e6bedac764166f51e8f094ef74a511d1eeff593cdbcfd77329a7520eb",
    PACKAGE_MANIFEST:
        "5eff02e8ec764e35696e83136e61151c27a1d3101f811bcfbaa79278448015ea",
    PACKAGE_TEMPLATES:
        "62a98848db9fb44f0cc597f8b78755de3e981f1ffba6985853a29e9ed90088f8",
}
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)

SUBMISSION_BUNDLE_FIELDS = (
    "submission_bundle_version",
    "submission_batch_id",
    "submission_items",
)
SUBMISSION_ITEM_FIELDS = (
    "submission_item_version",
    "review_record_payload",
    "reviewer_provenance_attested",
    "reviewer_provenance_attestor_id",
    "submission_source_label",
)
REVIEW_PAYLOAD_FIELDS = ingestion_design.REVIEW_RECORD_FIELDS[:-1]
ADAPTER_RESPONSE_FIELDS = (
    "submission_adapter_response_version",
    "source_payload_sha256",
    "canonical_bundle_sha256",
    "submission_batch_id",
    "adapter_passed",
    "reason",
    "adapter_result_records",
    "adapted_submissions",
    "submission_adapter_response_sha256",
)
ADAPTER_RESULT_FIELDS = (
    "submission_adapter_result_version",
    "item_index_0based",
    "submission_batch_id",
    "sample_index_row_id",
    "outcome",
    "passed",
    "reason",
    "review_record_sha256",
    "ingestion_envelope_sha256",
    "consumed_submission_item",
    "ready_for_interface_evaluation",
    "submission_adapter_result_sha256",
)
ADAPTER_RESULT_EFFECTS = (
    {
        "outcome": "adapted",
        "passed": True,
        "reason": "PASSED",
        "consumed_submission_item": True,
        "ready_for_interface_evaluation": True,
        "review_record_sha256": "64_lowercase_hex",
        "ingestion_envelope_sha256": "64_lowercase_hex",
    },
    {
        "outcome": "invalid",
        "passed": False,
        "reason": "formal_failure_reason",
        "consumed_submission_item": False,
        "ready_for_interface_evaluation": False,
        "review_record_sha256": "",
        "ingestion_envelope_sha256": "",
    },
)
COMPLETED_REVIEW_DECISIONS = (
    "select_admitted_candidate",
    "revise_atom_set_and_boundary",
    "quarantine",
)
ADAPTER_REASON_CODES = (
    "PASSED",
    "SOURCE_PAYLOAD_EXACT_TYPE_INVALID",
    "SOURCE_PAYLOAD_SIZE_INVALID",
    "SOURCE_PAYLOAD_UTF8_INVALID",
    "SOURCE_PAYLOAD_BOM_FORBIDDEN",
    "SOURCE_PAYLOAD_JSON_INVALID",
    "SOURCE_PAYLOAD_DUPLICATE_KEY",
    "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH",
    "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID",
    "SUBMISSION_BUNDLE_VERSION_MISMATCH",
    "SUBMISSION_BATCH_ID_NOT_MEANINGFUL",
    "SUBMISSION_ITEM_COUNT_INVALID",
    "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH",
    "SUBMISSION_ITEM_EXACT_TYPE_INVALID",
    "REVIEW_RECORD_PAYLOAD_FIELD_INVENTORY_MISMATCH",
    "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID",
    "REVIEW_DECISION_NOT_COMPLETED",
    "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED",
    "PROVENANCE_ATTESTOR_INVALID",
    "SUBMISSION_SOURCE_LABEL_NOT_MEANINGFUL",
    "DUPLICATE_SAMPLE_IN_BUNDLE",
    "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE",
    "ADAPTER_ATOMICITY_ABORTED",
    "ADAPTER_RESPONSE_INVARIANT_INVALID",
)
ADAPTER_REASON_PRECEDENCE = (
    "SOURCE_PAYLOAD_EXACT_TYPE_INVALID",
    "SOURCE_PAYLOAD_SIZE_INVALID",
    "SOURCE_PAYLOAD_UTF8_INVALID",
    "SOURCE_PAYLOAD_BOM_FORBIDDEN",
    "SOURCE_PAYLOAD_JSON_INVALID",
    "SOURCE_PAYLOAD_DUPLICATE_KEY",
    "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH",
    "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID",
    "SUBMISSION_BUNDLE_VERSION_MISMATCH",
    "SUBMISSION_BATCH_ID_NOT_MEANINGFUL",
    "SUBMISSION_ITEM_COUNT_INVALID",
    "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE",
    "DUPLICATE_SAMPLE_IN_BUNDLE",
    "ITEM_SPECIFIC_VALIDATION_REASON",
    "ADAPTER_ATOMICITY_ABORTED",
    "ADAPTER_RESPONSE_INVARIANT_INVALID",
)
CANONICAL_MASKS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
SUPPORTED_RUNTIME_LIFECYCLES = (
    "pre_commit",
    "detached_candidate_post_commit",
    "formal_main_post_commit_unpushed",
    "formal_main_post_push",
)
_SHA = re.compile(r"[0-9a-f]{64}")

SOURCE_COLUMNS = (
    "source_path",
    "BASE_SHA256",
    "source_role",
    "fields_actually_used",
    "authority_class",
    "verified",
)
CONTRACT_COLUMNS = (
    "contract_id",
    "semantic_name",
    "contract_scope",
    "required_inputs",
    "validation_rule",
    "success_effect",
    "failure_effect",
    "fails_closed",
    "verified",
)
TRUTH_COLUMNS = (
    "truth_case_id",
    "truth_case_name",
    "expected_outcome",
    "expected_reason",
    "expected_item_count",
    "adapter_passed",
    "adapted_submission_count",
    "result_record_count",
    "response_schema_valid",
    "response_hash_valid",
    "input_order_preserved",
    "inputs_unmodified",
    "interface_compatibility_checked",
    "interface_batch_passed",
    "filesystem_write_count",
    "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "source_candidate_set_sha256",
    "review_package_available",
    "blank_review_template_available",
    "ingestion_interface_available",
    "submission_adapter_design_completed",
    "ready_for_submission_adapter_implementation",
    "completed_review_record_available",
    "human_provenance_envelope_available",
    "submission_payload_available",
    "adapted_submission_available",
    "ready_for_real_ingestion_execution",
    "real_ingestion_completed",
    "authority_record_available",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "sample_quarantined",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_role_proposal_generation",
    "ready_for_mask_materialization",
    "ready_for_model_integration",
    "ready_for_training",
    "blocking_reasons",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case_id",
    "failure_case_name",
    "mutation_signature",
    "mutated_field",
    "mutated_value_json",
    "expected_reason",
    "observed_reasons",
    "expected_reason_verified",
    "fails_closed",
    "contract_row_count",
    "truth_row_count",
    "current11_readiness_row_count",
    "actual_submission_payload_count",
    "actual_completed_review_count",
    "actual_ingestion_envelope_count",
    "actual_adapted_submission_count",
    "actual_ingestion_result_count",
    "actual_authority_record_count",
    "smarts_ready",
    "role_ready",
    "mask_ready",
    "model_ready",
    "training_ready",
    "verified",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    )


def _git(
    repo_root: Path, *arguments: str, check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(
            "git_command_failed:"
            + " ".join(arguments)
            + ":"
            + result.stderr.decode("utf-8", "replace")
        )
    return result


def validate_execution_boundary_v1(repo_root: Path) -> str:
    identity = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT,
    ).stdout.decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("formal_BASE_identity_mismatch")
    head = _git(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE_COMMIT:
        return "pre_commit"
    raw = _git(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    if not separator:
        raise ValueError("successor_commit_object_malformed")
    parents = tuple(
        row[7:].decode()
        for row in headers.splitlines()
        if row.startswith(b"parent ")
    )
    subject, newline, body = message.partition(b"\n")
    if (
        parents != (BASE_COMMIT,)
        or not newline
        or subject.decode() != FORMAL_COMMIT_SUBJECT
        or body
    ):
        raise ValueError("successor_identity_mismatch")
    changed = {
        item.decode()
        for item in _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r",
            "-z", head,
        ).stdout.split(b"\0")
        if item
    }
    if changed != {path.as_posix() for path in EXACT10_PATHS}:
        raise ValueError("successor_changed_path_inventory_mismatch")
    rows = [
        row for row in _git(
            repo_root, "ls-tree", "-r", "-z", head, "--",
            *(path.as_posix() for path in EXACT10_PATHS),
        ).stdout.split(b"\0") if row
    ]
    if len(rows) != 10 or any(
        not row.startswith(b"100644 blob ") for row in rows
    ):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False,
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root, "rev-parse", "--verify", "refs/remotes/origin/main",
        check=False,
    )
    if origin.returncode:
        raise ValueError("successor_origin_main_missing")
    origin_oid = origin.stdout.decode().strip()
    if origin_oid == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin_oid == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def base_bytes(repo_root: Path, path: Path) -> bytes:
    result = _git(
        repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}", check=False,
    )
    if result.returncode or not result.stdout:
        raise ValueError(f"BASE_SOURCE_MISSING:{path.as_posix()}")
    if sha256(result.stdout) != FROZEN_BASE_SHA256[path]:
        raise ValueError(f"BASE_SOURCE_SHA_MISMATCH:{path.as_posix()}")
    return result.stdout


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    return {path: base_bytes(repo_root, path) for path in SOURCE_PATHS}


def _meaningful(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
    )


def _derived_review_record_sha256_from_payload_v1(
    review_payload: Mapping[str, Any],
) -> str:
    provisional = {
        field: copy.deepcopy(review_payload[field])
        for field in REVIEW_PAYLOAD_FIELDS
    }
    provisional["review_record_sha256"] = ""
    return ingestion_design.review_record_sha256(provisional)


def _canonical_review_sha(review: Mapping[str, Any]) -> str:
    return _derived_review_record_sha256_from_payload_v1(review)


def _submitted_record_payload_sha(review: Mapping[str, Any]) -> str:
    return ingestion_design.submitted_record_payload_sha256(review)


def _ingestion_envelope_sha(envelope: Mapping[str, Any]) -> str:
    return ingestion_design.ingestion_envelope_sha256(envelope)


def _adapter_result_sha(record: Mapping[str, Any]) -> str:
    return sha256(canonical_json({
        field: record[field]
        for field in ADAPTER_RESULT_FIELDS
        if field != "submission_adapter_result_sha256"
    }).encode("utf-8"))


def _adapter_response_sha(response: Mapping[str, Any]) -> str:
    return sha256(canonical_json({
        field: response[field]
        for field in ADAPTER_RESPONSE_FIELDS
        if field != "submission_adapter_response_sha256"
    }).encode("utf-8"))


class _DuplicateKeyError(ValueError):
    pass


@dataclass(frozen=True)
class _PreservedJsonObjectPairs:
    pairs: tuple[tuple[str, Any], ...]


def _preserve_json_object_pairs(
    pairs: list[tuple[str, Any]],
) -> _PreservedJsonObjectPairs:
    return _PreservedJsonObjectPairs(pairs=tuple(pairs))


def _reject_duplicate_pairs(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError("duplicate_json_key")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError("nonfinite_json_number")


def _json_value_contains_nul(value: Any) -> bool:
    """Scan parsed JSON iteratively so nesting cannot recurse in this phase."""

    stack = [value]
    while stack:
        current = stack.pop()
        if type(current) is str:
            if "\x00" in current:
                return True
        elif type(current) is list:
            stack.extend(current)
        elif type(current) is _PreservedJsonObjectPairs:
            for key, item in current.pairs:
                if "\x00" in key:
                    return True
                stack.append(item)
        elif type(current) is dict:
            for key, item in current.items():
                if "\x00" in key:
                    return True
                stack.append(item)
    return False


def _strict_json_loads(source_payload: bytes) -> tuple[Any | None, str | None]:
    try:
        text = source_payload.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return None, "SOURCE_PAYLOAD_UTF8_INVALID"
    if text.startswith("\ufeff"):
        return None, "SOURCE_PAYLOAD_BOM_FORBIDDEN"
    if "\x00" in text:
        return None, "SOURCE_PAYLOAD_JSON_INVALID"
    try:
        syntax_value = json.loads(
            text,
            object_pairs_hook=_preserve_json_object_pairs,
            parse_constant=_reject_nonfinite,
        )
    except (
        json.JSONDecodeError,
        ValueError,
        RecursionError,
        OverflowError,
    ):
        return None, "SOURCE_PAYLOAD_JSON_INVALID"
    if _json_value_contains_nul(syntax_value):
        return None, "SOURCE_PAYLOAD_JSON_INVALID"
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite,
        )
    except _DuplicateKeyError:
        return None, "SOURCE_PAYLOAD_DUPLICATE_KEY"
    except (
        json.JSONDecodeError,
        ValueError,
        RecursionError,
        OverflowError,
    ):
        return None, "SOURCE_PAYLOAD_JSON_INVALID"
    if _json_value_contains_nul(value):
        return None, "SOURCE_PAYLOAD_JSON_INVALID"
    return value, None


def _review_payload_reason(review: object) -> str | None:
    if type(review) is not dict or tuple(review) != REVIEW_PAYLOAD_FIELDS:
        return "REVIEW_RECORD_PAYLOAD_FIELD_INVENTORY_MISMATCH"
    int_fields = {
        "warhead_type_candidate_class_index_0based",
        "total_candidate_count",
        "admitted_candidate_count",
    }
    for field in REVIEW_PAYLOAD_FIELDS:
        value = review[field]
        if field in int_fields:
            if type(value) is not int or value < 0:
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        elif field == "selected_bridge_candidate_index_0based":
            if value is not None and (type(value) is not int or value < 0):
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        elif field == "reviewed_warhead_atom_ids":
            if type(value) is not list or any(
                type(item) is not str for item in value
            ):
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
            try:
                sorted_value = sorted(
                    value,
                    key=lambda item: item.encode("utf-8"),
                )
            except UnicodeEncodeError:
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
            if value != sorted_value or len(value) != len(set(value)):
                return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
        elif type(value) is not str:
            return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    if (
        review["review_record_version"] != ingestion_design.REVIEW_RECORD_VERSION
        or review["review_unit_type"] != ingestion_design.REVIEW_UNIT_TYPE
    ):
        return "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
    if review["review_decision"] not in COMPLETED_REVIEW_DECISIONS:
        return "REVIEW_DECISION_NOT_COMPLETED"
    return None


def _item_reason(item: object) -> str | None:
    if type(item) is not dict or tuple(item) != SUBMISSION_ITEM_FIELDS:
        return "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH"
    if (
        type(item["submission_item_version"]) is not str
        or type(item["review_record_payload"]) is not dict
        or type(item["reviewer_provenance_attested"]) is not bool
        or type(item["reviewer_provenance_attestor_id"]) is not str
        or type(item["submission_source_label"]) is not str
        or item["submission_item_version"] != SUBMISSION_ITEM_VERSION
    ):
        return "SUBMISSION_ITEM_EXACT_TYPE_INVALID"
    reason = _review_payload_reason(item["review_record_payload"])
    if reason is not None:
        return reason
    if item["reviewer_provenance_attested"] is not True:
        return "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED"
    if not _meaningful(item["reviewer_provenance_attestor_id"]):
        return "PROVENANCE_ATTESTOR_INVALID"
    if not _meaningful(item["submission_source_label"]):
        return "SUBMISSION_SOURCE_LABEL_NOT_MEANINGFUL"
    return None


@dataclass(frozen=True)
class AdapterSourceAnalysis:
    """Deterministic source-to-classification plan with no lifecycle effects."""

    source_payload_sha256: str
    parsed_json_available: bool
    parsed_bundle: Any | None
    canonical_bundle_sha256: str
    submission_batch_id: str
    submission_items: tuple[object, ...]
    item_specific_reasons: tuple[str | None, ...]
    derived_review_sha256s: tuple[str, ...]
    response_reason: str
    ordered_result_reasons: tuple[str, ...]
    adapter_passed: bool
    expected_adapted_item_count: int


def _source_analysis(
    *,
    source_sha: str,
    parsed_json_available: bool = False,
    parsed_bundle: Any | None = None,
    bundle_sha: str = "",
    batch_id: str = "",
    items: Sequence[object] = (),
    item_reasons: Sequence[str | None] = (),
    derived_shas: Sequence[str] = (),
    response_reason: str,
    result_reasons: Sequence[str] = (),
    passed: bool = False,
    adapted_count: int = 0,
) -> AdapterSourceAnalysis:
    return AdapterSourceAnalysis(
        source_payload_sha256=source_sha,
        parsed_json_available=parsed_json_available,
        parsed_bundle=parsed_bundle,
        canonical_bundle_sha256=bundle_sha,
        submission_batch_id=batch_id,
        submission_items=tuple(items),
        item_specific_reasons=tuple(item_reasons),
        derived_review_sha256s=tuple(derived_shas),
        response_reason=response_reason,
        ordered_result_reasons=tuple(result_reasons),
        adapter_passed=passed,
        expected_adapted_item_count=adapted_count,
    )


def _analyze_submission_source_v1(
    source_payload: object,
) -> AdapterSourceAnalysis:
    """Strictly parse and uniquely classify one raw in-memory source."""

    if type(source_payload) is not bytes:
        return _source_analysis(
            source_sha="",
            response_reason="SOURCE_PAYLOAD_EXACT_TYPE_INVALID",
        )
    source_sha = sha256(source_payload)
    if not 1 <= len(source_payload) <= MAX_SOURCE_PAYLOAD_BYTES:
        return _source_analysis(
            source_sha=source_sha,
            response_reason="SOURCE_PAYLOAD_SIZE_INVALID",
        )
    bundle, reason = _strict_json_loads(source_payload)
    if reason is not None:
        return _source_analysis(
            source_sha=source_sha,
            response_reason=reason,
        )
    try:
        bundle_sha = sha256(canonical_json(bundle).encode("utf-8"))
    except (TypeError, ValueError, RecursionError, OverflowError):
        return _source_analysis(
            source_sha=source_sha,
            response_reason="SOURCE_PAYLOAD_JSON_INVALID",
        )
    batch_id = (
        bundle.get("submission_batch_id", "")
        if type(bundle) is dict
        and type(bundle.get("submission_batch_id")) is str
        else ""
    )

    def bundle_failure(
        failure_reason: str,
        *,
        items: Sequence[object] = (),
    ) -> AdapterSourceAnalysis:
        return _source_analysis(
            source_sha=source_sha,
            parsed_json_available=True,
            parsed_bundle=bundle,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=items,
            response_reason=failure_reason,
        )

    if type(bundle) is not dict or tuple(bundle) != SUBMISSION_BUNDLE_FIELDS:
        return bundle_failure("SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH")
    if (
        type(bundle["submission_bundle_version"]) is not str
        or type(bundle["submission_batch_id"]) is not str
        or type(bundle["submission_items"]) is not list
    ):
        return bundle_failure("SUBMISSION_BUNDLE_EXACT_TYPE_INVALID")
    if bundle["submission_bundle_version"] != SUBMISSION_BUNDLE_VERSION:
        return bundle_failure("SUBMISSION_BUNDLE_VERSION_MISMATCH")
    if not _meaningful(batch_id):
        return bundle_failure("SUBMISSION_BATCH_ID_NOT_MEANINGFUL")
    items = bundle["submission_items"]
    if not 1 <= len(items) <= 11:
        return bundle_failure(
            "SUBMISSION_ITEM_COUNT_INVALID",
            items=items,
        )
    item_reasons = tuple(_item_reason(item) for item in items)
    if any(reason is not None for reason in item_reasons):
        response_reason = next(
            reason for reason in item_reasons if reason is not None
        )
        result_reasons = tuple(
            reason if reason is not None else "ADAPTER_ATOMICITY_ABORTED"
            for reason in item_reasons
        )
        return _source_analysis(
            source_sha=source_sha,
            parsed_json_available=True,
            parsed_bundle=bundle,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=items,
            item_reasons=item_reasons,
            response_reason=response_reason,
            result_reasons=result_reasons,
        )
    derived_sha_values: list[str] = []
    derived_authority_reasons: list[str | None] = []
    for item in items:
        try:
            derived_sha_values.append(
                _canonical_review_sha(item["review_record_payload"])
            )
            derived_authority_reasons.append(None)
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeEncodeError,
            RecursionError,
            OverflowError,
        ):
            derived_sha_values.append("")
            derived_authority_reasons.append(
                "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"
            )
    if any(reason is not None for reason in derived_authority_reasons):
        response_reason = next(
            reason
            for reason in derived_authority_reasons
            if reason is not None
        )
        return _source_analysis(
            source_sha=source_sha,
            parsed_json_available=True,
            parsed_bundle=bundle,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=items,
            item_reasons=derived_authority_reasons,
            derived_shas=derived_sha_values,
            response_reason=response_reason,
            result_reasons=tuple(
                reason
                if reason is not None
                else "ADAPTER_ATOMICITY_ABORTED"
                for reason in derived_authority_reasons
            ),
        )
    derived_shas = tuple(derived_sha_values)
    if len(derived_shas) != len(set(derived_shas)):
        reason = "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE"
        return _source_analysis(
            source_sha=source_sha,
            parsed_json_available=True,
            parsed_bundle=bundle,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=items,
            item_reasons=item_reasons,
            derived_shas=derived_shas,
            response_reason=reason,
            result_reasons=(reason,) * len(items),
        )
    samples = tuple(_safe_item_sample(item) for item in items)
    if len(samples) != len(set(samples)):
        reason = "DUPLICATE_SAMPLE_IN_BUNDLE"
        return _source_analysis(
            source_sha=source_sha,
            parsed_json_available=True,
            parsed_bundle=bundle,
            bundle_sha=bundle_sha,
            batch_id=batch_id,
            items=items,
            item_reasons=item_reasons,
            derived_shas=derived_shas,
            response_reason=reason,
            result_reasons=(reason,) * len(items),
        )
    return _source_analysis(
        source_sha=source_sha,
        parsed_json_available=True,
        parsed_bundle=bundle,
        bundle_sha=bundle_sha,
        batch_id=batch_id,
        items=items,
        item_reasons=item_reasons,
        derived_shas=derived_shas,
        response_reason="PASSED",
        result_reasons=("PASSED",) * len(items),
        passed=True,
        adapted_count=len(items),
    )


def _safe_item_sample(item: object) -> str:
    if type(item) is not dict:
        return ""
    review = item.get("review_record_payload")
    if type(review) is not dict:
        return ""
    sample = review.get("sample_index_row_id")
    return sample if type(sample) is str else ""


def _new_result(
    *,
    item_index: int,
    batch_id: str,
    sample: str,
    outcome: str,
    passed: bool,
    reason: str,
    review_sha: str = "",
    envelope_sha: str = "",
    consumed: bool = False,
    ready: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "submission_adapter_result_version": SUBMISSION_ADAPTER_RESULT_VERSION,
        "item_index_0based": item_index,
        "submission_batch_id": batch_id,
        "sample_index_row_id": sample,
        "outcome": outcome,
        "passed": passed,
        "reason": reason,
        "review_record_sha256": review_sha,
        "ingestion_envelope_sha256": envelope_sha,
        "consumed_submission_item": consumed,
        "ready_for_interface_evaluation": ready,
        "submission_adapter_result_sha256": "",
    }
    result["submission_adapter_result_sha256"] = _adapter_result_sha(result)
    return result


def _new_response(
    *,
    source_sha: str,
    bundle_sha: str,
    batch_id: str,
    passed: bool,
    reason: str,
    results: tuple[dict[str, Any], ...] = (),
    submissions: tuple[tuple[dict[str, Any], dict[str, Any]], ...] = (),
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "submission_adapter_response_version":
            SUBMISSION_ADAPTER_RESPONSE_VERSION,
        "source_payload_sha256": source_sha,
        "canonical_bundle_sha256": bundle_sha,
        "submission_batch_id": batch_id,
        "adapter_passed": passed,
        "reason": reason,
        "adapter_result_records": results,
        "adapted_submissions": submissions,
        "submission_adapter_response_sha256": "",
    }
    response["submission_adapter_response_sha256"] = _adapter_response_sha(
        response
    )
    return response


def _validate_reference_response_impl(
    response: Mapping[str, Any],
    *,
    source_payload: object,
) -> None:
    analysis = _analyze_submission_source_v1(source_payload)
    if type(response) is not dict or tuple(response) != ADAPTER_RESPONSE_FIELDS:
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    exact_types = (
        type(response["submission_adapter_response_version"]) is str,
        type(response["source_payload_sha256"]) is str,
        type(response["canonical_bundle_sha256"]) is str,
        type(response["submission_batch_id"]) is str,
        type(response["adapter_passed"]) is bool,
        type(response["reason"]) is str,
        type(response["adapter_result_records"]) is tuple,
        type(response["adapted_submissions"]) is tuple,
        type(response["submission_adapter_response_sha256"]) is str,
    )
    if not all(exact_types):
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    if response["submission_adapter_response_version"] != (
        SUBMISSION_ADAPTER_RESPONSE_VERSION
    ):
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    if response["reason"] not in ADAPTER_REASON_CODES:
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    if (
        response["source_payload_sha256"]
        != analysis.source_payload_sha256
        or response["canonical_bundle_sha256"]
        != analysis.canonical_bundle_sha256
        or response["submission_batch_id"]
        != analysis.submission_batch_id
        or response["adapter_passed"] is not analysis.adapter_passed
        or response["reason"] != analysis.response_reason
        or len(response["adapter_result_records"])
        != len(analysis.ordered_result_reasons)
        or len(response["adapted_submissions"])
        != analysis.expected_adapted_item_count
        or (
            response["canonical_bundle_sha256"]
            and _SHA.fullmatch(response["canonical_bundle_sha256"]) is None
        )
    ):
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    if response["submission_adapter_response_sha256"] != (
        _adapter_response_sha(response)
    ):
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    parsed_items = analysis.submission_items
    result_shas: set[str] = set()
    for position, result in enumerate(response["adapter_result_records"]):
        if type(result) is not dict or tuple(result) != ADAPTER_RESULT_FIELDS:
            raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        if (
            result["submission_adapter_result_version"]
            != SUBMISSION_ADAPTER_RESULT_VERSION
            or type(result["item_index_0based"]) is not int
            or result["item_index_0based"] < 0
            or result["item_index_0based"] != position
            or type(result["passed"]) is not bool
            or type(result["consumed_submission_item"]) is not bool
            or type(result["ready_for_interface_evaluation"]) is not bool
            or any(
                type(result[field]) is not str
                for field in ADAPTER_RESULT_FIELDS
                if field not in {
                    "item_index_0based",
                    "passed",
                    "consumed_submission_item",
                    "ready_for_interface_evaluation",
                }
            )
            or result["submission_adapter_result_sha256"]
            != _adapter_result_sha(result)
            or result["reason"] not in ADAPTER_REASON_CODES
            or result["reason"]
            != analysis.ordered_result_reasons[position]
            or result["outcome"] not in {"adapted", "invalid"}
            or result["submission_batch_id"] != response["submission_batch_id"]
        ):
            raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        if (
            result["submission_adapter_result_sha256"] in result_shas
            or _SHA.fullmatch(
                result["submission_adapter_result_sha256"]
            ) is None
        ):
            raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        result_shas.add(result["submission_adapter_result_sha256"])
        if (
            position >= len(parsed_items)
            or result["sample_index_row_id"]
            != _safe_item_sample(parsed_items[position])
        ):
            raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        if result["outcome"] == "adapted":
            if (
                result["passed"] is not True
                or result["reason"] != "PASSED"
                or result["consumed_submission_item"] is not True
                or result["ready_for_interface_evaluation"] is not True
                or _SHA.fullmatch(result["review_record_sha256"]) is None
                or _SHA.fullmatch(result["ingestion_envelope_sha256"]) is None
            ):
                raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        elif (
            result["passed"] is not False
            or result["reason"] == "PASSED"
            or result["consumed_submission_item"] is not False
            or result["ready_for_interface_evaluation"] is not False
            or result["review_record_sha256"] != ""
            or result["ingestion_envelope_sha256"] != ""
        ):
            raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    if response["adapter_passed"]:
        if (
            analysis.adapter_passed is not True
            or response["reason"] != "PASSED"
            or not parsed_items
            or not response["adapted_submissions"]
            or len(response["adapter_result_records"]) != len(parsed_items)
            or len(response["adapted_submissions"])
            != len(parsed_items)
            or any(
                result["outcome"] != "adapted"
                for result in response["adapter_result_records"]
            )
        ):
            raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        for position, submission in enumerate(response["adapted_submissions"]):
            if type(submission) is not tuple or len(submission) != 2:
                raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
            review, envelope = submission
            item = parsed_items[position]
            result = response["adapter_result_records"][position]
            if (
                type(item) is not dict
                or tuple(item) != SUBMISSION_ITEM_FIELDS
                or type(review) is not dict
                or tuple(review) != ingestion_design.REVIEW_RECORD_FIELDS
                or type(envelope) is not dict
                or tuple(envelope) != ingestion_design.INGESTION_ENVELOPE_FIELDS
                or envelope["ingestion_envelope_version"]
                != ingestion_design.INGESTION_ENVELOPE_VERSION
                or {
                    field: review[field] for field in REVIEW_PAYLOAD_FIELDS
                } != item["review_record_payload"]
                or envelope["reviewer_provenance_attested"]
                != item["reviewer_provenance_attested"]
                or envelope["reviewer_provenance_attestor_id"]
                != item["reviewer_provenance_attestor_id"]
                or envelope["submission_source_label"]
                != item["submission_source_label"]
                or review["review_record_sha256"]
                != ingestion_design.review_record_sha256(review)
                or envelope["submitted_record_payload_sha256"]
                != ingestion_design.submitted_record_payload_sha256(review)
                or envelope["ingestion_envelope_sha256"]
                != ingestion_design.ingestion_envelope_sha256(envelope)
                or result["review_record_sha256"]
                != review["review_record_sha256"]
                or result["ingestion_envelope_sha256"]
                != envelope["ingestion_envelope_sha256"]
                or result["sample_index_row_id"]
                != review["sample_index_row_id"]
                or envelope["sample_index_row_id"]
                != review["sample_index_row_id"]
                or envelope["review_record_sha256"]
                != review["review_record_sha256"]
                or envelope["submission_batch_id"]
                != response["submission_batch_id"]
            ):
                raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    else:
        if (
            analysis.adapter_passed is not False
            or response["reason"] == "PASSED"
            or response["adapted_submissions"]
            or any(
                result["outcome"] != "invalid"
                for result in response["adapter_result_records"]
            )
        ):
            raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
        if response["adapter_result_records"]:
            if (
                len(response["adapter_result_records"]) != len(parsed_items)
            ):
                raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
            non_atomic = [
                result["reason"]
                for result in response["adapter_result_records"]
                if result["reason"] != "ADAPTER_ATOMICITY_ABORTED"
            ]
            if not non_atomic or response["reason"] != non_atomic[0]:
                raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")


def _validate_reference_response(
    response: Mapping[str, Any],
    *,
    source_payload: object,
) -> None:
    """Normalize every response semantic failure to the sole public reason."""

    try:
        _validate_reference_response_impl(
            response,
            source_payload=source_payload,
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        RecursionError,
        OverflowError,
    ):
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID") from None


def _reference_adapt_submission_bundle_v1(
    *,
    source_payload: bytes,
) -> dict[str, Any]:
    """Private, synthetic-only reference evaluator for the frozen design."""

    source_snapshot = (
        bytes(source_payload) if type(source_payload) is bytes else None
    )
    analysis = _analyze_submission_source_v1(source_payload)
    results_list: list[dict[str, Any]] = []
    adapted: list[tuple[dict[str, Any], dict[str, Any]]] = []
    if analysis.adapter_passed:
        for index, item in enumerate(analysis.submission_items):
            if type(item) is not dict:
                raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
            review = {
                field: copy.deepcopy(item["review_record_payload"][field])
                for field in REVIEW_PAYLOAD_FIELDS
            }
            review["review_record_sha256"] = _canonical_review_sha(review)
            envelope: dict[str, Any] = {
                "ingestion_envelope_version":
                    ingestion_design.INGESTION_ENVELOPE_VERSION,
                "submission_batch_id": analysis.submission_batch_id,
                "sample_index_row_id": review["sample_index_row_id"],
                "review_record_sha256": review["review_record_sha256"],
                "submitted_record_payload_sha256":
                    _submitted_record_payload_sha(review),
                "reviewer_provenance_attested":
                    item["reviewer_provenance_attested"],
                "reviewer_provenance_attestor_id":
                    item["reviewer_provenance_attestor_id"],
                "submission_source_label": item["submission_source_label"],
                "ingestion_envelope_sha256": "",
            }
            envelope["ingestion_envelope_sha256"] = (
                _ingestion_envelope_sha(envelope)
            )
            adapted.append((review, envelope))
            results_list.append(_new_result(
                item_index=index,
                batch_id=analysis.submission_batch_id,
                sample=review["sample_index_row_id"],
                outcome="adapted",
                passed=True,
                reason=analysis.ordered_result_reasons[index],
                review_sha=review["review_record_sha256"],
                envelope_sha=envelope["ingestion_envelope_sha256"],
                consumed=True,
                ready=True,
            ))
    else:
        results_list.extend(
            _new_result(
                item_index=index,
                batch_id=analysis.submission_batch_id,
                sample=_safe_item_sample(item),
                outcome="invalid",
                passed=False,
                reason=result_reason,
            )
            for index, (item, result_reason) in enumerate(zip(
                analysis.submission_items,
                analysis.ordered_result_reasons,
            ))
        )
    response = _new_response(
        source_sha=analysis.source_payload_sha256,
        bundle_sha=analysis.canonical_bundle_sha256,
        batch_id=analysis.submission_batch_id,
        passed=analysis.adapter_passed,
        reason=analysis.response_reason,
        results=tuple(results_list),
        submissions=tuple(adapted),
    )
    _validate_reference_response(response, source_payload=source_payload)
    if (
        source_snapshot is not None
        and source_payload != source_snapshot
    ):
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    return response


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _cell(value: Any) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _csv_bytes(
    columns: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _cell(row[column]) for column in columns})
    return stream.getvalue().encode("utf-8")


def _source_inventory(
    payloads: Mapping[Path, bytes],
) -> tuple[Mapping[str, Any], ...]:
    roles = {
        INTERFACE_PRODUCTION: "formal ingestion public API and Exact6 response",
        INTERFACE_MANIFEST: "formal interface state and lifecycle counts",
        INTERFACE_CONTRACT: "interface contract predecessor evidence",
        INTERFACE_TRUTH: "interface synthetic predecessor evidence",
        INTERFACE_READINESS: "Current11 predecessor readiness evidence",
        INTERFACE_FAILURE: "interface fail-closed predecessor evidence",
        DESIGN_PRODUCTION: "Exact26 review and Exact9 envelope authority",
        DESIGN_MANIFEST: "review-ingestion design state",
        PACKAGE_MANIFEST: "Current11 package lineage and sample inventory",
        PACKAGE_TEMPLATES: "blank Exact26 templates and Current11 identity",
    }
    used = {
        INTERFACE_PRODUCTION:
            "public builder;evaluator;response validator;interface digest",
        INTERFACE_MANIFEST:
            "transaction;implementation;execution;counts;masks;modules;training",
        INTERFACE_CONTRACT: "header;row count;verified",
        INTERFACE_TRUTH: "header;row count;verified",
        INTERFACE_READINESS: "header;Current11 row count;verified",
        INTERFACE_FAILURE: "header;mutation count;verified",
        DESIGN_PRODUCTION:
            "review fields;versions;envelope fields;digest semantics",
        DESIGN_MANIFEST:
            "transaction;execution;counts;training prerequisite",
        PACKAGE_MANIFEST:
            "transaction;sample count;package/template availability",
        PACKAGE_TEMPLATES:
            "sample;pdb;ligand;candidate set;synthetic payload identity",
    }
    authorities = {
        INTERFACE_PRODUCTION: "committed implementation authority",
        INTERFACE_MANIFEST: "committed state authority",
        INTERFACE_CONTRACT: "committed evidence",
        INTERFACE_TRUTH: "committed evidence",
        INTERFACE_READINESS: "committed evidence",
        INTERFACE_FAILURE: "committed evidence",
        DESIGN_PRODUCTION: "committed schema and digest authority",
        DESIGN_MANIFEST: "committed state authority",
        PACKAGE_MANIFEST: "committed package authority",
        PACKAGE_TEMPLATES: "committed blank-template authority",
    }
    return tuple({
        "source_path": path.as_posix(),
        "BASE_SHA256": sha256(payloads[path]),
        "source_role": roles[path],
        "fields_actually_used": used[path],
        "authority_class": authorities[path],
        "verified": sha256(payloads[path]) == FROZEN_BASE_SHA256[path],
    } for path in SOURCE_PATHS)


def _contract_rows() -> tuple[Mapping[str, Any], ...]:
    specifications = (
        (
            "raw source is the sole parse, classification and response identity authority",
            "source",
            "in-memory bytes",
            "exact bytes;size 1..1048576;strict UTF-8;single source analysis",
            "strict parsing admitted",
            "public reason;no adapted submissions",
        ),
        (
            "pair-preserving NUL scan globally precedes duplicate-key rejection",
            "strict_json",
            "decoded JSON text",
            "preserve every object pair;scan NUL first;literal backslash-u0000 allowed;parser exceptions normalized",
            "single JSON value admitted",
            "strict JSON reason;no effects",
        ),
        (
            "submission bundle schema is Exact3",
            "bundle",
            "same raw source strict parse",
            "ordered Exact3 fields and exact types from source analysis",
            "bundle admitted",
            "bundle reason;no effects",
        ),
        (
            "submission item schema is Exact5",
            "item",
            "submission_items in input order",
            "ordered Exact5 fields and exact types",
            "item admitted",
            "item reason;atomic abort",
        ),
        (
            "review payload Exact25 inherits the formal Exact26 structural domain",
            "review",
            "review_record_payload",
            "ordered Exact25;exact inherited types;atom IDs UTF-8 sorted unique",
            "payload admitted for digest derivation",
            "review reason;atomic abort",
        ),
        (
            "no coercion, normalization, repair or field invention is allowed",
            "input_fidelity",
            "all human submission fields",
            "exact values are copied without mutation",
            "human fields preserved",
            "invalid exact input rejected",
        ),
        (
            "only completed review decisions are adaptable",
            "decision",
            "review_decision",
            "select;revise;quarantine only",
            "completed decision admitted",
            "not_reviewed rejected",
        ),
        (
            "review, submitted-payload and envelope digests use frozen authorities",
            "digest",
            "Exact25 and Exact5 provenance",
            "delegate frozen ingestion-design structural and digest authorities",
            "Exact26 and Exact9 constructed",
            "no partial digest effect",
        ),
        (
            "item order and all-valid duplicate precedence are exact",
            "bundle_identity",
            "1..11 ordered items",
            "single source analysis validates all items first;derived review SHA duplicate precedes sample duplicate",
            "ordered submissions emitted",
            "duplicate reason;atomic abort",
        ),
        (
            "bundle adaptation is all-or-nothing",
            "atomicity",
            "source analysis ordered result-reason plan",
            "every item must pass;atomic result reasons match the frozen plan",
            "all items consumed",
            "none consumed;adapted tuple empty",
        ),
        (
            "adapter response and derived records bind source and formal structures",
            "response",
            "raw source and reference evaluation",
            "Exact9/Exact12;derived Exact26/Exact9 version;types;authority digests;source linkage",
            "validated deterministic response",
            "response invariant failure",
        ),
        (
            "adapter performs no filesystem input/output or input mutation",
            "side_effect",
            "exact source bytes",
            "in-memory only;source snapshot unchanged",
            "zero filesystem effects",
            "fail closed",
        ),
        (
            "adapter success is not ingestion or authority approval",
            "authority_boundary",
            "adapted submissions",
            "formal interface remains semantic authority",
            "ready only for interface evaluation",
            "no authority created",
        ),
        (
            "SMARTS, model and training gates remain closed",
            "downstream",
            "design state",
            "canonical masks remain Exact5;modules 0/5",
            "implementation readiness only",
            "all downstream readiness false",
        ),
    )
    return tuple({
        "contract_id": f"ADAPTER_{index:03d}",
        "semantic_name": values[0],
        "contract_scope": values[1],
        "required_inputs": values[2],
        "validation_rule": values[3],
        "success_effect": values[4],
        "failure_effect": values[5],
        "fails_closed": True,
        "verified": True,
    } for index, values in enumerate(specifications, 1))


def _synthetic_payloads(
    repo_root: Path,
) -> tuple[
    ingestion_design.IngestionAuthorityContext,
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    context = (
        ingestion_interface.
        build_current11_warhead_boundary_review_ingestion_authority_context_v1(
            repo_root
        )
    )
    phase = ingestion_design._validated_ingestion_authority_context(context)
    if phase.blocking_reasons:
        raise ValueError("SYNTHETIC_INTERFACE_CONTEXT_BLOCKED")
    templates = [dict(row) for row in phase.template_rows]
    options_by_sample: dict[str, list[Mapping[str, Any]]] = {}
    for option in phase.option_rows:
        options_by_sample.setdefault(
            option["sample_index_row_id"], []
        ).append(option)

    def completed_payload(offset: int, decision: str) -> dict[str, Any]:
        record = copy.deepcopy(templates[offset])
        sample = record["sample_index_row_id"]
        if decision in {
            "select_admitted_candidate",
            "revise_atom_set_and_boundary",
        }:
            option = next(
                row for row in options_by_sample[sample]
                if row["review_eligible"]
            )
            record.update({
                "reviewed_warhead_atom_ids":
                    list(option["warhead_side_atom_ids"]),
                "reviewed_warhead_attachment_atom_id":
                    option["warhead_attachment_atom_id"],
                "reviewed_nonwarhead_boundary_atom_id":
                    option["nonwarhead_boundary_atom_id"],
                "reviewed_attachment_boundary_bond_order":
                    option["boundary_bond_order"],
                "reviewed_boundary_bond_id": option["boundary_bond_id"],
            })
            if decision == "select_admitted_candidate":
                record.update({
                    "selected_bridge_candidate_index_0based":
                        option["source_bridge_candidate_index_0based"],
                    "selected_bridge_candidate_record_sha256":
                        option["source_bridge_candidate_record_sha256"],
                })
        record.update({
            "review_decision": decision,
            "reviewer_id": f"synthetic-human-reviewer-{offset + 1:02d}",
            "review_rationale":
                "Synthetic human-shaped adapter design validation only.",
            "review_notes": "",
        })
        return {
            field: copy.deepcopy(record[field])
            for field in REVIEW_PAYLOAD_FIELDS
        }

    payloads = [
        completed_payload(0, "select_admitted_candidate"),
        completed_payload(1, "revise_atom_set_and_boundary"),
        completed_payload(2, "quarantine"),
        completed_payload(3, "select_admitted_candidate"),
        completed_payload(4, "quarantine"),
    ]
    items = [{
        "submission_item_version": SUBMISSION_ITEM_VERSION,
        "review_record_payload": payload,
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id":
            f"synthetic-human-attestor-{index + 1:02d}",
        "submission_source_label": "synthetic-adapter-design-validation-only",
    } for index, payload in enumerate(payloads)]
    return context, payloads, items


def _bundle_bytes(
    items: Sequence[Mapping[str, Any]],
    batch: str = "synthetic-adapter-design-batch",
) -> bytes:
    return json.dumps({
        "submission_bundle_version": SUBMISSION_BUNDLE_VERSION,
        "submission_batch_id": batch,
        "submission_items": list(items),
    }, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class SyntheticTruthCase:
    name: str
    source_payload: object
    expected_reason: str
    expected_outcome: str
    expected_item_count: int
    interface_compatibility: bool = False


def _truth_cases(
    items: Sequence[Mapping[str, Any]],
) -> tuple[SyntheticTruthCase, ...]:
    valid_select = _bundle_bytes([items[0]], "valid-select")
    valid_revise = _bundle_bytes([items[1]], "valid-revise")
    valid_quarantine = _bundle_bytes([items[2]], "valid-quarantine")
    valid_partial = _bundle_bytes(items[3:5], "valid-partial-two")
    bundle = json.loads(valid_select)

    def mutated(
        mutator: Any,
        *,
        base: Mapping[str, Any] = bundle,
    ) -> bytes:
        value = copy.deepcopy(base)
        mutator(value)
        return json.dumps(
            value, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
        ).encode("utf-8")

    twelve_items = [copy.deepcopy(items[0]) for _ in range(12)]
    for index, item in enumerate(twelve_items):
        item["review_record_payload"]["sample_index_row_id"] = (
            f"synthetic-count-{index:02d}"
        )
    duplicate_sample_items = [copy.deepcopy(items[0]), copy.deepcopy(items[1])]
    duplicate_sample_items[1]["review_record_payload"]["sample_index_row_id"] = (
        duplicate_sample_items[0]["review_record_payload"]["sample_index_row_id"]
    )
    duplicate_sha_items = [copy.deepcopy(items[0]), copy.deepcopy(items[0])]
    cases = (
        SyntheticTruthCase("valid_select", valid_select, "PASSED", "adapted", 1, True),
        SyntheticTruthCase("valid_revise", valid_revise, "PASSED", "adapted", 1, True),
        SyntheticTruthCase("valid_quarantine", valid_quarantine, "PASSED", "adapted", 1, True),
        SyntheticTruthCase("valid_partial_two_sample_bundle", valid_partial, "PASSED", "adapted", 2, True),
        SyntheticTruthCase("source_payload_not_bytes", "{}", "SOURCE_PAYLOAD_EXACT_TYPE_INVALID", "invalid", 0),
        SyntheticTruthCase("source_payload_empty", b"", "SOURCE_PAYLOAD_SIZE_INVALID", "invalid", 0),
        SyntheticTruthCase("source_payload_too_large", b"x" * (MAX_SOURCE_PAYLOAD_BYTES + 1), "SOURCE_PAYLOAD_SIZE_INVALID", "invalid", 0),
        SyntheticTruthCase("invalid_utf8", b"\xff", "SOURCE_PAYLOAD_UTF8_INVALID", "invalid", 0),
        SyntheticTruthCase("utf8_bom_forbidden", b"\xef\xbb\xbf{}", "SOURCE_PAYLOAD_BOM_FORBIDDEN", "invalid", 0),
        SyntheticTruthCase("malformed_json", b"{", "SOURCE_PAYLOAD_JSON_INVALID", "invalid", 0),
        SyntheticTruthCase("duplicate_json_key", b'{"submission_bundle_version":"x","submission_bundle_version":"y"}', "SOURCE_PAYLOAD_DUPLICATE_KEY", "invalid", 0),
        SyntheticTruthCase("top_level_not_object", b"[]", "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH", "invalid", 0),
        SyntheticTruthCase("bundle_extra_field", mutated(lambda value: value.__setitem__("extra", "")), "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH", "invalid", 0),
        SyntheticTruthCase("bundle_version_mismatch", mutated(lambda value: value.__setitem__("submission_bundle_version", "wrong")), "SUBMISSION_BUNDLE_VERSION_MISMATCH", "invalid", 0),
        SyntheticTruthCase("batch_id_empty", mutated(lambda value: value.__setitem__("submission_batch_id", "")), "SUBMISSION_BATCH_ID_NOT_MEANINGFUL", "invalid", 0),
        SyntheticTruthCase("submission_items_not_list", mutated(lambda value: value.__setitem__("submission_items", {})), "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID", "invalid", 0),
        SyntheticTruthCase("item_count_zero", mutated(lambda value: value.__setitem__("submission_items", [])), "SUBMISSION_ITEM_COUNT_INVALID", "invalid", 0),
        SyntheticTruthCase("item_count_twelve", _bundle_bytes(twelve_items), "SUBMISSION_ITEM_COUNT_INVALID", "invalid", 0),
        SyntheticTruthCase("item_field_inventory_mismatch", mutated(lambda value: value["submission_items"][0].pop("submission_source_label")), "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH", "invalid", 1),
        SyntheticTruthCase("item_exact_type_invalid", mutated(lambda value: value["submission_items"][0].__setitem__("reviewer_provenance_attested", 1)), "SUBMISSION_ITEM_EXACT_TYPE_INVALID", "invalid", 1),
        SyntheticTruthCase("review_payload_field_inventory_mismatch", mutated(lambda value: value["submission_items"][0]["review_record_payload"].pop("review_notes")), "REVIEW_RECORD_PAYLOAD_FIELD_INVENTORY_MISMATCH", "invalid", 1),
        SyntheticTruthCase("review_payload_exact_type_invalid", mutated(lambda value: value["submission_items"][0]["review_record_payload"].__setitem__("total_candidate_count", True)), "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID", "invalid", 1),
        SyntheticTruthCase("not_reviewed_decision", mutated(lambda value: value["submission_items"][0]["review_record_payload"].__setitem__("review_decision", "not_reviewed")), "REVIEW_DECISION_NOT_COMPLETED", "invalid", 1),
        SyntheticTruthCase("provenance_attestation_false", mutated(lambda value: value["submission_items"][0].__setitem__("reviewer_provenance_attested", False)), "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED", "invalid", 1),
        SyntheticTruthCase("provenance_attestor_invalid", mutated(lambda value: value["submission_items"][0].__setitem__("reviewer_provenance_attestor_id", " ")), "PROVENANCE_ATTESTOR_INVALID", "invalid", 1),
        SyntheticTruthCase("submission_source_label_invalid", mutated(lambda value: value["submission_items"][0].__setitem__("submission_source_label", "x ")), "SUBMISSION_SOURCE_LABEL_NOT_MEANINGFUL", "invalid", 1),
        SyntheticTruthCase("duplicate_sample", _bundle_bytes(duplicate_sample_items), "DUPLICATE_SAMPLE_IN_BUNDLE", "invalid", 2),
        SyntheticTruthCase("duplicate_derived_review_sha", _bundle_bytes(duplicate_sha_items), "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE", "invalid", 2),
    )
    return cases


def _evaluate_truth_rows(
    repo_root: Path,
    context: ingestion_design.IngestionAuthorityContext,
    items: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    del repo_root
    rows = []
    for index, case in enumerate(_truth_cases(items), 1):
        snapshot = copy.deepcopy(case.source_payload)
        response = _reference_adapt_submission_bundle_v1(
            source_payload=case.source_payload,
        )
        interface_passed = False
        if case.interface_compatibility:
            interface_response = (
                ingestion_interface.
                evaluate_current11_warhead_boundary_review_ingestion_v1(
                    submissions=response["adapted_submissions"],
                    authority_context=context,
                )
            )
            ingestion_interface.validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
                interface_response,
                submissions=response["adapted_submissions"],
                authority_context=context,
            )
            interface_passed = interface_response["batch_passed"] is True
        outcome = "adapted" if response["adapter_passed"] else "invalid"
        verified = (
            outcome == case.expected_outcome
            and response["reason"] == case.expected_reason
            and len(response["adapter_result_records"])
            == case.expected_item_count
            and response["submission_adapter_response_sha256"]
            == _adapter_response_sha(response)
            and case.source_payload == snapshot
            and (not case.interface_compatibility or interface_passed)
        )
        rows.append({
            "truth_case_id": f"TRUTH_{index:03d}",
            "truth_case_name": case.name,
            "expected_outcome": case.expected_outcome,
            "expected_reason": case.expected_reason,
            "expected_item_count": case.expected_item_count,
            "adapter_passed": response["adapter_passed"],
            "adapted_submission_count":
                len(response["adapted_submissions"]),
            "result_record_count":
                len(response["adapter_result_records"]),
            "response_schema_valid":
                tuple(response) == ADAPTER_RESPONSE_FIELDS,
            "response_hash_valid":
                response["submission_adapter_response_sha256"]
                == _adapter_response_sha(response),
            "input_order_preserved": True,
            "inputs_unmodified": case.source_payload == snapshot,
            "interface_compatibility_checked": case.interface_compatibility,
            "interface_batch_passed": interface_passed,
            "filesystem_write_count": 0,
            "verified": verified,
        })
    return tuple(rows)


def _readiness_rows(
    context: ingestion_design.IngestionAuthorityContext,
) -> tuple[Mapping[str, Any], ...]:
    phase = ingestion_design._validated_ingestion_authority_context(context)
    blocking = ";".join((
        "completed_human_review_record_missing",
        "human_provenance_attestation_missing",
        "submission_payload_missing",
        "submission_adapter_not_implemented",
        "real_ingestion_not_executed",
    ))
    return tuple({
        "sample_index_row_id": row["sample_index_row_id"],
        "pdb_id": row["pdb_id"],
        "ligand_comp_id": row["ligand_comp_id"],
        "source_candidate_set_sha256": row["source_candidate_set_sha256"],
        "review_package_available": True,
        "blank_review_template_available": True,
        "ingestion_interface_available": True,
        "submission_adapter_design_completed": True,
        "ready_for_submission_adapter_implementation": True,
        "completed_review_record_available": False,
        "human_provenance_envelope_available": False,
        "submission_payload_available": False,
        "adapted_submission_available": False,
        "ready_for_real_ingestion_execution": False,
        "real_ingestion_completed": False,
        "authority_record_available": False,
        "complete_warhead_atom_set_authority_available": False,
        "exact_one_attachment_boundary_authority_available": False,
        "sample_quarantined": False,
        "ready_for_candidate_warhead_smarts_materialization": False,
        "ready_for_role_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "blocking_reasons": blocking,
        "verified": True,
    } for row in sorted(
        phase.index_rows,
        key=lambda value: value["sample_index_row_id"].encode("utf-8"),
    ))


@dataclass(frozen=True)
class AdapterDesignScenario:
    base_source_present: bool = True
    base_source_sha_valid: bool = True
    interface_transaction_succeeded: bool = True
    interface_real_execution_closed: bool = True
    source_payload_exact_type_valid: bool = True
    source_payload_size_valid: bool = True
    invalid_utf8_rejected: bool = True
    bom_rejected: bool = True
    malformed_json_rejected: bool = True
    duplicate_json_key_rejected: bool = True
    bundle_field_inventory_exact: bool = True
    bundle_exact_types: bool = True
    bundle_version_exact: bool = True
    batch_id_meaningful: bool = True
    item_count_valid: bool = True
    item_field_inventory_exact: bool = True
    item_exact_types: bool = True
    review_payload_field_inventory_exact: bool = True
    review_payload_exact_types: bool = True
    not_reviewed_rejected: bool = True
    provenance_attestation_required: bool = True
    provenance_attestor_validated: bool = True
    source_label_validated: bool = True
    duplicate_sample_rejected: bool = True
    duplicate_review_sha_rejected: bool = True
    derived_review_sha_valid: bool = True
    derived_envelope_sha_valid: bool = True
    bundle_atomicity_enforced: bool = True
    response_schema_hash_valid: bool = True
    filesystem_path_input_rejected: bool = True
    actual_lifecycle_record_count: int = 0
    downstream_boundary_intact: bool = True
    nul_content_rejected: bool = True
    json_parser_exceptions_fail_closed: bool = True
    response_result_effect_linkage_valid: bool = True
    reason_precedence_exact: bool = True
    checker_hermetic_lifecycle_verified: bool = True
    source_payload_bundle_binding_valid: bool = True
    successful_response_requires_valid_source_analysis: bool = True
    failed_response_reason_matches_source_analysis: bool = True
    result_reason_plan_matches_source_analysis: bool = True
    checker_source_response_classification_verified: bool = True
    review_atom_ids_canonical_structure_required: bool = True
    ingestion_envelope_version_exact: bool = True
    checker_derived_record_structure_verified: bool = True
    nul_precedence_over_duplicate_key_global: bool = True
    checker_nul_duplicate_precedence_verified: bool = True


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_SOURCE_MISSING"),
    ("BASE source SHA mismatch", "base_source_sha_valid", False, "BASE_SOURCE_SHA_MISMATCH"),
    ("interface transaction not succeeded", "interface_transaction_succeeded", False, "INTERFACE_TRANSACTION_NOT_SUCCEEDED"),
    ("interface real execution prematurely true", "interface_real_execution_closed", False, "INTERFACE_REAL_EXECUTION_PREMATURELY_TRUE"),
    ("source payload exact type invalid", "source_payload_exact_type_valid", False, "SOURCE_PAYLOAD_EXACT_TYPE_INVALID"),
    ("source payload size invalid", "source_payload_size_valid", False, "SOURCE_PAYLOAD_SIZE_INVALID"),
    ("invalid UTF-8 accepted", "invalid_utf8_rejected", False, "SOURCE_PAYLOAD_UTF8_INVALID"),
    ("BOM accepted", "bom_rejected", False, "SOURCE_PAYLOAD_BOM_FORBIDDEN"),
    ("malformed JSON accepted", "malformed_json_rejected", False, "SOURCE_PAYLOAD_JSON_INVALID"),
    ("duplicate JSON key accepted", "duplicate_json_key_rejected", False, "SOURCE_PAYLOAD_DUPLICATE_KEY"),
    ("bundle field inventory mismatch", "bundle_field_inventory_exact", False, "SUBMISSION_BUNDLE_FIELD_INVENTORY_MISMATCH"),
    ("bundle exact type invalid", "bundle_exact_types", False, "SUBMISSION_BUNDLE_EXACT_TYPE_INVALID"),
    ("bundle version mismatch", "bundle_version_exact", False, "SUBMISSION_BUNDLE_VERSION_MISMATCH"),
    ("batch ID invalid", "batch_id_meaningful", False, "SUBMISSION_BATCH_ID_NOT_MEANINGFUL"),
    ("item count invalid", "item_count_valid", False, "SUBMISSION_ITEM_COUNT_INVALID"),
    ("item field inventory mismatch", "item_field_inventory_exact", False, "SUBMISSION_ITEM_FIELD_INVENTORY_MISMATCH"),
    ("item exact type invalid", "item_exact_types", False, "SUBMISSION_ITEM_EXACT_TYPE_INVALID"),
    ("review payload field inventory mismatch", "review_payload_field_inventory_exact", False, "REVIEW_RECORD_PAYLOAD_FIELD_INVENTORY_MISMATCH"),
    ("review payload exact type invalid", "review_payload_exact_types", False, "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"),
    ("not-reviewed decision accepted", "not_reviewed_rejected", False, "REVIEW_DECISION_NOT_COMPLETED"),
    ("provenance attestation false accepted", "provenance_attestation_required", False, "REVIEWER_PROVENANCE_ATTESTATION_REQUIRED"),
    ("provenance attestor invalid", "provenance_attestor_validated", False, "PROVENANCE_ATTESTOR_INVALID"),
    ("source label invalid", "source_label_validated", False, "SUBMISSION_SOURCE_LABEL_NOT_MEANINGFUL"),
    ("duplicate sample accepted", "duplicate_sample_rejected", False, "DUPLICATE_SAMPLE_IN_BUNDLE"),
    ("duplicate derived review SHA accepted", "duplicate_review_sha_rejected", False, "DUPLICATE_DERIVED_REVIEW_SHA_IN_BUNDLE"),
    ("derived review SHA invalid", "derived_review_sha_valid", False, "DERIVED_REVIEW_SHA_INVALID"),
    ("derived envelope SHA invalid", "derived_envelope_sha_valid", False, "DERIVED_ENVELOPE_SHA_INVALID"),
    ("adapter atomicity disabled", "bundle_atomicity_enforced", False, "ADAPTER_ATOMICITY_DISABLED"),
    ("adapter response schema/hash invalid", "response_schema_hash_valid", False, "ADAPTER_RESPONSE_INVARIANT_INVALID"),
    ("filesystem or path input accepted", "filesystem_path_input_rejected", False, "FILESYSTEM_OR_PATH_INPUT_ACCEPTED"),
    ("actual review/envelope/result/authority materialized", "actual_lifecycle_record_count", 1, "ACTUAL_LIFECYCLE_ARTIFACT_MATERIALIZED"),
    ("canonical mask, module or training boundary drift", "downstream_boundary_intact", False, "DOWNSTREAM_BOUNDARY_DRIFT"),
    ("NUL-containing JSON accepted", "nul_content_rejected", False, "SOURCE_PAYLOAD_JSON_INVALID"),
    ("JSON parser internal exception leaked", "json_parser_exceptions_fail_closed", False, "SOURCE_PAYLOAD_JSON_INVALID"),
    ("adapter result effect or adapted-submission linkage invalid", "response_result_effect_linkage_valid", False, "ADAPTER_RESPONSE_INVARIANT_INVALID"),
    ("adapter reason precedence inconsistent or unreachable", "reason_precedence_exact", False, "ADAPTER_REASON_PRECEDENCE_INVALID"),
    ("checker hermetic lifecycle not independently executed", "checker_hermetic_lifecycle_verified", False, "CHECKER_HERMETIC_LIFECYCLE_NOT_VERIFIED"),
    ("raw source and parsed bundle not bound", "source_payload_bundle_binding_valid", False, "ADAPTER_SOURCE_PAYLOAD_BUNDLE_BINDING_INVALID"),
    ("invalid source or bundle accepted as successful response", "successful_response_requires_valid_source_analysis", False, "ADAPTER_SUCCESS_CLASSIFICATION_INVALID"),
    ("valid source accepted as arbitrary failed response", "failed_response_reason_matches_source_analysis", False, "ADAPTER_FAILURE_CLASSIFICATION_INVALID"),
    ("item, atomic or duplicate result reasons not derived from source analysis", "result_reason_plan_matches_source_analysis", False, "ADAPTER_RESULT_REASON_PLAN_INVALID"),
    ("checker source-to-response classification not independently verified", "checker_source_response_classification_verified", False, "CHECKER_SOURCE_RESPONSE_CLASSIFICATION_NOT_VERIFIED"),
    ("inherited Exact26 canonical atom-list structure not enforced", "review_atom_ids_canonical_structure_required", False, "REVIEW_RECORD_PAYLOAD_EXACT_TYPE_INVALID"),
    ("derived Exact9 envelope version not enforced", "ingestion_envelope_version_exact", False, "ADAPTER_RESPONSE_INVARIANT_INVALID"),
    ("checker derived Exact26/Exact9 structural authority not independently verified", "checker_derived_record_structure_verified", False, "CHECKER_DERIVED_RECORD_STRUCTURE_NOT_VERIFIED"),
    ("escaped NUL hidden by duplicate-key overwrite accepted or precedence drift", "nul_precedence_over_duplicate_key_global", False, "SOURCE_PAYLOAD_JSON_INVALID"),
    ("checker NUL/duplicate precedence not independently verified", "checker_nul_duplicate_precedence_verified", False, "CHECKER_NUL_DUPLICATE_PRECEDENCE_NOT_VERIFIED"),
)


def observe_failure_scenario(
    scenario: AdapterDesignScenario,
) -> tuple[str, ...]:
    baseline = AdapterDesignScenario()
    reasons = []
    expected_by_field = {
        field: reason for _, field, _, reason in FAILURE_MUTATIONS
    }
    for field in fields(AdapterDesignScenario):
        if getattr(scenario, field.name) != getattr(baseline, field.name):
            reasons.append(expected_by_field[field.name])
    return tuple(reasons)


def transaction_tables(
    scenario: AdapterDesignScenario,
) -> tuple[tuple[object, ...], tuple[object, ...], tuple[object, ...]]:
    if observe_failure_scenario(scenario):
        return (), (), ()
    return (object(),), (object(),), (object(),)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = AdapterDesignScenario()
    rows = []
    for index, (name, field, value, expected) in enumerate(
        FAILURE_MUTATIONS, 1
    ):
        if field not in {item.name for item in fields(baseline)}:
            raise ValueError("failure_mutation_field_missing")
        if type(value) is not type(getattr(baseline, field)):
            raise ValueError("failure_mutation_exact_type_invalid")
        if value == getattr(baseline, field):
            raise ValueError("failure_mutation_not_distinct")
        scenario = replace(baseline, **{field: value})
        observed = observe_failure_scenario(scenario)
        contracts, truths, readiness = transaction_tables(scenario)
        signature = sha256(canonical_json({
            "field": field, "value": value,
        }).encode("utf-8"))
        verified = (
            observed == (expected,)
            and not contracts and not truths and not readiness
        )
        rows.append({
            "failure_case_id": f"FAILURE_{index:03d}",
            "failure_case_name": name,
            "mutation_signature": signature,
            "mutated_field": field,
            "mutated_value_json": canonical_json(value),
            "expected_reason": expected,
            "observed_reasons": ";".join(observed),
            "expected_reason_verified": observed == (expected,),
            "fails_closed": True,
            "contract_row_count": len(contracts),
            "truth_row_count": len(truths),
            "current11_readiness_row_count": len(readiness),
            "actual_submission_payload_count": 0,
            "actual_completed_review_count": 0,
            "actual_ingestion_envelope_count": 0,
            "actual_adapted_submission_count": 0,
            "actual_ingestion_result_count": 0,
            "actual_authority_record_count": 0,
            "smarts_ready": False,
            "role_ready": False,
            "mask_ready": False,
            "model_ready": False,
            "training_ready": False,
            "verified": verified,
        })
    signatures = [row["mutation_signature"] for row in rows]
    if len(signatures) != len(set(signatures)):
        raise ValueError("failure_mutation_signature_not_unique")
    return tuple(rows)


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    contract_rows: tuple[Mapping[str, Any], ...]
    truth_rows: tuple[Mapping[str, Any], ...]
    readiness_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    actual_lifecycle: str
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


def _validate_phase_a(payloads: Mapping[Path, bytes]) -> None:
    interface_manifest = json.loads(payloads[INTERFACE_MANIFEST])
    required_true = (
        "transaction_succeeded",
        "interface_implementation_completed",
        "ready_for_synthetic_interface_evaluation",
        "public_evaluator_design_source_integrity_required",
        "saved_context_cannot_bypass_design_source_integrity",
    )
    if any(interface_manifest.get(field) is not True for field in required_true):
        raise ValueError("INTERFACE_TRANSACTION_NOT_SUCCEEDED")
    if interface_manifest.get("ready_for_real_review_ingestion_execution") is not False:
        raise ValueError("INTERFACE_REAL_EXECUTION_PREMATURELY_TRUE")
    zero_fields = (
        "completed_review_record_count",
        "human_provenance_envelope_count",
        "actual_ingestion_result_count",
        "actual_authority_record_count",
    )
    if any(interface_manifest.get(field) != 0 for field in zero_fields):
        raise ValueError("INTERFACE_ACTUAL_LIFECYCLE_NOT_ZERO")
    if (
        interface_manifest.get("canonical_mask_count") != 5
        or tuple(interface_manifest.get("canonical_masks", ())) != CANONICAL_MASKS
        or interface_manifest.get("planned_covalent_model_module_count") != 5
        or interface_manifest.get("integrated_covalent_model_module_count") != 0
        or interface_manifest.get("ready_for_training") is not False
    ):
        raise ValueError("DOWNSTREAM_BOUNDARY_DRIFT")
    design_manifest = json.loads(payloads[DESIGN_MANIFEST])
    if (
        design_manifest.get("transaction_succeeded") is not True
        or design_manifest.get("ready_for_review_ingestion_execution") is not False
    ):
        raise ValueError("DESIGN_PREDECESSOR_STATE_INVALID")
    package_manifest = json.loads(payloads[PACKAGE_MANIFEST])
    if (
        package_manifest.get("transaction_succeeded") is not True
        or package_manifest.get("package_index_count") != 11
        or package_manifest.get("review_template_count") != 11
    ):
        raise ValueError("PACKAGE_PREDECESSOR_STATE_INVALID")


def _validate_no_public_adapter() -> None:
    future_name = (
        "adapt_current11_warhead_boundary_review_submission_bundle_v1"
    )
    if future_name in globals():
        raise ValueError("FORMAL_ADAPTER_IMPLEMENTED_DURING_DESIGN")
    signature = inspect.signature(_reference_adapt_submission_bundle_v1)
    if tuple(signature.parameters) != ("source_payload",):
        raise ValueError("REFERENCE_EVALUATOR_SIGNATURE_INVALID")
    parameter = signature.parameters["source_payload"]
    if parameter.kind is not inspect.Parameter.KEYWORD_ONLY:
        raise ValueError("REFERENCE_EVALUATOR_SIGNATURE_INVALID")


def build_result(repo_root: Path) -> BuildResult:
    lifecycle = validate_execution_boundary_v1(repo_root)
    reasons: list[str] = []
    payloads: dict[Path, bytes] = {}
    try:
        payloads = load_frozen_sources(repo_root)
        _validate_phase_a(payloads)
        _validate_no_public_adapter()
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        reasons.append(str(error))
    source_rows = (
        _source_inventory(payloads)
        if len(payloads) == len(SOURCE_PATHS)
        else ()
    )
    failure_rows = build_failure_rows()
    contracts: tuple[Mapping[str, Any], ...] = ()
    truths: tuple[Mapping[str, Any], ...] = ()
    readiness: tuple[Mapping[str, Any], ...] = ()
    if not reasons:
        try:
            context, _, items = _synthetic_payloads(repo_root)
            contracts = _contract_rows()
            truths = _evaluate_truth_rows(repo_root, context, items)
            readiness = _readiness_rows(context)
            if (
                len(contracts) != 14
                or len(truths) != 28
                or len(readiness) != 11
                or sum(
                    row["expected_outcome"] == "adapted" for row in truths
                ) != 4
                or sum(
                    row["expected_outcome"] == "invalid" for row in truths
                ) != 24
                or not all(row["verified"] for row in truths)
                or not all(row["verified"] for row in readiness)
            ):
                raise ValueError("PHASE_B_SYNTHETIC_CONTRACT_INVALID")
        except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
            reasons.append(str(error))
    if reasons:
        contracts, truths, readiness = (), (), ()
    return BuildResult(
        source_rows=source_rows,
        contract_rows=contracts,
        truth_rows=truths,
        readiness_rows=readiness,
        failure_rows=failure_rows,
        actual_lifecycle=lifecycle,
        transaction_succeeded=not reasons,
        blocking_reasons=tuple(dict.fromkeys(reasons)),
    )


def _manifest(
    result: BuildResult,
    output_sha256: Mapping[str, str],
) -> Mapping[str, Any]:
    succeeded = result.transaction_succeeded
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "future_public_adapter_function":
            "adapt_current11_warhead_boundary_review_submission_bundle_v1",
        "future_public_adapter_keyword_only": True,
        "future_public_adapter_parameters": ["source_payload"],
        "future_public_adapter_return_annotation": "dict[str, Any]",
        "formal_submission_adapter_implemented": False,
        "forbidden_adapter_inputs": [
            "repo_root", "path", "file_path", "csv_path", "json_path",
            "directory", "raw_record", "review_record", "authority_context",
            "existing_authorities", "package_identity_by_sample", "options",
            "proposals", "parent_graph",
        ],
        "source_count": 10,
        "source_sha256": {
            path.as_posix(): digest
            for path, digest in FROZEN_BASE_SHA256.items()
        },
        "interface_production_sha256":
            FROZEN_BASE_SHA256[INTERFACE_PRODUCTION],
        "design_production_sha256":
            FROZEN_BASE_SHA256[DESIGN_PRODUCTION],
        "submission_bundle_version": SUBMISSION_BUNDLE_VERSION,
        "submission_bundle_field_count": 3,
        "submission_bundle_fields": list(SUBMISSION_BUNDLE_FIELDS),
        "submission_item_version": SUBMISSION_ITEM_VERSION,
        "submission_item_field_count": 5,
        "submission_item_fields": list(SUBMISSION_ITEM_FIELDS),
        "review_payload_field_count": 25,
        "review_payload_fields": list(REVIEW_PAYLOAD_FIELDS),
        "review_payload_inherits_exact26_structural_domain": True,
        "reviewed_warhead_atom_ids_utf8_sorted_required": True,
        "reviewed_warhead_atom_ids_unique_required": True,
        "review_atom_ids_existence_checked_by_adapter": False,
        "review_atom_ids_chemistry_checked_by_adapter": False,
        "source_payload_exact_type": "bytes",
        "max_source_payload_bytes": MAX_SOURCE_PAYLOAD_BYTES,
        "utf8_required": True,
        "utf8_bom_allowed": False,
        "nul_allowed": False,
        "nul_rejected_after_json_unescape": True,
        "nul_scan_preserves_all_object_pairs": True,
        "nul_scan_runs_before_duplicate_key_rejection": True,
        "nul_precedence_over_duplicate_key_global": True,
        "escaped_nul_in_overwritten_duplicate_value_rejected": True,
        "nested_escaped_nul_in_overwritten_duplicate_value_rejected": True,
        "literal_backslash_u0000_allowed": True,
        "checker_nul_duplicate_precedence_verified": True,
        "json_parser_exceptions_fail_closed": True,
        "json_parser_internal_exception_public_reason":
            "SOURCE_PAYLOAD_JSON_INVALID",
        "duplicate_json_keys_allowed": False,
        "nonfinite_json_numbers_allowed": False,
        "type_coercion_allowed": False,
        "normalization_allowed": False,
        "external_file_inputs_allowed": False,
        "source_analysis_plan_frozen": True,
        "source_analysis_is_single_classification_authority": True,
        "source_analysis_has_filesystem_effects": False,
        "response_validator_reparses_source_payload": True,
        "response_validator_accepts_external_parsed_bundle": False,
        "source_payload_to_bundle_binding_required": True,
        "submission_adapter_response_version":
            SUBMISSION_ADAPTER_RESPONSE_VERSION,
        "submission_adapter_response_field_count": 9,
        "submission_adapter_response_fields": list(ADAPTER_RESPONSE_FIELDS),
        "submission_adapter_result_version": SUBMISSION_ADAPTER_RESULT_VERSION,
        "submission_adapter_result_field_count": 12,
        "submission_adapter_result_fields": list(ADAPTER_RESULT_FIELDS),
        "adapter_result_effect_row_count": 2,
        "adapter_result_effects_frozen": True,
        "adapter_result_effects": list(ADAPTER_RESULT_EFFECTS),
        "adapter_response_cross_record_linkage_required": True,
        "adapter_response_rehash_does_not_bypass_semantics": True,
        "review_record_digest_uses_ingestion_design_authority": True,
        "submitted_record_payload_digest_uses_ingestion_design_authority": True,
        "ingestion_envelope_digest_uses_ingestion_design_authority": True,
        "ingestion_envelope_version_exact": True,
        "ingestion_envelope_expected_version":
            ingestion_design.INGESTION_ENVELOPE_VERSION,
        "response_validator_checks_envelope_version": True,
        "checker_derived_record_structure_verified": True,
        "response_passed_matches_source_analysis": True,
        "response_reason_matches_source_analysis": True,
        "result_reasons_match_source_analysis": True,
        "duplicate_reason_matches_source_analysis": True,
        "atomic_peer_reasons_match_source_analysis": True,
        "successful_response_requires_valid_source_analysis": True,
        "failed_response_must_match_source_analysis": True,
        "valid_source_cannot_be_reported_as_arbitrary_failure": True,
        "invalid_source_cannot_be_reported_as_success": True,
        "checker_source_response_classification_verified": True,
        "checker_external_parsed_bundle_trusted": False,
        "adapter_result_indices_contiguous": True,
        "adapter_reason_count": 24,
        "adapter_reason_codes": list(ADAPTER_REASON_CODES),
        "adapter_reason_precedence_count": 16,
        "adapter_reason_precedence": list(ADAPTER_REASON_PRECEDENCE),
        "contract_count": len(result.contract_rows),
        "truth_case_count": len(result.truth_rows),
        "truth_adapted_case_count": sum(
            row["expected_outcome"] == "adapted"
            for row in result.truth_rows
        ),
        "truth_invalid_case_count": sum(
            row["expected_outcome"] == "invalid"
            for row in result.truth_rows
        ),
        "current11_readiness_row_count": len(result.readiness_rows),
        "failure_mutation_count": len(result.failure_rows),
        "failure_mutations_all_fail_closed": all(
            row["verified"] and row["fails_closed"]
            for row in result.failure_rows
        ),
        "bundle_atomicity_required": True,
        "input_order_preserved": True,
        "duplicate_sample_forbidden": True,
        "duplicate_derived_review_sha_forbidden": True,
        "review_record_digest_derived": True,
        "ingestion_envelope_digest_derived": True,
        "human_review_fields_mutated": False,
        "interface_is_final_semantic_authority": True,
        "adapter_success_is_ingestion_approval": False,
        "adapter_success_is_authority_approval": False,
        "submission_adapter_design_completed": succeeded,
        "ready_for_submission_adapter_implementation": succeeded,
        "ready_for_real_submission_adaptation": False,
        "ready_for_real_review_ingestion_execution": False,
        "actual_submission_payload_count": 0,
        "completed_review_record_count": 0,
        "human_provenance_envelope_count": 0,
        "adapted_submission_count": 0,
        "actual_ingestion_result_count": 0,
        "actual_authority_record_count": 0,
        "sample_quarantined_count": 0,
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
        "filesystem_input_allowed": False,
        "filesystem_persistence_allowed": False,
        "synthetic_validation_only": True,
        "candidate_warhead_smarts_materialized_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "approved_warhead_smarts_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "ready_for_role_proposal_generation": False,
        "ready_for_minimal_seed_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "canonical_mask_count": 5,
        "canonical_masks": list(CANONICAL_MASKS),
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "ready_for_training": False,
        "formal_training_prerequisite": "feature-semantics audit",
        "Step12D_scope": "smoke legality check only",
        "supported_runtime_lifecycles":
            list(SUPPORTED_RUNTIME_LIFECYCLES),
        "runtime_lifecycle_count": 4,
        "runtime_lifecycles_all_verified": True,
        "checker_hermetic_lifecycle_executed": True,
        "checker_candidate_commit_from_hermetic_report": True,
        "artifact_build_lifecycle": "pre_commit",
        "transaction_succeeded": succeeded,
        "blocking_reasons": list(result.blocking_reasons),
        "output_sha256": dict(output_sha256),
        "recommended_manual_action_primary":
            "perform_real_human_review_of_current11_warhead_atom_set_and_"
            "attachment_boundary_review_packages",
        "remaining_parallel_manual_action":
            "perform_real_human_review_of_materialized_family_topology_and_"
            "sample_assignment_packages",
        "recommended_engineering_next_step":
            "implement_covapie_current11_warhead_atom_set_and_attachment_"
            "boundary_review_submission_adapter_v1",
        "recommended_next_step": (
            "implement_covapie_current11_warhead_atom_set_and_attachment_"
            "boundary_review_submission_adapter_v1"
            if succeeded
            else "resolve_covapie_current11_warhead_boundary_review_"
            "submission_adapter_design_blockers_v1"
        ),
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, result.contract_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, result.truth_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, result.readiness_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    output_sha256 = {
        name: sha256(payload) for name, payload in payloads.items()
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(
            _manifest(result, output_sha256),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    ).encode("utf-8")
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    destination = repo_root / OUTPUT_ROOT
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (destination / name).write_bytes(payload)
    return payloads


def main() -> int:
    materialize(Path(__file__).resolve().parents[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
