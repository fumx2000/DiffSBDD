"""Publish bounded acquisition authority for the exact Stage-B0 cohort.

This module is an authority builder only.  It binds the published Stage-B0
worklist to the already-published Step14S RCSB/mmCIF source and raw-staging
architecture.  It never performs a network request or writes a raw structure.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit


SCHEMA_VERSION = (
    "covapie_cys_sg_exact12_bounded_targeted_structural_evidence_"
    "acquisition_authority_v1"
)
BASELINE_COMMIT = "43e1d476175b24d4a1c9ba21d68d5ac5d183303b"
PUBLISHED_B0_COMMIT = BASELINE_COMMIT
REPO_ROOT = Path(__file__).resolve().parents[2]

B0_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1"
)
B0_RECOVERY = B0_ROOT / "covapie_cys_sg_stage_b0_recovery_matrix.csv"
B0_WORKLIST = B0_ROOT / "covapie_cys_sg_stage_b0_acquisition_and_review_worklist.csv"
B0_MANIFEST = B0_ROOT / (
    "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_"
    "manifest.json"
)
PUBLISHED_B0_SHA256: Mapping[Path, str] = {
    B0_RECOVERY: "06ab2464a8e1e8da765f96b45d1fbd25224a3f76c8a420b0088763ee24ce241a",
    B0_WORKLIST: "77c8a447a5c6098b1b834837ee345e03db6ea6b00c7af8a886fa9668585d22f4",
    B0_MANIFEST: "a492af6cf5c27157baf74caef1bf1ab8d385db48cd2f0aeee3a0f367673922c2",
}

EXISTING_AUTHORITY_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_future_struct_conn_crosscheck_controlled_raw_"
    "acquisition_gate_v0"
)
EXISTING_POLICY = EXISTING_AUTHORITY_ROOT / (
    "covapie_cys_sg_controlled_raw_acquisition_policy_contract.csv"
)
EXISTING_REQUESTS = EXISTING_AUTHORITY_ROOT / (
    "covapie_cys_sg_controlled_raw_acquisition_request_manifest.csv"
)
EXISTING_MANIFEST = EXISTING_AUTHORITY_ROOT / (
    "covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate_"
    "manifest.json"
)
PUBLISHED_EXISTING_AUTHORITY_SHA256: Mapping[Path, str] = {
    EXISTING_POLICY: "170ba9f59229c0529dff35d4c09414fdbcc4a16cfa2ba372d0ffa234f3104bac",
    EXISTING_REQUESTS: "0db05f8ef79c595aa388e0cbb88684d77c8f2881c63c9eb0da9f2be16943254a",
    EXISTING_MANIFEST: "4c2de6e2ef662dd0e28bf98eb36b84a9eebd4f1f95feab9b699a78dc46367f19",
}

EXACT_IDENTITIES = (
    ("1A54", "MDC"),
    ("2DJF", "1ZB"),
    ("6VWE", "JY1"),
    ("2R9F", "K2Z"),
    ("4DCD", "K36"),
    ("6WTT", "K36"),
    ("4F49", "K36"),
    ("6L70", "K36"),
    ("6WTJ", "K36"),
    ("7C8U", "K36"),
    ("5WKJ", "K36"),
    ("6WTK", "UED"),
)
INHERITED_IDENTITY = ("1A54", "MDC")
K36_UED_IDENTITIES = EXACT_IDENTITIES[4:]
MAXIMUM_IDENTITY_COUNT = len(EXACT_IDENTITIES)

EXISTING_1A54_AUTHORITY_OWNER = (
    "src/covalent_ext/"
    "covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate.py"
)
EXISTING_1A54_EXECUTION_OWNER = (
    EXISTING_1A54_AUTHORITY_OWNER + "#execute_acquisition"
)
SOURCE_AUTHORITY_ID = "COVAPIE_STEP14S_CONTROLLED_RCSB_MMCIF_AUTHORITY_V0"
SOURCE_POLICY_ID = "RCSB_FILES_HTTPS_EXACT_PDB_MMCIF_V0"
SOURCE_SCHEME = "https"
SOURCE_HOST = "files.rcsb.org"
SOURCE_PATH_TEMPLATE = "/download/{PDB_ID}.cif"
STRUCTURE_FORMAT = "MMCIF"
DESTINATION_POLICY_ID = "COVAPIE_STEP14S_IGNORED_RAW_STAGING_V0"
DESTINATION_ROOT = PurePosixPath(
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0"
)
HISTORICAL_1A54_RAW_SHA256 = (
    "72027fd8250ab981a082a8081f7624ca81f2cc78dfeaba8ea124a3ead1543d11"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_exact12_bounded_targeted_structural_evidence_"
    "acquisition_authority_v1"
)
REQUEST_FILE = "covapie_cys_sg_exact12_targeted_acquisition_request_manifest.csv"
POLICY_FILE = "covapie_cys_sg_exact12_targeted_acquisition_policy_contract.csv"
MANIFEST_FILE = "covapie_cys_sg_exact12_targeted_acquisition_authority_manifest.json"
OUTPUT_FILES = (REQUEST_FILE, POLICY_FILE, MANIFEST_FILE)

REQUEST_COLUMNS = (
    "request_index",
    "canonical_candidate_id",
    "pdb_id",
    "expected_ligand_component_id",
    "b0_worklist_item_id",
    "b0_worklist_sha256",
    "source_authority_id",
    "authorization_origin",
    "source_policy_id",
    "structure_format",
    "source_request_identity",
    "destination_identity",
    "candidate_maximum_request_count",
    "authorization_decision",
    "historical_raw_sha256_provenance_or_NONE",
    "preknown_remote_payload_sha256_required",
    "primary_reason",
)
POLICY_COLUMNS = (
    "policy_item", "policy_value", "policy_basis", "policy_contract_passed",
)


class AuthorityValidationError(ValueError):
    """Raised when the bounded authority cannot be proved exactly."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _verify(payload: bytes, expected: str, identity: str) -> None:
    if _sha256(payload) != expected:
        raise AuthorityValidationError(f"EXACT12_SOURCE_SHA_MISMATCH:{identity}")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bytes(
    rows: Sequence[Mapping[str, Any]], columns: Sequence[str],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="raise", lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            column: str(row[column]).lower()
            if isinstance(row[column], bool) else row[column]
            for column in columns
        })
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False, indent=2,
    ) + "\n").encode("utf-8")


