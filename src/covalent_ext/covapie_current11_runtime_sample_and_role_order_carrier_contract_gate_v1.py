"""Build the read-only Current11 runtime carrier contract gate V1."""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import io
import json
import os
import re
import stat
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator, Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as _adapter
from covalent_ext import covapie_current11_task2_batch_index_remap_contract_gate_v1 as _remap_gate


__all__ = (
    "build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1",
)

_ERROR = "COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_CONTRACT_GATE_V1_ERROR"
_STATUS = "PASS_CONTRACT_ONLY"
_SCHEMA = "covapie_current11_runtime_sample_and_role_order_carrier_contract_v1"
_SAMPLE_KEY_SCHEMA = "covapie_sample_index_row_id_in_names_v1"
_ROLE_ORDER_SCHEMA = "order_preserving_checkpoint_heavy_projection_v1"
_ROLE_REGISTRY_SCHEMA = "covapie_current11_runtime_role_order_registry_v1"
_CARRIER_SCHEMA = "covapie_current11_runtime_sample_and_role_order_carrier_manifest_v1"
_REPORT_SCHEMA = (
    "covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_report_v1"
)
_RUNTIME_BATCH_SCHEMA = "processed_ligand_pocket_dataset_collate_observation_no_virtual_v1"
_VIRTUAL_POLICY = "no_virtual_nodes_v1"
_RUNTIME_KIND = "current11_processed_ligand_pocket_npz_v1"
_DOMAIN_TAG = (
    b"COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_CONTRACT_GATE_V1\0"
)

_MANIFEST = "current11_runtime_sample_and_role_order_carrier_contract_manifest.json"
_SAMPLE_REGISTRY = "current11_runtime_sample_key_registry.csv"
_ROLE_REGISTRY = "current11_runtime_role_order_registry.json"
_CARRIER_MANIFEST_SCHEMA = "current11_runtime_carrier_manifest_schema.json"
_VOCABULARY = (
    "current11_runtime_sample_and_role_order_carrier_status_vocabulary.csv"
)
_REPORT = (
    "current11_runtime_sample_and_role_order_carrier_contract_gate_report.json"
)
_ARTIFACT_NAMES = (
    _MANIFEST,
    _SAMPLE_REGISTRY,
    _ROLE_REGISTRY,
    _CARRIER_MANIFEST_SCHEMA,
    _VOCABULARY,
    _REPORT,
)
_STABLE_NAMES = _ARTIFACT_NAMES[:5]
_REPOSITORY_EXACT4 = (
    "src/covalent_ext/covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1.py",
    "scripts/check_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1.py",
    "tests/test_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1.py",
    "docs/covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1_guide.md",
)

_ADAPTER_RELATIVE = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_v1.py"
)
_ADAPTER_BYTES = 56510
_ADAPTER_LF = 1368
_ADAPTER_SHA256 = "d09bd5648a3c47851efd933fa8c0523c4ab7c67f8cce765b08fb8423a4e57dd2"
_ADAPTER_BLOB = "11573d4e0857cf69dceb22c3b1ec4f319faa6d08"
_ADAPTER_COMMIT = "b3c76bd4321da5aece08711a4d6f2d421cb8b54b"
_ADAPTER_OUTPUT_NAME = "current11_task2_batch_index_remap_output.json"
_ADAPTER_REPORT_NAME = "current11_task2_batch_index_remap_adapter_report.json"
_ADAPTER_ARTIFACT_NAMES = (_ADAPTER_OUTPUT_NAME, _ADAPTER_REPORT_NAME)
_ADAPTER_OUTPUT_BYTES = 7872
_ADAPTER_OUTPUT_LF = 416
_ADAPTER_OUTPUT_SHA256 = (
    "af21df0f1686bc898ae51d57c5dcfaf9f2d3c4488906ef241f7c98fdb04a9a3c"
)
_ADAPTER_REPORT_BYTES = 2505
_ADAPTER_REPORT_LF = 61
_ADAPTER_REPORT_SHA256 = (
    "1af588f06e58316077c43c331306d338a121d14a3fa17038a682114729ad78f4"
)
_ADAPTER_OUTPUT_DOMAIN_TAG = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1\0"
_ADAPTER_OUTPUT_DIGEST = "7e141fadc5a39bbad17e33eceb24f67efeff15d8057d785c56eebe940ff5a658"
_ADAPTER_CHECKER_RELATIVE = (
    "scripts/check_covapie_current11_task2_batch_index_remap_adapter_v1.py"
)
_ADAPTER_CHECKER_BYTES = 2207
_ADAPTER_CHECKER_LF = 69
_ADAPTER_CHECKER_SHA256 = (
    "48cd03d8474282140c355ee85c8a2ef51131369170f04a4ac9b2fcda078b09e2"
)
_ADAPTER_CHECKER_BLOB = "e813db9d21feb743cbb070b6fb4e5ebee8097947"
_REMAP_RELATIVE = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_contract_gate_v1.py"
)
_REMAP_BYTES = 70077
_REMAP_LF = 926
_REMAP_SHA256 = "e9f7d83a17d08eda338ce4d64ab60241887e488c6139ee70af7f210b82bc6eec"
_REMAP_BLOB = "6d5f495bac770ef4a87f641ae340fd39947122f4"
_REMAP_COMMIT = "6502321ca56ce8895adb3ee20587c383dfbda767"
_REMAP_DIGEST = "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
_PROJECTION_DIGEST = "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
_PAYLOAD_DIGEST = "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
_PROJECTION_CONTRACT_DIGEST = (
    "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
)

