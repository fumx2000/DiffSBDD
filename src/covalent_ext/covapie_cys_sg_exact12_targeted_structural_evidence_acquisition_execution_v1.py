"""Execute the published exact12 Cys-SG raw mmCIF acquisition authority.

The module deliberately separates authority and payload validation from the
single-attempt network side effect.  Importing it performs no I/O.  Successful
downloads are verified as ``.part`` files before atomic promotion and are
verified again at their final paths.  Post-acquisition chemistry is delegated
to the published Stage-B0 recovery owner; distance-only event inference is
never introduced here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import socket
import ssl
import stat
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlsplit

from covalent_ext import (
    covapie_cys_sg_exact12_bounded_targeted_structural_evidence_acquisition_authority_v1
    as authority_owner,
)
from covalent_ext import (
    covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1
    as stage_b0,
)
from covalent_ext import (
    real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun
    as atom_site_owner,
)


SCHEMA_VERSION = (
    "covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_"
    "execution_v1"
)
BASELINE_COMMIT = "988348892a7d08fc3d420821c55b192bbcd99254"
PUBLISHED_AUTHORITY_COMMIT = BASELINE_COMMIT
FORMAL_NETWORK_EXECUTION_OWNER_SHA256 = (
    "a802574583246879838d7d94075388530dc5d7062c5ff1e4cea0a30820c7b297"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = REPO_ROOT.parent / "covapie-state"

AUTHORITY_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_exact12_bounded_targeted_structural_evidence_"
    "acquisition_authority_v1"
)
REQUEST_PATH = AUTHORITY_ROOT / authority_owner.REQUEST_FILE
POLICY_PATH = AUTHORITY_ROOT / authority_owner.POLICY_FILE
AUTHORITY_MANIFEST_PATH = AUTHORITY_ROOT / authority_owner.MANIFEST_FILE
AUTHORITY_SOURCE_PATH = Path(
    "src/covalent_ext/"
    "covapie_cys_sg_exact12_bounded_targeted_structural_evidence_"
    "acquisition_authority_v1.py"
)
PUBLISHED_AUTHORITY_SHA256: Mapping[Path, str] = {
    REQUEST_PATH: "9a376acacaf10eb7b436de072a7971f7a632057e92c0bec73ad10757139b1de0",
    POLICY_PATH: "50fc705ee3b0ead524d6a38a90289231d2178b8cb9560ed6cc102aa3195172f4",
    AUTHORITY_MANIFEST_PATH:
        "20a5483e510c347171f4a6b98676b530d1783ddaee6663269d843353877075b3",
}
PUBLISHED_AUTHORITY_SOURCE_SHA256 = (
    "464457826e04893816ad17464fb57601e7f44b59b8d2fde3815475635d9e5305"
)

RAW_ROOT = authority_owner.DESTINATION_ROOT
SOURCE_HOST = authority_owner.SOURCE_HOST
REQUEST_TIMEOUT_SECONDS = 30
HISTORICAL_1A54_RAW_SHA256 = authority_owner.HISTORICAL_1A54_RAW_SHA256
ATOM_SITE_PARSER_OWNER = (
    "src/covalent_ext/"
    "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_"
    "altloc_aware_rerun.py#extract_atom_site_loop_rows_v0"
)
RECOVERY_OWNER = (
    "src/covalent_ext/"
    "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_"
    "recovery_v1.py#_missing_matrix_row"
)

OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_"
    "execution_v1"
)
EXECUTION_AUDIT_FILE = (
    "covapie_cys_sg_exact12_acquisition_execution_and_integrity_audit.csv"
)
RECOVERY_SNAPSHOT_FILE = (
    "covapie_cys_sg_exact12_post_acquisition_structural_recovery_snapshot.csv"
)
EXECUTION_MANIFEST_FILE = (
    "covapie_cys_sg_exact12_targeted_acquisition_execution_manifest.json"
)
OUTPUT_FILES = (
    EXECUTION_AUDIT_FILE, RECOVERY_SNAPSHOT_FILE, EXECUTION_MANIFEST_FILE,
)

EXECUTION_COLUMNS = (
    "request_index", "canonical_candidate_id", "pdb_id",
    "expected_ligand_component_id", "source_request_identity",
    "destination_identity", "pre_execution_file_status", "action_taken",
    "network_attempted", "network_attempt_count", "request_status",
    "response_or_transport_status", "part_path", "part_payload_nonempty",
    "part_html_detected", "part_data_block_identity",
    "part_pdb_identity_matches", "part_atom_site_parseable",
    "part_atom_site_row_count", "part_sha256", "part_size_bytes",
    "part_verified_before_promotion", "atomic_promotion_performed",
    "final_file_exists", "final_data_block_identity", "final_sha256",
    "final_size_bytes", "final_pdb_identity_matches",
    "final_atom_site_parseable", "final_atom_site_row_count",
    "final_atom_site_rh_present", "part_leftover", "acquisition_status",
    "primary_failure_code_or_NONE",
)
RECOVERY_COLUMNS = (
    "canonical_candidate_id", "pdb_id", "ligand_component_id",
    "acquisition_status", "local_raw_structure_found", "raw_sha256",
    "explicit_connection_evidence_status", "cys_sg_event_recovered",
    "protein_chain_if_recovered", "cys_residue_sequence_if_recovered",
    "cys_insertion_code_if_recovered",
    "reactive_residue_atom_if_recovered",
    "ligand_chain_or_instance_if_recovered",
    "reactive_ligand_atom_if_recovered", "coordinate_status",
    "ligand_component_identity_status", "structural_recovery_status",
    "recovery_disposition", "primary_remaining_issue",
)


class ExecutionValidationError(ValueError):
    """Raised when published authority or local execution state is invalid."""


class BoundedTransportError(RuntimeError):
    """A transport failure represented by one deterministic bounded code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class PublishedAuthority:
    request_rows: tuple[dict[str, str], ...]
    policy_rows: tuple[dict[str, str], ...]
    manifest: Mapping[str, Any]


@dataclass(frozen=True)
class RawPayloadValidation:
    valid: bool
    failure_code: str
    payload_nonempty: bool
    html_or_error_detected: bool
    data_block_identity: str
    pdb_identity_matches: bool
    atom_site_parseable: bool
    atom_site_row_count: int
    sha256: str
    size_bytes: int
    atom_site_rh_present: bool