def _source_request_identity(pdb_id: str) -> str:
    return f"{SOURCE_SCHEME}://{SOURCE_HOST}/download/{pdb_id}.cif"


def _destination_identity(pdb_id: str) -> str:
    return (DESTINATION_ROOT / f"{pdb_id.lower()}.cif").as_posix()


def _read_bound_inputs(repo_root: Path) -> dict[Path, bytes]:
    payloads: dict[Path, bytes] = {}
    for path, expected in {
        **PUBLISHED_B0_SHA256, **PUBLISHED_EXISTING_AUTHORITY_SHA256,
    }.items():
        payload = (repo_root / path).read_bytes()
        _verify(payload, expected, path.as_posix())
        payloads[path] = payload
    return payloads


def _validate_published_inputs(
    payloads: Mapping[Path, bytes],
) -> list[dict[str, str]]:
    b0_manifest = json.loads(payloads[B0_MANIFEST])
    required_b0 = {
        "recovery_candidate_count": 12,
        "targeted_external_acquisition_required_count": 12,
        "local_raw_structure_available_count": 0,
        "missing_raw_structure_count": 12,
        "existing_bounded_authorized_count": 1,
        "new_bounded_authorization_required_count": 11,
        "bulk_download_authorized_now": False,
    }
    if any(b0_manifest.get(key) != value for key, value in required_b0.items()):
        raise AuthorityValidationError("EXACT12_PUBLISHED_B0_MANIFEST_INVALID")

    rows = _csv_rows(payloads[B0_WORKLIST])
    identities = tuple(
        (row["pdb_id"], row["ligand_component_id"]) for row in rows
    )
    if identities != EXACT_IDENTITIES or len({pdb for pdb, _ in identities}) != 12:
        raise AuthorityValidationError("EXACT12_B0_WORKLIST_IDENTITY_MISMATCH")
    if any(
        row["worklist_category"] != "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
        or row["bulk_download_authorization_status"]
        != "BULK_DOWNLOAD_NOT_AUTHORIZED"
        or row["canonical_sample_authority_created"].lower() != "false"
        for row in rows
    ):
        raise AuthorityValidationError("EXACT12_B0_WORKLIST_SCOPE_INVALID")

    existing_manifest = json.loads(payloads[EXISTING_MANIFEST])
    existing_requests = _csv_rows(payloads[EXISTING_REQUESTS])
    policy_items = {
        row["policy_item"]: row for row in _csv_rows(payloads[EXISTING_POLICY])
    }
    one_a54 = [
        row for row in existing_requests
        if (row["pdb_id"], row["expected_het_id"]) == INHERITED_IDENTITY
    ]
    required_policy_items = {
        "controlled_acquisition_only_five_pdb_ids",
        "raw_files_must_remain_untracked",
        "raw_files_must_remain_unstaged",
    }
    if (
        existing_manifest.get("all_checks_passed") is not True
        or existing_manifest.get("raw_output_root") != DESTINATION_ROOT.as_posix()
        or len(one_a54) != 1
        or one_a54[0]["rcsb_mmcif_url"] != _source_request_identity("1A54")
        or one_a54[0]["expected_raw_relative_path"]
        != _destination_identity("1A54")
        or not required_policy_items.issubset(policy_items)
        or any(
            policy_items[item]["policy_contract_passed"].lower() != "true"
            for item in required_policy_items
        )
    ):
        raise AuthorityValidationError("EXACT12_EXISTING_1A54_AUTHORITY_INVALID")
    return rows