_FORMAL_RELATIVE = (
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_FORMAL_READLINK = (
    ".current11-dataset-partial-supervision-routing-sidecar-v2."
    "object-sha256-24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-"
    "1fd8cf5823427e941b11c7b2560a336f"
)
_FORMAL_AGGREGATE = "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
_FORMAL_SNAPSHOT = "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
_FORMAL_EXACT4 = {
    "current11_dataset_partial_supervision_routing_manifest.json": (
        "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d"
    ),
    "current11_dataset_partial_supervision_routing_records.csv": (
        "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03"
    ),
    "current11_dataset_partial_supervision_sample_coverage.csv": (
        "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e"
    ),
    "current11_dataset_partial_supervision_task_coverage.csv": (
        "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7"
    ),
}
_DESIGN_RELATIVE = (
    "review-scratch/current11-task2-batch-descriptor-compiler-contract-design-v1/"
    "batch_descriptor_compiler_contract_design_report.md"
)
_DESIGN_BYTES = 37665
_DESIGN_LF = 400
_DESIGN_SHA256 = "72259f5293a40378ceef0da439c9cbbe0a50dd515831bf2c07b498e538f5a15f"

_RUNTIME_SOURCES = {
    "dataset.py": (
        2693,
        70,
        "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99",
        "5cd1531e9beeca2f53c17b705949676bf457a967",
    ),
    "lightning_modules.py": (
        50939,
        1250,
        "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
        "d19f18ec2841a9a3163d099f4df451d97ce795d4",
    ),
    "utils.py": (
        7171,
        234,
        "2d8fdc954f025e70717b992a1382d8a020eff9170af8e92c961e74759287793b",
        "75450035d1dcd28590d487b3c5c0eaff79fced8a",
    ),
    "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py": (
        50616,
        1120,
        "11f3cc471427b1d2b56d36e8bca43448136ef0256ebde76e2f78058edf0f029b",
        "47c68bdaa53ed5cc1e18808457b54796b668b862",
    ),
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1.py": (
        37785,
        1025,
        "5d189c0451a1aad515932bd4e537de9378b79fcbc2987f671d069e0db857aada",
        "45f44f54fad81c9fc45326bdc442a09cffb9d36a",
    ),
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_formal_materializer_v2.py": (
        41812,
        1178,
        "a0feaf4686d3eedda0b7e807a0471efa2aa5b6e952a3514e51170c62fe22e047",
        "5a8d9323f324cab106141637b186f57bc57c4f21",
    ),
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": (
        64861,
        1570,
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241",
        "61c057af51fcb0bc9dd4ab83f917e1eece2be799",
    ),
}
_RUNTIME_SYMBOLS = {
    "dataset.py": (
        "ProcessedLigandPocketDataset.__init__",
        "ProcessedLigandPocketDataset.__getitem__",
        "ProcessedLigandPocketDataset.collate_fn",
    ),
    "lightning_modules.py": (
        "LigandPocketDDPM.setup",
        "LigandPocketDDPM.train_dataloader",
        "LigandPocketDDPM.val_dataloader",
        "LigandPocketDDPM.test_dataloader",
        "LigandPocketDDPM.get_ligand_and_pocket",
        "LigandPocketDDPM.forward",
    ),
    "utils.py": ("AppendVirtualNodes.__init__", "AppendVirtualNodes.__call__"),
    "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py": (
        "evaluate_covapie_target_residue_atom_condition_adapter_gate_v1",
    ),
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1.py": (
        "materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1",
        "_readiness",
    ),
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_formal_materializer_v2.py": (
        "materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2",
        "_readiness",
    ),
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": (
        "classify_type_symbol_v1",
        "project_type_symbols_to_checkpoint_heavy_v1",
    ),
}
_RUNTIME_ANCHORS = {
    "dataset.py": (
        "if k == 'names' or k == 'receptors':",
        "self.data[k] = v",
        "data = {key: val[idx] for key, val in self.data.items()}",
        "out[prop] = [x[prop] for x in batch]",
        "torch.tensor([len(x) for x in self.data['lig_mask']])",
        "torch.tensor([len(x) for x in self.data['pocket_mask']])",
        "i * torch.ones(len(x[prop]))",
        "torch.cat([x[prop] for x in batch], dim=0)",
        "self.data['lig_coords'][i] = self.data['lig_coords'][i] - mean",
        "self.data['pocket_coords'][i] = self.data['pocket_coords'][i] - mean",
    ),
    "lightning_modules.py": (
        "transform=self.data_transform",
        "shuffle=True",
        "shuffle=False",
        "virtual_nodes=False",
        "if virtual_nodes:",
        "utils.AppendVirtualNodes(",
        "'size': data['num_lig_atoms']",
        "'mask': data['lig_mask']",
        "'size': data['num_pocket_nodes']",
        "'mask': data['pocket_mask']",
    ),
    "utils.py": (
        "n_virt = self.max_ligand_size - data['num_lig_atoms']",
        "torch.cat((data['lig_coords'], virt_coords))",
        "data['num_lig_atoms'] = self.max_ligand_size",
        "torch.cat((data['lig_mask'], virt_mask))",
        "data['num_virtual_atoms'] = n_virt",
    ),
    "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py": (
        "with tempfile.TemporaryDirectory(",
        "temporary_path = temporary_directory / \"current11_runtime_gate.npz\"",
        "names=np.asarray(_EXPECTED_SAMPLES)",
        "receptors=np.asarray(receptors)",
        "tuple(str(value) for value in collated[\"names\"])",
        "temporary_npz_cleaned = True",
        "\"persistent_npz_created\": False",
    ),
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1.py": (
        '"formal_sidecar_materialized": True',
        '"runtime_consumer_available": False',
        '"tensor_materialized": False',
        '"ready_for_tensor_materialization": False',
        '"ready_for_dataloader_integration": False',
    ),
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_formal_materializer_v2.py": (
        '"formal_sidecar_materialized": True',
        '"runtime_consumer_available": False',
        '"tensor_materialized": False',
        '"ready_for_tensor_materialization": False',
        '"ready_for_dataloader_integration": False',
    ),
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": (
        'if type_symbol == "H"',
        'return "explicit_hydrogen"',
        'return "unsupported_nonhydrogen"',
        'if symbol_class in {"unsupported_nonhydrogen", "missing_or_invalid"}',
        "source_to_projected.append(next_index)",
        "source_to_projected.append(None)",
        "next_index += 1",
    ),
}

_EXPECTED_POCKET_RETAINED = (66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228)
_EXPECTED_LIGAND_RETAINED = (13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21)
_EXPECTED_POCKET_H = (55, 92, 82, 57, 43, 0, 0, 0, 0, 0, 0)
_EXPECTED_LIGAND_H = (0, 5, 0, 8, 3, 0, 0, 0, 0, 0, 0)
_EXPECTED_SAMPLE_IDS = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
_ATOM_IDENTITY_FIELDS = (
    "atom_site_id",
    "atom_name",
    "type_symbol",
    "residue_name_or_ligand_comp_id",
    "auth_asym_id",
    "auth_seq_id",
    "label_asym_id",
    "label_seq_id",
)
_LEGAL_ELEMENT_TOKEN = re.compile(r"^[A-Z][a-z]?$")

