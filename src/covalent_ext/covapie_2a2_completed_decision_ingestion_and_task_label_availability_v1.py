"""Ingest the frozen 2A2 Exact4 human decision as deterministic metadata.

This additive owner consumes existing sample-level authority.  It does not
reinterpret D1-D6, create human or reusable chemistry authority, reconstruct
PRE state, reconcile global state, refresh the census, admit training data,
tensorize, execute a model, or update parameters.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import copy
import csv
from datetime import datetime
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


__all__ = (
    "TwoA2IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = (
    "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_SCHEMA_VERSION = "covapie_2a2_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_2a2_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_2a2_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_2a2_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_2a2_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_2a2_event_task_label_availability_v1.csv"
SUMMARY = "covapie_2a2_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_2a2_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

# Frozen after the source-derived projection is independently reviewed.
# These close derived metadata only; they are not human/scientific authority.
_EXPECTED_SNAPSHOT_SHA256_V1 = (
    "87cfffd1c9e2e82db6d9aeba2dfedc907b459d89c0160c50fb9fbddee7393000"
)
_EXPECTED_MATRIX_SHA256_V1 = (
    "f6533013dcb2eea5fcee579d906c7ab3009d1db8c9f2d9f906aca5ee0122f52b"
)
_EXPECTED_SUMMARY_SHA256_V1 = (
    "6c5a92910becab41a4e3af0317fa3438d6a682e1dac4d4ef1d4e48fe34773ea2"
)

FORMAL_ROOT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "2A2_COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6/"
    "formal-human-decision-v1"
)
FORMAL_DECISION_RELATIVE = FORMAL_ROOT / "2a2_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = FORMAL_ROOT / "validate_2a2_formal_human_decision_v1.py"
FORMAL_DECISION_SCHEMA = "covapie_2a2_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "0b0b98b70458e03581e4d858c72556bfab1eeb534b0d9718ec50bbc6737fddd5"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6"
EXPECTED_APPROVED_AT_UTC = "2026-08-30T07:29:33Z"
EXPECTED_ROLE_PROFILE = "STRICT_LINKER_PRESENT_V1"
AUTHORITY_SOURCE = "FORMAL_2A2_HUMAN_DECISION"
AUTHORITY_SCOPE = "2A2_EXACT4_SAMPLE_LEVEL_ONLY"

EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:3ORZ:A:CYS:148-:SG:E:2A2:SD",
        507, "A", "E", "covale1", 2.022434, "2.022434",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3ORZ:B:CYS:148-:SG:G:2A2:SD",
        508, "B", "G", "covale3", 2.025631, "2.025631",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3ORZ:C:CYS:148-:SG:I:2A2:SD",
        509, "C", "I", "covale6", 2.020764, "2.020764",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3ORZ:D:CYS:148-:SG:K:2A2:SD",
        510, "D", "K", "covale8", 2.024483, "2.024483",
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
WARHEAD_ROLE = ("SD",)
LINKER_ROLE = ("C1", "C15", "C16", "C17", "O18")
SCAFFOLD_ROLE = (
    "C20", "C21", "C23", "C24", "C25", "C26", "C27",
    "C28", "C29", "C30", "CL99", "N19", "N22",
)
HEAVY_ATOMS = tuple((*WARHEAD_ROLE, *LINKER_ROLE, *SCAFFOLD_ROLE))
BOUNDARY_BONDS = (
    {
        "aromatic_flag": "N", "atom_id_1": "C1", "atom_id_2": "SD",
        "bond_order": "SING", "role_1": "L", "role_2": "W",
    },
    {
        "aromatic_flag": "N", "atom_id_1": "C17", "atom_id_2": "N19",
        "bond_order": "SING", "role_1": "L", "role_2": "S",
    },
)
CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (
        4, "scaffold_plus_linker_plus_warhead", "C",
        ("scaffold", "linker", "warhead"), ("minimal_seed",),
    ),
)
STRICT_VALID_TASK_IDS = (0, 1, 2, 3, 4)

# (path, namespace, bytes, sha256, role, required_mode)
FORMAL_BINDINGS = (
    (
        FORMAL_DECISION_RELATIVE, "project_parent_relative", 26532,
        "f0b10505af55883a3a4305a637b2299d2d5e1a25ef9f8e979efaad361d7351bd",
        "2A2_FROZEN_REVISED1_FORMAL_HUMAN_DECISION", "0664",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE, "project_parent_relative", 69082,
        "855ec10d9a311bdbdc3185e6c83b7f7d272e810ebfcbd5aeb9a4230a0d870715",
        "2A2_FROZEN_REVISED1_FORMAL_VALIDATOR", "0664",
    ),
)
SEMANTIC_OWNER_BINDINGS = (
    (
        Path("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"),
        "repository_relative", 37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "PUBLISHED_ROLE_PROFILE_RUNTIME_OWNER", None,
    ),
    (
        Path("src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"),
        "repository_relative", 67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        "CANONICAL_ROLE_AND_TASK_SEMANTICS_OWNER", None,
    ),
)
PRECEDENT_BINDINGS = (
    (
        Path("src/covalent_ext/covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1.py"),
        "repository_relative", 82797,
        "59401b7f495c28e5173771a329705286f76b98a7a0cc921fe345f9e5fa2248aa",
        "ONE_F8_STRICT_DISULFIDE_EXCLUDE_SEMANTIC_PRECEDENT", None,
    ),
    (
        Path("data/derived/covalent_small/covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1/covapie_1f8_event_task_label_availability_v1.csv"),
        "repository_relative", 14662,
        "63520f56ddb1c9fa9f962fc79c009549897e18299139e6b160498ca48080fb30",
        "ONE_F8_STRICT_DISULFIDE_EXCLUDE_MATRIX_PRECEDENT", None,
    ),
    (
        Path("src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py"),
        "repository_relative", 77160,
        "c67c88f83e535fd4319425459b97dcfc22f90a3b617b5ddbf1e8f315e2de0525",
        "F24_LATEST_INGESTION_ARCHITECTURE_PRECEDENT", None,
    ),
    (
        Path("scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py"),
        "repository_relative", 15600,
        "d057ff1695f9797fd2c54f9c91737fde6edd7580c471759350d179bb807565a7",
        "F24_DUAL_PROFILE_CHECKER_PRECEDENT", None,
    ),
)
CENSUS_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_f24_v1"
)
CENSUS_BINDINGS = (
    (
        Path("src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_f24_v1.py"),
        "repository_relative", 64468,
        "9afb435cb5110c68946a4356482665b2325707bacc96754aca2fa54337a2022b",
        "CURRENT_F24_REFRESHED_CENSUS_OWNER", None,
    ),
    (
        CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_f24_v1.csv",
        "repository_relative", 527918,
        "0660614ee950828cbb468cc72fdb776b26a6257e144cbae5df2a6d2a2c8f9b74",
        "CURRENT_F24_REFRESHED_CENSUS_CSV", None,
    ),
    (
        CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_f24_v1.json",
        "repository_relative", 16992,
        "4a75f817138379c25fc67186b3316e400c0850ecbb2611fa8d8158860cf39c9b",
        "CURRENT_F24_REFRESHED_CENSUS_SUMMARY", None,
    ),
    (
        CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_manifest_with_f24_v1.json",
        "repository_relative", 44602,
        "eb8111311d984705d437f496e1cdd5e41899883203665d1f4b366c832bae3347",
        "CURRENT_F24_REFRESHED_CENSUS_MANIFEST", None,
    ),
)
RECONCILIATION_BINDINGS = (
    (
        Path("src/covalent_ext/covapie_completed_human_decision_reconciliation_with_f24_v1.py"),
        "repository_relative", 21089,
        "7ab2d47d247e6a342645b1a1b78352671d5d60a2902f1ef21fad9241a83ee325",
        "CURRENT_PUBLISHED_F24_RECONCILIATION_OWNER", None,
    ),
)


class TwoA2IngestionSafetyError(ValueError):
    """Raised when the exact 2A2 ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise TwoA2IngestionSafetyError(reason)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    )


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=header, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _strict_json(payload: bytes, label: str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("DUPLICATE_JSON_KEY:" + label + ":" + key)
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        _fail("NONFINITE_JSON_CONSTANT:" + label + ":" + value)

    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=unique,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TwoA2IngestionSafetyError("JSON_PARSE_FAILED:" + label) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _parse_utc(value: object) -> datetime:
    if type(value) is not str:
        _fail("APPROVED_AT_UTC_TYPE_INVALID")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise TwoA2IngestionSafetyError("APPROVED_AT_UTC_INVALID") from error
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        _fail("APPROVED_AT_UTC_NONCANONICAL")
    return parsed


def _semantic_digest(document: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(document))
    digest = clone.pop("formal_semantic_canonical_sha256", None)
    if type(digest) is not str or len(digest) != 64:
        _fail("FORMAL_SEMANTIC_DIGEST_FIELD_INVALID")
    return _sha(_canonical_json(clone))


def _resolve_binding_path(
    repo_root: Path,
    binding: tuple[Path, str, int, str, str, str | None],
    overrides: Mapping[Path, Path],
) -> Path:
    relative, namespace, _count, _digest, _role, _mode = binding
    if relative in overrides:
        return Path(overrides[relative])
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace == "project_parent_relative":
        return repo_root.parent / relative
    _fail("SOURCE_NAMESPACE_INVALID:" + namespace)


def _binding_record(
    binding: tuple[Path, str, int, str, str, str | None]
) -> dict[str, object]:
    relative, namespace, count, digest, role, mode = binding
    record: dict[str, object] = {
        "path": relative.as_posix(),
        "path_namespace": namespace,
        "byte_count": count,
        "sha256": digest,
        "sha256_scope": "file_bytes",
        "source_role": role,
    }
    if mode is not None:
        record["mode"] = mode
    return record


def _expected_binding_records(
    bindings: Sequence[tuple[Path, str, int, str, str, str | None]],
) -> list[dict[str, object]]:
    return [_binding_record(binding) for binding in bindings]


def _verify_binding(
    repo_root: Path,
    binding: tuple[Path, str, int, str, str, str | None],
    overrides: Mapping[Path, Path],
) -> bytes:
    relative, _namespace, count, digest, role, mode = binding
    path = _resolve_binding_path(repo_root, binding, overrides)
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise TwoA2IngestionSafetyError("SOURCE_MISSING:" + role) from error
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        _fail("SOURCE_NOT_REGULAR:" + role)
    payload = path.read_bytes()
    if len(payload) != count:
        _fail("SOURCE_BYTE_COUNT_DRIFT:" + role)
    if _sha(payload) != digest:
        _fail("SOURCE_SHA256_DRIFT:" + role)
    if mode is not None and f"{stat.S_IMODE(metadata.st_mode):04o}" != mode:
        _fail("SOURCE_MODE_DRIFT:" + role)
    return payload


def _verify_bindings(
    repo_root: Path,
    bindings: Sequence[tuple[Path, str, int, str, str, str | None]],
    overrides: Mapping[Path, Path],
) -> dict[Path, bytes]:
    return {
        binding[0]: _verify_binding(repo_root, binding, overrides)
        for binding in bindings
    }


def _verify_formal_evidence_bindings(
    repo_root: Path, records: object
) -> tuple[list[dict[str, object]], dict[Path, bytes]]:
    if type(records) is not list or len(records) != 11:
        _fail("FORMAL_EVIDENCE_BINDING_COUNT_INVALID")
    payloads: dict[Path, bytes] = {}
    normalized: list[dict[str, object]] = []
    for record in records:
        if type(record) is not dict:
            _fail("FORMAL_EVIDENCE_BINDING_NOT_OBJECT")
        required = {
            "path", "path_namespace", "byte_count", "mode", "sha256",
            "source_role", "regular_file", "non_symlink",
        }
        if set(record) != required:
            _fail("FORMAL_EVIDENCE_BINDING_SCHEMA_INVALID")
        if (
            record.get("path_namespace") != "project_parent_relative"
            or record.get("regular_file") is not True
            or record.get("non_symlink") is not True
        ):
            _fail("FORMAL_EVIDENCE_BINDING_BOUNDARY_INVALID")
        relative = Path(str(record["path"]))
        path = repo_root.parent / relative
        if not path.is_file() or path.is_symlink():
            _fail("FORMAL_EVIDENCE_SOURCE_NOT_REGULAR")
        payload = path.read_bytes()
        if (
            len(payload) != record.get("byte_count")
            or _sha(payload) != record.get("sha256")
            or f"{stat.S_IMODE(path.stat().st_mode):04o}" != record.get("mode")
        ):
            _fail("FORMAL_EVIDENCE_SOURCE_DRIFT:" + str(record.get("source_role")))
        payloads[relative] = payload
        normalized.append(copy.deepcopy(record))
    if [row["source_role"] for row in normalized[:8]] != [
        "machine_evidence_manifest", "exact4_event_review",
        "graph_and_role_candidates", "human_review_guide",
        "unsigned_human_decision_template", "preparation_package_validator",
        "non_authoritative_human_review_scientific_preview",
        "human_review_scientific_preview_validator",
    ]:
        _fail("FORMAL_PREPARATION_OR_PREVIEW_BINDING_ORDER_DRIFT")
    return normalized, payloads


def _run_formal_validator(path: Path) -> dict[str, object]:
    # The frozen CLI intentionally requires a globally clean repository.  A live
    # Exact7 candidate is necessarily untracked, so execute the validator's own
    # strict source-derived package gate while the ingestion owner separately
    # binds both Exact2 files by bytes, mode, and SHA256.  The unchanged CLI is
    # run before candidate creation and again in a clean detached verification.
    code = """
import importlib.util
import json
from pathlib import Path
import sys

validator = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location("frozen_2a2_formal_validator", validator)
if spec is None or spec.loader is None:
    raise SystemExit(91)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
project_parent, repo_root = module.resolve_roots()
document = module.strict_json(
    (validator.parent / module.FORMAL_FILE).read_bytes(), module.FORMAL_FILE
)
approval = document.get("human_approval")
if type(approval) is not dict:
    raise SystemExit(92)
approved_at = module.parse_approved_at_utc(approval.get("approved_at_utc"))
expected = module.build_expected(project_parent, repo_root, approved_at)
report = module.validate_package(validator.parent, expected)
report["files"] = module.file_summary(validator.parent)
print(json.dumps(report, ensure_ascii=False, sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)], cwd=path.parent, check=False,
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if result.returncode != 0:
        _fail("FROZEN_FORMAL_VALIDATOR_FAILED")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise TwoA2IngestionSafetyError(
            "FROZEN_FORMAL_VALIDATOR_OUTPUT_INVALID"
        ) from error
    if (
        type(report) is not dict
        or report.get("status") != "PASS"
        or report.get("exact_file_count") != 2
        or report.get("formal_human_decision_valid") is not True
        or report.get("human_decision_created") is not True
        or report.get("formal_authority_created") is not True
        or report.get("ingestion_started") is not False
        or report.get("ready_for_training") is not False
    ):
        _fail("FROZEN_FORMAL_VALIDATOR_REPORT_INVALID")
    files = report.get("files")
    if type(files) is not list or [row.get("sha256") for row in files] != [
        FORMAL_BINDINGS[0][3], FORMAL_BINDINGS[1][3]
    ]:
        _fail("FROZEN_FORMAL_VALIDATOR_FILE_REPORT_INVALID")
    return report


def _validate_formal_decision_v1(formal: Mapping[str, Any]) -> None:
    if type(formal) is not dict:
        _fail("FORMAL_DOCUMENT_TYPE_INVALID")
    if (
        formal.get("schema_version") != FORMAL_DECISION_SCHEMA
        or formal.get("record_role") != FORMAL_RECORD_ROLE
        or formal.get("formal_semantic_canonical_sha256")
        != FORMAL_SEMANTIC_CANONICAL_SHA256
        or _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256
    ):
        _fail("FORMAL_SCHEMA_ROLE_OR_DIGEST_DRIFT")
    for key, expected in (
        ("approved", True), ("unsigned", False),
        ("decision_finalized", True), ("human_review_completed", True),
        ("human_decision_created", True), ("formal_authority_created", True),
    ):
        if formal.get(key) is not expected:
            _fail("FORMAL_LIFECYCLE_DRIFT:" + key)
    approval = formal.get("human_approval")
    if type(approval) is not dict:
        _fail("FORMAL_APPROVAL_MISSING")
    for key, expected in (
        ("reviewer_id", "fmx"), ("attestor_id", "fmx"),
        ("approved_at_utc", EXPECTED_APPROVED_AT_UTC),
        ("authorization_source", "EXTERNAL_EXPLICIT_HUMAN_APPROVAL"),
        ("human_choices_externally_authorized", True),
        ("machine_approval_claimed", False),
        ("chat_cryptographic_verification_claimed", False),
        ("D1_task_relevance", "RELEVANT"), ("D2_chemistry", "POSITIVE"),
        ("D3_reactive_pair", "CONFIRM_OBSERVED_PAIR"),
        ("D4_role_partition", "SELECT_CANDIDATE_4"),
        ("D5_training_use", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("human_selected_role_candidate_index_0based", 4),
    ):
        if approval.get(key) != expected:
            _fail("FORMAL_APPROVAL_OR_D1_D5_DRIFT:" + key)
    _parse_utc(approval["approved_at_utc"])
    context = formal.get("human_approved_context")
    if (
        type(context) is not dict
        or type(approval.get("D6_scientific_context")) is not str
        or not approval["D6_scientific_context"]
        or context.get("D6_scientific_context")
        != approval["D6_scientific_context"]
        or context.get("formal_D6_equals_preview_proposed_D6") is not True
        or context.get("exact_text_frozen") is not True
    ):
        _fail("FORMAL_D6_DRIFT")
    identity = formal.get("identity")
    if type(identity) is not dict or (
        identity.get("review_unit_id") != EXPECTED_REVIEW_UNIT_ID
        or identity.get("ligand_component_id") != "2A2"
        or identity.get("exact_event_count") != 4
        or identity.get("unique_event_count") != 4
        or identity.get("duplicate_event_count") != 0
        or identity.get("missing_event_count") != 0
        or identity.get("extra_event_count") != 0
        or identity.get("canonical_event_ids") != list(EXPECTED_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(EXPECTED_RANKS)
        or identity.get("pdb_ids") != ["3ORZ"]
        or identity.get("event_contexts_collapsed") is not False
    ):
        _fail("FORMAL_EXACT4_IDENTITY_DRIFT")
    events = formal.get("event_level_human_decisions")
    if type(events) is not list or len(events) != 4:
        _fail("FORMAL_EVENT_COUNT_DRIFT")
    if len({row.get("canonical_event_id") for row in events if type(row) is dict}) != 4:
        _fail("FORMAL_EVENT_DUPLICATE")
    for event, expected in zip(events, EXPECTED_EVENTS, strict=True):
        if type(event) is not dict:
            _fail("FORMAL_EVENT_NOT_OBJECT")
        required = {
            "canonical_event_id": expected[0], "scaleup_rank": expected[1],
            "pdb_id": "3ORZ", "model_number": 1,
            "protein_asym": expected[2], "cys_residue_id": "CYS:148-",
            "protein_reactive_atom": "SG", "ligand_asym": expected[3],
            "ligand_component_id": "2A2", "ligand_reactive_atom": "SD",
            "selected_connection_id": expected[4],
            "POST_distance_angstrom": expected[5],
            "explicit_covalent_evidence": True,
            "distance_only_inference_used": False,
            "full_POST_coordinate_evidence": True,
            "CCD_graph_complete": True,
            "D1_task_relevance": "RELEVANT", "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_partition": "SELECT_CANDIDATE_4",
            "D5_training_use": "EXCLUDE_FROM_TRAINING_ONLY",
            "reactive_pair_human_authoritative": True,
            "role_partition_human_authoritative": True,
            "formal_training_admitted": False,
        }
        for key, value in required.items():
            if event.get(key) != value:
                _fail("FORMAL_EVENT_DRIFT:" + key)
    pair = formal.get("reactive_pair_human_decision")
    if type(pair) is not dict or (
        pair.get("D3_human_choice") != "CONFIRM_OBSERVED_PAIR"
        or pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_reactive_atom") != "SD"
        or pair.get("reactive_pair_human_authoritative") is not True
        or pair.get("reactive_pair_human_authoritative_event_count") != 4
        or pair.get("cross_sample_reusable_pair_authority_created") is not False
    ):
        _fail("FORMAL_REACTIVE_PAIR_DRIFT")
    role = formal.get("selected_role_partition")
    if type(role) is not dict or (
        role.get("D4_human_choice") != "SELECT_CANDIDATE_4"
        or role.get("selected_candidate_index_0based") != 4
        or role.get("human_selected_role_candidate_index_0based") != 4
        or role.get("human_selected") is not True
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("role_profile") != EXPECTED_ROLE_PROFILE
        or role.get("warhead_role_atom_ids") != list(WARHEAD_ROLE)
        or role.get("linker_atom_ids") != list(LINKER_ROLE)
        or role.get("scaffold_atom_ids") != list(SCAFFOLD_ROLE)
        or role.get("boundary_bonds") != list(BOUNDARY_BONDS)
        or role.get("partition_heavy_atom_count") != 19
        or role.get("partition_pairwise_disjoint") is not True
        or role.get("partition_exhaustive") is not True
        or role.get("warhead_role_connected") is not True
        or role.get("linker_role_connected") is not True
        or role.get("scaffold_role_connected") is not True
        or role.get("applicable_task_ids") != [0, 1, 2, 3, 4]
    ):
        _fail("FORMAL_SELECTED_ROLE_DRIFT")
    canonical = formal.get("canonical_Exact5_and_sample_applicability")
    expected_tasks = [
        {
            "display_alias": alias, "semantic_name": semantic,
            "structurally_applicable_to_2A2": True, "task_id": task_id,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    if type(canonical) is not dict or (
        canonical.get("global_canonical_task_count") != 5
        or canonical.get("B3_present") is not True
        or canonical.get("sixth_task_present") is not False
        or canonical.get("sample_applicable_task_ids") != [0, 1, 2, 3, 4]
        or canonical.get("tasks") != expected_tasks
    ):
        _fail("FORMAL_EXACT5_DRIFT")
    chemical = formal.get("chemical_warhead_boundary")
    if type(chemical) is not dict or (
        chemical.get("chemical_warhead_atom_ids") is not None
        or chemical.get("chemical_warhead_human_authoritative") is not False
        or chemical.get("chemical_warhead_status")
        != "PRE_DISULFIDE_REAGENT_NOT_FULLY_REPRESENTED"
        or chemical.get("W_SD_is_sample_level_canonical_role_region") is not True
        or chemical.get("W_SD_is_complete_PRE_chemical_warhead_definition")
        is not False
    ):
        _fail("FORMAL_CHEMICAL_WARHEAD_BOUNDARY_DRIFT")
    pre = formal.get("experimental_context_and_PRE_boundary")
    if type(pre) is not dict or (
        pre.get("engineered_target_site") != "PDK1_T148C"
        or pre.get("native_cysteine_site") is not False
        or pre.get("disulfide_trapping_context") is not True
        or pre.get("observed_retained_fragment_context") is not True
        or pre.get("complete_PRE_disulfide_reagent_authority") is not False
        or pre.get("observed_graph_is_complete_authoritative_PRE_reagent")
        is not False
        or pre.get("PRE_topology_authority_created") is not False
        or pre.get("PRE_geometry_authority_created") is not False
        or pre.get("PRE_reconstruction_performed") is not False
        or pre.get("POST_to_PRE_copy_performed") is not False
        or pre.get("PRE_zero_fill_performed") is not False
    ):
        _fail("FORMAL_PRE_BOUNDARY_DRIFT")
    post = formal.get("POST_evidence_boundary")
    if post != {
        "POST_geometry_training_authority_created": False,
        "POST_geometry_training_target_created": False,
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
    }:
        _fail("FORMAL_POST_BOUNDARY_DRIFT")
    if formal.get("minimal_seed") != {
        "minimal_seed_atom_ids": None,
        "minimal_seed_authority_created": False,
    }:
        _fail("FORMAL_MINIMAL_SEED_DRIFT")
    training = formal.get("training_use_human_decision")
    if type(training) is not dict or (
        training.get("D5_human_choice") != "EXCLUDE_FROM_TRAINING_ONLY"
        or training.get("task_relevance") != "RELEVANT"
        or training.get("chemistry") != "POSITIVE"
        or training.get("human_training_excluded") is not True
        or training.get("training_use_allowed") is not False
        or training.get("candidate_for_future_training_admission") is not False
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_materialization_allowed_now") is not False
        or training.get("formal_split_authority_created") is not False
        or training.get("tensor_target_created") is not False
        or training.get("current_runtime_model_usable") is not False
        or training.get("parameter_update_authorization") is not False
    ):
        _fail("FORMAL_TRAINING_BOUNDARY_DRIFT")
    reusable = formal.get("reusable_authority_boundary")
    if type(reusable) is not dict or any(
        reusable.get(key) is not False
        for key in (
            "reaction_family_authority_created", "warhead_rule_authority_created",
            "warhead_type_authority_created", "reusable_chemistry_authority_created",
            "reusable_pair_authority_created", "reusable_role_authority_created",
            "generic_all_disulfide_trapping_EXCLUDE_rule_created",
        )
    ):
        _fail("FORMAL_REUSABLE_AUTHORITY_DRIFT")
    precedent = formal.get("published_1F8_same_context_precedent")
    if type(precedent) is not dict or (
        "2A2_independent_human_review_still_required" in precedent
        or precedent.get("precedent_did_not_substitute_for_2A2_independent_review")
        is not True
        or precedent.get("2A2_independent_human_review_completed") is not True
        or precedent.get("precedent_use") != "SAME_EXPERIMENTAL_CONTEXT_PRECEDENT"
        or precedent.get("generic_disulfide_trapping_exclusion_rule_created")
        is not False
        or precedent.get("reusable_rule_created") is not False
    ):
        _fail("FORMAL_PRECEDENT_STATE_DRIFT")
    census = formal.get("current_published_census_provenance")
    if census != {
        "2A2_current_status": "CURRENTLY_UNREVIEWED",
        "2A2_human_review_completed": False,
        "HEAD": "ff5afe36d915743be54871a3b3aff4f5eb9ff1ae",
        "current_census_modified_by_this_step": False,
        "future_candidate": 27, "pair_authority": 108,
        "positive": 108, "relevant": 109, "role_authority": 108,
        "training_EXCLUDE": 64, "training_INCLUDE": 44,
    }:
        _fail("FORMAL_CURRENT_CENSUS_PROVENANCE_DRIFT")


def _validate_published_runtime(
    formal: Mapping[str, Any], evidence_payloads: Mapping[Path, bytes]
) -> dict[str, object]:
    graph_path = next(
        path for path in evidence_payloads
        if path.name == "2a2_graph_and_role_candidates_v1.json"
    )
    graph = _strict_json(evidence_payloads[graph_path], "2A2_GRAPH")
    atoms = tuple(row["atom_id"] for row in graph.get("heavy_atoms", []))
    bonds = tuple(
        (row["atom_id_1"], row["atom_id_2"], row["bond_order"])
        for row in graph.get("heavy_bonds", [])
    )
    role = formal["selected_role_partition"]
    runtime = importlib.import_module(
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
    )
    result = runtime.validate_role_profile_v1(
        role_profile=role["role_profile"], retained_heavy_atoms=atoms,
        scaffold_atoms=role["scaffold_atom_ids"],
        linker_atoms=role["linker_atom_ids"],
        warhead_atoms=role["warhead_role_atom_ids"], reactive_atom_id="SD",
        explicit_graph_bonds=bonds,
    )
    if (
        result.valid is not True or tuple(result.reasons) != ()
        or result.role_profile != EXPECTED_ROLE_PROFILE
        or result.warhead_count != 1 or result.linker_count != 5
        or result.scaffold_count != 13
        or result.linker_warhead_boundary_applicable is not True
        or result.scaffold_linker_boundary_applicable is not True
        or result.direct_scaffold_warhead_boundary_applicable is not False
    ):
        _fail("PUBLISHED_RUNTIME_ROLE_VALIDATION_FAILED")
    return {
        "validator": "validate_role_profile_v1", "valid": True,
        "reasons": [], "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_count": 1, "linker_count": 5, "scaffold_count": 13,
        "applicable_task_ids": [0, 1, 2, 3, 4],
    }


def _current_census_boundary(
    verified: Mapping[Path, bytes]
) -> dict[str, object]:
    csv_path = CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_f24_v1.csv"
    summary_path = CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_f24_v1.json"
    try:
        rows = list(csv.DictReader(io.StringIO(verified[csv_path].decode("utf-8"))))
        summary = _strict_json(verified[summary_path], "CURRENT_F24_CENSUS_SUMMARY")
    except UnicodeDecodeError as error:
        raise TwoA2IngestionSafetyError("CURRENT_CENSUS_PARSE_FAILED") from error
    target = [row for row in rows if row.get("ligand_component_id") == "2A2"]
    if (
        len(rows) != 1000 or len(target) != 4
        or tuple(row.get("canonical_event_id") for row in target) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in target) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_2A2_EXACT4_DRIFT")
    expected_cells = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false", "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    if any(
        any(row.get(key) != value for key, value in expected_cells.items())
        for row in target
    ):
        _fail("CURRENT_CENSUS_2A2_PRIOR_STATE_DRIFT")
    task_counts = {
        row["display_alias"]: row["structurally_applicable_authoritative_role_count"]
        for row in summary["canonical_exact5"]["tasks"]
    }
    counts = {
        "positive": summary["chemistry"]["POSITIVE"]["count"],
        "relevant": summary["task_relevance"]["RELEVANT"]["count"],
        "training_INCLUDE": summary["training_use"]["INCLUDE"]["count"],
        "training_EXCLUDE": summary["training_use"]["EXCLUDE_FROM_TRAINING_ONLY"]["count"],
        "future_candidates": summary["training_stage"]["future_training_admission_candidate_count"],
        "pair_sample_authority": summary["reactive_pair"]["sample_level_authoritative_pair_count"],
        "role_sample_authority": summary["role"]["role_partition_sample_authoritative_count"],
        "strict_profile": summary["role"]["role_profile_counts"][EXPECTED_ROLE_PROFILE],
        "direct_profile": summary["role"]["role_profile_counts"]["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"],
        "A": task_counts.get("A"), "B": task_counts.get("B"),
        "B2": task_counts.get("B2"), "B3": task_counts.get("B3"),
        "C": task_counts.get("C"),
    }
    expected_counts = {
        "positive": 108, "relevant": 109, "training_INCLUDE": 44,
        "training_EXCLUDE": 64, "future_candidates": 27,
        "pair_sample_authority": 108, "role_sample_authority": 108,
        "strict_profile": 48, "direct_profile": 60,
        "A": 108, "B": 48, "B2": 48, "B3": 108, "C": 108,
    }
    if counts != expected_counts:
        _fail("CURRENT_CENSUS_COUNTS_OR_EXACT5_DRIFT")
    authority = summary.get("authority_boundary", {})
    if (
        authority.get("next_priority_review_ligand") != "2A2"
        or authority.get("next_priority_review_unit") != EXPECTED_REVIEW_UNIT_ID
        or authority.get("next_priority_review_event_count") != 4
    ):
        _fail("CURRENT_CENSUS_PRIORITY_HEAD_DRIFT")
    return {
        **counts, "current_2A2_status": "CURRENTLY_UNREVIEWED",
        "current_2A2_human_review_completed": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False, "priority_queue_updated": False,
    }


def _future_census_informational(
    current: Mapping[str, object]
) -> dict[str, object]:
    projected = {
        "positive": current["positive"] + 4,
        "relevant": current["relevant"] + 4,
        "training_INCLUDE": current["training_INCLUDE"],
        "training_EXCLUDE": current["training_EXCLUDE"] + 4,
        "future_candidates": current["future_candidates"],
        "pair_sample_authority": current["pair_sample_authority"] + 4,
        "role_sample_authority": current["role_sample_authority"] + 4,
        "strict_profile": current["strict_profile"] + 4,
        "direct_profile": current["direct_profile"],
        "A": current["A"] + 4, "B": current["B"] + 4,
        "B2": current["B2"] + 4, "B3": current["B3"] + 4,
        "C": current["C"] + 4,
    }
    expected = {
        "positive": 112, "relevant": 113, "training_INCLUDE": 44,
        "training_EXCLUDE": 68, "future_candidates": 27,
        "pair_sample_authority": 112, "role_sample_authority": 112,
        "strict_profile": 52, "direct_profile": 60,
        "A": 112, "B": 52, "B2": 52, "B3": 112, "C": 112,
    }
    if projected != expected:
        _fail("FUTURE_CENSUS_INFORMATIONAL_DELTA_INVALID")
    return {
        "status": "INFORMATIONAL_ONLY", "current_global_state": False,
        "materialized_this_step": False, **projected,
    }


def _reconciliation_informational(repo_root: Path) -> dict[str, object]:
    module = importlib.import_module(
        "covalent_ext.covapie_completed_human_decision_reconciliation_with_f24_v1"
    )
    result = module.reconcile_real_completed_human_decisions_with_f24_v1(repo_root)
    current = dict(result.review_summary)
    expected_current = {
        "universe_event_count": 338, "universe_review_unit_count": 131,
        "completed_positive_event_count": 91,
        "completed_positive_unit_count": 12,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 115,
        "completed_total_unit_count": 16,
        "in_progress_event_count": 0, "in_progress_unit_count": 0,
        "unreviewed_event_count": 223, "unreviewed_unit_count": 115,
    }
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    if current != expected_current or dispositions != {
        "INCLUDE": 27, "EXCLUDE_FROM_TRAINING_ONLY": 64
    }:
        _fail("CURRENT_F24_RECONCILIATION_BOUNDARY_DRIFT")
    future = {
        "completed_positive_event_count": current["completed_positive_event_count"] + 4,
        "completed_positive_unit_count": current["completed_positive_unit_count"] + 1,
        "completed_negative_event_count": current["completed_negative_event_count"],
        "completed_negative_unit_count": current["completed_negative_unit_count"],
        "completed_total_event_count": current["completed_total_event_count"] + 4,
        "completed_total_unit_count": current["completed_total_unit_count"] + 1,
        "unreviewed_event_count": current["unreviewed_event_count"] - 4,
        "unreviewed_unit_count": current["unreviewed_unit_count"] - 1,
        "in_progress_event_count": 0, "in_progress_unit_count": 0,
        "normalized_INCLUDE": dispositions["INCLUDE"],
        "normalized_EXCLUDE_FROM_TRAINING_ONLY":
            dispositions["EXCLUDE_FROM_TRAINING_ONLY"] + 4,
    }
    expected_future = {
        "completed_positive_event_count": 95, "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24, "completed_negative_unit_count": 4,
        "completed_total_event_count": 119, "completed_total_unit_count": 17,
        "unreviewed_event_count": 219, "unreviewed_unit_count": 114,
        "in_progress_event_count": 0, "in_progress_unit_count": 0,
        "normalized_INCLUDE": 27,
        "normalized_EXCLUDE_FROM_TRAINING_ONLY": 68,
    }
    if future != expected_future:
        _fail("FUTURE_RECONCILIATION_INFORMATIONAL_DELTA_INVALID")
    return {
        "status": "INFORMATIONAL_ONLY", "reconciled_this_step": False,
        "materialized_this_step": False, "current_published": current,
        "future_after_reconciliation": future,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
    execute_formal_validator: bool = True,
) -> dict[str, object]:
    """Bind and independently validate the frozen authority and owners."""

    repo_root = Path(repo_root).resolve()
    overrides = dict(repository_path_overrides or {})
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    formal_payloads = _verify_bindings(repo_root, FORMAL_BINDINGS, overrides)
    _verify_bindings(repo_root, SEMANTIC_OWNER_BINDINGS, overrides)
    _verify_bindings(repo_root, PRECEDENT_BINDINGS, overrides)
    census_payloads = _verify_bindings(repo_root, CENSUS_BINDINGS, overrides)
    _verify_bindings(repo_root, RECONCILIATION_BINDINGS, overrides)
    formal = _strict_json(
        formal_payloads[FORMAL_DECISION_RELATIVE], "2A2_FORMAL_DECISION"
    )
    _validate_formal_decision_v1(formal)
    evidence = formal.get("evidence_provenance")
    if type(evidence) is not dict:
        _fail("FORMAL_EVIDENCE_PROVENANCE_MISSING")
    evidence_bindings, evidence_payloads = _verify_formal_evidence_bindings(
        repo_root, evidence.get("source_bindings")
    )
    runtime_result = _validate_published_runtime(formal, evidence_payloads)
    validator_path = _resolve_binding_path(repo_root, FORMAL_BINDINGS[1], overrides)
    validator_result = (
        _run_formal_validator(validator_path)
        if execute_formal_validator
        else {
            "status": "PASS", "exact_file_count": 2,
            "formal_human_decision_valid": True,
            "human_decision_created": True, "formal_authority_created": True,
            "ingestion_started": False, "ready_for_training": False,
        }
    )
    current_census = _current_census_boundary(census_payloads)
    return {
        "formal": formal,
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "formal_evidence_bindings": evidence_bindings,
        "semantic_owner_bindings": _expected_binding_records(SEMANTIC_OWNER_BINDINGS),
        "precedent_bindings": _expected_binding_records(PRECEDENT_BINDINGS),
        "current_census_bindings": _expected_binding_records(CENSUS_BINDINGS),
        "current_reconciliation_bindings": _expected_binding_records(RECONCILIATION_BINDINGS),
        "formal_validator_result": validator_result,
        "published_runtime_result": runtime_result,
        "current_published_census_boundary": current_census,
        "future_census_informational": _future_census_informational(current_census),
        "reconciliation_informational": _reconciliation_informational(repo_root),
    }


def _canonical_task_contract() -> dict[str, object]:
    applicability = [
        {
            "task_id": task_id, "semantic_long_name": semantic,
            "display_alias": alias, "structurally_applicable": True,
            "role_profile": EXPECTED_ROLE_PROFILE,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    return {
        "global_canonical_tasks": [
            {
                "task_id": task_id, "semantic_long_name": semantic,
                "display_alias": alias, "generated_roles": list(generated),
                "fixed_or_seed_roles": list(fixed),
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5, "B3_present": True,
        "sixth_task_present": False, "canonical_vocabulary_changed": False,
        "strict_profile_applicable_task_ids": [0, 1, 2, 3, 4],
        "strict_profile_applicable_task_count": 5,
        "task_applicability": applicability,
    }


def _role_projection(formal: Mapping[str, Any]) -> dict[str, object]:
    role = formal["selected_role_partition"]
    return {
        "D4_human_choice": "SELECT_CANDIDATE_4",
        "selected_candidate_index_0based": 4,
        "human_selected": True, "machine_selected": False,
        "machine_recommended": False, "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
        "linker_atom_ids": list(LINKER_ROLE),
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "boundary_bonds": copy.deepcopy(list(BOUNDARY_BONDS)),
        "partition_heavy_atom_count": 19, "partition_pairwise_disjoint": True,
        "partition_exhaustive": True, "warhead_connected": True,
        "linker_connected": True, "scaffold_connected": True,
        "applicable_task_ids": [0, 1, 2, 3, 4],
        "chemical_warhead_atom_ids": None,
        "chemical_warhead_human_authoritative": False,
        "chemical_warhead_status": formal["chemical_warhead_boundary"]["chemical_warhead_status"],
        "legacy_warhead_atoms_json_semantics":
            "CANONICAL_ROLE_PARTITION_WARHEAD_REGION_NOT_COMPLETE_PRE_CHEMICAL_WARHEAD",
    }


def _training_boundary() -> dict[str, object]:
    return {
        "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
        "event_training_use_human_decision_available": True,
        "human_training_excluded": True, "training_use_allowed": False,
        "training_use_include": False,
        "formal_future_training_admission_candidate": None,
        "candidate_for_future_training_admission": False,
        "future_training_candidate_derived_by_ingestion": False,
        "future_training_candidate_is_training_admission": False,
        "training_admitted": False, "training_admission_created": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False, "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False, "ready_for_training": False,
    }


def _geometry_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_available": True, "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_created": False,
        "POST_geometry_training_target_created": False,
        "PRE_topology_authority_available": False,
        "PRE_geometry_authority_available": False,
        "PRE_reconstruction_performed": False,
        "POST_to_PRE_copy_performed": False, "PRE_zero_fill_performed": False,
        "complete_PRE_disulfide_reagent_authority_available": False,
        "observed_graph_is_complete_authoritative_PRE_reagent": False,
    }


def _reusable_boundary() -> dict[str, object]:
    return {
        "reaction_family_target_available": False,
        "warhead_rule_target_available": False,
        "warhead_type_target_available": False,
        "reusable_chemistry_authority_available": False,
        "reusable_pair_authority_available": False,
        "reusable_role_authority_available": False,
        "generic_disulfide_exclusion_rule_created": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "snapshot_created_by_ingestion": True,
        "snapshot_is_new_human_authority": False,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "formal_human_decision_modified": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "chemical_warhead_authority_created": False,
        "minimal_seed_authority_created": False,
        "PRE_topology_authority_created": False,
        "PRE_geometry_authority_created": False,
        "POST_geometry_training_authority_created": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False, "priority_queue_updated": False,
        "training_admission_created": False, "training_admitted": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False, "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False, "ready_for_training": False,
        "2A2_reconciliation_started": False,
        "2A2_global_census_refresh_started": False,
        "2A2_priority_queue_refresh_started": False,
        "2A2_training_admission_started": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "Step12D":
            "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "commit_performed": False, "push_performed": False,
    }


def _event_projection(event: Mapping[str, Any]) -> dict[str, object]:
    return {
        "canonical_event_id": event["canonical_event_id"],
        "scaleup_rank": event["scaleup_rank"], "pdb_id": "3ORZ",
        "model_number": 1, "protein_chain_or_asym": event["protein_asym"],
        "cys_residue_id": "CYS:148-", "protein_reactive_atom": "SG",
        "ligand_chain_or_asym": event["ligand_asym"],
        "ligand_component_id": "2A2", "ligand_reactive_atom": "SD",
        "ligand_reactive_atom_element": "S",
        "selected_connection_id": event["selected_connection_id"],
        "POST_distance_angstrom": event["POST_distance_angstrom"],
        "POST_distance_frozen_lexeme": next(
            row[6] for row in EXPECTED_EVENTS
            if row[0] == event["canonical_event_id"]
        ),
        "explicit_covalent_evidence": True,
        "distance_only_inference_used": False,
        "human_task_relevance_decision": "RELEVANT", "task_relevant": True,
        "chemistry_known_positive": True, "negative_chemistry": False,
        "task_domain_negative": False,
        "reactive_pair_human_decision_available": True,
        "reactive_pair_human_authoritative": True,
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        "chemical_warhead_human_authoritative": False,
        "minimal_seed_authority_available": False,
        **_training_boundary(), **_geometry_boundary(), **_reusable_boundary(),
        "authority_source": AUTHORITY_SOURCE,
        "authority_scope": AUTHORITY_SCOPE, "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
    }


def _snapshot(bound: Mapping[str, Any]) -> dict[str, object]:
    formal = bound["formal"]
    approval = formal["human_approval"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "artifact_role": "IMMUTABLE_2A2_HUMAN_AUTHORITY_INGESTION_SNAPSHOT",
        "snapshot_created_by_ingestion": True,
        "snapshot_is_new_human_authority": False,
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_evidence_bindings": bound["formal_evidence_bindings"],
        "formal_validator_result": bound["formal_validator_result"],
        "published_role_runtime_validation": bound["published_runtime_result"],
        "formal_schema_version": formal["schema_version"],
        "formal_record_role": formal["record_role"],
        "formal_semantic_canonical_sha256":
            formal["formal_semantic_canonical_sha256"],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID, "ligand_component_id": "2A2",
        "human_approval": {
            "reviewer_id": approval["reviewer_id"],
            "attestor_id": approval["attestor_id"],
            "approved_at_utc": approval["approved_at_utc"],
            "authorization_source": approval["authorization_source"],
            "human_choices_externally_authorized": True,
            "D1_task_relevance": approval["D1_task_relevance"],
            "D2_chemistry": approval["D2_chemistry"],
            "D3_reactive_pair": approval["D3_reactive_pair"],
            "D4_role_partition": approval["D4_role_partition"],
            "D5_training_use": approval["D5_training_use"],
            "D6_scientific_context": approval["D6_scientific_context"],
        },
        "identity": copy.deepcopy(formal["identity"]),
        "events": [_event_projection(event) for event in formal["event_level_human_decisions"]],
        "reactive_pair": copy.deepcopy(formal["reactive_pair_human_decision"]),
        "selected_role_partition": _role_projection(formal),
        "canonical_task_contract": _canonical_task_contract(),
        "chemical_warhead_boundary": copy.deepcopy(formal["chemical_warhead_boundary"]),
        "experimental_context_and_PRE_boundary":
            copy.deepcopy(formal["experimental_context_and_PRE_boundary"]),
        "POST_evidence_boundary": copy.deepcopy(formal["POST_evidence_boundary"]),
        "minimal_seed": copy.deepcopy(formal["minimal_seed"]),
        "training_boundary": _training_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "precedent_state": copy.deepcopy(formal["published_1F8_same_context_precedent"]),
        "current_published_census_boundary":
            bound["current_published_census_boundary"],
        "future_census_informational": bound["future_census_informational"],
        "reconciliation_informational": bound["reconciliation_informational"],
        "authority_boundary": _authority_boundary(),
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "protein_reactive_atom",
    "ligand_chain_or_asym", "ligand_component_id", "ligand_reactive_atom",
    "selected_connection_id", "POST_distance_angstrom",
    "human_task_relevance_decision", "chemistry_known_positive",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_authoritative", "selected_role_candidate_index_0based",
    "role_partition_human_authoritative", "role_profile",
    "warhead_atoms_json", "linker_atoms_json", "scaffold_atoms_json",
    "boundary_bonds_json", "global_canonical_task_count",
    "canonical_task_applicability_json", "strict_profile_applicable_task_ids_json",
    "formal_event_training_use_decision", "human_training_excluded",
    "training_use_allowed", "training_use_include",
    "engineered_target_site", "native_cysteine_site",
    "disulfide_trapping_context", "observed_retained_fragment_context",
    "chemical_warhead_human_authoritative", "chemical_warhead_atoms_json",
    "chemical_warhead_status", "observed_graph_is_complete_authoritative_PRE_reagent",
    "complete_PRE_disulfide_reagent_authority_available",
    "PRE_topology_authority_available", "PRE_geometry_authority_available",
    "PRE_reconstruction_performed", "POST_to_PRE_copy_performed",
    "PRE_zero_fill_performed", "POST_source_evidence_available",
    "POST_geometry_training_authority_available", "minimal_seed_atom_ids_json",
    "minimal_seed_authority_available", "candidate_for_future_training_admission",
    "future_training_candidate_derived_by_ingestion",
    "formal_future_training_admission_candidate_json", "training_admitted",
    "training_admission_created", "training_materialization_allowed_now",
    "formal_split_authority_created", "tensor_target_created",
    "current_runtime_model_usable", "parameter_update_authorization",
    "reaction_family_target_available", "warhead_rule_target_available",
    "warhead_type_target_available", "reusable_chemistry_authority_available",
    "reusable_pair_authority_available", "reusable_role_authority_available",
    "authority_source", "authority_ingested", "authority_created_by_this_ingestion",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    role = snapshot["selected_role_partition"]
    applicability = snapshot["canonical_task_contract"]["task_applicability"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append({
            "canonical_event_id": event["canonical_event_id"],
            "scaleup_rank": str(event["scaleup_rank"]), "pdb_id": "3ORZ",
            "model_number": "1", "protein_chain_or_asym": event["protein_chain_or_asym"],
            "cys_residue_id": "CYS:148-", "protein_reactive_atom": "SG",
            "ligand_chain_or_asym": event["ligand_chain_or_asym"],
            "ligand_component_id": "2A2", "ligand_reactive_atom": "SD",
            "selected_connection_id": event["selected_connection_id"],
            "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
            "human_task_relevance_decision": "RELEVANT",
            "chemistry_known_positive": "true", "negative_chemistry": "false",
            "task_domain_negative": "false",
            "reactive_pair_human_authoritative": "true",
            "selected_role_candidate_index_0based": "4",
            "role_partition_human_authoritative": "true",
            "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atoms_json": _json_cell(list(WARHEAD_ROLE)),
            "linker_atoms_json": _json_cell(list(LINKER_ROLE)),
            "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ROLE)),
            "boundary_bonds_json": _json_cell(list(BOUNDARY_BONDS)),
            "global_canonical_task_count": "5",
            "canonical_task_applicability_json": _json_cell(applicability),
            "strict_profile_applicable_task_ids_json": "[0,1,2,3,4]",
            "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
            "human_training_excluded": "true", "training_use_allowed": "false",
            "training_use_include": "false", "engineered_target_site": "PDK1_T148C",
            "native_cysteine_site": "false", "disulfide_trapping_context": "true",
            "observed_retained_fragment_context": "true",
            "chemical_warhead_human_authoritative": "false",
            "chemical_warhead_atoms_json": "null",
            "chemical_warhead_status": "PRE_DISULFIDE_REAGENT_NOT_FULLY_REPRESENTED",
            "observed_graph_is_complete_authoritative_PRE_reagent": "false",
            "complete_PRE_disulfide_reagent_authority_available": "false",
            "PRE_topology_authority_available": "false",
            "PRE_geometry_authority_available": "false",
            "PRE_reconstruction_performed": "false",
            "POST_to_PRE_copy_performed": "false", "PRE_zero_fill_performed": "false",
            "POST_source_evidence_available": "true",
            "POST_geometry_training_authority_available": "false",
            "minimal_seed_atom_ids_json": "null",
            "minimal_seed_authority_available": "false",
            "candidate_for_future_training_admission": "false",
            "future_training_candidate_derived_by_ingestion": "false",
            "formal_future_training_admission_candidate_json": "null",
            "training_admitted": "false", "training_admission_created": "false",
            "training_materialization_allowed_now": "false",
            "formal_split_authority_created": "false", "tensor_target_created": "false",
            "current_runtime_model_usable": "false",
            "parameter_update_authorization": "false",
            "reaction_family_target_available": "false",
            "warhead_rule_target_available": "false",
            "warhead_type_target_available": "false",
            "reusable_chemistry_authority_available": "false",
            "reusable_pair_authority_available": "false",
            "reusable_role_authority_available": "false",
            "authority_source": AUTHORITY_SOURCE, "authority_ingested": "true",
            "authority_created_by_this_ingestion": "false",
        })
    return rows


def _summary_from_rows(
    rows: Sequence[Mapping[str, str]],
    current: Mapping[str, object],
    future_census: Mapping[str, object],
    reconciliation: Mapping[str, object],
) -> dict[str, object]:
    count = lambda field, value: sum(row[field] == value for row in rows)
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "event_count": len(rows),
        "completed_human_positive_count": sum(
            row["human_task_relevance_decision"] == "RELEVANT"
            and row["chemistry_known_positive"] == "true" for row in rows
        ),
        "chemistry_positive_count": count("chemistry_known_positive", "true"),
        "task_relevant_count": count("human_task_relevance_decision", "RELEVANT"),
        "reactive_pair_human_authority_count":
            count("reactive_pair_human_authoritative", "true"),
        "role_partition_human_authority_count":
            count("role_partition_human_authoritative", "true"),
        "chemical_warhead_human_authority_count":
            count("chemical_warhead_human_authoritative", "true"),
        "human_training_INCLUDE_count":
            count("formal_event_training_use_decision", "INCLUDE"),
        "human_training_EXCLUDE_count": count(
            "formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"
        ),
        "strict_profile_count": count("role_profile", EXPECTED_ROLE_PROFILE),
        "direct_profile_count":
            count("role_profile", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
        "future_training_admission_candidate_count":
            count("candidate_for_future_training_admission", "true"),
        "future_training_candidate_derived_by_ingestion_count":
            count("future_training_candidate_derived_by_ingestion", "true"),
        "training_admitted_count": count("training_admitted", "true"),
        "training_materialization_allowed_count":
            count("training_materialization_allowed_now", "true"),
        "current_runtime_model_usable_count":
            count("current_runtime_model_usable", "true"),
        "minimal_seed_authority_count": count("minimal_seed_authority_available", "true"),
        "PRE_topology_authority_count": count("PRE_topology_authority_available", "true"),
        "PRE_geometry_authority_count": count("PRE_geometry_authority_available", "true"),
        "POST_source_evidence_count": count("POST_source_evidence_available", "true"),
        "POST_geometry_training_authority_count":
            count("POST_geometry_training_authority_available", "true"),
        "reaction_family_target_count": count("reaction_family_target_available", "true"),
        "warhead_rule_target_count": count("warhead_rule_target_available", "true"),
        "warhead_type_target_count": count("warhead_type_target_available", "true"),
        "global_canonical_task_count": 5, "B3_present": True,
        "sixth_task_present": False,
        "training_exclusion_is_chemistry_negative": False,
        "training_exclusion_is_task_irrelevance": False,
        "current_published_census_boundary": copy.deepcopy(dict(current)),
        "future_census_informational": copy.deepcopy(dict(future_census)),
        "reconciliation_informational": copy.deepcopy(dict(reconciliation)),
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "priority_queue_update_status": "NOT_DONE_THIS_STEP",
        "feature_semantics": "AUDIT_REQUIRED_LATER", "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes or len(payload) == 0
        or len(payload) >= 1024 * 1024 or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload or b"\r" in payload
        or not payload.endswith(b"\n") or payload.endswith(b"\n\n")
    ):
        _fail("TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise TwoA2IngestionSafetyError("UTF8_INVALID:" + label) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _reject_dynamic_metadata(value: object, path: str = "root") -> None:
    forbidden = {
        "generated_at", "created_at", "ingested_at", "timestamp", "hostname",
        "host", "pid", "uuid", "cwd", "temporary_path", "output_path",
        "live_git_status", "git_head", "git_tree",
    }
    if type(value) is dict:
        for key, child in value.items():
            if key.lower() in forbidden or (
                "timestamp" in key.lower() and key != "approved_at_utc"
            ):
                _fail("DYNAMIC_METADATA_KEY:" + path + "." + key)
            _reject_dynamic_metadata(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_dynamic_metadata(child, f"{path}[{index}]")
    elif type(value) is str and (
        value.startswith("/cpfs") or value.startswith("/home/")
        or value.startswith("/tmp/") or value.startswith("file://")
    ):
        _fail("ABSOLUTE_OR_MACHINE_PATH:" + path)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative, role in (
        (SOURCE_RELATIVE, "production_owner"),
        (CHECKER_RELATIVE, "fail_closed_checker"),
        (TEST_RELATIVE, "targeted_test_contract"),
    ):
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            _fail("CANDIDATE_SOURCE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        _validate_text_payload(relative.as_posix(), payload)
        rows.append({
            "path": relative.as_posix(), "path_namespace": "repository_relative",
            "byte_count": len(payload), "sha256": _sha(payload),
            "sha256_scope": "file_bytes", "source_role": role,
        })
    return rows


def _validate_candidate_bindings(value: object) -> None:
    if type(value) is not list or len(value) != 3:
        _fail("CANDIDATE_SOURCE_BINDINGS_INVALID")
    expected = [path.as_posix() for path in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE)]
    if [row.get("path") for row in value if type(row) is dict] != expected:
        _fail("CANDIDATE_SOURCE_BINDING_PATHS_INVALID")
    for row in value:
        if type(row) is not dict or (
            row.get("path_namespace") != "repository_relative"
            or type(row.get("byte_count")) is not int or row["byte_count"] <= 0
            or type(row.get("sha256")) is not str or len(row["sha256"]) != 64
            or row.get("sha256_scope") != "file_bytes"
        ):
            _fail("CANDIDATE_SOURCE_BINDING_SHAPE_INVALID")


def _manifest(
    bound: Mapping[str, object], candidate_bindings: list[dict[str, object]],
    snapshot_payload: bytes, matrix_payload: bytes, summary_payload: bytes,
) -> dict[str, object]:
    summary = _strict_json(summary_payload, "SUMMARY_FOR_MANIFEST")
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "artifact_role":
            "2A2_COMPLETED_DECISION_INGESTION_NOT_RECONCILIATION_OR_ADMISSION",
        "candidate_publication_file_count": 7, "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_evidence_bindings": bound["formal_evidence_bindings"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "precedent_bindings": bound["precedent_bindings"],
        "current_published_census_bindings": bound["current_census_bindings"],
        "current_reconciliation_bindings": bound["current_reconciliation_bindings"],
        "current_published_census_boundary":
            bound["current_published_census_boundary"],
        "future_census_informational": bound["future_census_informational"],
        "reconciliation_informational": bound["reconciliation_informational"],
        "candidate_source_bindings": candidate_bindings,
        "canonical_task_contract": _canonical_task_contract(),
        "counts": {
            key: value for key, value in summary.items()
            if type(value) is int and type(value) is not bool
        },
        "chemical_warhead_vs_role_region": {
            "warhead_role_atom_ids": ["SD"], "chemical_warhead_atom_ids": None,
            "chemical_warhead_human_authoritative": False,
            "legacy_matrix_warhead_atoms_json_semantics":
                "CANONICAL_ROLE_PARTITION_WARHEAD_REGION_NOT_COMPLETE_PRE_CHEMICAL_WARHEAD",
            "chemical_warhead_atoms_json": None,
        },
        "human_authority_ingestion_semantics": {
            "authority_source": AUTHORITY_SOURCE, "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True, "authority_created_by_ingestion": False,
            "D4_human_choice": "SELECT_CANDIDATE_4",
            "selected_candidate_index_0based": 4,
            "D5_human_choice": "EXCLUDE_FROM_TRAINING_ONLY",
            "candidate_for_future_training_admission": False,
            "training_admitted": False,
        },
        "output_artifact_bindings": {
            SNAPSHOT: {"sha256": _sha(snapshot_payload)},
            MATRIX: {"sha256": _sha(matrix_payload)},
            SUMMARY: {"sha256": _sha(summary_payload)},
        },
        "manifest_self_sha256_recorded": False,
        "manifest_self_sha256_policy": "SELF_SHA256_PROHIBITED",
        "deterministic": True,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "priority_queue_update_status": "NOT_DONE_THIS_STEP",
        "informational_future_values_materialized": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_2A2_reconciliation_successor": True,
        "ready_for_training": False, "authority_boundary": _authority_boundary(),
    }


def _build_artifacts_unvalidated(
    repo_root: Path,
    *, formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
    execute_formal_validator: bool = True,
) -> dict[str, bytes]:
    repo_root = Path(repo_root).resolve()
    bound = load_frozen_formal_decision_v1(
        repo_root, formal_decision_path=formal_decision_path,
        formal_validator_path=formal_validator_path,
        repository_path_overrides=repository_path_overrides,
        execute_formal_validator=execute_formal_validator,
    )
    snapshot = _snapshot(bound)
    snapshot_payload = _json_bytes(snapshot)
    rows = _matrix_rows(snapshot)
    matrix_payload = _csv_bytes(MATRIX_HEADER, rows)
    summary_payload = _json_bytes(_summary_from_rows(
        rows, bound["current_published_census_boundary"],
        bound["future_census_informational"], bound["reconciliation_informational"],
    ))
    manifest_payload = _json_bytes(_manifest(
        bound, _candidate_source_bindings(repo_root),
        snapshot_payload, matrix_payload, summary_payload,
    ))
    return {
        SNAPSHOT: snapshot_payload, MATRIX: matrix_payload,
        SUMMARY: summary_payload, MANIFEST: manifest_payload,
    }


def _validate_derived_projection_digests(artifacts: Mapping[str, bytes]) -> None:
    for name, digest in (
        (SNAPSHOT, _EXPECTED_SNAPSHOT_SHA256_V1),
        (MATRIX, _EXPECTED_MATRIX_SHA256_V1),
        (SUMMARY, _EXPECTED_SUMMARY_SHA256_V1),
    ):
        if (
            type(digest) is not str or len(digest) != 64 or digest == "0" * 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            _fail("DERIVED_PROJECTION_CONTRACT_DIGEST_NOT_FROZEN:" + name)
        if _sha(artifacts[name]) != digest:
            _fail("DERIVED_PROJECTION_SHA256_INVALID:" + name)


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Validate the Exact4 projection and fail closed on coordinated drift."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    snapshot = _strict_json(artifacts[SNAPSHOT], "SNAPSHOT")
    summary = _strict_json(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json(artifacts[MANIFEST], "MANIFEST")
    try:
        rows = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
    except UnicodeDecodeError as error:
        raise TwoA2IngestionSafetyError("MATRIX_PARSE_FAILED") from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_metadata(document)
    if (list(rows[0]) if rows else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if (
        len(rows) != 4
        or tuple(row["canonical_event_id"] for row in rows) != EXPECTED_EVENT_IDS
        or len({row["canonical_event_id"] for row in rows}) != 4
        or tuple(int(row["scaleup_rank"]) for row in rows) != EXPECTED_RANKS
    ):
        _fail("MATRIX_EXACT4_INVALID")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_DIRECT_PROJECTION_INVALID")
    expected_summary = _summary_from_rows(
        rows, snapshot["current_published_census_boundary"],
        snapshot["future_census_informational"],
        snapshot["reconciliation_informational"],
    )
    if summary != expected_summary:
        _fail("SUMMARY_NOT_INDEPENDENTLY_DERIVED_FROM_MATRIX")
    for row, expected in zip(rows, EXPECTED_EVENTS, strict=True):
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["POST_distance_angstrom"] != expected[6]
            or row["selected_role_candidate_index_0based"] != "4"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or json.loads(row["warhead_atoms_json"]) != ["SD"]
            or json.loads(row["linker_atoms_json"]) != list(LINKER_ROLE)
            or json.loads(row["scaffold_atoms_json"]) != list(SCAFFOLD_ROLE)
            or json.loads(row["chemical_warhead_atoms_json"]) is not None
            or row["chemical_warhead_human_authoritative"] != "false"
            or [item["task_id"] for item in applicability if item["structurally_applicable"]]
            != [0, 1, 2, 3, 4]
            or row["formal_event_training_use_decision"]
            != "EXCLUDE_FROM_TRAINING_ONLY"
            or row["human_training_excluded"] != "true"
            or row["training_use_allowed"] != "false"
            or row["candidate_for_future_training_admission"] != "false"
            or row["training_admitted"] != "false"
            or row["current_runtime_model_usable"] != "false"
        ):
            _fail("MATRIX_ROLE_CHEMICAL_TASK_OR_TRAINING_DRIFT")
    candidate_bindings = manifest.get("candidate_source_bindings")
    _validate_candidate_bindings(candidate_bindings)
    expected_manifest = _manifest(
        {
            "formal_decision_binding": snapshot["formal_decision_binding"],
            "formal_validator_binding": snapshot["formal_validator_binding"],
            "formal_evidence_bindings": snapshot["formal_evidence_bindings"],
            "semantic_owner_bindings": manifest["semantic_owner_bindings"],
            "precedent_bindings": manifest["precedent_bindings"],
            "current_census_bindings": manifest["current_published_census_bindings"],
            "current_reconciliation_bindings": manifest["current_reconciliation_bindings"],
            "current_published_census_boundary": snapshot["current_published_census_boundary"],
            "future_census_informational": snapshot["future_census_informational"],
            "reconciliation_informational": snapshot["reconciliation_informational"],
        },
        candidate_bindings, artifacts[SNAPSHOT], artifacts[MATRIX], artifacts[SUMMARY],
    )
    if manifest != expected_manifest:
        _fail("MANIFEST_CLOSURE_INVALID")
    _validate_derived_projection_digests(artifacts)
    if repo_root is not None:
        repo_root = Path(repo_root).resolve()
        bound = load_frozen_formal_decision_v1(repo_root)
        if snapshot != _snapshot(bound):
            _fail("SNAPSHOT_DIRECT_FORMAL_SOURCE_PROJECTION_INVALID")
        if candidate_bindings != _candidate_source_bindings(repo_root):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID")


def build_artifacts_v1(
    repo_root: Path,
    *, formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Build and validate the deterministic Exact4 metadata projection."""

    artifacts = _build_artifacts_unvalidated(
        repo_root, formal_decision_path=formal_decision_path,
        formal_validator_path=formal_validator_path,
        repository_path_overrides=repository_path_overrides,
    )
    validate_completed_decision_projection_v1(artifacts, repo_root=repo_root)
    return artifacts


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_artifacts_v1(
    repo_root: Path, *, output_root: Path | None = None
) -> dict[str, bytes]:
    """Materialize only the four authorized deterministic metadata outputs."""

    repo_root = Path(repo_root).resolve()
    artifacts = build_artifacts_v1(repo_root)
    target = Path(output_root) if output_root is not None else repo_root / OUTPUT_ROOT_RELATIVE
    if target.exists() and (
        not target.is_dir() or target.is_symlink()
        or {path.name for path in target.iterdir()} - set(OUTPUT_FILENAMES)
    ):
        _fail("OUTPUT_DIRECTORY_INVALID_OR_CONTAINS_UNEXPECTED_FILES")
    for name, payload in artifacts.items():
        _atomic_write(target / name, payload)
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Check live outputs against a fresh source-derived projection."""

    repo_root = Path(repo_root).resolve()
    expected = build_artifacts_v1(repo_root)
    root = repo_root / OUTPUT_ROOT_RELATIVE
    if not root.is_dir() or root.is_symlink() or {
        path.name for path in root.iterdir()
    } != set(OUTPUT_FILENAMES):
        _fail("MATERIALIZED_OUTPUT_INVENTORY_NOT_EXACT4")
    actual: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            _fail("MATERIALIZED_OUTPUT_NOT_REGULAR:" + name)
        actual[name] = path.read_bytes()
    validate_completed_decision_projection_v1(actual, repo_root=repo_root)
    if actual != expected:
        _fail("MATERIALIZED_OUTPUT_BYTES_DRIFT")
    return {
        "status": "PASS", "schema_version": SCHEMA_VERSION,
        "exact_output_count": 4, "event_count": 4, "deterministic": True,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "training_excluded_positive_count": 4, "training_include_count": 0,
        "future_training_admission_candidate_count": 0,
        "global_reconciliation_updated": False,
        "global_census_updated": False, "ready_for_training": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize_artifacts_v1(repo_root)
    print(json.dumps(check_materialized_v1(repo_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
