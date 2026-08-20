"""Exact shadow-only task-domain negative gate for 1FVG DTT adducts.

The rule is deliberately narrow: it transfers one immutable human-negative
decision only across the exact attribute-preserving endpoint automorphism of
the same official DTT CCD component in the same SHA-bound 1FVG reagent and
crystallization context.  It does not authorize DTU, other structures,
reducing reagents generally, production chemistry, or training data.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import csv
import gzip
import hashlib
import inspect
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
from types import MappingProxyType
from typing import Any

from covalent_ext import covapie_post_only_auto_negative_ts_dump_exact_v1 as common


SCHEMA_VERSION = (
    "covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1"
)
STAGE = SCHEMA_VERSION
RULE_ID = "NEG_V2_DTT_CRYSTALLIZATION_REDUCING_ADDUCT_EXACT"
RULE_ROLE = "TASK_DOMAIN_AUTO_NEGATIVE_RULE"

# These aliases intentionally preserve the exact result/status/runtime types
# accepted by the already-published successor dispatcher.
MATCHED_AUTO_NEGATIVE_EXACT = common.MATCHED_AUTO_NEGATIVE_EXACT
NOT_MATCHED = common.NOT_MATCHED
INVALID_EVIDENCE = common.INVALID_EVIDENCE
AutoNegativeEvaluationResult = common.AutoNegativeEvaluationResult
RuntimePositiveOverrideContext = common.RuntimePositiveOverrideContext
RUNTIME_OVERRIDE_SCHEMA_VERSION = common.RUNTIME_OVERRIDE_SCHEMA_VERSION

UNIT_SHADOW_AUTO_NEGATIVE_EXACT = "SHADOW_AUTO_NEGATIVE_EXACT"
UNIT_NOT_SHADOW_AUTO_NEGATIVE = "NOT_SHADOW_AUTO_NEGATIVE"

BASE_SUCCESSOR_ROUTING_COMMIT = "c0adc96ec0153abf277991c867605f1e9a7a16a1"
BASE_SUCCESSOR_ROUTING_SUBJECT = (
    "add CovaPIE successor task-domain auto-negative routing v1"
)
CALIBRATION_COMMIT = "106e4182b09a0861294495d1385d678d08868fae"
CALIBRATION_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_2EBCD325E1CD2081"
DTU_COUNTEREXAMPLE_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_024EEB356034F83D"

HUMAN_DECISIONS_RELATIVE = common.HUMAN_DECISIONS_RELATIVE
CALIBRATION_HUMAN_BYTES = common.CALIBRATION_HUMAN_BYTES
CALIBRATION_HUMAN_SHA256 = common.CALIBRATION_HUMAN_SHA256
CALIBRATION_RATIONALE = (
    "Human negative calibration for 1FVG/DTT-S4: DTT is dithiothreitol, a "
    "reducing reagent present as an actual small-molecule ligand in the "
    "frozen biochemical and crystallization context, and the same DTT "
    "instance participates through its two sulfur ends. The Cys218-SG to "
    "DTT-S4 state is reducing-reagent or biochemical-artifact chemistry "
    "rather than a medicinal pocket-recognition covalent ligand. This "
    "decision is exact to this unit and does not decide DTT-S1, DTU, AJ3, "
    "or thiols and disulfides generally."
)

TRIAGE_ROOT_RELATIVE = common.TRIAGE_ROOT_RELATIVE
UPSTREAM_ROOT_RELATIVE = common.UPSTREAM_ROOT_RELATIVE
EVENT_INVENTORY_RELATIVE = common.EVENT_INVENTORY_RELATIVE
REVIEW_PACKET_RELATIVE = common.REVIEW_PACKET_RELATIVE
LEGACY_SUMMARY_RELATIVE = common.LEGACY_SUMMARY_RELATIVE
UPSTREAM_OUTCOMES_RELATIVE = common.UPSTREAM_OUTCOMES_RELATIVE
UPSTREAM_ACQUISITION_RELATIVE = common.UPSTREAM_ACQUISITION_RELATIVE
INPUT_SHA256 = common.INPUT_SHA256
CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT = (
    common.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
)

DTT_GRAPH_SHA256 = (
    "caf1efccafd3624f5eaf17143e96aa9bdd7df4a4e672f24c261fd9af3eb05520"
)
DTU_GRAPH_SHA256 = (
    "d5afdf263da823e28913f8e9dadd6b7748c2aa529ba3f8a49992bc74869536aa"
)
DTT_CCD_SOURCE_SHA256 = (
    "86aebd7b9a429244d244b2c911daf49c9064024eec1932b9e2c9366d41d00c03"
)
DTU_CCD_SOURCE_SHA256 = (
    "679e48f8c37e3946f44a4bdd23e3098adb4fa6579cb08a57b88ab4a0c810e359"
)
DTT_INCHIKEY = "VHJLVAABSRFDPM-IMJSIDKUSA-N"
DTU_INCHIKEY = "VHJLVAABSRFDPM-ZXZARUISSA-N"
DTT_RADIUS1_SHA256 = (
    "e6ca1bc51fe2e6a441cee743e1e8351ac9e24a449cfdb678c4db60c12eec33b8"
)
DTT_RADIUS2_SHA256 = (
    "faffb9025d78c584582ffa19fda6801bc22e0f9e68def174a0a1683f1d7cb5aa"
)
DTT_LOCAL_TOPOLOGY = "[SH:1]-C-C"
DTT_HEAVY_MAP_SHA256 = (
    "5bfe5db75a105f22517839c8184dfa0090d9fd5f9649784efd4fe014d9f44435"
)
SOURCE_STRUCTURE_ID = "1FVG"
SOURCE_STRUCTURE_SHA256 = (
    "549772e3091c4951242a539f245c2bfe73d78b10f5bd3f421fcea849579767c5"
)
SOURCE_PROTEIN_ACCESSION = "P54149"
SOURCE_PROTEIN_SEQUENCE_SHA256 = (
    "cd13b8e05f1d4143dc5067e327624d5d61694e00fc7c6166f13d60d522786b71"
)

ARTIFACT_SEMANTICS = "IMMUTABLE_CALIBRATION_SNAPSHOT_SHADOW_EVALUATION"
READINESS_MODE = (
    "SAME_STRUCTURE_DTT_ENDPOINT_GENERALIZATION_PROVEN_WITHOUT_SHADOW_"
    "LABEL_LEAKAGE"
)
NOT_READY_MODE = "CALIBRATION_ONLY_DTT_ENDPOINT_GENERALIZATION_NOT_PROVEN"
RUNTIME_POSITIVE_OVERRIDE_POLICY = (
    "CURRENT_HUMAN_RELEVANT_OR_CURRENT_PRODUCTION_EXACT_POSITIVE_OR_"
    "EXPLICIT_RUNTIME_POSITIVE_OVERRIDES_AUTO_NEGATIVE; MALFORMED_"
    "OVERRIDE_CONTEXT_INVALIDATES_MATCH"
)

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1"
)
RULE_MANIFEST = "covapie_dtt_auto_negative_rule_manifest_v1.json"
SHADOW_INVENTORY = "covapie_dtt_shadow_match_inventory_v1.csv"
SUMMARY = "covapie_dtt_auto_negative_summary_v1.json"
OUTPUT_FILENAMES = (RULE_MANIFEST, SHADOW_INVENTORY, SUMMARY)

CODE_RELATIVE_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1.py"
    ),
    Path(
        "scripts/"
        "build_covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1.py"
    ),
)
AUTHORIZED_NEW_PATHS = tuple(CODE_RELATIVE_PATHS) + tuple(
    OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES
)

SHADOW_HEADER = (
    "canonical_event_id",
    "review_unit_id",
    "pdb_id",
    "ligand_component_id",
    "ccd_component_graph_sha256",
    "ligand_reactive_atom",
    "ligand_reactive_element",
    "radius1_sha256",
    "radius2_sha256",
    "rule_id",
    "evaluation_status",
    "evaluation_reason",
    "matched_predicates_json",
    "failed_predicates_json",
    "calibration_snapshot_human_review_state",
    "review_unit_shadow_status",
    "shadow_would_auto_negative",
)

REQUIRED_PREDICATES = (
    "candidate_lane",
    "structural_model_eligible",
    "feature_compatible",
    "explicit_cys_sg_covalent_evidence",
    "usable_post_complex_structural_evidence",
    "full_ligand_coordinates",
    "exact_ccd_observed_heavy_atom_identity_coverage",
    "exact_ccd_observed_heavy_atom_element_agreement",
    "exact_reactive_ligand_atom_coverage",
    "pocket_coordinates",
    "outcome_candidate_route",
    "outcome_feature_projection_passed",
    "outcome_explicit_covalent_evidence",
    "exact_connection_and_endpoint_coordinates",
    "exact_dtt_component_identity",
    "exact_dtt_component_graph_sha256",
    "official_dtt_ccd_stereochemical_identity",
    "exact_dtt_heavy_identity_and_charge",
    "automorphism_derived_dtt_sulfur_endpoint",
    "exact_ligand_reactive_element",
    "exact_radius1_sha256",
    "exact_radius2_sha256",
    "exact_local_topology",
    "exact_1fvg_source_structure_context",
    "exact_1fvg_reagent_protein_context",
    "structured_source_boundary",
    "source_annotations_well_formed",
    "no_source_annotation_conflict",
    "no_existing_exact_positive_authority",
    "no_production_approval",
    "no_runtime_positive_override",
)

FORBIDDEN_SOLE_PREDICATES = (
    "component_name_DTT",
    "component_name_DTU",
    "molecular_size",
    "thiol",
    "dithiol",
    "disulfide",
    "sulfur_containing_molecule",
    "source_role",
    "linker_label",
    "probe_label",
    "protein_name",
    "pdb_id",
    "distance_threshold",
    "reagent_intuition",
    "crystallization_word",
)

MANDATORY_COMPONENT_COUNTEREXAMPLES = (
    "GSH",
    "YMA",
    "SC2",
    "TP2",
    "SGM",
    "AJ3",
    "MHC",
    "MEE",
    "FXN",
    "EIP",
    "5X",
    "PYR",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PDB_RE = re.compile(r"^[0-9A-Z]{4}$")


@dataclass(frozen=True)
class UnitShadowEvaluationResult:
    """Immutable fail-closed review-unit aggregation result."""

    rule_id: str
    review_unit_id: str
    status: str
    reason: str
    event_count: int
    matched_event_count: int
    invalid_event_count: int
    shadow_would_auto_negative: bool


class _EvidenceError(ValueError):
    pass


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=list(header), extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(header):
            raise ValueError("CSV_ROW_SCHEMA_MISMATCH")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_ROOT_NOT_OBJECT:" + path.name)
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple | frozenset):
        return [_thaw(item) for item in value]
    return value


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in {0, 1}:
        raise ValueError("GIT_ANCESTRY_CHECK_FAILED")
    return completed.returncode == 0


def verify_repository_binding_v1(repo_root: Path) -> dict[str, object]:
    """Bind synchronized main descendants to the published successor base."""

    repo_root = repo_root.resolve()
    state = dict(common.verify_repository_binding_v1(repo_root))
    subject = _git(
        repo_root, "show", "-s", "--format=%s", BASE_SUCCESSOR_ROUTING_COMMIT
    )
    base_is_ancestor_of_head = _git_is_ancestor(
        repo_root, BASE_SUCCESSOR_ROUTING_COMMIT, "HEAD"
    )
    base_is_ancestor_of_origin = _git_is_ancestor(
        repo_root, BASE_SUCCESSOR_ROUTING_COMMIT, "refs/remotes/origin/main"
    )
    if subject != BASE_SUCCESSOR_ROUTING_SUBJECT:
        raise ValueError("BASE_SUCCESSOR_ROUTING_SUBJECT_BINDING_MISMATCH")
    if not base_is_ancestor_of_head:
        raise ValueError("BASE_SUCCESSOR_ROUTING_COMMIT_NOT_ANCESTOR_OF_HEAD")
    if not base_is_ancestor_of_origin:
        raise ValueError(
            "BASE_SUCCESSOR_ROUTING_COMMIT_NOT_ANCESTOR_OF_ORIGIN_MAIN"
        )
    return {
        **state,
        "base_successor_routing_commit": BASE_SUCCESSOR_ROUTING_COMMIT,
        "base_successor_routing_subject": subject,
        "base_successor_routing_commit_is_ancestor_of_head": (
            base_is_ancestor_of_head
        ),
        "base_successor_routing_commit_is_ancestor_of_origin_main": (
            base_is_ancestor_of_origin
        ),
        "descendant_repository_compatible": True,
    }


def verify_bound_inputs_v1(repo_root: Path) -> dict[str, str]:
    return common.verify_bound_inputs_v1(repo_root.resolve())


def _required_mapping(value: object, owner: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _EvidenceError(owner + ":EXPECTED_MAPPING")
    return value


def _required_string(value: object, owner: str) -> str:
    if not isinstance(value, str):
        raise _EvidenceError(owner + ":EXPECTED_STRING")
    if not value:
        raise _EvidenceError(owner + ":MISSING")
    return value


def _required_sha(value: object, owner: str) -> str:
    text = _required_string(value, owner)
    if not _SHA256_RE.fullmatch(text):
        raise _EvidenceError(owner + ":MALFORMED_SHA256")
    return text


def _strict_bool(value: object, owner: str) -> bool:
    if type(value) is bool:
        return value
    if isinstance(value, str) and value in {"true", "false"}:
        return value == "true"
    raise _EvidenceError(owner + ":EXPECTED_STRICT_BOOLEAN")


def _required_int(value: object, owner: str) -> int:
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        return int(value)
    raise _EvidenceError(owner + ":EXPECTED_NONNEGATIVE_INTEGER")


def _json_list(value: object, owner: str) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise _EvidenceError(owner + ":MALFORMED_JSON") from error
    if not isinstance(value, list):
        raise _EvidenceError(owner + ":EXPECTED_LIST")
    return value


def _coordinates(value: object, owner: str) -> tuple[float, float, float]:
    parsed = _json_list(value, owner)
    if len(parsed) != 3:
        raise _EvidenceError(owner + ":EXPECTED_THREE_COORDINATES")
    result: list[float] = []
    for coordinate in parsed:
        if type(coordinate) not in {int, float}:
            raise _EvidenceError(owner + ":COORDINATE_TYPE_INVALID")
        numeric = float(coordinate)
        if not math.isfinite(numeric):
            raise _EvidenceError(owner + ":COORDINATE_NONFINITE")
        result.append(numeric)
    return tuple(result)  # type: ignore[return-value]


def _normalized_sequence(value: str) -> str:
    return "".join(value.split()).upper()


def _token_scalar(tokens: Sequence[str], tag: str) -> str:
    indices = [index for index, token in enumerate(tokens) if token == tag]
    if len(indices) != 1 or indices[0] + 1 >= len(tokens):
        raise ValueError("MMCIF_SCALAR_NOT_UNIQUE:" + tag)
    value = tokens[indices[0] + 1]
    if value.startswith("_") or value == "loop_":
        raise ValueError("MMCIF_SCALAR_VALUE_INVALID:" + tag)
    return value


def _read_sha_bound_cache_file(
    *, path: Path, expected_bytes: int, expected_sha256: str, owner: str
) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(owner + "_CACHE_FILE_INVALID")
    before = path.stat()
    payload = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(owner + "_CACHE_FILE_CHANGED_DURING_READ")
    if len(payload) != expected_bytes:
        raise ValueError(owner + "_BYTE_COUNT_MISMATCH")
    if _sha(payload) != expected_sha256:
        raise ValueError(owner + "_SHA256_MISMATCH")
    return payload


def _acquisition_bindings(repo_root: Path) -> dict[str, dict[str, Any]]:
    acquisition = _read_json_object(repo_root / UPSTREAM_ACQUISITION_RELATIVE)
    ccd_rows = acquisition.get("ccd_components")
    structure_rows = acquisition.get("structures")
    if not isinstance(ccd_rows, list) or not isinstance(structure_rows, list):
        raise ValueError("ACQUISITION_BINDING_COLLECTION_INVALID")
    result: dict[str, dict[str, Any]] = {}
    for prefix, key, rows in (
        ("CCD", "ccd_id", ccd_rows),
        ("PDB", "pdb_id", structure_rows),
    ):
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("ACQUISITION_BINDING_ROW_INVALID")
            identity = row.get(key)
            if isinstance(identity, str) and identity:
                combined = prefix + ":" + identity.upper()
                if combined in result:
                    raise ValueError("ACQUISITION_BINDING_DUPLICATE:" + combined)
                result[combined] = row
    return result


def _parse_official_ccd(
    *, repo_root: Path, cache_root: Path, component_id: str
) -> dict[str, Any]:
    bindings = _acquisition_bindings(repo_root)
    row = bindings.get("CCD:" + component_id)
    if row is None or row.get("status") != "CCD_COMPONENT_RESOLVED":
        raise ValueError("OFFICIAL_CCD_ACQUISITION_BINDING_MISSING:" + component_id)
    expected_sha = _required_sha(row.get("sha256"), "ccd_acquisition.sha256")
    expected_bytes = _required_int(
        row.get("byte_count"), "ccd_acquisition.byte_count"
    )
    payload = _read_sha_bound_cache_file(
        path=cache_root / "rcsb" / "ccd" / (component_id + ".cif"),
        expected_bytes=expected_bytes,
        expected_sha256=expected_sha,
        owner=component_id + "_OFFICIAL_CCD",
    )
    text = payload.decode("utf-8")
    tokens = common._tokenize_mmcif_metadata(text)
    atoms_raw = common._loop_rows_from_tokens(tokens, "_chem_comp_atom.")
    bonds_raw = common._loop_rows_from_tokens(tokens, "_chem_comp_bond.")
    descriptor_rows = common._loop_rows_from_tokens(
        tokens, "_pdbx_chem_comp_descriptor."
    )
    identifier_rows = common._loop_rows_from_tokens(
        tokens, "_pdbx_chem_comp_identifier."
    )
    atoms: list[dict[str, Any]] = []
    for row_index, atom in enumerate(atoms_raw):
        if atom.get("_chem_comp_atom.comp_id") != component_id:
            raise ValueError("OFFICIAL_CCD_ATOM_COMPONENT_MISMATCH")
        try:
            charge = int(atom.get("_chem_comp_atom.charge", ""))
        except ValueError as error:
            raise ValueError("OFFICIAL_CCD_ATOM_CHARGE_INVALID") from error
        atoms.append(
            {
                "atom_id": str(atom.get("_chem_comp_atom.atom_id", "")),
                "element": str(atom.get("_chem_comp_atom.type_symbol", "")),
                "formal_charge": charge,
                "aromatic_flag": str(
                    atom.get("_chem_comp_atom.pdbx_aromatic_flag", "")
                ),
                "leaving_atom_flag": str(
                    atom.get("_chem_comp_atom.pdbx_leaving_atom_flag", "")
                ),
                "stereo_config": str(
                    atom.get("_chem_comp_atom.pdbx_stereo_config", "")
                ),
                "source_row_index": row_index,
            }
        )
    bonds: list[dict[str, str]] = []
    for bond in bonds_raw:
        if bond.get("_chem_comp_bond.comp_id") != component_id:
            raise ValueError("OFFICIAL_CCD_BOND_COMPONENT_MISMATCH")
        bonds.append(
            {
                "atom_id_1": str(bond.get("_chem_comp_bond.atom_id_1", "")),
                "atom_id_2": str(bond.get("_chem_comp_bond.atom_id_2", "")),
                "bond_order": str(bond.get("_chem_comp_bond.value_order", "")),
                "aromatic_flag": str(
                    bond.get("_chem_comp_bond.pdbx_aromatic_flag", "")
                ),
                "stereo_config": str(
                    bond.get("_chem_comp_bond.pdbx_stereo_config", "")
                ),
            }
        )
    if len(atoms) != 18 or len({item["atom_id"] for item in atoms}) != 18:
        raise ValueError("OFFICIAL_CCD_ATOM_IDENTITY_INVALID:" + component_id)
    atom_ids = {item["atom_id"] for item in atoms}
    if len(bonds) != 17 or any(
        bond["atom_id_1"] not in atom_ids or bond["atom_id_2"] not in atom_ids
        for bond in bonds
    ):
        raise ValueError("OFFICIAL_CCD_BOND_IDENTITY_INVALID:" + component_id)
    inchikeys = {
        str(row.get("_pdbx_chem_comp_descriptor.descriptor", ""))
        for row in descriptor_rows
        if row.get("_pdbx_chem_comp_descriptor.comp_id") == component_id
        and row.get("_pdbx_chem_comp_descriptor.type") == "InChIKey"
        and row.get("_pdbx_chem_comp_descriptor.program") == "InChI"
    }
    if len(inchikeys) != 1:
        raise ValueError("OFFICIAL_CCD_INCHIKEY_NOT_UNIQUE:" + component_id)
    systematic_names = sorted(
        {
            str(row.get("_pdbx_chem_comp_identifier.identifier", ""))
            for row in identifier_rows
            if row.get("_pdbx_chem_comp_identifier.comp_id") == component_id
            and row.get("_pdbx_chem_comp_identifier.type") == "SYSTEMATIC NAME"
        }
    )
    atom_stereo = {
        item["atom_id"]: item["stereo_config"]
        for item in atoms
        if item["stereo_config"] not in {"", "N"}
    }
    heavy_atoms = [item for item in atoms if item["element"] != "H"]
    composition = Counter(item["element"] for item in heavy_atoms)
    heavy_bonds = [
        item
        for item in bonds
        if next(a for a in atoms if a["atom_id"] == item["atom_id_1"])[
            "element"
        ]
        != "H"
        and next(a for a in atoms if a["atom_id"] == item["atom_id_2"])[
            "element"
        ]
        != "H"
    ]
    return {
        "component_id": component_id,
        "source_binding": {
            "bounded_cache_relative_path": "rcsb/ccd/" + component_id + ".cif",
            "official_url": row.get("official_ccd_url"),
            "byte_count": len(payload),
            "sha256": expected_sha,
        },
        "inchikey": next(iter(inchikeys)),
        "systematic_names": systematic_names,
        "atom_stereo_config": dict(sorted(atom_stereo.items())),
        "atom_identity": [
            {key: item[key] for key in item if key != "source_row_index"}
            for item in atoms
        ],
        "bond_identity": bonds,
        "heavy_atom_count": len(heavy_atoms),
        "heavy_element_composition": dict(sorted(composition.items())),
        "all_atom_formal_charges_zero": all(
            item["formal_charge"] == 0 for item in atoms
        ),
        "all_heavy_bonds_single": all(
            item["bond_order"] == "SING" for item in heavy_bonds
        ),
    }


def _derive_attribute_preserving_automorphisms(
    ccd_identity: Mapping[str, Any], *, calibration_seed_atom: str
) -> dict[str, Any]:
    """Enumerate automorphisms from official atom/bond attributes only."""

    atoms_raw = ccd_identity.get("atom_identity")
    bonds_raw = ccd_identity.get("bond_identity")
    if not isinstance(atoms_raw, list) or not isinstance(bonds_raw, list):
        raise ValueError("DTT_AUTOMORPHISM_GRAPH_INPUT_INVALID")
    nodes: dict[str, tuple[Any, ...]] = {}
    for atom in atoms_raw:
        if not isinstance(atom, Mapping):
            raise ValueError("DTT_AUTOMORPHISM_ATOM_INVALID")
        atom_id = str(atom.get("atom_id", ""))
        attribute = (
            atom.get("element"),
            atom.get("formal_charge"),
            atom.get("aromatic_flag"),
            atom.get("leaving_atom_flag"),
            atom.get("stereo_config"),
        )
        if not atom_id or atom_id in nodes:
            raise ValueError("DTT_AUTOMORPHISM_ATOM_ID_INVALID")
        nodes[atom_id] = attribute
    edges: dict[frozenset[str], tuple[Any, ...]] = {}
    neighbors: dict[str, set[str]] = {atom_id: set() for atom_id in nodes}
    for bond in bonds_raw:
        if not isinstance(bond, Mapping):
            raise ValueError("DTT_AUTOMORPHISM_BOND_INVALID")
        left, right = str(bond.get("atom_id_1", "")), str(
            bond.get("atom_id_2", "")
        )
        key = frozenset((left, right))
        if left not in nodes or right not in nodes or len(key) != 2 or key in edges:
            raise ValueError("DTT_AUTOMORPHISM_EDGE_INVALID")
        edges[key] = (
            bond.get("bond_order"),
            bond.get("aromatic_flag"),
            bond.get("stereo_config"),
        )
        neighbors[left].add(right)
        neighbors[right].add(left)
    if calibration_seed_atom not in nodes:
        raise ValueError("DTT_AUTOMORPHISM_CALIBRATION_SEED_MISSING")

    candidates = {
        source: tuple(
            sorted(
                target
                for target in nodes
                if nodes[target] == nodes[source]
                and len(neighbors[target]) == len(neighbors[source])
                and sorted(
                    (nodes[item], edges[frozenset((source, item))])
                    for item in neighbors[source]
                )
                == sorted(
                    (nodes[item], edges[frozenset((target, item))])
                    for item in neighbors[target]
                )
            )
        )
        for source in nodes
    }
    order = sorted(
        nodes, key=lambda item: (len(candidates[item]), -len(neighbors[item]), item)
    )
    mappings: list[dict[str, str]] = []

    def extend(mapping: dict[str, str], used: set[str]) -> None:
        if len(mapping) == len(order):
            mappings.append(dict(sorted(mapping.items())))
            return
        source = order[len(mapping)]
        for target in candidates[source]:
            if target in used:
                continue
            compatible = True
            for prior_source, prior_target in mapping.items():
                source_edge = edges.get(frozenset((source, prior_source)))
                target_edge = edges.get(frozenset((target, prior_target)))
                if source_edge != target_edge:
                    compatible = False
                    break
            if compatible:
                mapping[source] = target
                used.add(target)
                extend(mapping, used)
                used.remove(target)
                del mapping[source]

    extend({}, set())
    node_order = sorted(nodes)
    mappings.sort(key=lambda item: tuple(item[node] for node in node_order))
    if not mappings:
        raise ValueError("DTT_ENDPOINT_AUTOMORPHISM_NOT_REPRODUCED")
    identity = {node: node for node in node_order}
    if identity not in mappings:
        raise ValueError("DTT_AUTOMORPHISM_IDENTITY_MISSING")
    orbit = sorted({mapping[calibration_seed_atom] for mapping in mappings})
    if (
        len(orbit) != 2
        or any(nodes[atom][0] != "S" for atom in orbit)
        or calibration_seed_atom not in orbit
    ):
        raise ValueError("DTT_ENDPOINT_AUTOMORPHISM_ORBIT_INVALID")
    swaps = [
        mapping
        for mapping in mappings
        if mapping[calibration_seed_atom] != calibration_seed_atom
    ]
    if not swaps or any(set(mapping) != set(nodes) for mapping in swaps):
        raise ValueError("DTT_ENDPOINT_AUTOMORPHISM_SWAP_MISSING")
    inventory_digest = _sha(_json_bytes(mappings))
    return {
        "DTT_ENDPOINT_AUTOMORPHISM_PROVEN": True,
        "derivation_source": "OFFICIAL_SHA_BOUND_DTT_CCD_ATTRIBUTE_GRAPH",
        "calibration_seed_atom": calibration_seed_atom,
        "attribute_contract": [
            "element",
            "formal_charge",
            "aromatic_flag",
            "leaving_atom_flag",
            "atom_stereo_config",
            "bond_order",
            "bond_aromatic_flag",
            "bond_stereo_config",
        ],
        "automorphism_count": len(mappings),
        "automorphism_mappings": mappings,
        "automorphism_inventory_sha256": inventory_digest,
        "reactive_sulfur_orbit": orbit,
        "deterministic_endpoint_swap_mapping": swaps[0],
        "hydrogen_atoms_in_swap_mapping": sorted(
            atom for atom in swaps[0] if nodes[atom][0] == "H"
        ),
    }


def _build_independent_1fvg_reagent_context(
    *, repo_root: Path, cache_root: Path
) -> dict[str, Any]:
    bindings = _acquisition_bindings(repo_root)
    row = bindings.get("PDB:" + SOURCE_STRUCTURE_ID)
    if row is None or row.get("acquisition_status") != "SOURCE_VERIFIED":
        raise ValueError("SOURCE_STRUCTURE_ACQUISITION_BINDING_MISSING")
    expected_sha = _required_sha(
        row.get("compressed_sha256"), "structure_acquisition.compressed_sha256"
    )
    expected_bytes = _required_int(
        row.get("compressed_byte_count"),
        "structure_acquisition.compressed_byte_count",
    )
    payload = _read_sha_bound_cache_file(
        path=cache_root / "rcsb" / "structures" / "1FVG.cif.gz",
        expected_bytes=expected_bytes,
        expected_sha256=expected_sha,
        owner="SOURCE_1FVG_MMCIF",
    )
    try:
        text = gzip.decompress(payload).decode("utf-8", "replace")
    except (OSError, EOFError) as error:
        raise ValueError("SOURCE_1FVG_MMCIF_GZIP_INVALID") from error
    metadata = common._without_atom_site_loop(text)
    tokens = common._tokenize_mmcif_metadata(metadata)
    entities = common._loop_rows_from_tokens(tokens, "_entity.")
    nonpoly = common._loop_rows_from_tokens(tokens, "_pdbx_entity_nonpoly.")
    sequence_rows = common._loop_rows_from_tokens(tokens, "_entity_poly_seq.")
    if len(entities) != 3:
        raise ValueError("SOURCE_1FVG_ENTITY_COUNT_INVALID")
    polymer = [row for row in entities if row.get("_entity.id") == "1"]
    dtt_entity = [
        row
        for row in nonpoly
        if row.get("_pdbx_entity_nonpoly.comp_id") == "DTT"
    ]
    if len(polymer) != 1 or len(dtt_entity) != 1:
        raise ValueError("SOURCE_1FVG_REAGENT_ENTITY_BINDING_INVALID")
    struct_ref = common._scalar_category(
        metadata,
        "_struct_ref.",
        wanted_fields=frozenset(
            {
                "_struct_ref.id",
                "_struct_ref.db_code",
                "_struct_ref.db_name",
                "_struct_ref.entity_id",
                "_struct_ref.pdbx_db_accession",
            }
        ),
    )
    crystallization = common._scalar_category(
        metadata,
        "_exptl_crystal_grow.",
        wanted_fields=frozenset(
            {
                "_exptl_crystal_grow.crystal_id",
                "_exptl_crystal_grow.method",
                "_exptl_crystal_grow.pH",
                "_exptl_crystal_grow.temp",
                "_exptl_crystal_grow.pdbx_details",
            }
        ),
    )
    structure = common._scalar_category(
        metadata,
        "_struct.",
        wanted_fields=frozenset({"_struct.entry_id", "_struct.title"}),
    )
    reference_sequence = _normalized_sequence(
        _token_scalar(tokens, "_struct_ref.pdbx_seq_one_letter_code")
    )
    record = {
        "entry_id": structure.get("_struct.entry_id"),
        "structure_title": structure.get("_struct.title"),
        "polymer_entity": {
            "entity_id": polymer[0].get("_entity.id"),
            "type": polymer[0].get("_entity.type"),
            "description": polymer[0].get("_entity.pdbx_description"),
            "ec": polymer[0].get("_entity.pdbx_ec"),
            "details": polymer[0].get("_entity.details"),
        },
        "dtt_nonpolymer_entity": {
            "entity_id": dtt_entity[0].get("_pdbx_entity_nonpoly.entity_id"),
            "name": dtt_entity[0].get("_pdbx_entity_nonpoly.name"),
            "component_id": dtt_entity[0].get("_pdbx_entity_nonpoly.comp_id"),
        },
        "crystallization": {
            "crystal_id": crystallization.get(
                "_exptl_crystal_grow.crystal_id"
            ),
            "method": crystallization.get("_exptl_crystal_grow.method"),
            "pH": crystallization.get("_exptl_crystal_grow.pH"),
            "temperature_kelvin": crystallization.get(
                "_exptl_crystal_grow.temp"
            ),
            "details": crystallization.get(
                "_exptl_crystal_grow.pdbx_details"
            ),
        },
        "protein_reference": {
            "reference_id": struct_ref.get("_struct_ref.id"),
            "db_code": struct_ref.get("_struct_ref.db_code"),
            "db_name": struct_ref.get("_struct_ref.db_name"),
            "entity_id": struct_ref.get("_struct_ref.entity_id"),
            "accession": struct_ref.get("_struct_ref.pdbx_db_accession"),
            "struct_ref_sequence_sha256": _sha(reference_sequence.encode("utf-8")),
            "entity_poly_seq_sha256": common._exact_entity_sequence_sha256(
                sequence_rows, "1"
            ),
        },
    }
    details = str(record["crystallization"]["details"] or "")
    polymer_details = str(record["polymer_entity"]["details"] or "")
    if (
        record["entry_id"] != SOURCE_STRUCTURE_ID
        or expected_sha != SOURCE_STRUCTURE_SHA256
        or record["dtt_nonpolymer_entity"]["component_id"] != "DTT"
        or record["polymer_entity"]["description"]
        != "PEPTIDE METHIONINE SULFOXIDE REDUCTASE"
        or polymer_details != "DITHIOTHREITOL COMPLEX"
        or "dithiothreitol" not in details.lower()
        or record["protein_reference"]["accession"]
        != SOURCE_PROTEIN_ACCESSION
        or record["protein_reference"]["entity_poly_seq_sha256"]
        != SOURCE_PROTEIN_SEQUENCE_SHA256
    ):
        raise ValueError("SOURCE_1FVG_REAGENT_CONTEXT_MISMATCH")
    return {
        "source_binding": {
            "bounded_cache_relative_path": "rcsb/structures/1FVG.cif.gz",
            "official_url": row.get("official_structure_url"),
            "compressed_byte_count": len(payload),
            "compressed_sha256": expected_sha,
        },
        "normalized_metadata_record": record,
        "normalized_metadata_record_sha256": _sha(_json_bytes(record)),
        "selection_contract": (
            "SHA_BOUND_1FVG_ENTRY_PLUS_STRUCTURED_DTT_NONPOLY_ENTITY_PLUS_"
            "ENTITY_DETAILS_DITHIOTHREITOL_COMPLEX_PLUS_CRYSTALLIZATION_"
            "DETAILS_PLUS_UNP_ACCESSION_AND_SEQUENCE"
        ),
        "pdb_id_is_not_a_sole_predicate": True,
        "crystallization_word_is_not_a_sole_predicate": True,
        "not_cross_pdb_generalization": True,
    }


def load_immutable_dtt_human_gold_v1(repo_root: Path) -> dict[str, Any]:
    """Read and validate DTT calibration state from the exact Git object."""

    object_spec = CALIBRATION_COMMIT + ":" + HUMAN_DECISIONS_RELATIVE.as_posix()
    payload = subprocess.run(
        ["git", "show", object_spec],
        cwd=repo_root.resolve(),
        check=True,
        capture_output=True,
    ).stdout
    if len(payload) != CALIBRATION_HUMAN_BYTES:
        raise ValueError("CALIBRATION_HUMAN_BYTES_MISMATCH")
    if _sha(payload) != CALIBRATION_HUMAN_SHA256:
        raise ValueError("CALIBRATION_HUMAN_SHA256_MISMATCH")
    value = json.loads(payload)
    if not isinstance(value, dict) or value.get("schema_version") != (
        "covapie_post_only_human_review_decisions_v1"
    ):
        raise ValueError("CALIBRATION_HUMAN_ROOT_OR_SCHEMA_INVALID")
    units = value.get("units")
    history = value.get("decision_history")
    if not isinstance(units, list) or not isinstance(history, list):
        raise ValueError("CALIBRATION_HUMAN_COLLECTION_INVALID")
    matches = [
        unit
        for unit in units
        if isinstance(unit, dict)
        and unit.get("review_unit_id") == CALIBRATION_UNIT_ID
    ]
    if len(matches) != 1:
        raise ValueError("DTT_CALIBRATION_UNIT_NOT_UNIQUE")
    unit = matches[0]
    expected = {
        "workflow_status": "COMPLETED",
        "training_domain_relevance_decision": (
            "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
        ),
        "reactive_atom_confirmation": None,
        "warhead_family_decision": None,
        "warhead_atom_ids": [],
        "roles": {
            "linker_atom_ids": [],
            "scaffold_atom_ids": [],
            "warhead_atom_ids": [],
        },
        "review_rationale": CALIBRATION_RATIONALE,
    }
    for field, expected_value in expected.items():
        if unit.get(field) != expected_value:
            raise ValueError("DTT_CALIBRATION_HUMAN_STATE_MISMATCH:" + field)
    events = unit.get("events")
    if not isinstance(events, list) or len(events) != 1:
        raise ValueError("DTT_CALIBRATION_EVENT_COUNT_MISMATCH")
    if any(
        not isinstance(event, dict)
        or not isinstance(event.get("canonical_event_id"), str)
        or any(
            event.get(field) != ""
            for field in (
                "post_geometry_training_usable",
                "event_training_use_decision",
                "event_exclusion_reason",
            )
        )
        for event in events
    ):
        raise ValueError("DTT_CALIBRATION_EVENT_DECISION_INVALID")
    unit_history = [
        item
        for item in history
        if isinstance(item, dict)
        and item.get("review_unit_id") == CALIBRATION_UNIT_ID
    ]
    expected_history = (
        (
            "training_domain_relevance_decision",
            "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
        ),
        ("workflow_status", "COMPLETED"),
        ("reviewer_id", "fmx"),
        ("reviewed_at_utc", unit.get("reviewed_at_utc")),
        ("review_rationale", CALIBRATION_RATIONALE),
    )
    observed_history = tuple(
        (item.get("field"), item.get("new_value")) for item in unit_history
    )
    if observed_history != expected_history:
        raise ValueError("DTT_CALIBRATION_HUMAN_HISTORY_MISMATCH")
    sequences = [item.get("sequence") for item in unit_history]
    if (
        any(type(item) is not int for item in sequences)
        or sequences != list(range(sequences[0], sequences[0] + len(sequences)))
        or any(
            not isinstance(item.get("entry_sha256"), str)
            or not _SHA256_RE.fullmatch(item["entry_sha256"])
            for item in unit_history
        )
    ):
        raise ValueError("DTT_CALIBRATION_HUMAN_HISTORY_CHAIN_INVALID")
    return value


def _load_calibration_snapshot_evidence_v1(repo_root: Path) -> dict[str, Any]:
    input_hashes = verify_bound_inputs_v1(repo_root)
    with (repo_root / EVENT_INVENTORY_RELATIVE).open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        candidate_rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("post_only_partition") == "POST_ONLY_V1_REVIEW_CANDIDATE"
        ]
    if len(candidate_rows) != 123:
        raise ValueError("CANDIDATE_EVENT_COUNT_MISMATCH")
    event_by_id = {row.get("canonical_event_id", ""): row for row in candidate_rows}
    if len(event_by_id) != 123 or "" in event_by_id:
        raise ValueError("CANDIDATE_EVENT_ID_INVALID_OR_DUPLICATE")
    packet = _read_json_object(repo_root / REVIEW_PACKET_RELATIVE)
    units = packet.get("review_units")
    if not isinstance(units, list) or len(units) != 36:
        raise ValueError("REVIEW_PACKET_UNIT_COUNT_MISMATCH")
    unit_by_id: dict[str, dict[str, Any]] = {}
    unit_by_event: dict[str, str] = {}
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("REVIEW_PACKET_UNIT_NOT_OBJECT")
        unit_id = unit.get("review_unit_id")
        event_ids = unit.get("canonical_event_ids")
        if (
            not isinstance(unit_id, str)
            or not unit_id
            or unit_id in unit_by_id
            or not isinstance(event_ids, list)
            or not event_ids
        ):
            raise ValueError("REVIEW_PACKET_UNIT_ID_OR_EVENTS_INVALID")
        unit_by_id[unit_id] = unit
        for event_id in event_ids:
            if not isinstance(event_id, str) or event_id in unit_by_event:
                raise ValueError("EVENT_REVIEW_UNIT_MEMBERSHIP_INVALID")
            unit_by_event[event_id] = unit_id
    if set(unit_by_event) != set(event_by_id):
        raise ValueError("REVIEW_UNIT_CANDIDATE_EVENT_COVERAGE_MISMATCH")
    outcomes_raw = _read_json_object(repo_root / UPSTREAM_OUTCOMES_RELATIVE).get(
        "events"
    )
    if not isinstance(outcomes_raw, list):
        raise ValueError("UPSTREAM_OUTCOME_EVENTS_INVALID")
    outcome_by_id = {
        item.get("canonical_event_id", ""): item
        for item in outcomes_raw
        if isinstance(item, dict)
    }
    if not set(event_by_id) <= set(outcome_by_id):
        raise ValueError("CANDIDATE_OUTCOME_COVERAGE_MISMATCH")
    legacy = _read_json_object(repo_root / LEGACY_SUMMARY_RELATIVE)
    if (
        legacy.get("population", {}).get("post_only_v1_review_candidate_count")
        != 123
        or legacy.get("human_review_workload", {}).get("review_unit_count") != 36
    ):
        raise ValueError("LEGACY_SUMMARY_POPULATION_MISMATCH")
    human = load_immutable_dtt_human_gold_v1(repo_root)
    human_units = human.get("units")
    if not isinstance(human_units, list):
        raise ValueError("CALIBRATION_HUMAN_UNITS_INVALID")
    human_unit_by_id = {
        item.get("review_unit_id", ""): item
        for item in human_units
        if isinstance(item, dict)
    }
    if set(human_unit_by_id) != set(unit_by_id):
        raise ValueError("CALIBRATION_HUMAN_REVIEW_UNIT_COVERAGE_MISMATCH")
    return {
        "input_hashes": input_hashes,
        "event_by_id": event_by_id,
        "outcome_by_id": outcome_by_id,
        "unit_by_id": unit_by_id,
        "unit_by_event": unit_by_event,
        "calibration_human": human,
        "calibration_human_unit_by_id": human_unit_by_id,
        "legacy_summary": legacy,
    }


def _calibration_machine_pair(
    repo_root: Path, calibration_human: Mapping[str, Any]
) -> tuple[dict[str, str], dict[str, Any]]:
    units = calibration_human.get("units")
    if not isinstance(units, list):
        raise ValueError("DTT_CALIBRATION_UNITS_INVALID")
    unit = next(
        item
        for item in units
        if isinstance(item, dict) and item.get("review_unit_id") == CALIBRATION_UNIT_ID
    )
    calibration_event_id = unit["events"][0]["canonical_event_id"]
    with (repo_root / EVENT_INVENTORY_RELATIVE).open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        event_matches = [
            row
            for row in csv.DictReader(handle)
            if row.get("canonical_event_id") == calibration_event_id
        ]
    outcomes = _read_json_object(repo_root / UPSTREAM_OUTCOMES_RELATIVE).get(
        "events"
    )
    if not isinstance(outcomes, list):
        raise ValueError("DTT_CALIBRATION_OUTCOMES_INVALID")
    outcome_matches = [
        row
        for row in outcomes
        if isinstance(row, dict)
        and row.get("canonical_event_id") == calibration_event_id
    ]
    if len(event_matches) != 1 or len(outcome_matches) != 1:
        raise ValueError("DTT_CALIBRATION_MACHINE_EVENT_NOT_UNIQUE")
    return event_matches[0], outcome_matches[0]


def _build_static_rule_context_v1(
    *, repo_root: Path, cache_root: Path
) -> Mapping[str, Any]:
    """Construct the rule from calibration and independent sources only."""

    verify_bound_inputs_v1(repo_root)
    calibration_human = load_immutable_dtt_human_gold_v1(repo_root)
    calibration_event, calibration_outcome = _calibration_machine_pair(
        repo_root, calibration_human
    )
    dtt = _parse_official_ccd(
        repo_root=repo_root, cache_root=cache_root, component_id="DTT"
    )
    if (
        dtt["source_binding"]["sha256"] != DTT_CCD_SOURCE_SHA256
        or dtt["inchikey"] != DTT_INCHIKEY
        or dtt["atom_stereo_config"] != {"C2": "R", "C3": "R"}
        or dtt["heavy_atom_count"] != 8
        or dtt["heavy_element_composition"] != {"C": 4, "O": 2, "S": 2}
        or dtt["all_atom_formal_charges_zero"] is not True
        or dtt["all_heavy_bonds_single"] is not True
    ):
        raise ValueError("OFFICIAL_DTT_CCD_IDENTITY_MISMATCH")
    seed_atom = calibration_event.get("ligand_reactive_atom")
    if not isinstance(seed_atom, str) or not seed_atom:
        raise ValueError("DTT_CALIBRATION_ENDPOINT_INVALID")
    automorphism = _derive_attribute_preserving_automorphisms(
        dtt, calibration_seed_atom=seed_atom
    )
    reagent = _build_independent_1fvg_reagent_context(
        repo_root=repo_root, cache_root=cache_root
    )
    structural = calibration_outcome.get("structural_processing")
    if not isinstance(structural, Mapping):
        raise ValueError("DTT_CALIBRATION_STRUCTURAL_EVIDENCE_INVALID")
    leakage = structural.get("leakage_evidence")
    if not isinstance(leakage, Mapping):
        raise ValueError("DTT_CALIBRATION_LEAKAGE_EVIDENCE_INVALID")
    if (
        calibration_event.get("pdb_id") != SOURCE_STRUCTURE_ID
        or calibration_event.get("ligand_component_id") != "DTT"
        or calibration_event.get("ligand_instance") != "B"
        or calibration_event.get("ccd_component_graph_sha256")
        != DTT_GRAPH_SHA256
        or calibration_event.get("ccd_heavy_atom_map_sha256")
        != DTT_HEAVY_MAP_SHA256
        or calibration_event.get("ligand_reactive_element") != "S"
        or calibration_event.get("reactive_center_radius1_fingerprint")
        != DTT_RADIUS1_SHA256
        or calibration_event.get("reactive_center_radius2_fingerprint")
        != DTT_RADIUS2_SHA256
        or calibration_event.get("reactive_center_local_topology")
        != DTT_LOCAL_TOPOLOGY
        or structural.get("mmcif_entry_id") != SOURCE_STRUCTURE_ID
        or leakage.get("protein_accession") != SOURCE_PROTEIN_ACCESSION
        or leakage.get("protein_sequence_sha256")
        != SOURCE_PROTEIN_SEQUENCE_SHA256
    ):
        raise ValueError("DTT_CALIBRATION_MACHINE_CHEMISTRY_MISMATCH")
    context = {
        "schema_version": SCHEMA_VERSION,
        "rule_id": RULE_ID,
        "rule_role": RULE_ROLE,
        "exact_ligand_identity": {
            "component_id": "DTT",
            "ccd_component_graph_sha256": DTT_GRAPH_SHA256,
            "ccd_heavy_atom_map_sha256": DTT_HEAVY_MAP_SHA256,
            "reactive_element": "S",
            "radius1_sha256": DTT_RADIUS1_SHA256,
            "radius2_sha256": DTT_RADIUS2_SHA256,
            "local_topology": DTT_LOCAL_TOPOLOGY,
            "official_ccd_identity": dtt,
        },
        "endpoint_automorphism": automorphism,
        "independent_1fvg_reagent_context": reagent,
        "calibration_seed": {
            "immutable_human_git_object": (
                CALIBRATION_COMMIT + ":" + HUMAN_DECISIONS_RELATIVE.as_posix()
            ),
            "review_unit_id": CALIBRATION_UNIT_ID,
            "canonical_event_id": calibration_event["canonical_event_id"],
            "reactive_atom": seed_atom,
        },
        "required_predicates": list(REQUIRED_PREDICATES),
        "forbidden_sole_predicates": list(FORBIDDEN_SOLE_PREDICATES),
        "shadow_label_leakage_prohibited": True,
        "rule_context_was_derived_from_shadow_population": False,
        "rule_context_is_independent_of_shadow_evaluation_population": True,
        "cross_CCD_DTU_generalization_authorized": False,
        "cross_pdb_dtt_generalization_authorized": False,
        "generic_reducing_agent_authority_created": False,
        "distance_is_rule_identity_predicate": False,
    }
    return _freeze(context)


def build_static_rule_context_v1(
    *, repo_root: Path, cache_root: Path | None = None
) -> Mapping[str, Any]:
    resolved = (
        cache_root.resolve()
        if cache_root is not None
        else repo_root.resolve().parent / CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    return _build_static_rule_context_v1(
        repo_root=repo_root.resolve(), cache_root=resolved
    )


def static_rule_context_bytes_v1(context: Mapping[str, Any]) -> bytes:
    return _json_bytes(_thaw(context))


def build_runtime_positive_override_context_v1(**kwargs: Any) -> Any:
    return common.build_runtime_positive_override_context_v1(**kwargs)


def validate_current_human_overlay_v1(
    value: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    return common.validate_current_human_overlay_v1(value)


def build_calibration_snapshot_positive_override_context_v1(
    *,
    immutable_calibration_human: Mapping[str, Any],
    frozen_outcome_by_id: Mapping[str, Mapping[str, Any]],
) -> RuntimePositiveOverrideContext:
    return common.build_runtime_positive_override_context_v1(
        current_human_overlay=immutable_calibration_human,
        current_human_overlay_sha256=CALIBRATION_HUMAN_SHA256,
        outcome_by_id=frozen_outcome_by_id,
    )


def _context_values(rule_context: Mapping[str, Any]) -> dict[str, Any]:
    if _required_string(rule_context.get("rule_id"), "rule_context.rule_id") != RULE_ID:
        raise _EvidenceError("rule_context.rule_id:VALUE_MISMATCH")
    if _required_string(rule_context.get("rule_role"), "rule_context.rule_role") != (
        RULE_ROLE
    ):
        raise _EvidenceError("rule_context.rule_role:VALUE_MISMATCH")
    ligand = _required_mapping(
        rule_context.get("exact_ligand_identity"),
        "rule_context.exact_ligand_identity",
    )
    official = _required_mapping(
        ligand.get("official_ccd_identity"),
        "rule_context.exact_ligand_identity.official_ccd_identity",
    )
    source_binding = _required_mapping(
        official.get("source_binding"), "rule_context.official_ccd.source_binding"
    )
    stereo = _required_mapping(
        official.get("atom_stereo_config"),
        "rule_context.official_ccd.atom_stereo_config",
    )
    if (
        _required_string(ligand.get("component_id"), "rule_context.component_id")
        != "DTT"
        or _required_sha(
            ligand.get("ccd_component_graph_sha256"),
            "rule_context.ccd_component_graph_sha256",
        )
        != DTT_GRAPH_SHA256
        or _required_sha(
            ligand.get("ccd_heavy_atom_map_sha256"),
            "rule_context.ccd_heavy_atom_map_sha256",
        )
        != DTT_HEAVY_MAP_SHA256
        or _required_string(
            ligand.get("reactive_element"), "rule_context.reactive_element"
        )
        != "S"
        or _required_sha(ligand.get("radius1_sha256"), "rule_context.radius1")
        != DTT_RADIUS1_SHA256
        or _required_sha(ligand.get("radius2_sha256"), "rule_context.radius2")
        != DTT_RADIUS2_SHA256
        or _required_string(
            ligand.get("local_topology"), "rule_context.local_topology"
        )
        != DTT_LOCAL_TOPOLOGY
        or _required_sha(source_binding.get("sha256"), "rule_context.ccd_sha")
        != DTT_CCD_SOURCE_SHA256
        or _required_string(official.get("component_id"), "rule_context.ccd_id")
        != "DTT"
        or _required_string(official.get("inchikey"), "rule_context.inchikey")
        != DTT_INCHIKEY
        or dict(stereo) != {"C2": "R", "C3": "R"}
        or _required_int(official.get("heavy_atom_count"), "rule_context.heavy_count")
        != 8
        or dict(
            _required_mapping(
                official.get("heavy_element_composition"),
                "rule_context.heavy_element_composition",
            )
        )
        != {"C": 4, "O": 2, "S": 2}
        or _strict_bool(
            official.get("all_atom_formal_charges_zero"),
            "rule_context.all_atom_formal_charges_zero",
        )
        is not True
        or _strict_bool(
            official.get("all_heavy_bonds_single"),
            "rule_context.all_heavy_bonds_single",
        )
        is not True
    ):
        raise _EvidenceError("rule_context.official_dtt_identity:VALUE_MISMATCH")

    automorphism = _required_mapping(
        rule_context.get("endpoint_automorphism"),
        "rule_context.endpoint_automorphism",
    )
    if _strict_bool(
        automorphism.get("DTT_ENDPOINT_AUTOMORPHISM_PROVEN"),
        "rule_context.DTT_ENDPOINT_AUTOMORPHISM_PROVEN",
    ) is not True:
        raise _EvidenceError("rule_context.endpoint_automorphism:NOT_PROVEN")
    seed = _required_string(
        automorphism.get("calibration_seed_atom"),
        "rule_context.calibration_seed_atom",
    )
    orbit_raw = automorphism.get("reactive_sulfur_orbit")
    mappings_raw = automorphism.get("automorphism_mappings")
    if (
        not isinstance(orbit_raw, Sequence)
        or isinstance(orbit_raw, (str, bytes))
        or not isinstance(mappings_raw, Sequence)
        or isinstance(mappings_raw, (str, bytes))
    ):
        raise _EvidenceError("rule_context.automorphism_inventory:INVALID")
    orbit = tuple(sorted(str(item) for item in orbit_raw))
    mappings: list[dict[str, str]] = []
    for index, mapping in enumerate(mappings_raw):
        parsed = _required_mapping(
            mapping, f"rule_context.automorphism_mappings[{index}]"
        )
        normalized = {str(key): str(value) for key, value in parsed.items()}
        if not normalized or any(not key or not value for key, value in normalized.items()):
            raise _EvidenceError("rule_context.automorphism_mapping:INVALID")
        mappings.append(dict(sorted(normalized.items())))
    observed_orbit = tuple(sorted({mapping.get(seed, "") for mapping in mappings}))
    if (
        len(orbit) != 2
        or seed not in orbit
        or observed_orbit != orbit
        or _required_int(
            automorphism.get("automorphism_count"),
            "rule_context.automorphism_count",
        )
        != len(mappings)
        or _required_sha(
            automorphism.get("automorphism_inventory_sha256"),
            "rule_context.automorphism_inventory_sha256",
        )
        != _sha(_json_bytes(mappings))
    ):
        raise _EvidenceError("rule_context.endpoint_automorphism:VALUE_MISMATCH")

    reagent = _required_mapping(
        rule_context.get("independent_1fvg_reagent_context"),
        "rule_context.independent_1fvg_reagent_context",
    )
    reagent_binding = _required_mapping(
        reagent.get("source_binding"), "rule_context.reagent.source_binding"
    )
    record = _required_mapping(
        reagent.get("normalized_metadata_record"),
        "rule_context.reagent.normalized_metadata_record",
    )
    record_digest = _required_sha(
        reagent.get("normalized_metadata_record_sha256"),
        "rule_context.reagent.normalized_metadata_record_sha256",
    )
    if record_digest != _sha(_json_bytes(_thaw(record))):
        raise _EvidenceError("rule_context.reagent.record_digest:MISMATCH")
    protein = _required_mapping(
        record.get("protein_reference"), "rule_context.reagent.protein_reference"
    )
    nonpoly = _required_mapping(
        record.get("dtt_nonpolymer_entity"),
        "rule_context.reagent.dtt_nonpolymer_entity",
    )
    polymer = _required_mapping(
        record.get("polymer_entity"), "rule_context.reagent.polymer_entity"
    )
    crystallization = _required_mapping(
        record.get("crystallization"), "rule_context.reagent.crystallization"
    )
    if (
        _required_sha(
            reagent_binding.get("compressed_sha256"),
            "rule_context.reagent.compressed_sha256",
        )
        != SOURCE_STRUCTURE_SHA256
        or _required_string(record.get("entry_id"), "rule_context.reagent.entry_id")
        != SOURCE_STRUCTURE_ID
        or _required_string(nonpoly.get("component_id"), "rule_context.nonpoly.id")
        != "DTT"
        or _required_string(polymer.get("details"), "rule_context.polymer.details")
        != "DITHIOTHREITOL COMPLEX"
        or "dithiothreitol"
        not in _required_string(
            crystallization.get("details"), "rule_context.crystallization.details"
        ).lower()
        or _required_string(protein.get("accession"), "rule_context.protein.accession")
        != SOURCE_PROTEIN_ACCESSION
        or _required_sha(
            protein.get("entity_poly_seq_sha256"),
            "rule_context.protein.sequence_sha256",
        )
        != SOURCE_PROTEIN_SEQUENCE_SHA256
    ):
        raise _EvidenceError("rule_context.independent_1fvg_context:VALUE_MISMATCH")
    required_raw = rule_context.get("required_predicates")
    if tuple(required_raw) != REQUIRED_PREDICATES:  # type: ignore[arg-type]
        raise _EvidenceError("rule_context.required_predicates:VALUE_MISMATCH")
    for field, expected in (
        ("shadow_label_leakage_prohibited", True),
        ("rule_context_was_derived_from_shadow_population", False),
        ("rule_context_is_independent_of_shadow_evaluation_population", True),
        ("cross_CCD_DTU_generalization_authorized", False),
        ("cross_pdb_dtt_generalization_authorized", False),
        ("generic_reducing_agent_authority_created", False),
        ("distance_is_rule_identity_predicate", False),
    ):
        if _strict_bool(rule_context.get(field), "rule_context." + field) is not expected:
            raise _EvidenceError("rule_context." + field + ":VALUE_MISMATCH")
    return {
        "orbit": frozenset(orbit),
        "source_record": record,
        "source_record_sha256": record_digest,
    }


def _invalid_result(
    matched: Sequence[str], issues: Sequence[str]
) -> AutoNegativeEvaluationResult:
    return AutoNegativeEvaluationResult(
        rule_id=RULE_ID,
        status=INVALID_EVIDENCE,
        reason="INVALID_EVIDENCE:" + ",".join(sorted(set(issues))),
        matched_predicates=tuple(matched),
    )


def evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
    *,
    event: Mapping[str, Any],
    outcome: Mapping[str, Any],
    rule_context: Mapping[str, Any],
    override_context: RuntimePositiveOverrideContext,
) -> AutoNegativeEvaluationResult:
    """Evaluate the compound DTT rule with fail-closed tri-state semantics."""

    if not isinstance(event, Mapping):
        return _invalid_result((), ("event:EXPECTED_MAPPING",))
    if not isinstance(outcome, Mapping):
        return _invalid_result((), ("outcome:EXPECTED_MAPPING",))
    if not isinstance(rule_context, Mapping):
        return _invalid_result((), ("rule_context:EXPECTED_MAPPING",))
    if type(override_context) is not RuntimePositiveOverrideContext:
        return _invalid_result((), ("override_context:EXPECTED_FROZEN_CONTEXT",))
    try:
        expected = _context_values(rule_context)
        if override_context.schema_version != RUNTIME_OVERRIDE_SCHEMA_VERSION:
            raise _EvidenceError("override_context.schema_version:VALUE_MISMATCH")
        if not _SHA256_RE.fullmatch(override_context.current_human_overlay_sha256):
            raise _EvidenceError("override_context.current_human_overlay_sha256:INVALID")
        override_sets = (
            override_context.current_human_relevant_event_ids,
            override_context.current_production_exact_positive_event_ids,
            override_context.explicit_positive_override_event_ids,
        )
        if any(
            type(values) is not frozenset
            or any(not isinstance(item, str) or not item for item in values)
            for values in override_sets
        ):
            raise _EvidenceError("override_context.event_id_sets:INVALID")
        positive_ids = frozenset().union(*override_sets)
    except _EvidenceError as error:
        return _invalid_result((), (str(error),))

    matched: list[str] = []
    failed: list[str] = []
    invalid: list[str] = []

    def predicate(name: str, reader: Any, expected_value: object) -> None:
        try:
            actual = reader()
        except _EvidenceError as error:
            invalid.append(name + "[" + str(error) + "]")
            return
        if actual == expected_value:
            matched.append(name)
        else:
            failed.append(name)

    def structural() -> Mapping[str, Any]:
        return _required_mapping(
            outcome.get("structural_processing"), "outcome.structural_processing"
        )

    def structural_value(field: str) -> object:
        value = structural()
        if field not in value:
            raise _EvidenceError("outcome.structural_processing." + field + ":MISSING")
        return value[field]

    predicate(
        "candidate_lane",
        lambda: _required_string(
            event.get("post_only_partition"), "event.post_only_partition"
        ),
        "POST_ONLY_V1_REVIEW_CANDIDATE",
    )
    for predicate_name, field in (
        ("structural_model_eligible", "structural_model_eligible"),
        ("feature_compatible", "feature_compatible"),
        ("explicit_cys_sg_covalent_evidence", "explicit_cys_sg_event"),
        (
            "usable_post_complex_structural_evidence",
            "usable_post_complex_structural_evidence",
        ),
        ("full_ligand_coordinates", "full_ligand_coordinates_recoverable"),
        (
            "exact_ccd_observed_heavy_atom_identity_coverage",
            "exact_ccd_observed_heavy_atom_identity_coverage",
        ),
        (
            "exact_ccd_observed_heavy_atom_element_agreement",
            "exact_ccd_observed_heavy_atom_element_agreement",
        ),
        ("exact_reactive_ligand_atom_coverage", "reactive_ligand_atom_exact_coverage"),
        ("pocket_coordinates", "canonical_pocket_coordinates_recoverable"),
    ):
        predicate(
            predicate_name,
            lambda field=field: _strict_bool(event.get(field), "event." + field),
            True,
        )
    predicate(
        "outcome_candidate_route",
        lambda: _required_string(
            outcome.get("terminal_outcome"), "outcome.terminal_outcome"
        ),
        "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
    )

    def feature_status() -> str:
        statuses = _required_mapping(outcome.get("stage_statuses"), "outcome.stage_statuses")
        return _required_string(
            statuses.get("BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"),
            "outcome.stage_statuses.BULK_09_MODEL_AND_FEATURE_COMPATIBILITY",
        )

    predicate("outcome_feature_projection_passed", feature_status, "PASSED")
    predicate(
        "outcome_explicit_covalent_evidence",
        lambda: _strict_bool(
            structural_value("explicit_covalent_evidence"),
            "outcome.structural_processing.explicit_covalent_evidence",
        ),
        True,
    )

    def exact_connection_and_coordinates() -> bool:
        event_connection = _required_string(
            event.get("selected_connection_id"), "event.selected_connection_id"
        )
        outcome_connection = _required_string(
            structural_value("selected_connection_id"),
            "outcome.structural_processing.selected_connection_id",
        )
        event_protein = _coordinates(
            event.get("selected_protein_endpoint_coordinates_json"),
            "event.selected_protein_endpoint_coordinates_json",
        )
        event_ligand = _coordinates(
            event.get("selected_ligand_endpoint_coordinates_json"),
            "event.selected_ligand_endpoint_coordinates_json",
        )
        outcome_protein = _coordinates(
            structural_value("protein_endpoint_coordinates"),
            "outcome.structural_processing.protein_endpoint_coordinates",
        )
        outcome_ligand = _coordinates(
            structural_value("ligand_endpoint_coordinates"),
            "outcome.structural_processing.ligand_endpoint_coordinates",
        )
        return bool(
            event_connection == outcome_connection
            and event_protein == outcome_protein
            and event_ligand == outcome_ligand
        )

    predicate(
        "exact_connection_and_endpoint_coordinates",
        exact_connection_and_coordinates,
        True,
    )

    def exact_component_identity() -> bool:
        graph = _required_mapping(
            structural_value("ccd_component_graph"),
            "outcome.structural_processing.ccd_component_graph",
        )
        return bool(
            _required_string(event.get("ligand_component_id"), "event.ligand_component_id")
            == "DTT"
            and _required_string(outcome.get("ligand_component_id"), "outcome.ligand_component_id")
            == "DTT"
            and _required_string(graph.get("ccd_id"), "outcome.ccd_component_graph.ccd_id")
            == "DTT"
        )

    predicate("exact_dtt_component_identity", exact_component_identity, True)

    def exact_graph_identity() -> bool:
        graph = _required_mapping(
            structural_value("ccd_component_graph"),
            "outcome.structural_processing.ccd_component_graph",
        )
        return bool(
            _required_sha(event.get("ccd_component_graph_sha256"), "event.ccd_graph")
            == DTT_GRAPH_SHA256
            and _required_sha(
                graph.get("ccd_component_graph_sha256"), "outcome.ccd_graph"
            )
            == DTT_GRAPH_SHA256
        )

    predicate("exact_dtt_component_graph_sha256", exact_graph_identity, True)
    predicate(
        "official_dtt_ccd_stereochemical_identity", lambda: True, True
    )

    def exact_heavy_identity() -> bool:
        graph = _required_mapping(
            structural_value("ccd_component_graph"),
            "outcome.structural_processing.ccd_component_graph",
        )
        charges = graph.get("ccd_formal_charge_pattern")
        elements = _required_mapping(
            structural_value("ligand_element_counts"),
            "outcome.structural_processing.ligand_element_counts",
        )
        if not isinstance(charges, list) or len(charges) != 18:
            raise _EvidenceError("outcome.ccd_formal_charge_pattern:INVALID")
        charge_zero = all(
            isinstance(item, list)
            and len(item) == 2
            and isinstance(item[0], str)
            and item[0]
            and item[1] == 0
            for item in charges
        )
        return bool(
            _required_int(event.get("ligand_heavy_atom_count"), "event.heavy_count")
            == 8
            and _required_sha(event.get("ccd_heavy_atom_map_sha256"), "event.heavy_map")
            == DTT_HEAVY_MAP_SHA256
            and _required_int(graph.get("ccd_heavy_atom_count"), "outcome.heavy_count")
            == 8
            and dict(elements) == {"C": 4, "O": 2, "S": 2}
            and charge_zero
        )

    predicate("exact_dtt_heavy_identity_and_charge", exact_heavy_identity, True)
    predicate(
        "automorphism_derived_dtt_sulfur_endpoint",
        lambda: _required_string(
            event.get("ligand_reactive_atom"), "event.ligand_reactive_atom"
        )
        in expected["orbit"],
        True,
    )

    def exact_element() -> bool:
        return bool(
            _required_string(event.get("ligand_reactive_element"), "event.reactive_element")
            == "S"
            and _required_string(
                structural_value("ligand_reactive_element"),
                "outcome.structural_processing.ligand_reactive_element",
            )
            == "S"
        )

    predicate("exact_ligand_reactive_element", exact_element, True)

    def exact_radius(field: str, structural_field: str, expected_sha: str) -> bool:
        return bool(
            _required_sha(event.get(field), "event." + field) == expected_sha
            and _required_sha(
                structural_value(structural_field),
                "outcome.structural_processing." + structural_field,
            )
            == expected_sha
        )

    predicate(
        "exact_radius1_sha256",
        lambda: exact_radius(
            "reactive_center_radius1_fingerprint",
            "reactive_center_radius1_sha256",
            DTT_RADIUS1_SHA256,
        ),
        True,
    )
    predicate(
        "exact_radius2_sha256",
        lambda: exact_radius(
            "reactive_center_radius2_fingerprint",
            "reactive_center_radius2_sha256",
            DTT_RADIUS2_SHA256,
        ),
        True,
    )
    predicate(
        "exact_local_topology",
        lambda: bool(
            _required_string(
                event.get("reactive_center_local_topology"), "event.local_topology"
            )
            == DTT_LOCAL_TOPOLOGY
            and _required_string(
                structural_value("reactive_center_local_topology"),
                "outcome.structural_processing.reactive_center_local_topology",
            )
            == DTT_LOCAL_TOPOLOGY
        ),
        True,
    )

    def exact_source_structure() -> bool:
        event_pdb = _required_string(event.get("pdb_id"), "event.pdb_id")
        outcome_pdb = _required_string(outcome.get("pdb_id"), "outcome.pdb_id")
        entry = _required_string(
            structural_value("mmcif_entry_id"),
            "outcome.structural_processing.mmcif_entry_id",
        )
        ligand_instance = _required_string(
            event.get("ligand_instance"), "event.ligand_instance"
        )
        if not _PDB_RE.fullmatch(event_pdb) or not _PDB_RE.fullmatch(outcome_pdb):
            raise _EvidenceError("event_outcome.pdb_id:GRAMMAR_INVALID")
        return bool(
            event_pdb == SOURCE_STRUCTURE_ID
            and outcome_pdb == SOURCE_STRUCTURE_ID
            and entry == SOURCE_STRUCTURE_ID
            and ligand_instance == "B"
        )

    predicate("exact_1fvg_source_structure_context", exact_source_structure, True)

    def leakage() -> Mapping[str, Any]:
        return _required_mapping(
            structural_value("leakage_evidence"),
            "outcome.structural_processing.leakage_evidence",
        )

    def exact_reagent_protein() -> bool:
        evidence = leakage()
        return bool(
            _required_string(evidence.get("protein_accession"), "leakage.accession")
            == SOURCE_PROTEIN_ACCESSION
            and _required_sha(
                evidence.get("protein_sequence_sha256"), "leakage.sequence_sha256"
            )
            == SOURCE_PROTEIN_SEQUENCE_SHA256
        )

    predicate("exact_1fvg_reagent_protein_context", exact_reagent_protein, True)

    def source_boundary() -> bool:
        evidence = leakage()
        return bool(
            _strict_bool(evidence.get("complete"), "leakage.complete") is True
            and _strict_bool(
                evidence.get("external_uniprot_call_performed"),
                "leakage.external_uniprot_call_performed",
            )
            is False
            and _required_string(evidence.get("source_boundary"), "leakage.source_boundary")
            == "PDB_MMCIF_CORE_PLUS_OFFICIAL_WWPDB_CCD"
        )

    predicate("structured_source_boundary", source_boundary, True)

    def annotations_well_formed() -> bool:
        annotations = _json_list(
            event.get("source_annotations_json"), "event.source_annotations_json"
        )
        if not annotations or any(not isinstance(item, Mapping) for item in annotations):
            raise _EvidenceError("event.source_annotations_json:ITEMS_INVALID")
        return True

    predicate("source_annotations_well_formed", annotations_well_formed, True)
    predicate(
        "no_source_annotation_conflict",
        lambda: len(
            _json_list(
                event.get("annotation_conflicts_json"),
                "event.annotation_conflicts_json",
            )
        ),
        0,
    )
    predicate(
        "no_existing_exact_positive_authority",
        lambda: _strict_bool(
            outcome.get("existing_exact_authority_match"),
            "outcome.existing_exact_authority_match",
        ),
        False,
    )

    def no_production_approval() -> bool:
        return bool(
            _strict_bool(
                event.get("production_approval_created"),
                "event.production_approval_created",
            )
            is False
            and _strict_bool(
                outcome.get("production_materialization_performed"),
                "outcome.production_materialization_performed",
            )
            is False
        )

    predicate("no_production_approval", no_production_approval, True)

    def no_runtime_override() -> bool:
        event_id = _required_string(
            event.get("canonical_event_id"), "event.canonical_event_id"
        )
        outcome_id = _required_string(
            outcome.get("canonical_event_id"), "outcome.canonical_event_id"
        )
        if event_id != outcome_id:
            raise _EvidenceError("event_outcome.canonical_event_id:MISMATCH")
        return event_id not in positive_ids

    predicate("no_runtime_positive_override", no_runtime_override, True)
    matched = [name for name in REQUIRED_PREDICATES if name in set(matched)]
    failed_set = sorted(set(failed))
    invalid_set = sorted(set(invalid))
    if failed_set:
        reason = "PREDICATE_MISMATCH:" + ",".join(failed_set)
        if invalid_set:
            reason += ";UNAVAILABLE_OR_MALFORMED:" + ",".join(invalid_set)
        return AutoNegativeEvaluationResult(
            rule_id=RULE_ID,
            status=NOT_MATCHED,
            reason=reason,
            matched_predicates=tuple(matched),
        )
    if invalid_set:
        return _invalid_result(matched, invalid_set)
    if tuple(matched) != REQUIRED_PREDICATES:
        return _invalid_result(matched, ("predicate_coverage:INCOMPLETE",))
    return AutoNegativeEvaluationResult(
        rule_id=RULE_ID,
        status=MATCHED_AUTO_NEGATIVE_EXACT,
        reason="ALL_EXACT_PREDICATES_MATCHED",
        matched_predicates=tuple(matched),
    )


def aggregate_review_unit_shadow_v1(
    *, review_unit_id: str, event_results: Sequence[AutoNegativeEvaluationResult]
) -> UnitShadowEvaluationResult:
    if not isinstance(review_unit_id, str) or not review_unit_id:
        raise ValueError("REVIEW_UNIT_ID_INVALID")
    if not isinstance(event_results, Sequence) or isinstance(event_results, (str, bytes)):
        raise ValueError("EVENT_RESULTS_NOT_SEQUENCE")
    results = tuple(event_results)
    if not results:
        raise ValueError("EVENT_RESULTS_EMPTY")
    if any(type(item) is not AutoNegativeEvaluationResult for item in results):
        raise ValueError("EVENT_RESULT_TYPE_INVALID")
    if any(item.rule_id != RULE_ID for item in results):
        raise ValueError("EVENT_RESULT_RULE_ID_MISMATCH")
    counts = Counter(item.status for item in results)
    if set(counts) - {MATCHED_AUTO_NEGATIVE_EXACT, NOT_MATCHED, INVALID_EVIDENCE}:
        raise ValueError("EVENT_RESULT_STATUS_INVALID")
    all_match = counts[MATCHED_AUTO_NEGATIVE_EXACT] == len(results)
    return UnitShadowEvaluationResult(
        rule_id=RULE_ID,
        review_unit_id=review_unit_id,
        status=(
            UNIT_SHADOW_AUTO_NEGATIVE_EXACT
            if all_match
            else UNIT_NOT_SHADOW_AUTO_NEGATIVE
        ),
        reason=(
            "EVERY_EVENT_IN_UNIT_MATCHED_SAME_EXACT_RULE"
            if all_match
            else (
                "UNIT_FAIL_CLOSED:matched="
                + str(counts[MATCHED_AUTO_NEGATIVE_EXACT])
                + ",not_matched="
                + str(counts[NOT_MATCHED])
                + ",invalid="
                + str(counts[INVALID_EVIDENCE])
            )
        ),
        event_count=len(results),
        matched_event_count=counts[MATCHED_AUTO_NEGATIVE_EXACT],
        invalid_event_count=counts[INVALID_EVIDENCE],
        shadow_would_auto_negative=all_match,
    )


def _human_state(unit: Mapping[str, Any]) -> str:
    workflow = str(unit.get("workflow_status") or "")
    decision = str(unit.get("training_domain_relevance_decision") or "")
    return workflow + ((":" + decision) if decision else "")


def _failed_predicates(reason: str) -> tuple[str, ...]:
    if not reason.startswith("PREDICATE_MISMATCH:"):
        return ()
    body = reason[len("PREDICATE_MISMATCH:") :].split(";", 1)[0]
    return tuple(sorted(item for item in body.split(",") if item))


def _build_manifest_base(
    *,
    context: Mapping[str, Any],
    evidence: Mapping[str, Any],
    dtu_identity: Mapping[str, Any],
) -> dict[str, Any]:
    human = evidence["calibration_human"]
    calibration = evidence["calibration_human_unit_by_id"][CALIBRATION_UNIT_ID]
    history = [
        item
        for item in human["decision_history"]
        if item.get("review_unit_id") == CALIBRATION_UNIT_ID
    ]
    thawed = _thaw(context)
    immutable_object = CALIBRATION_COMMIT + ":" + HUMAN_DECISIONS_RELATIVE.as_posix()
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "rule_id": RULE_ID,
        "rule_role": RULE_ROLE,
        "artifact_semantics": ARTIFACT_SEMANTICS,
        "human_readable_meaning": (
            "Exact DTT covalent adduct in the independently source-verified "
            "1FVG crystallization/reagent context, including the exact "
            "graph-automorphic opposite DTT thiol endpoint, outside CovaPIE "
            "medicinal small-molecule task-domain relevance."
        ),
        "not_authority_for": [
            "DTU",
            "other_pdb_dtt",
            "generic_reducing_reagent",
            "generic_thiol",
            "generic_dithiol",
            "generic_disulfide",
            "chemistry_family",
            "production",
            "training",
        ],
        "immutable_calibration_gold_git_object": immutable_object,
        "calibration_commit": CALIBRATION_COMMIT,
        "calibration_unit_id": CALIBRATION_UNIT_ID,
        "calibration_artifact_binding": {
            "git_object": immutable_object,
            "path": HUMAN_DECISIONS_RELATIVE.as_posix(),
            "byte_count": CALIBRATION_HUMAN_BYTES,
            "sha256": CALIBRATION_HUMAN_SHA256,
        },
        "calibration_human_decision": {
            "workflow_status": calibration["workflow_status"],
            "training_domain_relevance_decision": calibration[
                "training_domain_relevance_decision"
            ],
            "reactive_atom_confirmation": calibration["reactive_atom_confirmation"],
            "warhead_family_decision": calibration["warhead_family_decision"],
            "warhead_atom_ids": calibration["warhead_atom_ids"],
            "roles": calibration["roles"],
            "event_decision_count": len(calibration["events"]),
            "all_event_decisions_blank": True,
            "review_rationale": calibration["review_rationale"],
        },
        "calibration_human_history_evidence": history,
        "exact_dtt_ccd_source_binding": thawed["exact_ligand_identity"][
            "official_ccd_identity"
        ],
        "dtt_graph_sha256": DTT_GRAPH_SHA256,
        "dtt_stereochemical_identity": {
            "inchikey": DTT_INCHIKEY,
            "atom_stereo_config": {"C2": "R", "C3": "R"},
        },
        "derived_endpoint_automorphism": thawed["endpoint_automorphism"],
        "independent_1fvg_reagent_context_provenance": thawed[
            "independent_1fvg_reagent_context"
        ],
        "required_predicates": list(REQUIRED_PREDICATES),
        "forbidden_sole_predicates": list(FORBIDDEN_SOLE_PREDICATES),
        "dtu_counterexample_identity": _thaw(dtu_identity),
        "cross_CCD_DTU_generalization_authorized": False,
        "runtime_positive_override_policy": RUNTIME_POSITIVE_OVERRIDE_POLICY,
        "shadow_label_leakage_prohibited": True,
        "rule_context_independent_of_shadow_population": True,
        "scientific_rule_context": thawed,
        "input_artifact_sha256": evidence["input_hashes"],
        "runtime_state_embedded_in_deterministic_artifacts": False,
        "current_human_overlay_embedded_in_deterministic_artifacts": False,
        "current_production_registry_embedded_in_deterministic_artifacts": False,
        "runtime_positive_override_evaluated_separately": True,
        "descendant_repository_compatible": True,
    }


def build_artifacts_v1(
    *, repo_root: Path, cache_root: Path | None = None
) -> dict[str, bytes]:
    """Build the three immutable-calibration shadow artifacts in memory."""

    repo_root = repo_root.resolve()
    resolved_cache = (
        cache_root.resolve()
        if cache_root is not None
        else repo_root.parent / CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    verify_repository_binding_v1(repo_root)
    input_hashes_before = verify_bound_inputs_v1(repo_root)
    context = _build_static_rule_context_v1(
        repo_root=repo_root, cache_root=resolved_cache
    )
    evidence = _load_calibration_snapshot_evidence_v1(repo_root)
    override = build_calibration_snapshot_positive_override_context_v1(
        immutable_calibration_human=evidence["calibration_human"],
        frozen_outcome_by_id=evidence["outcome_by_id"],
    )
    dtu_identity = _parse_official_ccd(
        repo_root=repo_root, cache_root=resolved_cache, component_id="DTU"
    )
    if (
        dtu_identity["source_binding"]["sha256"] != DTU_CCD_SOURCE_SHA256
        or dtu_identity["inchikey"] != DTU_INCHIKEY
        or dtu_identity["atom_stereo_config"] != {"C2": "S", "C3": "R"}
    ):
        raise ValueError("OFFICIAL_DTU_CCD_IDENTITY_MISMATCH")
    manifest = _build_manifest_base(
        context=context, evidence=evidence, dtu_identity=dtu_identity
    )

    event_results: dict[str, AutoNegativeEvaluationResult] = {}
    by_unit: dict[str, list[AutoNegativeEvaluationResult]] = defaultdict(list)
    for event_id in sorted(evidence["event_by_id"]):
        result = evaluate_neg_v2_dtt_crystallization_reducing_adduct_exact(
            event=evidence["event_by_id"][event_id],
            outcome=evidence["outcome_by_id"][event_id],
            rule_context=context,
            override_context=override,
        )
        event_results[event_id] = result
        by_unit[evidence["unit_by_event"][event_id]].append(result)
    unit_results = {
        unit_id: aggregate_review_unit_shadow_v1(
            review_unit_id=unit_id, event_results=results
        )
        for unit_id, results in sorted(by_unit.items())
    }
    counts = Counter(item.status for item in event_results.values())
    matched_units = sorted(
        unit_id
        for unit_id, result in unit_results.items()
        if result.shadow_would_auto_negative
    )
    calibration_event_ids = tuple(
        item["canonical_event_id"]
        for item in evidence["calibration_human_unit_by_id"][CALIBRATION_UNIT_ID][
            "events"
        ]
    )
    calibration_matched_events = sum(
        event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in calibration_event_ids
    )
    unreviewed_matched_units = [
        unit_id
        for unit_id in matched_units
        if evidence["calibration_human_unit_by_id"][unit_id].get("workflow_status")
        == "UNREVIEWED"
    ]
    unreviewed_matched_event_ids = sorted(
        event_id
        for unit_id in unreviewed_matched_units
        for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]
        if event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
    )
    builder_source = inspect.getsource(_build_static_rule_context_v1)
    rule_source_has_shadow_label = any(
        unit_id in builder_source or event_id in builder_source
        for unit_id in unreviewed_matched_units
        for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]
    )
    automorphism_proven = bool(
        context["endpoint_automorphism"]["DTT_ENDPOINT_AUTOMORPHISM_PROVEN"]
    )
    generalization_without_label_leakage = bool(
        automorphism_proven
        and not rule_source_has_shadow_label
        and context[
            "rule_context_is_independent_of_shadow_evaluation_population"
        ]
        is True
        and calibration_matched_events == 1
        and len(unreviewed_matched_event_ids) == 1
        and counts[MATCHED_AUTO_NEGATIVE_EXACT] == 2
    )

    dtu_event_ids = sorted(
        event_id
        for event_id, event in evidence["event_by_id"].items()
        if event.get("ligand_component_id") == "DTU"
    )
    if (
        not dtu_event_ids
        or evidence["unit_by_id"].get(DTU_COUNTEREXAMPLE_UNIT_ID, {}).get(
            "canonical_event_ids"
        )
        != dtu_event_ids
    ):
        raise ValueError("DTU_COUNTEREXAMPLE_POPULATION_BINDING_MISMATCH")
    dtu_matches = sum(
        event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in dtu_event_ids
    )
    dtu_failures = {
        event_id: list(_failed_predicates(event_results[event_id].reason))
        for event_id in dtu_event_ids
    }
    human_relevant_event_ids = {
        event["canonical_event_id"]
        for unit in evidence["calibration_human_unit_by_id"].values()
        if unit.get("training_domain_relevance_decision")
        == "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
        for event in unit["events"]
    }
    human_relevant_matches = sum(
        event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in human_relevant_event_ids
    )
    component_counterexamples: dict[str, dict[str, int]] = {}
    for component in MANDATORY_COMPONENT_COUNTEREXAMPLES:
        event_ids = [
            event_id
            for event_id, event in evidence["event_by_id"].items()
            if event.get("ligand_component_id") == component
        ]
        component_counterexamples[component] = {
            "present_event_count": len(event_ids),
            "match_count": sum(
                event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
                for event_id in event_ids
            ),
        }
    orbit = frozenset(context["endpoint_automorphism"]["reactive_sulfur_orbit"])
    lookalike_event_ids = {
        event_id
        for event_id, event in evidence["event_by_id"].items()
        if (
            event.get("reactive_center_radius1_fingerprint") == DTT_RADIUS1_SHA256
            or event.get("reactive_center_radius2_fingerprint") == DTT_RADIUS2_SHA256
            or event.get("reactive_center_local_topology") == DTT_LOCAL_TOPOLOGY
        )
    }
    authorized_shape_ids = {
        event_id
        for event_id in lookalike_event_ids
        if evidence["event_by_id"][event_id].get("ligand_component_id") == "DTT"
        and evidence["event_by_id"][event_id].get("ccd_component_graph_sha256")
        == DTT_GRAPH_SHA256
        and evidence["event_by_id"][event_id].get("pdb_id") == SOURCE_STRUCTURE_ID
        and evidence["event_by_id"][event_id].get("ligand_reactive_atom") in orbit
        and evidence["event_by_id"][event_id].get(
            "reactive_center_radius1_fingerprint"
        )
        == DTT_RADIUS1_SHA256
        and evidence["event_by_id"][event_id].get(
            "reactive_center_radius2_fingerprint"
        )
        == DTT_RADIUS2_SHA256
        and evidence["event_by_id"][event_id].get("reactive_center_local_topology")
        == DTT_LOCAL_TOPOLOGY
    }
    broader_lookalike_ids = lookalike_event_ids - authorized_shape_ids
    broader_lookalike_matches = sum(
        event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in broader_lookalike_ids
    )
    component_false_positive_count = sum(
        record["match_count"] for record in component_counterexamples.values()
    )
    live_integration_ready = bool(
        generalization_without_label_leakage
        and len(matched_units) == 2
        and calibration_matched_events == 1
        and CALIBRATION_UNIT_ID in matched_units
        and len(unreviewed_matched_units) == 1
        and dtu_matches == 0
        and human_relevant_matches == 0
        and component_false_positive_count == 0
        and broader_lookalike_matches == 0
        and counts[INVALID_EVIDENCE] == 0
    )
    readiness_mode = READINESS_MODE if live_integration_ready else NOT_READY_MODE
    manifest.update(
        {
            "readiness_mode": readiness_mode,
            "DTT_ENDPOINT_AUTOMORPHISM_PROVEN": automorphism_proven,
            "generalization_without_sibling_label_leakage": (
                generalization_without_label_leakage
            ),
            "rule_context_source_contains_shadow_unit_or_event_id": (
                rule_source_has_shadow_label
            ),
            "rule_context_independent_of_shadow_population": True,
            "observed_shadow_counts": {
                "candidate_event_count": len(event_results),
                "not_matched_event_count": counts[NOT_MATCHED],
                "matched_event_count": counts[MATCHED_AUTO_NEGATIVE_EXACT],
                "invalid_evidence_count": counts[INVALID_EVIDENCE],
                "matched_unit_count": len(matched_units),
                "human_calibration_matched_event_count": calibration_matched_events,
                "calibration_snapshot_unreviewed_matched_event_count": len(
                    unreviewed_matched_event_ids
                ),
            },
            "dtu_counterexample_observation": {
                "candidate_event_count": len(dtu_event_ids),
                "match_count": dtu_matches,
                "failed_predicates_by_event": dtu_failures,
                "classified_as_negative": False,
                "human_state_mutated": False,
            },
            "broader_sulfur_counterexample_observations": component_counterexamples,
            "same_local_environment_lookalike_observation": {
                "lookalike_event_count": len(lookalike_event_ids),
                "unauthorized_shape_event_count": len(broader_lookalike_ids),
                "unauthorized_shape_match_count": broader_lookalike_matches,
            },
            "human_relevant_counterexample_match_count": human_relevant_matches,
            "live_integration_ready": live_integration_ready,
            "integration_into_live_successor_routing_performed": False,
        }
    )

    rows: list[dict[str, object]] = []
    for event_id in sorted(evidence["event_by_id"]):
        event = evidence["event_by_id"][event_id]
        unit_id = evidence["unit_by_event"][event_id]
        result = event_results[event_id]
        unit_result = unit_results[unit_id]
        raw = {
            "canonical_event_id": event_id,
            "review_unit_id": unit_id,
            "pdb_id": event["pdb_id"],
            "ligand_component_id": event["ligand_component_id"],
            "ccd_component_graph_sha256": event["ccd_component_graph_sha256"],
            "ligand_reactive_atom": event["ligand_reactive_atom"],
            "ligand_reactive_element": event["ligand_reactive_element"],
            "radius1_sha256": event["reactive_center_radius1_fingerprint"],
            "radius2_sha256": event["reactive_center_radius2_fingerprint"],
            "rule_id": result.rule_id,
            "evaluation_status": result.status,
            "evaluation_reason": result.reason,
            "matched_predicates_json": _json_cell(list(result.matched_predicates)),
            "failed_predicates_json": _json_cell(
                list(_failed_predicates(result.reason))
            ),
            "calibration_snapshot_human_review_state": _human_state(
                evidence["calibration_human_unit_by_id"][unit_id]
            ),
            "review_unit_shadow_status": unit_result.status,
            "shadow_would_auto_negative": (
                "true" if unit_result.shadow_would_auto_negative else "false"
            ),
        }
        rows.append({field: raw[field] for field in SHADOW_HEADER})
    manifest_bytes = _json_bytes(manifest)
    inventory_bytes = _csv_bytes(SHADOW_HEADER, rows)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "rule_id": RULE_ID,
        "implementation_mode": (
            "SHADOW_EXACT_GATE_NOT_YET_LIVE_SUCCESSOR_ROUTING"
        ),
        "artifact_semantics": ARTIFACT_SEMANTICS,
        "readiness_mode": readiness_mode,
        "candidate_event_count": len(event_results),
        "historical_review_unit_count": len(unit_results),
        "observed_shadow_matched_event_count": counts[
            MATCHED_AUTO_NEGATIVE_EXACT
        ],
        "observed_shadow_matched_unit_count": len(matched_units),
        "human_calibration_matched_event_count": calibration_matched_events,
        "human_calibration_matched_unit_count": int(
            CALIBRATION_UNIT_ID in matched_units
        ),
        "calibration_snapshot_unreviewed_shadow_auto_negative_event_count": len(
            unreviewed_matched_event_ids
        ),
        "calibration_snapshot_unreviewed_shadow_auto_negative_unit_count": len(
            unreviewed_matched_units
        ),
        "DTU_counterexample_match_count": dtu_matches,
        "human_relevant_counterexample_match_count": human_relevant_matches,
        "invalid_evidence_count": counts[INVALID_EVIDENCE],
        "generalization_without_sibling_label_leakage": (
            generalization_without_label_leakage
        ),
        "DTT_endpoint_automorphism_proven": automorphism_proven,
        "cross_CCD_DTU_generalization_authorized": False,
        "cross_pdb_DTT_generalization_authorized": False,
        "live_integration_ready": live_integration_ready,
        "integration_into_live_successor_routing_performed": False,
        "runtime_positive_override_evaluated_separately": True,
        "runtime_state_embedded_in_deterministic_artifacts": False,
        "rule_context_independent_of_shadow_population": True,
        "rule_context_source_contains_shadow_unit_or_event_id": (
            rule_source_has_shadow_label
        ),
        "broader_sulfur_counterexample_match_count": component_false_positive_count,
        "same_local_environment_unauthorized_match_count": (
            broader_lookalike_matches
        ),
        "matched_review_units": [
            {
                "review_unit_id": unit_id,
                "event_count": unit_results[unit_id].event_count,
                "calibration_snapshot_human_review_state": _human_state(
                    evidence["calibration_human_unit_by_id"][unit_id]
                ),
                "shadow_only": True,
            }
            for unit_id in matched_units
        ],
        "unit_aggregation_policy": (
            "EVERY_EVENT_MUST_INDEPENDENTLY_MATCH_SAME_EXACT_RULE; "
            "PARTIAL_OR_INVALID_UNIT_FAILS_CLOSED"
        ),
        "legacy_triage_artifacts_modified": False,
        "human_review_overlay_modified": False,
        "successor_routing_modified": False,
        "production_chemistry_authority_created": False,
        "training_materialization_performed": False,
        "output_sha256_excluding_summary": {
            RULE_MANIFEST: _sha(manifest_bytes),
            SHADOW_INVENTORY: _sha(inventory_bytes),
        },
        "ready_for_gpt_review": live_integration_ready,
        "recommended_next_step_exactly": (
            "gpt_audit_DTT_exact_shadow_gate_then_commit_push_DTT_gate"
            if live_integration_ready
            else "resolve_DTT_exact_shadow_gate_evidence_blocker"
        ),
    }
    artifacts = {
        RULE_MANIFEST: manifest_bytes,
        SHADOW_INVENTORY: inventory_bytes,
        SUMMARY: _json_bytes(summary),
    }
    if verify_bound_inputs_v1(repo_root) != input_hashes_before:
        raise ValueError("SOURCE_INPUTS_MODIFIED_DURING_BUILD")
    return {name: artifacts[name] for name in OUTPUT_FILENAMES}


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
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_v1(
    *,
    repo_root: Path,
    cache_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = (
        output_root.resolve()
        if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    authorized = repo_root / OUTPUT_ROOT_RELATIVE
    if target != authorized:
        try:
            target.relative_to(Path(tempfile.gettempdir()).resolve())
        except ValueError as error:
            raise ValueError("OUTPUT_ROOT_OUTSIDE_AUTHORIZED_PATH") from error
    artifacts = build_artifacts_v1(repo_root=repo_root, cache_root=cache_root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(target / name, artifacts[name])
    return json.loads(artifacts[SUMMARY])


def verify_deterministic_replay_v1(
    repo_root: Path, cache_root: Path | None = None
) -> dict[str, str]:
    target = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    observed = {name: (target / name).read_bytes() for name in OUTPUT_FILENAMES}
    replay = build_artifacts_v1(repo_root=repo_root, cache_root=cache_root)
    result: dict[str, str] = {}
    for name in OUTPUT_FILENAMES:
        if observed[name] != replay[name]:
            raise ValueError("OUTPUT_NOT_BYTE_IDENTICAL_ON_REPLAY:" + name)
        result[name] = _sha(observed[name])
    return result