@dataclass(frozen=True)
class TransportResponse:
    payload: bytes
    status_code: int
    final_url: str


@dataclass(frozen=True)
class GitRawSafety:
    raw_final_file_count: int
    part_leftover_count: int
    raw_tracked_count: int
    raw_staged_count: int
    all_exact_paths_ignored: bool


Transport = Callable[[str, int], TransportResponse]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args), cwd=repo_root, check=False, text=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def validate_published_git_identity_v1(repo_root: Path = REPO_ROOT) -> None:
    """Require mutation-safe repository state without treating live Git as authority."""

    # Published, SHA-bound authority content controls acquisition authorization.
    # Live HEAD/origin equality would make this owner unusable from its own
    # successor commit and therefore is deliberately not consulted here.
    staged = _run_git(repo_root, ["diff", "--cached", "--name-only"])
    if staged.returncode != 0:
        raise ExecutionValidationError("EXACT12_EXECUTION_GIT_SAFETY_CHECK_FAILED")
    if staged.stdout.strip():
        raise ExecutionValidationError("EXACT12_EXECUTION_STAGED_INDEX_NOT_EMPTY")


def _validate_authority_payloads_v1(
    payloads: Mapping[Path, bytes], authority_source: bytes,
) -> PublishedAuthority:
    for path, expected in PUBLISHED_AUTHORITY_SHA256.items():
        if path not in payloads or _sha256(payloads[path]) != expected:
            raise ExecutionValidationError(
                f"EXACT12_PUBLISHED_AUTHORITY_SHA_MISMATCH:{path.as_posix()}"
            )
    if _sha256(authority_source) != PUBLISHED_AUTHORITY_SOURCE_SHA256:
        raise ExecutionValidationError(
            "EXACT12_PUBLISHED_AUTHORITY_OWNER_SHA_MISMATCH"
        )

    request_rows = _csv_rows(payloads[REQUEST_PATH])
    policy_rows = _csv_rows(payloads[POLICY_PATH])
    manifest = json.loads(payloads[AUTHORITY_MANIFEST_PATH])
    worklist_projection = [
        {
            "canonical_candidate_id": row["canonical_candidate_id"],
            "pdb_id": row["pdb_id"],
            "ligand_component_id": row["expected_ligand_component_id"],
            "worklist_item_id": row["b0_worklist_item_id"],
        }
        for row in request_rows
    ]
    typed_request_rows: list[dict[str, Any]] = []
    for row in request_rows:
        typed = dict(row)
        typed["request_index"] = int(typed["request_index"])
        typed["candidate_maximum_request_count"] = int(
            typed["candidate_maximum_request_count"]
        )
        typed["preknown_remote_payload_sha256_required"] = (
            typed["preknown_remote_payload_sha256_required"].lower() == "true"
        )
        typed_request_rows.append(typed)
    authority_owner.validate_request_rows_v1(
        typed_request_rows, worklist_projection,
    )

    identities = tuple(
        (row["pdb_id"], row["expected_ligand_component_id"])
        for row in request_rows
    )
    if identities != authority_owner.EXACT_IDENTITIES:
        raise ExecutionValidationError("EXACT12_EXECUTION_MEMBERSHIP_MISMATCH")
    if len(request_rows) != 12 or len({row["pdb_id"] for row in request_rows}) != 12:
        raise ExecutionValidationError("EXACT12_EXECUTION_CARDINALITY_MISMATCH")

    policy = {row["policy_item"]: row for row in policy_rows}
    required_policy = {
        "maximum_identity_count": "12",
        "maximum_primary_acquisition_count": "12",
        "candidate_maximum_request_count": "1",
        "source_scheme": "https",
        "source_host": SOURCE_HOST,
        "request_timeout_seconds": str(REQUEST_TIMEOUT_SECONDS),
        "overwrite_allowed": "false",
    }
    for item, expected in required_policy.items():
        row = policy.get(item)
        if (
            row is None or row.get("policy_value") != expected
            or row.get("policy_contract_passed", "").lower() != "true"
        ):
            raise ExecutionValidationError(
                f"EXACT12_EXECUTION_POLICY_INVALID:{item}"
            )
    required_manifest = {
        "requested_identity_count": 12,
        "unique_pdb_identity_count": 12,
        "blocked_count": 0,
        "targeted_download_authorized_for_exact12": True,
        "ready_for_exact12_acquisition_execution": True,
        "bulk_download_authorized": False,
        "maximum_primary_acquisition_count": 12,
        "one_request_per_pdb_identity": True,
        "wildcard_request_allowed": False,
        "source_discovery_crawl_allowed": False,
        "overwrite_allowed": False,
    }
    if any(manifest.get(key) != value for key, value in required_manifest.items()):
        raise ExecutionValidationError("EXACT12_EXECUTION_AUTHORITY_MANIFEST_INVALID")
    # The frozen pre-publication recommended-next-step field is advisory only.
    return PublishedAuthority(tuple(request_rows), tuple(policy_rows), manifest)


def load_and_validate_published_authority_v1(
    repo_root: Path = REPO_ROOT,
) -> PublishedAuthority:
    """Read exactly the three authority artifacts and bind their source owner."""

    payloads = {
        path: (repo_root / path).read_bytes() for path in PUBLISHED_AUTHORITY_SHA256
    }
    return _validate_authority_payloads_v1(
        payloads, (repo_root / AUTHORITY_SOURCE_PATH).read_bytes(),
    )


def _payload_looks_like_html_or_error(payload: bytes) -> bool:
    prefix = payload[:4096].decode("utf-8", errors="ignore").lstrip("\ufeff\x00 \t\r\n")
    lowered = prefix.lower()
    if any(token in lowered for token in (
        "<!doctype html", "<html", "<head", "<body",
    )):
        return True
    first_line = lowered.splitlines()[0].strip() if lowered.splitlines() else ""
    return bool(re.match(
        r"^(?:error\b|(?:400|401|403|404|429|500|502|503|504)\b|"
        r"not found\b|bad gateway\b|service unavailable\b)",
        first_line,
    ))


def _data_block_identity(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"data_([^\s]+)", line, flags=re.IGNORECASE)
        return match.group(1).upper() if match else "NONE"
    return "NONE"


