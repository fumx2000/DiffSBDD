"""Source-bound ingestion of the approved POA 4I3U Exact8 Task C seed.

This module compiles text and JSON evidence only.  Its public loader has no
caller-supplied decision path, digest, or bypass: it always reads the frozen
signed record and its fixed supporting sources.  The result is sample-level
metadata for a later A1 consumer; it does not activate runtime authority,
admit training samples, change masks, or execute a model.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn


__all__ = (
    "AUTHORITY_INGESTION_SCHEMA_V1",
    "SIGNED_DECISION_RELATIVE_PATH_V1",
    "SIGNED_DECISION_SHA256_V1",
    "load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1",
    "validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1",
    "serialize_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1",
)


INGESTION_ERROR = (
    "COVAPIE_POA_4I3U_EXACT8_TASK_C_SEED_ANCHOR_AUTHORITY_INGESTION_V1_ERROR"
)
AUTHORITY_INGESTION_SCHEMA_V1 = (
    "covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1"
)
FORMAL_DECISION_SCHEMA_V1 = (
    "covapie_poa_4i3u_exact8_task_c_seed_anchor_formal_human_decision_v1"
)
RESULT_RECORD_ROLE_V1 = (
    "SOURCE_BOUND_SAMPLE_LEVEL_TASK_C_SEED_ANCHOR_AUTHORITY_INGESTION_RESULT_"
    "NOT_RUNTIME_ACTIVATION"
)
BASELINE_COMMIT_V1 = "b8f7353218c33bd580796e7b663da2c0c1b9cd2a"
REVIEW_UNIT_RELATIVE_PATH_V1 = Path(
    "manual-review-aids/cumulative1000-high-yield-calibration-v1/"
    "POA_COVAPIE_BULK_REVIEW_UNIT_6A4D564E712634EB"
)
SIGNED_DECISION_RELATIVE_PATH_V1 = REVIEW_UNIT_RELATIVE_PATH_V1 / (
    "task-c-seed-anchor-formal-human-decision-v1/"
    "poa_4i3u_exact8_task_c_seed_anchor_formal_human_decision_v1.json"
)
SIGNED_DECISION_SHA256_V1 = (
    "701c119016a0cbfe2c5d5884b3ba0bdb04daff00fc8fa404ef6087d1d0cb6e1b"
)

_SIGNED_DECISION_BYTES_V1 = 37499
_SIGNED_DECISION_MODE_V1 = 0o664
_SIGNED_RECORD_ROLE_V1 = (
    "SAMPLE_LEVEL_HUMAN_APPROVED_SEED_ANCHOR_DECISION_AWAITING_PROGRAMMATIC_"
    "AUTHORITY_INGESTION"
)
_CANDIDATE_ID_V1 = "POA_4I3U_EXACT8_TASK_C_SEED_CANDIDATE_01"
_SEED_ATOM_IDS_V1 = ("P", "O1P")
_ANCHOR_ATOM_ID_V1 = "P"
_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:A:CYS:291-:SG:I:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:B:CYS:291-:SG:J:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:C:CYS:291-:SG:K:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:D:CYS:291-:SG:L:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:E:CYS:291-:SG:M:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:F:CYS:291-:SG:N:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:G:CYS:291-:SG:O:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:H:CYS:291-:SG:P:POA:C2",
)
_CHAINS_V1 = tuple("ABCDEFGH")
_LIGAND_ASYMS_V1 = tuple("IJKLMNOP")
_ROLE_ATOMS_V1 = {
    "scaffold": ("P", "O1P", "O2P", "O3P"),
    "linker": ("C1",),
    "warhead": ("C2", "O2"),
}
_ROLE_IDS_V1 = {"scaffold": 0, "linker": 1, "warhead": 2}
_ATOM_TYPES_V1 = {
    "C1": "C", "C2": "C", "O2": "O", "O1P": "O",
    "O2P": "O", "O3P": "O", "P": "P",
}
_B1_ATOM_ORDER_V1 = ("C1", "C2", "O2", "O1P", "O2P", "O3P", "P")
_CANONICAL_MASKS_V1 = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
_UTC_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)


def _state_path(suffix: str) -> str:
    return (REVIEW_UNIT_RELATIVE_PATH_V1 / suffix).as_posix()


_SOURCE_SPECS_V1 = (
    {
        "key": "choice",
        "root": "state",
        "path": _state_path(
            "task-c-seed-anchor-human-decision-candidate-v1/"
            "poa_4i3u_exact8_task_c_seed_anchor_human_choice_candidate_v1.json"
        ),
        "path_namespace": "covapie_state_root_relative",
        "role": "bound_human_choice_candidate",
        "schema_version": (
            "covapie_poa_4i3u_exact8_task_c_seed_anchor_human_choice_candidate_v1"
        ),
        "bytes": 34315,
        "mode": "0664",
        "sha256": "67ab9fd8c54790380d53bc4a490a830a31903c96968ab85c46fe8c46a9f7fe73",
    },
    {
        "key": "packet",
        "root": "state",
        "path": _state_path(
            "task-c-seed-anchor-review-preparation-v1/"
            "poa_4i3u_exact8_task_c_seed_anchor_review_packet_v1.json"
        ),
        "path_namespace": "covapie_state_root_relative",
        "role": "frozen_seed_anchor_review_packet",
        "schema_version": (
            "covapie_poa_4i3u_exact8_task_c_seed_anchor_review_packet_v1"
        ),
        "bytes": 111521,
        "sha256": "a21501edbb650457ffd72725d28a1e61f317cbbd9a3f8db2ba4d039c05222597",
    },
    {
        "key": "guide",
        "root": "state",
        "path": _state_path(
            "task-c-seed-anchor-review-preparation-v1/"
            "poa_4i3u_exact8_task_c_seed_anchor_review_guide_v1.md"
        ),
        "path_namespace": "covapie_state_root_relative",
        "role": "frozen_seed_anchor_review_guide",
        "bytes": 9443,
        "sha256": "76e5249c291cea385b5e3f757683ce3a49fbb2943cf81939937235b6c5d1d975",
    },
    {
        "key": "template",
        "root": "state",
        "path": _state_path(
            "task-c-seed-anchor-review-preparation-v1/"
            "poa_4i3u_exact8_task_c_seed_anchor_decision_template_v1.json"
        ),
        "path_namespace": "covapie_state_root_relative",
        "role": "frozen_unsigned_decision_template_unchanged",
        "bytes": 2879,
        "sha256": "6f53a8f394a18285afbfb4aef7cb0c47e01454ed360a6a7c0053a06747b08265",
    },
    {
        "key": "b1",
        "root": "repository",
        "path": (
            "data/derived/covalent_small/"
            "covapie_poa_4i3u_exact8_real_preview_evidence_v1/"
            "poa_4i3u_exact8_real_preview_evidence_v1.json"
        ),
        "path_namespace": "repository_root_relative",
        "role": "published_B1_structure_mapping_evidence",
        "baseline_commit": BASELINE_COMMIT_V1,
        "git_blob_sha1": "5fd595ca9923d4d6339446cf74d872a74ac78c23",
        "bytes": 1522292,
        "sha256": "98d4ec2e0d8c6fc00816a70b5927240f437d7e8d64a0981751ddc93684906d40",
    },
    {
        "key": "b1_implementation",
        "root": "repository",
        "path": "src/covalent_ext/covapie_poa_4i3u_exact8_real_preview_evidence_v1.py",
        "path_namespace": "repository_root_relative",
        "role": "published_B1_implementation",
        "baseline_commit": BASELINE_COMMIT_V1,
        "git_blob_sha1": "2dbba7c5e800b609293750f626b01d5f2b064716",
        "bytes": 49717,
        "sha256": "854dd063ac822d7b8e7ddad7a887ec9fd7c78645e09a2166bbc4d46b0ac01649",
    },
    {
        "key": "role_decision",
        "root": "state",
        "path": _state_path(
            "formal-human-decision-v1/poa_formal_human_decision_v1.json"
        ),
        "path_namespace": "covapie_state_root_relative",
        "role": "formal_human_role_and_event_decision",
        "bytes": 15675,
        "sha256": "263eec2e33a7b50001f6c058959b9218601fc7fb122dc97e937b517f98c90ba8",
    },
    {
        "key": "topology",
        "root": "state",
        "path": _state_path("poa_ccd_reactive_center_topology_v1.json"),
        "path_namespace": "covapie_state_root_relative",
        "role": "formal_decision_bound_CCD_topology_evidence",
        "bytes": 21568,
        "sha256": "fdde10c5e50ce56e58bb5f57ffaa31ee87100161f7f63d9a1d1920f7e31b46c1",
    },
    {
        "key": "validator",
        "root": "repository",
        "path": (
            "src/covalent_ext/"
            "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
        ),
        "path_namespace": "repository_root_relative",
        "role": "published_pure_minimal_seed_validator",
        "baseline_commit": BASELINE_COMMIT_V1,
        "git_blob_sha1": "502f9e5b7b5ace1c67dc7fda59e17d1a6172a76d",
        "bytes": 67274,
        "sha256": "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        "function": "validate_minimal_seed",
        "function_source_bytes": 3040,
        "function_source_sha256": (
            "b7ae45534ccc4e83744c7fb5c3c1ed0227f0c9349c7e7e8b63cf3cc342bdc855"
        ),
    },
)


class _InvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _InvariantError()


def _dict(value: object) -> dict[str, object]:
    if type(value) is not dict:
        _fail()
    return value  # type: ignore[return-value]


def _list(value: object, *, length: int | None = None) -> list[object]:
    if type(value) is not list or (length is not None and len(value) != length):
        _fail()
    return value  # type: ignore[return-value]


def _text(value: object) -> str:
    if type(value) is not str or not value:
        _fail()
    return value


def _integer(value: object) -> int:
    if type(value) is not int:
        _fail()
    return value


def _strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        left_dict = left  # type: ignore[assignment]
        right_dict = right  # type: ignore[assignment]
        return set(left_dict) == set(right_dict) and all(
            _strict_equal(left_dict[key], right_dict[key]) for key in left_dict
        )
    if type(left) is list:
        return len(left) == len(right) and all(  # type: ignore[arg-type]
            _strict_equal(a, b) for a, b in zip(left, right, strict=True)  # type: ignore[arg-type]
        )
    return left == right


def _expect(value: object, expected: object) -> None:
    if not _strict_equal(value, expected):
        _fail()


def _reject_constant(_: str) -> NoReturn:
    _fail()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def _strict_json(payload: object) -> dict[str, object]:
    if type(payload) is not bytes:
        _fail()
    try:
        text = payload.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except _InvariantError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail()
    return _dict(value)


def _canonical_json_bytes(value: object, *, newline: bool = False) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        _fail()
    return (rendered + ("\n" if newline else "")).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _validate_utc_timestamp(value: object) -> str:
    text = _text(value)
    if _UTC_TIMESTAMP.fullmatch(text) is None:
        _fail()
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        _fail()
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        _fail()
    return text


def _binding_from_spec(spec: dict[str, object]) -> dict[str, object]:
    excluded = {"key", "root"}
    return {key: copy.deepcopy(value) for key, value in spec.items() if key not in excluded}


def _source_identity_projection() -> list[dict[str, object]]:
    return [_binding_from_spec(spec) for spec in _SOURCE_SPECS_V1]


def _resolve_root(value: object) -> Path:
    if not isinstance(value, Path):
        _fail()
    try:
        root = value.resolve(strict=True)
    except OSError:
        _fail()
    if not root.is_dir():
        _fail()
    return root


def _read_fixed_file(root: Path, spec: dict[str, object]) -> bytes:
    relative = Path(_text(spec["path"]))
    if relative.is_absolute() or ".." in relative.parts:
        _fail()
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if resolved != path.absolute():
            _fail()
        metadata = path.lstat()
        payload = path.read_bytes()
    except (OSError, ValueError):
        _fail()
    if not stat.S_ISREG(metadata.st_mode):
        _fail()
    if "mode" in spec and stat.S_IMODE(metadata.st_mode) != int(_text(spec["mode"]), 8):
        _fail()
    if len(payload) != _integer(spec["bytes"]) or _sha256(payload) != _text(spec["sha256"]):
        _fail()
    if spec["root"] == "repository" and _git_blob_sha1(payload) != _text(spec["git_blob_sha1"]):
        _fail()
    return payload


def _git_output(repository_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository_root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        _fail()
    return completed.stdout.strip()


def _validate_repository_lineage(repository_root: Path) -> None:
    _git_output(
        repository_root,
        "merge-base",
        "--is-ancestor",
        BASELINE_COMMIT_V1,
        "HEAD",
    )
    for spec in _SOURCE_SPECS_V1:
        if spec["root"] != "repository":
            continue
        actual = _git_output(
            repository_root,
            "rev-parse",
            f"{BASELINE_COMMIT_V1}:{spec['path']}",
        )
        if actual != spec["git_blob_sha1"]:
            _fail()


def _load_bound_source_bytes(
    *, repository_root: object, state_root: object
) -> dict[str, bytes]:
    repository = _resolve_root(repository_root)
    state = _resolve_root(state_root)
    if repository == state:
        _fail()
    _validate_repository_lineage(repository)
    signed_spec = {
        "path": SIGNED_DECISION_RELATIVE_PATH_V1.as_posix(),
        "root": "state",
        "bytes": _SIGNED_DECISION_BYTES_V1,
        "mode": "0664",
        "sha256": SIGNED_DECISION_SHA256_V1,
    }
    bundle = {"signed": _read_fixed_file(state, signed_spec)}
    for spec in _SOURCE_SPECS_V1:
        root = state if spec["root"] == "state" else repository
        bundle[_text(spec["key"])] = _read_fixed_file(root, spec)
    return bundle


def _selection_core(value: object) -> dict[str, object]:
    selection = _dict(value)
    core = {
        "selected_seed_candidate_id": selection.get("selected_seed_candidate_id"),
        "selected_minimal_seed_atom_ids": selection.get("selected_minimal_seed_atom_ids"),
        "selected_primary_anchor_atom_id": selection.get("selected_primary_anchor_atom_id"),
        "apply_to_event_ids": selection.get("apply_to_event_ids"),
        "apply_to_exact_event_count": selection.get("apply_to_exact_event_count"),
        "scope_explicitly_limited_to_this_exact8": selection.get(
            "scope_explicitly_limited_to_this_exact8"
        ),
    }
    expected = {
        "selected_seed_candidate_id": _CANDIDATE_ID_V1,
        "selected_minimal_seed_atom_ids": list(_SEED_ATOM_IDS_V1),
        "selected_primary_anchor_atom_id": _ANCHOR_ATOM_ID_V1,
        "apply_to_event_ids": list(_EVENT_IDS_V1),
        "apply_to_exact_event_count": 8,
        "scope_explicitly_limited_to_this_exact8": True,
    }
    _expect(core, expected)
    event_ids = _list(core["apply_to_event_ids"], length=8)
    if len(set(event_ids)) != 8 or any(type(item) is not str for item in event_ids):
        _fail()
    return copy.deepcopy(core)


def _validate_signed_decision(signed: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    _expect(signed.get("schema_version"), FORMAL_DECISION_SCHEMA_V1)
    _expect(signed.get("record_role"), _SIGNED_RECORD_ROLE_V1)
    _expect(signed.get("decision_status"), "HUMAN_APPROVED_SIGNED_RECORD_NOT_INGESTED")
    _expect(signed.get("human_approval_recorded"), True)
    _expect(signed.get("formal_signed_decision_record_created"), True)
    _expect(signed.get("review_unit_id"), "COVAPIE_BULK_REVIEW_UNIT_6A4D564E712634EB")
    _expect(signed.get("ligand_component_id"), "POA")

    approval = _dict(signed.get("human_approval"))
    for key, expected in (
        ("approval_recorded", True),
        ("reviewer_id", "fmx"),
        ("attestor_id", "fmx"),
        ("approval_time_semantic", "ACTUAL_UTC_TIME_OF_THIS_APPROVAL_RECORD_REGISTRATION"),
        ("approval_time_source", "SYSTEM_UTC_CLOCK_CAPTURED_IMMEDIATELY_BEFORE_RECORD_MATERIALIZATION"),
        ("cryptographic_signature_created", False),
        ("certificate_or_third_party_identity_verification_claimed", False),
    ):
        _expect(approval.get(key), expected)
    approved_at = _validate_utc_timestamp(approval.get("approved_at_utc"))

    gate = _dict(signed.get("approval_gate"))
    for key, expected in (
        ("approval_gate_status", "PASS"),
        ("explicit_approval_for_this_exact_registered_choice_present", True),
        ("reviewer_id_present_and_not_placeholder", True),
        ("attestor_id_present_and_not_placeholder", True),
        ("reviewer_and_attestor_roles_explicitly_confirmed_in_this_approval", True),
        ("reviewer_and_attestor_same_identity", True),
        ("third_party_attestation_claimed", False),
    ):
        _expect(gate.get(key), expected)

    bindings = _list(signed.get("source_bindings"), length=len(_SOURCE_SPECS_V1))
    _expect(bindings, _source_identity_projection())
    selection = _selection_core(signed.get("approved_selection"))
    approved = _dict(signed.get("approved_selection"))
    _expect(
        approved.get("apply_to_event_ids_source"),
        "bound_human_choice_candidate.selection.apply_to_event_ids_cross_checked_with_frozen_packet",
    )
    _expect(approved.get("excluded_event_scopes"), ["4I3V", "4I3W", "G3H", "all_other_events"])

    nonclaims = _dict(signed.get("approved_scope_and_nonclaims"))
    _expect(
        nonclaims.get("approval_scope"),
        "SAMPLE_LEVEL_TASK_C_MINIMAL_SEED_AND_PRIMARY_ANCHOR_FOR_BOUND_4I3U_EXACT8_ONLY",
    )
    for key in (
        "A1_consumer_adapter_completion_inferred",
        "PRE_or_POST_geometry_authority_inferred",
        "geometry_supervision_changed_or_approved",
        "reactive_pair_changed",
        "role_decision_changed",
        "seed_atoms_should_now_be_set_fixed_inferred",
        "task_C_generated_or_fixed_mask_changed",
        "training_admission_granted",
        "training_readiness_inferred",
    ):
        _expect(nonclaims.get(key), False)

    execution = _dict(signed.get("authority_and_execution_boundary"))
    for key in (
        "AUTHORITY_INGESTION_COMPLETED",
        "CHECKPOINT_ACCESSED",
        "CURRENT_TRAIN12_POPULATION_CHANGED",
        "FORWARD_LOSS_OR_BACKWARD_EXECUTED",
        "GEOMETRY_VALID_OR_LOSS_CHANGED",
        "NEW_FORMAL_ADMISSION_CREATED",
        "PARAMETER_UPDATE_PERFORMED",
        "READY_FOR_TRAINING",
        "REAL_MODEL_EXECUTED",
        "RUNTIME_SEED_AUTHORITY_ACTIVATED",
        "STRUCTURE_PREVIEW_REBUILT",
        "TASK_C_MASK_MODIFIED",
        "TRAINING_CONSUMER_ADAPTER_CREATED",
    ):
        _expect(execution.get(key), False)
    _expect(execution.get("FORMAL_SIGNED_DECISION_RECORD_CREATED"), True)
    _expect(execution.get("HUMAN_APPROVED_SEED_ANCHOR_DECISION_RECORDED"), True)
    _expect(execution.get("FEATURE_SEMANTICS_OR_USE_AUDIT_REQUIRED_LATER"), True)
    _expect(execution.get("STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK"), True)

    mask_boundary = _dict(signed.get("canonical_mask_and_consumer_boundary"))
    _expect(mask_boundary.get("canonical_semantic_long_names"), list(_CANONICAL_MASKS_V1))
    _expect(mask_boundary.get("canonical_task_count"), 5)
    _expect(mask_boundary.get("scaffold_only_B3_present"), True)
    _expect(mask_boundary.get("task_C_fixed_atom_count_per_event"), 0)
    _expect(mask_boundary.get("task_C_generated_atom_count_per_event"), 7)
    _expect(mask_boundary.get("task_C_mask_modified"), False)

    programmatic = _dict(signed.get("programmatic_acceptance_status"))
    _expect(programmatic.get("AUTHORITY_INGESTION_COMPLETED"), False)
    _expect(programmatic.get("RUNTIME_SEED_AUTHORITY_ACTIVATED"), False)
    _expect(programmatic.get("TENSORIZER_ACCEPTANCE_CLAIMED"), False)
    _expect(programmatic.get("TRAINING_ENTRYPOINT_ACCEPTANCE_CLAIMED"), False)
    return selection, {
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": approved_at,
        "approval_time_semantic": approval["approval_time_semantic"],
        "approval_time_source": approval["approval_time_source"],
        "same_identity_dual_role_explicitly_allowed": True,
        "cryptographic_signature_verified": False,
        "third_party_identity_verified": False,
    }


def _validate_choice_and_packet(
    choice: dict[str, object], packet: dict[str, object], selection: dict[str, object]
) -> None:
    _expect(
        choice.get("schema_version"),
        "covapie_poa_4i3u_exact8_task_c_seed_anchor_human_choice_candidate_v1",
    )
    _expect(choice.get("record_role"), "HUMAN_CHOICE_CANDIDATE_PENDING_FORMAL_REVIEW_NOT_AUTHORITY")
    _expect(choice.get("decision_status"), "CANDIDATE_UNSIGNED_NOT_FORMAL")
    _expect(_selection_core(choice.get("selection")), selection)

    _expect(
        packet.get("schema_version"),
        "covapie_poa_4i3u_exact8_task_c_seed_anchor_review_packet_v1",
    )
    _expect(packet.get("record_role"), "HUMAN_REVIEW_PREPARATION_CANDIDATES_NOT_AUTHORITY")
    scope = _dict(packet.get("review_scope"))
    _expect(scope.get("canonical_event_ids_in_order"), list(_EVENT_IDS_V1))
    _expect(scope.get("exact_event_count"), 8)
    _expect(scope.get("pdb_id"), "4I3U")
    task = _dict(scope.get("canonical_task"))
    _expect(task, {"canonical_task_id": 4, "semantic_long_name": _CANONICAL_MASKS_V1[-1], "short_alias": "C"})

    candidates = _list(packet.get("minimal_seed_candidates"))
    selected = [
        _dict(row) for row in candidates
        if _dict(row).get("candidate_id") == _CANDIDATE_ID_V1
    ]
    if len(selected) != 1:
        _fail()
    candidate = selected[0]
    _expect(candidate.get("minimal_seed_atom_ids"), list(_SEED_ATOM_IDS_V1))
    _expect(candidate.get("minimal_seed_atom_count"), 2)
    options = _list(candidate.get("primary_anchor_options"), length=2)
    _expect([_dict(row).get("atom_id") for row in options], list(_SEED_ATOM_IDS_V1))
    _expect(_dict(options[0]).get("validator_local_index_0based"), 6)
    _expect(_dict(options[1]).get("validator_local_index_0based"), 2)
    _expect(candidate.get("published_validator_result"), "PASS_FOR_EVERY_LISTED_PRIMARY_ANCHOR")


def _validate_role_and_topology(
    role: dict[str, object], topology: dict[str, object]
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    _expect(role.get("schema_version"), "covapie_poa_formal_human_decision_v1")
    _expect(role.get("record_role"), "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY")
    _expect(role.get("decision_status"), "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION")
    role_decision = _dict(role.get("role_human_decision"))
    for name, atoms in _ROLE_ATOMS_V1.items():
        _expect(role_decision.get(f"{name}_atom_ids"), list(atoms))
    _expect(role_decision.get("exact_ccd_heavy_atom_ids"), ["C1", "C2", "O1P", "O2", "O2P", "O3P", "P"])
    _expect(role_decision.get("sample_specific_role_decision_created"), True)
    _expect(role_decision.get("reusable_role_authority_created"), False)
    subgroups = _list(role.get("subgroup_human_decisions"), length=2)
    first_group = _dict(subgroups[0])
    _expect(first_group.get("canonical_event_ids"), list(_EVENT_IDS_V1))
    _expect(first_group.get("event_count"), 8)
    _expect(first_group.get("pdb_id"), "4I3U")
    _expect(first_group.get("training_admission_created"), False)

    _expect(topology.get("schema_version"), "covapie_poa_ccd_reactive_center_topology_v1")
    heavy_atoms = _list(topology.get("heavy_atoms"), length=7)
    atom_types: dict[str, str] = {}
    for raw_atom in heavy_atoms:
        atom = _dict(raw_atom)
        atom_id = _text(atom.get("atom_id"))
        element = _text(atom.get("element"))
        if atom_id in atom_types:
            _fail()
        atom_types[atom_id] = element
    _expect(atom_types, _ATOM_TYPES_V1)
    heavy_bonds = _list(topology.get("heavy_bonds"), length=6)
    bond_set: set[tuple[str, str]] = set()
    for raw_bond in heavy_bonds:
        bond = _dict(raw_bond)
        left = _text(bond.get("atom_id_1"))
        right = _text(bond.get("atom_id_2"))
        edge = tuple(sorted((left, right)))
        if edge in bond_set or left not in atom_types or right not in atom_types:
            _fail()
        bond_set.add(edge)
    expected_bonds = {
        tuple(sorted(edge)) for edge in (
            ("C1", "C2"), ("C1", "P"), ("C2", "O2"),
            ("P", "O1P"), ("P", "O2P"), ("P", "O3P"),
        )
    }
    if bond_set != expected_bonds:
        _fail()
    scaffold_edges = [("P", "O1P"), ("P", "O2P"), ("P", "O3P")]
    role_by_atom = {
        atom_id: role_name
        for role_name, atoms in _ROLE_ATOMS_V1.items()
        for atom_id in atoms
    }
    return role_by_atom, scaffold_edges


def _validate_b1_boundaries(b1: dict[str, object]) -> list[dict[str, object]]:
    _expect(b1.get("schema_version"), "covapie_poa_4i3u_exact8_real_preview_evidence_v1")
    population = _dict(b1.get("population"))
    _expect(population.get("target_event_count"), 8)
    _expect(population.get("target_event_ids_in_order"), list(_EVENT_IDS_V1))
    _expect(population.get("G3H_or_other_structure_read"), False)
    summary = _dict(b1.get("summary"))
    _expect(summary.get("sample_count"), 8)
    _expect(summary.get("sample_training_admitted_count"), 0)
    _expect(summary.get("task_C_minimal_seed_authority_count"), 0)
    _expect(summary.get("canonical_mask_count"), 5)
    _expect(summary.get("canonical_exact5_includes_B3_and_C"), True)
    events = [_dict(row) for row in _list(b1.get("events"), length=8)]
    _expect([row.get("canonical_event_id") for row in events], list(_EVENT_IDS_V1))
    for ordinal, event in enumerate(events):
        _expect(event.get("sample_ordinal_0based"), ordinal)
        metadata = _dict(event.get("formal_metadata"))
        for key, expected in (
            ("pdb_id", "4I3U"),
            ("protein_chain", _CHAINS_V1[ordinal]),
            ("ligand_component_id", "POA"),
            ("ligand_label_asym_id", _LIGAND_ASYMS_V1[ordinal]),
            ("training_use_disposition", "INCLUDE"),
            ("training_admitted", False),
        ):
            _expect(metadata.get(key), expected)
        masks = [_dict(row) for row in _list(event.get("canonical_exact5_structural_masks"), length=5)]
        _expect([row.get("semantic_long_name") for row in masks], list(_CANONICAL_MASKS_V1))
        task_c = masks[4]
        _expect(task_c.get("short_alias"), "C")
        _expect(task_c.get("fixed_atom_local_indices"), [])
        _expect(task_c.get("fixed_count"), 0)
        _expect(task_c.get("generated_atom_local_indices"), list(range(7)))
        _expect(task_c.get("generated_count"), 7)
        _expect(task_c.get("minimal_seed_authority_created"), False)
    return events


def _mapping_from_atom(atom: dict[str, object], approved_role: str) -> dict[str, object]:
    return {
        "atom_id": _text(atom.get("atom_id")),
        "type_symbol": _text(atom.get("type_symbol")),
        "approved_role": approved_role,
        "B1_role_id": _integer(atom.get("role_id")),
        "atom_site_id": _text(atom.get("atom_site_id")),
        "source_atom_site_row_index_0based": _integer(atom.get("source_atom_site_row_index_0based")),
        "extractor_parser_local_index_0based": _integer(atom.get("extractor_parser_local_index_0based")),
        "model_parser_local_index_0based": _integer(atom.get("model_parser_local_index_0based")),
        "model_sample_local_index_0based": _integer(atom.get("model_sample_local_index_0based")),
        "model_flat_index_0based": _integer(atom.get("model_flat_index_0based")),
    }


def _mapping_without_role(mapping: dict[str, object]) -> dict[str, object]:
    omitted = {"type_symbol", "approved_role", "B1_role_id"}
    return {key: copy.deepcopy(value) for key, value in mapping.items() if key not in omitted}


def _validate_minimal_seed_call(
    *, seed: list[int], scaffold: list[int], linker: list[int],
    warhead: list[int], scaffold_edges: list[tuple[int, int]], anchor: int,
) -> None:
    try:
        from covalent_ext.covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1 import (
            validate_minimal_seed,
        )
    except (ImportError, AttributeError):
        _fail()
    reasons = validate_minimal_seed(
        seed, scaffold, linker, warhead, scaffold_edges, anchor
    )
    if type(reasons) is not tuple or reasons:
        _fail()


def _compile_event_records(
    *, signed: dict[str, object], choice: dict[str, object], packet: dict[str, object],
    b1_events: list[dict[str, object]], role_by_atom: dict[str, str],
    scaffold_edges_by_atom: list[tuple[str, str]],
) -> list[dict[str, object]]:
    signed_mappings = [_dict(row) for row in _list(signed.get("per_event_approved_seed_and_anchor_mappings"), length=8)]
    choice_mappings = [_dict(row) for row in _list(choice.get("per_event_selected_atom_and_index_mappings"), length=8)]
    packet_events = [_dict(row) for row in _list(packet.get("event_atom_and_candidate_mappings"), length=8)]
    _expect([row.get("canonical_event_id") for row in signed_mappings], list(_EVENT_IDS_V1))
    _expect([row.get("canonical_event_id") for row in choice_mappings], list(_EVENT_IDS_V1))
    _expect([row.get("canonical_event_id") for row in packet_events], list(_EVENT_IDS_V1))

    compiled: list[dict[str, object]] = []
    all_flat: list[int] = []
    for ordinal, (event, packet_event) in enumerate(zip(b1_events, packet_events, strict=True)):
        ligand = _dict(event.get("ligand"))
        atoms = [_dict(row) for row in _list(ligand.get("atoms"), length=7)]
        _expect([row.get("atom_id") for row in atoms], list(_B1_ATOM_ORDER_V1))
        mappings: dict[str, dict[str, object]] = {}
        local_values: list[int] = []
        flat_values: list[int] = []
        source_values: list[int] = []
        for local_index, atom in enumerate(atoms):
            atom_id = _text(atom.get("atom_id"))
            role_name = role_by_atom.get(atom_id)
            if role_name is None:
                _fail()
            mapping = _mapping_from_atom(atom, role_name)
            _expect(mapping["type_symbol"], _ATOM_TYPES_V1[atom_id])
            _expect(mapping["B1_role_id"], _ROLE_IDS_V1[role_name])
            for key in (
                "extractor_parser_local_index_0based",
                "model_parser_local_index_0based",
                "model_sample_local_index_0based",
            ):
                _expect(mapping[key], local_index)
            _expect(mapping["model_flat_index_0based"], ordinal * 7 + local_index)
            _expect(mapping["atom_site_id"], str(_integer(mapping["source_atom_site_row_index_0based"]) + 1))
            mappings[atom_id] = mapping
            local_values.append(_integer(mapping["model_sample_local_index_0based"]))
            flat_values.append(_integer(mapping["model_flat_index_0based"]))
            source_values.append(_integer(mapping["source_atom_site_row_index_0based"]))
        if len(set(local_values)) != 7 or len(set(flat_values)) != 7 or len(set(source_values)) != 7:
            _fail()
        all_flat.extend(flat_values)

        _expect(packet_event.get("sample_ordinal_0based"), ordinal)
        _expect(packet_event.get("protein_chain"), _CHAINS_V1[ordinal])
        _expect(packet_event.get("ligand_label_asym_id"), _LIGAND_ASYMS_V1[ordinal])
        packet_seven = _list(packet_event.get("seven_atom_mapping"), length=7)
        _expect(packet_seven, [mappings[atom_id] for atom_id in _B1_ATOM_ORDER_V1])

        candidate_rows = [
            _dict(row) for row in _list(packet_event.get("candidate_event_index_mappings"))
            if _dict(row).get("candidate_id") == _CANDIDATE_ID_V1
        ]
        if len(candidate_rows) != 1:
            _fail()
        packet_candidate = candidate_rows[0]
        seed_maps = [mappings[atom_id] for atom_id in _SEED_ATOM_IDS_V1]
        seed_local = [_integer(row["model_sample_local_index_0based"]) for row in seed_maps]
        scaffold_local = [
            _integer(mappings[atom_id]["model_sample_local_index_0based"])
            for atom_id in _ROLE_ATOMS_V1["scaffold"]
        ]
        linker_local = [
            _integer(mappings[atom_id]["model_sample_local_index_0based"])
            for atom_id in _ROLE_ATOMS_V1["linker"]
        ]
        warhead_local = [
            _integer(mappings[atom_id]["model_sample_local_index_0based"])
            for atom_id in _ROLE_ATOMS_V1["warhead"]
        ]
        scaffold_edges = [
            (
                _integer(mappings[left]["model_sample_local_index_0based"]),
                _integer(mappings[right]["model_sample_local_index_0based"]),
            )
            for left, right in scaffold_edges_by_atom
        ]
        anchor_local = _integer(mappings[_ANCHOR_ATOM_ID_V1]["model_sample_local_index_0based"])
        _validate_minimal_seed_call(
            seed=seed_local,
            scaffold=scaffold_local,
            linker=linker_local,
            warhead=warhead_local,
            scaffold_edges=scaffold_edges,
            anchor=anchor_local,
        )

        seed_indices = {
            "extractor_parser_local_indices_0based": [_integer(row["extractor_parser_local_index_0based"]) for row in seed_maps],
            "model_flat_indices_0based": [_integer(row["model_flat_index_0based"]) for row in seed_maps],
            "model_parser_local_indices_0based": [_integer(row["model_parser_local_index_0based"]) for row in seed_maps],
            "model_sample_local_indices_0based": seed_local,
            "source_atom_site_row_indices_0based": [_integer(row["source_atom_site_row_index_0based"]) for row in seed_maps],
        }
        expected_packet_candidate = {
            "candidate_id": _CANDIDATE_ID_V1,
            "mapping_status": "PASS",
            "primary_anchor_options": [
                {
                    "atom_id": row["atom_id"],
                    "atom_site_id": row["atom_site_id"],
                    "model_flat_index_0based": row["model_flat_index_0based"],
                    "model_sample_local_index_0based": row["model_sample_local_index_0based"],
                    "source_atom_site_row_index_0based": row["source_atom_site_row_index_0based"],
                }
                for row in seed_maps
            ],
            "seed_indices": seed_indices,
        }
        _expect(packet_candidate, expected_packet_candidate)

        validator_call = {
            "linker_model_sample_local_indices_0based": linker_local,
            "primary_anchor_model_sample_local_index_0based": anchor_local,
            "scaffold_edges_model_sample_local_indices_0based": [list(edge) for edge in scaffold_edges],
            "scaffold_model_sample_local_indices_0based": scaffold_local,
            "seed_model_sample_local_indices_0based": seed_local,
            "status": "PASS",
            "validation_reasons": [],
            "warhead_model_sample_local_indices_0based": warhead_local,
        }
        b1_binding = {
            "path": _SOURCE_SPECS_V1[4]["path"],
            "role": _SOURCE_SPECS_V1[4]["role"],
            "sha256": _SOURCE_SPECS_V1[4]["sha256"],
        }
        expected_signed_mapping = {
            "canonical_event_id": _EVENT_IDS_V1[ordinal],
            "event_local_published_validator_call": validator_call,
            "ligand_label_asym_id": _LIGAND_ASYMS_V1[ordinal],
            "packet_mapping_status": "PASS",
            "protein_chain": _CHAINS_V1[ordinal],
            "selected_primary_anchor_mapping": _mapping_without_role(mappings[_ANCHOR_ATOM_ID_V1]),
            "selected_seed_atom_mappings": seed_maps,
            "selected_seed_indices_from_packet": seed_indices,
            "source_binding": b1_binding,
        }
        _expect(signed_mappings[ordinal], expected_signed_mapping)
        _expect(choice_mappings[ordinal], expected_signed_mapping)

        compiled.append({
            "canonical_event_id": _EVENT_IDS_V1[ordinal],
            "sample_ordinal_0based": ordinal,
            "protein_chain": _CHAINS_V1[ordinal],
            "ligand_label_asym_id": _LIGAND_ASYMS_V1[ordinal],
            "minimal_seed_atom_ids": list(_SEED_ATOM_IDS_V1),
            "primary_anchor_atom_id": _ANCHOR_ATOM_ID_V1,
            "seed_atom_mappings": copy.deepcopy(seed_maps),
            "primary_anchor_mapping": _mapping_without_role(mappings[_ANCHOR_ATOM_ID_V1]),
            "pure_minimal_seed_validation": {
                "function": "validate_minimal_seed",
                "status": "PASS",
                "validation_reasons": [],
            },
            "ingestion_status": "HUMAN_APPROVED_SEED_ANCHOR_ACCEPTED_FOR_THIS_SAMPLE",
        })
    if all_flat != list(range(56)):
        _fail()
    return compiled


def _compile_documents(documents: object) -> dict[str, object]:
    docs = copy.deepcopy(_dict(documents))
    expected_keys = {"signed", "choice", "packet", "template", "role_decision", "topology", "b1"}
    if set(docs) != expected_keys:
        _fail()
    signed = _dict(docs["signed"])
    choice = _dict(docs["choice"])
    packet = _dict(docs["packet"])
    template = _dict(docs["template"])
    role = _dict(docs["role_decision"])
    topology = _dict(docs["topology"])
    b1 = _dict(docs["b1"])

    selection, approval = _validate_signed_decision(signed)
    _validate_choice_and_packet(choice, packet, selection)
    _expect(template.get("schema_version"), "covapie_poa_4i3u_exact8_task_c_seed_anchor_decision_template_v1")
    _expect(template.get("record_role"), "UNSIGNED_HUMAN_DECISION_TEMPLATE_NOT_AUTHORITY")
    _expect(template.get("decision_status"), "UNSIGNED")
    _expect(template.get("human_approval_recorded"), False)
    role_by_atom, scaffold_edges = _validate_role_and_topology(role, topology)
    b1_events = _validate_b1_boundaries(b1)
    event_records = _compile_event_records(
        signed=signed,
        choice=choice,
        packet=packet,
        b1_events=b1_events,
        role_by_atom=role_by_atom,
        scaffold_edges_by_atom=scaffold_edges,
    )

    permission_boundary = {
        "PUBLISHED_INGESTION_OWNER_AVAILABLE": False,
        "RUNTIME_SEED_AUTHORITY_ACTIVATED": False,
        "NEW_HUMAN_DECISION_CREATED": False,
        "NEW_FORMAL_ADMISSION_CREATED": False,
        "TRAINING_CONSUMER_ADAPTER_CREATED": False,
        "NAN_GEOMETRY_CONSUMER_CONVERSION_APPLIED": False,
        "CURRENT_TRAIN12_POPULATION_CHANGED": False,
        "B1_PREVIEW_REEXECUTED": False,
        "REAL_MODEL_EXECUTED": False,
        "PARAMETER_UPDATE_PERFORMED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
        "role_authority_regranted": False,
        "reactive_pair_authority_regranted": False,
        "geometry_authority_granted": False,
        "reaction_family_authority_granted": False,
        "warhead_rule_authority_granted": False,
        "task_C_generated_or_fixed_mask_changed": False,
    }
    projection = {
        "schema_version": AUTHORITY_INGESTION_SCHEMA_V1,
        "record_role": RESULT_RECORD_ROLE_V1,
        "signed_decision_identity": {
            "path": SIGNED_DECISION_RELATIVE_PATH_V1.as_posix(),
            "path_namespace": "covapie_state_root_relative",
            "bytes": _SIGNED_DECISION_BYTES_V1,
            "mode": "0664",
            "sha256": SIGNED_DECISION_SHA256_V1,
            "schema_version": FORMAL_DECISION_SCHEMA_V1,
        },
        "human_approval": approval,
        "approved_selection": selection,
        "event_count": 8,
        "event_records": event_records,
        "index_namespace_contract": {
            "extractor_parser_local_index_0based": "WITHIN_EACH_SEVEN_HEAVY_ATOM_LIGAND_EVENT",
            "model_parser_local_index_0based": "WITHIN_EACH_SEVEN_HEAVY_ATOM_LIGAND_EVENT",
            "model_sample_local_index_0based": "WITHIN_EACH_SEVEN_HEAVY_ATOM_LIGAND_EVENT",
            "model_flat_index_0based": "FROZEN_PUBLISHED_B1_EXACT8_LIGAND_BATCH_ONLY_NOT_FUTURE_GLOBAL_INDEX",
            "source_atom_site_row_index_0based": "BOUND_4I3U_SOURCE_ATOM_SITE_ROW",
            "future_batches_must_remap_from_atom_ids_and_sample_local_indices": True,
        },
        "fixed_supporting_source_identities": _source_identity_projection(),
        "canonical_mask_contract": {
            "semantic_long_names": list(_CANONICAL_MASKS_V1),
            "task_count": 5,
            "scaffold_only_B3_present": True,
            "sixth_or_seventh_mask_created": False,
        },
        "permission_boundary": permission_boundary,
    }
    digest = _sha256(_canonical_json_bytes(projection))
    return {
        "schema_version": AUTHORITY_INGESTION_SCHEMA_V1,
        "record_role": RESULT_RECORD_ROLE_V1,
        "acceptance_status": {
            "SIGNED_DECISION_SCHEMA_ACCEPTED": True,
            "SIGNED_DECISION_SOURCE_BINDINGS_VERIFIED": True,
            "EXACT8_SEED_ANCHOR_AUTHORITY_COMPILED": True,
            "EXACT8_SOURCE_LOCAL_FLAT_MAPPING_PASS": True,
            "SEMANTIC_DIGEST_AND_SOURCE_REVALIDATION_PASS": True,
            "AUTHORITY_INGESTION_IMPLEMENTATION_VALIDATED": True,
        },
        "semantic_projection": projection,
        "semantic_projection_sha256": digest,
    }


def _compile_source_bytes(bundle: object) -> dict[str, object]:
    source_bytes = _dict(bundle)
    expected = {"signed", *(str(spec["key"]) for spec in _SOURCE_SPECS_V1)}
    if set(source_bytes) != expected:
        _fail()
    documents = {
        "signed": _strict_json(source_bytes["signed"]),
        "choice": _strict_json(source_bytes["choice"]),
        "packet": _strict_json(source_bytes["packet"]),
        "template": _strict_json(source_bytes["template"]),
        "role_decision": _strict_json(source_bytes["role_decision"]),
        "topology": _strict_json(source_bytes["topology"]),
        "b1": _strict_json(source_bytes["b1"]),
    }
    for key in ("guide", "b1_implementation", "validator"):
        if type(source_bytes[key]) is not bytes or not source_bytes[key]:
            _fail()
    return _compile_documents(documents)


def _load_and_compile_impl(
    *, repository_root: object, state_root: object
) -> dict[str, object]:
    bundle = _load_bound_source_bytes(
        repository_root=repository_root,
        state_root=state_root,
    )
    return _compile_source_bytes(bundle)


def load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
    *, repository_root: Path, state_root: Path
) -> dict[str, object]:
    """Load only the fixed signed record and compile the bound Exact8 result."""

    try:
        return _load_and_compile_impl(
            repository_root=repository_root,
            state_root=state_root,
        )
    except Exception as error:
        raise ValueError(INGESTION_ERROR) from error


def validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
    *, result: object, repository_root: Path, state_root: Path
) -> None:
    """Recompile from fixed sources and require the supplied result to match."""

    try:
        candidate = copy.deepcopy(_dict(result))
        projection = _dict(candidate.get("semantic_projection"))
        _expect(
            candidate.get("semantic_projection_sha256"),
            _sha256(_canonical_json_bytes(projection)),
        )
        expected = _load_and_compile_impl(
            repository_root=repository_root,
            state_root=state_root,
        )
        _expect(candidate, expected)
    except Exception as error:
        raise ValueError(INGESTION_ERROR) from error


def serialize_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
    result: object,
) -> bytes:
    """Return canonical deterministic UTF-8 JSON with one trailing newline."""

    try:
        candidate = copy.deepcopy(_dict(result))
        projection = _dict(candidate.get("semantic_projection"))
        _expect(candidate.get("schema_version"), AUTHORITY_INGESTION_SCHEMA_V1)
        _expect(candidate.get("record_role"), RESULT_RECORD_ROLE_V1)
        _expect(
            candidate.get("semantic_projection_sha256"),
            _sha256(_canonical_json_bytes(projection)),
        )
        return _canonical_json_bytes(candidate, newline=True)
    except Exception as error:
        raise ValueError(INGESTION_ERROR) from error