def _expected_request_row(
    index: int, worklist_row: Mapping[str, str],
) -> dict[str, Any]:
    pdb_id = worklist_row["pdb_id"]
    ligand = worklist_row["ligand_component_id"]
    inherited = (pdb_id, ligand) == INHERITED_IDENTITY
    return {
        "request_index": index,
        "canonical_candidate_id": worklist_row["canonical_candidate_id"],
        "pdb_id": pdb_id,
        "expected_ligand_component_id": ligand,
        "b0_worklist_item_id": worklist_row["worklist_item_id"],
        "b0_worklist_sha256": PUBLISHED_B0_SHA256[B0_WORKLIST],
        "source_authority_id": SOURCE_AUTHORITY_ID,
        "authorization_origin": (
            "INHERITED_PUBLISHED_BOUNDED_AUTHORITY" if inherited
            else "NEW_EXACT12_SUCCESSOR_AUTHORITY"
        ),
        "source_policy_id": SOURCE_POLICY_ID,
        "structure_format": STRUCTURE_FORMAT,
        "source_request_identity": _source_request_identity(pdb_id),
        "destination_identity": _destination_identity(pdb_id),
        "candidate_maximum_request_count": 1,
        "authorization_decision": (
            "INHERITED_AUTHORIZED_EXACT_TARGET" if inherited
            else "AUTHORIZED_EXACT_TARGET"
        ),
        "historical_raw_sha256_provenance_or_NONE": (
            HISTORICAL_1A54_RAW_SHA256 if inherited else "NONE"
        ),
        "preknown_remote_payload_sha256_required": False,
        "primary_reason": (
            "PRESERVE_PUBLISHED_1A54_BOUNDED_REACQUISITION_AUTHORITY"
            if inherited else
            "AUTHORIZE_EXACT_PUBLISHED_B0_MISSING_RAW_STRUCTURE_IDENTITY"
        ),
    }


