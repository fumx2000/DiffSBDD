#!/usr/bin/env python3
"""Independently check the CovaPIE training atom-policy resolution V1."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as resolution,
)

BASE = "5b2013281b03d7bd3e0c59b9985e52494263c69f"
STAGE = "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PREDECESSOR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1"
)
PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1.py"
)
PREDECESSOR_MANIFEST = PREDECESSOR_ROOT / (
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_"
    "audit_manifest.json"
)
PREDECESSOR_ISSUES = (
    PREDECESSOR_ROOT / "covapie_feature_semantics_issue_readiness_inventory.csv"
)
PREDECESSOR_REGISTRY = (
    PREDECESSOR_ROOT / "covapie_training_feature_semantics_registry.csv"
)
PREDECESSOR_UNKNOWN = (
    PREDECESSOR_ROOT / "covapie_unknown_atom_policy_audit_matrix.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
PAIR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1"
)
PAIR_MATRIX = PAIR_ROOT / (
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
PAIR_MANIFEST = PAIR_ROOT / (
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_manifest.json"
)

SOURCE_FILE = (
    OUTPUT_ROOT / "covapie_unknown_atom_resolution_source_inventory.csv"
)
DISPOSITION_FILE = OUTPUT_ROOT / (
    "covapie_heavy_atom_disposition_and_index_projection_matrix.csv"
)
SAMPLE_FILE = OUTPUT_ROOT / (
    "covapie_sample_heavy_atom_projection_validation_matrix.csv"
)
FAILURE_FILE = (
    OUTPUT_ROOT / "covapie_unknown_atom_policy_resolution_failure_matrix.csv"
)
ISSUE_FILE = OUTPUT_ROOT / (
    "covapie_unknown_atom_policy_resolution_issue_readiness_inventory.csv"
)
MANIFEST_FILE = OUTPUT_ROOT / (
    "covapie_training_feature_semantics_and_unknown_atom_policy_"
    "resolution_manifest.json"
)

EXACT10 = (
    Path(
        "src/covalent_ext/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_training_feature_semantics_and_unknown_atom_policy_"
        "resolution_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_training_feature_semantics_and_unknown_atom_policy_"
        "resolution_v1.py"
    ),
    Path(
        "docs/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_"
        "resolution_v1_summary.md"
    ),
    SOURCE_FILE,
    DISPOSITION_FILE,
    SAMPLE_FILE,
    FAILURE_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)

FROZEN = {
    PREDECESSOR_SOURCE: "30dcd94500fa5acc40a566072b80df9f1383b326778eb1ce7e5709819a7c57ad",
    PREDECESSOR_MANIFEST: "8e9aa9e853556715f1f6920b6bb80c1aa0ab22344b4118ba63f988d0ae659dbe",
    PREDECESSOR_ISSUES: "38469f4d1fff515b47d47463bd085844e64109aed3875723710776e4f36c7128",
    PREDECESSOR_REGISTRY: "820e0abaa8dad761d66950ee85b3ba0f0078448ca33180c29c9238572a91995f",
    PREDECESSOR_UNKNOWN: "f6aeeb1528563429652a4ab8441d785547b0a44385c628448c04e18a99b4c5bd",
    FINAL_INDEX: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    PAIR_MATRIX: "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    PAIR_MANIFEST: "229f5430feb3b5c147edce6c80dce684703b614e3764c7c18afd8344c25c3152",
}
CHANNELS = {
    "C": 0,
    "N": 1,
    "O": 2,
    "S": 3,
    "B": 4,
    "Br": 5,
    "Cl": 6,
    "P": 7,
    "I": 8,
    "F": 9,
}
ATOMIC_CHANNELS = {
    6: 0,
    7: 1,
    8: 2,
    16: 3,
    5: 4,
    35: 5,
    17: 6,
    15: 7,
    53: 8,
    9: 9,
}
CHANNEL_ORDER = "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
LEGAL_ELEMENT = re.compile(r"^[A-Z][a-z]?$")
EXPECTED_COUNTS = {
    "source_atom_row_count": 2870,
    "protein_source_row_count": 2531,
    "ligand_source_row_count": 339,
    "excluded_explicit_hydrogen_row_count": 345,
    "protein_excluded_hydrogen_row_count": 329,
    "ligand_excluded_hydrogen_row_count": 16,
    "retained_heavy_atom_row_count": 2525,
    "protein_retained_heavy_row_count": 2202,
    "ligand_retained_heavy_row_count": 323,
    "unsupported_nonhydrogen_row_count": 0,
    "missing_or_invalid_symbol_row_count": 0,
}
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".npz", ".tar", ".zip",
    ".tgz", ".tmp", ".part",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _git(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"git failed: {args!r}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def _base(path: Path) -> bytes:
    name = path.as_posix()
    _require(not name.startswith("data/raw/"), "raw read attempted")
    _require(path.suffix.lower() not in FORBIDDEN_SUFFIXES, "artifact read attempted")
    _git("cat-file", "-e", f"{BASE}:{name}")
    return _git("show", f"{BASE}:{name}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _object(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    _require(isinstance(value, dict), "JSON root is not an object")
    return value


def _read_output(path: Path) -> bytes:
    target = ROOT / path
    _require(target.is_file(), f"output missing: {path}")
    _require(not target.is_symlink(), f"output symlink forbidden: {path}")
    _require(target.stat().st_mode & 0o777 == 0o644, f"mode drift: {path}")
    _require(target.stat().st_size < 100 * 1024 * 1024, f"oversize: {path}")
    return target.read_bytes()


def _classify_type_symbol_independent(type_symbol: object) -> str:
    if type(type_symbol) is not str:
        return "missing_or_invalid"
    if not type_symbol or type_symbol.strip() != type_symbol:
        return "missing_or_invalid"
    if type_symbol == "H":
        return "explicit_hydrogen"
    if type_symbol in CHANNELS:
        return "supported_checkpoint_heavy_atom"
    if LEGAL_ELEMENT.fullmatch(type_symbol) is None:
        return "missing_or_invalid"
    return "unsupported_nonhydrogen"


def _literal_assignment(payload: bytes, name: str) -> Any:
    tree = ast.parse(payload.decode("utf-8"))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"literal assignment missing: {name}")


def _dataset_assignment(payload: bytes, key: str) -> dict[str, Any]:
    tree = ast.parse(payload.decode("utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id == "dataset_params"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == key
        ):
            value = ast.literal_eval(node.value)
            _require(isinstance(value, dict), "dataset assignment is not dict")
            return value
    raise AssertionError(f"dataset assignment missing: {key}")


def _classification_helper_uses_only_type_symbol(path: Path) -> bool:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "classify_type_symbol_v1"
    ]
    if len(functions) != 1:
        return False
    function = functions[0]
    if [argument.arg for argument in function.args.args] != ["type_symbol"]:
        return False
    for node in ast.walk(function):
        if isinstance(node, ast.Name) and node.id == "atom_name":
            return False
        if isinstance(node, ast.Constant) and node.value == "atom_name":
            return False
    return True


def _verify_lineage() -> None:
    config = _base(Path("configs/crossdock_fullatom_cond.yml")).decode("utf-8")
    for fragment in (
        "dataset: 'crossdock'",
        "processed_crossdock_noH_full",
        "pocket_representation: 'full-atom'",
        "normalize_factors: [1, 4]",
    ):
        _require(fragment in config, f"checkpoint config drift: {fragment}")
    constants = _base(Path("constants.py"))
    checkpoint = _dataset_assignment(constants, "crossdock")
    preview = _dataset_assignment(constants, "crossdock_full")
    _require(checkpoint.get("atom_encoder") == CHANNELS, "10D constants drift")
    _require(
        preview.get("atom_encoder") == {**CHANNELS, "others": 10},
        "11D constants drift",
    )
    preview_source = _base(Path("src/covalent_ext/diffsbdd_input_adapter.py"))
    _require(
        _literal_assignment(preview_source, "ATOM_ENCODER_CROSSDOCK_FULL")
        == {**CHANNELS, "others": 10},
        "preview adapter vocabulary drift",
    )
    smoke = _base(
        Path("src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py")
    )
    _require(
        _literal_assignment(smoke, "CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX")
        == ATOMIC_CHANNELS,
        "checkpoint smoke channel drift",
    )
    smoke_text = smoke.decode("utf-8")
    for fragment in (
        "torch.zeros((len(flat_numbers), len(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX))",
        "feature_idx = CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX.get(int(value))",
        "if feature_idx is None:",
        "one_hot[row_idx, feature_idx] = 1.0",
        'input_contract.get("target_ligand_feature_dim", 0)',
        'input_contract.get("target_pocket_feature_dim", 0)',
        "target_ligand_dim != 10 or target_pocket_dim != 10",
    ):
        _require(fragment in smoke_text, f"checkpoint smoke behavior drift: {fragment}")
    _require(
        _classification_helper_uses_only_type_symbol(EXACT10[0]),
        "classification helper reads atom-name semantics",
    )


def _verify_predecessor() -> dict[Path, bytes]:
    payloads = {path: _base(path) for path in FROZEN}
    for path, expected in FROZEN.items():
        _require(_sha(payloads[path]) == expected, f"frozen SHA drift: {path}")
    manifest = _object(payloads[PREDECESSOR_MANIFEST])
    expected = {
        "feature_semantics_audit_completed": True,
        "audit_outcome": "audited_with_blockers",
        "all_current_model_input_semantics_frozen": True,
        "protein_unknown_atom_policy": "unknown_atom_policy_unresolved",
        "ligand_unknown_atom_policy": "unknown_atom_policy_unresolved",
        "unknown_atom_feature_policy_resolved": False,
        "feature_semantics_known": False,
        "effective_open_issue_count": 1,
        "effective_open_issues": ["UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED"],
        "checkpoint_compatibility_preserved": True,
        "ready_for_tensor_label_loss_mask_contract_design": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
    }
    for key, value in expected.items():
        _require(manifest.get(key) == value, f"predecessor field drift: {key}")
    issues = _rows(payloads[PREDECESSOR_ISSUES])
    _require(len(issues) == 32, "predecessor issue count drift")
    _require(
        [
            row["issue_id"]
            for row in issues
            if row["successor_effective_status"] == "open"
        ]
        == ["UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED"],
        "predecessor open issue set drift",
    )
    return payloads


def _recompute_atom_projection(
    payloads: dict[Path, bytes],
) -> tuple[
    list[dict[str, str]],
    dict[tuple[str, str], dict[str, Any]],
    dict[Path, bytes],
    dict[Path, list[dict[str, str]]],
    dict[str, int],
]:
    final_rows = _rows(payloads[FINAL_INDEX])
    _require(len(final_rows) == 11, "canonical sample count drift")
    projections: dict[tuple[str, str], dict[str, Any]] = {}
    table_payloads: dict[Path, bytes] = {}
    table_rows: dict[Path, list[dict[str, str]]] = {}
    counts = {
        "source_atom_row_count": 0,
        "protein_source_row_count": 0,
        "ligand_source_row_count": 0,
        "excluded_explicit_hydrogen_row_count": 0,
        "protein_excluded_hydrogen_row_count": 0,
        "ligand_excluded_hydrogen_row_count": 0,
        "retained_heavy_atom_row_count": 0,
        "protein_retained_heavy_row_count": 0,
        "ligand_retained_heavy_row_count": 0,
        "unsupported_nonhydrogen_row_count": 0,
        "missing_or_invalid_symbol_row_count": 0,
    }
    for sample in final_rows:
        for domain, column in (
            ("protein_or_pocket_atom", "pocket_atom_table_path"),
            ("ligand_atom", "ligand_atom_table_path"),
        ):
            path = Path(sample[column])
            _require(path not in table_payloads, "duplicate atom table")
            payload = _base(path)
            rows = _rows(payload)
            table_payloads[path] = payload
            table_rows[path] = rows
            classes = tuple(
                _classify_type_symbol_independent(row.get("type_symbol"))
                for row in rows
            )
            rejected = any(
                value in {"unsupported_nonhydrogen", "missing_or_invalid"}
                for value in classes
            )
            next_index = 0
            mapping: list[int | None] = []
            channels: list[int | None] = []
            for row, symbol_class in zip(rows, classes):
                counts["source_atom_row_count"] += 1
                prefix = "protein" if domain == "protein_or_pocket_atom" else "ligand"
                counts[f"{prefix}_source_row_count"] += 1
                if symbol_class == "explicit_hydrogen":
                    counts["excluded_explicit_hydrogen_row_count"] += 1
                    counts[f"{prefix}_excluded_hydrogen_row_count"] += 1
                    mapping.append(None)
                    channels.append(None)
                elif symbol_class == "supported_checkpoint_heavy_atom":
                    counts["retained_heavy_atom_row_count"] += 1
                    counts[f"{prefix}_retained_heavy_row_count"] += 1
                    mapping.append(next_index)
                    channels.append(CHANNELS[row["type_symbol"]])
                    next_index += 1
                elif symbol_class == "unsupported_nonhydrogen":
                    counts["unsupported_nonhydrogen_row_count"] += 1
                    mapping.append(None)
                    channels.append(None)
                else:
                    counts["missing_or_invalid_symbol_row_count"] += 1
                    mapping.append(None)
                    channels.append(None)
            projections[(sample["sample_index_row_id"], domain)] = {
                "path": path,
                "rows": rows,
                "classes": classes,
                "mapping": tuple(mapping),
                "channels": tuple(channels),
                "rejected": rejected,
            }
    _require(len(table_payloads) == 22, "atom table count drift")
    _require(counts == EXPECTED_COUNTS, f"independent counts drift: {counts!r}")
    return final_rows, projections, table_payloads, table_rows, counts


def _verify_disposition(
    final_rows: list[dict[str, str]],
    projections: dict[tuple[str, str], dict[str, Any]],
    table_payloads: dict[Path, bytes],
) -> None:
    actual = _rows(_read_output(DISPOSITION_FILE))
    _require(len(actual) == 2870, "disposition row count drift")
    offset = 0
    identities: set[tuple[str, str, str]] = set()
    for sample in final_rows:
        for domain in ("protein_or_pocket_atom", "ligand_atom"):
            projection = projections[(sample["sample_index_row_id"], domain)]
            rows = projection["rows"]
            mapping = projection["mapping"]
            channels = projection["channels"]
            for source_index, (source, symbol_class) in enumerate(
                zip(rows, projection["classes"])
            ):
                row = actual[offset]
                offset += 1
                expected_identity = (
                    sample["sample_index_row_id"],
                    domain,
                    str(source_index),
                )
                _require(expected_identity not in identities, "duplicate disposition identity")
                identities.add(expected_identity)
                _require(
                    (
                        row["sample_index_row_id"],
                        row["domain"],
                        row["source_atom_row_index_0based"],
                    )
                    == expected_identity,
                    "disposition identity/order drift",
                )
                _require(
                    row["source_table_path"] == projection["path"].as_posix(),
                    "disposition table path drift",
                )
                _require(
                    row["source_table_sha256"]
                    == _sha(table_payloads[projection["path"]]),
                    "disposition table SHA drift",
                )
                _require(row["type_symbol"] == source.get("type_symbol", ""), "type symbol drift")
                _require(row["symbol_class"] == symbol_class, "symbol class drift")
                retained = symbol_class == "supported_checkpoint_heavy_atom"
                _require(_truth(row["retained_for_checkpoint_model"]) == retained, "retention drift")
                expected_mapping = "" if mapping[source_index] is None else str(mapping[source_index])
                expected_channel = "" if channels[source_index] is None else str(channels[source_index])
                _require(
                    row["projected_heavy_atom_row_index_0based"] == expected_mapping,
                    "projected index drift",
                )
                _require(row["checkpoint_channel_index"] == expected_channel, "channel drift")
                _require(not _truth(row["sample_rejected"]), "current sample rejected")
                for field in (
                    "excluded_before_centering",
                    "excluded_before_node_count",
                    "excluded_before_batch_membership",
                    "excluded_before_mask_projection",
                    "excluded_before_pair_index_projection",
                ):
                    _require(_truth(row[field]) == (not retained), f"{field} drift")
                _require(_truth(row["verified"]), "disposition unverified")


def _verify_samples(
    final_rows: list[dict[str, str]],
    projections: dict[tuple[str, str], dict[str, Any]],
    payloads: dict[Path, bytes],
) -> None:
    pair_rows = _rows(payloads[PAIR_MATRIX])
    _require(len(pair_rows) == 22, "pair matrix count drift")
    by_sample: dict[str, dict[str, dict[str, str]]] = {}
    for row in pair_rows:
        by_sample.setdefault(row["sample_index_row_id"], {})[row["entity_role"]] = row
    actual = _rows(_read_output(SAMPLE_FILE))
    _require(len(actual) == 11, "sample projection count drift")
    for sample, row in zip(final_rows, actual):
        sample_id = sample["sample_index_row_id"]
        _require(row["sample_index_row_id"] == sample_id, "sample projection order drift")
        pocket = projections[(sample_id, "protein_or_pocket_atom")]
        ligand = projections[(sample_id, "ligand_atom")]
        residue_source = int(
            by_sample[sample_id]["target_residue_atom"]["matched_row_index_0based"]
        )
        ligand_source = int(
            by_sample[sample_id]["ligand_atom"]["matched_row_index_0based"]
        )
        residue_projected = pocket["mapping"][residue_source]
        ligand_projected = ligand["mapping"][ligand_source]
        _require(residue_projected is not None, "residue pair atom excluded")
        _require(ligand_projected is not None, "ligand pair atom excluded")
        expected = {
            "source_residue_pair_row_index_0based": str(residue_source),
            "projected_residue_pair_row_index_0based": str(residue_projected),
            "source_ligand_pair_row_index_0based": str(ligand_source),
            "projected_ligand_pair_row_index_0based": str(ligand_projected),
            "residue_pair_atom_type_symbol": pocket["rows"][residue_source]["type_symbol"],
            "ligand_pair_atom_type_symbol": ligand["rows"][ligand_source]["type_symbol"],
            "checkpoint_width_after_projection": "10",
            "centering_node_set": "retained_ligand_plus_pocket_heavy_atoms",
            "sample_policy_outcome": "passed",
        }
        for key, value in expected.items():
            _require(row[key] == value, f"sample projection drift: {key}")
        for key in (
            "retained_pocket_nonempty",
            "retained_ligand_nonempty",
            "residue_pair_atom_retained",
            "ligand_pair_atom_retained",
            "pair_projection_exact_one",
            "projected_pocket_indices_contiguous",
            "projected_ligand_indices_contiguous",
            "source_order_preserved",
            "hydrogen_filter_before_centering",
            "verified",
        ):
            _require(_truth(row[key]), f"sample projection false: {key}")
        pocket_indices = [value for value in pocket["mapping"] if value is not None]
        ligand_indices = [value for value in ligand["mapping"] if value is not None]
        _require(pocket_indices == list(range(len(pocket_indices))), "pocket index discontinuity")
        _require(ligand_indices == list(range(len(ligand_indices))), "ligand index discontinuity")


def _verify_source_inventory(
    table_payloads: dict[Path, bytes],
) -> None:
    rows = _rows(_read_output(SOURCE_FILE))
    _require(len(rows) >= 42, "source inventory incomplete")
    paths = [Path(row["source_path"]) for row in rows]
    required = {
        PREDECESSOR_SOURCE,
        PREDECESSOR_MANIFEST,
        PREDECESSOR_REGISTRY,
        PREDECESSOR_UNKNOWN,
        PREDECESSOR_ISSUES,
        FINAL_INDEX,
        PAIR_MATRIX,
        PAIR_MANIFEST,
        Path("configs/crossdock_fullatom_cond.yml"),
        Path("constants.py"),
        Path("process_crossdock.py"),
        Path("dataset.py"),
        Path("src/covalent_ext/diffsbdd_input_adapter.py"),
        Path("src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py"),
        Path("src/covalent_ext/npz_dataset.py"),
        Path("src/covalent_ext/batch_adapter.py"),
        Path("src/covalent_ext/model_input_adapter.py"),
    } | set(table_payloads)
    _require(required.issubset(set(paths)), "source inventory required path missing")
    for row in rows:
        path = Path(row["source_path"])
        payload = _base(path)
        _require(_sha(payload) == row["source_sha256"], f"inventory SHA drift: {path}")
        _require(_truth(row["committed_in_base"]), "inventory source not BASE committed")
        _require(_truth(row["verified"]), "inventory source unverified")


def _verify_issue_transition(payloads: dict[Path, bytes]) -> None:
    before = _rows(payloads[PREDECESSOR_ISSUES])
    after = _rows(_read_output(ISSUE_FILE))
    _require(len(before) == len(after) == 32, "issue row count drift")
    mutable = {
        "successor_effective_status",
        "successor_transition_stage",
        "successor_transition_action",
        "successor_transition_evidence",
    }
    for index, (old, new) in enumerate(zip(before, after)):
        _require(
            old["inherited_order"] == new["inherited_order"]
            and old["issue_id"] == new["issue_id"],
            "issue identity/order drift",
        )
        if old["issue_id"] != "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED":
            _require(old == new, f"non-unknown issue modified at row {index}")
        else:
            for key in old:
                if key not in mutable:
                    _require(old[key] == new[key], f"unknown issue field changed: {key}")
            _require(new["successor_effective_status"] == "resolved", "unknown issue unresolved")
            _require(new["successor_transition_stage"] == STAGE, "transition stage drift")
            _require(
                new["successor_transition_action"]
                == "resolved_by_explicit_hydrogen_exclusion_and_fail_closed_nonhydrogen_policy_v1",
                "transition action drift",
            )
            for fragment in (
                "2870/2870 rows classified",
                "345 explicit H rows excluded",
                "2525 supported heavy rows retained",
                "11/11 covalent atom pairs retained and reindexed",
                "checkpoint width remains 10",
                "runtime integration deferred to tensor contract",
            ):
                _require(
                    fragment in new["successor_transition_evidence"],
                    f"transition evidence missing: {fragment}",
                )
    _require(
        after[30]["issue_id"] == "FINAL_TRAINING_FEATURE_SEMANTICS_UNRESOLVED"
        and after[30] == before[30],
        "final feature-semantics issue row changed",
    )


def _verify_failure_matrix() -> None:
    actual = _read_output(FAILURE_FILE)
    expected_rows = resolution.build_failure_matrix_rows_v1()
    _require(len(expected_rows) == 32, "formal failure case count drift")
    parsed = _rows(actual)
    _require(
        [row["failure_case"] for row in parsed]
        == list(resolution.FAILURE_CASES),
        "failure case identity/order drift",
    )
    for row in parsed:
        _require(row["observed_outcome"] == "invalid", "failure did not invalidate")
        _require(not _truth(row["unknown_atom_policy_contract_resolved"]), "failure resolved policy")
        _require(not _truth(row["feature_semantics_known"]), "failure knew semantics")
        _require(
            not _truth(row["ready_for_tensor_label_loss_mask_contract_design"]),
            "failure allowed contract design",
        )
        _require(not _truth(row["ready_for_tensorization"]), "failure allowed tensorization")
        _require(not _truth(row["ready_for_model_integration"]), "failure allowed integration")
        _require(not _truth(row["ready_for_training"]), "failure allowed training")
        _require(row["unknown_issue_effective_status"] == "open", "failure closed issue")
        _require(_truth(row["fails_closed"]) and _truth(row["verified"]), "failure not verified")


def _verify_manifest(
    counts: dict[str, int],
    output_payloads: dict[Path, bytes],
) -> dict[str, Any]:
    manifest = _object(output_payloads[MANIFEST_FILE])
    expected = {
        "schema_version": STAGE,
        "base_commit": BASE,
        "policy_resolution_completed": True,
        "resolution_outcome": "resolved_policy_contract",
        **counts,
        "protein_unknown_atom_policy": "fail_closed_rejection_required_for_checkpoint_compatibility",
        "ligand_unknown_atom_policy": "fail_closed_rejection_required_for_checkpoint_compatibility",
        "explicit_hydrogen_handling": "exclude_before_checkpoint_model_projection",
        "unsupported_nonhydrogen_handling": "reject_sample_fail_closed",
        "checkpoint_categorical_width": 10,
        "checkpoint_channel_order": CHANNEL_ORDER,
        "checkpoint_channel_order_preserved": True,
        "preview_11d_checkpoint_authority": False,
        "silent_zero_vector_fallback_allowed": False,
        "new_unknown_channel_allowed": False,
        "hydrogen_filter_before_coordinate_centering": True,
        "hydrogen_filter_before_node_count": True,
        "hydrogen_filter_before_batch_membership": True,
        "hydrogen_filter_before_mask_projection": True,
        "hydrogen_filter_before_atom_pair_index_projection": True,
        "all_atom_rows_classified": True,
        "all_sample_projections_valid": True,
        "all_pair_indices_remapped": True,
        "pair_projection_valid_count": 11,
        "feature_semantics_audit_completed": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "unknown_atom_runtime_enforcement_integrated": False,
        "effective_open_issue_count": 0,
        "effective_open_issues": [],
        "ready_for_tensor_label_loss_mask_contract_design": True,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "tensorization_used": False,
        "checkpoint_access": False,
        "model_changed": False,
        "dataloader_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "training_used": False,
        "raw_read": False,
        "raw_write": False,
        "provider_used": False,
        "network_used": False,
        "download_used": False,
        "recommended_next_step": "design_covapie_tensor_label_and_loss_mask_contract_v1",
    }
    for key, value in expected.items():
        _require(manifest.get(key) == value, f"manifest field drift: {key}")
    observed_masks = tuple(
        (row.get("semantic_name"), row.get("display_alias"))
        for row in manifest.get("canonical_masks", [])
    )
    _require(observed_masks == MASKS, "manifest canonical masks drift")
    _require(manifest.get("canonical_mask_tensors_materialized") is False, "mask tensor boundary crossed")
    evidence = manifest.get("evidence_sha256")
    _require(isinstance(evidence, dict), "manifest evidence SHA map missing")
    for path in (
        SOURCE_FILE,
        DISPOSITION_FILE,
        SAMPLE_FILE,
        FAILURE_FILE,
        ISSUE_FILE,
    ):
        _require(
            evidence.get(path.name) == _sha(output_payloads[path]),
            f"evidence SHA drift: {path.name}",
        )
    return manifest


def _verify_determinism(output_payloads: dict[Path, bytes]) -> None:
    first = (
        resolution.build_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_artifacts_v1(
            ROOT
        )
    )
    second = (
        resolution.build_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_artifacts_v1(
            ROOT
        )
    )
    _require(first == second, "independent artifact builds differ")
    _require(set(first) == {path.name for path in output_payloads}, "artifact set drift")
    for path, payload in output_payloads.items():
        _require(first[path.name] == payload, f"materialized artifact drift: {path}")
    first_result = (
        resolution.derive_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1(
            ROOT
        )
    )
    second_result = (
        resolution.derive_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1(
            ROOT
        )
    )
    _require(first_result["decision"] == second_result["decision"], "decision drift")
    _require(
        resolution.serialize_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_decision_v1(
            first_result["decision"]
        )
        == resolution.serialize_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_decision_v1(
            second_result["decision"]
        ),
        "serialized decision drift",
    )


def _verify_exact_files_and_boundaries() -> None:
    _require(len(EXACT10) == 10 and len(set(EXACT10)) == 10, "Exact10 drift")
    for path in EXACT10:
        target = ROOT / path
        _require(target.is_file() and not target.is_symlink(), f"Exact10 invalid: {path}")
        _require(path.suffix.lower() not in FORBIDDEN_SUFFIXES, "forbidden suffix")
        _require(target.stat().st_size < 100 * 1024 * 1024, "Exact10 oversize")
    protected = (
        "data/raw",
        "checkpoints",
        "equivariant_diffusion",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    )
    _require(
        not _git("diff", "--name-only", BASE, "--", *protected).strip(),
        "protected source changed",
    )


def run_checks() -> dict[str, Any]:
    _verify_exact_files_and_boundaries()
    payloads = _verify_predecessor()
    _verify_lineage()
    (
        final_rows,
        projections,
        table_payloads,
        _table_rows,
        counts,
    ) = _recompute_atom_projection(payloads)
    _verify_disposition(final_rows, projections, table_payloads)
    _verify_samples(final_rows, projections, payloads)
    _verify_source_inventory(table_payloads)
    _verify_issue_transition(payloads)
    _verify_failure_matrix()
    output_payloads = {
        path: _read_output(path)
        for path in (
            SOURCE_FILE,
            DISPOSITION_FILE,
            SAMPLE_FILE,
            FAILURE_FILE,
            ISSUE_FILE,
            MANIFEST_FILE,
        )
    }
    manifest = _verify_manifest(counts, output_payloads)
    _verify_determinism(output_payloads)
    return manifest


def main() -> int:
    manifest = run_checks()
    report_keys = (
        "resolution_outcome",
        "source_atom_row_count",
        "retained_heavy_atom_row_count",
        "excluded_explicit_hydrogen_row_count",
        "unsupported_nonhydrogen_row_count",
        "missing_or_invalid_symbol_row_count",
        "protein_unknown_atom_policy",
        "ligand_unknown_atom_policy",
        "explicit_hydrogen_handling",
        "checkpoint_categorical_width",
        "checkpoint_channel_order_preserved",
        "preview_11d_checkpoint_authority",
        "silent_zero_vector_fallback_allowed",
        "all_atom_rows_classified",
        "all_sample_projections_valid",
        "all_pair_indices_remapped",
        "hydrogen_filter_before_coordinate_centering",
        "unknown_atom_policy_contract_resolved",
        "unknown_atom_runtime_enforcement_integrated",
        "feature_semantics_known",
        "unknown_atom_feature_policy_resolved",
        "effective_open_issue_count",
        "effective_open_issues",
        "ready_for_tensor_label_loss_mask_contract_design",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
        "recommended_next_step",
    )
    for key in report_keys:
        value = manifest[key]
        if isinstance(value, bool):
            rendered = str(value).lower()
        elif isinstance(value, (list, dict)):
            rendered = json.dumps(value, sort_keys=True, separators=(",", ":"))
        else:
            rendered = str(value)
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