_STATUS_ROWS = (
    ("CARRIER_BOUND_EXACT", "carrier", True, False, True, "A formal carrier is bound exactly to this contract."),
    ("MATERIALIZED_CARRIER_MISSING", "carrier", False, True, True, "The current formal runtime carrier is not materialized."),
    ("CARRIER_MANIFEST_SCHEMA_MISMATCH", "manifest", False, True, True, "The carrier manifest schema is not exact."),
    ("SAMPLE_KEY_SCHEMA_MISMATCH", "sample_key", False, True, True, "The names sample-key schema is not exact."),
    ("SAMPLE_KEY_INVALID", "sample_key", False, True, True, "A names value is empty, untrimmed, or non-string."),
    ("SAMPLE_KEY_DUPLICATED", "sample_key", False, True, True, "A names value is duplicated."),
    ("SAMPLE_KEY_UNKNOWN", "sample_key", False, True, True, "A names value is not in the exact registry."),
    ("SAMPLE_KEY_AMBIGUOUS", "sample_key", False, True, True, "A names value does not resolve exact-one."),
    ("ROLE_ORDER_SCHEMA_MISMATCH", "role_order", False, True, True, "The role-order projection schema is not exact."),
    ("ROLE_TABLE_AUTHORITY_MISMATCH", "role_order", False, True, True, "A role source table path, hash, count, or row order differs."),
    ("ROLE_LENGTH_MISMATCH", "role_order", False, True, True, "A runtime role length differs from retained-heavy count."),
    ("SOURCE_TO_PROJECTED_MAPPING_MISMATCH", "role_order", False, True, True, "A full source-to-projected mapping differs."),
    ("VIRTUAL_NODE_POLICY_MISMATCH", "runtime_schema", False, True, True, "Padding, virtual nodes, crop, or atom reorder is present."),
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _blob(payload: bytes) -> str:
    framed = b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    return hashlib.sha1(framed).hexdigest()


def _json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    return (text + "\n").encode("utf-8")


def _compact_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            parse_constant=lambda _value: _fail(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
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


def _safe_relative(relative: str) -> PurePosixPath:
    if type(relative) is not str:
        _fail()
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or str(path) != relative:
        _fail()
    return path


def _read_regular(
    root: Path,
    relative: str,
    expected_sha256: str | None = None,
) -> bytes:
    rel = _safe_relative(relative)
    path = root.joinpath(*rel.parts)
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
        payload = path.read_bytes()
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if (
        not resolved.is_relative_to(root)
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or (expected_sha256 is not None and _sha(payload) != expected_sha256)
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
        None if payload is None else _sha(payload),
    )


def _formal_snapshot(canonical: Path) -> dict[str, object]:
    try:
        parent = canonical.parent
        link = os.readlink(canonical)
        object_path = parent / link
        inventory = tuple(sorted(os.listdir(object_path)))
        return {
            "parent": _path_snapshot(parent),
            "parent_inventory": tuple(sorted(os.listdir(parent))),
            "canonical": _path_snapshot(canonical),
            "readlink": link,
            "object": _path_snapshot(object_path),
            "object_inventory": inventory,
            "leaves": {
                name: _path_snapshot(object_path / name) for name in inventory
            },
        }
    except OSError as error:
        raise ValueError(_ERROR) from error


def _validate_formal(canonical: Path) -> dict[str, object]:
    snapshot = _formal_snapshot(canonical)
    if snapshot.get("readlink") != _FORMAL_READLINK:
        _fail()
    if tuple(snapshot.get("object_inventory", ())) != tuple(sorted(_FORMAL_EXACT4)):
        _fail()
    object_path = canonical.parent / _FORMAL_READLINK
    for name, expected in _FORMAL_EXACT4.items():
        payload = _read_regular(object_path, name, expected)
        if not payload or stat.S_IMODE((object_path / name).lstat().st_mode) != 0o644:
            _fail()
    return snapshot


@contextmanager
def _predecessor_status_compatibility() -> Iterator[None]:
    git_owner = _adapter._projection_contract_gate
    original = git_owner._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            lines = output.splitlines()
            if any(
                len(line) >= 4
                and line[3:] in _REPOSITORY_EXACT4
                and line not in allowed
                for line in lines
            ):
                _fail()
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        git_owner._run_git = compatible
        yield
    finally:
        git_owner._run_git = original


def _validate_fixed_source(
    repo: Path,
    relative: str,
    size: int,
    lines: int,
    digest: str,
    blob: str,
) -> bytes:
    payload = _read_regular(repo, relative, digest)
    if len(payload) != size or payload.count(b"\n") != lines or _blob(payload) != blob:
        _fail()
    return payload


def _adapter_output_digest(payload: bytes) -> str:
    name = _ADAPTER_OUTPUT_NAME.encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_ADAPTER_OUTPUT_DOMAIN_TAG)
    digest.update(len(name).to_bytes(8, "big", signed=False))
    digest.update(name)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _validate_adapter_exact2(
    exact2: object,
) -> tuple[dict[str, object], dict[str, object]]:
    if type(exact2) is not dict or tuple(exact2) != _ADAPTER_ARTIFACT_NAMES:
        _fail()
    output_payload = exact2[_ADAPTER_OUTPUT_NAME]
    report_payload = exact2[_ADAPTER_REPORT_NAME]
    if (
        type(output_payload) is not bytes
        or len(output_payload) != _ADAPTER_OUTPUT_BYTES
        or output_payload.count(b"\n") != _ADAPTER_OUTPUT_LF
        or _sha(output_payload) != _ADAPTER_OUTPUT_SHA256
        or type(report_payload) is not bytes
        or len(report_payload) != _ADAPTER_REPORT_BYTES
        or report_payload.count(b"\n") != _ADAPTER_REPORT_LF
        or _sha(report_payload) != _ADAPTER_REPORT_SHA256
    ):
        _fail()
    output = _strict_json(output_payload)
    report = _strict_json(report_payload)
    digest = _adapter_output_digest(output_payload)
    if (
        output.get("remap_status") != "REMAPPED_EXACT"
        or output.get("failure_reason") != "NONE"
        or report.get("adapter_status")
        != "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY"
        or report.get("remap_status") != "REMAPPED_EXACT"
        or report.get("failure_reason") != "NONE"
        or report.get("remap_output_digest") != _ADAPTER_OUTPUT_DIGEST
        or report.get("remap_output_digest") != digest
        or report.get("remap_contract_digest") != _REMAP_DIGEST
        or report.get("artifact_file_count") != 2
        or report.get("artifact_identities")
        != [
            {
                "artifact_index": 0,
                "artifact_name": _ADAPTER_OUTPUT_NAME,
                "stable_digest_participation": True,
                "bytes": _ADAPTER_OUTPUT_BYTES,
                "LF": _ADAPTER_OUTPUT_LF,
                "SHA256": _ADAPTER_OUTPUT_SHA256,
            },
            {
                "artifact_index": 1,
                "artifact_name": _ADAPTER_REPORT_NAME,
                "stable_digest_participation": False,
                "content_identity": "self_excluded",
            },
        ]
    ):
        _fail()
    return output, report


def _predecessors(
    repo: Path,
    state: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    _validate_fixed_source(
        repo,
        _ADAPTER_RELATIVE,
        _ADAPTER_BYTES,
        _ADAPTER_LF,
        _ADAPTER_SHA256,
        _ADAPTER_BLOB,
    )
    _validate_fixed_source(
        repo,
        _REMAP_RELATIVE,
        _REMAP_BYTES,
        _REMAP_LF,
        _REMAP_SHA256,
        _REMAP_BLOB,
    )
    _validate_fixed_source(
        repo,
        _ADAPTER_CHECKER_RELATIVE,
        _ADAPTER_CHECKER_BYTES,
        _ADAPTER_CHECKER_LF,
        _ADAPTER_CHECKER_SHA256,
        _ADAPTER_CHECKER_BLOB,
    )
    try:
        with _predecessor_status_compatibility():
            contract_first = _remap_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1(
                repo_root=repo,
                state_root=state,
            )
            if type(contract_first) is not dict:
                _fail()
            contract_report = _strict_json(
                contract_first["current11_task2_batch_index_remap_contract_gate_report.json"]
            )
            vectors = _strict_json(
                contract_first["current11_task2_batch_index_remap_reference_vectors.json"]
            )
            if (
                contract_report.get("gate_status") != "PASS_CONTRACT_ONLY"
                or contract_report.get("contract_digest") != _REMAP_DIGEST
                or vectors.get("schema_version")
                != "covapie_current11_task2_batch_index_remap_reference_vectors_v1"
            ):
                _fail()
            contract = _adapter._parse_contract(contract_first)
            source = contract["source"]
            canonical = contract["vectors"]["canonical_exact11_batch_reference"]
            batch_contract = canonical["batch_contract"]
            batch_order = canonical["output"]["batch_sample_order"]
            authority_by_key = {
                _adapter._identity_key(table["sample_identity"]): table
                for table in contract["authority"]
            }
            tables = [
                copy.deepcopy(authority_by_key[_adapter._identity_key(sample)])
                for sample in batch_order
            ]
            lengths = copy.deepcopy(batch_contract["batch_role_lengths"])
            offsets = copy.deepcopy(batch_contract["batch_role_offsets"])
            masks = {
                role: [
                    ordinal
                    for ordinal, length in enumerate(lengths[role])
                    for _ in range(length)
                ]
                for role in ("pocket", "ligand")
            }
            adapter_input = {
                "schema_version": _adapter._INPUT_SCHEMA,
                "source_projection_digest": _PROJECTION_DIGEST,
                "source_payload_digest": _PAYLOAD_DIGEST,
                "parser_schema_version": _ROLE_ORDER_SCHEMA,
                "collate_schema_version": _adapter._COLLATE_SCHEMA,
                "source_sample_order": copy.deepcopy(source["sample_order"]),
                "source_pair_values_int64": copy.deepcopy(
                    source["pair_values_source_row_indices"]
                ),
                "source_sample_offsets_int64": copy.deepcopy(source["sample_pair_offsets"]),
                "source_entry_validity_bool": copy.deepcopy(source["entry_validity"]),
                "source_sample_validity_bool": copy.deepcopy(source["sample_validity"]),
                "batch_sample_order": copy.deepcopy(batch_order),
                "batch_sample_atom_identity_tables": tables,
                "batch_role_lengths": lengths,
                "batch_role_offsets": offsets,
                "batch_membership_masks": masks,
                "joint_layout_descriptor": batch_contract["joint_layout_descriptor"],
                "debug_coordinates": None,
                "debug_rank_metadata": None,
            }
            adapter_exact2 = (
                _adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
                    repo_root=repo,
                    state_root=state,
                    adapter_input=copy.deepcopy(adapter_input),
                )
            )
    except BaseException as error:
        raise ValueError(_ERROR) from error
    adapter_output, public_report = _validate_adapter_exact2(adapter_exact2)
    adapter_reference = {
        "adapter_status": public_report["adapter_status"],
        "remap_output_digest": public_report["remap_output_digest"],
        "remap_contract_digest": _REMAP_DIGEST,
        "public_adapter_api_called": True,
        "adapter_exact2_identity_verified": True,
        "adapter_canonical_remap_status": adapter_output["remap_status"],
        "adapter_canonical_failure_reason": adapter_output["failure_reason"],
    }
    return vectors, adapter_output, adapter_reference


def _ast_symbols(payload: bytes) -> set[str]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found.add(f"{node.name}.{child.name}")
    return found


def _literal_assignment(payload: bytes, name: str) -> object:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, TypeError) as error:
                raise ValueError(_ERROR) from error
    _fail()