def validate_request_rows_v1(
    request_rows: Sequence[Mapping[str, Any]],
    worklist_rows: Sequence[Mapping[str, str]],
) -> None:
    """Fail closed unless rows are the exact, source-bound B0 authority."""

    if len(request_rows) > MAXIMUM_IDENTITY_COUNT:
        raise AuthorityValidationError("EXACT12_MAXIMUM_CARDINALITY_EXCEEDED")
    if len(request_rows) != MAXIMUM_IDENTITY_COUNT:
        raise AuthorityValidationError("EXACT12_REQUEST_CARDINALITY_INVALID")
    if len(worklist_rows) != MAXIMUM_IDENTITY_COUNT:
        raise AuthorityValidationError("EXACT12_WORKLIST_CARDINALITY_INVALID")

    pdb_ids = [str(row.get("pdb_id", "")) for row in request_rows]
    source_ids = [str(row.get("source_request_identity", "")) for row in request_rows]
    destinations = [str(row.get("destination_identity", "")) for row in request_rows]
    if len(set(pdb_ids)) != len(pdb_ids):
        raise AuthorityValidationError("EXACT12_DUPLICATE_PDB_REQUEST")
    if len(set(source_ids)) != len(source_ids) or len(set(destinations)) != len(destinations):
        raise AuthorityValidationError("EXACT12_DUPLICATE_REQUEST_IDENTITY")

    wildcard_tokens = ("*", "?", "[", "]")
    for index, (row, worklist_row) in enumerate(
        zip(request_rows, worklist_rows), start=1,
    ):
        pdb_id = str(row.get("pdb_id", ""))
        if not re.fullmatch(r"[0-9][A-Z0-9]{3}", pdb_id):
            raise AuthorityValidationError("EXACT12_PDB_IDENTITY_INVALID")
        if any(
            token in str(row.get(field, ""))
            for field in ("pdb_id", "source_request_identity", "destination_identity")
            for token in wildcard_tokens
        ):
            raise AuthorityValidationError("EXACT12_WILDCARD_REQUEST_FORBIDDEN")

        source = urlsplit(str(row.get("source_request_identity", "")))
        if (
            source.scheme != SOURCE_SCHEME
            or source.netloc != SOURCE_HOST
            or source.path != SOURCE_PATH_TEMPLATE.format(PDB_ID=pdb_id)
            or source.query or source.fragment
        ):
            raise AuthorityValidationError("EXACT12_SOURCE_POLICY_INVALID")

        destination_text = str(row.get("destination_identity", ""))
        destination = PurePosixPath(destination_text)
        try:
            destination.relative_to(DESTINATION_ROOT)
        except ValueError as exc:
            raise AuthorityValidationError(
                "EXACT12_DESTINATION_ESCAPES_APPROVED_ROOT"
            ) from exc
        if destination.is_absolute() or ".." in destination.parts:
            raise AuthorityValidationError(
                "EXACT12_DESTINATION_ESCAPES_APPROVED_ROOT"
            )

        expected = _expected_request_row(index, worklist_row)
        if dict(row) != expected:
            raise AuthorityValidationError(
                f"EXACT12_REQUEST_ROW_CONTRACT_MISMATCH:{index}"
            )


def _build_policy_rows() -> list[dict[str, Any]]:
    specs = (
        ("authority_scope", "EXACT12_PUBLISHED_B0_WORKLIST_ONLY", "published B0 worklist"),
        ("bulk_download_authorized", False, "ADMIT_014 boundary remains false"),
        ("network_execution_in_authority_stage", False, "authority-only stage"),
        ("maximum_identity_count", 12, "exact B0 cardinality"),
        ("maximum_primary_acquisition_count", 12, "one primary request per PDB identity"),
        ("candidate_maximum_request_count", 1, "single bounded primary request"),
        ("source_policy_id", SOURCE_POLICY_ID, "published Step14S request authority"),
        ("source_scheme", SOURCE_SCHEME, "published Step14S exact URL"),
        ("source_host", SOURCE_HOST, "published Step14S exact URL"),
        ("source_path_template", SOURCE_PATH_TEMPLATE, "published Step14S exact URL"),
        ("pdb_id_normalization", "UPPERCASE_FOUR_CHARACTER", "published Step14S URL token"),
        ("structure_format", STRUCTURE_FORMAT, "published Step14S .cif request"),
        ("destination_policy_id", DESTINATION_POLICY_ID, "published Step14S raw staging"),
        ("destination_root", DESTINATION_ROOT.as_posix(), "published Step14S raw output root"),
        ("raw_git_policy", "REPOSITORY_IGNORED_UNTRACKED_UNSTAGED_RAW_ONLY", "published Step14S policy and .gitignore"),
        ("overwrite_allowed", False, "invalid existing target fails closed"),
        ("valid_existing_file_action", "VERIFY_AND_REUSE_WITHOUT_NETWORK", "idempotent exact identity/integrity reuse"),
        ("invalid_existing_file_action", "FAIL_CLOSED_NO_OVERWRITE", "bounded idempotence requirement"),
        ("temporary_path_policy", "FINAL_PATH_PLUS_DOT_PART", "published Step14S safe-write suffix"),
        ("atomic_write_policy", "VERIFY_PART_THEN_OS_REPLACE_AND_REMOVE_PART", "published Step14S atomic primitive with successor pre-promotion verification"),
        ("integrity_verification_policy", "REQUEST_SUCCEEDED_NONEMPTY_NON_HTML_MMCIF_DATA_BLOCK_ID_MATCHES_PDB_ATOM_SITE_PARSEABLE_RECORD_SHA256_SIZE_FINAL_PATH", "future execution evidence contract"),
        ("preknown_remote_sha256_required", False, "upstream remediation-safe identity validation"),
        ("maximum_attempts_per_identity", 1, "published Step14S has no retry loop"),
        ("request_timeout_seconds", 30, "published Step14S timeout"),
        ("pagination_discovery_crawl_or_recursive_acquisition", False, "exact bounded request rows only"),
        ("failure_final_state", "NO_CORRUPTED_FINAL_AND_NO_PART_LEFTOVER", "fail-closed atomic execution contract"),
    )
    return [
        {
            "policy_item": item,
            "policy_value": value,
            "policy_basis": basis,
            "policy_contract_passed": True,
        }
        for item, value, basis in specs
    ]