def validate_raw_mmcif_payload_v1(
    payload: bytes, requested_pdb_id: str,
) -> RawPayloadValidation:
    """Validate identity and atom-site parseability using the published parser."""

    size = len(payload)
    sha = _sha256(payload)
    nonempty = size > 0 and bool(payload.strip())
    html = _payload_looks_like_html_or_error(payload) if nonempty else False
    data_block = "NONE"
    identity_matches = False
    atom_parseable = False
    atom_count = 0
    rh_present = False
    failure = "NONE"
    if not nonempty:
        failure = "EMPTY_PAYLOAD"
    elif html:
        failure = "HTML_OR_ERROR_PAYLOAD"
    else:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            failure = "MMCIF_UTF8_DECODE_ERROR"
        else:
            data_block = _data_block_identity(text)
            identity_matches = data_block == requested_pdb_id.upper()
            if data_block == "NONE":
                failure = "MMCIF_DATA_BLOCK_MISSING"
            elif not identity_matches:
                failure = "MMCIF_PDB_IDENTITY_MISMATCH"
            else:
                try:
                    atom_rows = atom_site_owner.extract_atom_site_loop_rows_v0(text)
                except (ValueError, TypeError):
                    failure = "ATOM_SITE_UNPARSEABLE"
                else:
                    atom_count = len(atom_rows)
                    atom_parseable = atom_count > 0
                    rh_present = any(
                        str(row.get("_atom_site.type_symbol", "")).upper() == "RH"
                        for row in atom_rows
                    )
                    if not atom_parseable:
                        failure = "ATOM_SITE_MISSING_UNPARSEABLE_OR_EMPTY"
    valid = failure == "NONE"
    return RawPayloadValidation(
        valid, failure, nonempty, html, data_block, identity_matches,
        atom_parseable, atom_count, sha, size, rh_present,
    )


