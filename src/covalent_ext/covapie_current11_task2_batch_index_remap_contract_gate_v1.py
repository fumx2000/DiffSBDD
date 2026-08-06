"""Build the read-only Current11 Task 2 batch-index remap contract gate V1."""

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

from covalent_ext import covapie_current11_tensor_projection_instance_builder_v1 as _instance_builder


__all__ = ("build_covapie_current11_task2_batch_index_remap_contract_gate_v1",)

_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1_ERROR"
_STATUS = "PASS_CONTRACT_ONLY"
_SCHEMA = "covapie_current11_task2_batch_index_remap_contract_v1"
_INPUT_SCHEMA = "covapie_current11_task2_batch_index_remap_adapter_input_v1"
_OUTPUT_SCHEMA = "covapie_current11_task2_batch_index_remap_adapter_output_v1"
_REFERENCE_SCHEMA = "covapie_current11_task2_batch_index_remap_reference_vectors_v1"
_REPORT_SCHEMA = "covapie_current11_task2_batch_index_remap_contract_gate_report_v1"
_JOINT_LAYOUT = "ligand_segment_then_pocket_segment_v1"
_JOIN = "exact_source_table_row_identity_to_order_preserving_parser_node_v1"
_PARSER_SCHEMA = "order_preserving_checkpoint_heavy_projection_v1"
_COLLATE_SCHEMA = "processed_ligand_pocket_dataset_collate_fn_v1"
_DOMAIN_TAG = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1\0"

_INPUT_FIELD_ORDER = (
    "schema_version",
    "source_projection_digest",
    "source_payload_digest",
    "parser_schema_version",
    "collate_schema_version",
    "source_sample_order",
    "source_pair_values_int64",
    "source_sample_offsets_int64",
    "source_entry_validity_bool",
    "source_sample_validity_bool",
    "batch_sample_order",
    "batch_sample_atom_identity_tables",
    "batch_role_lengths",
    "batch_role_offsets",
    "batch_membership_masks",
    "joint_layout_descriptor",
    "debug_coordinates",
    "debug_rank_metadata",
)
_INPUT_REQUIRED = frozenset(_INPUT_FIELD_ORDER[:15])
_INPUT_OPTIONAL = frozenset(_INPUT_FIELD_ORDER[15:])
_LEGACY_INPUT_ALIASES = frozenset(
    (
        "source_pair_values",
        "source_sample_offsets",
        "source_entry_validity",
        "source_sample_validity",
    )
)
_IDENTITY_FIELDS = (
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_comp_id",
)
_TABLE_AUTHORITY_FIELDS = (
    "root_kind",
    "relative_path",
    "SHA256",
    "row_count",
    "row_order_digest",
    "row_order_version",
    "selected_source_row_index_0based",
    "selected_parser_local_index",
    "parser_output_atom_count",
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

_MANIFEST = "current11_task2_batch_index_remap_contract_manifest.json"
_INPUT = "current11_task2_batch_index_remap_input_schema.json"
_OUTPUT = "current11_task2_batch_index_remap_output_schema.json"
_VOCABULARY = "current11_task2_batch_index_remap_status_vocabulary.csv"
_VECTORS = "current11_task2_batch_index_remap_reference_vectors.json"
_REPORT = "current11_task2_batch_index_remap_contract_gate_report.json"
_ARTIFACT_NAMES = (_MANIFEST, _INPUT, _OUTPUT, _VOCABULARY, _VECTORS, _REPORT)
_STABLE_NAMES = _ARTIFACT_NAMES[:5]

_REPOSITORY_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_contract_gate_v1.py",
    "scripts/check_covapie_current11_task2_batch_index_remap_contract_gate_v1.py",
    "tests/test_covapie_current11_task2_batch_index_remap_contract_gate_v1.py",
    "docs/covapie_current11_task2_batch_index_remap_contract_gate_v1_guide.md",
)
_PROJECTION_MODULE = "src/covalent_ext/covapie_current11_tensor_projection_instance_builder_v1.py"
_PROJECTION_MODULE_SHA = "39132d2f020ffd3a399c4203d10e534114bd370b8c3a288a9fbde101801022b8"
_PROJECTION_COMMIT = "124543d39ab8f2bc27e748ad2e2c57387730ba47"
_PROJECTION_DIGEST = "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
_PROJECTION_EXACT2 = {
    "current11_tensor_projection_instance.json": "ac191d0fa8b6855fd01247c4c93cce2901c91f5862de923f66855315655cf23b",
    "current11_tensor_projection_instance_builder_report.json": "d23ab150561d2a56e810b0114a2faa97f3c512e806816e1203ea70230c13e86d",
}
_PAYLOAD_MODULE = "src/covalent_ext/covapie_current11_tensor_projection_payload_builder_v1.py"
_PAYLOAD_MODULE_SHA = "c6229dce93afb82766ef1b6aacf5c547e32145f334d51ebbd6ac1d7ea5a4e197"
_PAYLOAD_COMMIT = "bc927ef679a6605339d8879559f69fc5ab3002a7"
_PAYLOAD_DIGEST = "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
_CONTRACT_MODULE = "src/covalent_ext/covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py"
_CONTRACT_MODULE_SHA = "d46ebaf163abf862aadb35301efa649eac6dc799da434e29f58f95deae2cbe0f"
_CONTRACT_COMMIT = "df9aa9d0b2a91df577b4182e0afdcf4cdfc3bbce"
_CONTRACT_DIGEST = "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
_FORMAL_RELATIVE = "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
_FORMAL_READLINK = ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-1fd8cf5823427e941b11c7b2560a336f"
_FORMAL_AGGREGATE = "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
_FORMAL_SNAPSHOT = "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
_FORMAL_EXACT4 = {
    "current11_dataset_partial_supervision_routing_manifest.json": "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d",
    "current11_dataset_partial_supervision_routing_records.csv": "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03",
    "current11_dataset_partial_supervision_sample_coverage.csv": "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e",
    "current11_dataset_partial_supervision_task_coverage.csv": "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7",
}
_DESIGN_RELATIVE = "review-scratch/current11-task2-batch-index-remap-adapter-contract-design-v1/batch_index_remap_adapter_contract_design_report.md"
_DESIGN_SHA = "12141464e9f0065a19b6bbe47014d0e29ba2ea32593766e2462cbf7ca6afc6e2"
_MATRIX_RELATIVE = "data/derived/covalent_small/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/covapie_sample_heavy_atom_projection_validation_matrix.csv"
_MATRIX_SHA = "63f1df49d9a6f4e0efbee6c8bb474deabaedea9cef91f27d2cf49f7caeee6f96"

_RUNTIME_SOURCES = {
    "dataset.py": (2693, 70, "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99", "5cd1531e9beeca2f53c17b705949676bf457a967"),
    "lightning_modules.py": (50939, 1250, "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983", "d19f18ec2841a9a3163d099f4df451d97ce795d4"),
    "equivariant_diffusion/dynamics.py": (9628, 230, "204370982696136884b50126dbd5211559d0caed51c92cb4d1ae62066ab00b8d", "a9f339c8d542b36e1703630700989c80885912d2"),
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": (64861, 1570, "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241", "61c057af51fcb0bc9dd4ab83f917e1eece2be799"),
    "configs/crossdock_fullatom_cond.yml": (1448, 61, "41428bcb548c4dc541f945ef4e52f8830fb1c64dd149fbce86aae98d73fcf519", "64284ee6758f90381ed859ae2084e35d20e194e8"),
}
_RUNTIME_VALIDATED_SYMBOLS = {
    "dataset.py": ("ProcessedLigandPocketDataset.__init__", "ProcessedLigandPocketDataset.collate_fn"),
    "lightning_modules.py": ("LigandPocketDDPM.setup", "LigandPocketDDPM.train_dataloader", "LigandPocketDDPM.val_dataloader", "LigandPocketDDPM.test_dataloader", "LigandPocketDDPM.get_ligand_and_pocket", "LigandPocketDDPM.forward"),
    "equivariant_diffusion/dynamics.py": ("EGNNDynamics.forward", "EGNNDynamics.get_edges"),
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": ("classify_type_symbol_v1", "project_type_symbols_to_checkpoint_heavy_v1"),
    "configs/crossdock_fullatom_cond.yml": (),
}
_RUNTIME_ANCHORS = {
    "dataset.py": ("np.where(np.diff(data['lig_mask']))[0] + 1", "np.where(np.diff(data['pocket_mask']))[0] + 1", "np.split(v, sections)", "torch.cat([i * torch.ones(len(x[prop]))", "torch.cat([x[prop] for x in batch], dim=0)"),
    "lightning_modules.py": ("shuffle=True", "shuffle=False", "'x': data['lig_coords']", "'x': data['pocket_coords']", "'mask': data['lig_mask']", "'mask': data['pocket_mask']", "self.ddpm(ligand, pocket, return_info=True)"),
    "equivariant_diffusion/dynamics.py": ("torch.cat((x_atoms, x_residues), dim=0)", "torch.cat((h_atoms, h_residues), dim=0)", "torch.cat([mask_atoms, mask_residues])", "h_final[:len(mask_atoms)]", "h_final[len(mask_atoms):]", "torch.cat((adj_ligand, adj_cross), dim=1)"),
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": ("if type_symbol == \"H\"", "return \"explicit_hydrogen\"", "return \"unsupported_nonhydrogen\"", "source_to_projected.append(next_index)", "next_index += 1"),
    "configs/crossdock_fullatom_cond.yml": ("dataset: 'crossdock'", "datadir: '/path/to/processed_crossdock_noH_full'", "mode: 'pocket_conditioning'", "pocket_representation: 'full-atom'", "augment_rotation: False", "augment_noise: 0"),
}