def _build_manifest(
    request_rows: Sequence[Mapping[str, Any]],
    request_payload: bytes,
    policy_payload: bytes,
) -> dict[str, Any]:
    inherited = sum(
        row["authorization_origin"] == "INHERITED_PUBLISHED_BOUNDED_AUTHORITY"
        for row in request_rows
    )
    newly_authorized = sum(
        row["authorization_origin"] == "NEW_EXACT12_SUCCESSOR_AUTHORITY"
        for row in request_rows
    )
    authorized = [
        f"{row['pdb_id']}/{row['expected_ligand_component_id']}"
        for row in request_rows
        if row["authorization_decision"] in {
            "INHERITED_AUTHORIZED_EXACT_TARGET", "AUTHORIZED_EXACT_TARGET",
        }
    ]
    blocked = [
        f"{row['pdb_id']}/{row['expected_ligand_component_id']}"
        for row in request_rows
        if row["authorization_decision"] not in {
            "INHERITED_AUTHORIZED_EXACT_TARGET", "AUTHORIZED_EXACT_TARGET",
        }
    ]
    exact12_ready = (
        len(request_rows) == len(authorized) == MAXIMUM_IDENTITY_COUNT
        and inherited == 1 and newly_authorized == 11 and not blocked
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_commit": BASELINE_COMMIT,
        "published_b0_commit": PUBLISHED_B0_COMMIT,
        "published_b0_owner": (
            "src/covalent_ext/"
            "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_"
            "recovery_v1.py"
        ),
        "published_b0_worklist_sha256": PUBLISHED_B0_SHA256[B0_WORKLIST],
        "published_b0_recovery_matrix_sha256": PUBLISHED_B0_SHA256[B0_RECOVERY],
        "published_b0_manifest_sha256": PUBLISHED_B0_SHA256[B0_MANIFEST],
        "existing_1a54_authority_owner": EXISTING_1A54_AUTHORITY_OWNER,
        "existing_1a54_execution_owner_if_any": EXISTING_1A54_EXECUTION_OWNER,
        "existing_1a54_source_endpoint_policy": (
            "https://files.rcsb.org/download/{UPPERCASE_PDB_ID}.cif"
        ),
        "existing_1a54_destination_policy": (
            DESTINATION_ROOT.as_posix() + "/{lowercase_pdb_id}.cif;ignored;untracked;unstaged"
        ),
        "existing_1a54_integrity_policy": (
            "nonempty;non_html;mmcif_data_block;sha256;byte_size;final_path"
        ),
        "existing_1a54_retry_timeout_policy": (
            "single_attempt_no_retry_loop;timeout_seconds=30"
        ),
        "existing_1a54_atomic_write_policy": (
            ".part temporary path;os.replace;part cleanup"
        ),
        "candidate_scope": "EXACT12_PUBLISHED_B0_TARGETED_ACQUISITION_ROWS_ONLY",
        "requested_identity_count": len(request_rows),
        "unique_pdb_identity_count": len({row["pdb_id"] for row in request_rows}),
        "authorized_exact_target_count": len(authorized),
        "inherited_authorized_count": inherited,
        "newly_authorized_count": newly_authorized,
        "blocked_count": len(blocked),
        "authorized_identity_list": authorized,
        "blocked_identity_list": blocked,
        "source_authority_id": SOURCE_AUTHORITY_ID,
        "source_policy_id": SOURCE_POLICY_ID,
        "structure_format": STRUCTURE_FORMAT,
        "destination_policy_id": DESTINATION_POLICY_ID,
        "destination_root": DESTINATION_ROOT.as_posix(),
        "bulk_download_authorized": False,
        "targeted_download_authorized_for_exact12": exact12_ready,
        "maximum_primary_acquisition_count": len(request_rows),
        "one_request_per_pdb_identity": len(request_rows) == len({row["pdb_id"] for row in request_rows}),
        "wildcard_request_allowed": False,
        "source_discovery_crawl_allowed": False,
        "overwrite_allowed": False,
        "idempotence_policy": "VERIFY_AND_REUSE_VALID_EXISTING_ELSE_DOWNLOAD_IF_ABSENT_ELSE_FAIL_CLOSED",
        "atomic_write_policy": "DOT_PART_VERIFY_BEFORE_ATOMIC_OS_REPLACE_CLEANUP_ON_FAILURE",
        "integrity_verification_policy": "REQUEST_SUCCEEDED_NONEMPTY_NON_HTML_MMCIF_DATA_BLOCK_ID_MATCHES_PDB_ATOM_SITE_PARSEABLE_RECORD_SHA256_SIZE_FINAL_PATH",
        "historical_1a54_raw_sha256": HISTORICAL_1A54_RAW_SHA256,
        "historical_1a54_sha_treatment": "HISTORICAL_PROVENANCE_ONLY_NOT_PREKNOWN_REMOTE_BYTE_REQUIREMENT",
        "six_vwe_rh_model_graph_claim_created": False,
        "k36_ued_bounded_request_count": sum(
            (row["pdb_id"], row["expected_ligand_component_id"])
            in K36_UED_IDENTITIES for row in request_rows
        ),
        "future_execution_inputs": [
            REQUEST_FILE, POLICY_FILE, MANIFEST_FILE,
        ],
        "network_request_executed": False,
        "network_executed": False,
        "download_executed": False,
        "targeted_acquisition_executed": False,
        "bulk_acquisition_executed": False,
        "raw_structure_downloaded": False,
        "raw_structure_modified": False,
        "geometry_executed": False,
        "inverse_reaction_chemistry_executed": False,
        "rdkit_minimization_executed": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "trainer_fit": False,
        "rl": False,
        "canonical_sample_authority_created": False,
        "published_b0_modified": False,
        "published_stage_a_modified": False,
        "current11_modified": False,
        "raw_modified": False,
        "deterministic_output_hashes": {
            REQUEST_FILE: _sha256(request_payload),
            POLICY_FILE: _sha256(policy_payload),
        },
        "manifest_self_sha256_recorded": False,
        "ready_for_publication": exact12_ready,
        "ready_for_exact12_acquisition_authority_publication": exact12_ready,
        "ready_for_exact12_acquisition_execution": exact12_ready,
        "ready_for_bulk_expansion": False,
        "ready_for_geometry_loss_activation": False,
        "ready_for_training": False,
        "recommended_next_step_exactly": (
            "review_and_publish_covapie_cys_sg_exact12_bounded_targeted_"
            "structural_evidence_acquisition_authority_v1"
        ),
    }


