"""SHA-bound structural inputs for the 13 positive batch-001 events.

The owner is deliberately read-only.  It projects the published human role
decisions onto retained-heavy mmCIF rows from the existing bulk cache and
reuses the bulk executor's exact ``struct_conn``/altloc and 6 Angstrom pocket
selection primitives.  It performs no acquisition, model execution, or state
write.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import stat
from typing import Any, Mapping, NoReturn, Sequence

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk_owner
from covalent_ext import covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime
from covalent_ext import covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 as feature_owner


__all__ = (
    "BATCH001_POSITIVE_STRUCTURAL_INPUT_ERROR_V1",
    "BATCH001_POSITIVE_EVENT_IDS_V1",
    "BATCH001_STRUCTURE_SHA256_BY_PDB_V1",
    "BATCH001_CCD_SHA256_BY_COMPONENT_V1",
    "BATCH001_PUBLISHED_SOURCE_BINDINGS_V1",
    "BATCH001_EXISTING_OWNER_BINDINGS_V1",
    "CovapieBatch001RetainedHeavyAtomV1",
    "CovapieBatch001StructConnEvidenceV1",
    "CovapieBatch001PositiveStructuralRecordV1",
    "build_covapie_batch001_positive_structural_records_v1",
    "validate_covapie_batch001_positive_structural_record_v1",
    "structural_record_as_evidence_dict_v1",
    "verified_covapie_batch001_source_bindings_v1",
)


BATCH001_POSITIVE_STRUCTURAL_INPUT_ERROR_V1 = (
    "COVAPIE_BATCH001_POSITIVE_STRUCTURAL_INPUT_V1_ERROR"
)
STRICT_LINKER_PRESENT_V1 = direct_runtime.STRICT_LINKER_PRESENT_V1
DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 = (
    direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
)
STRICT_TASK_IDS_V1 = (0, 1, 2, 3, 4)
DIRECT_TASK_IDS_V1 = (0, 3, 4)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CACHE_ROOT = (
    _DEFAULT_REPOSITORY_ROOT.parent
    / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)
_BATCH_SOURCE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1"
)
_SNAPSHOT_PATH = _BATCH_SOURCE_ROOT / (
    "covapie_batch001_completed_human_decision_snapshot_v1.json"
)
_MATRIX_PATH = _BATCH_SOURCE_ROOT / (
    "covapie_batch001_event_task_label_availability_v1.csv"
)
_MANIFEST_PATH = _BATCH_SOURCE_ROOT / (
    "covapie_batch001_task_label_availability_manifest_v1.json"
)
_SUMMARY_PATH = _BATCH_SOURCE_ROOT / (
    "covapie_batch001_task_label_availability_summary_v1.json"
)
_ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "incremental_processing_outcomes_v1.json"
)

BATCH001_PUBLISHED_SOURCE_BINDINGS_V1 = {
    _SNAPSHOT_PATH.as_posix(): (
        "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200"
    ),
    _MATRIX_PATH.as_posix(): (
        "f8481147babbad02215c3c3f767fe22ba6a511b8a076482a9635fec5d5cf8e82"
    ),
    _MANIFEST_PATH.as_posix(): (
        "435b9a03616f9c821c339a96cb21b8ac6d0964619fb1b6b260cdde1c2292ef2a"
    ),
    _SUMMARY_PATH.as_posix(): (
        "ffd086891fea7571faa25bec06806e21cbb944aaa1c95981fcfe370a54387c63"
    ),
}
BATCH001_CACHE_MANIFEST_SHA256_V1 = (
    "10057a8fd7e34c5e63a912a44f242926247aef15cffefa942dceb910d3f1cd58"
)
BATCH001_ATTEMPT001_INCREMENTAL_SHA256_V1 = (
    "d891a267dc4493cfceda33b70ab4a200d9f806e1bff38c4b6f39b69a1a3548d7"
)
BATCH001_STRUCTURE_SHA256_BY_PDB_V1 = {
    "2ZK1": "fba751c18098dad5cbae2fefba243143cd32771841865285437d328e94960da2",
    "2ZK2": "06e3a765c028122a61dfa30244b3e5fd3f5cb9c455a294550228f7a0521b1f15",
    "3B9H": "f907ac342928ec24708516f793f8306401521e6fa5a6b2d893160e65a734c31f",
    "3BHL": "9fd80c44497a6737d83c6f12150cb608e933d1823ca9c58a1e8013c1ceca5b7a",
    "3BHR": "b084d30d981db2fe4a630d1d4832d30a84f1b3752f994ffafa29703b9efb4c89",
    "3I4A": "bfc2a97413c135447cb2294dee561048b4aa5441b422c1583d309643c2c6ae71",
    "3LOK": "d28b889493477bc824ed6eeaf05958a85bad492c509b9fe79e07d7bebb763f52",
    "3O6T": "764bebdae7492f5645a6cf117a55c087cd885e863de30344ae81b9a52175a4e7",
}
BATCH001_CCD_SHA256_BY_COMPONENT_V1 = {
    "DJK": "b46763d6287b3f02e720e166ac9ba06c3ebb5ad0573274b9138356603aa71bfe",
    "LN5": "f37a8aa4ec3128a7668126bfad1e087637d385674ee2cc4698b1631dac9695bf",
    "NDU": "2f691a07ffddc265de12a6ff2d689b9592a6637cfc6672436be6db601d5c2ddd",
    "PTG": "cb1d577730f62137976eb2dfb9c55294130ed018fad8b9e881a6a92b4199a948",
    "PX5": "eb4d1362b2bb2b58d28ffec0168cd66bceb81555beb8fb459bf8c287ad62ee94",
}
BATCH001_EXISTING_OWNER_BINDINGS_V1 = {
    "src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py": (
        "ef17777a634284a94662ac3277c02a7fb4efa20375d84fcf88ac074c61e69ce0"
    ),
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": (
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241"
    ),
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py": (
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535"
    ),
    "src/covalent_ext/covapie_current11_training_tensorizer_v1.py": (
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606"
    ),
    "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py": (
        "c95bac177ba2ef1dd519bb5659cb97a8367484b1e41553be56fe3b2789ceb932"
    ),
    "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py": (
        "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac"
    ),
    "src/covalent_ext/covapie_exact16_post_geometry_partial_supervision_authority_v1.py": (
        "6f388b42bd58ffed67ed752a9fec9f85e57050fc96a89e6f3d3e90b1281dba44"
    ),
    "src/covalent_ext/covapie_current11_target_residue_atom_condition_authority_v1.py": (
        "1cf8839382bccfb595a841493a0e22c550578c02f2592dc7481ff67b078d7248"
    ),
}

BATCH001_POSITIVE_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:3I4A:A:CYS:274-:SG:C:LN5:CZ",
    "COVAPIE_CYS_SG_EVENT_V1:3I4A:B:CYS:274-:SG:D:LN5:CZ",
    "COVAPIE_CYS_SG_EVENT_V1:3O6T:A:CYS:37-:SG:E:PX5:C15",
    "COVAPIE_CYS_SG_EVENT_V1:3O6T:C:CYS:37-:SG:G:PX5:C15",
    "COVAPIE_CYS_SG_EVENT_V1:3B9H:A:CYS:146-:SG:D:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHL:A:CYS:146-:SG:C:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHL:B:CYS:146-:SG:G:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHR:A:CYS:146-:SG:E:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
)

_EVENT = re.compile(
    r"^COVAPIE_CYS_SG_EVENT_V1:([A-Z0-9]+):([^:]+):CYS:"
    r"([0-9]+)([^:]*):SG:([^:]+):([A-Z0-9]+):([^:]+)$"
)
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001RetainedHeavyAtomV1:
    source_atom_site_row_index_0based: int
    atom_site_id: str
    group_PDB: str
    label_asym_id: str
    auth_asym_id: str
    label_comp_id: str
    auth_comp_id: str
    label_seq_id: str
    auth_seq_id: str
    label_atom_id: str
    auth_atom_id: str
    insertion_code: str
    label_alt_id: str
    model_num: str
    occupancy: float
    type_symbol: str
    checkpoint_channel_index: int
    coordinates_angstrom: tuple[float, float, float]


@dataclass(frozen=True)
class CovapieBatch001StructConnEvidenceV1:
    connection_id: str
    evidence_kind: str
    protein_endpoint_comp_id: str
    protein_endpoint_atom_id: str
    ligand_endpoint_comp_id: str
    ligand_endpoint_atom_id: str
    selected_protein_altloc: str
    selected_ligand_altloc: str
    reported_distance_angstrom: float


@dataclass(frozen=True)
class CovapieBatch001PositiveStructuralRecordV1:
    sample_identity: str
    canonical_event_id: str
    review_unit_id: str
    pdb_id: str
    ligand_component_id: str
    protein_chain: str
    protein_residue_name: str
    protein_residue_number: str
    protein_insertion_code: str
    protein_reactive_atom_id: str
    ligand_instance: str
    ligand_reactive_atom_id: str
    structure_relative_path: str
    structure_sha256: str
    ccd_relative_path: str
    ccd_sha256: str
    struct_conn_evidence: CovapieBatch001StructConnEvidenceV1
    ligand_retained_heavy_atoms: tuple[CovapieBatch001RetainedHeavyAtomV1, ...]
    pocket_retained_heavy_atoms: tuple[CovapieBatch001RetainedHeavyAtomV1, ...]
    ligand_source_row_to_retained_index: tuple[tuple[int, int], ...]
    pocket_source_row_to_retained_index: tuple[tuple[int, int], ...]
    ligand_atom_id_to_retained_local_index: tuple[tuple[str, int], ...]
    target_cys_atom_id_to_pocket_local_index: tuple[tuple[str, int], ...]
    target_cys_pocket_local_indices: tuple[int, ...]
    target_sg_pocket_local_index: int
    ligand_reactive_retained_local_index: int
    scaffold_atom_ids: tuple[str, ...]
    linker_atom_ids: tuple[str, ...]
    warhead_atom_ids: tuple[str, ...]
    scaffold_retained_local_indices: tuple[int, ...]
    linker_retained_local_indices: tuple[int, ...]
    warhead_retained_local_indices: tuple[int, ...]
    role_profile: str
    applicable_canonical_task_ids: tuple[int, ...]
    not_applicable_canonical_task_ids: tuple[int, ...]
    historical_snapshot_mask_compatibility: bool
    direct_scaffold_warhead_boundary: tuple[str, str, str] | None
    protein_endpoint_coordinates_angstrom: tuple[float, float, float]
    ligand_endpoint_coordinates_angstrom: tuple[float, float, float]
    post_reactive_pair_distance_angstrom: float
    ligand_element_domain: tuple[str, ...]
    pocket_element_domain: tuple[str, ...]
    feature_projection_status: str
    minimal_seed_authority_available: bool
    split_prediction_status: str
    predicted_split_if_any: str
    predicted_leakage_group_id: str
    split_admission_authoritative: bool
    sample_training_admitted: bool


class _StructuralInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _StructuralInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _StructuralInvariantError):
        raise ValueError(
            f"{BATCH001_POSITIVE_STRUCTURAL_INPUT_ERROR_V1}:{error.reason}"
        ) from error
    if type(error) is ValueError and str(error).startswith(
        BATCH001_POSITIVE_STRUCTURAL_INPUT_ERROR_V1
    ):
        raise error
    raise ValueError(BATCH001_POSITIVE_STRUCTURAL_INPUT_ERROR_V1) from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _require_root(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _StructuralInvariantError(reason) from error
    if resolved != path or stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail(reason)
    return path


def _safe_file(root: Path, relative: str) -> Path:
    pure = Path(relative)
    if (
        type(relative) is not str
        or not relative
        or "\\" in relative
        or pure.is_absolute()
        or ".." in pure.parts
    ):
        _fail("SOURCE_RELATIVE_PATH_INVALID")
    current = root
    try:
        for part in pure.parts:
            current = current / part
            if stat.S_ISLNK(current.lstat().st_mode):
                _fail("SOURCE_SYMLINK_FORBIDDEN")
        if not current.resolve(strict=True).is_relative_to(root):
            _fail("SOURCE_PATH_ESCAPE")
        if not stat.S_ISREG(current.lstat().st_mode):
            _fail("SOURCE_FILE_INVALID")
    except _StructuralInvariantError:
        raise
    except (OSError, RuntimeError) as error:
        raise _StructuralInvariantError("SOURCE_FILE_UNAVAILABLE") from error
    return current


def _read_sha(root: Path, relative: str, expected: str) -> bytes:
    path = _safe_file(root, relative)
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise _StructuralInvariantError("SOURCE_FILE_UNAVAILABLE") from error
    if _sha256(payload) != expected:
        _fail("SOURCE_SHA256_MISMATCH")
    return payload


def _parse_json(payload: bytes, reason: str) -> dict[str, Any]:
    try:
        result = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _StructuralInvariantError(reason) from error
    if type(result) is not dict:
        _fail(reason)
    return result


def _event_identity(event_id: str) -> dict[str, str]:
    match = _EVENT.fullmatch(event_id)
    if match is None:
        _fail("CANONICAL_EVENT_ID_INVALID")
    pdb_id, protein_chain, residue_number, insertion, ligand_instance, component, reactive = match.groups()
    if insertion != "-":
        _fail("CANONICAL_EVENT_INSERTION_CODE_UNSUPPORTED")
    return {
        "pdb_id": pdb_id,
        "protein_instance": protein_chain,
        "protein_residue_number": residue_number,
        "protein_insertion_code": "",
        "ligand_instance": ligand_instance,
        "ligand_component_id": component,
        "ligand_reactive_atom": reactive,
    }


def _verified_inputs(
    repository_root: Path, cache_root: Path
) -> dict[str, Any]:
    published: dict[str, bytes] = {}
    for relative, sha in BATCH001_PUBLISHED_SOURCE_BINDINGS_V1.items():
        published[relative] = _read_sha(repository_root, relative, sha)
    for relative, sha in BATCH001_EXISTING_OWNER_BINDINGS_V1.items():
        _read_sha(repository_root, relative, sha)

    manifest_payload = _read_sha(
        cache_root.parent,
        "cache_manifest_v1.json",
        BATCH001_CACHE_MANIFEST_SHA256_V1,
    )
    manifest = _parse_json(manifest_payload, "CACHE_MANIFEST_INVALID")
    payload_rows = manifest.get("payloads")
    if (
        manifest.get("schema_version") != "covapie_bulk_cache_manifest_v1"
        or type(payload_rows) is not list
    ):
        _fail("CACHE_MANIFEST_INVALID")
    by_relative: dict[str, dict[str, Any]] = {}
    for raw in payload_rows:
        if type(raw) is not dict or type(raw.get("relative_path")) is not str:
            _fail("CACHE_MANIFEST_INVALID")
        relative = raw["relative_path"]
        if relative in by_relative:
            _fail("CACHE_MANIFEST_DUPLICATE_PATH")
        by_relative[relative] = raw

    structure_payloads: dict[str, bytes] = {}
    for pdb_id, expected_sha in BATCH001_STRUCTURE_SHA256_BY_PDB_V1.items():
        manifest_relative = f"rcsb/structures/{pdb_id}.cif.gz"
        row = by_relative.get(manifest_relative)
        if (
            row is None
            or row.get("sha256") != expected_sha
            or row.get("validation_status")
            != "SHA256_SIZE_AND_SCIENTIFIC_VALIDATION_PASSED"
        ):
            _fail("STRUCTURE_CACHE_MANIFEST_BINDING_INVALID")
        payload = _read_sha(cache_root, f"structures/{pdb_id}.cif.gz", expected_sha)
        if row.get("byte_count") != len(payload):
            _fail("STRUCTURE_CACHE_SIZE_INVALID")
        structure_payloads[pdb_id] = payload

    ccd_payloads: dict[str, bytes] = {}
    for component, expected_sha in BATCH001_CCD_SHA256_BY_COMPONENT_V1.items():
        manifest_relative = f"rcsb/ccd/{component}.cif"
        row = by_relative.get(manifest_relative)
        if (
            row is None
            or row.get("sha256") != expected_sha
            or row.get("validation_status")
            != "SHA256_SIZE_AND_SCIENTIFIC_VALIDATION_PASSED"
        ):
            _fail("CCD_CACHE_MANIFEST_BINDING_INVALID")
        payload = _read_sha(cache_root, f"ccd/{component}.cif", expected_sha)
        if row.get("byte_count") != len(payload):
            _fail("CCD_CACHE_SIZE_INVALID")
        ccd_payloads[component] = payload

    attempt_payload = _read_sha(
        repository_root.parent,
        _ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        BATCH001_ATTEMPT001_INCREMENTAL_SHA256_V1,
    )
    return {
        "published": published,
        "cache_manifest": manifest,
        "structures": structure_payloads,
        "ccds": ccd_payloads,
        "attempt": _parse_json(attempt_payload, "ATTEMPT001_EVIDENCE_INVALID"),
    }


def verified_covapie_batch001_source_bindings_v1(
    *, repository_root: object = None, cache_root: object = None
) -> tuple[dict[str, str], ...]:
    """Verify every immutable input and return path/SHA binding rows."""

    try:
        repo = _require_root(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        cache = _require_root(
            cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID"
        )
        _verified_inputs(repo, cache)
        rows: list[dict[str, str]] = []
        for relative, sha in sorted(BATCH001_PUBLISHED_SOURCE_BINDINGS_V1.items()):
            rows.append({
                "source_category": "BATCH001_PUBLISHED_ARTIFACT",
                "source_root_kind": "REPOSITORY_ROOT",
                "relative_path": relative,
                "sha256": sha,
                "consumed_for": "positive_population_and_human_label_authority",
                "sha256_verified": "true",
            })
        for relative, sha in sorted(BATCH001_EXISTING_OWNER_BINDINGS_V1.items()):
            category = "EXISTING_SEMANTIC_OWNER"
            rows.append({
                "source_category": category,
                "source_root_kind": "REPOSITORY_ROOT",
                "relative_path": relative,
                "sha256": sha,
                "consumed_for": "reused_model_input_and_supervision_contract",
                "sha256_verified": "true",
            })
        rows.append({
            "source_category": "CANONICAL_CACHE_MANIFEST",
            "source_root_kind": "CACHE_PARENT_ROOT",
            "relative_path": "cache_manifest_v1.json",
            "sha256": BATCH001_CACHE_MANIFEST_SHA256_V1,
            "consumed_for": "external_payload_integrity_authority",
            "sha256_verified": "true",
        })
        for pdb_id, sha in sorted(BATCH001_STRUCTURE_SHA256_BY_PDB_V1.items()):
            rows.append({
                "source_category": "RCSB_MMCIF_PAYLOAD",
                "source_root_kind": "STRUCTURAL_SOURCE_ROOT",
                "relative_path": f"structures/{pdb_id}.cif.gz",
                "sha256": sha,
                "consumed_for": "event_specific_full_atom_and_6A_pocket_projection",
                "sha256_verified": "true",
            })
        for component, sha in sorted(BATCH001_CCD_SHA256_BY_COMPONENT_V1.items()):
            rows.append({
                "source_category": "WWPDB_CCD_PAYLOAD",
                "source_root_kind": "STRUCTURAL_SOURCE_ROOT",
                "relative_path": f"ccd/{component}.cif",
                "sha256": sha,
                "consumed_for": "explicit_component_graph_and_direct_boundary",
                "sha256_verified": "true",
            })
        rows.append({
            "source_category": "READ_ONLY_SPLIT_LEAKAGE_EVIDENCE",
            "source_root_kind": "REPOSITORY_PARENT_ROOT",
            "relative_path": _ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
            "sha256": BATCH001_ATTEMPT001_INCREMENTAL_SHA256_V1,
            "consumed_for": "post_distance_reconciliation_and_non_authoritative_split_prediction",
            "sha256_verified": "true",
        })
        return tuple(rows)
    except Exception as error:
        _public_error(error)


def _snapshot_and_matrix_sources(
    inputs: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, str]]]:
    published = inputs["published"]
    snapshot = _parse_json(
        published[_SNAPSHOT_PATH.as_posix()], "BATCH001_SNAPSHOT_INVALID"
    )
    if (
        snapshot.get("schema_version")
        != "covapie_batch001_completed_human_decision_snapshot_v1"
        or snapshot.get("counts", {}).get("completed_positive_event_count") != 13
        or snapshot.get("counts", {}).get("completed_negative_event_count") != 24
        or snapshot.get("held_out_in_progress", {}).get("ONL_ingested") is not False
    ):
        _fail("BATCH001_SNAPSHOT_INVALID")
    by_event: dict[str, dict[str, Any]] = {}
    decisions = snapshot.get("completed_human_decisions")
    if type(decisions) is not list:
        _fail("BATCH001_SNAPSHOT_INVALID")
    for unit in decisions:
        if type(unit) is not dict or unit.get("completed_lane") != "COMPLETED_POSITIVE_CHEMISTRY":
            continue
        human = unit.get("human_decision")
        if type(human) is not dict or type(human.get("events")) is not list:
            _fail("BATCH001_POSITIVE_DECISION_INVALID")
        for event in human["events"]:
            if type(event) is not dict or type(event.get("canonical_event_id")) is not str:
                _fail("BATCH001_POSITIVE_DECISION_INVALID")
            event_id = event["canonical_event_id"]
            if event_id in by_event:
                _fail("BATCH001_POSITIVE_EVENT_DUPLICATE")
            by_event[event_id] = {
                "review_unit_id": unit.get("review_unit_id"),
                "human_decision": human,
                "event_decision": event,
            }
    if tuple(by_event) != BATCH001_POSITIVE_EVENT_IDS_V1:
        _fail("BATCH001_EXACT13_POPULATION_INVALID")

    try:
        matrix_rows = list(csv.DictReader(io.StringIO(
            published[_MATRIX_PATH.as_posix()].decode("utf-8")
        )))
    except (UnicodeDecodeError, csv.Error) as error:
        raise _StructuralInvariantError("BATCH001_MATRIX_INVALID") from error
    positive_rows = {
        row.get("canonical_event_id"): row
        for row in matrix_rows
        if row.get("completed_lane") == "COMPLETED_POSITIVE_CHEMISTRY"
    }
    if (
        len(matrix_rows) != 37
        or len(positive_rows) != 13
        or tuple(event for event in BATCH001_POSITIVE_EVENT_IDS_V1 if event in positive_rows)
        != BATCH001_POSITIVE_EVENT_IDS_V1
    ):
        _fail("BATCH001_MATRIX_POPULATION_INVALID")
    return by_event, positive_rows  # type: ignore[return-value]


def _attempt_sources(inputs: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    attempt = inputs["attempt"]
    events = attempt.get("events")
    if (
        attempt.get("schema_version")
        != "covapie_bulk_500_event_executor_v1"
        or type(events) is not list
    ):
        _fail("ATTEMPT001_EVIDENCE_INVALID")
    by_event = {
        row.get("canonical_event_id"): row
        for row in events
        if type(row) is dict and row.get("canonical_event_id") in BATCH001_POSITIVE_EVENT_IDS_V1
    }
    if set(by_event) != set(BATCH001_POSITIVE_EVENT_IDS_V1):
        _fail("ATTEMPT001_EXACT13_EVIDENCE_MISSING")
    return by_event  # type: ignore[return-value]


def _atom_record(
    row: Mapping[str, str], *, source_index: int, channel: int
) -> CovapieBatch001RetainedHeavyAtomV1:
    try:
        coordinates = bulk_owner._coordinates(row)
        occupancy = bulk_owner._occupancy(row)
    except (TypeError, ValueError) as error:
        raise _StructuralInvariantError("RETAINED_ATOM_COORDINATES_INVALID") from error
    value = bulk_owner._atom_value
    return CovapieBatch001RetainedHeavyAtomV1(
        source_atom_site_row_index_0based=source_index,
        atom_site_id=value(row, "id"),
        group_PDB=value(row, "group_PDB"),
        label_asym_id=value(row, "label_asym_id"),
        auth_asym_id=value(row, "auth_asym_id"),
        label_comp_id=value(row, "label_comp_id").upper(),
        auth_comp_id=value(row, "auth_comp_id").upper(),
        label_seq_id=value(row, "label_seq_id"),
        auth_seq_id=value(row, "auth_seq_id"),
        label_atom_id=value(row, "label_atom_id").upper(),
        auth_atom_id=value(row, "auth_atom_id").upper(),
        insertion_code=value(row, "pdbx_PDB_ins_code"),
        label_alt_id=value(row, "label_alt_id"),
        model_num=value(row, "pdbx_PDB_model_num") or "1",
        occupancy=occupancy,
        type_symbol=value(row, "type_symbol").title(),
        checkpoint_channel_index=channel,
        coordinates_angstrom=coordinates,
    )


def _project_rows(
    rows: Sequence[Mapping[str, str]], source_index_by_object: Mapping[int, int]
) -> tuple[CovapieBatch001RetainedHeavyAtomV1, ...]:
    heavy_rows = tuple(
        row
        for row in rows
        if bulk_owner._atom_value(row, "type_symbol").upper() != "H"
    )
    symbols = tuple(
        bulk_owner._atom_value(row, "type_symbol").title() for row in heavy_rows
    )
    projection = feature_owner.project_type_symbols_to_checkpoint_heavy_v1(symbols)
    if (
        projection.sample_rejected
        or projection.outcome != "passed"
        or not all(projection.keep_mask)
        or any(type(channel) is not int for channel in projection.checkpoint_channel_indices)
    ):
        _fail("UNSUPPORTED_NON_H_FEATURE_PROJECTION")
    return tuple(
        _atom_record(
            row,
            source_index=source_index_by_object[id(row)],
            channel=channel,
        )
        for row, channel in zip(heavy_rows, projection.checkpoint_channel_indices)
        if type(channel) is int
    )


def _inventory_sha(
    rows: Sequence[CovapieBatch001RetainedHeavyAtomV1], *, pocket: bool
) -> str:
    values = []
    for row in rows:
        item = {
            "atom": row.label_atom_id,
            "element": row.type_symbol,
            "coordinates": list(row.coordinates_angstrom),
        }
        if pocket:
            item = {
                "asym": row.label_asym_id,
                "seq": row.label_seq_id,
                **item,
            }
        values.append(item)
    return _sha256(_canonical_json_bytes(values))


def _explicit_heavy_bonds(
    ccd: Mapping[str, Any], retained_atom_ids: set[str]
) -> tuple[direct_runtime.ExplicitBondV1, ...]:
    bonds = ccd.get("ccd_bond_inventory")
    if type(bonds) is not list:
        _fail("CCD_BOND_INVENTORY_INVALID")
    result = []
    for raw in bonds:
        if type(raw) is not dict:
            _fail("CCD_BOND_INVENTORY_INVALID")
        left, right, order = (
            raw.get("atom_id_1"), raw.get("atom_id_2"), raw.get("value_order")
        )
        if left in retained_atom_ids and right in retained_atom_ids:
            if type(left) is not str or type(right) is not str or type(order) is not str:
                _fail("CCD_BOND_INVENTORY_INVALID")
            result.append(direct_runtime.ExplicitBondV1(left, right, order))
    if not result:
        _fail("CCD_RETAINED_HEAVY_GRAPH_EMPTY")
    return tuple(result)


def _build_record(
    *,
    event_id: str,
    decision: Mapping[str, Any],
    matrix: Mapping[str, str],
    attempt: Mapping[str, Any],
    structure_payload: bytes,
    ccd_payload: bytes,
) -> CovapieBatch001PositiveStructuralRecordV1:
    identity = _event_identity(event_id)
    pdb_id = identity["pdb_id"]
    component = identity["ligand_component_id"]
    structural = attempt.get("structural_processing")
    if type(structural) is not dict:
        _fail("ATTEMPT001_STRUCTURAL_EVIDENCE_INVALID")
    try:
        text = bulk_owner._validate_mmcif_payload(structure_payload, pdb_id)
        ccd = bulk_owner.parse_ccd_cif_v1(ccd_payload, ccd_id=component)
        _tags, connections, status, parse_error = (
            bulk_owner.struct_conn_owner.parse_struct_conn_loop(text)
        )
    except Exception as error:
        raise _StructuralInvariantError("STRUCTURAL_PAYLOAD_PARSE_FAILED") from error
    if status == "raw_parse_error":
        _fail("STRUCT_CONN_PARSE_FAILED:" + parse_error)
    event_for_parser = {
        **identity,
        "connection_ids": [structural.get("selected_connection_id")],
    }
    matches = []
    for connection in connections:
        endpoints = bulk_owner._connection_matches_event(connection, event_for_parser)
        if endpoints is not None:
            matches.append((connection, endpoints[0], endpoints[1]))
    selected_connection_id = structural.get("selected_connection_id")
    matches.sort(key=lambda item: (
        0 if bulk_owner._conn_value(item[0], "id") == selected_connection_id else 1,
        bulk_owner._conn_value(item[0], "id"),
        item[1]["altloc"],
        item[2]["altloc"],
    ))
    if not matches or bulk_owner._conn_value(matches[0][0], "id") != selected_connection_id:
        _fail("EXACT_STRUCT_CONN_NOT_RECOVERED")
    selected_connection, protein_endpoint, ligand_endpoint = matches[0]
    atom_rows = bulk_owner.atom_site_owner.extract_atom_site_loop_rows_v0(text)
    source_index = {id(row): index for index, row in enumerate(atom_rows)}
    protein_candidates = bulk_owner._endpoint_candidates(
        atom_rows, endpoint=protein_endpoint, event=event_for_parser, protein=True
    )
    ligand_candidates = bulk_owner._endpoint_candidates(
        atom_rows, endpoint=ligand_endpoint, event=event_for_parser, protein=False
    )
    try:
        selected_protein, selected_ligand = bulk_owner._select_endpoint_pair(
            protein_candidates,
            ligand_candidates,
            reported_distance=float(structural.get("reported_distance_angstrom")),
        )
    except (TypeError, ValueError) as error:
        raise _StructuralInvariantError("EXACT_ENDPOINT_PAIR_SELECTION_FAILED") from error
    ligand_source_rows = bulk_owner._selected_ligand_atoms(
        atom_rows, event_for_parser, selected_ligand
    )
    pocket_source_rows = bulk_owner._selected_pocket_atoms(
        atom_rows, ligand_source_rows
    )
    ligand_rows = _project_rows(ligand_source_rows, source_index)
    pocket_rows = _project_rows(pocket_source_rows, source_index)
    if not ligand_rows or not pocket_rows:
        _fail("MODEL_BOUND_RETAINED_HEAVY_ROWS_EMPTY")

    ligand_index: dict[str, int] = {}
    for index, row in enumerate(ligand_rows):
        if not row.label_atom_id or row.label_atom_id in ligand_index:
            _fail("LIGAND_ATOM_ID_MAPPING_AMBIGUOUS")
        ligand_index[row.label_atom_id] = index
    selected_protein_source_index = source_index[id(selected_protein)]
    target_members = tuple(
        index
        for index, row in enumerate(pocket_rows)
        if row.label_comp_id == "CYS"
        and row.label_asym_id == identity["protein_instance"]
        and (row.auth_seq_id or row.label_seq_id) == identity["protein_residue_number"]
        and row.insertion_code == identity["protein_insertion_code"]
    )
    sg_matches = tuple(
        index
        for index in target_members
        if pocket_rows[index].label_atom_id == "SG"
        and pocket_rows[index].source_atom_site_row_index_0based
        == selected_protein_source_index
    )
    if len(sg_matches) != 1 or not target_members:
        _fail("TARGET_CYS_SG_MAPPING_NOT_EXACTLY_ONE")
    target_sg = sg_matches[0]
    reactive = identity["ligand_reactive_atom"]
    if reactive not in ligand_index:
        _fail("LIGAND_REACTIVE_ATOM_MAPPING_NOT_EXACTLY_ONE")
    reactive_index = ligand_index[reactive]
    if ligand_rows[reactive_index].source_atom_site_row_index_0based != source_index[id(selected_ligand)]:
        _fail("LIGAND_REACTIVE_ENDPOINT_MAPPING_MISMATCH")

    human = decision.get("human_decision")
    if type(human) is not dict or type(human.get("roles")) is not dict:
        _fail("HUMAN_ROLE_DECISION_INVALID")
    roles = human["roles"]
    try:
        scaffold_ids = tuple(roles["scaffold_atom_ids"])
        linker_ids = tuple(roles["linker_atom_ids"])
        warhead_ids = tuple(roles["warhead_atom_ids"])
    except (KeyError, TypeError) as error:
        raise _StructuralInvariantError("HUMAN_ROLE_DECISION_INVALID") from error
    if any(type(atom) is not str for group in (scaffold_ids, linker_ids, warhead_ids) for atom in group):
        _fail("HUMAN_ROLE_DECISION_INVALID")
    try:
        scaffold_indices = tuple(ligand_index[atom] for atom in scaffold_ids)
        linker_indices = tuple(ligand_index[atom] for atom in linker_ids)
        warhead_indices = tuple(ligand_index[atom] for atom in warhead_ids)
    except KeyError as error:
        raise _StructuralInvariantError("HUMAN_ROLE_ATOM_NOT_RETAINED") from error

    role_profile = (
        DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 if component == "PX5"
        else STRICT_LINKER_PRESENT_V1
    )
    applicable = direct_runtime.valid_canonical_task_ids_for_role_profile_v1(role_profile)
    not_applicable = tuple(task for task in range(5) if task not in applicable)
    retained_ids = tuple(row.label_atom_id for row in ligand_rows)
    explicit_bonds = _explicit_heavy_bonds(ccd, set(retained_ids))
    direct_boundary: tuple[str, str, str] | None = None
    boundaries: tuple[tuple[str, str, str], ...] = ()
    if role_profile == DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1:
        boundary_matches = []
        scaffold_set, warhead_set = set(scaffold_ids), set(warhead_ids)
        for bond in explicit_bonds:
            if bond.atom_id_1 in scaffold_set and bond.atom_id_2 in warhead_set:
                boundary_matches.append((bond.atom_id_1, bond.atom_id_2, bond.bond_order))
            elif bond.atom_id_2 in scaffold_set and bond.atom_id_1 in warhead_set:
                boundary_matches.append((bond.atom_id_2, bond.atom_id_1, bond.bond_order))
        if boundary_matches != [("C8", "C10", "SING")]:
            _fail("PX5_DIRECT_BOUNDARY_INVALID")
        direct_boundary = boundary_matches[0]
        boundaries = (direct_boundary,)
    role_validation = direct_runtime.validate_role_profile_v1(
        role_profile=role_profile,
        retained_heavy_atoms=retained_ids,
        scaffold_atoms=scaffold_ids,
        linker_atoms=linker_ids,
        warhead_atoms=warhead_ids,
        reactive_atom_id=reactive,
        direct_scaffold_warhead_boundaries=boundaries,
        explicit_graph_bonds=explicit_bonds,
    )
    if not role_validation.valid:
        _fail("ROLE_PROFILE_INVALID:" + ";".join(role_validation.reasons))

    protein_coordinate = bulk_owner._coordinates(selected_protein)
    ligand_coordinate = bulk_owner._coordinates(selected_ligand)
    post_distance = math.dist(protein_coordinate, ligand_coordinate)
    recorded_distance = structural.get("post_distance_angstrom")
    if (
        not math.isfinite(post_distance)
        or post_distance <= 0
        or type(recorded_distance) not in (int, float)
        or abs(post_distance - float(recorded_distance)) > 0.000001
    ):
        _fail("POST_GEOMETRY_RECONCILIATION_FAILED")
    if (
        _inventory_sha(ligand_rows, pocket=False)
        != structural.get("ligand_atom_inventory_sha256")
        or _inventory_sha(pocket_rows, pocket=True)
        != structural.get("pocket_atom_inventory_sha256")
        or len(ligand_rows) != structural.get("ligand_heavy_atom_count")
        or len(pocket_rows) != structural.get("pocket_heavy_atom_count")
    ):
        _fail("ATTEMPT001_RETAINED_INVENTORY_RECONCILIATION_FAILED")
    ligand_elements = tuple(sorted({row.type_symbol for row in ligand_rows}))
    pocket_elements = tuple(sorted({row.type_symbol for row in pocket_rows}))
    if dict(Counter(row.type_symbol for row in ligand_rows)) != structural.get(
        "ligand_element_counts"
    ):
        _fail("ATTEMPT001_LIGAND_ELEMENT_RECONCILIATION_FAILED")

    historical_compatible = all(
        matrix.get(field) == "true"
        for field in (
            "mask_A_warhead_only_available",
            "mask_B_linker_plus_warhead_available",
            "mask_B2_scaffold_plus_warhead_available",
            "mask_B3_scaffold_only_available",
            "mask_C_scaffold_plus_linker_plus_warhead_available",
        )
    )
    if historical_compatible is (component == "PX5"):
        _fail("HISTORICAL_AND_EFFECTIVE_MASK_STATE_INVALID")
    leakage_class = attempt.get("leakage_classification")
    predicted_split = attempt.get("predicted_split")
    predicted_group = attempt.get("predicted_group_id")
    if component == "NDU":
        prediction_status = "LEAKAGE_EVIDENCE_INCOMPLETE_UNASSIGNED_READ_ONLY"
        if predicted_split != "UNASSIGNED_READ_ONLY" or predicted_group is not None:
            _fail("NDU_SPLIT_PREDICTION_STATE_INVALID")
        predicted_split_text = ""
        predicted_group_text = ""
    else:
        prediction_status = "READ_ONLY_PREDICTION_AVAILABLE"
        if predicted_split not in {"train", "validation"} or type(predicted_group) is not str:
            _fail("READ_ONLY_SPLIT_PREDICTION_INVALID")
        predicted_split_text = predicted_split
        predicted_group_text = predicted_group
    if type(leakage_class) is not str:
        _fail("READ_ONLY_SPLIT_PREDICTION_INVALID")

    return CovapieBatch001PositiveStructuralRecordV1(
        sample_identity=event_id,
        canonical_event_id=event_id,
        review_unit_id=str(decision.get("review_unit_id")),
        pdb_id=pdb_id,
        ligand_component_id=component,
        protein_chain=identity["protein_instance"],
        protein_residue_name="CYS",
        protein_residue_number=identity["protein_residue_number"],
        protein_insertion_code="",
        protein_reactive_atom_id="SG",
        ligand_instance=identity["ligand_instance"],
        ligand_reactive_atom_id=reactive,
        structure_relative_path=f"structures/{pdb_id}.cif.gz",
        structure_sha256=BATCH001_STRUCTURE_SHA256_BY_PDB_V1[pdb_id],
        ccd_relative_path=f"ccd/{component}.cif",
        ccd_sha256=BATCH001_CCD_SHA256_BY_COMPONENT_V1[component],
        struct_conn_evidence=CovapieBatch001StructConnEvidenceV1(
            connection_id=str(selected_connection_id),
            evidence_kind="MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR",
            protein_endpoint_comp_id="CYS",
            protein_endpoint_atom_id="SG",
            ligand_endpoint_comp_id=component,
            ligand_endpoint_atom_id=reactive,
            selected_protein_altloc=bulk_owner._atom_value(selected_protein, "label_alt_id"),
            selected_ligand_altloc=bulk_owner._atom_value(selected_ligand, "label_alt_id"),
            reported_distance_angstrom=float(structural["reported_distance_angstrom"]),
        ),
        ligand_retained_heavy_atoms=ligand_rows,
        pocket_retained_heavy_atoms=pocket_rows,
        ligand_source_row_to_retained_index=tuple(
            (row.source_atom_site_row_index_0based, index)
            for index, row in enumerate(ligand_rows)
        ),
        pocket_source_row_to_retained_index=tuple(
            (row.source_atom_site_row_index_0based, index)
            for index, row in enumerate(pocket_rows)
        ),
        ligand_atom_id_to_retained_local_index=tuple(ligand_index.items()),
        target_cys_atom_id_to_pocket_local_index=tuple(
            (pocket_rows[index].label_atom_id, index) for index in target_members
        ),
        target_cys_pocket_local_indices=target_members,
        target_sg_pocket_local_index=target_sg,
        ligand_reactive_retained_local_index=reactive_index,
        scaffold_atom_ids=scaffold_ids,
        linker_atom_ids=linker_ids,
        warhead_atom_ids=warhead_ids,
        scaffold_retained_local_indices=scaffold_indices,
        linker_retained_local_indices=linker_indices,
        warhead_retained_local_indices=warhead_indices,
        role_profile=role_profile,
        applicable_canonical_task_ids=applicable,
        not_applicable_canonical_task_ids=not_applicable,
        historical_snapshot_mask_compatibility=historical_compatible,
        direct_scaffold_warhead_boundary=direct_boundary,
        protein_endpoint_coordinates_angstrom=protein_coordinate,
        ligand_endpoint_coordinates_angstrom=ligand_coordinate,
        post_reactive_pair_distance_angstrom=round(post_distance, 6),
        ligand_element_domain=ligand_elements,
        pocket_element_domain=pocket_elements,
        feature_projection_status="EXACT10_PASS",
        minimal_seed_authority_available=False,
        split_prediction_status=prediction_status,
        predicted_split_if_any=predicted_split_text,
        predicted_leakage_group_id=predicted_group_text,
        split_admission_authoritative=False,
        sample_training_admitted=False,
    )


def validate_covapie_batch001_positive_structural_record_v1(
    record: object,
) -> bool:
    """Fail closed on any structural, role, feature, or admission drift."""

    try:
        if not isinstance(record, CovapieBatch001PositiveStructuralRecordV1):
            _fail("STRUCTURAL_RECORD_TYPE_INVALID")
        if record.canonical_event_id not in BATCH001_POSITIVE_EVENT_IDS_V1:
            if ":ONL:" in record.canonical_event_id:
                _fail("ONL_EXCLUDED_FROM_BATCH001_POSITIVE_BRIDGE")
            _fail("SAMPLE_IDENTITY_NOT_IN_BATCH001_POSITIVE_POPULATION")
        identity = _event_identity(record.canonical_event_id)
        if (
            record.sample_identity != record.canonical_event_id
            or record.pdb_id != identity["pdb_id"]
            or record.ligand_component_id != identity["ligand_component_id"]
            or record.protein_chain != identity["protein_instance"]
            or record.protein_residue_number != identity["protein_residue_number"]
            or record.protein_residue_name != "CYS"
            or record.protein_reactive_atom_id != "SG"
            or record.ligand_instance != identity["ligand_instance"]
            or record.ligand_reactive_atom_id != identity["ligand_reactive_atom"]
            or record.structure_sha256
            != BATCH001_STRUCTURE_SHA256_BY_PDB_V1.get(record.pdb_id)
            or record.ccd_sha256
            != BATCH001_CCD_SHA256_BY_COMPONENT_V1.get(record.ligand_component_id)
        ):
            _fail("STRUCTURAL_RECORD_IDENTITY_INVALID")
        ligand_rows = record.ligand_retained_heavy_atoms
        pocket_rows = record.pocket_retained_heavy_atoms
        if not ligand_rows or not pocket_rows:
            _fail("STRUCTURAL_RECORD_ATOM_ROWS_EMPTY")
        for rows in (ligand_rows, pocket_rows):
            projection = feature_owner.project_type_symbols_to_checkpoint_heavy_v1(
                tuple(row.type_symbol for row in rows)
            )
            if (
                projection.sample_rejected
                or not all(projection.keep_mask)
                or tuple(projection.checkpoint_channel_indices)
                != tuple(row.checkpoint_channel_index for row in rows)
                or any(
                    len(row.coordinates_angstrom) != 3
                    or not all(math.isfinite(value) for value in row.coordinates_angstrom)
                    for row in rows
                )
            ):
                _fail("STRUCTURAL_RECORD_FEATURE_PROJECTION_INVALID")
        ligand_ids = tuple(row.label_atom_id for row in ligand_rows)
        if (
            len(ligand_ids) != len(set(ligand_ids))
            or record.ligand_reactive_retained_local_index not in range(len(ligand_rows))
            or ligand_rows[record.ligand_reactive_retained_local_index].label_atom_id
            != record.ligand_reactive_atom_id
        ):
            _fail("STRUCTURAL_RECORD_LIGAND_REACTIVE_MAPPING_INVALID")
        if (
            record.target_sg_pocket_local_index not in record.target_cys_pocket_local_indices
            or record.target_sg_pocket_local_index not in range(len(pocket_rows))
            or pocket_rows[record.target_sg_pocket_local_index].label_atom_id != "SG"
            or sum(
                pocket_rows[index].label_atom_id == "SG"
                for index in record.target_cys_pocket_local_indices
            ) != 1
        ):
            _fail("STRUCTURAL_RECORD_TARGET_SG_MAPPING_INVALID")
        roles = (
            record.scaffold_retained_local_indices,
            record.linker_retained_local_indices,
            record.warhead_retained_local_indices,
        )
        flattened = tuple(index for group in roles for index in group)
        if (
            len(flattened) != len(set(flattened))
            or set(flattened) != set(range(len(ligand_rows)))
            or not record.scaffold_retained_local_indices
            or not record.warhead_retained_local_indices
        ):
            _fail("STRUCTURAL_RECORD_ROLE_PARTITION_INVALID")
        expected_profile = (
            DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
            if record.ligand_component_id == "PX5"
            else STRICT_LINKER_PRESENT_V1
        )
        if (
            record.role_profile != expected_profile
            or record.applicable_canonical_task_ids
            != direct_runtime.valid_canonical_task_ids_for_role_profile_v1(expected_profile)
            or record.not_applicable_canonical_task_ids
            != tuple(task for task in range(5) if task not in record.applicable_canonical_task_ids)
        ):
            _fail("STRUCTURAL_RECORD_ROLE_PROFILE_INVALID")
        if expected_profile == DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1:
            if (
                record.linker_atom_ids
                or record.linker_retained_local_indices
                or record.direct_scaffold_warhead_boundary != ("C8", "C10", "SING")
                or record.applicable_canonical_task_ids != DIRECT_TASK_IDS_V1
                or record.historical_snapshot_mask_compatibility is not False
            ):
                _fail("PX5_DIRECT_PROFILE_CONTRACT_INVALID")
        elif (
            not record.linker_atom_ids
            or not record.linker_retained_local_indices
            or record.direct_scaffold_warhead_boundary is not None
            or record.applicable_canonical_task_ids != STRICT_TASK_IDS_V1
            or record.historical_snapshot_mask_compatibility is not True
        ):
            _fail("STRICT_PROFILE_CONTRACT_INVALID")
        recomputed = math.dist(
            record.protein_endpoint_coordinates_angstrom,
            record.ligand_endpoint_coordinates_angstrom,
        )
        if (
            record.struct_conn_evidence.evidence_kind
            != "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
            or record.struct_conn_evidence.protein_endpoint_comp_id != "CYS"
            or record.struct_conn_evidence.protein_endpoint_atom_id != "SG"
            or record.struct_conn_evidence.ligand_endpoint_comp_id
            != record.ligand_component_id
            or record.struct_conn_evidence.ligand_endpoint_atom_id
            != record.ligand_reactive_atom_id
            or not math.isfinite(recomputed)
            or recomputed <= 0
            or abs(recomputed - record.post_reactive_pair_distance_angstrom) > 0.000001
        ):
            _fail("STRUCTURAL_RECORD_POST_GEOMETRY_INVALID")
        if (
            record.minimal_seed_authority_available is not False
            or record.split_admission_authoritative is not False
            or record.sample_training_admitted is not False
            or record.feature_projection_status != "EXACT10_PASS"
        ):
            _fail("STRUCTURAL_RECORD_AUTHORITY_BOUNDARY_INVALID")
        return True
    except Exception as error:
        _public_error(error)


def build_covapie_batch001_positive_structural_records_v1(
    *, repository_root: object = None, cache_root: object = None
) -> tuple[CovapieBatch001PositiveStructuralRecordV1, ...]:
    """Build the exact 13 deterministic event-specific structural records."""

    try:
        repo = _require_root(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        cache = _require_root(
            cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID"
        )
        inputs = _verified_inputs(repo, cache)
        decisions, matrix_rows = _snapshot_and_matrix_sources(inputs)
        attempt_rows = _attempt_sources(inputs)
        records = tuple(
            _build_record(
                event_id=event_id,
                decision=decisions[event_id],
                matrix=matrix_rows[event_id],
                attempt=attempt_rows[event_id],
                structure_payload=inputs["structures"][_event_identity(event_id)["pdb_id"]],
                ccd_payload=inputs["ccds"][_event_identity(event_id)["ligand_component_id"]],
            )
            for event_id in BATCH001_POSITIVE_EVENT_IDS_V1
        )
        if tuple(record.canonical_event_id for record in records) != BATCH001_POSITIVE_EVENT_IDS_V1:
            _fail("BUILT_EXACT13_POPULATION_INVALID")
        for record in records:
            validate_covapie_batch001_positive_structural_record_v1(record)
        if (
            sum(record.role_profile == STRICT_LINKER_PRESENT_V1 for record in records) != 11
            or sum(record.role_profile == DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 for record in records) != 2
        ):
            _fail("ROLE_PROFILE_COUNT_INVALID")
        return records
    except Exception as error:
        _public_error(error)


def structural_record_as_evidence_dict_v1(
    record: object,
) -> dict[str, Any]:
    """Return a deterministic JSON-safe, path-relative evidence record."""

    validate_covapie_batch001_positive_structural_record_v1(record)
    assert isinstance(record, CovapieBatch001PositiveStructuralRecordV1)
    result = asdict(record)
    result["ligand_retained_heavy_count"] = len(record.ligand_retained_heavy_atoms)
    result["pocket_retained_heavy_count"] = len(record.pocket_retained_heavy_atoms)
    result["target_cys_retained_heavy_count"] = len(
        record.target_cys_pocket_local_indices
    )
    result["effective_role_profile_task_applicability"] = list(
        record.applicable_canonical_task_ids
    )
    return result