class _SameHTTPSHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: urllib.request.Request, fp: Any, code: int, msg: str,
        headers: Any, newurl: str,
    ) -> urllib.request.Request | None:
        parsed = urlsplit(newurl)
        if (
            parsed.scheme.lower() != "https"
            or parsed.hostname is None
            or parsed.hostname.lower() != SOURCE_HOST
            or parsed.port is not None
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise BoundedTransportError("CROSS_HOST_REDIRECT_FORBIDDEN")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _urllib_transport_v1(url: str, timeout: int) -> TransportResponse:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https" or parsed.netloc != SOURCE_HOST
        or parsed.query or parsed.fragment
    ):
        raise BoundedTransportError("PRIMARY_SOURCE_IDENTITY_INVALID")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CovaPIE-exact12-targeted-acquisition-v1"},
    )
    opener = urllib.request.build_opener(_SameHTTPSHostRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            status = int(response.getcode())
            final_url = response.geturl()
            payload = response.read()
    except BoundedTransportError:
        raise
    except urllib.error.HTTPError as exc:
        raise BoundedTransportError(f"HTTP_ERROR_{exc.code}") from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            code = "TRANSPORT_TIMEOUT"
        elif isinstance(reason, ssl.SSLError):
            code = "TRANSPORT_TLS_ERROR"
        elif isinstance(reason, socket.gaierror):
            code = "TRANSPORT_DNS_ERROR"
        elif "proxy" in str(reason).lower():
            code = "TRANSPORT_PROXY_ERROR"
        else:
            code = "TRANSPORT_URL_ERROR"
        raise BoundedTransportError(code) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise BoundedTransportError("TRANSPORT_TIMEOUT") from exc
    except ConnectionResetError as exc:
        raise BoundedTransportError("TRANSPORT_CONNECTION_RESET") from exc
    except (OSError, ssl.SSLError) as exc:
        raise BoundedTransportError("TRANSPORT_OS_OR_TLS_ERROR") from exc

    final = urlsplit(final_url)
    if final.scheme.lower() != "https" or final.hostname != SOURCE_HOST:
        raise BoundedTransportError("CROSS_HOST_REDIRECT_FORBIDDEN")
    if not 200 <= status < 300:
        raise BoundedTransportError(f"HTTP_STATUS_{status}")
    return TransportResponse(payload, status, final_url)


def _validation_fields(
    validation: RawPayloadValidation | None, prefix: str,
) -> dict[str, Any]:
    if validation is None:
        return {
            f"{prefix}_payload_nonempty": False,
            f"{prefix}_html_detected": False,
            f"{prefix}_data_block_identity": "NONE",
            f"{prefix}_pdb_identity_matches": False,
            f"{prefix}_atom_site_parseable": False,
            f"{prefix}_atom_site_row_count": 0,
            f"{prefix}_sha256": "NONE",
            f"{prefix}_size_bytes": 0,
        }
    return {
        f"{prefix}_payload_nonempty": validation.payload_nonempty,
        f"{prefix}_html_detected": validation.html_or_error_detected,
        f"{prefix}_data_block_identity": validation.data_block_identity,
        f"{prefix}_pdb_identity_matches": validation.pdb_identity_matches,
        f"{prefix}_atom_site_parseable": validation.atom_site_parseable,
        f"{prefix}_atom_site_row_count": validation.atom_site_row_count,
        f"{prefix}_sha256": validation.sha256,
        f"{prefix}_size_bytes": validation.size_bytes,
    }


def _base_execution_record(request: Mapping[str, str]) -> dict[str, Any]:
    destination = request["destination_identity"]
    return {
        "request_index": int(request["request_index"]),
        "canonical_candidate_id": request["canonical_candidate_id"],
        "pdb_id": request["pdb_id"],
        "expected_ligand_component_id": request["expected_ligand_component_id"],
        "source_request_identity": request["source_request_identity"],
        "destination_identity": destination,
        "pre_execution_file_status": "ABSENT",
        "action_taken": "NONE",
        "network_attempted": False,
        "network_attempt_count": 0,
        "request_status": "NOT_ATTEMPTED",
        "response_or_transport_status": "NONE",
        "part_path": destination + ".part",
        **_validation_fields(None, "part"),
        "part_verified_before_promotion": False,
        "atomic_promotion_performed": False,
        "final_file_exists": False,
        "final_data_block_identity": "NONE",
        "final_sha256": "NONE",
        "final_size_bytes": 0,
        "final_pdb_identity_matches": False,
        "final_atom_site_parseable": False,
        "final_atom_site_row_count": 0,
        "final_atom_site_rh_present": False,
        "part_leftover": False,
        "acquisition_status": "FAILED",
        "primary_failure_code_or_NONE": "NONE",
    }


def _apply_final_validation(
    record: dict[str, Any], validation: RawPayloadValidation | None,
    final_exists: bool,
) -> None:
    record["final_file_exists"] = final_exists
    if validation is None:
        return
    record["final_data_block_identity"] = validation.data_block_identity
    record["final_sha256"] = validation.sha256
    record["final_size_bytes"] = validation.size_bytes
    record["final_pdb_identity_matches"] = validation.pdb_identity_matches
    record["final_atom_site_parseable"] = validation.atom_site_parseable
    record["final_atom_site_row_count"] = validation.atom_site_row_count
    record["final_atom_site_rh_present"] = validation.atom_site_rh_present


def _execute_request_v1(
    request: Mapping[str, str], *, repo_root: Path,
    transport: Transport,
) -> dict[str, Any]:
    record = _base_execution_record(request)
    final_path = repo_root / request["destination_identity"]
    part_path = final_path.with_suffix(final_path.suffix + ".part")
    pdb_id = request["pdb_id"]

    if final_path.exists():
        payload = final_path.read_bytes() if final_path.is_file() else b""
        validation = validate_raw_mmcif_payload_v1(payload, pdb_id)
        record["pre_execution_file_status"] = (
            "EXISTING_VALID" if validation.valid else "EXISTING_INVALID"
        )
        _apply_final_validation(record, validation, final_path.is_file())
        if validation.valid:
            record["action_taken"] = "REUSED_EXISTING_VALID"
            record["request_status"] = "NOT_ATTEMPTED_REUSED_EXISTING_VALID"
            record["response_or_transport_status"] = "NOT_APPLICABLE"
            record["acquisition_status"] = "VALID"
        else:
            record["action_taken"] = "FAILED_EXISTING_INVALID_NO_OVERWRITE"
            record["request_status"] = "NOT_ATTEMPTED_EXISTING_INVALID"
            record["response_or_transport_status"] = "NOT_APPLICABLE"
            record["primary_failure_code_or_NONE"] = (
                "EXISTING_INVALID_" + validation.failure_code
            )
        record["part_leftover"] = part_path.exists()
        return record

    if part_path.exists():
        record["action_taken"] = "FAILED_PREEXISTING_PART_NO_OVERWRITE"
        record["primary_failure_code_or_NONE"] = "PREEXISTING_PART_PRESENT"
        record["part_leftover"] = True
        return record

    final_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    os.chmod(final_path.parent, 0o755)
    record["network_attempted"] = True
    record["network_attempt_count"] = 1
    part_created = False
    part_validation: RawPayloadValidation | None = None
    try:
        try:
            response = transport(
                request["source_request_identity"], REQUEST_TIMEOUT_SECONDS,
            )
        except BoundedTransportError as exc:
            record["action_taken"] = "FAILED_TRANSPORT"
            record["request_status"] = "FAILED"
            record["response_or_transport_status"] = exc.code
            record["primary_failure_code_or_NONE"] = exc.code
            return record
        except Exception as exc:  # injected transports remain fail closed.
            code = (
                "TRANSPORT_TIMEOUT" if isinstance(exc, (TimeoutError, socket.timeout))
                else "TRANSPORT_UNCLASSIFIED_ERROR"
            )
            record["action_taken"] = "FAILED_TRANSPORT"
            record["request_status"] = "FAILED"
            record["response_or_transport_status"] = code
            record["primary_failure_code_or_NONE"] = code
            return record

        final_url = urlsplit(response.final_url)
        if final_url.scheme.lower() != "https" or final_url.hostname != SOURCE_HOST:
            record["action_taken"] = "FAILED_TRANSPORT"
            record["request_status"] = "FAILED"
            record["response_or_transport_status"] = (
                "CROSS_HOST_REDIRECT_FORBIDDEN"
            )
            record["primary_failure_code_or_NONE"] = (
                "CROSS_HOST_REDIRECT_FORBIDDEN"
            )
            return record
        if not 200 <= response.status_code < 300:
            code = f"HTTP_STATUS_{response.status_code}"
            record["action_taken"] = "FAILED_TRANSPORT"
            record["request_status"] = "FAILED"
            record["response_or_transport_status"] = code
            record["primary_failure_code_or_NONE"] = code
            return record

        record["request_status"] = "SUCCEEDED"
        record["response_or_transport_status"] = f"HTTP_{response.status_code}"
        part_path.write_bytes(response.payload)
        part_created = True
        os.chmod(part_path, 0o644)
        part_validation = validate_raw_mmcif_payload_v1(
            part_path.read_bytes(), pdb_id,
        )
        record.update(_validation_fields(part_validation, "part"))
        if not part_validation.valid:
            record["action_taken"] = "FAILED_DOWNLOADED_PAYLOAD_INVALID"
            record["primary_failure_code_or_NONE"] = part_validation.failure_code
            return record
        record["part_verified_before_promotion"] = True

        if final_path.exists():
            record["action_taken"] = "FAILED_FINAL_PATH_RACE_NO_OVERWRITE"
            record["primary_failure_code_or_NONE"] = (
                "FINAL_PATH_APPEARED_BEFORE_PROMOTION"
            )
            return record
        os.replace(part_path, final_path)
        part_created = False
        record["atomic_promotion_performed"] = True
        os.chmod(final_path, 0o644)

        final_validation = validate_raw_mmcif_payload_v1(
            final_path.read_bytes(), pdb_id,
        )
        _apply_final_validation(record, final_validation, True)
        same_bytes = (
            final_validation.sha256 == part_validation.sha256
            and final_validation.size_bytes == part_validation.size_bytes
        )
        if not final_validation.valid or not same_bytes:
            final_path.unlink()
            record["final_file_exists"] = False
            record["action_taken"] = "FAILED_FINAL_INTEGRITY_AFTER_PROMOTION"
            record["primary_failure_code_or_NONE"] = (
                "FINAL_BYTES_DIFFER_FROM_VERIFIED_PART"
                if not same_bytes else "FINAL_" + final_validation.failure_code
            )
            return record

        record["action_taken"] = "DOWNLOADED_AND_VERIFIED"
        record["acquisition_status"] = "VALID"
        record["primary_failure_code_or_NONE"] = "NONE"
        return record
    finally:
        if part_created and part_path.exists():
            part_path.unlink()
        record["part_leftover"] = part_path.exists()


def execute_exact12_targeted_acquisition_v1(
    authority: PublishedAuthority, *, repo_root: Path = REPO_ROOT,
    transport: Transport = _urllib_transport_v1,
) -> tuple[dict[str, Any], ...]:
    """Perform at most one primary request for each exact published identity."""

    requests = authority.request_rows
    if len(requests) != 12:
        raise ExecutionValidationError("EXACT12_EXECUTION_REQUEST_COUNT_INVALID")
    records = tuple(
        _execute_request_v1(request, repo_root=repo_root, transport=transport)
        for request in requests
    )
    if sum(int(row["network_attempt_count"]) for row in records) > 12:
        raise ExecutionValidationError("EXACT12_PRIMARY_ATTEMPT_LIMIT_EXCEEDED")
    if any(int(row["network_attempt_count"]) > 1 for row in records):
        raise ExecutionValidationError("EXACT12_IDENTITY_ATTEMPT_LIMIT_EXCEEDED")
    return records


def _post_acquisition_remaining_issue_v1(
    recovered: Mapping[str, Any], pdb_id: str,
) -> str:
    if bool(recovered["cys_sg_event_recovered"]):
        return str(recovered["primary_remaining_issue"])
    if recovered["explicit_connection_evidence_status"] == "STRUCT_CONN_LOOP_ABSENT":
        if pdb_id == "6VWE":
            return (
                "EXPLICIT_CONNECTION_AUTHORITY_ABSENT_IN_ACQUIRED_MMCIF_AND_"
                "CANONICAL_MODEL_GRAPH_RH_MEMBERSHIP_UNRESOLVED"
            )
        return (
            "EXPLICIT_CONNECTION_AUTHORITY_ABSENT_IN_ACQUIRED_MMCIF_"
            "HUMAN_STRUCTURAL_REVIEW_REQUIRED"
        )
    return (
        "PUBLISHED_STAGE_B0_" + str(recovered["structural_recovery_status"])
        + "_ON_ACQUIRED_RAW_HUMAN_STRUCTURAL_REVIEW_REQUIRED"
    )


def build_post_acquisition_recovery_snapshot_v1(
    execution_records: Sequence[Mapping[str, Any]], *,
    repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT,
) -> tuple[dict[str, Any], ...]:
    """Call the published Stage-B0 row recovery owner on exact valid raw paths."""

    source_rows, _ = stage_b0._load_and_validate_inputs(repo_root)
    source_by_candidate = {
        row["canonical_candidate_id"]: row for row in source_rows
    }
    snapshot: list[dict[str, Any]] = []
    for record in execution_records:
        source = source_by_candidate[record["canonical_candidate_id"]]
        final_path = repo_root / str(record["destination_identity"])
        valid = record["acquisition_status"] == "VALID"
        lookup = stage_b0.LocalEvidenceLookup(
            (final_path,) if valid else (), (), (),
        )
        recovered = stage_b0._missing_matrix_row(
            source, lookup, repo_root, state_root,
        )
        if valid and recovered["cys_sg_event_recovered"]:
            ligand_status = "EXPECTED_LIGAND_COMPONENT_MATCHED_EXPLICIT_EVENT"
        elif recovered["structural_recovery_status"] == "LIGAND_COMPONENT_MISMATCH":
            ligand_status = "EXPECTED_LIGAND_COMPONENT_MISMATCH"
        else:
            ligand_status = "UNRESOLVED_NO_EXPLICIT_EXACT_EVENT"
        snapshot.append({
            "canonical_candidate_id": record["canonical_candidate_id"],
            "pdb_id": record["pdb_id"],
            "ligand_component_id": record["expected_ligand_component_id"],
            "acquisition_status": record["acquisition_status"],
            "local_raw_structure_found": (
                bool(recovered["local_raw_structure_found"]) if valid
                else final_path.is_file()
            ),
            "raw_sha256": (
                record["final_sha256"] if final_path.is_file() else "NONE"
            ),
            "explicit_connection_evidence_status": (
                recovered["explicit_connection_evidence_status"] if valid
                else "NOT_EVALUATED_ACQUISITION_INVALID"
            ),
            "cys_sg_event_recovered": (
                bool(recovered["cys_sg_event_recovered"]) if valid else False
            ),
            "protein_chain_if_recovered": (
                recovered["protein_chain"] if valid else "NONE"
            ),
            "cys_residue_sequence_if_recovered": (
                recovered["cys_residue_sequence"] if valid else "NONE"
            ),
            "cys_insertion_code_if_recovered": (
                recovered["cys_insertion_code"] if valid else "NONE"
            ),
            "reactive_residue_atom_if_recovered": (
                recovered["reactive_residue_atom"] if valid else "NONE"
            ),
            "ligand_chain_or_instance_if_recovered": (
                recovered["ligand_chain_or_instance"] if valid else "NONE"
            ),
            "reactive_ligand_atom_if_recovered": (
                recovered["reactive_ligand_atom"] if valid else "NONE"
            ),
            "coordinate_status": (
                recovered["coordinate_status"] if valid
                else "NOT_EVALUATED_ACQUISITION_INVALID"
            ),
            "ligand_component_identity_status": (
                ligand_status if valid else "NOT_EVALUATED_ACQUISITION_INVALID"
            ),
            "structural_recovery_status": (
                recovered["structural_recovery_status"] if valid
                else "BLOCKED_ACQUISITION_INVALID"
            ),
            "recovery_disposition": (
                recovered["recovery_disposition"] if valid
                else "TARGETED_EXTERNAL_ACQUISITION_REQUIRED"
            ),
            "primary_remaining_issue": (
                _post_acquisition_remaining_issue_v1(
                    recovered, str(record["pdb_id"]),
                ) if valid
                else "BOUNDED_EXACT_IDENTITY_ACQUISITION_REMEDIATION_REQUIRED"
            ),
        })
    if len(snapshot) != 12:
        raise ExecutionValidationError("EXACT12_RECOVERY_SNAPSHOT_COUNT_INVALID")
    return tuple(snapshot)


def audit_exact_raw_git_safety_v1(
    request_rows: Sequence[Mapping[str, str]], *, repo_root: Path = REPO_ROOT,
) -> GitRawSafety:
    final_count = 0
    part_count = 0
    tracked_count = 0
    staged_count = 0
    ignored = True
    for request in request_rows:
        identity = request["destination_identity"]
        final_path = repo_root / identity
        part_path = final_path.with_suffix(final_path.suffix + ".part")
        final_count += final_path.is_file()
        part_count += part_path.exists()
        tracked = _run_git(repo_root, ["ls-files", "--", identity])
        staged = _run_git(
            repo_root, ["diff", "--cached", "--name-only", "--", identity],
        )
        ignore = _run_git(repo_root, ["check-ignore", "--quiet", "--", identity])
        if tracked.returncode != 0 or staged.returncode != 0:
            raise ExecutionValidationError("EXACT12_RAW_GIT_AUDIT_FAILED")
        tracked_count += bool(tracked.stdout.strip())
        staged_count += bool(staged.stdout.strip())
        ignored = ignored and ignore.returncode == 0
    return GitRawSafety(
        final_count, part_count, tracked_count, staged_count, ignored,
    )


def _manifest_from_records(
    execution_records: Sequence[Mapping[str, Any]],
    recovery_rows: Sequence[Mapping[str, Any]], safety: GitRawSafety,
    execution_payload: bytes, recovery_payload: bytes,
) -> dict[str, Any]:
    valid = [row for row in execution_records if row["acquisition_status"] == "VALID"]
    downloads = [
        row for row in execution_records
        if row["action_taken"] == "DOWNLOADED_AND_VERIFIED"
    ]
    failed = [row for row in execution_records if row["acquisition_status"] != "VALID"]
    exact_recovered = sum(bool(row["cys_sg_event_recovered"]) for row in recovery_rows)
    other_recovered = 0
    acquisition_valid = len(valid)
    all_valid = acquisition_valid == 12
    raw_git_safe = (
        safety.raw_tracked_count == safety.raw_staged_count == 0
        and safety.all_exact_paths_ignored
    )
    ready = (
        all_valid and safety.raw_final_file_count == 12
        and safety.part_leftover_count == 0 and raw_git_safe
        and len(recovery_rows) == 12
    )
    failed_identities = [
        f"{row['pdb_id']}/{row['expected_ligand_component_id']}" for row in failed
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_status": "COMPLETE" if all_valid else "INCOMPLETE",
        "baseline_commit": BASELINE_COMMIT,
        "published_authority_commit": PUBLISHED_AUTHORITY_COMMIT,
        "published_request_manifest_sha256":
            PUBLISHED_AUTHORITY_SHA256[REQUEST_PATH],
        "published_policy_contract_sha256":
            PUBLISHED_AUTHORITY_SHA256[POLICY_PATH],
        "published_authority_manifest_sha256":
            PUBLISHED_AUTHORITY_SHA256[AUTHORITY_MANIFEST_PATH],
        "published_authority_owner_sha256": PUBLISHED_AUTHORITY_SOURCE_SHA256,
        "formal_network_execution_owner_sha256":
            FORMAL_NETWORK_EXECUTION_OWNER_SHA256,
        "formal_network_execution_reexecuted_after_runtime_repair": False,
        "successor_runtime_compatibility_repair_applied_after_capture": True,
        "published_successor_runtime_compatible": True,
        "live_head_exact_authority_required": False,
        "live_origin_main_exact_authority_required": False,
        "ahead_behind_exact_authority_required": False,
        "atom_site_parser_owner_reused": ATOM_SITE_PARSER_OWNER,
        "stage_b0_recovery_owner_reused": RECOVERY_OWNER,
        "requested_identity_count": len(execution_records),
        "preexisting_valid_count": sum(
            row["pre_execution_file_status"] == "EXISTING_VALID"
            for row in execution_records
        ),
        "preexisting_invalid_count": sum(
            row["pre_execution_file_status"] == "EXISTING_INVALID"
            for row in execution_records
        ),
        "absent_before_execution_count": sum(
            row["pre_execution_file_status"] == "ABSENT"
            for row in execution_records
        ),
        "network_attempted_identity_count": sum(
            bool(row["network_attempted"]) for row in execution_records
        ),
        "network_request_count": sum(
            int(row["network_attempt_count"]) for row in execution_records
        ),
        "reused_existing_valid_count": sum(
            row["action_taken"] == "REUSED_EXISTING_VALID"
            for row in execution_records
        ),
        "downloaded_and_verified_count": len(downloads),
        "acquisition_failed_count": len(failed),
        "acquisition_valid_count": acquisition_valid,
        "all_exact12_acquisition_valid": all_valid,
        "raw_final_file_count": safety.raw_final_file_count,
        "part_leftover_count": safety.part_leftover_count,
        "raw_tracked_count": safety.raw_tracked_count,
        "raw_staged_count": safety.raw_staged_count,
        "raw_files_ignored_only": raw_git_safe,
        "raw_sha256_by_pdb": {
            row["pdb_id"]: row["final_sha256"] for row in valid
        },
        "raw_size_bytes_by_pdb": {
            row["pdb_id"]: row["final_size_bytes"] for row in valid
        },
        "atom_site_parseable_count": sum(
            bool(row["final_atom_site_parseable"]) for row in execution_records
        ),
        "part_verified_before_promotion_all_downloads": all(
            bool(row["part_verified_before_promotion"]) for row in downloads
        ),
        "atomic_promotion_all_downloads": all(
            bool(row["atomic_promotion_performed"]) for row in downloads
        ),
        "final_integrity_verified_all_valid": all(
            bool(row["final_pdb_identity_matches"])
            and bool(row["final_atom_site_parseable"])
            and row["final_sha256"] != "NONE"
            and int(row["final_size_bytes"]) > 0
            for row in valid
        ),
        "source_host_exact": all(
            urlsplit(str(row["source_request_identity"])).netloc == SOURCE_HOST
            for row in execution_records
        ),
        "cross_host_request_count": 0,
        "wildcard_request_count": 0,
        "automatic_retry_count": 0,
        "historical_1a54_raw_sha256": HISTORICAL_1A54_RAW_SHA256,
        "one_a54_current_raw_sha256": next(
            (row["final_sha256"] for row in valid if row["pdb_id"] == "1A54"),
            "NONE",
        ),
        "one_a54_historical_sha_matches_current": next((
            row["final_sha256"] == HISTORICAL_1A54_RAW_SHA256
            for row in valid if row["pdb_id"] == "1A54"
        ), False),
        "post_acquisition_snapshot_completed": len(recovery_rows) == 12,
        "struct_conn_exact_event_recovered_count": exact_recovered,
        "other_explicit_event_recovered_count": other_recovered,
        "exact_structural_event_recovered_count": exact_recovered + other_recovered,
        "no_explicit_event_recovered_count": (
            len(recovery_rows) - exact_recovered - other_recovered
        ),
        "post_acquisition_human_structural_review_count": sum(
            row["recovery_disposition"] == "HUMAN_STRUCTURAL_REVIEW_REQUIRED"
            for row in recovery_rows
        ),
        "post_acquisition_downstream_label_review_count": sum(
            row["recovery_disposition"]
            == "AUTO_RECOVERED_BUT_DOWNSTREAM_LABEL_REVIEW_REQUIRED"
            for row in recovery_rows
        ),
        "distance_only_inference_used": False,
        "six_vwe_raw_rh_observation_if_available": next((
            "ATOM_SITE_TYPE_SYMBOL_RH_PRESENT"
            if row["final_atom_site_rh_present"]
            else "ATOM_SITE_TYPE_SYMBOL_RH_NOT_OBSERVED"
            for row in valid if row["pdb_id"] == "6VWE"
        ), "UNAVAILABLE_ACQUISITION_INVALID"),
        "six_vwe_canonical_model_graph_rh_claim_created": False,
        "k36_ued_raw_structure_count": sum(
            (row["pdb_id"], row["expected_ligand_component_id"])
            in authority_owner.K36_UED_IDENTITIES for row in valid
        ),
        "failed_exact_identities": failed_identities,
        "network_request_executed": any(
            bool(row["network_attempted"]) for row in execution_records
        ),
        "targeted_acquisition_executed": True,
        "bulk_acquisition_executed": False,
        "inverse_reaction_reconstruction_executed": False,
        "pre_geometry_generation_executed": False,
        "torsion_enumeration_executed": False,
        "mmff_executed": False,
        "uff_executed": False,
        "rdkit_minimization_executed": False,
        "geometry_executed": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "trainer_fit": False,
        "training_executed": False,
        "rl": False,
        "published_authority_modified": False,
        "published_b0_modified": False,
        "published_stage_a_modified": False,
        "current11_modified": False,
        "deterministic_output_hashes": {
            EXECUTION_AUDIT_FILE: _sha256(execution_payload),
            RECOVERY_SNAPSHOT_FILE: _sha256(recovery_payload),
        },
        "captured_record_double_serialization_byte_identical": True,
        "manifest_self_sha256_recorded": False,
        "ready_for_execution_evidence_publication": ready,
        "ready_for_post_acquisition_structural_recovery_progression": ready,
        "ready_for_bulk_expansion": False,
        "ready_for_geometry_loss_activation": False,
        "ready_for_training": False,
        "recommended_next_step_exactly": (
            "review_and_publish_covapie_cys_sg_exact12_targeted_structural_"
            "evidence_acquisition_execution_v1"
            if ready else
            "remediate_only_failed_covapie_cys_sg_exact12_acquisition_"
            "identities_without_source_substitution_or_automatic_retry"
        ),
    }


def deserialize_execution_records_v1(
    payload: bytes,
) -> tuple[dict[str, Any], ...]:
    """Losslessly restore typed records from the immutable execution audit."""

    rows = _csv_rows(payload)
    if not rows or tuple(rows[0]) != EXECUTION_COLUMNS:
        raise ExecutionValidationError("EXACT12_EXECUTION_AUDIT_COLUMNS_INVALID")
    boolean_columns = {
        "network_attempted", "part_payload_nonempty", "part_html_detected",
        "part_pdb_identity_matches", "part_atom_site_parseable",
        "part_verified_before_promotion", "atomic_promotion_performed",
        "final_file_exists", "final_pdb_identity_matches",
        "final_atom_site_parseable", "final_atom_site_rh_present",
        "part_leftover",
    }
    integer_columns = {
        "request_index", "network_attempt_count", "part_atom_site_row_count",
        "part_size_bytes", "final_size_bytes", "final_atom_site_row_count",
    }
    typed_rows: list[dict[str, Any]] = []
    for row in rows:
        typed: dict[str, Any] = dict(row)
        for column in boolean_columns:
            if typed[column] not in {"true", "false"}:
                raise ExecutionValidationError(
                    f"EXACT12_EXECUTION_AUDIT_BOOLEAN_INVALID:{column}"
                )
            typed[column] = typed[column] == "true"
        for column in integer_columns:
            typed[column] = int(typed[column])
        typed_rows.append(typed)
    if len(typed_rows) != 12:
        raise ExecutionValidationError("EXACT12_EXECUTION_AUDIT_COUNT_INVALID")
    return tuple(typed_rows)


def deserialize_recovery_snapshot_v1(
    payload: bytes,
) -> tuple[dict[str, Any], ...]:
    """Losslessly restore typed rows from immutable recovery evidence."""

    rows = _csv_rows(payload)
    if not rows or tuple(rows[0]) != RECOVERY_COLUMNS:
        raise ExecutionValidationError("EXACT12_RECOVERY_SNAPSHOT_COLUMNS_INVALID")
    boolean_columns = {
        "local_raw_structure_found", "cys_sg_event_recovered",
    }
    typed_rows: list[dict[str, Any]] = []
    for row in rows:
        typed: dict[str, Any] = dict(row)
        for column in boolean_columns:
            if typed[column] not in {"true", "false"}:
                raise ExecutionValidationError(
                    f"EXACT12_RECOVERY_SNAPSHOT_BOOLEAN_INVALID:{column}"
                )
            typed[column] = typed[column] == "true"
        typed_rows.append(typed)
    if len(typed_rows) != 12:
        raise ExecutionValidationError("EXACT12_RECOVERY_SNAPSHOT_COUNT_INVALID")
    return tuple(typed_rows)


def build_execution_artifacts_v1(
    execution_records: Sequence[Mapping[str, Any]],
    recovery_rows: Sequence[Mapping[str, Any]], safety: GitRawSafety,
) -> dict[str, bytes]:
    """Serialize one immutable captured execution/recovery record set."""

    if len(execution_records) != 12 or len(recovery_rows) != 12:
        raise ExecutionValidationError("EXACT12_CAPTURE_CARDINALITY_INVALID")
    execution_payload = _csv_bytes(execution_records, EXECUTION_COLUMNS)
    recovery_payload = _csv_bytes(recovery_rows, RECOVERY_COLUMNS)
    manifest = _manifest_from_records(
        execution_records, recovery_rows, safety,
        execution_payload, recovery_payload,
    )
    return {
        EXECUTION_AUDIT_FILE: execution_payload,
        RECOVERY_SNAPSHOT_FILE: recovery_payload,
        EXECUTION_MANIFEST_FILE: _json_bytes(manifest),
    }


def materialize_execution_artifacts_v1(
    artifacts: Mapping[str, bytes],
    output_root: Path = REPO_ROOT / OUTPUT_ROOT,
) -> dict[str, str]:
    """Atomically materialize only the three exact execution evidence files."""

    if set(artifacts) != set(OUTPUT_FILES):
        raise ExecutionValidationError("EXACT12_EXECUTION_ARTIFACT_SET_INVALID")
    output_root.mkdir(parents=True, exist_ok=True, mode=0o755)
    os.chmod(output_root, 0o755)
    hashes: dict[str, str] = {}
    for filename in OUTPUT_FILES:
        path = output_root / filename
        temporary = path.with_suffix(path.suffix + ".tmp")
        try:
            temporary.write_bytes(artifacts[filename])
            os.chmod(temporary, 0o644)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        os.chmod(path, 0o644)
        hashes[filename] = _sha256(path.read_bytes())
    return hashes


def materialize_execution_artifacts_twice_v1(
    execution_records: Sequence[Mapping[str, Any]],
    recovery_rows: Sequence[Mapping[str, Any]], safety: GitRawSafety,
    output_root: Path = REPO_ROOT / OUTPUT_ROOT,
) -> tuple[dict[str, str], bool]:
    first = build_execution_artifacts_v1(execution_records, recovery_rows, safety)
    first_hashes = materialize_execution_artifacts_v1(first, output_root)
    first_disk = {
        filename: (output_root / filename).read_bytes() for filename in OUTPUT_FILES
    }
    second = build_execution_artifacts_v1(execution_records, recovery_rows, safety)
    second_hashes = materialize_execution_artifacts_v1(second, output_root)
    identical = (
        first == second == first_disk
        and all(
            (output_root / filename).read_bytes() == first[filename]
            for filename in OUTPUT_FILES
        )
        and first_hashes == second_hashes
    )
    if not identical:
        raise ExecutionValidationError(
            "EXACT12_CAPTURED_RECORD_DOUBLE_SERIALIZATION_MISMATCH"
        )
    return second_hashes, True


def rebuild_execution_manifest_from_captured_evidence_v1(
    output_root: Path = REPO_ROOT / OUTPUT_ROOT, *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Rebuild only the manifest; never rerun or rewrite captured CSV evidence."""

    validate_published_git_identity_v1(repo_root)
    authority = load_and_validate_published_authority_v1(repo_root)
    execution_path = output_root / EXECUTION_AUDIT_FILE
    recovery_path = output_root / RECOVERY_SNAPSHOT_FILE
    execution_payload = execution_path.read_bytes()
    recovery_payload = recovery_path.read_bytes()
    execution_records = deserialize_execution_records_v1(execution_payload)
    recovery_records = deserialize_recovery_snapshot_v1(recovery_payload)
    safety = audit_exact_raw_git_safety_v1(
        authority.request_rows, repo_root=repo_root,
    )
    first = build_execution_artifacts_v1(
        execution_records, recovery_records, safety,
    )
    second = build_execution_artifacts_v1(
        execution_records, recovery_records, safety,
    )
    if first != second:
        raise ExecutionValidationError(
            "EXACT12_CAPTURED_MANIFEST_REBUILD_NONDETERMINISTIC"
        )
    if first[EXECUTION_AUDIT_FILE] != execution_payload:
        raise ExecutionValidationError("EXACT12_EXECUTION_AUDIT_BYTE_DRIFT")
    if first[RECOVERY_SNAPSHOT_FILE] != recovery_payload:
        raise ExecutionValidationError("EXACT12_RECOVERY_SNAPSHOT_BYTE_DRIFT")

    manifest_path = output_root / EXECUTION_MANIFEST_FILE
    temporary = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    try:
        temporary.write_bytes(first[EXECUTION_MANIFEST_FILE])
        os.chmod(temporary, 0o644)
        os.replace(temporary, manifest_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    os.chmod(manifest_path, 0o644)
    return {
        "execution_audit_bytes_unchanged": True,
        "recovery_snapshot_bytes_unchanged": True,
        "captured_execution_roundtrip_byte_identical": True,
        "captured_recovery_roundtrip_byte_identical": True,
        "deterministic_manifest_rebuild_proved": True,
        "new_execution_manifest_sha256": _sha256(
            first[EXECUTION_MANIFEST_FILE]
        ),
        "new_network_request_count": 0,
        "formal_network_execution_reexecuted_after_runtime_repair": False,
    }


def run_formal_exact12_execution_v1(
    *, repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT,
    output_root: Path | None = None,
    transport: Transport = _urllib_transport_v1,
) -> dict[str, Any]:
    """Perform the one bounded formal execution and materialize its evidence."""

    validate_published_git_identity_v1(repo_root)
    authority = load_and_validate_published_authority_v1(repo_root)
    records = execute_exact12_targeted_acquisition_v1(
        authority, repo_root=repo_root, transport=transport,
    )
    recovery = build_post_acquisition_recovery_snapshot_v1(
        records, repo_root=repo_root, state_root=state_root,
    )
    safety = audit_exact_raw_git_safety_v1(
        authority.request_rows, repo_root=repo_root,
    )
    target = output_root or repo_root / OUTPUT_ROOT
    hashes, identical = materialize_execution_artifacts_twice_v1(
        records, recovery, safety, target,
    )
    manifest = json.loads((target / EXECUTION_MANIFEST_FILE).read_bytes())
    return {
        "execution_status": manifest["execution_status"],
        "network_request_count": manifest["network_request_count"],
        "acquisition_valid_count": manifest["acquisition_valid_count"],
        "exact_structural_event_recovered_count":
            manifest["exact_structural_event_recovered_count"],
        "candidate_sha256": hashes,
        "captured_record_double_serialization_byte_identical": identical,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute-exact12", action="store_true",
        help="perform the single published exact12 bounded acquisition",
    )
    args = parser.parse_args(argv)
    if not args.execute_exact12:
        parser.error("formal execution requires --execute-exact12")
    os.umask(0o022)
    print(json.dumps(run_formal_exact12_execution_v1(), sort_keys=True))


if __name__ == "__main__":
    main()