def build_covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1(
    *, repo_root: Path = REPO_ROOT,
) -> dict[str, bytes]:
    payloads = _read_bound_inputs(repo_root)
    worklist_rows = _validate_published_inputs(payloads)
    request_rows = [
        _expected_request_row(index, row)
        for index, row in enumerate(worklist_rows, start=1)
    ]
    validate_request_rows_v1(request_rows, worklist_rows)
    policy_rows = _build_policy_rows()
    request_payload = _csv_bytes(request_rows, REQUEST_COLUMNS)
    policy_payload = _csv_bytes(policy_rows, POLICY_COLUMNS)
    manifest = _build_manifest(request_rows, request_payload, policy_payload)
    return {
        REQUEST_FILE: request_payload,
        POLICY_FILE: policy_payload,
        MANIFEST_FILE: _json_bytes(manifest),
    }


def materialize_covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1(
    output_root: Path = REPO_ROOT / OUTPUT_ROOT,
    *, repo_root: Path = REPO_ROOT,
) -> dict[str, str]:
    artifacts = (
        build_covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1(
            repo_root=repo_root,
        )
    )
    output_root.mkdir(parents=True, exist_ok=True, mode=0o755)
    os.chmod(output_root, 0o755)
    hashes: dict[str, str] = {}
    for filename in OUTPUT_FILES:
        path = output_root / filename
        temporary = path.with_suffix(path.suffix + ".tmp")
        try:
            temporary.write_bytes(artifacts[filename])
            os.chmod(
                temporary,
                stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
            )
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        os.chmod(
            path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
        )
        hashes[filename] = _sha256(artifacts[filename])
    return hashes


def main() -> None:
    print(json.dumps(
        materialize_covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1(),
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