def _runtime_inventory(repo: Path) -> tuple[list[dict[str, object]], tuple[str, ...]]:
    result: list[dict[str, object]] = []
    checkpoint_vocabulary: tuple[str, ...] | None = None
    for relative, identity in _RUNTIME_SOURCES.items():
        payload = _validate_fixed_source(repo, relative, *identity)
        symbols = _RUNTIME_SYMBOLS[relative]
        anchors = _RUNTIME_ANCHORS[relative]
        if not set(symbols).issubset(_ast_symbols(payload)):
            _fail()
        text = payload.decode("utf-8")
        if any(anchor not in text for anchor in anchors):
            _fail()
        if relative.endswith("unknown_atom_policy_resolution_v1.py"):
            vocabulary = _literal_assignment(payload, "CHECKPOINT_VOCABULARY")
            if (
                type(vocabulary) is not tuple
                or any(type(row) is not tuple or len(row) != 3 for row in vocabulary)
            ):
                _fail()
            checkpoint_vocabulary = tuple(row[0] for row in vocabulary)
            if checkpoint_vocabulary != ("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"):
                _fail()
            policies = {
                key: _literal_assignment(payload, key)
                for key in (
                    "EXPLICIT_HYDROGEN_POLICY",
                    "UNSUPPORTED_NONHYDROGEN_POLICY",
                )
            }
            if policies != {
                "EXPLICIT_HYDROGEN_POLICY": "exclude_before_checkpoint_model_projection",
                "UNSUPPORTED_NONHYDROGEN_POLICY": "reject_sample_fail_closed",
            }:
                _fail()
        result.append(
            {
                "relative_path": relative,
                "bytes": identity[0],
                "LF": identity[1],
                "SHA256": identity[2],
                "Git_blob": identity[3],
                "validated_symbols": list(symbols),
                "semantic_anchors": list(anchors),
            }
        )
    if checkpoint_vocabulary is None:
        _fail()
    return result, checkpoint_vocabulary


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            _fail()
        rows = [dict(row) for row in reader]
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(_ERROR) from error
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        _fail()
    return rows


def _classify(type_symbol: object, supported: frozenset[str]) -> str:
    if type(type_symbol) is not str or not type_symbol or type_symbol.strip() != type_symbol:
        return "missing_or_invalid"
    if type_symbol == "H":
        return "explicit_hydrogen"
    if type_symbol in supported:
        return "supported_checkpoint_heavy_atom"
    if _LEGAL_ELEMENT_TOKEN.fullmatch(type_symbol) is None:
        return "missing_or_invalid"
    return "unsupported_nonhydrogen"


def _atom_identity(row: Mapping[str, str], role: str) -> dict[str, str]:
    residue = row.get("residue_name", "") if role == "pocket" else row.get("ligand_comp_id", "")
    identity = {
        "atom_site_id": row.get("atom_site_id", ""),
        "atom_name": row.get("atom_name", ""),
        "type_symbol": row.get("type_symbol", ""),
        "residue_name_or_ligand_comp_id": residue,
        "auth_asym_id": row.get("auth_asym_id", ""),
        "auth_seq_id": row.get("auth_seq_id", ""),
        "label_asym_id": row.get("label_asym_id", ""),
        "label_seq_id": row.get("label_seq_id", ""),
    }
    if tuple(identity) != _ATOM_IDENTITY_FIELDS or any(type(value) is not str for value in identity.values()):
        _fail()
    return identity


