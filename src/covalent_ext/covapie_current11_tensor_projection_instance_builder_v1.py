"""Build the Current11 Exact11 x Exact25 projection instance in memory."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_tensor_projection_payload_builder_v1 as _payload_builder


__all__ = ("build_covapie_current11_tensor_projection_instance_v1",)

_ERROR = "COVAPIE_CURRENT11_TENSOR_PROJECTION_INSTANCE_BUILDER_V1_ERROR"
_INSTANCE_NAME = "current11_tensor_projection_instance.json"
_REPORT_NAME = "current11_tensor_projection_instance_builder_report.json"
_ARTIFACT_NAMES = (_INSTANCE_NAME, _REPORT_NAME)
_INSTANCE_SCHEMA = "covapie_current11_tensor_projection_instance_v1"
_REPORT_SCHEMA = "covapie_current11_tensor_projection_instance_builder_report_v1"
_STATUS = "PASS_IN_MEMORY_FULL_EXACT25_PROJECTION_INSTANCE_ONLY"
_DOMAIN_TAG = b"COVAPIE_CURRENT11_TENSOR_PROJECTION_INSTANCE_V1\0"

_PAYLOAD_MODULE_RELATIVE = (
    "src/covalent_ext/covapie_current11_tensor_projection_payload_builder_v1.py"
)
_PAYLOAD_MODULE_SHA256 = (
    "c6229dce93afb82766ef1b6aacf5c547e32145f334d51ebbd6ac1d7ea5a4e197"
)
_PAYLOAD_BUILDER_COMMIT = "bc927ef679a6605339d8879559f69fc5ab3002a7"
_PAYLOAD_BUNDLE_DIGEST = (
    "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
)
_GATE_MODULE_RELATIVE = (
    "src/covalent_ext/"
    "covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py"
)
_GATE_MODULE_SHA256 = (
    "d46ebaf163abf862aadb35301efa649eac6dc799da434e29f58f95deae2cbe0f"
)
_CONTRACT_DIGEST = (
    "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
)
_CONTRACT_SCHEMA = "covapie_current11_routing_tensor_projection_contract_v1"
_FORMAL_RELATIVE = (
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_FORMAL_READLINK = (
    ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-"
    "1fd8cf5823427e941b11c7b2560a336f"
)
_FORMAL_AGGREGATE_SHA256 = (
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
)
_FORMAL_SNAPSHOT_SHA256 = (
    "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
)
_FORMAL_FILES = {
    "current11_dataset_partial_supervision_routing_records.csv": (
        69557,
        276,
        "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03",
    ),
    "current11_dataset_partial_supervision_task_coverage.csv": (
        1883,
        26,
        "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7",
    ),
    "current11_dataset_partial_supervision_sample_coverage.csv": (
        1445,
        12,
        "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e",
    ),
    "current11_dataset_partial_supervision_routing_manifest.json": (
        43109,
        1044,
        "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d",
    ),
}
_REPOSITORY_EXACT4 = (
    "docs/covapie_current11_tensor_projection_instance_builder_v1_guide.md",
    "scripts/check_covapie_current11_tensor_projection_instance_builder_v1.py",
    "src/covalent_ext/covapie_current11_tensor_projection_instance_builder_v1.py",
    "tests/test_covapie_current11_tensor_projection_instance_builder_v1.py",
)
_PAYLOAD_NAMES = (
    "current11_tensor_projection_payload_bundle_manifest.json",
    "current11_tensor_projection_payload_sample_identity.json",
    "current11_tensor_projection_payload_explicit_covalent_event.json",
    "current11_tensor_projection_payload_ligand_residue_atom_pair.json",
    "current11_tensor_projection_payload_warhead_boundary.json",
    "current11_tensor_projection_payload_observed_complex_geometry.json",
    "current11_tensor_projection_payload_provenance.json",
    "current11_tensor_projection_payload_builder_report.json",
)
_PAYLOAD_IDENTITIES = {
    _PAYLOAD_NAMES[0]: (17038, 341, "d4a1fac58d869a97a73b3f645344aeabf300df604b7ddadfcc55bcb23380df3c"),
    _PAYLOAD_NAMES[1]: (6645, 554, "bbe2426593ca5d8df59604ec5ef91fdefb0d6e34abba4eea57b1c7abd65748e8"),
    _PAYLOAD_NAMES[2]: (6744, 229, "ca55e53f43c2b7743da9b2445b649d66a6e4bfbbd4f1ea5f52ccd2000b939688"),
    _PAYLOAD_NAMES[3]: (6381, 302, "fc73c3ed9113ad5183da0bfbc211113e524430ee5546d1c1acbabe6a1a4bf692"),
    _PAYLOAD_NAMES[4]: (12830, 1007, "77a489114b9b74e7f50bdcc09f33da2a005bc7472f78ccd64bbd4adafa7942c5"),
    _PAYLOAD_NAMES[5]: (2444, 98, "d59d1ceeed3b8626d4bd91c2a058d81884e23635cdcf0a4ea980da7155a7fb4e"),
    _PAYLOAD_NAMES[6]: (119508, 2798, "4bd1d06af9c763eeed75cad0b93b4d0699d9da93014c940658a4f065dc16abe9"),
    _PAYLOAD_NAMES[7]: (5229, 144, "05e456e762ba554aeb110dd64e2a3b4eae35ddba1a2144602da40c53873ab7c8"),
}
_PAYLOAD_TASKS = {
    0: _PAYLOAD_NAMES[1],
    1: _PAYLOAD_NAMES[2],
    2: _PAYLOAD_NAMES[3],
    6: _PAYLOAD_NAMES[4],
    12: _PAYLOAD_NAMES[5],
}
_SAMPLES = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP"),
)
_TASKS = (
    "sample_identity_supervision",
    "explicit_covalent_event_supervision",
    "ligand_residue_atom_pair_supervision",
    "covalent_link_bond_order_supervision",
    "warhead_type_supervision",
    "reaction_family_supervision",
    "warhead_boundary_supervision",
    "canonical_mask_warhead_only",
    "canonical_mask_linker_plus_warhead",
    "canonical_mask_scaffold_plus_warhead",
    "canonical_mask_scaffold_only",
    "canonical_mask_scaffold_plus_linker_plus_warhead",
    "observed_complex_geometry_supervision",
    "pre_covalent_geometry_supervision",
    "post_covalent_geometry_supervision",
    "complete_post_state_graph_supervision",
    "reaction_atom_map_supervision",
    "formed_edge_supervision",
    "broken_edge_supervision",
    "bond_order_delta_supervision",
    "formal_charge_delta_supervision",
    "protonation_transfer_supervision",
    "leaving_group_supervision",
    "reversibility_supervision",
    "full_transformation_supervision",
)
_MASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ()),
)
_ELIGIBILITY = (
    "admissible_now",
    "admissible_as_observed_geometry_only",
    "candidate_only_not_authoritative",
    "blocked_missing_evidence",
    "blocked_state_ambiguity",
    "blocked_missing_human_approval",
    "not_applicable",
)
_ELIGIBILITY_COUNTS = {0: 44, 1: 11, 2: 55, 3: 103, 4: 7, 5: 55, 6: 0}
_EVIDENCE = (
    "CANONICAL_SAMPLE_IDENTITY",
    "EXPLICIT_BINARY_COVALENT_EVENT",
    "EXPLICIT_LIGAND_RESIDUE_ATOM_PAIR",
    "AUTHORITATIVE_LINK_BOND_ORDER_ABSENT",
    "CANDIDATE_FAMILY_OR_WARHEAD_TYPE",
    "REVIEWED_WARHEAD_BOUNDARY_ONLY",
    "CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES",
    "OBSERVED_COMPLEX_COORDINATE_DISTANCE",
    "PRE_COVALENT_GEOMETRY_ABSENT",
    "POST_COVALENT_STATE_UNRESOLVED",
    "COMPLETE_POST_STATE_GRAPH_UNRESOLVED",
    "REACTION_ATOM_MAP_ABSENT",
    "CANDIDATE_FORMED_EDGE",
    "CANDIDATE_OR_AMBIGUOUS_BROKEN_EDGE",
    "BOND_ORDER_DELTA_ABSENT",
    "FORMAL_CHARGE_DELTA_ABSENT",
    "PROTONATION_TRANSFER_ABSENT",
    "CANDIDATE_LEAVING_GROUP",
    "SAMPLE_REVERSIBILITY_UNRESOLVED",
    "FULL_TRANSFORMATION_UNRESOLVED",
)
_BLOCKING = (
    "NONE",
    "OBSERVED_COMPLEX_GEOMETRY_ONLY",
    "AUTHORITATIVE_LINK_BOND_ORDER_MISSING",
    "CANDIDATE_LABEL_NOT_APPROVED",
    "PRIMARY_ROLE_AUTHORITY_INCOMPLETE",
    "PRE_COVALENT_GEOMETRY_MISSING",
    "DEDICATED_TRANSFORMATION_REVIEW_MISSING",
    "POST_STATE_AMBIGUOUS",
    "REACTION_ATOM_MAP_MISSING",
    "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY",
    "BOND_ORDER_DELTA_MISSING",
    "FORMAL_CHARGE_DELTA_MISSING",
    "PROTONATION_TRANSFER_MISSING",
    "SAMPLE_SPECIFIC_REVERSIBILITY_MISSING",
    "FULL_TRANSFORMATION_INCOMPLETE",
)
_RECORD_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "semantic_task_name",
    "eligibility_state",
    "direct_authority_found",
    "evidence_scope",
    "blocking_reason_code",
    "supporting_source_ids_json",
    "dedicated_transformation_review_available",
    "availability_mask_required",
    "current_runtime_consumer_available",
    "training_loss_authorized",
)
_INSTANCE_FIELDS = (
    "schema_version",
    "source_lineage",
    "sample_order",
    "task_order",
    "canonical_mask_semantics",
    "eligibility_state_code",
    "evidence_scope_code",
    "blocking_reason_code",
    "direct_authority_mask",
    "data_availability_mask",
    "applicability_mask",
    "candidate_only_mask",
    "observed_geometry_only_mask",
    "state_ambiguity_mask",
    "human_approval_missing_mask",
    "loss_authorization_mask",
    "runtime_consumer_available_mask",
    "task_payloads",
    "task_payload_validity",
    "task_payload_entry_validity",
    "candidate_payloads",
    "candidate_payload_validity",
    "task_payload_provenance",
    "projection_readiness",
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda unused: _fail(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        _fail()
    return value


def _require_root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if resolved != path or stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail()
    return path


def _safe_regular(root: Path, relative: str, expected_sha256: str) -> bytes:
    path = root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if (
        not resolved.is_relative_to(root)
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or not payload.endswith(b"\n")
        or _sha256(payload) != expected_sha256
    ):
        _fail()
    return payload


def _path_snapshot(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else _sha256(payload),
    )


def _formal_snapshot(canonical: Path) -> dict[str, object]:
    try:
        parent = canonical.parent
        link = os.readlink(canonical)
        object_path = parent / link
        object_inventory = tuple(sorted(os.listdir(object_path)))
        return {
            "parent": _path_snapshot(parent),
            "parent_inventory": tuple(sorted(os.listdir(parent))),
            "canonical": _path_snapshot(canonical),
            "readlink": link,
            "object": _path_snapshot(object_path),
            "object_inventory": object_inventory,
            "leaves": {name: _path_snapshot(object_path / name) for name in object_inventory},
        }
    except OSError as error:
        raise ValueError(_ERROR) from error


def _read_formal(canonical: Path) -> dict[str, bytes]:
    try:
        if os.readlink(canonical) != _FORMAL_READLINK or not stat.S_ISLNK(canonical.lstat().st_mode):
            _fail()
        object_path = canonical.parent / _FORMAL_READLINK
        if (
            not stat.S_ISDIR(object_path.lstat().st_mode)
            or stat.S_IMODE(object_path.lstat().st_mode) != 0o755
            or tuple(sorted(os.listdir(object_path))) != tuple(sorted(_FORMAL_FILES))
        ):
            _fail()
        result: dict[str, bytes] = {}
        for name, (size, lines, digest) in _FORMAL_FILES.items():
            path = object_path / name
            metadata = path.lstat()
            payload = path.read_bytes()
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or len(payload) != size
                or payload.count(b"\n") != lines
                or _sha256(payload) != digest
                or not payload.endswith(b"\n")
            ):
                _fail()
            result[name] = payload
        return result
    except OSError as error:
        raise ValueError(_ERROR) from error


@contextmanager
def _successor_status_compatibility() -> Iterator[None]:
    gate = _payload_builder._contract_gate
    original = gate._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            lines = output.splitlines()
            if any(
                len(line) >= 4 and line[3:] in _REPOSITORY_EXACT4 and line not in allowed
                for line in lines
            ):
                _fail()
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        gate._run_git = compatible
        yield
    finally:
        gate._run_git = original


def _payload_exact8(
    repo_root: Path, state_root: Path
) -> tuple[dict[str, bytes], dict[str, object], dict[str, object]]:
    _safe_regular(repo_root, _PAYLOAD_MODULE_RELATIVE, _PAYLOAD_MODULE_SHA256)
    _safe_regular(repo_root, _GATE_MODULE_RELATIVE, _GATE_MODULE_SHA256)
    gate = _payload_builder._contract_gate
    original_gate_api = gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1
    captured_contracts: list[dict[str, bytes]] = []

    def capture_contract(**arguments: object) -> dict[str, bytes]:
        result = original_gate_api(**arguments)
        captured_contracts.append(result)
        return result

    try:
        gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1 = capture_contract
        with _successor_status_compatibility():
            first = _payload_builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
                repo_root=repo_root, state_root=state_root
            )
            second = _payload_builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
                repo_root=repo_root, state_root=state_root
            )
    finally:
        gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1 = original_gate_api
    if (
        type(first) is not dict
        or type(second) is not dict
        or tuple(first) != _PAYLOAD_NAMES
        or first != second
        or any(type(value) is not bytes for value in first.values())
    ):
        _fail()
    decoded: dict[str, object] = {}
    for name, payload in first.items():
        size, lines, digest = _PAYLOAD_IDENTITIES[name]
        if len(payload) != size or payload.count(b"\n") != lines or _sha256(payload) != digest:
            _fail()
        decoded[name] = _strict_json(payload)
    report = decoded[_PAYLOAD_NAMES[7]]
    manifest = decoded[_PAYLOAD_NAMES[0]]
    if (
        type(report) is not dict
        or report.get("builder_status") != "PASS_IN_MEMORY_PAYLOAD_BUNDLE_ONLY"
        or report.get("payload_bundle_digest") != _PAYLOAD_BUNDLE_DIGEST
        or type(manifest) is not dict
        or manifest.get("source_contract_lineage")
        != {
            "published_contract_digest": _CONTRACT_DIGEST,
            "published_gate_module_relative_path": _GATE_MODULE_RELATIVE,
            "published_gate_module_sha256": _GATE_MODULE_SHA256,
        }
    ):
        _fail()
    contract_names = tuple(gate.ARTIFACT_NAMES)
    if (
        len(captured_contracts) != 4
        or any(type(value) is not dict or tuple(value) != contract_names for value in captured_contracts)
        or any(value != captured_contracts[0] for value in captured_contracts[1:])
    ):
        _fail()
    contract_manifest = _strict_json(captured_contracts[0][contract_names[0]])
    contract_report = _strict_json(captured_contracts[0][contract_names[3]])
    if (
        contract_manifest.get("schema_version") != _CONTRACT_SCHEMA
        or contract_report.get("gate_status") != "PASS_CONTRACT_ONLY"
        or contract_report.get("contract_digest") != _CONTRACT_DIGEST
    ):
        _fail()
    return first, decoded, contract_manifest


def _matrix(rows: Sequence[dict[str, str]], key: str, converter: object) -> list[list[object]]:
    result: list[list[object]] = []
    for sample_index, sample in enumerate(_SAMPLES):
        current: list[object] = []
        for task_index, task in enumerate(_TASKS):
            row = rows[sample_index * 25 + task_index]
            if (
                row["sample_index_row_id"] != sample[0]
                or row["pdb_id"] != sample[1]
                or row["ligand_comp_id"] != sample[2]
                or row["semantic_task_name"] != task
            ):
                _fail()
            current.append(converter(row[key]))
        result.append(current)
    return result


def _routing(
    formal: Mapping[str, bytes], contract_manifest: Mapping[str, object] | None = None
) -> dict[str, object]:
    manifest = _strict_json(formal["current11_dataset_partial_supervision_routing_manifest.json"])
    if contract_manifest is None:
        expected_tasks = list(_TASKS)
        expected_eligibility = list(_ELIGIBILITY)
        expected_evidence = list(_EVIDENCE)
        expected_blocking = list(_BLOCKING)
    else:
        expected_tasks = contract_manifest.get("task_order")
        expected_eligibility = contract_manifest.get("eligibility_state_code_order")
        expected_evidence = contract_manifest.get("evidence_scope_code_order")
        expected_blocking = contract_manifest.get("blocking_reason_code_order")
        if (
            expected_tasks
            != [
                {"task_index": index, "semantic_task_name": task}
                for index, task in enumerate(_TASKS)
            ]
            or expected_eligibility
            != [
                {"code": index, "eligibility_state": value}
                for index, value in enumerate(_ELIGIBILITY)
            ]
            or expected_evidence
            != [
                {"code": index, "evidence_scope": value}
                for index, value in enumerate(_EVIDENCE)
            ]
            or expected_blocking
            != [
                {"code": index, "blocking_reason": value}
                for index, value in enumerate(_BLOCKING)
            ]
        ):
            _fail()
    if (
        manifest.get("canonical_sample_identity")
        != [
            {"ligand_comp_id": item[2], "pdb_id": item[1], "sample_index_row_id": item[0]}
            for item in _SAMPLES
        ]
        or manifest.get("semantic_task_names") != list(_TASKS)
        or manifest.get("eligibility_state_vocabulary") != list(_ELIGIBILITY)
        or manifest.get("evidence_scope_vocabulary") != list(_EVIDENCE)
        or manifest.get("blocking_reason_vocabulary") != list(_BLOCKING)
    ):
        _fail()
    try:
        reader = csv.DictReader(io.StringIO(formal["current11_dataset_partial_supervision_routing_records.csv"].decode("utf-8"), newline=""))
        rows = list(reader)
    except (csv.Error, UnicodeDecodeError) as error:
        raise ValueError(_ERROR) from error
    if tuple(reader.fieldnames or ()) != _RECORD_COLUMNS or len(rows) != 275:
        _fail()

    def boolean(value: str) -> bool:
        if value not in ("true", "false"):
            _fail()
        return value == "true"

    def vocabulary_code(value: str, vocabulary: Sequence[str]) -> int:
        try:
            return vocabulary.index(value)
        except ValueError as error:
            raise ValueError(_ERROR) from error

    eligibility = _matrix(rows, "eligibility_state", lambda value: vocabulary_code(value, _ELIGIBILITY))
    evidence = _matrix(rows, "evidence_scope", lambda value: vocabulary_code(value, _EVIDENCE))
    blocking = _matrix(rows, "blocking_reason_code", lambda value: vocabulary_code(value, _BLOCKING))
    direct = _matrix(rows, "direct_authority_found", boolean)
    loss = _matrix(rows, "training_loss_authorized", boolean)
    runtime = _matrix(rows, "current_runtime_consumer_available", boolean)
    flat = [value for row in eligibility for value in row]
    counts = Counter(flat)
    if (
        any(counts[code] != expected for code, expected in _ELIGIBILITY_COUNTS.items())
        or set(counts) - set(_ELIGIBILITY_COUNTS)
        or any(value for row in loss for value in row)
        or any(value for row in runtime for value in row)
    ):
        _fail()
    return {
        "eligibility": eligibility,
        "evidence": evidence,
        "blocking": blocking,
        "direct": direct,
        "loss": loss,
        "runtime": runtime,
    }


def _validate_offsets(offsets: object, final: int) -> bool:
    return (
        type(offsets) is list
        and len(offsets) >= 1
        and offsets[0] == 0
        and offsets[-1] == final
        and all(type(value) is int for value in offsets)
        and all(left <= right for left, right in zip(offsets, offsets[1:]))
    )


def _entry_validity(task_index: int, payload: Mapping[str, object]) -> dict[str, object]:
    sample = payload.get("sample_validity_bool")
    if sample != [True] * 11:
        _fail()
    if task_index == 0:
        names = ("sample_index_row_id", "pdb_id", "ligand_comp_id")
        offsets_validity: dict[str, list[bool]] = {}
        for name in names:
            buffer = payload.get(name)
            if type(buffer) is not dict:
                _fail()
            raw = buffer.get("bytes_uint8")
            offsets = buffer.get("offsets_int64")
            if type(raw) is not list or not _validate_offsets(offsets, len(raw)) or len(offsets) != 12:
                _fail()
            offsets_validity[name] = [True] * 12
        value = {"sample_validity_bool": sample, "utf8_offsets_validity_bool": offsets_validity}
    elif task_index == 1:
        if payload.get("values_bool") != [True] * 11:
            _fail()
        value = {"sample_validity_bool": sample}
    elif task_index == 2:
        offsets = payload.get("sample_offsets_int64")
        entries = payload.get("entry_validity_bool")
        values = payload.get("values_int64")
        if offsets != list(range(12)) or entries != [True] * 11 or type(values) is not list or len(values) != 11:
            _fail()
        value = {
            "sample_validity_bool": sample,
            "entry_validity_bool": entries,
            "sample_offsets_int64": offsets,
        }
    elif task_index == 6:
        checks = (
            ("sample_token_offsets_int64", 118),
            ("sample_warhead_offsets_int64", 102),
            ("sample_boundary_offsets_int64", 16),
        )
        if any(not _validate_offsets(payload.get(name), final) or len(payload[name]) != 12 for name, final in checks):
            _fail()
        if (
            payload.get("token_validity_bool") != [True] * 118
            or payload.get("warhead_entry_validity_bool") != [True] * 102
            or payload.get("boundary_entry_validity_bool") != [True] * 16
        ):
            _fail()
        value = {
            "sample_validity_bool": sample,
            "token_validity_bool": payload["token_validity_bool"],
            "warhead_entry_validity_bool": payload["warhead_entry_validity_bool"],
            "boundary_entry_validity_bool": payload["boundary_entry_validity_bool"],
            "sample_token_offsets_int64": payload["sample_token_offsets_int64"],
            "sample_warhead_offsets_int64": payload["sample_warhead_offsets_int64"],
            "sample_boundary_offsets_int64": payload["sample_boundary_offsets_int64"],
        }
    elif task_index == 12:
        hexadecimal = payload.get("values_float32_le_hex")
        if type(hexadecimal) is not str or len(bytes.fromhex(hexadecimal)) != 44 or payload.get("logical_shape") != [11, 1]:
            _fail()
        value = {
            "sample_validity_bool": sample,
            "float32_byte_validity_bool": [True] * 44,
            "logical_shape": [11, 1],
        }
    else:
        _fail()
    return value


def _payload_slots(decoded: Mapping[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    slots: list[dict[str, object]] = []
    entries: list[dict[str, object]] = []
    for index, task in enumerate(_TASKS):
        name = _PAYLOAD_TASKS.get(index)
        if name is None:
            slots.append({
                "task_index": index,
                "semantic_task_name": task,
                "payload_materialized_in_memory": False,
                "payload_schema_version": None,
                "source_payload_artifact_name": None,
                "payload": None,
            })
            entries.append({
                "task_index": index,
                "semantic_task_name": task,
                "entry_validity_materialized_in_memory": False,
                "entry_validity_schema": None,
                "entry_validity": None,
            })
            continue
        payload = decoded[name]
        if type(payload) is not dict or type(payload.get("schema_version")) is not str:
            _fail()
        slots.append({
            "task_index": index,
            "semantic_task_name": task,
            "payload_materialized_in_memory": True,
            "payload_schema_version": payload["schema_version"],
            "source_payload_artifact_name": name,
            "payload": payload,
        })
        entries.append({
            "task_index": index,
            "semantic_task_name": task,
            "entry_validity_materialized_in_memory": True,
            "entry_validity_schema": f"covapie_current11_tensor_projection_instance_task_{index}_entry_validity_v1",
            "entry_validity": _entry_validity(index, payload),
        })
    return slots, entries


def _provenance(decoded: Mapping[str, object]) -> list[dict[str, object]]:
    provenance = decoded[_PAYLOAD_NAMES[6]]
    if type(provenance) is not dict:
        _fail()
    records = provenance.get("cell_provenance_records")
    expected_indices = tuple(_PAYLOAD_TASKS)
    secondary_count = 0
    if type(records) is not list or len(records) != 55:
        _fail()
    for cell, record in enumerate(records):
        sample_index, task_minor = divmod(cell, 5)
        task_index = expected_indices[task_minor]
        if (
            type(record) is not dict
            or record.get("cell_index") != cell
            or record.get("sample_index") != sample_index
            or record.get("sample_index_row_id") != _SAMPLES[sample_index][0]
            or record.get("semantic_task_name") != _TASKS[task_index]
            or record.get("payload_artifact_name") != _PAYLOAD_TASKS[task_index]
            or record.get("payload_entry_locator") != {"sample_index": sample_index, "task_index": task_index}
            or record.get("payload_valid") is not True
            or record.get("provenance_complete") is not True
            or record.get("candidate_promotion_used") is not False
            or record.get("inference_used") is not False
            or record.get("semantic_promotion_used") is not False
        ):
            _fail()
        bindings = record.get("source_bindings")
        secondary = record.get("secondary_source_bindings")
        if type(bindings) is not list or type(secondary) is not list:
            _fail()
        secondary_count += len(secondary)
        for binding in (*bindings, *secondary):
            if type(binding) is not dict:
                _fail()
            for key, value in binding.items():
                if "path" in key and (type(value) is not str or Path(value).is_absolute()):
                    _fail()
        if task_index == 6:
            locator = record.get("source_record_locators")
            if type(locator) is not dict or set(locator) != {
                "effective_authority_record_index_0based",
                "source_authority_record_sha256",
                "source_authority_record_version",
                "source_id",
            }:
                _fail()
        if task_index == 12:
            check = record.get("consistency_check")
            if type(check) is not dict or check.get("passed") is not True:
                _fail()
    if secondary_count != 22:
        _fail()
    return records


def _source_lineage(decoded: Mapping[str, object]) -> dict[str, object]:
    manifest = decoded[_PAYLOAD_NAMES[0]]
    if type(manifest) is not dict:
        _fail()
    audit = manifest.get("audit_lineage")
    if type(audit) is not dict or audit.get("runtime_dependency") is not False or audit.get("payload_value_authority") is not False:
        _fail()
    return {
        "projection_contract_gate": {
            "module_relative_path": _GATE_MODULE_RELATIVE,
            "module_sha256": _GATE_MODULE_SHA256,
            "contract_digest": _CONTRACT_DIGEST,
            "schema_version": _CONTRACT_SCHEMA,
        },
        "payload_builder": {
            "module_relative_path": _PAYLOAD_MODULE_RELATIVE,
            "module_sha256": _PAYLOAD_MODULE_SHA256,
            "commit": _PAYLOAD_BUILDER_COMMIT,
            "payload_bundle_digest": _PAYLOAD_BUNDLE_DIGEST,
            "exact8_artifact_sha256": {name: identity[2] for name, identity in _PAYLOAD_IDENTITIES.items()},
        },
        "formal_routing_sidecar": {
            "canonical_relative_path": _FORMAL_RELATIVE,
            "readlink": _FORMAL_READLINK,
            "formal_snapshot_sha256": _FORMAL_SNAPSHOT_SHA256,
            "formal_aggregate_sha256": _FORMAL_AGGREGATE_SHA256,
            "exact4_sha256": {name: identity[2] for name, identity in _FORMAL_FILES.items()},
        },
        "non_runtime_lineage": {
            "audit_markdown_relative_path": audit["relative_path"],
            "audit_markdown_sha256": audit["sha256"],
            "runtime_dependency": False,
            "payload_authority": False,
        },
    }


def _assemble(routing: Mapping[str, object], decoded: Mapping[str, object]) -> dict[str, object]:
    eligibility = routing["eligibility"]
    if type(eligibility) is not list:
        _fail()
    applicability = [[value != 6 for value in row] for row in eligibility]
    candidate = [[value == 2 for value in row] for row in eligibility]
    observed = [[value == 1 for value in row] for row in eligibility]
    ambiguity = [[value == 4 for value in row] for row in eligibility]
    approval = [[value == 5 for value in row] for row in eligibility]
    validity = [[task_index in _PAYLOAD_TASKS for task_index in range(25)] for unused in range(11)]
    availability = [
        [validity[sample][task] and eligibility[sample][task] in (0, 1) for task in range(25)]
        for sample in range(11)
    ]
    if availability != validity or sum(value for row in availability for value in row) != 55:
        _fail()
    slots, entry_validity = _payload_slots(decoded)
    candidate_slots = [
        {
            "task_index": index,
            "semantic_task_name": task,
            "candidate_payload_materialized_in_memory": False,
            "candidate_payload": None,
        }
        for index, task in enumerate(_TASKS)
    ]
    instance = {
        "schema_version": _INSTANCE_SCHEMA,
        "source_lineage": _source_lineage(decoded),
        "sample_order": [
            {"sample_index": index, "sample_index_row_id": sample[0], "pdb_id": sample[1], "ligand_comp_id": sample[2]}
            for index, sample in enumerate(_SAMPLES)
        ],
        "task_order": [
            {"task_index": index, "semantic_task_name": task}
            for index, task in enumerate(_TASKS)
        ],
        "canonical_mask_semantics": [
            {"mask_index": index, "semantic_name": semantic, "display_alias": alias, "generated_roles": list(generated), "fixed_roles": list(fixed)}
            for index, semantic, alias, generated, fixed in _MASKS
        ],
        "eligibility_state_code": eligibility,
        "evidence_scope_code": routing["evidence"],
        "blocking_reason_code": routing["blocking"],
        "direct_authority_mask": routing["direct"],
        "data_availability_mask": availability,
        "applicability_mask": applicability,
        "candidate_only_mask": candidate,
        "observed_geometry_only_mask": observed,
        "state_ambiguity_mask": ambiguity,
        "human_approval_missing_mask": approval,
        "loss_authorization_mask": routing["loss"],
        "runtime_consumer_available_mask": routing["runtime"],
        "task_payloads": slots,
        "task_payload_validity": validity,
        "task_payload_entry_validity": entry_validity,
        "candidate_payloads": candidate_slots,
        "candidate_payload_validity": [[False] * 25 for unused in range(11)],
        "task_payload_provenance": _provenance(decoded),
        "projection_readiness": {
            "projection_instance_builder_implemented": True,
            "projection_instance_builder_passed": True,
            "full_exact25_projection_schema_instantiated_in_memory": True,
            "routing_matrices_built_in_memory": True,
            "task_slots_materialized_in_memory": True,
            "authoritative_or_observed_payload_cells_built_in_memory": 55,
            "task_payload_validity_built_in_memory": True,
            "data_availability_matrix_built_in_memory": True,
            "data_availability_true_count": 55,
            "candidate_payloads_materialized": False,
            "candidate_payload_validity_true_count": 0,
            "loss_authorization_true_count": 0,
            "runtime_consumer_available_true_count": 0,
            "formal_projection_instance_materialized": False,
            "formal_payload_bundle_materialized": False,
            "torch_tensor_materialized": False,
            "numpy_artifact_materialized": False,
            "ready_for_batch_index_remap_adapter_design": True,
            "ready_for_dataloader_integration": False,
            "ready_for_model_integration": False,
            "training_loss_authorized": False,
            "training_performed": False,
            "feature_semantics_reaudit_required_before_training": True,
            "ready_for_training": False,
        },
    }
    if tuple(instance) != _INSTANCE_FIELDS or len(instance) != 24:
        _fail()
    return instance


def _stable_digest(payload: bytes) -> str:
    name = _INSTANCE_NAME.encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_DOMAIN_TAG)
    digest.update(len(name).to_bytes(8, "big", signed=False))
    digest.update(name)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _validate_artifact(payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or _canonical_json(_strict_json(payload)) != payload
    ):
        _fail()


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    canonical = state / _FORMAL_RELATIVE
    before = _formal_snapshot(canonical)
    unused_payload_bytes, decoded, contract_manifest = _payload_exact8(repository, state)
    del unused_payload_bytes
    formal = _read_formal(canonical)
    routing = _routing(formal, contract_manifest)
    first = _canonical_json(_assemble(routing, decoded))
    second = _canonical_json(_assemble(routing, decoded))
    if first != second:
        _fail()
    _validate_artifact(first)
    digest = _stable_digest(first)
    after = _formal_snapshot(canonical)
    if before != after:
        _fail()
    report_value = {
        "schema_version": _REPORT_SCHEMA,
        "builder_status": _STATUS,
        "projection_instance_digest": digest,
        "artifact_file_count": 2,
        "artifact_identities": [
            {
                "artifact_index": 0,
                "artifact_name": _INSTANCE_NAME,
                "stable_digest_participation": True,
                "bytes": len(first),
                "lines": first.count(b"\n"),
                "sha256": _sha256(first),
            },
            {
                "artifact_index": 1,
                "artifact_name": _REPORT_NAME,
                "stable_digest_participation": False,
                "content_identity": "self_excluded",
            },
        ],
        "contract_gate_passed": True,
        "contract_digest": _CONTRACT_DIGEST,
        "payload_builder_passed": True,
        "payload_bundle_digest": _PAYLOAD_BUNDLE_DIGEST,
        "payload_exact8_double_build_identical": True,
        "formal_sidecar_check_passed": True,
        "formal_snapshot_unchanged": True,
        "formal_aggregate_sha256": _FORMAL_AGGREGATE_SHA256,
        "formal_exact4_sha256": {name: identity[2] for name, identity in _FORMAL_FILES.items()},
        "sample_count": 11,
        "task_count": 25,
        "routing_cell_count": 275,
        "payload_slot_count": 25,
        "audited_payload_task_indices": [0, 1, 2, 6, 12],
        "eligibility_permitted_count": 55,
        "validated_payload_cell_count": 55,
        "task_payload_validity_true_count": 55,
        "data_availability_true_count": 55,
        "candidate_eligible_count": 55,
        "candidate_payload_materialized_count": 0,
        "candidate_payload_validity_true_count": 0,
        "applicability_true_count": 275,
        "observed_geometry_only_true_count": 11,
        "state_ambiguity_true_count": 7,
        "human_approval_missing_true_count": 55,
        "loss_authorization_true_count": 0,
        "runtime_consumer_available_true_count": 0,
        "provenance_record_count": 55,
        "readiness": _strict_json(first)["projection_readiness"],
    }
    report = _canonical_json(report_value)
    _validate_artifact(report)
    artifacts = {_INSTANCE_NAME: first, _REPORT_NAME: report}
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES or len(artifacts) != 2:
        _fail()
    return artifacts


def build_covapie_current11_tensor_projection_instance_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]:
    """Return the deterministic Current11 projection instance Exact2 in memory."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