_SAMPLES = (
    ("CYS_SG_SAMPLE_INDEX_000001", "CYS_SG_SAMPLE_PREP_INPUT_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "CYS_SG_SAMPLE_PREP_INPUT_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "CYS_SG_SAMPLE_PREP_INPUT_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "CYS_SG_EXPANSION_PREP_000001", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "CYS_SG_EXPANSION_PREP_000002", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "CYS_SG_EXPANSION_PREP_000003", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "CYS_SG_EXPANSION_PREP_000004", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "CYS_SG_EXPANSION_PREP_000005", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "CYS_SG_EXPANSION_PREP_000006", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "CYS_SG_EXPANSION_PREP_000007", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "CYS_SG_EXPANSION_PREP_000008", "1B02", "UFP"),
)
_SOURCE_PAIRS = ((88, 3), (25, 3), (19, 3), (39, 3), (37, 27), (50, 21), (48, 16), (53, 20), (52, 21), (53, 18), (84, 5))
_POCKET_LOCAL = (49, 15, 12, 33, 31, 50, 48, 53, 52, 53, 84)
_LIGAND_LOCAL = (3, 3, 3, 3, 27, 21, 16, 20, 21, 18, 5)
_POCKET_ROWS = (121, 196, 178, 265, 231, 278, 267, 257, 249, 261, 228)
_LIGAND_ROWS = (13, 18, 13, 33, 31, 43, 42, 42, 43, 40, 21)
_POCKET_H = (55, 92, 82, 57, 43, 0, 0, 0, 0, 0, 0)
_LIGAND_H = (0, 5, 0, 8, 3, 0, 0, 0, 0, 0, 0)
_POCKET_RETAINED = (66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228)
_LIGAND_RETAINED = (13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21)
_SUPPORTED = frozenset(("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"))
_LEGAL_ELEMENT_TOKEN = re.compile(r"^[A-Z][a-z]?$")

_STATUS_ROWS = (
    ("REMAPPED_EXACT", "entry|overall|joint", True, False, False, True, True, "Exact deterministic remap succeeded."),
    ("NOT_IN_BATCH", "source_entry", False, True, False, False, False, "Source entry is absent from this batch."),
    ("SOURCE_SAMPLE_DUPLICATED", "entry|overall", False, False, True, False, True, "Source sample identity is duplicated."),
    ("BATCH_SAMPLE_IDENTITY_UNKNOWN", "entry|overall", False, False, True, False, True, "Batch sample identity is not bound."),
    ("BATCH_SAMPLE_DUPLICATED", "entry|overall", False, False, True, False, True, "Batch sample identity is duplicated."),
    ("SCHEMA_VERSION_MISMATCH", "entry|overall", False, False, True, False, True, "Input schema version is not exact."),
    ("SOURCE_TABLE_IDENTITY_MISMATCH", "entry|overall", False, False, True, False, True, "Source table path, hash, count, order, or sample binding differs."),
    ("SOURCE_ROW_OUT_OF_RANGE", "entry|overall", False, False, True, False, True, "Source row is outside its exact table."),
    ("SOURCE_ATOM_IDENTITY_MISMATCH", "entry|overall", False, False, True, False, True, "Source atom composite identity differs."),
    ("ROLE_MISMATCH", "entry|overall", False, False, True, False, True, "Pocket and ligand roles differ or are exchanged."),
    ("PARSER_ATOM_NOT_FOUND", "entry|overall", False, False, True, False, True, "No retained parser atom maps from the source row."),
    ("PARSER_ATOM_NOT_UNIQUE", "entry|overall", False, False, True, False, True, "More than one parser atom maps from the source row."),
    ("PARSER_COUNT_MISMATCH", "entry|overall", False, False, True, False, True, "Parser count differs from the actual role length."),
    ("COLLATE_OFFSET_MISSING", "entry|overall", False, False, True, False, True, "Role offsets are missing or not the exact exclusive prefix sum."),
    ("COLLATE_LENGTH_MISMATCH", "entry|overall", False, False, True, False, True, "Lengths, offsets, or membership masks disagree."),
    ("BATCH_INDEX_OUT_OF_RANGE", "entry|overall", False, False, True, False, True, "Computed segment or joint index is out of range."),
    ("JOINT_INDEX_SPACE_UNAVAILABLE", "joint", False, False, False, False, False, "Exact joint layout was not supplied; segment remap remains valid."),
    ("ENTRY_INVALID", "entry|overall", False, False, True, False, True, "A source or sample validity flag is false, or a valid-pair segment is empty."),
)
_HARD_FAILURES = tuple(row[0] for row in _STATUS_ROWS if row[4])


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _blob(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def _json(value: object) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"), parse_constant=lambda _value: _fail())
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
    path = PurePosixPath(relative)
    if type(relative) is not str or not relative or path.is_absolute() or ".." in path.parts or str(path) != relative:
        _fail()
    return path


def _read_regular(root: Path, relative: str, expected_sha: str | None = None) -> bytes:
    rel = _safe_relative(relative)
    path = root.joinpath(*rel.parts)
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
        payload = path.read_bytes()
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if (not resolved.is_relative_to(root) or stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o644 or (expected_sha is not None and _sha(payload) != expected_sha)):
        _fail()
    return payload


def _snapshot(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    return (int(metadata.st_dev), int(metadata.st_ino), stat.S_IFMT(metadata.st_mode), stat.S_IMODE(metadata.st_mode), int(metadata.st_size), int(metadata.st_mtime_ns), None if payload is None else _sha(payload))


def _formal_snapshot(canonical: Path) -> dict[str, object]:
    try:
        parent = canonical.parent
        link = os.readlink(canonical)
        object_path = parent / link
        inventory = tuple(sorted(os.listdir(object_path)))
        return {"parent": _snapshot(parent), "parent_inventory": tuple(sorted(os.listdir(parent))), "canonical": _snapshot(canonical), "readlink": link, "object": _snapshot(object_path), "object_inventory": inventory, "leaves": {name: _snapshot(object_path / name) for name in inventory}}
    except OSError as error:
        raise ValueError(_ERROR) from error


@contextmanager
def _predecessor_status_compatibility() -> Iterator[None]:
    gate = _instance_builder._payload_builder._contract_gate
    original = gate._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            lines = output.splitlines()
            if any(len(line) >= 4 and line[3:] in _REPOSITORY_EXACT4 and line not in allowed for line in lines):
                _fail()
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        gate._run_git = compatible
        yield
    finally:
        gate._run_git = original


def _projection_exact2(repo: Path, state: Path) -> tuple[dict[str, bytes], dict[str, object], dict[str, object]]:
    with _predecessor_status_compatibility():
        first = _instance_builder.build_covapie_current11_tensor_projection_instance_v1(repo_root=repo, state_root=state)
    with _predecessor_status_compatibility():
        second = _instance_builder.build_covapie_current11_tensor_projection_instance_v1(repo_root=repo, state_root=state)
    if type(first) is not dict or first != second or tuple(first) != tuple(_PROJECTION_EXACT2):
        _fail()
    for name, digest in _PROJECTION_EXACT2.items():
        if type(first[name]) is not bytes or _sha(first[name]) != digest:
            _fail()
    instance = _strict_json(first["current11_tensor_projection_instance.json"])
    report = _strict_json(first["current11_tensor_projection_instance_builder_report.json"])
    if report.get("builder_status") != "PASS_IN_MEMORY_FULL_EXACT25_PROJECTION_INSTANCE_ONLY" or report.get("projection_instance_digest") != _PROJECTION_DIGEST or report.get("payload_bundle_digest") != _PAYLOAD_DIGEST or report.get("contract_digest") != _CONTRACT_DIGEST:
        _fail()
    return first, instance, report


def _ast_symbols(payload: bytes) -> set[str]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = next((outer for outer in ast.walk(tree) if isinstance(outer, ast.ClassDef) and node in outer.body), None)
            found.add(f"{parent.name}.{node.name}" if parent is not None else node.name)
    return found


def _runtime_inventory(repo: Path) -> list[dict[str, object]]:
    result = []
    for relative, (size, lines, digest, blob) in _RUNTIME_SOURCES.items():
        payload = _read_regular(repo, relative, digest)
        if len(payload) != size or payload.count(b"\n") != lines or _blob(payload) != blob:
            _fail()
        symbols = _RUNTIME_VALIDATED_SYMBOLS[relative]
        if symbols and not set(symbols).issubset(_ast_symbols(payload)):
            _fail()
        anchors = _RUNTIME_ANCHORS[relative]
        text = payload.decode("utf-8")
        if any(anchor not in text for anchor in anchors):
            _fail()
        result.append({"relative_path": relative, "bytes": size, "LF": lines, "SHA256": digest, "Git_blob": blob, "validated_symbols": list(symbols), "semantic_anchors": list(anchors)})
    return result


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(_ERROR) from error
    if reader.fieldnames is None or any(None in row for row in rows):
        _fail()
    return rows


def _bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    _fail()


def _sample_identity(index: int) -> dict[str, object]:
    row_id, prep_id, pdb_id, ligand = _SAMPLES[index]
    return {"source_sample_index": index, "sample_index_row_id": row_id, "sample_preparation_input_id": prep_id, "pdb_id": pdb_id, "ligand_comp_id": ligand}


def _source_contract(instance: Mapping[str, object]) -> dict[str, object]:
    try:
        samples = instance["sample_order"]
        tasks = instance["task_order"]
        task_payloads = instance["task_payloads"]
        task_validity = instance["task_payload_entry_validity"]
        assert type(samples) is list and type(tasks) is list and type(task_payloads) is list and type(task_validity) is list
        payload_slot = task_payloads[2]
        validity_slot = task_validity[2]
        payload = payload_slot["payload"]
        validity = validity_slot["entry_validity"]
    except (AssertionError, KeyError, IndexError, TypeError) as error:
        raise ValueError(_ERROR) from error
    expected_samples = [{"sample_index": i, "sample_index_row_id": s[0], "pdb_id": s[2], "ligand_comp_id": s[3]} for i, s in enumerate(_SAMPLES)]
    if samples != expected_samples or tasks[2] != {"task_index": 2, "semantic_task_name": "ligand_residue_atom_pair_supervision"}:
        _fail()
    if payload.get("values_int64") != [list(pair) for pair in _SOURCE_PAIRS] or payload.get("sample_offsets_int64") != list(range(12)) or payload.get("entry_validity_bool") != [True] * 11 or payload.get("sample_validity_bool") != [True] * 11 or validity != {"entry_validity_bool": [True] * 11, "sample_offsets_int64": list(range(12)), "sample_validity_bool": [True] * 11}:
        _fail()
    frozen = {"column_semantics": ["pocket_atom_table_row_index_0based", "ligand_atom_table_row_index_0based"], "locator_semantics": "derived_row_index_bound_to_exact_atom_table_bytes_and_order", "permanent_chemical_identifier": False, "model_input_allowed_now": False, "batch_index_remap_required": True}
    if any(payload.get(key) != value for key, value in frozen.items()):
        _fail()
    return {"sample_order": [_sample_identity(i) for i in range(11)], "pair_values_source_row_indices": [list(pair) for pair in _SOURCE_PAIRS], "sample_pair_offsets": list(range(12)), "entry_validity": [True] * 11, "sample_validity": [True] * 11, "pair_count": 11, **frozen}


def _classify(symbol: object) -> str:
    if type(symbol) is not str or not symbol or symbol.strip() != symbol:
        return "missing_or_invalid"
    if symbol == "H":
        return "explicit_hydrogen"
    if symbol in _SUPPORTED:
        return "supported_checkpoint_heavy_atom"
    if _LEGAL_ELEMENT_TOKEN.fullmatch(symbol) is None:
        return "missing_or_invalid"
    return "unsupported_nonhydrogen"


def _projection_records(repo: Path, instance: Mapping[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    matrix = _csv_rows(_read_regular(repo, _MATRIX_RELATIVE, _MATRIX_SHA))
    if len(matrix) != 11:
        _fail()
    provenance = instance.get("task_payload_provenance")
    if type(provenance) is not list:
        _fail()
    pair_provenance = [row for row in provenance if type(row) is dict and row.get("semantic_task_name") == "ligand_residue_atom_pair_supervision"]
    if len(pair_provenance) != 11:
        _fail()
    records: list[dict[str, object]] = []
    evaluator_tables: list[dict[str, object]] = []
    for index, (matrix_row, provenance_row) in enumerate(zip(matrix, pair_provenance)):
        expected_matrix = {
            "sample_index_row_id": _SAMPLES[index][0], "sample_preparation_input_id": _SAMPLES[index][1], "pdb_id": _SAMPLES[index][2], "ligand_identity": _SAMPLES[index][3],
            "source_pocket_atom_count": str(_POCKET_ROWS[index]), "excluded_pocket_h_count": str(_POCKET_H[index]), "retained_pocket_heavy_count": str(_POCKET_RETAINED[index]), "unsupported_pocket_nonh_count": "0",
            "source_ligand_atom_count": str(_LIGAND_ROWS[index]), "excluded_ligand_h_count": str(_LIGAND_H[index]), "retained_ligand_heavy_count": str(_LIGAND_RETAINED[index]), "unsupported_ligand_nonh_count": "0",
            "source_residue_pair_row_index_0based": str(_SOURCE_PAIRS[index][0]), "projected_residue_pair_row_index_0based": str(_POCKET_LOCAL[index]), "source_ligand_pair_row_index_0based": str(_SOURCE_PAIRS[index][1]), "projected_ligand_pair_row_index_0based": str(_LIGAND_LOCAL[index]),
            "residue_pair_atom_retained": "true", "ligand_pair_atom_retained": "true", "pair_projection_exact_one": "true", "source_order_preserved": "true", "sample_policy_outcome": "passed", "verified": "true",
        }
        if any(matrix_row.get(key) != value for key, value in expected_matrix.items()):
            _fail()
        bindings = provenance_row.get("secondary_source_bindings")
        if type(bindings) is not list or len(bindings) != 2:
            _fail()
        role_records: dict[str, object] = {}
        sample_record = {"source_sample_index": index, "sample_identity": _sample_identity(index), "roles": []}
        for role_index, (role, source_row, local, row_count, h_count, retained) in enumerate((("pocket", _SOURCE_PAIRS[index][0], _POCKET_LOCAL[index], _POCKET_ROWS[index], _POCKET_H[index], _POCKET_RETAINED[index]), ("ligand", _SOURCE_PAIRS[index][1], _LIGAND_LOCAL[index], _LIGAND_ROWS[index], _LIGAND_H[index], _LIGAND_RETAINED[index]))):
            binding = bindings[role_index]
            expected_entity = "target_residue_atom" if role == "pocket" else "ligand_atom"
            if type(binding) is not dict or binding.get("entity_role") != expected_entity or binding.get("matched_row_index_0based") != source_row or binding.get("data_row_count") != row_count:
                _fail()
            relative = binding.get("relative_path")
            digest = binding.get("sha256")
            if type(relative) is not str or type(digest) is not str or binding.get("root_kind") != "repo_root":
                _fail()
            table_payload = _read_regular(repo, relative, digest)
            table = _csv_rows(table_payload)
            if len(table) != row_count or not 0 <= source_row < len(table):
                _fail()
            classes = [_classify(row.get("type_symbol")) for row in table]
            unsupported = sum(value in {"unsupported_nonhydrogen", "missing_or_invalid"} for value in classes)
            hydrogen = classes.count("explicit_hydrogen")
            retained_actual = classes.count("supported_checkpoint_heavy_atom")
            if unsupported != 0 or hydrogen != h_count or retained_actual != retained:
                _fail()
            source_to_local: list[int | None] = []
            next_local = 0
            for value in classes:
                if value == "supported_checkpoint_heavy_atom":
                    source_to_local.append(next_local)
                    next_local += 1
                else:
                    source_to_local.append(None)
            selected = table[source_row]
            if source_to_local[source_row] != local or selected.get("atom_site_id") != str(binding.get("matched_atom_site_id")):
                _fail()
            if selected.get("sample_preparation_input_id") != _SAMPLES[index][1] or selected.get("pdb_id") != _SAMPLES[index][2] or (role == "ligand" and selected.get("ligand_comp_id") != _SAMPLES[index][3]):
                _fail()
            identity = {key: selected.get(key, "") for key in ("atom_site_id", "atom_name", "type_symbol", "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id")}
            identity["residue_name_or_ligand_comp_id"] = selected.get("residue_name", selected.get("ligand_comp_id", ""))
            role_record = {"role": role, "root_kind": "repo_root", "relative_path": relative, "SHA256": digest, "row_count": row_count, "row_order_digest": digest, "row_order_version": "physical_csv_data_row_order_v1", "selected_source_row_index_0based": source_row, "selected_parser_local_index": local, "selected_atom_identity": identity, "explicit_hydrogen_count": hydrogen, "unsupported_nonhydrogen_count": unsupported, "retained_heavy_count": retained, "source_to_parser_exact_one": True, "selected_row_retained": True, "committed_projection_matrix_local_index": int(matrix_row["projected_residue_pair_row_index_0based" if role == "pocket" else "projected_ligand_pair_row_index_0based"])}
            sample_record["roles"].append(role_record)
            role_records[role] = {**role_record, "parser_output_atom_count": retained, "source_to_parser_local": {str(source_row): local}}
        records.append(sample_record)
        evaluator_tables.append({"sample_identity": _sample_identity(index), "roles": role_records})
    return records, evaluator_tables


def _prefix(lengths: Sequence[int]) -> list[int]:
    result = [0]
    for value in lengths:
        if type(value) is not int or value < 0:
            _fail()
        result.append(result[-1] + value)
    return result


class _ReferenceFailure(Exception):
    def __init__(self, status: str) -> None:
        self.status = status


def _reference_fail(status: str) -> NoReturn:
    if status not in _HARD_FAILURES:
        _fail()
    raise _ReferenceFailure(status)


def _identity_key(identity: Mapping[str, object]) -> tuple[object, ...]:
    return tuple(identity.get(key) for key in _IDENTITY_FIELDS)


def _identity_is_complete(identity: object) -> bool:
    return type(identity) is dict and all(
        type(identity.get(field)) is str
        and bool(identity[field])
        and identity[field].strip() == identity[field]
        for field in _IDENTITY_FIELDS
    )


def _authority_lookup(
    authoritative_tables: Sequence[Mapping[str, object]],
) -> dict[tuple[object, ...], Mapping[str, object]]:
    if type(authoritative_tables) not in (list, tuple):
        _fail()
    result: dict[tuple[object, ...], Mapping[str, object]] = {}
    for table in authoritative_tables:
        if type(table) is not dict or not _identity_is_complete(table.get("sample_identity")):
            _fail()
        key = _identity_key(table["sample_identity"])
        if key in result:
            _fail()
        result[key] = table
    return result


def _empty_failure(case: Mapping[str, object], status: str, pair_count: int) -> dict[str, object]:
    return {"schema_version": _OUTPUT_SCHEMA, "source_projection_digest": _PROJECTION_DIGEST, "source_payload_digest": _PAYLOAD_DIGEST, "batch_sample_order": case.get("batch_sample_order", []), "pair_values_source_row_indices": [], "pair_values_parser_local_indices": [], "pair_values_batch_indices": [], "pair_values_joint_global_indices": None, "pair_sample_indices": [], "sample_pair_offsets": [0], "entry_validity": [], "sample_validity": [], "source_entry_outcomes": [{"source_entry_index": i, "status": status if i == 0 else "ENTRY_INVALID", "failure_reason": status if i == 0 else "ENTRY_INVALID"} for i in range(pair_count)], "remap_status": status, "failure_reason": status, "provenance": {"joint_index_status": "JOINT_INDEX_SPACE_UNAVAILABLE", "reference_contract_evaluator_only": True}, "readiness": {"public_adapter_implemented": False, "model_integration_authorized": False, "loss_authorized": False}}


def _evaluate_reference_case(
    case: Mapping[str, object],
    *,
    authoritative_tables: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Private contract evaluator used only to freeze and test reference cases."""
    if type(case) is not dict:
        _fail()
    pairs = case.get("source_pair_values_int64")
    offsets = case.get("source_sample_offsets_int64")
    source_samples = case.get("source_sample_order")
    pair_count = len(pairs) if type(pairs) is list else 0
    try:
        keys = set(case)
        if (
            not _INPUT_REQUIRED.issubset(keys)
            or not keys.issubset(_INPUT_REQUIRED | _INPUT_OPTIONAL)
            or bool(keys & _LEGACY_INPUT_ALIASES)
            or case.get("schema_version") != _INPUT_SCHEMA
            or case.get("source_projection_digest") != _PROJECTION_DIGEST
            or case.get("source_payload_digest") != _PAYLOAD_DIGEST
            or case.get("parser_schema_version") != _PARSER_SCHEMA
            or case.get("collate_schema_version") != _COLLATE_SCHEMA
        ):
            _reference_fail("SCHEMA_VERSION_MISMATCH")
        if type(pairs) is not list or type(offsets) is not list or type(source_samples) is not list or len(offsets) != len(source_samples) + 1 or not offsets or offsets[0] != 0 or offsets[-1] != len(pairs) or any(type(value) is not int for value in offsets) or any(a > b for a, b in zip(offsets, offsets[1:])):
            _reference_fail("ENTRY_INVALID")
        if any(not _identity_is_complete(value) for value in source_samples):
            _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        source_keys = [_identity_key(value) for value in source_samples]
        if len(set(source_keys)) != len(source_keys):
            _reference_fail("SOURCE_SAMPLE_DUPLICATED")
        if [value.get("source_sample_index") for value in source_samples] != list(range(len(source_samples))):
            _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        batch = case.get("batch_sample_order")
        tables = case.get("batch_sample_atom_identity_tables")
        lengths = case.get("batch_role_lengths")
        declared_offsets = case.get("batch_role_offsets")
        masks = case.get("batch_membership_masks")
        if type(batch) is not list or type(tables) is not list or len(tables) != len(batch):
            _reference_fail("BATCH_SAMPLE_IDENTITY_UNKNOWN")
        if any(not _identity_is_complete(value) for value in batch):
            _reference_fail("BATCH_SAMPLE_IDENTITY_UNKNOWN")
        batch_keys = [_identity_key(value) for value in batch]
        if len(set(batch_keys)) != len(batch_keys):
            _reference_fail("BATCH_SAMPLE_DUPLICATED")
        if type(lengths) is not dict or type(declared_offsets) is not dict or type(masks) is not dict:
            _reference_fail("COLLATE_OFFSET_MISSING")
        for role in ("pocket", "ligand"):
            role_lengths = lengths.get(role)
            if type(role_lengths) is not list or len(role_lengths) != len(batch):
                _reference_fail("COLLATE_LENGTH_MISMATCH")
            expected_offsets = _prefix(role_lengths)
            if declared_offsets.get(role) != expected_offsets:
                _reference_fail("COLLATE_OFFSET_MISSING")
            expected_mask = [ordinal for ordinal, length in enumerate(role_lengths) for _ in range(length)]
            if masks.get(role) != expected_mask:
                _reference_fail("COLLATE_LENGTH_MISMATCH")
        table_by_key: dict[tuple[object, ...], Mapping[str, object]] = {}
        for table, key in zip(tables, batch_keys):
            if type(table) is not dict or not _identity_is_complete(table.get("sample_identity")) or _identity_key(table["sample_identity"]) != key:
                _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
            table_by_key[key] = table
        source_lookup = {key: index for index, key in enumerate(source_keys)}
        authority = _authority_lookup(authoritative_tables)
        if any(key not in authority for key in source_keys):
            _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        source_outcomes = [{"source_entry_index": i, "status": "NOT_IN_BATCH", "failure_reason": "NONE"} for i in range(len(pairs))]
        out_source: list[list[int]] = []
        out_local: list[list[int]] = []
        out_segment: list[list[int]] = []
        out_sample_indices: list[int] = []
        out_validity: list[bool] = []
        output_offsets = [0]
        source_entry_validity = case.get("source_entry_validity_bool")
        source_sample_validity = case.get("source_sample_validity_bool")
        if type(source_entry_validity) is not list or len(source_entry_validity) != len(pairs) or type(source_sample_validity) is not list or len(source_sample_validity) != len(source_samples):
            _reference_fail("ENTRY_INVALID")
        for batch_ordinal, key in enumerate(batch_keys):
            source_index = source_lookup.get(key)
            before_count = len(out_source)
            table = table_by_key[key]
            roles = table.get("roles")
            if type(roles) is not dict or set(roles) != {"pocket", "ligand"} or any(type(roles[role]) is not dict or roles[role].get("role") != role for role in ("pocket", "ligand")):
                _reference_fail("ROLE_MISMATCH")
            expected_roles = authority[key].get("roles") if source_index is not None else None
            if source_index is not None and (type(expected_roles) is not dict or set(expected_roles) != {"pocket", "ligand"}):
                _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
            for role in ("pocket", "ligand"):
                role_table = roles[role]
                if role_table.get("parser_output_atom_count") != lengths[role][batch_ordinal]:
                    _reference_fail("PARSER_COUNT_MISMATCH")
                digest = role_table.get("SHA256")
                relative = role_table.get("relative_path")
                identity = role_table.get("selected_atom_identity")
                if (
                    role_table.get("root_kind") != "repo_root"
                    or type(relative) is not str
                    or not relative
                    or relative.strip() != relative
                    or type(digest) is not str
                    or len(digest) != 64
                    or any(character not in "0123456789abcdef" for character in digest)
                    or role_table.get("row_order_digest") != digest
                    or role_table.get("row_order_version") != "physical_csv_data_row_order_v1"
                    or type(role_table.get("row_count")) is not int
                    or role_table["row_count"] < 0
                    or type(role_table.get("source_to_parser_local")) is not dict
                ):
                    _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
                if (
                    type(identity) is not dict
                    or set(identity) != set(_ATOM_IDENTITY_FIELDS)
                    or any(type(identity[field]) is not str for field in _ATOM_IDENTITY_FIELDS)
                ):
                    _reference_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
                if source_index is not None:
                    expected = expected_roles[role]
                    if any(role_table.get(field) != expected.get(field) for field in _TABLE_AUTHORITY_FIELDS):
                        _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
                    expected_identity = expected.get("selected_atom_identity")
                    if type(expected_identity) is not dict or set(expected_identity) != set(_ATOM_IDENTITY_FIELDS) or any(identity[field] != expected_identity.get(field) or type(identity[field]) is not type(expected_identity.get(field)) for field in _ATOM_IDENTITY_FIELDS):
                        _reference_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
            if source_index is not None:
                if source_sample_validity[source_index] is not True:
                    _reference_fail("ENTRY_INVALID")
                for entry_index in range(offsets[source_index], offsets[source_index + 1]):
                    if source_entry_validity[entry_index] is not True:
                        _reference_fail("ENTRY_INVALID")
                    pair = pairs[entry_index]
                    if type(pair) is not list or len(pair) != 2 or any(type(value) is not int for value in pair):
                        _reference_fail("ENTRY_INVALID")
                    local_pair = []
                    segment_pair = []
                    for role, source_row in zip(("pocket", "ligand"), pair):
                        role_table = roles[role]
                        if not 0 <= source_row < role_table.get("row_count", -1):
                            _reference_fail("SOURCE_ROW_OUT_OF_RANGE")
                        mapping = role_table.get("source_to_parser_local")
                        if type(mapping) is not dict or str(source_row) not in mapping:
                            _reference_fail("PARSER_ATOM_NOT_FOUND")
                        local = mapping[str(source_row)]
                        if type(local) is list:
                            _reference_fail("PARSER_ATOM_NOT_UNIQUE")
                        expected_mapping = expected_roles[role].get("source_to_parser_local")
                        if type(expected_mapping) is not dict or expected_mapping.get(str(source_row)) != local:
                            _reference_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
                        if type(local) is not int or not 0 <= local < lengths[role][batch_ordinal]:
                            _reference_fail("BATCH_INDEX_OUT_OF_RANGE")
                        local_pair.append(local)
                        segment = declared_offsets[role][batch_ordinal] + local
                        if not declared_offsets[role][batch_ordinal] <= segment < declared_offsets[role][batch_ordinal + 1] or masks[role][segment] != batch_ordinal:
                            _reference_fail("BATCH_INDEX_OUT_OF_RANGE")
                        segment_pair.append(segment)
                    out_source.append(pair[:])
                    out_local.append(local_pair)
                    out_segment.append(segment_pair)
                    out_sample_indices.append(batch_ordinal)
                    out_validity.append(True)
                    source_outcomes[entry_index] = {"source_entry_index": entry_index, "status": "REMAPPED_EXACT", "failure_reason": "NONE"}
            output_offsets.append(len(out_source))
            if source_index is not None and offsets[source_index + 1] > offsets[source_index] and len(out_source) == before_count:
                _reference_fail("ENTRY_INVALID")
        descriptor = case.get("joint_layout_descriptor")
        if descriptor not in (None, _JOINT_LAYOUT):
            _reference_fail("SCHEMA_VERSION_MISMATCH")
        if descriptor == _JOINT_LAYOUT:
            n_lig = declared_offsets["ligand"][-1]
            joint = [[n_lig + pocket, ligand] for (pocket, ligand) in out_segment]
            total = n_lig + declared_offsets["pocket"][-1]
            if any(any(not 0 <= value < total for value in pair) for pair in joint):
                _reference_fail("BATCH_INDEX_OUT_OF_RANGE")
            joint_status = "REMAPPED_EXACT"
        else:
            joint = None
            joint_status = "JOINT_INDEX_SPACE_UNAVAILABLE"
        return {"schema_version": _OUTPUT_SCHEMA, "source_projection_digest": case["source_projection_digest"], "source_payload_digest": case["source_payload_digest"], "batch_sample_order": batch, "pair_values_source_row_indices": out_source, "pair_values_parser_local_indices": out_local, "pair_values_batch_indices": out_segment, "pair_values_joint_global_indices": joint, "pair_sample_indices": out_sample_indices, "sample_pair_offsets": output_offsets, "entry_validity": out_validity, "sample_validity": [True] * len(batch), "source_entry_outcomes": source_outcomes, "remap_status": "REMAPPED_EXACT", "failure_reason": "NONE", "provenance": {"joint_index_status": joint_status, "joint_layout_descriptor": descriptor, "reference_contract_evaluator_only": True}, "readiness": {"public_adapter_implemented": False, "model_integration_authorized": False, "loss_authorized": False}}
    except _ReferenceFailure as error:
        return _empty_failure(case, error.status, pair_count)


def _reference_input(order: Sequence[int], tables: Sequence[Mapping[str, object]], *, joint: str | None = _JOINT_LAYOUT) -> dict[str, object]:
    batch = [_sample_identity(index) for index in order]
    pocket_lengths = [_POCKET_RETAINED[index] for index in order]
    ligand_lengths = [_LIGAND_RETAINED[index] for index in order]
    return {"schema_version": _INPUT_SCHEMA, "source_projection_digest": _PROJECTION_DIGEST, "source_payload_digest": _PAYLOAD_DIGEST, "parser_schema_version": _PARSER_SCHEMA, "collate_schema_version": _COLLATE_SCHEMA, "source_sample_order": [_sample_identity(i) for i in range(11)], "source_pair_values_int64": [list(pair) for pair in _SOURCE_PAIRS], "source_sample_offsets_int64": list(range(12)), "source_entry_validity_bool": [True] * 11, "source_sample_validity_bool": [True] * 11, "batch_sample_order": batch, "batch_sample_atom_identity_tables": [copy.deepcopy(tables[index]) for index in order], "batch_role_lengths": {"pocket": pocket_lengths, "ligand": ligand_lengths}, "batch_role_offsets": {"pocket": _prefix(pocket_lengths), "ligand": _prefix(ligand_lengths)}, "batch_membership_masks": {"pocket": [i for i, length in enumerate(pocket_lengths) for _ in range(length)], "ligand": [i for i, length in enumerate(ligand_lengths) for _ in range(length)]}, "joint_layout_descriptor": joint}


def _synthetic_authority() -> list[dict[str, object]]:
    identities = [{"source_sample_index": i, "sample_index_row_id": f"S{i}", "sample_preparation_input_id": f"P{i}", "pdb_id": f"X{i}", "ligand_comp_id": f"L{i}"} for i in range(3)]
    tables: list[dict[str, object]] = []
    for sample_index, identity in enumerate(identities):
        roles = {}
        for role in ("pocket", "ligand"):
            digest = _sha(f"synthetic:{sample_index}:{role}:physical_csv_data_row_order_v1".encode("ascii"))
            atom_identity = {"atom_site_id": f"{sample_index}-{role}-0", "atom_name": "C0", "type_symbol": "C", "residue_name_or_ligand_comp_id": f"R{sample_index}" if role == "pocket" else f"L{sample_index}", "auth_asym_id": "A", "auth_seq_id": str(sample_index), "label_asym_id": "A" if role == "pocket" else "B", "label_seq_id": ""}
            roles[role] = {"role": role, "root_kind": "repo_root", "relative_path": f"synthetic/reference/S{sample_index}/{role}_atom_table.csv", "SHA256": digest, "row_count": 8, "row_order_digest": digest, "row_order_version": "physical_csv_data_row_order_v1", "selected_source_row_index_0based": 0, "selected_parser_local_index": 0, "selected_atom_identity": atom_identity, "parser_output_atom_count": 8, "source_to_parser_local": {str(i): i for i in range(8)}}
        tables.append({"sample_identity": identity, "roles": roles})
    return tables


def _synthetic_case() -> dict[str, object]:
    tables = _synthetic_authority()
    identities = [copy.deepcopy(table["sample_identity"]) for table in tables]
    order = [2, 0, 1]
    return {"schema_version": _INPUT_SCHEMA, "source_projection_digest": _PROJECTION_DIGEST, "source_payload_digest": _PAYLOAD_DIGEST, "parser_schema_version": _PARSER_SCHEMA, "collate_schema_version": _COLLATE_SCHEMA, "source_sample_order": identities, "source_pair_values_int64": [[1, 2], [3, 4], [0, 0]], "source_sample_offsets_int64": [0, 2, 2, 3], "source_entry_validity_bool": [True, True, True], "source_sample_validity_bool": [True, True, True], "batch_sample_order": [copy.deepcopy(identities[i]) for i in order], "batch_sample_atom_identity_tables": [copy.deepcopy(tables[i]) for i in order], "batch_role_lengths": {"pocket": [8, 8, 8], "ligand": [8, 8, 8]}, "batch_role_offsets": {"pocket": [0, 8, 16, 24], "ligand": [0, 8, 16, 24]}, "batch_membership_masks": {"pocket": [i for i in range(3) for _ in range(8)], "ligand": [i for i in range(3) for _ in range(8)]}, "joint_layout_descriptor": _JOINT_LAYOUT}


def _batch_contract(case: Mapping[str, object]) -> dict[str, object]:
    lengths = case["batch_role_lengths"]
    offsets = case["batch_role_offsets"]
    n_lig = offsets["ligand"][-1]
    n_pocket = offsets["pocket"][-1]
    return {
        "batch_role_lengths": lengths,
        "batch_role_offsets": offsets,
        "N_lig": n_lig,
        "N_pocket": n_pocket,
        "joint_total": n_lig + n_pocket,
        "joint_layout_descriptor": case.get("joint_layout_descriptor"),
    }


def _field(field_name: str, *, required: bool, optional: bool, forbidden_if: list[str], container_kind: str, dtype: str, rank: int | str, logical_shape: str, axes: list[str], missing_semantics: str, validation_rules: list[str], authority: str, model: bool = False, loss: bool = False) -> dict[str, object]:
    return {"field_name": field_name, "required": required, "optional": optional, "forbidden_if": forbidden_if, "container_kind": container_kind, "dtype": dtype, "rank": rank, "logical_shape": logical_shape, "axes": axes, "missing_semantics": missing_semantics, "validation_rules": validation_rules, "authority": authority, "model_input_allowed_now": model, "loss_participation_allowed_now": loss}


def _input_schema_artifact() -> dict[str, object]:
    names = _INPUT_FIELD_ORDER
    fields = []
    for index, name in enumerate(names):
        required = index < 15
        optional = not required
        kind, dtype, rank, shape, axes = ("scalar", "utf8_string", 0, "[]", [])
        if name in {"source_sample_order", "batch_sample_order", "batch_sample_atom_identity_tables"}:
            exact_shape = {"source_sample_order": "[S]", "batch_sample_order": "[B]", "batch_sample_atom_identity_tables": "[B]"}[name]
            kind, dtype, rank, shape, axes = "record_array", "structured", 1, exact_shape, ["sample"]
        elif name == "source_pair_values_int64":
            kind, dtype, rank, shape, axes = "array", "int64", 2, "[P,2]", ["pair", "role:pocket,ligand"]
        elif name == "source_sample_offsets_int64":
            kind, dtype, rank, shape, axes = "array", "int64", 1, "[S+1]", ["source_sample_boundary"]
        elif name in {"source_entry_validity_bool", "source_sample_validity_bool"}:
            exact_shape = {"source_entry_validity_bool": "[P]", "source_sample_validity_bool": "[S]"}[name]
            kind, dtype, rank, shape, axes = "array", "bool", 1, exact_shape, ["entry_or_sample"]
        elif name in {"batch_role_lengths", "batch_role_offsets", "batch_membership_masks"}:
            kind, dtype, rank, shape, axes = "role_keyed_arrays", "int64", "role-dependent", "pocket and ligand arrays", ["role", "batch_or_node"]
        elif name == "debug_coordinates":
            kind, dtype, rank, shape, axes = "optional_record", "float", "debug-only", "implementation-defined debug shape", ["debug_only"]
        elif name == "debug_rank_metadata":
            kind, dtype, rank, shape, axes = "optional_record", "structured", "debug-only", "rank-local metadata", ["debug_only"]
        rules = ["exact type and shape", "all identity/provenance bindings validate", "no implicit coercion"]
        if name == "joint_layout_descriptor":
            rules = [f"absent or null allowed", f"only exact non-null value {_JOINT_LAYOUT}", "unknown descriptor fails closed"]
        fields.append(_field(name, required=required, optional=optional, forbidden_if=[], container_kind=kind, dtype=dtype, rank=rank, logical_shape=shape, axes=axes, missing_semantics="forbidden" if required else "absent_or_null_without_semantic_substitution", validation_rules=rules, authority="published projection, exact runtime batch, or debug-only as named"))
    return {"schema_version": _INPUT_SCHEMA, "field_order": list(names), "fields": fields, "required_fields": list(names[:15]), "optional_fields": list(names[15:]), "forbidden_input_semantics": ["distance-based match", "feature-vector equality", "model logits", "candidate/inferred labels", "warhead type", "reaction family", "nearest atom", "RDKit index", "atom-map number", "checkpoint bytes"], "index_base": 0, "adapter_implemented": False}


def _output_schema_artifact() -> dict[str, object]:
    names = ("schema_version", "source_projection_digest", "source_payload_digest", "batch_sample_order", "pair_values_source_row_indices", "pair_values_parser_local_indices", "pair_values_batch_indices", "pair_values_joint_global_indices", "pair_sample_indices", "sample_pair_offsets", "entry_validity", "sample_validity", "source_entry_outcomes", "remap_status", "failure_reason", "provenance", "readiness")
    fields = []
    for name in names:
        kind, dtype, rank, shape, axes = "scalar", "utf8_string", 0, "[]", []
        nullable = False
        presence = "always"
        if name == "batch_sample_order":
            kind, dtype, rank, shape, axes = "record_array", "structured", 1, "[B]", ["batch_sample"]
        elif name.startswith("pair_values_"):
            kind, dtype, rank, shape, axes = "array", "int64", 2, "[P_batch,2]", ["batch_pair", "role:pocket,ligand"]
            if name == "pair_values_joint_global_indices":
                nullable = True
        elif name in {"pair_sample_indices", "entry_validity", "sample_validity", "sample_pair_offsets"}:
            exact_shape = {"pair_sample_indices": "[P_batch]", "sample_pair_offsets": "[B+1]", "entry_validity": "[P_batch]", "sample_validity": "[B]"}[name]
            kind, dtype, rank, shape, axes = "array", "bool" if "validity" in name else "int64", 1, exact_shape, ["entry_sample_or_boundary"]
        elif name == "source_entry_outcomes":
            kind, dtype, rank, shape, axes = "record_array", "structured", 1, "[P_source]", ["source_entry"]
        elif name in {"provenance", "readiness"}:
            kind, dtype, rank, shape, axes = "record", "structured", 0, "{}", []
        missing = "never absent"
        rules = ["exact type, presence, shape, and closed vocabulary"]
        if name == "pair_values_joint_global_indices":
            rules = ["top-level field always present", "int64[P_batch,2] only for exact joint layout", "null when joint index space unavailable", "never use 0 or -1 placeholder"]
            missing = "null means JOINT_INDEX_SPACE_UNAVAILABLE without segment remap failure"
        fields.append({"field_name": name, "container_kind": kind, "dtype": dtype, "rank": rank, "logical_shape": shape, "axes": axes, "presence": presence, "nullability": nullable, "missing_semantics": missing, "validation_rules": rules, "authority": "deterministic exact remap contract output"})
    return {"schema_version": _OUTPUT_SCHEMA, "field_order": list(names), "fields": fields, "joint_field_normalization": {"field_always_present": True, "exact_layout_value": "int64[P_batch,2]", "unavailable_value": None, "exact_status": "REMAPPED_EXACT", "unavailable_status": "JOINT_INDEX_SPACE_UNAVAILABLE", "segment_success_preserved_when_unavailable": True}, "numeric_placeholder_semantics": {"sentinel_placeholder_usage_forbidden": True, "valid_zero_index_allowed": True, "negative_index_allowed": False, "missing_numeric_entry_is_omitted": True, "joint_unavailable_representation": None}, "adapter_implemented": False}


def _status_csv() -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(("status_code", "status", "scope", "is_success", "is_nonmember", "is_hard_failure", "numeric_output_allowed", "overall_status_allowed", "description"))
    for code, row in enumerate(_STATUS_ROWS):
        writer.writerow((code, row[0], row[1], str(row[2]).lower(), str(row[3]).lower(), str(row[4]).lower(), str(row[5]).lower(), str(row[6]).lower(), row[7]))
    return buffer.getvalue().encode("utf-8")


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


def _manifest(runtime: list[dict[str, object]], source: dict[str, object], projection_records: list[dict[str, object]]) -> dict[str, object]:
    invariants = [
        "valid source pair binds exactly one source sample", "batch numeric output binds exactly one batch sample", "duplicate source sample fails", "duplicate batch sample fails", "role, path, SHA256, row count, and row order all match", "source row is in range", "source atom composite identity matches", "source to parser mapping is exact-one", "explicit hydrogen target cannot be valid", "unsupported or invalid sample cannot be valid", "pocket and ligand cannot cross samples", "pocket and ligand roles cannot be exchanged", "parser counts equal actual role lengths", "role offsets are exclusive prefix sums of actual lengths", "offsets are monotonic and terminate at flat buffer length", "segment index is in role-specific range", "membership mask equals pair batch-sample ordinal", "joint index is generated only for the exact layout", "joint index is in joint range", "invalid, missing, or duplicate input produces no valid numeric output", "distance and coordinates never participate in selection", "feature vectors, logits, and candidate labels never participate in selection", "shuffle changes only batch order and offsets, never identity or local index", "remap changes no Task2 authority and authorizes no model or loss", "distributed sampler indices are rank-local only", "padding is excluded from node offsets", "empty valid-pair segment fails", "ragged P greater than one is supported", "non-source batch sample may have zero pairs", "source sample outside batch uses NOT_IN_BATCH",
    ]
    lineage = {"projection_instance_builder": {"module_relative_path": _PROJECTION_MODULE, "module_SHA256": _PROJECTION_MODULE_SHA, "commit": _PROJECTION_COMMIT, "projection_digest": _PROJECTION_DIGEST, "Exact2_SHA256": _PROJECTION_EXACT2}, "payload_builder": {"module_relative_path": _PAYLOAD_MODULE, "module_SHA256": _PAYLOAD_MODULE_SHA, "commit": _PAYLOAD_COMMIT, "payload_digest": _PAYLOAD_DIGEST}, "projection_contract_gate": {"module_relative_path": _CONTRACT_MODULE, "module_SHA256": _CONTRACT_MODULE_SHA, "commit": _CONTRACT_COMMIT, "contract_digest": _CONTRACT_DIGEST}, "formal_routing_sidecar": {"canonical_relative_path": _FORMAL_RELATIVE, "readlink": _FORMAL_READLINK, "aggregate": _FORMAL_AGGREGATE, "snapshot_SHA256": _FORMAL_SNAPSHOT, "Exact4_SHA256": _FORMAL_EXACT4}, "runtime_source_code": runtime, "heavy_atom_projection_validation_matrix": {"relative_path": _MATRIX_RELATIVE, "SHA256": _MATRIX_SHA}, "source_atom_tables": projection_records, "non_runtime_lineage": {"relative_path": _DESIGN_RELATIVE, "SHA256": _DESIGN_SHA, "runtime_dependency": False, "contract_authority": False}}
    return {"schema_version": _SCHEMA, "source_lineage": lineage, "current11_source_contract": source, "index_space_definitions": [{"name": "source_atom_table_data_row_index", "base": 0, "scope": "exact CSV path, bytes, and physical data-row order; header excluded"}, {"name": "parser_sample_local_index", "base": 0, "scope": "single sample and role retained-heavy buffer; retained earlier-row count"}, {"name": "collated_batch_segment_index", "base": 0, "scope": "independent ligand or pocket flat buffer in actual batch order", "formula": "role_offset[batch_sample_index] + parser_local_index"}, {"name": "dynamics_joint_global_node_index", "base": 0, "scope": f"only {_JOINT_LAYOUT}", "ligand_formula": "ligand_segment_index", "pocket_formula": "N_lig + pocket_segment_index"}], "join_contract": {"name": _JOIN, "required_composite_binding": {"sample_identity": ["sample_index_row_id", "sample_preparation_input_id", "pdb_id", "ligand_comp_id_or_expected_het_id"], "role": ["pocket", "ligand", "not_exchangeable"], "source_table": ["root_kind", "relative_path", "SHA256", "row_count", "row_order_digest_or_version", "source_row_index_0based"], "atom_identity": ["atom_site_id", "atom_name", "type_symbol", "residue_name_or_ligand_comp_id", "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id"], "parser": ["parser_schema_version", "parser_output_atom_count", "exact_parser_local_index"]}, "coordinates": "debug_consistency_only", "forbidden_selection": ["distance", "feature vector", "model logit", "candidate label", "warhead type", "reaction family", "RDKit index", "atom-map number"], "all_required_bindings_must_match": True, "single_field_fallback_forbidden": True}, "batch_semantics": {"actual_batch_order_controls_offsets": True, "ligand_and_pocket_flat_spaces_independent": True, "membership_masks_are_batch_ordinals": True, "canonical_collate_node_padding": False, "distributed_scope": "rank_local_only"}, "joint_layout_semantics": {"descriptor": _JOINT_LAYOUT, "conditional": True, "unknown_layout_fails_closed": True, "unknown_head_generalization_forbidden": True}, "status_semantics": {"closed_status_count": 18, "overall_success": "REMAPPED_EXACT", "not_in_batch_is_overall_failure": False, "joint_unavailable_is_segment_failure": False, "failure_reason_vocabulary": ["NONE", *_HARD_FAILURES], "success_failure_reason": "NONE", "hard_failure_reason": "deterministic_first_hard_failure_status", "source_entry_outcomes_align_full_source_P": True}, "fail_closed_invariants": invariants, "checkpoint_compatibility": {"checkpoint_state_dict_change_required": False, "base_model_parameter_shape_change_required": False, "base_atom_feature_width_change_required": False, "egnn_or_se3_backbone_change_required": False}, "auxiliary_module_scope": {"recommended_data_flow": ["projection instance", "future pure batch-remap sidecar", "future target-residue condition adapter or pair head"], "directly_advanced": ["target_residue_atom_condition_adapter", "covalent_pair_prediction_head"], "not_ready": {"role_mask_anchor_encoding": "primary role authority incomplete", "pre_post_geometry_prediction_head": "authoritative pre/post state missing", "covalent_pair_contrastive_loss": "negative sampling and loss authorization missing"}}, "artifact_names": list(_ARTIFACT_NAMES), "stable_artifact_names": list(_STABLE_NAMES), "readiness": _readiness()}


def _readiness() -> dict[str, bool]:
    return {"task2_batch_index_remap_contract_gate_implemented": True, "task2_batch_index_remap_contract_gate_passed": True, "task2_batch_index_remap_contract_designed": True, "source_row_to_parser_local_mapping_deterministic": True, "parser_local_to_batch_segment_mapping_deterministic": True, "batch_segment_to_joint_global_mapping_available": True, "public_batch_index_remap_adapter_implemented": False, "remap_instance_materialized": False, "torch_tensor_materialized": False, "numpy_artifact_materialized": False, "ready_for_task2_batch_index_remap_adapter_implementation": True, "ready_for_dataloader_integration": False, "ready_for_model_integration": False, "ready_for_loss_integration": False, "feature_semantics_reaudit_required_before_training": True, "ready_for_training": False}


def _validate_artifact(name: str, payload: bytes) -> None:
    if type(payload) is not bytes or not payload or len(payload) >= 1024 * 1024 or payload.startswith(b"\xef\xbb\xbf") or b"\0" in payload or b"\r" in payload or not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        _fail()
    if name.endswith(".json") and _json(_strict_json(payload)) != payload:
        _fail()


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    canonical = state / _FORMAL_RELATIVE
    before = _formal_snapshot(canonical)
    if before.get("readlink") != _FORMAL_READLINK:
        _fail()
    _read_regular(repo, _PROJECTION_MODULE, _PROJECTION_MODULE_SHA)
    _read_regular(repo, _PAYLOAD_MODULE, _PAYLOAD_MODULE_SHA)
    _read_regular(repo, _CONTRACT_MODULE, _CONTRACT_MODULE_SHA)
    exact2, instance, predecessor_report = _projection_exact2(repo, state)
    del exact2
    runtime = _runtime_inventory(repo)
    source = _source_contract(instance)
    projection_records, evaluator_tables = _projection_records(repo, instance)
    canonical_input = _reference_input(list(range(11)), evaluator_tables)
    reverse_input = _reference_input(list(reversed(range(11))), evaluator_tables)
    mixed_input = _reference_input([10, 4, 0, 7, 2], evaluator_tables)
    subset_input = _reference_input([10, 4, 0], evaluator_tables)
    no_joint_input = _reference_input(list(range(11)), evaluator_tables, joint=None)
    synthetic_input = _synthetic_case()
    synthetic_authority = _synthetic_authority()
    canonical_output = _evaluate_reference_case(canonical_input, authoritative_tables=evaluator_tables)
    reverse_output = _evaluate_reference_case(reverse_input, authoritative_tables=evaluator_tables)
    mixed_output = _evaluate_reference_case(mixed_input, authoritative_tables=evaluator_tables)
    subset_output = _evaluate_reference_case(subset_input, authoritative_tables=evaluator_tables)
    no_joint_output = _evaluate_reference_case(no_joint_input, authoritative_tables=evaluator_tables)
    synthetic_output = _evaluate_reference_case(synthetic_input, authoritative_tables=synthetic_authority)
    outputs = (canonical_output, reverse_output, mixed_output, subset_output, no_joint_output, synthetic_output)
    if any(output.get("remap_status") != "REMAPPED_EXACT" for output in outputs) or no_joint_output.get("pair_values_joint_global_indices") is not None or no_joint_output["provenance"].get("joint_index_status") != "JOINT_INDEX_SPACE_UNAVAILABLE" or synthetic_output.get("sample_pair_offsets") != [0, 1, 3, 3]:
        _fail()
    vectors = {"schema_version": _REFERENCE_SCHEMA, "source_contract": source, "exact22_source_to_local": projection_records, "canonical_exact11_batch_reference": {"batch_contract": _batch_contract(canonical_input), "output": canonical_output}, "permutation_reference_cases": [{"case_name": "reversed_exact11", "source_sample_indices": list(reversed(range(11))), "batch_contract": _batch_contract(reverse_input), "output": reverse_output}, {"case_name": "mixed_permutation", "source_sample_indices": [10, 4, 0, 7, 2], "batch_contract": _batch_contract(mixed_input), "output": mixed_output}], "subset_reference_cases": [{"case_name": "subset_10_4_0", "source_sample_indices": [10, 4, 0], "batch_contract": _batch_contract(subset_input), "output": subset_output}], "no_joint_layout_reference_case": {"joint_layout_descriptor": None, "batch_contract": _batch_contract(no_joint_input), "output": no_joint_output}, "synthetic_future_p_gt_1_reference_case": {"source_pair_counts_by_sample": [2, 0, 1], "source_sample_offsets_int64": [0, 2, 2, 3], "batch_source_sample_order": [2, 0, 1], "batch_contract": _batch_contract(synthetic_input), "output": synthetic_output}, "reference_case_semantics": {"canonical_exact11_batch_reference_only": True, "future_batch_values_must_be_recomputed": True, "hardcode_as_runtime_output_forbidden": True, "reference_contract_evaluator_only": True, "public_adapter_implemented": False, "model_integration_authorized": False, "loss_authorized": False}}
    stable_values = (_manifest(runtime, source, projection_records), _input_schema_artifact(), _output_schema_artifact(), None, vectors)
    artifacts: dict[str, bytes] = {}
    for name, value in zip(_STABLE_NAMES, stable_values):
        artifacts[name] = _status_csv() if name == _VOCABULARY else _json(value)
    digest = _stable_digest(artifacts)
    identities = [{"artifact_index": index, "artifact_name": name, "stable_digest_participation": True, "bytes": len(artifacts[name]), "LF": artifacts[name].count(b"\n"), "SHA256": _sha(artifacts[name])} for index, name in enumerate(_STABLE_NAMES)]
    identities.append({"artifact_index": 5, "artifact_name": _REPORT, "stable_digest_participation": False, "content_identity": "self_excluded"})
    report = {"schema_version": _REPORT_SCHEMA, "gate_status": _STATUS, "contract_digest": digest, "artifact_file_count": 6, "artifact_identities": identities, "projection_instance_builder_passed": True, "projection_instance_digest": _PROJECTION_DIGEST, "projection_exact2_double_build_identical": True, "payload_builder_passed": True, "payload_bundle_digest": _PAYLOAD_DIGEST, "projection_contract_gate_passed": True, "projection_contract_digest": _CONTRACT_DIGEST, "formal_sidecar_check_passed": predecessor_report.get("formal_sidecar_check_passed") is True, "formal_snapshot_unchanged": predecessor_report.get("formal_snapshot_unchanged") is True, "runtime_source_identity_count": len(runtime), "runtime_semantic_anchor_count": sum(len(row["semantic_anchors"]) for row in runtime), "source_atom_table_count": 22, "source_pair_count": 11, "source_to_parser_local_valid_count": 22, "canonical_reference_case_passed": True, "permutation_reference_case_count": 2, "subset_reference_case_count": 1, "no_joint_reference_case_passed": True, "synthetic_p_gt_1_reference_case_passed": True, "status_vocabulary_count": 18, "fail_closed_invariant_count": len(_manifest(runtime, source, projection_records)["fail_closed_invariants"]), "readiness": _readiness()}
    artifacts[_REPORT] = _json(report)
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES or len(artifacts) != 6:
        _fail()
    for name, payload in artifacts.items():
        _validate_artifact(name, payload)
    after = _formal_snapshot(canonical)
    if before != after:
        _fail()
    return artifacts


def build_covapie_current11_task2_batch_index_remap_contract_gate_v1(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    """Return the deterministic contract Exact6 in memory without writing files."""
    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