def _sample_and_role_records(
    repo: Path,
    vectors: dict[str, object],
    adapter_output: dict[str, object],
    supported_tokens: tuple[str, ...],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source = vectors.get("source_contract")
    provenance = vectors.get("exact22_source_to_local")
    if type(source) is not dict or type(provenance) is not list or len(provenance) != 11:
        _fail()
    sample_order = source.get("sample_order")
    adapter_order = adapter_output.get("batch_sample_order")
    if type(sample_order) is not list or len(sample_order) != 11 or sample_order != adapter_order:
        _fail()
    sample_records: list[dict[str, object]] = []
    normalized_samples: list[dict[str, object]] = []
    for index, sample in enumerate(sample_order):
        if type(sample) is not dict:
            _fail()
        normalized = {
            "sample_index_0based": index,
            "sample_index_row_id": sample.get("sample_index_row_id"),
            "sample_preparation_input_id": sample.get("sample_preparation_input_id"),
            "pdb_id": sample.get("pdb_id"),
            "ligand_comp_id": sample.get("ligand_comp_id"),
        }
        if (
            normalized["sample_index_row_id"] != _EXPECTED_SAMPLE_IDS[index]
            or any(
                type(normalized[field]) is not str
                or not normalized[field]
                or normalized[field].strip() != normalized[field]
                for field in normalized
                if field != "sample_index_0based"
            )
        ):
            _fail()
        normalized_samples.append(normalized)
    if len({sample["sample_index_row_id"] for sample in normalized_samples}) != 11:
        _fail()
    supported = frozenset(supported_tokens)
    by_role: dict[str, list[dict[str, object]]] = {"pocket": [], "ligand": []}
    for index, (sample, provenance_row) in enumerate(zip(normalized_samples, provenance)):
        if (
            type(provenance_row) is not dict
            or provenance_row.get("source_sample_index") != index
            or type(provenance_row.get("roles")) is not list
        ):
            _fail()
        roles = {row.get("role"): row for row in provenance_row["roles"] if type(row) is dict}
        if set(roles) != {"pocket", "ligand"}:
            _fail()
        for role in ("pocket", "ligand"):
            source_role = roles[role]
            relative = source_role.get("relative_path")
            digest = source_role.get("SHA256")
            row_count = source_role.get("row_count")
            selected_source = source_role.get("selected_source_row_index_0based")
            selected_local = source_role.get("selected_parser_local_index")
            if (
                source_role.get("root_kind") != "repo_root"
                or type(relative) is not str
                or type(digest) is not str
                or type(row_count) is not int
                or type(selected_source) is not int
                or type(selected_local) is not int
            ):
                _fail()
            table = _csv_rows(_read_regular(repo, relative, digest))
            if len(table) != row_count or not 0 <= selected_source < row_count:
                _fail()
            classes = [_classify(row.get("type_symbol"), supported) for row in table]
            unsupported = sum(
                value in {"unsupported_nonhydrogen", "missing_or_invalid"}
                for value in classes
            )
            explicit_h = classes.count("explicit_hydrogen")
            projected_rows = [
                source_index
                for source_index, value in enumerate(classes)
                if value == "supported_checkpoint_heavy_atom"
            ]
            source_to_projected: list[int | None] = []
            next_index = 0
            for value in classes:
                if value == "supported_checkpoint_heavy_atom":
                    source_to_projected.append(next_index)
                    next_index += 1
                else:
                    source_to_projected.append(None)
            identities = [_atom_identity(table[source_index], role) for source_index in projected_rows]
            if (
                unsupported != 0
                or source_to_projected[selected_source] != selected_local
                or len(projected_rows) != source_role.get("retained_heavy_count")
                or explicit_h != source_role.get("explicit_hydrogen_count")
                or any(left >= right for left, right in zip(projected_rows, projected_rows[1:]))
                or [value for value in source_to_projected if value is not None]
                != list(range(len(projected_rows)))
                or any(
                    source_to_projected[row_index] is not None
                    for row_index, value in enumerate(classes)
                    if value == "explicit_hydrogen"
                )
            ):
                _fail()
            record: dict[str, object] = {
                "sample_index_0based": index,
                "sample_index_row_id": sample["sample_index_row_id"],
                "role": role,
                "source_table_root_kind": "repo_root",
                "source_table_relative_path": relative,
                "source_table_sha256": digest,
                "source_row_count": row_count,
                "explicit_hydrogen_count": explicit_h,
                "unsupported_nonhydrogen_count": unsupported,
                "retained_heavy_count": len(projected_rows),
                "projected_source_row_indices_int64": projected_rows,
                "source_to_projected_index_nullable_int64": source_to_projected,
                "projected_atom_identity_sequence_sha256": _sha(_compact_json(identities)),
                "selected_task2_source_row_index_0based": selected_source,
                "selected_task2_parser_local_index_0based": selected_local,
                "projection_schema_version": _ROLE_ORDER_SCHEMA,
                "runtime_role_order_materialized": False,
            }
            record["role_order_record_sha256"] = _sha(_compact_json(record))
            by_role[role].append(record)
    if (
        tuple(row["retained_heavy_count"] for row in by_role["pocket"])
        != _EXPECTED_POCKET_RETAINED
        or tuple(row["retained_heavy_count"] for row in by_role["ligand"])
        != _EXPECTED_LIGAND_RETAINED
        or tuple(row["explicit_hydrogen_count"] for row in by_role["pocket"])
        != _EXPECTED_POCKET_H
        or tuple(row["explicit_hydrogen_count"] for row in by_role["ligand"])
        != _EXPECTED_LIGAND_H
    ):
        _fail()
    sample_records = [*by_role["pocket"], *by_role["ligand"]]
    return normalized_samples, sample_records


def _sample_registry_csv(samples: list[dict[str, object]]) -> bytes:
    fields = (
        "sample_index_0based",
        "sample_index_row_id",
        "sample_preparation_input_id",
        "pdb_id",
        "ligand_comp_id",
        "expected_name",
        "expected_receptor",
        "sample_key_schema_version",
        "sample_key_exact_one",
        "runtime_carrier_materialized",
    )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for sample in samples:
        writer.writerow(
            {
                **sample,
                "expected_name": sample["sample_index_row_id"],
                "expected_receptor": sample["pdb_id"],
                "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
                "sample_key_exact_one": "true",
                "runtime_carrier_materialized": "false",
            }
        )
    return buffer.getvalue().encode("utf-8")


def _readiness() -> dict[str, bool]:
    return {
        "runtime_sample_and_role_order_carrier_contract_gate_implemented": True,
        "runtime_sample_and_role_order_carrier_contract_gate_passed": True,
        "runtime_sample_and_role_order_carrier_contract_designed": True,
        "sample_key_registry_built_in_memory": True,
        "role_order_registry_built_in_memory": True,
        "full_role_order_bound_to_source_tables": True,
        "temporary_reference_feasibility_passed": True,
        "formal_runtime_carrier_materialized": False,
        "runtime_batch_sample_key_available": False,
        "runtime_batch_sample_key_exact_one_for_current11": False,
        "runtime_batch_role_order_binding_available": False,
        "current11_atom_identity_provider_available": True,
        "general_non_source_identity_provider_available": False,
        "ready_for_runtime_sample_and_role_order_carrier_materializer_implementation": True,
        "ready_for_batch_descriptor_compiler_contract_gate_implementation": False,
        "ready_for_task2_batch_descriptor_compiler_implementation": False,
        "ready_for_runtime_batch_observation_extractor_design": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _fail_closed_invariants() -> list[str]:
    return [
        "names is the sole sample identity carrier",
        "each names value exactly equals sample_index_row_id",
        "receptors does not participate in identity",
        "names values are unique",
        "fuzzy case path basename prefix and normalization transforms are forbidden",
        "sample key is exact-one against the Current11 registry",
        "batch ordinal is not sample identity",
        "coordinates features counts distances and filesystem metadata are not sample identity",
        "ligand and pocket are independent role spaces",
        "ligand and pocket roles cannot be exchanged",
        "role order is the source-order-preserving checkpoint-heavy projection",
        "explicit hydrogen maps to null and never to a minus-one sentinel",
        "unsupported nonhydrogen or invalid type symbol rejects the full sample",
        "retained projected local indices are contiguous zero through N minus one",
        "full role order is bound and a selected endpoint alone is insufficient",
        "source table relative path SHA256 row count and physical row order are bound",
        "the full projected Exact8 atom identity sequence is digest-bound",
        "runtime role length equals retained-heavy count",
        "runtime padding is forbidden",
        "runtime crop is forbidden",
        "runtime atom reorder is forbidden",
        "runtime virtual nodes are forbidden",
        "the temporary NPZ probe is feasibility evidence and not formal authority",
        "this contract gate does not materialize a carrier",
        "this contract does not authorize compiler model loss or training",
        "shuffle changes only batch order and never per-sample identity or role order",
        "a runtime batch may contain an exact registry subset in its actual order",
        "a materialized runtime artifact must bind its actual byte SHA256",
        "callers cannot override schema status registry path or digest authority",
        "formal carrier absence keeps all runtime carrier availability values false",
    ]


def _runtime_source_semantics() -> dict[str, object]:
    return {
        "dataset_transport": {
            "names_and_receptors_preserved_without_conversion": True,
            "getitem_uses_exact_requested_index": True,
            "collate_preserves_actual_batch_order": True,
            "sizes_derive_from_split_lengths": True,
            "role_masks_are_actual_batch_ordinals": True,
            "centering_changes_coordinates_only_not_count_or_order": True,
        },
        "lightning_transport": {
            "train_shuffle": True,
            "validation_shuffle": False,
            "test_shuffle": False,
            "transform_boundary_optional": True,
            "checked_default_virtual_nodes": False,
            "model_boundary_uses_role_sizes_and_masks": True,
        },
        "append_virtual_nodes": {
            "appends_to_ligand_tail": True,
            "changes_num_lig_atoms": True,
            "extends_lig_mask": True,
            "adds_num_virtual_atoms": True,
            "allowed_by_v1": False,
        },
        "materializer_readiness": {
            "v1_formal_sidecar_materialized": True,
            "v2_formal_sidecar_materialized": True,
            "runtime_consumer_available": False,
            "tensor_materialized": False,
            "ready_for_tensor_materialization": False,
            "ready_for_dataloader_integration": False,
        },
    }


def _role_registry(
    samples: list[dict[str, object]],
    records: list[dict[str, object]],
) -> dict[str, object]:
    pocket = records[:11]
    ligand = records[11:]
    aggregate = {
        "sample_count": 11,
        "role_record_count": 22,
        "total_source_rows_pocket": sum(row["source_row_count"] for row in pocket),
        "total_source_rows_ligand": sum(row["source_row_count"] for row in ligand),
        "total_retained_pocket": sum(row["retained_heavy_count"] for row in pocket),
        "total_retained_ligand": sum(row["retained_heavy_count"] for row in ligand),
        "total_explicit_h_pocket": sum(row["explicit_hydrogen_count"] for row in pocket),
        "total_explicit_h_ligand": sum(row["explicit_hydrogen_count"] for row in ligand),
        "unsupported_nonhydrogen_count": sum(
            row["unsupported_nonhydrogen_count"] for row in records
        ),
    }
    return {
        "schema_version": _ROLE_REGISTRY_SCHEMA,
        "sample_order": samples,
        "role_order": ["pocket", "ligand"],
        "role_order_records": records,
        "aggregate_counts": aggregate,
        "projection_policy": {
            "schema_version": _ROLE_ORDER_SCHEMA,
            "supported_checkpoint_tokens_in_channel_order": [
                "C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"
            ],
            "explicit_hydrogen_policy": "exclude_before_checkpoint_model_projection",
            "unsupported_nonhydrogen_policy": "reject_sample_fail_closed",
            "surviving_row_order": "strict physical CSV data-row order",
            "projected_local_indices": "contiguous 0-based",
        },
        "identity_sequence_framing": {
            "fields_in_semantic_order": list(_ATOM_IDENTITY_FIELDS),
            "container": "JSON array of Exact8 objects in projected order",
            "object_key_serialization": "sort_keys=true",
            "separators": [",", ":"],
            "ensure_ascii": True,
            "allow_nan": False,
            "terminal_lf": False,
            "digest": "SHA256 of exact UTF-8 canonical JSON bytes",
        },
        "readiness": _readiness(),
    }


def _carrier_schema(samples: list[dict[str, object]]) -> dict[str, object]:
    order = [sample["sample_index_row_id"] for sample in samples]
    names_digest = _sha(_compact_json(order))
    field_order = [
        "schema_version",
        "source_contract_digest",
        "sample_key_registry_digest",
        "role_order_registry_digest",
        "runtime_artifact_kind",
        "runtime_artifact_relative_path",
        "runtime_artifact_sha256",
        "runtime_batch_schema_version",
        "sample_key_schema_version",
        "role_order_schema_version",
        "virtual_node_policy",
        "sample_order",
        "names_binding",
        "receptors_binding",
        "ligand_buffer_binding",
        "pocket_buffer_binding",
        "materialization_provenance",
        "readiness",
    ]
    role_binding = {
        "required_fields": [
            "role",
            "projection_schema_version",
            "sample_offsets",
            "sample_lengths",
            "per_sample_role_order_record_digests",
            "flat_projected_source_row_order_digest",
            "flat_atom_identity_sequence_digest",
            "padding_present",
            "virtual_nodes_present",
            "atom_reorder_present",
        ],
        "sample_offsets": "int64[S+1] exact exclusive prefix sum",
        "sample_lengths": "int64[S] exact retained-heavy counts",
        "padding_present_required_value": False,
        "virtual_nodes_present_required_value": False,
        "atom_reorder_present_required_value": False,
    }
    return {
        "schema_version": _CARRIER_SCHEMA,
        "artifact_kind": "manifest_schema_not_manifest_instance",
        "top_level_field_order": field_order,
        "top_level_fields": {
            "schema_version": {"exact_value": _CARRIER_SCHEMA},
            "source_contract_digest": {"required": True, "format": "lowercase_sha256"},
            "sample_key_registry_digest": {"required": True, "format": "lowercase_sha256"},
            "role_order_registry_digest": {"required": True, "format": "lowercase_sha256"},
            "runtime_artifact_kind": {"exact_value": _RUNTIME_KIND},
            "runtime_artifact_relative_path": {
                "required_in_instance": True,
                "safe_state_root_relative": True,
                "repository_committed_npz_forbidden": True,
                "actual_value_in_schema": None,
            },
            "runtime_artifact_sha256": {
                "required_in_instance": True,
                "format": "lowercase_sha256_of_actual_runtime_artifact_bytes",
                "actual_value_in_schema": None,
            },
            "runtime_batch_schema_version": {"exact_value": _RUNTIME_BATCH_SCHEMA},
            "sample_key_schema_version": {"exact_value": _SAMPLE_KEY_SCHEMA},
            "role_order_schema_version": {"exact_value": _ROLE_ORDER_SCHEMA},
            "virtual_node_policy": {"exact_value": _VIRTUAL_POLICY},
            "sample_order": {"exact_value": order},
            "names_binding": {
                "field_name": "names",
                "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
                "sample_order": order,
                "array_dtype_family": "unicode_string",
                "array_rank": 1,
                "array_length": 11,
                "array_values_digest": names_digest,
                "array_values_digest_framing": "canonical compact JSON exact string array",
                "exact_values_required": True,
            },
            "receptors_binding": {
                "field_name": "receptors",
                "identity_authority": False,
                "consistency_only": True,
                "recommended_exact_values": [sample["pdb_id"] for sample in samples],
            },
            "ligand_buffer_binding": {"role": "ligand", **role_binding},
            "pocket_buffer_binding": {"role": "pocket", **role_binding},
            "materialization_provenance": {
                "required": True,
                "must_bind_actual_artifact_bytes": True,
                "must_not_claim_temporary_probe_as_formal": True,
            },
            "readiness": {
                "required_fields": [
                    "formal_runtime_carrier_materialized",
                    "runtime_batch_sample_key_available",
                    "runtime_batch_role_order_binding_available",
                    "ready_for_batch_descriptor_compiler_contract_gate_implementation",
                ],
                "formal_instance_success_requires_all_true": True,
            },
        },
        "runtime_schema_contract": {
            "padding_present": False,
            "crop_present": False,
            "atom_reorder_present": False,
            "virtual_nodes_present": False,
            "ligand_and_pocket_role_spaces_independent": True,
        },
        "schema_is_instance": False,
    }


def _status_csv() -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(
        (
            "status_code",
            "status",
            "scope",
            "is_success",
            "is_hard_failure",
            "formal_materialization_required",
            "description",
        )
    )
    for code, row in enumerate(_STATUS_ROWS):
        writer.writerow(
            (
                code,
                row[0],
                row[1],
                str(row[2]).lower(),
                str(row[3]).lower(),
                str(row[4]).lower(),
                row[5],
            )
        )
    return buffer.getvalue().encode("utf-8")


def _manifest(
    runtime_sources: list[dict[str, object]],
    samples: list[dict[str, object]],
    records: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA,
        "source_lineage": {
            "public_task2_remap_adapter_v1": {
                "relative_path": _ADAPTER_RELATIVE,
                "bytes": _ADAPTER_BYTES,
                "LF": _ADAPTER_LF,
                "SHA256": _ADAPTER_SHA256,
                "Git_blob": _ADAPTER_BLOB,
                "commit": _ADAPTER_COMMIT,
                "stable_output_digest": _ADAPTER_OUTPUT_DIGEST,
                "checker_identity": {
                    "relative_path": _ADAPTER_CHECKER_RELATIVE,
                    "bytes": _ADAPTER_CHECKER_BYTES,
                    "LF": _ADAPTER_CHECKER_LF,
                    "SHA256": _ADAPTER_CHECKER_SHA256,
                    "Git_blob": _ADAPTER_CHECKER_BLOB,
                },
                "public_adapter_api_called": True,
                "adapter_exact2_identity_verified": True,
                "canonical_remap_status": "REMAPPED_EXACT",
                "canonical_failure_reason": "NONE",
            },
            "task2_remap_contract_gate_v1": {
                "relative_path": _REMAP_RELATIVE,
                "module_identity": {
                    "bytes": _REMAP_BYTES,
                    "LF": _REMAP_LF,
                    "SHA256": _REMAP_SHA256,
                    "Git_blob": _REMAP_BLOB,
                },
                "commit": _REMAP_COMMIT,
                "contract_digest": _REMAP_DIGEST,
            },
            "projection_lineage": {
                "projection_instance_digest": _PROJECTION_DIGEST,
                "payload_bundle_digest": _PAYLOAD_DIGEST,
                "projection_contract_digest": _PROJECTION_CONTRACT_DIGEST,
            },
            "formal_routing_sidecar": {
                "canonical_relative_path": _FORMAL_RELATIVE,
                "readlink": _FORMAL_READLINK,
                "aggregate": _FORMAL_AGGREGATE,
                "snapshot_SHA256": _FORMAL_SNAPSHOT,
                "Exact4_SHA256": _FORMAL_EXACT4,
            },
            "runtime_sources": runtime_sources,
            "source_atom_tables": [
                {
                    "sample_index_row_id": row["sample_index_row_id"],
                    "role": row["role"],
                    "root_kind": row["source_table_root_kind"],
                    "relative_path": row["source_table_relative_path"],
                    "SHA256": row["source_table_sha256"],
                    "row_count": row["source_row_count"],
                }
                for row in records
            ],
            "non_runtime_lineage": {
                "relative_path": _DESIGN_RELATIVE,
                "bytes": _DESIGN_BYTES,
                "LF": _DESIGN_LF,
                "SHA256": _DESIGN_SHA256,
                "runtime_dependency": False,
                "contract_authority": False,
                "read_or_parsed_by_gate": False,
            },
        },
        "contract_scope": {
            "contract_only": True,
            "read_only": True,
            "in_memory_only": True,
            "stdlib_and_local_covalent_ext_only": True,
            "carrier_materializer_implemented": False,
            "compiler_implemented": False,
            "runtime_extractor_implemented": False,
        },
        "sample_key_contract": {
            "schema_version": _SAMPLE_KEY_SCHEMA,
            "field_name": "names",
            "logical_shape": "[S]",
            "value_semantics": "exact UTF-8 sample_index_row_id",
            "current11_expected_values": [sample["sample_index_row_id"] for sample in samples],
            "required_properties": [
                "exact string",
                "nonempty",
                "trimmed",
                "unique",
                "ordered by materialized sample order",
            ],
            "forbidden_transforms": [
                "basename extraction",
                "case folding",
                "prefix stripping",
                "path normalization",
                "fuzzy match",
            ],
            "receptors": {
                "optional_consistency_debug_carrier": True,
                "recommended_current11_value": "exact PDB ID",
                "sample_identity_authority": False,
                "may_replace_names": False,
            },
            "forbidden_identity_inputs": [
                "batch ordinal",
                "coordinates",
                "features",
                "counts",
                "distance",
                "filesystem metadata",
            ],
            "runtime_batch_sample_key_available": False,
            "runtime_batch_sample_key_exact_one_for_current11": False,
        },
        "role_order_contract": {
            "schema_version": _ROLE_ORDER_SCHEMA,
            "roles": ["ligand", "pocket"],
            "role_spaces_independent": True,
            "source_order_preserved": True,
            "full_projected_source_row_vector_required": True,
            "full_source_to_projected_vector_required": True,
            "full_projected_atom_identity_sequence_digest_required": True,
            "selected_task2_endpoint_is_cross_check_only": True,
            "runtime_role_order_materialized": False,
        },
        "runtime_schema_contract": {
            "runtime_batch_schema_version": _RUNTIME_BATCH_SCHEMA,
            "no_padding": True,
            "no_crop": True,
            "no_atom_reorder": True,
            "no_virtual_nodes": True,
            "ligand_and_pocket_independent": True,
        },
        "virtual_node_policy": _VIRTUAL_POLICY,
        "temporary_reference_evidence": {
            "temporary_reference_feasibility_evidence": True,
            "temporary_reference_feasibility_passed": True,
            "unicode_names_shape_11_transport_observed": True,
            "collate_sample_order_preserved": True,
            "names_equal_exact11_row_ids_observed": True,
            "pocket_role_order_and_indicator_preserved": True,
            "temporary_artifact_cleaned": True,
            "formal_runtime_authority": False,
            "persistent_runtime_artifact": False,
        },
        "formal_authority_boundary": {
            "formal_current11_npz_exists": False,
            "formal_runtime_carrier_manifest_exists": False,
            "formal_names_binding_exists": False,
            "formal_ligand_role_order_binding_exists": False,
            "formal_pocket_role_order_binding_exists": False,
            "temporary_probe_is_formal_predecessor": False,
        },
        "runtime_source_semantics": _runtime_source_semantics(),
        "artifact_names": list(_ARTIFACT_NAMES),
        "stable_artifact_names": list(_STABLE_NAMES),
        "fail_closed_invariants": _fail_closed_invariants(),
        "checkpoint_compatibility": {
            "checkpoint_state_dict_change_required": False,
            "base_model_parameter_shape_change_required": False,
            "base_atom_feature_width_change_required": False,
            "egnn_or_se3_backbone_change_required": False,
            "checkpoint_bytes_read": False,
        },
        "auxiliary_module_scope": {
            "authorized": [
                "future runtime sample and role-order carrier materializer",
                "future runtime batch observation extractor design",
            ],
            "not_authorized": [
                "batch descriptor compiler",
                "dataloader integration",
                "model integration",
                "loss integration",
                "training",
            ],
        },
        "readiness": _readiness(),
    }


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(_DOMAIN_TAG)
    for name in _STABLE_NAMES:
        name_bytes = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(name_bytes).to_bytes(8, "big", signed=False))
        digest.update(name_bytes)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _validate_artifact(name: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail()
    if name.endswith(".json") and _json(_strict_json(payload)) != payload:
        _fail()


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    canonical = state / _FORMAL_RELATIVE
    before = _validate_formal(canonical)
    vectors, adapter_output, adapter_report = _predecessors(repo, state)
    runtime_sources, supported_tokens = _runtime_inventory(repo)
    samples, role_records = _sample_and_role_records(
        repo,
        vectors,
        adapter_output,
        supported_tokens,
    )
    role_registry = _role_registry(samples, role_records)
    artifacts: dict[str, bytes] = {
        _MANIFEST: _json(_manifest(runtime_sources, samples, role_records)),
        _SAMPLE_REGISTRY: _sample_registry_csv(samples),
        _ROLE_REGISTRY: _json(role_registry),
        _CARRIER_MANIFEST_SCHEMA: _json(_carrier_schema(samples)),
        _VOCABULARY: _status_csv(),
    }
    digest = _stable_digest(artifacts)
    identities = [
        {
            "artifact_index": index,
            "artifact_name": name,
            "stable_digest_participation": True,
            "bytes": len(artifacts[name]),
            "LF": artifacts[name].count(b"\n"),
            "SHA256": _sha(artifacts[name]),
        }
        for index, name in enumerate(_STABLE_NAMES)
    ]
    identities.append(
        {
            "artifact_index": 5,
            "artifact_name": _REPORT,
            "stable_digest_participation": False,
            "content_identity": "self_excluded",
        }
    )
    report = {
        "schema_version": _REPORT_SCHEMA,
        "gate_status": _STATUS,
        "contract_digest": digest,
        "artifact_file_count": 6,
        "artifact_identities": identities,
        "adapter_predecessor_passed": True,
        "adapter_stable_output_digest": adapter_report["remap_output_digest"],
        "public_adapter_api_called": adapter_report["public_adapter_api_called"],
        "adapter_exact2_identity_verified": adapter_report[
            "adapter_exact2_identity_verified"
        ],
        "adapter_canonical_remap_status": adapter_report[
            "adapter_canonical_remap_status"
        ],
        "adapter_canonical_failure_reason": adapter_report[
            "adapter_canonical_failure_reason"
        ],
        "remap_contract_predecessor_passed": True,
        "remap_contract_digest": _REMAP_DIGEST,
        "projection_instance_digest": _PROJECTION_DIGEST,
        "payload_bundle_digest": _PAYLOAD_DIGEST,
        "projection_contract_digest": _PROJECTION_CONTRACT_DIGEST,
        "formal_sidecar_check_passed": True,
        "formal_snapshot_unchanged": True,
        "runtime_source_identity_count": len(runtime_sources),
        "runtime_semantic_anchor_count": sum(
            len(row["semantic_anchors"]) for row in runtime_sources
        ),
        "sample_key_registry_count": len(samples),
        "role_order_record_count": len(role_records),
        "source_atom_table_count": len(role_records),
        "full_projected_order_recomputed": True,
        "full_atom_identity_sequence_digests_built": True,
        "temporary_reference_feasibility_passed": True,
        "temporary_reference_is_formal_authority": False,
        "sample_key_schema_frozen": True,
        "role_order_schema_frozen": True,
        "carrier_manifest_schema_frozen": True,
        "status_vocabulary_count": len(_STATUS_ROWS),
        "fail_closed_invariant_count": len(_fail_closed_invariants()),
        "role_order_aggregate_counts": role_registry["aggregate_counts"],
        "readiness": _readiness(),
    }
    artifacts[_REPORT] = _json(report)
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES or len(artifacts) != 6:
        _fail()
    for name, payload in artifacts.items():
        _validate_artifact(name, payload)
    after = _validate_formal(canonical)
    if before != after:
        _fail()
    return artifacts


def build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic Current11 carrier contract Exact6 in memory."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
