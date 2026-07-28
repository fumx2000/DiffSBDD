"""Independent checker for the CovaPIE tensor/label/loss-mask V1 design."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import math
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_tensor_label_and_loss_mask_contract_design_v1 as contract,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "160cdbda8800a535b5c0a81d501babfae9a8615b"
OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_tensor_label_and_loss_mask_contract_design_v1"
)
EXACT10 = (
    Path("src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py"),
    Path("tests/test_covapie_tensor_label_and_loss_mask_contract_design_v1.py"),
    Path("scripts/check_covapie_tensor_label_and_loss_mask_contract_design_v1.py"),
    Path("docs/covapie_tensor_label_and_loss_mask_contract_design_v1_summary.md"),
    OUTPUT_ROOT / "covapie_tensor_label_loss_mask_source_inventory.csv",
    OUTPUT_ROOT / "covapie_tensor_label_loss_mask_contract_registry.csv",
    OUTPUT_ROOT / "covapie_pair_candidate_and_negative_policy_matrix.csv",
    OUTPUT_ROOT / "covapie_tensor_label_loss_mask_failure_matrix.csv",
    OUTPUT_ROOT / "covapie_tensor_label_loss_mask_issue_readiness_inventory.csv",
    OUTPUT_ROOT / "covapie_tensor_label_and_loss_mask_contract_design_manifest.json",
)
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".tmp", ".part",
}


def _fail(message: str) -> None:
    raise SystemExit(message)


def _git(*args: str) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        _fail(
            f"git command failed: {args!r}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def _base_bytes(path: str | Path) -> bytes:
    source = Path(path)
    name = source.as_posix()
    if name.startswith("data/raw/") or source.suffix.lower() in FORBIDDEN_SUFFIXES:
        _fail(f"forbidden BASE source requested: {name}")
    _git("cat-file", "-e", f"{BASE_COMMIT}:{name}")
    return _git("show", f"{BASE_COMMIT}:{name}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _json(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        _fail("expected JSON object")
    return value


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def _mutation_signature(fields: dict[str, Any]) -> str:
    if not fields:
        return "baseline"
    return "|".join(
        f"{name}={json.dumps(fields[name], sort_keys=True, separators=(',', ':'))}"
        for name in sorted(fields)
    )


def _read_output(name: str) -> bytes:
    return (ROOT / OUTPUT_ROOT / name).read_bytes()


def _check_base_identity() -> None:
    identity = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    expected = [
        BASE_COMMIT,
        "5b2013281b03d7bd3e0c59b9985e52494263c69f",
        "cecb5fe5cb70162bc1c41162d4503ec73fea2968",
        "add CovaPIE training unknown-atom policy resolution v1",
    ]
    if identity != expected:
        _fail("formal BASE identity drift")


def _check_exact10() -> None:
    if len(EXACT10) != len(set(EXACT10)) != 0 or len(EXACT10) != 10:
        _fail("Exact10 identity drift")
    for relative in EXACT10:
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            _fail(f"Exact10 path invalid: {relative}")
        if stat.S_IMODE(path.stat().st_mode) != 0o644:
            _fail(f"Exact10 mode is not 100644: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail(f"Exact10 forbidden suffix: {relative}")
        if path.stat().st_size >= 100 * 1024 * 1024:
            _fail(f"Exact10 file exceeds 100 MiB: {relative}")
    observed_outputs = {
        path.relative_to(ROOT)
        for path in (ROOT / OUTPUT_ROOT).iterdir()
        if path.is_file()
    }
    if observed_outputs != set(EXACT10[4:]):
        _fail("output directory is not Exact6 evidence files")


def _check_frozen_predecessor() -> dict[str, Any]:
    for path, expected in contract.FROZEN_SHA256.items():
        if _sha(_base_bytes(path)) != expected:
            _fail(f"predecessor SHA drift: {path}")
    manifest = _json(_base_bytes(contract.PREDECESSOR_MANIFEST))
    expected = {
        "policy_resolution_completed": True,
        "resolution_outcome": "resolved_policy_contract",
        "source_atom_row_count": 2870,
        "retained_heavy_atom_row_count": 2525,
        "excluded_explicit_hydrogen_row_count": 345,
        "unsupported_nonhydrogen_row_count": 0,
        "missing_or_invalid_symbol_row_count": 0,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "unknown_atom_runtime_enforcement_integrated": False,
        "effective_open_issue_count": 0,
        "effective_open_issues": [],
        "checkpoint_categorical_width": 10,
        "checkpoint_channel_order_preserved": True,
        "preview_11d_checkpoint_authority": False,
        "silent_zero_vector_fallback_allowed": False,
        "ready_for_tensor_label_loss_mask_contract_design": True,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
    }
    for key, expected_value in expected.items():
        if manifest.get(key) != expected_value:
            _fail(f"predecessor manifest drift: {key}")
    return manifest


def _check_source_inventory() -> list[dict[str, str]]:
    inventory = _rows(_read_output(contract.SOURCE_INVENTORY_FILE))
    if len(inventory) != 69:
        _fail(f"source inventory row count drift: {len(inventory)}")
    paths: set[str] = set()
    required_roles = {
        "unknown_policy_resolution_source",
        "unknown_policy_resolution_manifest",
        "unknown_policy_resolution_issue_inventory",
        "heavy_atom_disposition_and_projection",
        "sample_heavy_atom_projection",
        "final_dataset_index",
        "atom_pair_mapping_authority",
        "canonical_task_and_pair_authority",
        "canonical_role_and_mask_authority",
        "b3_role_mask_authority",
        "legacy_role_warhead_schema_boundary",
        "pre_post_geometry_authority",
        "current_collate_adapter",
        "current_batch_adapter",
        "current_model_input_consumer",
        "step12d_checkpoint_10d_lineage",
        "current11_ligand_atom_table",
        "current11_pocket_atom_table",
        "current11_positive_pair_table",
        "current11_covalent_event_table",
    }
    roles = {row["source_role"] for row in inventory}
    if not required_roles.issubset(roles):
        _fail("source inventory required authority missing")
    for row in inventory:
        path = row["source_path"]
        if path in paths:
            _fail(f"duplicate source inventory path: {path}")
        paths.add(path)
        if path.startswith("data/raw/") or Path(path).suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail(f"forbidden source inventory path: {path}")
        payload = _base_bytes(path)
        if (
            _sha(payload) != row["source_sha256"]
            or not _truth(row["committed_in_base"])
            or not _truth(row["verified"])
        ):
            _fail(f"source inventory verification failed: {path}")
    return inventory


def _check_checkpoint_and_registry(
    manifest: dict[str, Any],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    registry = _rows(_read_output(contract.CONTRACT_REGISTRY_FILE))
    if len(registry) != manifest["contract_registry_row_count"] != 0:
        _fail("contract registry row count drift")
    identities = [row["contract_id"] for row in registry]
    if len(identities) != len(set(identities)):
        _fail("duplicate normalized contract")
    counts = {
        category: sum(
            row["contract_category"] == category for row in registry
        )
        for category in contract.CONTRACT_CATEGORIES
    }
    expected_counts = {
        "current_checkpoint_input": 6,
        "batch_index_structure": 11,
        "covalent_sidecar_condition": 9,
        "canonical_task_mask": 6,
        "auxiliary_training_label": 8,
        "auxiliary_loss_mask": 5,
        "reserved_metadata_only": 3,
    }
    if counts != expected_counts:
        _fail(f"contract category counts drift: {counts!r}")
    if len(registry) != 48:
        _fail("contract registry is not Exact48")
    current_names = {
        "ligand_heavy_atom_one_hot_10d",
        "pocket_heavy_atom_one_hot_10d",
        "ligand_heavy_coordinates",
        "pocket_heavy_coordinates",
        "ligand_batch_membership",
        "pocket_batch_membership",
    }
    current = [
        row for row in registry
        if row["contract_category"] == "current_checkpoint_input"
    ]
    if {row["semantic_name"] for row in current} != current_names:
        _fail("current checkpoint input contract identity drift")
    one_hot = {
        row["semantic_name"]: row for row in current
        if "one_hot_10d" in row["semantic_name"]
    }
    if (
        len(one_hot) != 2
        or any(row["shape"].split(",")[-1] != "10]" for row in one_hot.values())
        or any(row["width_or_component_count"] != "10" for row in one_hot.values())
    ):
        _fail("checkpoint 10D width contract drift")
    for row in registry:
        if (
            row["contract_category"] not in contract.CONTRACT_CATEGORIES
            or row["contract_status"] not in contract.CONTRACT_STATUSES
            or _truth(row["changes_checkpoint_input_width"])
            or _truth(row["materialized_current_step"])
            or not _truth(row["verified"])
        ):
            _fail(f"registry invariant failed: {row['contract_id']}")
    if {
        row["index_space"]
        for row in registry
        if row["index_space"] in contract.EXACT_INDEX_SPACES
    } != set(contract.EXACT_INDEX_SPACES):
        _fail("Exact6 index-space coverage drift")
    registry_by_name = {
        row["semantic_name"]: row for row in registry
    }
    pair_offsets = registry_by_name.get("pair_candidate_offsets")
    residue_local = registry_by_name.get(
        "pair_candidate_residue_local_index"
    )
    if (
        pair_offsets is None
        or pair_offsets["dtype"] != "int64"
        or pair_offsets["rank"] != "1"
        or pair_offsets["shape"] != "[B+1]"
        or pair_offsets["index_space"] != "pair_candidate_index_0based"
        or pair_offsets["local_or_flat"]
        != "batch_boundary_to_global_candidate"
    ):
        _fail("pair candidate offsets registry contract drift")
    if (
        residue_local is None
        or residue_local["index_space"]
        != "retained_heavy_local_index_0based"
        or residue_local["local_or_flat"]
        != "pocket_retained_heavy_local_within_sample"
        or "never target-residue member ordinal"
        not in residue_local["derivation_rule"]
    ):
        _fail("pair residue-local semantics remain ambiguous")
    expected_loss_masks = {
        "warhead_type_loss_mask",
        "pair_head_candidate_loss_mask",
        "pair_contrastive_sample_loss_mask",
        "geometry_component_loss_mask",
        "geometry_sample_loss_mask",
    }
    if {
        row["semantic_name"] for row in registry
        if row["contract_category"] == "auxiliary_loss_mask"
    } != expected_loss_masks:
        _fail("auxiliary loss-mask identities drift")
    if manifest["base_checkpoint_atom_feature_width"] != 10:
        _fail("manifest checkpoint width drift")
    if (
        manifest["base_checkpoint_atom_feature_width_changed"]
        or not manifest["new_covalent_tensors_are_sidecars"]
        or not manifest["future_adapter_required"]
    ):
        _fail("manifest sidecar/checkpoint boundary drift")
    return registry, counts


def _retained_map(rows: list[dict[str, str]]) -> tuple[list[bool], list[int | None]]:
    keep = [row["type_symbol"] in contract.SUPPORTED_HEAVY_SYMBOLS for row in rows]
    mapping: list[int | None] = []
    next_index = 0
    for retained in keep:
        mapping.append(next_index if retained else None)
        next_index += int(retained)
    return keep, mapping


def _check_current11_semantics(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    final_rows = _rows(_base_bytes(contract.FINAL_DATASET_INDEX))
    projection_rows = {
        row["sample_index_row_id"]: row
        for row in _rows(_base_bytes(contract.SAMPLE_PROJECTION))
    }
    mapping_rows = {
        (row["sample_index_row_id"], row["entity_role"]): row
        for row in _rows(_base_bytes(contract.ATOM_PAIR_MAPPING))
    }
    if len(final_rows) != 11 or len(mapping_rows) != 22:
        _fail("current11 identity count drift")
    ligand_offsets = [0]
    pocket_offsets = [0]
    pair_offsets = [0]
    sample_specs: list[contract.PairCandidateSampleSpec] = []
    pair_total = 0
    role_like: set[str] = set()
    warhead_like: set[str] = set()
    distances: list[float] = []
    for batch_index, sample in enumerate(final_rows):
        sample_id = sample["sample_index_row_id"]
        ligand = _rows(_base_bytes(sample["ligand_atom_table_path"]))
        pocket = _rows(_base_bytes(sample["pocket_atom_table_path"]))
        pair = _rows(_base_bytes(sample["ligand_residue_atom_pair_table_path"]))
        event = _rows(_base_bytes(sample["covalent_event_table_path"]))
        fields = set(ligand[0]) | set(pocket[0]) | set(pair[0]) | set(event[0])
        role_like.update(
            fields
            & {
                "ligand_role", "atom_role", "scaffold_atoms", "linker_atoms",
                "warhead_atoms", "minimal_seed_atoms", "anchor_atoms",
            }
        )
        warhead_like.update(
            fields & {"warhead_type", "warhead_class", "warhead_type_label"}
        )
        ligand_keep, ligand_map = _retained_map(ligand)
        pocket_keep, pocket_map = _retained_map(pocket)
        ligand_count = sum(ligand_keep)
        pocket_count = sum(pocket_keep)
        projection = projection_rows[sample_id]
        if (
            ligand_count != int(projection["retained_ligand_heavy_count"])
            or pocket_count != int(projection["retained_pocket_heavy_count"])
        ):
            _fail("independent retained-heavy projection count drift")
        target_source = [
            index
            for index, row in enumerate(pocket)
            if (
                row["residue_name"] == sample["covalent_residue_name"]
                and row["chain_id"] == sample["covalent_residue_chain_id"]
                and row["residue_index"] == sample["covalent_residue_index"]
                and pocket_keep[index]
            )
        ]
        target_local = [pocket_map[index] for index in target_source]
        if len(target_local) != 6 or any(value is None for value in target_local):
            _fail("target residue membership is not exact six heavy atoms")
        residue_source = int(
            mapping_rows[(sample_id, "target_residue_atom")][
                "matched_row_index_0based"
            ]
        )
        ligand_source = int(
            mapping_rows[(sample_id, "ligand_atom")][
                "matched_row_index_0based"
            ]
        )
        residue_local = pocket_map[residue_source]
        ligand_local = ligand_map[ligand_source]
        if (
            residue_local is None
            or ligand_local is None
            or residue_local not in target_local
            or residue_local
            != int(projection["projected_residue_pair_row_index_0based"])
            or ligand_local
            != int(projection["projected_ligand_pair_row_index_0based"])
        ):
            _fail("reactive atom remap/local membership drift")
        positive_count = sum(
            1
            for ligand_candidate in range(ligand_count)
            for residue_candidate in target_local
            if ligand_candidate == ligand_local
            and residue_candidate == residue_local
        )
        if positive_count != 1:
            _fail("positive pair is not exact-one")
        candidate_count = ligand_count * len(target_local)
        if candidate_count - positive_count < 1:
            _fail("sample has no negative candidate")
        pair_total += candidate_count
        pair_offsets.append(pair_offsets[-1] + candidate_count)
        ligand_offsets.append(ligand_offsets[-1] + ligand_count)
        pocket_offsets.append(pocket_offsets[-1] + pocket_count)
        sample_specs.append(contract.PairCandidateSampleSpec(
            batch_sample_index_0based=batch_index,
            retained_ligand_count=ligand_count,
            retained_pocket_count=pocket_count,
            target_residue_pocket_local_indices=tuple(
                int(value) for value in target_local
            ),
            positive_ligand_local_index=int(ligand_local),
            positive_pocket_local_index=int(residue_local),
        ))
        if len(pair) != 1:
            _fail("positive pair table row count drift")
        pair_distance = float(pair[0]["bond_distance_angstrom"])
        index_distance = float(sample["bond_distance_angstrom"])
        if not math.isclose(pair_distance, index_distance, abs_tol=1e-6):
            _fail("geometry distance crosscheck drift")
        distances.append(index_distance)
        if batch_index != len(ligand_offsets) - 2:
            _fail("sample order drift")
    if role_like or warhead_like:
        _fail("unreviewed role/warhead authority appeared in current11")
    if (
        ligand_offsets[0] != 0
        or pocket_offsets[0] != 0
        or ligand_offsets[-1] != 323
        or pocket_offsets[-1] != 2202
        or any(a > b for a, b in zip(ligand_offsets, ligand_offsets[1:]))
        or any(a > b for a, b in zip(pocket_offsets, pocket_offsets[1:]))
    ):
        _fail("independent offset contract drift")
    if pair_total != 1938 or manifest["pair_candidate_count_current11"] != 1938:
        _fail("pair candidate total drift")
    expected_ligand_offsets = [
        0, 13, 26, 39, 64, 92, 135, 177, 219, 262, 302, 323,
    ]
    expected_pocket_offsets = [
        0, 66, 170, 266, 474, 662, 940, 1207, 1464, 1713, 1974, 2202,
    ]
    expected_pair_offsets = [
        0, 78, 156, 234, 384, 552, 810, 1062, 1314, 1572, 1812, 1938,
    ]
    if (
        ligand_offsets != expected_ligand_offsets
        or pocket_offsets != expected_pocket_offsets
        or pair_offsets != expected_pair_offsets
    ):
        _fail("current11 exact offset arrays drift")
    projection = contract.build_pair_candidate_records_v1(
        sample_specs,
        ligand_offsets,
        pocket_offsets,
    )
    if (
        len(projection.records) != 1938
        or list(projection.pair_candidate_offsets) != pair_offsets
        or sum(projection.pair_candidate_is_positive) != 11
        or not all(projection.pair_positive_candidate_valid)
        or not all(value >= 1 for value in projection.pair_negative_count)
        or projection.pair_contrastive_sample_loss_mask != (True,) * 11
    ):
        _fail("independent pair candidate record projection drift")
    for record in projection.records:
        batch = record.pair_candidate_batch_index
        if (
            record.pair_candidate_ligand_flat_index
            != ligand_offsets[batch]
            + record.pair_candidate_ligand_local_index
            or record.pair_candidate_pocket_flat_index
            != pocket_offsets[batch]
            + record.pair_candidate_residue_local_index
        ):
            _fail("independent pair local-to-flat relation failed")
    for spec, positive_index in zip(
        sample_specs,
        projection.pair_positive_candidate_index,
    ):
        ordinal = spec.target_residue_pocket_local_indices.index(
            spec.positive_pocket_local_index
        )
        batch = spec.batch_sample_index_0based
        expected_positive = (
            pair_offsets[batch]
            + spec.positive_ligand_local_index
            * len(spec.target_residue_pocket_local_indices)
            + ordinal
        )
        if positive_index != expected_positive:
            _fail("independent positive global candidate formula failed")
    if not any(
        value > 5
        for value in projection.pair_candidate_residue_local_index
    ):
        _fail("residue-local evidence does not distinguish pocket-local from ordinal")
    if len(distances) != 11 or not all(value > 0 for value in distances):
        _fail("post-covalent bond-distance coverage drift")
    if manifest["role_vocabulary"] != ["scaffold", "linker", "warhead"]:
        _fail("dynamic role vocabulary drift")
    if (
        manifest["role_assignments_current11_complete"]
        or manifest["minimal_seed_or_anchor_authority_present"]
        or manifest["warhead_type_vocabulary"]
        or manifest["warhead_type_vocabulary_frozen"]
        or manifest["warhead_type_valid_sample_count"] != 0
    ):
        _fail("role/seed/warhead blocker truthfulness drift")
    expected_tasks = [
        {
            "canonical_task_id": task_id,
            "semantic_name": name,
            "display_alias": alias,
        }
        for task_id, name, alias in contract.CANONICAL_TASKS
    ]
    if manifest["canonical_tasks"] != expected_tasks:
        _fail("Exact5 canonical task drift")
    if manifest["index_spaces"] != list(contract.EXACT_INDEX_SPACES):
        _fail("Exact6 index-space drift")
    expected_manifest_offsets = {
        "ligand_node_offsets_current11": ligand_offsets,
        "pocket_node_offsets_current11": pocket_offsets,
        "pair_candidate_offsets_current11": pair_offsets,
    }
    if any(
        manifest.get(name) != values
        for name, values in expected_manifest_offsets.items()
    ):
        _fail("manifest current11 offset arrays drift")
    if (
        not manifest["pair_candidate_offsets_contract_frozen"]
        or manifest["pair_candidate_residue_local_index_semantics"]
        != "pocket_retained_heavy_local_within_sample"
        or not manifest["target_residue_member_ordinal_is_enumeration_only"]
        or manifest["target_residue_member_ordinal_is_formal_index_space"]
        or not manifest["pair_local_to_flat_relations_verified"]
        or not manifest["pair_positive_global_index_formula_verified"]
        or manifest["pair_candidate_record_count_current11"] != 1938
        or manifest["pair_contrastive_sample_loss_mask_current11"]
        != [True] * 11
        or manifest["pair_contrastive_mask_true_count_current11"] != 11
    ):
        _fail("manifest pair index hardening contract drift")
    if (
        manifest["geometry_component_count"] != 1
        or manifest["geometry_contract_frozen"]
        or manifest["complete_pre_post_geometry_available"]
    ):
        _fail("geometry blocker truthfulness drift")
    component = manifest["geometry_components"][0]
    if (
        component["geometry_component_id"] != 0
        or component["unit"] != "angstrom"
        or component["periodic_or_nonperiodic"] != "nonperiodic"
        or component["current_valid_sample_count"] != 11
        or component["pre_post_or_delta"] != "post_covalent"
    ):
        _fail("geometry component registry drift")
    return {
        "pair_total": pair_total,
        "ligand_offsets": ligand_offsets,
        "pocket_offsets": pocket_offsets,
        "pair_offsets": pair_offsets,
        "projection": projection,
    }


def _check_v3_exact_types_and_zero_negative(
    manifest: dict[str, Any],
) -> dict[str, bool]:
    single_spec = contract.PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=1,
        retained_pocket_count=1,
        target_residue_pocket_local_indices=(0,),
        positive_ligand_local_index=0,
        positive_pocket_local_index=0,
    )
    single = contract.build_pair_candidate_records_v1(
        (single_spec,),
        (0, 1),
        (0, 1),
    )
    if (
        len(single.records) != 1
        or single.pair_candidate_is_positive != (True,)
        or single.pair_candidate_is_negative != (False,)
        or single.pair_positive_candidate_valid != (True,)
        or single.pair_negative_count != (0,)
        or single.pair_contrastive_sample_loss_mask != (False,)
    ):
        _fail("single-candidate zero-negative projection drift")

    invalid_specs = (
        dataclasses.replace(single_spec, batch_sample_index_0based=False),
        dataclasses.replace(single_spec, positive_ligand_local_index=True),
        dataclasses.replace(single_spec, positive_pocket_local_index=True),
        dataclasses.replace(single_spec, retained_ligand_count=True),
        dataclasses.replace(single_spec, retained_pocket_count=True),
        dataclasses.replace(
            single_spec,
            target_residue_pocket_local_indices=(False,),
        ),
        dataclasses.replace(
            single_spec,
            target_residue_pocket_local_indices=[0],
        ),
    )
    for spec in invalid_specs:
        valid, reasons = (
            contract.validate_pair_candidate_sample_spec_exact_types_v1(
                spec
            )
        )
        if valid or not reasons:
            _fail("PairCandidateSampleSpec bool/list type was accepted")
        try:
            contract.build_pair_candidate_records_v1(
                (spec,),
                (0, 1),
                (0, 1),
            )
        except ValueError as error:
            if "type_invalid" not in str(error):
                _fail("pair builder returned nondeterministic type reason")
        else:
            _fail("pair builder accepted invalid exact scalar type")

    zero_negative_scenario = dataclasses.replace(
        contract.TensorLabelAndLossMaskContractScenario(),
        pair_negative_count=0,
        contrastive_sample_loss_mask_enabled=False,
    )
    zero_observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            zero_negative_scenario
        )
    )
    if (
        zero_observation.outcome != "designed_with_blockers"
        or not zero_observation.pair_contract_resolved
        or zero_observation.ready_for_tensor_materialization_smoke
    ):
        _fail("zero-negative contract scenario incorrectly rejected")

    invalid_contract_values = (
        ("predecessor_sha_valid", 1),
        ("predecessor_effective_open_issue_count", False),
        ("checkpoint_atom_feature_width", True),
        ("canonical_task_count", True),
        ("pair_positive_count", True),
        ("pair_negative_count", True),
        ("pair_positive_count", 1.0),
        ("pair_negative_count", "1"),
    )
    for field_name, value in invalid_contract_values:
        scenario = dataclasses.replace(
            contract.TensorLabelAndLossMaskContractScenario(),
            **{field_name: value},
        )
        observation = (
            contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
                scenario
            )
        )
        if observation.outcome != "invalid" or observation.reasons != (
            f"scenario_field_type_invalid:{field_name}",
        ):
            _fail(f"contract scenario exact type accepted: {field_name}")

    invalid_pair_policy_values = (
        ("same_sample", 1),
        ("positive_count", True),
        ("negative_count", True),
    )
    for field_name, value in invalid_pair_policy_values:
        scenario = dataclasses.replace(
            contract.PairCandidatePolicyScenario(),
            **{field_name: value},
        )
        observation = (
            contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
                scenario
            )
        )
        if observation.candidate_allowed or observation.reasons != (
            f"pair_policy_scenario_field_type_invalid:{field_name}",
        ):
            _fail(f"pair policy bool-as-int accepted: {field_name}")

    registry_specs = (
        (
            contract.TensorLabelAndLossMaskContractScenario(),
            contract.FAILURE_MUTATIONS,
            40,
        ),
        (
            contract.PairCandidatePolicyScenario(),
            contract.PAIR_POLICY_MUTATIONS,
            16,
        ),
    )
    for baseline, registry, expected_count in registry_specs:
        baseline_fields = {
            field.name: getattr(baseline, field.name)
            for field in dataclasses.fields(baseline)
        }
        signatures: set[str] = set()
        for case_id, mutation in registry.items():
            fields = mutation["fields"]
            for field_name, value in fields.items():
                if (
                    field_name not in baseline_fields
                    or type(value) is not type(baseline_fields[field_name])
                ):
                    _fail(
                        f"mutation registry exact type drift: "
                        f"{case_id}:{field_name}"
                    )
            signatures.add(_mutation_signature(fields))
        if len(registry) != expected_count or len(signatures) != expected_count:
            _fail("mutation registry signature count drift")

    flags = {
        "pair_builder_zero_negative_pair_head_supported": True,
        "pair_contrastive_mask_false_when_zero_negative": True,
        "pair_candidate_sample_spec_exact_types_verified": True,
        "contract_scenario_exact_scalar_types_verified": True,
        "pair_policy_scenario_exact_scalar_types_verified": True,
        "boolean_rejected_for_integer_index_and_count_fields": True,
        "failure_mutation_registry_exact_types_verified": True,
        "pair_policy_mutation_registry_exact_types_verified": True,
    }
    for name, expected in flags.items():
        if manifest.get(name) is not expected:
            _fail(f"manifest V3 hardening flag drift: {name}")
    return flags


def _check_v4_public_index_helpers(
    manifest: dict[str, Any],
) -> dict[str, bool]:
    if (
        not contract.validate_offsets_v1((0, 1), 1)
        or not contract.validate_offsets_v1((0,), 0)
    ):
        _fail("valid exact-int offset contract rejected")
    invalid_offsets = (
        ((0, 1), True),
        ((0, 1), 1.0),
        ((0, True), 1),
        (None, 0),
        ((), 0),
    )
    if any(
        contract.validate_offsets_v1(offsets, terminal)
        for offsets, terminal in invalid_offsets
    ):
        _fail("offset helper accepted non-exact-int or malformed input")

    invalid_flatten = (
        (False, 0, "batch sample index exact int required"),
        (True, 0, "batch sample index exact int required"),
        (0.0, 0, "batch sample index exact int required"),
        ("0", 0, "batch sample index exact int required"),
        (0, False, "retained-heavy local index exact int required"),
        (0, True, "retained-heavy local index exact int required"),
        (0, 1.0, "retained-heavy local index exact int required"),
        (0, "1", "retained-heavy local index exact int required"),
    )
    for batch, local, expected_reason in invalid_flatten:
        try:
            contract.flatten_local_index_v1((0, 2), batch, local)
        except ValueError as error:
            if str(error) != expected_reason:
                _fail("flatten-local deterministic reason drift")
        else:
            _fail("flatten-local helper accepted non-exact int")
    valid_flatten = (
        contract.flatten_local_index_v1((0, 2), 0, 0),
        contract.flatten_local_index_v1((0, 2), 0, 1),
    )
    if valid_flatten != (0, 1) or any(
        type(value) is not int for value in valid_flatten
    ):
        _fail("flatten-local valid zero/exact-int result drift")

    expected_targets = (
        ("warhead",),
        ("linker", "warhead"),
        ("scaffold", "warhead"),
        ("scaffold",),
        ("scaffold", "linker", "warhead"),
    )
    observed_targets = tuple(
        contract.canonical_task_regions_v1(task_id)["target"]
        for task_id in range(5)
    )
    if observed_targets != expected_targets:
        _fail("canonical Exact5 target regions drift")
    if contract.CANONICAL_TASKS[3] != (3, "scaffold_only", "B3"):
        _fail("canonical B3 task identity drift")
    for invalid_task_id in (True, False, 1.0, "0", None):
        try:
            contract.canonical_task_regions_v1(invalid_task_id)
        except ValueError as error:
            if str(error) != "canonical task id exact int required":
                _fail("canonical task deterministic reason drift")
        else:
            _fail("canonical task helper accepted non-exact int")

    if (
        not contract.validate_sentinel_with_validity_v1(0, True)
        or contract.validate_sentinel_with_validity_v1(True, True)
        or contract.validate_sentinel_with_validity_v1(0, 1)
    ):
        _fail("sentinel exact-type helper regression")
    zero_spec = contract.PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=1,
        retained_pocket_count=1,
        target_residue_pocket_local_indices=(0,),
        positive_ligand_local_index=0,
        positive_pocket_local_index=0,
    )
    if (
        not contract.validate_pair_candidate_sample_spec_exact_types_v1(
            zero_spec
        )[0]
        or contract.validate_pair_candidate_sample_spec_exact_types_v1(
            dataclasses.replace(
                zero_spec,
                positive_ligand_local_index=True,
            )
        )[0]
    ):
        _fail("PairCandidateSampleSpec public exact-type regression")

    flags = {
        "offset_terminal_count_exact_int_verified": True,
        "offset_elements_exact_int_verified": True,
        "flatten_local_index_exact_int_verified": True,
        "canonical_task_id_exact_int_verified": True,
        "public_index_helpers_exact_scalar_types_verified": True,
        "boolean_rejected_across_all_public_index_helpers": True,
    }
    for name, expected in flags.items():
        if manifest.get(name) is not expected:
            _fail(f"manifest V4 public-helper flag drift: {name}")
    return flags


def _check_v5_nonnegative_counts_and_ordered_offsets(
    manifest: dict[str, Any],
) -> dict[str, bool]:
    negative_contract = dataclasses.replace(
        contract.TensorLabelAndLossMaskContractScenario(),
        pair_negative_count=-1,
        contrastive_sample_loss_mask_enabled=False,
    )
    negative_contract_observation = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            negative_contract
        )
    )
    if (
        negative_contract_observation.outcome != "invalid"
        or negative_contract_observation.reasons
        != ("negative_pair_count_negative",)
    ):
        _fail("negative top-level pair count accepted with contrastive disabled")

    negative_policy = dataclasses.replace(
        contract.PairCandidatePolicyScenario(),
        negative_count=-1,
        contrastive_sample_loss_mask_enabled=False,
    )
    negative_policy_observation = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            negative_policy
        )
    )
    if (
        negative_policy_observation.candidate_allowed
        or negative_policy_observation.reasons
        != ("negative_pair_count_negative",)
    ):
        _fail("negative pair-policy count accepted with contrastive disabled")

    positive_policy = dataclasses.replace(
        contract.PairCandidatePolicyScenario(),
        positive_count=-1,
    )
    positive_policy_observation = (
        contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            positive_policy
        )
    )
    if (
        positive_policy_observation.candidate_allowed
        or positive_policy_observation.reasons
        != ("positive_pair_count_negative",)
    ):
        _fail("negative positive-count reason semantics drift")

    valid_offsets = (
        ((0, 1), 1),
        ([0, 1], 1),
        (range(0, 2), 1),
    )
    if not all(
        contract.validate_offsets_v1(offsets, terminal)
        for offsets, terminal in valid_offsets
    ):
        _fail("ordered repeatable offset Sequence was rejected")
    invalid_offsets = (
        ({0: "x", 1: "y"}, 1),
        ({0, 1}, 1),
        (frozenset({0, 1}), 1),
        (iter([0, 1]), 1),
        ((value for value in [0, 1]), 1),
        ("01", 1),
        (b"\x00\x01", 1),
        (bytearray([0, 1]), 1),
        (memoryview(b"\x00\x01"), 1),
    )
    if any(
        contract.validate_offsets_v1(offsets, terminal)
        for offsets, terminal in invalid_offsets
    ):
        _fail("unordered, single-pass, or binary offset container accepted")

    valid_flatten = (
        contract.flatten_local_index_v1((0, 2), 0, 0),
        contract.flatten_local_index_v1([0, 2], 0, 1),
        contract.flatten_local_index_v1(range(0, 3, 2), 0, 1),
    )
    if valid_flatten != (0, 1, 1) or any(
        type(value) is not int for value in valid_flatten
    ):
        _fail("ordered Sequence flatten result drift")
    for offsets in (
        {0: "x", 1: "y"},
        {0, 1},
        frozenset({0, 1}),
        iter([0, 2]),
        (value for value in [0, 2]),
        "02",
        b"\x00\x02",
        bytearray([0, 2]),
        memoryview(b"\x00\x02"),
    ):
        try:
            contract.flatten_local_index_v1(offsets, 0, 0)
        except ValueError as error:
            if str(error) != "offset contract invalid":
                _fail("invalid offset container reason drift")
        else:
            _fail("flatten accepted invalid offset container")

    flags = {
        "pair_positive_count_nonnegative_verified": True,
        "pair_negative_count_nonnegative_verified": True,
        "negative_pair_count_rejected_when_contrastive_disabled": True,
        "negative_count_reason_semantics_frozen": True,
        "offset_container_ordered_sequence_verified": True,
        "unordered_offset_containers_rejected": True,
        "single_pass_offset_iterables_rejected": True,
        "binary_offset_containers_rejected": True,
    }
    for name, expected in flags.items():
        if manifest.get(name) is not expected:
            _fail(f"manifest V5 count/offset flag drift: {name}")
    return flags


def _independent_invalid_reasons(
    scenario: contract.TensorLabelAndLossMaskContractScenario,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not scenario.predecessor_sha_valid:
        reasons.append("predecessor_sha_invalid")
    if not scenario.predecessor_contract_design_ready:
        reasons.append("predecessor_contract_design_not_ready")
    if scenario.predecessor_effective_open_issue_count != 0:
        reasons.append("predecessor_effective_open_issue_count_not_zero")
    lower = (
        contract.validate_checkpoint_sidecar_boundary_v1(scenario),
        contract._validate_index_and_offset_contract_v1(scenario),
        contract.validate_task_mask_partition_v1(scenario),
        contract.validate_target_residue_condition_contract_v1(scenario),
        contract._validate_pair_candidate_contract_v1(scenario),
        contract.validate_geometry_component_contract_v1(scenario),
        contract.validate_auxiliary_label_and_loss_mask_contract_v1(
            scenario
        ),
    )
    for observation in lower:
        reasons.extend(observation.reasons)
    if any((
        scenario.tensor_materialization_requested,
        scenario.dataloader_changed,
        scenario.model_changed,
        scenario.forward_changed,
        scenario.loss_changed,
        scenario.checkpoint_accessed,
        scenario.training_used,
    )):
        reasons.append("execution_boundary_crossed")
    return tuple(dict.fromkeys(reasons))


def _check_pair_and_failure_matrices(
    manifest: dict[str, Any],
) -> None:
    pair_rows = _rows(_read_output(contract.PAIR_POLICY_FILE))
    if [row["case_id"] for row in pair_rows] != list(contract.PAIR_POLICY_CASES):
        _fail("pair policy case order drift")
    for row in pair_rows:
        mutation = contract.PAIR_POLICY_MUTATIONS[row["case_id"]]
        fields = mutation["fields"]
        scenario = dataclasses.replace(
            contract.PairCandidatePolicyScenario(),
            **fields,
        )
        observation = (
            contract.evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
                scenario
            )
        )
        expected_reason = mutation["expected_reason"]
        expected_values = {
            "mutation_signature": _mutation_signature(fields),
            "candidate_allowed": observation.candidate_allowed,
            "label_semantics": observation.label_semantics,
            "negative_semantics": observation.negative_semantics,
            "loss_mask_semantics": observation.loss_mask_semantics,
            "fails_closed": observation.fails_closed,
            "reason": expected_reason,
            "verified": expected_reason in observation.reasons,
        }
        for key, value in expected_values.items():
            normalized = (
                str(value).lower() if isinstance(value, bool) else str(value)
            )
            if row[key] != normalized:
                _fail(
                    f"pair policy scenario evidence drift: "
                    f"{row['case_id']}:{key}"
                )
    failures = _rows(_read_output(contract.FAILURE_MATRIX_FILE))
    if [row["failure_case"] for row in failures] != list(contract.FAILURE_CASES):
        _fail("failure matrix case identity/order drift")
    scenario_fields = {
        field.name
        for field in dataclasses.fields(
            contract.TensorLabelAndLossMaskContractScenario
        )
    }
    if "failure_case" in scenario_fields:
        _fail("scenario retains forbidden failure_case string field")
    false_fields = (
        "tensor_label_loss_mask_contract_designed",
        "ready_for_tensor_materialization_smoke",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
    )
    signatures: set[str] = set()
    for row in failures:
        mutation = contract.FAILURE_MUTATIONS[row["failure_case"]]
        fields = mutation["fields"]
        if not fields or any(
            getattr(contract.TensorLabelAndLossMaskContractScenario(), name)
            == value
            for name, value in fields.items()
        ):
            _fail(f"failure mutation did not change state: {row['failure_case']}")
        signature = _mutation_signature(fields)
        if signature in signatures:
            _fail(f"duplicate failure mutation signature: {row['failure_case']}")
        signatures.add(signature)
        scenario = dataclasses.replace(
            contract.TensorLabelAndLossMaskContractScenario(),
            **fields,
        )
        observation = (
            contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
                scenario
            )
        )
        independently_observed = _independent_invalid_reasons(scenario)
        expected_reason = mutation["expected_reason"]
        try:
            recorded_reasons = json.loads(row["observed_reasons"])
        except json.JSONDecodeError:
            _fail(f"failure observed reasons are not JSON: {row['failure_case']}")
        if (
            observation.outcome != "invalid"
            or independently_observed != observation.reasons
            or row["expected_outcome"] != "invalid"
            or row["observed_outcome"] != "invalid"
            or row["expected_primary_reason"] != expected_reason
            or recorded_reasons != list(observation.reasons)
            or expected_reason not in independently_observed
            or row["mutation_signature"] != signature
            or not _truth(row["failure_detected"])
            or _truth(row["condition_contract_resolved"])
            != observation.condition_contract_resolved
            or _truth(row["pair_contract_resolved"])
            != observation.pair_contract_resolved
            or _truth(
                row["geometry_and_auxiliary_label_contract_resolved"]
            )
            != observation.geometry_and_auxiliary_label_contract_resolved
            or any(_truth(row[field]) for field in false_fields)
            or not _truth(row["fails_closed"])
            or not _truth(row["verified"])
        ):
            _fail(f"failure case did not fail closed: {row['failure_case']}")
    baseline = (
        contract.validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            contract.TensorLabelAndLossMaskContractScenario()
        )
    )
    if (
        baseline.outcome != "designed_with_blockers"
        or baseline.reasons
        != (
            "current11_per_atom_role_and_minimal_seed_authority_missing",
            "current11_warhead_type_vocabulary_missing",
            "complete_pre_post_geometry_contract_missing",
        )
        or baseline.condition_contract_resolved
        or not baseline.pair_contract_resolved
        or baseline.geometry_and_auxiliary_label_contract_resolved
        or baseline.tensor_label_loss_mask_contract_designed
        or baseline.ready_for_tensor_materialization_smoke
    ):
        _fail("independently rebuilt baseline scenario drift")
    if (
        len(signatures) != 40
        or not manifest["failure_matrix_uses_explicit_state_mutations"]
        or manifest["failure_matrix_string_driven_invalid_fallback"]
        or not manifest["failure_matrix_expected_reasons_verified"]
    ):
        _fail("failure mutation hardening manifest drift")


def _check_issue_inventory(
    manifest: dict[str, Any],
) -> dict[str, str]:
    predecessor = _base_bytes(contract.PREDECESSOR_ISSUES)
    successor = _read_output(contract.ISSUE_INVENTORY_FILE)
    if not successor.startswith(predecessor):
        _fail("first 32 issue rows are not byte-equivalent predecessor prefix")
    predecessor_rows = _rows(predecessor)
    successor_rows = _rows(successor)
    if successor_rows[:32] != predecessor_rows or len(successor_rows) != 35:
        _fail("issue inventory inheritance/count drift")
    exact3 = successor_rows[32:]
    expected = [
        ("COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED", "open"),
        ("COVALENT_PAIR_LABEL_AND_NEGATIVE_POLICY_UNRESOLVED", "resolved"),
        ("COVALENT_GEOMETRY_AND_AUXILIARY_LABEL_CONTRACT_UNRESOLVED", "open"),
    ]
    if [
        (row["issue_id"], row["successor_effective_status"])
        for row in exact3
    ] != expected:
        _fail("issue inventory Exact3 state drift")
    open_issues = [
        row["issue_id"]
        for row in successor_rows
        if row["successor_effective_status"] == "open"
    ]
    if (
        manifest["effective_open_issue_count"] != len(open_issues)
        or manifest["effective_open_issues"] != open_issues
    ):
        _fail("manifest/evidence effective issue set mismatch")
    return {
        "condition": exact3[0]["successor_effective_status"],
        "pair": exact3[1]["successor_effective_status"],
        "geometry": exact3[2]["successor_effective_status"],
    }


def _check_manifest_boundaries(
    manifest: dict[str, Any],
    predecessor: dict[str, Any],
) -> None:
    false_fields = (
        "base_checkpoint_atom_feature_width_changed",
        "tensor_label_loss_mask_contract_designed",
        "ready_for_tensor_materialization_smoke",
        "tensor_materialized",
        "npz_created",
        "tensor_materialization_used",
        "runtime_enforcement_integrated",
        "checkpoint_access",
        "model_changed",
        "dataloader_changed",
        "forward_changed",
        "loss_changed",
        "training_used",
        "raw_read",
        "raw_write",
        "provider_used",
        "network_used",
        "download_used",
        "ready_for_tensorization",
        "ready_for_model_integration",
        "ready_for_training",
    )
    if any(manifest[field] is not False for field in false_fields):
        _fail("metadata-only execution boundary crossed")
    if (
        manifest["contract_design_completed"] is not True
        or manifest["design_outcome"] != "designed_with_blockers"
        or manifest["planned_covalent_model_module_count"] != 5
        or manifest["integrated_covalent_model_module_count"] != 0
        or predecessor["planned_covalent_model_module_count"] != 5
        or predecessor["integrated_covalent_model_module_count"] != 0
        or manifest["recommended_next_step"]
        != "resolve_covapie_condition_and_task_mask_tensor_contract_gaps_v1"
    ):
        _fail("decision/module/readiness boundary drift")
    if (
        not manifest["generation_masks_are_not_loss_masks"]
        or not manifest["padding_masks_are_not_label_availability_masks"]
        or not manifest["sentinel_requires_validity_mask"]
        or manifest["zero_means_missing"]
        or manifest["cross_sample_negatives_allowed"]
        or manifest["random_negative_sampling_allowed"]
        or manifest["hard_negative_mining_allowed"]
    ):
        _fail("mask/sentinel/negative policy drift")


def _check_deterministic_evidence(manifest: dict[str, Any]) -> Any:
    generated_first = (
        contract.build_covapie_tensor_label_and_loss_mask_contract_design_artifacts_v1(
            ROOT
        )
    )
    generated_second = (
        contract.build_covapie_tensor_label_and_loss_mask_contract_design_artifacts_v1(
            ROOT
        )
    )
    if generated_first != generated_second:
        _fail("builder is nondeterministic")
    for name, expected in generated_first.items():
        observed = _read_output(name)
        if observed != expected:
            _fail(f"generated evidence bytes drift: {name}")
    for name, expected_sha in manifest["evidence_sha256"].items():
        if name == contract.MANIFEST_FILE:
            _fail("manifest records its own SHA")
        if _sha(_read_output(name)) != expected_sha:
            _fail(f"manifest evidence SHA mismatch: {name}")
    decision_first = (
        contract.derive_covapie_tensor_label_and_loss_mask_contract_design_v1(
            ROOT
        )["decision"]
    )
    decision_second = (
        contract.derive_covapie_tensor_label_and_loss_mask_contract_design_v1(
            ROOT
        )["decision"]
    )
    if (
        decision_first != decision_second
        or contract.serialize_covapie_tensor_label_and_loss_mask_contract_design_decision_v1(
            decision_first
        )
        != contract.serialize_covapie_tensor_label_and_loss_mask_contract_design_decision_v1(
            decision_second
        )
    ):
        _fail("decision serialization is nondeterministic")
    return decision_first


def main() -> None:
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    _check_base_identity()
    _check_exact10()
    predecessor = _check_frozen_predecessor()
    _check_source_inventory()
    manifest = _json(_read_output(contract.MANIFEST_FILE))
    _registry, counts = _check_checkpoint_and_registry(manifest)
    current11 = _check_current11_semantics(manifest)
    v3_hardening = _check_v3_exact_types_and_zero_negative(manifest)
    v4_hardening = _check_v4_public_index_helpers(manifest)
    v5_hardening = _check_v5_nonnegative_counts_and_ordered_offsets(
        manifest
    )
    _check_pair_and_failure_matrices(manifest)
    issue_statuses = _check_issue_inventory(manifest)
    _check_manifest_boundaries(manifest, predecessor)
    decision = _check_deterministic_evidence(manifest)
    output = {
        "design_outcome": decision.outcome,
        "contract_registry_row_count": decision.contract_registry_row_count,
        "batch_index_structure_count": counts["batch_index_structure"],
        "current_checkpoint_input_contract_count": (
            decision.current_checkpoint_input_contract_count
        ),
        "sidecar_condition_contract_count": (
            decision.sidecar_condition_contract_count
        ),
        "auxiliary_label_contract_count": (
            decision.auxiliary_label_contract_count
        ),
        "auxiliary_loss_mask_contract_count": (
            decision.auxiliary_loss_mask_contract_count
        ),
        "index_space_contract_count": decision.index_space_contract_count,
        "canonical_task_count": decision.canonical_task_count,
        "role_vocabulary_frozen": decision.role_vocabulary_frozen,
        "pair_candidate_policy_frozen": (
            decision.pair_candidate_policy_frozen
        ),
        "pair_negative_policy_frozen": decision.pair_negative_policy_frozen,
        "pair_positive_exact_one_verified": (
            decision.pair_positive_exact_one_verified
        ),
        "pair_candidate_count_current11": current11["pair_total"],
        "pair_candidate_offsets_contract_frozen": manifest[
            "pair_candidate_offsets_contract_frozen"
        ],
        "pair_local_to_flat_relations_verified": manifest[
            "pair_local_to_flat_relations_verified"
        ],
        "pair_positive_global_index_formula_verified": manifest[
            "pair_positive_global_index_formula_verified"
        ],
        "pair_builder_zero_negative_pair_head_supported": v3_hardening[
            "pair_builder_zero_negative_pair_head_supported"
        ],
        "pair_contrastive_mask_false_when_zero_negative": v3_hardening[
            "pair_contrastive_mask_false_when_zero_negative"
        ],
        "pair_contrastive_mask_true_count_current11": manifest[
            "pair_contrastive_mask_true_count_current11"
        ],
        "pair_candidate_sample_spec_exact_types_verified": v3_hardening[
            "pair_candidate_sample_spec_exact_types_verified"
        ],
        "contract_scenario_exact_scalar_types_verified": v3_hardening[
            "contract_scenario_exact_scalar_types_verified"
        ],
        "pair_policy_scenario_exact_scalar_types_verified": v3_hardening[
            "pair_policy_scenario_exact_scalar_types_verified"
        ],
        "boolean_rejected_for_integer_index_and_count_fields": (
            v3_hardening[
                "boolean_rejected_for_integer_index_and_count_fields"
            ]
        ),
        "offset_terminal_count_exact_int_verified": v4_hardening[
            "offset_terminal_count_exact_int_verified"
        ],
        "offset_elements_exact_int_verified": v4_hardening[
            "offset_elements_exact_int_verified"
        ],
        "flatten_local_index_exact_int_verified": v4_hardening[
            "flatten_local_index_exact_int_verified"
        ],
        "canonical_task_id_exact_int_verified": v4_hardening[
            "canonical_task_id_exact_int_verified"
        ],
        "public_index_helpers_exact_scalar_types_verified": (
            v4_hardening[
                "public_index_helpers_exact_scalar_types_verified"
            ]
        ),
        "boolean_rejected_across_all_public_index_helpers": (
            v4_hardening[
                "boolean_rejected_across_all_public_index_helpers"
            ]
        ),
        "pair_positive_count_nonnegative_verified": v5_hardening[
            "pair_positive_count_nonnegative_verified"
        ],
        "pair_negative_count_nonnegative_verified": v5_hardening[
            "pair_negative_count_nonnegative_verified"
        ],
        "negative_pair_count_rejected_when_contrastive_disabled": (
            v5_hardening[
                "negative_pair_count_rejected_when_contrastive_disabled"
            ]
        ),
        "negative_count_reason_semantics_frozen": v5_hardening[
            "negative_count_reason_semantics_frozen"
        ],
        "offset_container_ordered_sequence_verified": v5_hardening[
            "offset_container_ordered_sequence_verified"
        ],
        "unordered_offset_containers_rejected": v5_hardening[
            "unordered_offset_containers_rejected"
        ],
        "single_pass_offset_iterables_rejected": v5_hardening[
            "single_pass_offset_iterables_rejected"
        ],
        "binary_offset_containers_rejected": v5_hardening[
            "binary_offset_containers_rejected"
        ],
        "failure_matrix_row_count": manifest["failure_matrix_row_count"],
        "pair_policy_matrix_row_count": manifest[
            "pair_policy_matrix_row_count"
        ],
        "issue_inventory_row_count": manifest["issue_inventory_row_count"],
        "failure_matrix_uses_explicit_state_mutations": manifest[
            "failure_matrix_uses_explicit_state_mutations"
        ],
        "failure_matrix_expected_reasons_verified": manifest[
            "failure_matrix_expected_reasons_verified"
        ],
        "condition_issue": issue_statuses["condition"],
        "pair_issue": issue_statuses["pair"],
        "geometry_issue": issue_statuses["geometry"],
        "warhead_type_vocabulary_frozen": (
            decision.warhead_type_vocabulary_frozen
        ),
        "geometry_component_count": decision.geometry_component_count,
        "geometry_contract_frozen": decision.geometry_contract_frozen,
        "tensor_label_loss_mask_contract_designed": (
            decision.tensor_label_loss_mask_contract_designed
        ),
        "ready_for_tensor_materialization_smoke": (
            decision.ready_for_tensor_materialization_smoke
        ),
        "effective_open_issue_count": manifest["effective_open_issue_count"],
        "effective_open_issues": manifest["effective_open_issues"],
        "ready_for_tensorization": decision.ready_for_tensorization,
        "ready_for_model_integration": decision.ready_for_model_integration,
        "ready_for_training": decision.ready_for_training,
        "recommended_next_step": decision.recommended_next_step,
    }
    if counts["current_checkpoint_input"] != output[
        "current_checkpoint_input_contract_count"
    ]:
        _fail("checker count crosscheck drift")
    for key, value in output.items():
        print(
            f"{key}="
            + (
                json.dumps(value, sort_keys=True, separators=(",", ":"))
                if isinstance(value, (list, dict))
                else str(value).lower() if isinstance(value, bool)
                else str(value)
            )
        )


if __name__ == "__main__":
    main()
