"""Exact shadow-only task-domain negative gate for catalytic TS/dUMP adducts.

The gate is additive.  It consumes SHA-bound published evidence and an
immutable human decision from a specific Git object.  It neither changes the
legacy triage lane nor creates chemistry, reaction-family, or training
authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
from typing import Any


SCHEMA_VERSION = "covapie_post_only_auto_negative_ts_dump_exact_v1"
STAGE = SCHEMA_VERSION
RULE_ID = "NEG_V1_TS_DUMP_CATALYTIC_ADDUCT_EXACT"

MATCHED_AUTO_NEGATIVE_EXACT = "MATCHED_AUTO_NEGATIVE_EXACT"
NOT_MATCHED = "NOT_MATCHED"
INVALID_EVIDENCE = "INVALID_EVIDENCE"

UNIT_SHADOW_AUTO_NEGATIVE_EXACT = "SHADOW_AUTO_NEGATIVE_EXACT"
UNIT_NOT_SHADOW_AUTO_NEGATIVE = "NOT_SHADOW_AUTO_NEGATIVE"

CALIBRATION_COMMIT = "106e4182b09a0861294495d1385d678d08868fae"
CALIBRATION_SUBJECT = "record CovaPIE negative calibration human gold checkpoint v1"
CALIBRATION_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_5184266C4D495D18"
SIBLING_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_EB1C0FF8712C32A9"
CALIBRATION_EVENT_COUNT = 16

UFP_COUNTEREXAMPLE_UNITS = (
    "COVAPIE_BULK_REVIEW_UNIT_1E58101A3E611294",
    "COVAPIE_BULK_REVIEW_UNIT_CF6D3ADC970757BA",
)
HUMAN_RELEVANT_COUNTEREXAMPLE_UNITS = (
    "COVAPIE_BULK_REVIEW_UNIT_07BD3B72031BD7CC",
    "COVAPIE_BULK_REVIEW_UNIT_5662273FCD38234C",
    "COVAPIE_BULK_REVIEW_UNIT_59100AAB78E957D9",
)
PYR_COUNTEREXAMPLE_UNIT = "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4"

HUMAN_DECISIONS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_post_only_cys_sg_human_review_v1/"
    "covapie_post_only_human_review_decisions_v1.json"
)
CALIBRATION_HUMAN_BYTES = 91133
CALIBRATION_HUMAN_SHA256 = (
    "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441"
)
CALIBRATION_RATIONALE = (
    "Human negative calibration for 2AAZ/UMP: the deposited component is "
    "natural dUMP in the normal thymidylate-synthase catalytic "
    "substrate/intermediate state. This is a genuine and structurally useful "
    "biochemical covalent state, but dUMP is not a designed medicinal "
    "pocket-recognition covalent ligand for CovaPIE post-only V1. This "
    "decision is exact to this unit and does not cover UFP/FdUMP, other "
    "nucleotides, or other thymidylate-synthase ligands."
)

TRIAGE_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_post_only_cys_sg_training_candidate_triage_v1"
)
UPSTREAM_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_dataset_expansion_v1/bulk_pilot_v1"
)
EVENT_INVENTORY_RELATIVE = TRIAGE_ROOT_RELATIVE / (
    "covapie_bulk_post_only_training_candidate_event_inventory_v1.csv"
)
REVIEW_PACKET_RELATIVE = TRIAGE_ROOT_RELATIVE / (
    "covapie_bulk_post_only_training_human_review_packet_v1.json"
)
LEGACY_SUMMARY_RELATIVE = TRIAGE_ROOT_RELATIVE / (
    "covapie_bulk_post_only_training_candidate_summary_v1.json"
)
UPSTREAM_OUTCOMES_RELATIVE = UPSTREAM_ROOT_RELATIVE / (
    "bulk_processing_outcomes_v1.json"
)
UPSTREAM_ACQUISITION_RELATIVE = UPSTREAM_ROOT_RELATIVE / (
    "bulk_acquisition_manifest_v1.json"
)
CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/bulk-multisource-cys-sg-v1"
)
TARGET_FAMILY_EC = "2.1.1.45"
TARGET_FAMILY_CONTEXT_PROVENANCE = (
    "SHA_BOUND_WWPDB_MMCIF_ENTITY_PDBX_EC_EXACT_2.1.1.45_"
    "PLUS_UNP_ACCESSION_AND_ENTITY_POLY_SEQ_SHA256_V1"
)
RUNTIME_OVERRIDE_SCHEMA_VERSION = (
    "covapie_auto_negative_runtime_positive_override_context_v1"
)
GENERALIZATION_MODE = "GENERALIZATION_PROVEN_WITHOUT_SHADOW_LABEL_LEAKAGE"
CALIBRATION_ONLY_MODE = (
    "CALIBRATION_ONLY_TARGET_FAMILY_GENERALIZATION_NOT_YET_AUTHORIZED"
)
ARTIFACT_SEMANTICS = "IMMUTABLE_CALIBRATION_SNAPSHOT_SHADOW_EVALUATION"
RUNTIME_POSITIVE_OVERRIDE_POLICY = (
    "CURRENT_HUMAN_RELEVANT_OR_CURRENT_PRODUCTION_EXACT_POSITIVE_OR_"
    "EXPLICIT_RUNTIME_POSITIVE_OVERRIDES_AUTO_NEGATIVE; MALFORMED_"
    "OVERRIDE_CONTEXT_INVALIDATES_MATCH"
)

INPUT_SHA256 = {
    EVENT_INVENTORY_RELATIVE: (
        "a1e48d9efaa9b0f5f1b1d7d5988d9f54c07c22d7249b5a7b43dee31fd6efaa75"
    ),
    REVIEW_PACKET_RELATIVE: (
        "39f8afd7b8f62531f9f8704163cc7a444c3b008ff8d4610744d90b4918053194"
    ),
    LEGACY_SUMMARY_RELATIVE: (
        "1f8deb600137598786b3566c6fd35f0e044e150a306fe75da98f61c59dda07ac"
    ),
    UPSTREAM_OUTCOMES_RELATIVE: (
        "0270dd93a31427042d02f7751ab7b46679308c7f1ee5207a5560b199a6a94d57"
    ),
    UPSTREAM_ACQUISITION_RELATIVE: (
        "b12b0e29d223d7469c81e6cbfe0d8eaf7aa4f8a18368b65843df8e63c75afe46"
    ),
}

DUMP_GRAPH_SHA256 = (
    "94a0c576d62f9955d6574009b4a79479396f2ebaa977c7340bc9b0ab4203d8f9"
)
DUMP_REACTIVE_ATOM = "C6"
DUMP_REACTIVE_ELEMENT = "C"
DUMP_RADIUS1_SHA256 = (
    "9d8060b2268ba49a158fddd66dd1ec165d7ec06ed6a41a9ab4cce7ae93031ef9"
)
DUMP_RADIUS2_SHA256 = (
    "cc17eb042e28bb3d8672f4c98c90659357dd42a1e2f3a33f5beeee7d73847b1e"
)

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_post_only_auto_negative_ts_dump_exact_v1"
)
RULE_MANIFEST = "covapie_ts_dump_auto_negative_rule_manifest_v1.json"
SHADOW_INVENTORY = "covapie_ts_dump_shadow_match_inventory_v1.csv"
SUMMARY = "covapie_ts_dump_auto_negative_summary_v1.json"
OUTPUT_FILENAMES = (RULE_MANIFEST, SHADOW_INVENTORY, SUMMARY)

CODE_RELATIVE_PATHS = (
    Path("src/covalent_ext/covapie_post_only_auto_negative_ts_dump_exact_v1.py"),
    Path("scripts/build_covapie_post_only_auto_negative_ts_dump_exact_v1.py"),
    Path("scripts/check_covapie_post_only_auto_negative_ts_dump_exact_v1.py"),
    Path("tests/test_covapie_post_only_auto_negative_ts_dump_exact_v1.py"),
)
AUTHORIZED_NEW_PATHS = tuple(CODE_RELATIVE_PATHS) + tuple(
    OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES
)

SHADOW_HEADER = (
    "canonical_event_id",
    "review_unit_id",
    "pdb_id",
    "ligand_component_id",
    "target_cys_identity",
    "protein_accession",
    "protein_sequence_sha256",
    "ccd_component_graph_sha256",
    "ligand_reactive_atom",
    "ligand_reactive_element",
    "radius1_sha256",
    "radius2_sha256",
    "rule_id",
    "evaluation_status",
    "evaluation_reason",
    "matched_predicates_json",
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
    "exact_ccd_component_graph_sha256",
    "exact_ligand_reactive_atom",
    "exact_ligand_reactive_element",
    "exact_radius1_sha256",
    "exact_radius2_sha256",
    "exact_ts_family_accession_sequence_key",
    "structured_protein_identity_source_boundary",
    "source_annotations_well_formed",
    "no_source_annotation_conflict",
    "no_existing_exact_positive_authority",
    "no_production_approval",
    "no_runtime_positive_override",
)

FORBIDDEN_SOLE_PREDICATES = (
    "molecule_name_or_substring",
    "source_reaction_equals_substrate",
    "protein_name_or_thymidylate_synthase_substring",
    "nucleotide_status",
    "warhead_label",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PDB_RE = re.compile(r"^[0-9A-Z]{4}$")
_TARGET_RE = re.compile(r"^[^:]+:CYS:[^:]+$")
_ENTRY_ID_RE = re.compile(r"(?m)^_entry\.id\s+([A-Za-z0-9]+)")


@dataclass(frozen=True)
class AutoNegativeEvaluationResult:
    """Immutable event-level gate result."""

    rule_id: str
    status: str
    reason: str
    matched_predicates: tuple[str, ...]


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


@dataclass(frozen=True)
class RuntimePositiveOverrideContext:
    """Explicit dynamic precedence inputs supplied by the current runtime."""

    schema_version: str
    current_human_relevant_event_ids: frozenset[str]
    current_production_exact_positive_event_ids: frozenset[str]
    explicit_positive_override_event_ids: frozenset[str]
    current_human_overlay_sha256: str


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
        output, fieldnames=list(header), lineterminator="\n", extrasaction="raise"
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


def _git(repo_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


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
    """Accept a synchronized main descendant containing immutable calibration."""

    repo_root = repo_root.resolve()
    branch = _git(repo_root, "branch", "--show-current")
    head = _git(repo_root, "rev-parse", "HEAD")
    origin = _git(repo_root, "rev-parse", "refs/remotes/origin/main")
    calibration_subject = _git(
        repo_root, "show", "-s", "--format=%s", CALIBRATION_COMMIT
    )
    divergence = _git(
        repo_root,
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...refs/remotes/origin/main",
    )
    try:
        ahead_text, behind_text = divergence.split()
        ahead, behind = int(ahead_text), int(behind_text)
    except (TypeError, ValueError) as error:
        raise ValueError("GIT_DIVERGENCE_OUTPUT_INVALID") from error
    if branch != "main":
        raise ValueError("BASE_BRANCH_MISMATCH")
    if head != origin:
        raise ValueError("HEAD_ORIGIN_MAIN_MISMATCH")
    if (ahead, behind) != (0, 0):
        raise ValueError("BASE_AHEAD_BEHIND_MISMATCH")
    calibration_is_ancestor_of_head = _git_is_ancestor(
        repo_root, CALIBRATION_COMMIT, "HEAD"
    )
    calibration_is_ancestor_of_origin = _git_is_ancestor(
        repo_root, CALIBRATION_COMMIT, "refs/remotes/origin/main"
    )
    if not calibration_is_ancestor_of_head:
        raise ValueError("CALIBRATION_COMMIT_NOT_ANCESTOR_OF_HEAD")
    if not calibration_is_ancestor_of_origin:
        raise ValueError("CALIBRATION_COMMIT_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if calibration_subject != CALIBRATION_SUBJECT:
        raise ValueError("CALIBRATION_SUBJECT_BINDING_MISMATCH")
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "calibration_commit": CALIBRATION_COMMIT,
        "calibration_subject": calibration_subject,
        "calibration_is_ancestor_of_head": calibration_is_ancestor_of_head,
        "calibration_is_ancestor_of_origin_main": (
            calibration_is_ancestor_of_origin
        ),
        "descendant_repository_compatible": True,
    }


def verify_bound_inputs_v1(repo_root: Path) -> dict[str, str]:
    repo_root = repo_root.resolve()
    observed: dict[str, str] = {}
    for relative, expected in INPUT_SHA256.items():
        path = repo_root / relative
        if not path.is_file():
            raise ValueError("BOUND_INPUT_MISSING:" + relative.as_posix())
        digest = _sha(path.read_bytes())
        if digest != expected:
            raise ValueError("BOUND_INPUT_SHA256_MISMATCH:" + relative.as_posix())
        observed[relative.as_posix()] = digest
    return dict(sorted(observed.items()))


def _without_atom_site_loop(mmcif_text: str) -> str:
    """Remove only the large atom-site loop while retaining all metadata."""

    lines = mmcif_text.splitlines()
    retained: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].strip() != "loop_":
            retained.append(lines[index])
            index += 1
            continue
        tag_index = index + 1
        tags: list[str] = []
        while tag_index < len(lines):
            stripped = lines[tag_index].strip()
            if not stripped:
                tag_index += 1
                continue
            if not stripped.startswith("_"):
                break
            tags.append(stripped.split(None, 1)[0])
            tag_index += 1
        if tags and all(tag.startswith("_atom_site.") for tag in tags):
            index = tag_index
            while index < len(lines) and lines[index].strip() != "#":
                index += 1
            if index < len(lines):
                retained.append("#")
                index += 1
            continue
        retained.append(lines[index])
        index += 1
    return "\n".join(retained) + "\n"


def _tokenize_mmcif_metadata(text: str) -> list[str]:
    tokens: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped == "#":
            index += 1
            continue
        if line.startswith(";"):
            block: list[str] = []
            if line[1:]:
                block.append(line[1:])
            index += 1
            while index < len(lines) and not lines[index].startswith(";"):
                block.append(lines[index])
                index += 1
            if index >= len(lines):
                raise ValueError("MMCIF_MULTILINE_VALUE_UNTERMINATED")
            tokens.append("\n".join(block).strip())
            index += 1
            continue
        lexer = shlex.shlex(line, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens.extend(
            "" if token in {"?", "."} else token for token in lexer
        )
        index += 1
    return tokens


def _loop_rows_from_tokens(
    tokens: Sequence[str], prefix: str
) -> list[dict[str, str]]:
    index = 0
    result: list[dict[str, str]] = []
    while index < len(tokens):
        if tokens[index] != "loop_":
            index += 1
            continue
        index += 1
        tags: list[str] = []
        while index < len(tokens) and tokens[index].startswith("_"):
            tags.append(tokens[index])
            index += 1
        values: list[str] = []
        while (
            index < len(tokens)
            and tokens[index] != "loop_"
            and not tokens[index].startswith("_")
        ):
            values.append(tokens[index])
            index += 1
        if not tags or not all(tag.startswith(prefix) for tag in tags):
            continue
        if not values or len(values) % len(tags) != 0:
            raise ValueError("MMCIF_LOOP_SCHEMA_INVALID:" + prefix)
        for start in range(0, len(values), len(tags)):
            result.append(
                {
                    tag: values[start + offset]
                    for offset, tag in enumerate(tags)
                }
            )
    return result


def _scalar_category(
    text: str, prefix: str, *, wanted_fields: frozenset[str]
) -> dict[str, str]:
    result: dict[str, str] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped.startswith(prefix):
            index += 1
            continue
        lexer = shlex.shlex(stripped, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        parts = list(lexer)
        tag = parts[0]
        if tag not in wanted_fields:
            index += 1
            continue
        if len(parts) >= 2:
            value = parts[1]
        else:
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
            if index >= len(lines) or lines[index].startswith(";"):
                raise ValueError("MMCIF_SCALAR_VALUE_INVALID:" + tag)
            value = lines[index].strip().strip("'\"")
        result[tag] = "" if value in {"?", "."} else value
        index += 1
    return result


def _exact_entity_sequence_sha256(
    sequence_rows: Sequence[Mapping[str, str]], entity_id: str
) -> str:
    selected: list[tuple[int, str]] = []
    for row in sequence_rows:
        if str(row.get("_entity_poly_seq.entity_id", "")) != entity_id:
            continue
        try:
            number = int(str(row.get("_entity_poly_seq.num", "")))
        except ValueError as error:
            raise ValueError("TARGET_FAMILY_SEQUENCE_NUMBER_INVALID") from error
        monomer = str(row.get("_entity_poly_seq.mon_id", ""))
        if not monomer:
            raise ValueError("TARGET_FAMILY_SEQUENCE_MONOMER_MISSING")
        selected.append((number, monomer))
    selected.sort()
    if not selected or [number for number, _ in selected] != list(
        range(1, len(selected) + 1)
    ):
        raise ValueError("TARGET_FAMILY_SEQUENCE_NOT_EXACT_CONTIGUOUS_ENTITY")
    return _sha(";".join(monomer for _, monomer in selected).encode("utf-8"))


def build_independent_target_family_context_v1(
    *, repo_root: Path, cache_root: Path
) -> dict[str, Any]:
    """Build an EC-selected TS registry without reading shadow event labels."""

    repo_root = repo_root.resolve()
    cache_root = cache_root.resolve()
    acquisition = _read_json_object(repo_root / UPSTREAM_ACQUISITION_RELATIVE)
    structures = acquisition.get("structures")
    if not isinstance(structures, list) or not structures:
        raise ValueError("TARGET_FAMILY_ACQUISITION_STRUCTURE_LIST_INVALID")
    source_inventory: list[dict[str, object]] = []
    provenance_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    exact_keys: dict[str, dict[str, str]] = {}
    matched_structure_ids: set[str] = set()
    excluded_ec_entity_count = 0
    verified_count = 0
    for structure in sorted(structures, key=lambda item: str(item.get("pdb_id"))):
        if not isinstance(structure, Mapping):
            raise ValueError("TARGET_FAMILY_ACQUISITION_ROW_INVALID")
        if structure.get("acquisition_status") != "SOURCE_VERIFIED":
            continue
        pdb_id = str(structure.get("pdb_id") or "")
        expected_sha = str(structure.get("compressed_sha256") or "")
        if not _PDB_RE.fullmatch(pdb_id) or not _SHA256_RE.fullmatch(expected_sha):
            raise ValueError("TARGET_FAMILY_ACQUISITION_IDENTITY_INVALID")
        path = cache_root / "rcsb" / "structures" / f"{pdb_id}.cif.gz"
        if path.is_symlink() or not path.is_file():
            raise ValueError("TARGET_FAMILY_MMCIF_SOURCE_INVALID:" + pdb_id)
        before = path.stat()
        payload = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError("TARGET_FAMILY_MMCIF_CHANGED_DURING_READ:" + pdb_id)
        if len(payload) != int(structure.get("compressed_byte_count", -1)):
            raise ValueError("TARGET_FAMILY_MMCIF_SIZE_MISMATCH:" + pdb_id)
        if _sha(payload) != expected_sha:
            raise ValueError("TARGET_FAMILY_MMCIF_SHA256_MISMATCH:" + pdb_id)
        try:
            text = gzip.decompress(payload).decode("utf-8", "replace")
        except (OSError, EOFError) as error:
            raise ValueError("TARGET_FAMILY_MMCIF_GZIP_INVALID:" + pdb_id) from error
        entry_match = _ENTRY_ID_RE.search(text)
        if entry_match is None or entry_match.group(1).upper() != pdb_id:
            raise ValueError("TARGET_FAMILY_MMCIF_ENTRY_ID_MISMATCH:" + pdb_id)
        metadata = _without_atom_site_loop(text)
        tokens = _tokenize_mmcif_metadata(metadata)
        entities = _loop_rows_from_tokens(tokens, "_entity.")
        sequence_rows = _loop_rows_from_tokens(tokens, "_entity_poly_seq.")
        reference_rows = _loop_rows_from_tokens(tokens, "_struct_ref.")
        scalar_reference = _scalar_category(
            metadata,
            "_struct_ref.",
            wanted_fields=frozenset(
                {
                    "_struct_ref.id",
                    "_struct_ref.db_name",
                    "_struct_ref.entity_id",
                    "_struct_ref.pdbx_db_accession",
                }
            ),
        )
        if scalar_reference:
            reference_rows.append(scalar_reference)
        source_inventory.append(
            {
                "pdb_id": pdb_id,
                "compressed_byte_count": len(payload),
                "compressed_sha256": expected_sha,
            }
        )
        verified_count += 1
        for entity in entities:
            if str(entity.get("_entity.pdbx_ec", "")) != TARGET_FAMILY_EC:
                continue
            entity_id = str(entity.get("_entity.id", ""))
            accessions = {
                str(reference.get("_struct_ref.pdbx_db_accession", ""))
                for reference in reference_rows
                if str(reference.get("_struct_ref.entity_id", "")) == entity_id
                and str(reference.get("_struct_ref.db_name", "")) == "UNP"
                and str(reference.get("_struct_ref.pdbx_db_accession", ""))
            }
            if len(accessions) != 1:
                excluded_ec_entity_count += 1
                continue
            try:
                sequence_sha = _exact_entity_sequence_sha256(
                    sequence_rows, entity_id
                )
            except ValueError:
                excluded_ec_entity_count += 1
                continue
            accession = next(iter(accessions))
            key = {
                "protein_accession": accession,
                "protein_sequence_sha256": sequence_sha,
                "protein_reactive_atom": "SG",
                "structured_target_family_id": "EC:" + TARGET_FAMILY_EC,
            }
            key_json = _json_cell(key)
            exact_keys[key_json] = key
            provenance_by_key[key_json].append(
                {
                    "source_pdb_id": pdb_id,
                    "source_entity_id": entity_id,
                    "source_mmcif_compressed_sha256": expected_sha,
                    "structured_family_field": "_entity.pdbx_ec",
                    "structured_family_value": TARGET_FAMILY_EC,
                    "accession_field": "_struct_ref.pdbx_db_accession",
                    "sequence_field": "_entity_poly_seq.mon_id",
                }
            )
            matched_structure_ids.add(pdb_id)
    if verified_count != len(structures):
        raise ValueError("TARGET_FAMILY_NOT_ALL_ACQUISITION_STRUCTURES_VERIFIED")
    if not exact_keys:
        raise ValueError("TARGET_FAMILY_GENERALIZATION_EVIDENCE_INSUFFICIENT")
    registry = []
    for key_json in sorted(exact_keys):
        registry.append(
            {
                **exact_keys[key_json],
                "provenance_records": sorted(
                    provenance_by_key[key_json],
                    key=lambda item: (
                        item["source_pdb_id"],
                        item["source_entity_id"],
                    ),
                ),
            }
        )
    return {
        "target_family_context_provenance": TARGET_FAMILY_CONTEXT_PROVENANCE,
        "target_family_context_input_sha256": {
            UPSTREAM_ACQUISITION_RELATIVE.as_posix(): INPUT_SHA256[
                UPSTREAM_ACQUISITION_RELATIVE
            ],
            "source_verified_mmcif_inventory_sha256": _sha(
                _json_bytes(source_inventory)
            ),
        },
        "target_family_context_was_derived_from_shadow_matches": False,
        "shadow_label_leakage_prohibited": True,
        "rule_context_is_independent_of_shadow_evaluation_population": True,
        "selection_contract": (
            "EXACT_STRUCTURED_ENTITY_PDBX_EC_EQUALS_2.1.1.45; "
            "EXACT_UNP_ACCESSION; EXACT_ENTITY_POLY_SEQ_MONOMER_SHA256"
        ),
        "rule_identity_excludes_pdb_id": True,
        "rule_identity_excludes_chain_id": True,
        "source_verified_structure_count": verified_count,
        "structured_ec_matched_structure_count": len(matched_structure_ids),
        "excluded_incomplete_ec_entity_count": excluded_ec_entity_count,
        "authorized_target_family_key_count": len(registry),
        "authorized_target_family_registry": registry,
    }


def load_immutable_human_gold_v1(repo_root: Path) -> dict[str, Any]:
    """Read and validate human gold from the exact calibration Git object."""

    object_spec = f"{CALIBRATION_COMMIT}:{HUMAN_DECISIONS_RELATIVE.as_posix()}"
    completed = subprocess.run(
        ["git", "show", object_spec],
        cwd=repo_root.resolve(),
        check=True,
        capture_output=True,
    )
    payload = completed.stdout
    if len(payload) != CALIBRATION_HUMAN_BYTES:
        raise ValueError("CALIBRATION_HUMAN_BYTES_MISMATCH")
    if _sha(payload) != CALIBRATION_HUMAN_SHA256:
        raise ValueError("CALIBRATION_HUMAN_SHA256_MISMATCH")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("CALIBRATION_HUMAN_ROOT_NOT_OBJECT")
    if value.get("schema_version") != "covapie_post_only_human_review_decisions_v1":
        raise ValueError("CALIBRATION_HUMAN_SCHEMA_MISMATCH")
    if any(
        value.get(field) is not False
        for field in (
            "authorized_population_changed",
            "production_authority_created",
            "production_materialization_performed",
            "training_materialization_performed",
        )
    ):
        raise ValueError("CALIBRATION_HUMAN_SAFETY_STATE_MISMATCH")
    units = value.get("units")
    history = value.get("decision_history")
    if not isinstance(units, list) or not isinstance(history, list):
        raise ValueError("CALIBRATION_HUMAN_COLLECTION_INVALID")
    matching = [
        item
        for item in units
        if isinstance(item, dict) and item.get("review_unit_id") == CALIBRATION_UNIT_ID
    ]
    if len(matching) != 1:
        raise ValueError("CALIBRATION_UNIT_NOT_UNIQUE")
    unit = matching[0]
    exact_state = {
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
    for field, expected in exact_state.items():
        if unit.get(field) != expected:
            raise ValueError("CALIBRATION_HUMAN_STATE_MISMATCH:" + field)
    events = unit.get("events")
    if not isinstance(events, list) or len(events) != CALIBRATION_EVENT_COUNT:
        raise ValueError("CALIBRATION_EVENT_COUNT_MISMATCH")
    event_ids: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("CALIBRATION_EVENT_NOT_OBJECT")
        event_id = event.get("canonical_event_id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("CALIBRATION_EVENT_ID_INVALID")
        event_ids.append(event_id)
        if any(
            event.get(field) != ""
            for field in (
                "post_geometry_training_usable",
                "event_training_use_decision",
                "event_exclusion_reason",
            )
        ):
            raise ValueError("CALIBRATION_EVENT_DECISION_NOT_BLANK")
    if len(set(event_ids)) != CALIBRATION_EVENT_COUNT:
        raise ValueError("CALIBRATION_EVENT_ID_DUPLICATE")

    unit_history = [
        item
        for item in history
        if isinstance(item, dict) and item.get("review_unit_id") == CALIBRATION_UNIT_ID
    ]
    expected_history = [
        (60, "training_domain_relevance_decision", exact_state["training_domain_relevance_decision"]),
        (61, "workflow_status", "COMPLETED"),
        (62, "reviewer_id", "fmx"),
        (63, "reviewed_at_utc", "2026-08-20T08:16:07Z"),
        (64, "review_rationale", CALIBRATION_RATIONALE),
    ]
    observed_history = [
        (item.get("sequence"), item.get("field"), item.get("new_value"))
        for item in unit_history
    ]
    if observed_history != expected_history:
        raise ValueError("CALIBRATION_HUMAN_HISTORY_MISMATCH")
    if any(
        not isinstance(item.get("entry_sha256"), str)
        or not _SHA256_RE.fullmatch(str(item.get("entry_sha256")))
        for item in unit_history
    ):
        raise ValueError("CALIBRATION_HUMAN_HISTORY_SHA_INVALID")
    return value


def validate_current_human_overlay_v1(
    value: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    """Validate a current descendant overlay without freezing its content SHA."""

    if not isinstance(value, Mapping):
        raise ValueError("CURRENT_HUMAN_OVERLAY_ROOT_INVALID")
    if value.get("schema_version") != "covapie_post_only_human_review_decisions_v1":
        raise ValueError("CURRENT_HUMAN_OVERLAY_SCHEMA_MISMATCH")
    if value.get("overlay_role") != (
        "HUMAN_REVIEW_DECISION_OVERLAY_NOT_PRODUCTION_AUTHORITY"
    ):
        raise ValueError("CURRENT_HUMAN_OVERLAY_ROLE_MISMATCH")
    if any(
        value.get(field) is not False
        for field in (
            "authorized_population_changed",
            "production_authority_created",
            "production_materialization_performed",
            "training_materialization_performed",
        )
    ):
        raise ValueError("CURRENT_HUMAN_OVERLAY_SAFETY_STATE_MISMATCH")
    units = value.get("units")
    if not isinstance(units, list):
        raise ValueError("CURRENT_HUMAN_OVERLAY_UNITS_INVALID")
    result: dict[str, Mapping[str, Any]] = {}
    all_event_ids: set[str] = set()
    allowed_decisions = {
        "",
        "RELEVANT_FOR_COVAPIE_POST_ONLY_V1",
        "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK",
        "DEFERRED_INSUFFICIENT_EVIDENCE",
    }
    for unit in units:
        if not isinstance(unit, Mapping):
            raise ValueError("CURRENT_HUMAN_OVERLAY_UNIT_NOT_OBJECT")
        unit_id = unit.get("review_unit_id")
        decision = unit.get("training_domain_relevance_decision")
        events = unit.get("events")
        if not isinstance(unit_id, str) or not unit_id or unit_id in result:
            raise ValueError("CURRENT_HUMAN_OVERLAY_UNIT_ID_INVALID")
        if decision not in allowed_decisions:
            raise ValueError("CURRENT_HUMAN_OVERLAY_DECISION_INVALID:" + unit_id)
        if not isinstance(events, list) or not events:
            raise ValueError("CURRENT_HUMAN_OVERLAY_UNIT_EVENTS_INVALID:" + unit_id)
        for event in events:
            if not isinstance(event, Mapping):
                raise ValueError("CURRENT_HUMAN_OVERLAY_EVENT_NOT_OBJECT")
            event_id = event.get("canonical_event_id")
            if (
                not isinstance(event_id, str)
                or not event_id
                or event_id in all_event_ids
            ):
                raise ValueError("CURRENT_HUMAN_OVERLAY_EVENT_ID_INVALID")
            all_event_ids.add(event_id)
        result[unit_id] = unit
    return result


def build_runtime_positive_override_context_v1(
    *,
    current_human_overlay: Mapping[str, Any],
    current_human_overlay_sha256: str,
    outcome_by_id: Mapping[str, Mapping[str, Any]],
    explicit_positive_override_event_ids: Sequence[str] = (),
) -> RuntimePositiveOverrideContext:
    """Build dynamic positive precedence inputs from current read-only state."""

    units = validate_current_human_overlay_v1(current_human_overlay)
    if not _SHA256_RE.fullmatch(current_human_overlay_sha256):
        raise ValueError("CURRENT_HUMAN_OVERLAY_SHA256_INVALID")
    human_positive = frozenset(
        str(event["canonical_event_id"])
        for unit in units.values()
        if unit.get("training_domain_relevance_decision")
        == "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
        for event in unit["events"]
    )
    production_positive: set[str] = set()
    for event_id, outcome in outcome_by_id.items():
        if not isinstance(event_id, str) or not isinstance(outcome, Mapping):
            raise ValueError("CURRENT_PRODUCTION_OUTCOME_CONTEXT_INVALID")
        value = outcome.get("existing_exact_authority_match")
        if type(value) is not bool:
            raise ValueError("CURRENT_PRODUCTION_AUTHORITY_BOOLEAN_INVALID")
        if value:
            production_positive.add(event_id)
    explicit = frozenset(explicit_positive_override_event_ids)
    if len(explicit) != len(tuple(explicit_positive_override_event_ids)) or any(
        not isinstance(event_id, str) or not event_id for event_id in explicit
    ):
        raise ValueError("EXPLICIT_POSITIVE_OVERRIDE_EVENT_IDS_INVALID")
    return RuntimePositiveOverrideContext(
        schema_version=RUNTIME_OVERRIDE_SCHEMA_VERSION,
        current_human_relevant_event_ids=human_positive,
        current_production_exact_positive_event_ids=frozenset(production_positive),
        explicit_positive_override_event_ids=explicit,
        current_human_overlay_sha256=current_human_overlay_sha256,
    )


def build_calibration_snapshot_positive_override_context_v1(
    *,
    immutable_calibration_human: Mapping[str, Any],
    frozen_outcome_by_id: Mapping[str, Mapping[str, Any]],
) -> RuntimePositiveOverrideContext:
    """Build the immutable override context for persisted shadow artifacts.

    The evaluator intentionally uses the same explicit precedence-context type
    at runtime and for the historical shadow experiment.  This constructor
    binds that context to the calibration Git object and SHA-bound production
    authority snapshot, never to the mutable descendant human overlay.
    """

    return build_runtime_positive_override_context_v1(
        current_human_overlay=immutable_calibration_human,
        current_human_overlay_sha256=CALIBRATION_HUMAN_SHA256,
        outcome_by_id=frozen_outcome_by_id,
    )


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


def _json_list(value: object, owner: str) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise _EvidenceError(owner + ":MALFORMED_JSON") from error
    if not isinstance(value, list):
        raise _EvidenceError(owner + ":EXPECTED_LIST")
    return value


def _coordinates(value: object, owner: str) -> list[float]:
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
    return result


def _target_observation_from_evidence(
    event: Mapping[str, Any], outcome: Mapping[str, Any]
) -> dict[str, str]:
    pdb_id = _required_string(event.get("pdb_id"), "event.pdb_id")
    if not _PDB_RE.fullmatch(pdb_id):
        raise _EvidenceError("event.pdb_id:GRAMMAR_INVALID")
    target = _required_string(
        event.get("target_residue_identity"), "event.target_residue_identity"
    )
    if not _TARGET_RE.fullmatch(target):
        raise _EvidenceError("event.target_residue_identity:GRAMMAR_INVALID")
    protein_atom = _required_string(
        event.get("protein_reactive_atom"), "event.protein_reactive_atom"
    )
    structural = _required_mapping(
        outcome.get("structural_processing"), "outcome.structural_processing"
    )
    leakage = _required_mapping(
        structural.get("leakage_evidence"),
        "outcome.structural_processing.leakage_evidence",
    )
    accession = _required_string(
        leakage.get("protein_accession"), "leakage_evidence.protein_accession"
    )
    sequence_sha = _required_sha(
        leakage.get("protein_sequence_sha256"),
        "leakage_evidence.protein_sequence_sha256",
    )
    return {
        "pdb_id": pdb_id,
        "protein_accession": accession,
        "protein_sequence_sha256": sequence_sha,
        "target_cys_identity": f"{pdb_id}:{target}:{protein_atom}",
        "protein_reactive_atom": protein_atom,
    }


def _target_family_key_from_evidence(
    event: Mapping[str, Any], outcome: Mapping[str, Any]
) -> dict[str, str]:
    observation = _target_observation_from_evidence(event, outcome)
    return {
        "protein_accession": observation["protein_accession"],
        "protein_sequence_sha256": observation["protein_sequence_sha256"],
        "protein_reactive_atom": observation["protein_reactive_atom"],
        "structured_target_family_id": "EC:" + TARGET_FAMILY_EC,
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


def evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
    *,
    event: Mapping[str, Any],
    outcome: Mapping[str, Any],
    rule_context: Mapping[str, Any],
    override_context: RuntimePositiveOverrideContext,
) -> AutoNegativeEvaluationResult:
    """Evaluate all exact predicates with fail-closed tri-state semantics.

    A decisive, well-formed mismatch remains ``NOT_MATCHED`` even when an
    unrelated downstream predicate is unavailable.  If no predicate disproves
    the rule, any missing or malformed required evidence is
    ``INVALID_EVIDENCE``.  Consequently missing evidence can never match.
    ``KeyboardInterrupt`` and ``SystemExit`` are intentionally not caught.
    """

    if not isinstance(event, Mapping):
        return _invalid_result((), ("event:EXPECTED_MAPPING",))
    if not isinstance(outcome, Mapping):
        return _invalid_result((), ("outcome:EXPECTED_MAPPING",))
    if not isinstance(rule_context, Mapping):
        return _invalid_result((), ("rule_context:EXPECTED_MAPPING",))
    if type(override_context) is not RuntimePositiveOverrideContext:
        return _invalid_result((), ("override_context:EXPECTED_FROZEN_CONTEXT",))

    matched: list[str] = []
    failed: list[str] = []
    invalid: list[str] = []

    def predicate(name: str, reader: Any, expected: object) -> None:
        try:
            actual = reader()
        except _EvidenceError as error:
            invalid.append(name + "[" + str(error) + "]")
            return
        if actual == expected:
            matched.append(name)
        else:
            failed.append(name)

    try:
        context_rule_id = _required_string(
            rule_context.get("rule_id"), "rule_context.rule_id"
        )
        if context_rule_id != RULE_ID:
            raise _EvidenceError("rule_context.rule_id:VALUE_MISMATCH")
        exact_ligand = _required_mapping(
            rule_context.get("exact_ligand_identity"),
            "rule_context.exact_ligand_identity",
        )
        expected_graph = _required_sha(
            exact_ligand.get("ccd_component_graph_sha256"),
            "rule_context.exact_ligand_identity.ccd_component_graph_sha256",
        )
        expected_atom = _required_string(
            exact_ligand.get("reactive_atom"),
            "rule_context.exact_ligand_identity.reactive_atom",
        )
        expected_element = _required_string(
            exact_ligand.get("reactive_element"),
            "rule_context.exact_ligand_identity.reactive_element",
        )
        expected_radius1 = _required_sha(
            exact_ligand.get("radius1_sha256"),
            "rule_context.exact_ligand_identity.radius1_sha256",
        )
        expected_radius2 = _required_sha(
            exact_ligand.get("radius2_sha256"),
            "rule_context.exact_ligand_identity.radius2_sha256",
        )
        if rule_context.get("target_family_context_provenance") != (
            TARGET_FAMILY_CONTEXT_PROVENANCE
        ):
            raise _EvidenceError(
                "rule_context.target_family_context_provenance:VALUE_MISMATCH"
            )
        provenance_inputs = _required_mapping(
            rule_context.get("target_family_context_input_sha256"),
            "rule_context.target_family_context_input_sha256",
        )
        if not provenance_inputs or any(
            not isinstance(name, str)
            or not name
            or not isinstance(digest, str)
            or not _SHA256_RE.fullmatch(digest)
            for name, digest in provenance_inputs.items()
        ):
            raise _EvidenceError(
                "rule_context.target_family_context_input_sha256:INVALID"
            )
        for field, expected in (
            ("target_family_context_was_derived_from_shadow_matches", False),
            ("shadow_label_leakage_prohibited", True),
            (
                "rule_context_is_independent_of_shadow_evaluation_population",
                True,
            ),
            ("rule_identity_excludes_pdb_id", True),
            ("rule_identity_excludes_chain_id", True),
            ("target_family_generalization_authorized", True),
        ):
            if _strict_bool(rule_context.get(field), "rule_context." + field) is not expected:
                raise _EvidenceError("rule_context." + field + ":VALUE_MISMATCH")
        allowed_raw = rule_context.get("authorized_target_family_registry")
        if not isinstance(allowed_raw, list) or not allowed_raw:
            raise _EvidenceError(
                "rule_context.authorized_target_family_registry:EXPECTED_NONEMPTY_LIST"
            )
        allowed: set[str] = set()
        for index, item in enumerate(allowed_raw):
            mapping = _required_mapping(item, f"rule_context.family_key[{index}]")
            normalized = {
                "protein_accession": _required_string(
                    mapping.get("protein_accession"),
                    f"rule_context.family_key[{index}].protein_accession",
                ),
                "protein_sequence_sha256": _required_sha(
                    mapping.get("protein_sequence_sha256"),
                    f"rule_context.family_key[{index}].protein_sequence_sha256",
                ),
                "protein_reactive_atom": _required_string(
                    mapping.get("protein_reactive_atom"),
                    f"rule_context.family_key[{index}].protein_reactive_atom",
                ),
                "structured_target_family_id": _required_string(
                    mapping.get("structured_target_family_id"),
                    f"rule_context.family_key[{index}].structured_target_family_id",
                ),
            }
            if normalized["structured_target_family_id"] != "EC:" + TARGET_FAMILY_EC:
                raise _EvidenceError(
                    f"rule_context.family_key[{index}].structured_target_family_id:VALUE_MISMATCH"
                )
            allowed.add(_json_cell(normalized))
        if len(allowed) != len(allowed_raw):
            raise _EvidenceError("rule_context.family_key:DUPLICATE")
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
        positive_id_set = frozenset().union(*override_sets)
    except _EvidenceError as error:
        return _invalid_result((), (str(error),))

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
        (
            "exact_reactive_ligand_atom_coverage",
            "reactive_ligand_atom_exact_coverage",
        ),
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

    def outcome_feature_status() -> str:
        statuses = _required_mapping(
            outcome.get("stage_statuses"), "outcome.stage_statuses"
        )
        return _required_string(
            statuses.get("BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"),
            "outcome.stage_statuses.BULK_09_MODEL_AND_FEATURE_COMPATIBILITY",
        )

    predicate("outcome_feature_projection_passed", outcome_feature_status, "PASSED")

    def structural_value(field: str) -> object:
        structural = _required_mapping(
            outcome.get("structural_processing"), "outcome.structural_processing"
        )
        if field not in structural:
            raise _EvidenceError("outcome.structural_processing." + field + ":MISSING")
        return structural[field]

    predicate(
        "outcome_explicit_covalent_evidence",
        lambda: _strict_bool(
            structural_value("explicit_covalent_evidence"),
            "outcome.structural_processing.explicit_covalent_evidence",
        ),
        True,
    )

    def exact_connection_and_coordinates() -> bool:
        _required_string(
            structural_value("selected_connection_id"),
            "outcome.structural_processing.selected_connection_id",
        )
        _coordinates(
            structural_value("protein_endpoint_coordinates"),
            "outcome.structural_processing.protein_endpoint_coordinates",
        )
        _coordinates(
            structural_value("ligand_endpoint_coordinates"),
            "outcome.structural_processing.ligand_endpoint_coordinates",
        )
        _coordinates(
            event.get("selected_protein_endpoint_coordinates_json"),
            "event.selected_protein_endpoint_coordinates_json",
        )
        _coordinates(
            event.get("selected_ligand_endpoint_coordinates_json"),
            "event.selected_ligand_endpoint_coordinates_json",
        )
        return True

    predicate(
        "exact_connection_and_endpoint_coordinates",
        exact_connection_and_coordinates,
        True,
    )
    predicate(
        "exact_ccd_component_graph_sha256",
        lambda: _required_sha(
            event.get("ccd_component_graph_sha256"),
            "event.ccd_component_graph_sha256",
        ),
        expected_graph,
    )
    predicate(
        "exact_ligand_reactive_atom",
        lambda: _required_string(
            event.get("ligand_reactive_atom"), "event.ligand_reactive_atom"
        ),
        expected_atom,
    )
    predicate(
        "exact_ligand_reactive_element",
        lambda: _required_string(
            event.get("ligand_reactive_element"), "event.ligand_reactive_element"
        ),
        expected_element,
    )
    predicate(
        "exact_radius1_sha256",
        lambda: _required_sha(
            event.get("reactive_center_radius1_fingerprint"),
            "event.reactive_center_radius1_fingerprint",
        ),
        expected_radius1,
    )
    predicate(
        "exact_radius2_sha256",
        lambda: _required_sha(
            event.get("reactive_center_radius2_fingerprint"),
            "event.reactive_center_radius2_fingerprint",
        ),
        expected_radius2,
    )

    target_family_key_holder: dict[str, str] = {}

    def target_is_allowed() -> bool:
        target_family_key_holder.update(
            _target_family_key_from_evidence(event, outcome)
        )
        return _json_cell(target_family_key_holder) in allowed

    predicate("exact_ts_family_accession_sequence_key", target_is_allowed, True)

    def structured_protein_identity_source_boundary() -> bool:
        structural = _required_mapping(
            outcome.get("structural_processing"), "outcome.structural_processing"
        )
        leakage = _required_mapping(
            structural.get("leakage_evidence"),
            "outcome.structural_processing.leakage_evidence",
        )
        source_boundary = _required_string(
            leakage.get("source_boundary"), "leakage_evidence.source_boundary"
        )
        external = _strict_bool(
            leakage.get("external_uniprot_call_performed"),
            "leakage_evidence.external_uniprot_call_performed",
        )
        return bool(
            source_boundary == "PDB_MMCIF_CORE_PLUS_OFFICIAL_WWPDB_CCD"
            and external is False
        )

    predicate(
        "structured_protein_identity_source_boundary",
        structured_protein_identity_source_boundary,
        True,
    )

    def source_annotations_well_formed() -> bool:
        annotations = _json_list(
            event.get("source_annotations_json"), "event.source_annotations_json"
        )
        if not annotations or any(not isinstance(item, Mapping) for item in annotations):
            raise _EvidenceError("event.source_annotations_json:ITEMS_INVALID")
        return True

    predicate(
        "source_annotations_well_formed", source_annotations_well_formed, True
    )
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

    def production_not_created() -> bool:
        event_approval = _strict_bool(
            event.get("production_approval_created"),
            "event.production_approval_created",
        )
        outcome_materialization = _strict_bool(
            outcome.get("production_materialization_performed"),
            "outcome.production_materialization_performed",
        )
        return not event_approval and not outcome_materialization

    predicate("no_production_approval", production_not_created, True)

    def no_runtime_positive_override() -> bool:
        event_id = _required_string(
            event.get("canonical_event_id"), "event.canonical_event_id"
        )
        outcome_id = _required_string(
            outcome.get("canonical_event_id"), "outcome.canonical_event_id"
        )
        if event_id != outcome_id:
            raise _EvidenceError("event_outcome.canonical_event_id:MISMATCH")
        return event_id not in positive_id_set

    predicate("no_runtime_positive_override", no_runtime_positive_override, True)

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
    *,
    review_unit_id: str,
    event_results: Sequence[AutoNegativeEvaluationResult],
) -> UnitShadowEvaluationResult:
    """Auto-negative a unit only when every event independently matches."""

    if not isinstance(review_unit_id, str) or not review_unit_id:
        raise ValueError("REVIEW_UNIT_ID_INVALID")
    if not isinstance(event_results, Sequence) or isinstance(
        event_results, (str, bytes)
    ):
        raise ValueError("EVENT_RESULTS_NOT_SEQUENCE")
    results = list(event_results)
    if not results:
        raise ValueError("EVENT_RESULTS_EMPTY")
    if any(type(result) is not AutoNegativeEvaluationResult for result in results):
        raise ValueError("EVENT_RESULT_TYPE_INVALID")
    if any(result.rule_id != RULE_ID for result in results):
        raise ValueError("EVENT_RESULT_RULE_ID_MISMATCH")
    counts = Counter(result.status for result in results)
    allowed_statuses = {
        MATCHED_AUTO_NEGATIVE_EXACT,
        NOT_MATCHED,
        INVALID_EVIDENCE,
    }
    if set(counts) - allowed_statuses:
        raise ValueError("EVENT_RESULT_STATUS_INVALID")
    all_match = counts[MATCHED_AUTO_NEGATIVE_EXACT] == len(results)
    if all_match:
        status = UNIT_SHADOW_AUTO_NEGATIVE_EXACT
        reason = "EVERY_EVENT_IN_UNIT_MATCHED_SAME_EXACT_RULE"
    else:
        status = UNIT_NOT_SHADOW_AUTO_NEGATIVE
        reason = (
            "UNIT_FAIL_CLOSED:matched="
            + str(counts[MATCHED_AUTO_NEGATIVE_EXACT])
            + ",not_matched="
            + str(counts[NOT_MATCHED])
            + ",invalid="
            + str(counts[INVALID_EVIDENCE])
        )
    return UnitShadowEvaluationResult(
        rule_id=RULE_ID,
        review_unit_id=review_unit_id,
        status=status,
        reason=reason,
        event_count=len(results),
        matched_event_count=counts[MATCHED_AUTO_NEGATIVE_EXACT],
        invalid_event_count=counts[INVALID_EVIDENCE],
        shadow_would_auto_negative=all_match,
    )


def _load_calibration_snapshot_evidence_v1(repo_root: Path) -> dict[str, Any]:
    """Load only SHA-bound and immutable calibration-snapshot evidence."""

    input_hashes = verify_bound_inputs_v1(repo_root)
    with (repo_root / EVENT_INVENTORY_RELATIVE).open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        all_event_rows = list(csv.DictReader(handle))
    candidate_rows = [
        row
        for row in all_event_rows
        if row.get("post_only_partition") == "POST_ONLY_V1_REVIEW_CANDIDATE"
    ]
    if len(candidate_rows) != 123:
        raise ValueError("CANDIDATE_EVENT_COUNT_MISMATCH")
    event_by_id = {row.get("canonical_event_id", ""): row for row in candidate_rows}
    if len(event_by_id) != len(candidate_rows) or "" in event_by_id:
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
        if not isinstance(unit_id, str) or not unit_id or unit_id in unit_by_id:
            raise ValueError("REVIEW_PACKET_UNIT_ID_INVALID_OR_DUPLICATE")
        if not isinstance(event_ids, list) or not event_ids:
            raise ValueError("REVIEW_PACKET_UNIT_EVENTS_INVALID")
        unit_by_id[unit_id] = unit
        for event_id in event_ids:
            if not isinstance(event_id, str) or event_id in unit_by_event:
                raise ValueError("EVENT_REVIEW_UNIT_MEMBERSHIP_INVALID")
            unit_by_event[event_id] = unit_id
    if set(unit_by_event) != set(event_by_id):
        raise ValueError("REVIEW_UNIT_CANDIDATE_EVENT_COVERAGE_MISMATCH")

    outcomes_artifact = _read_json_object(repo_root / UPSTREAM_OUTCOMES_RELATIVE)
    outcomes = outcomes_artifact.get("events")
    if not isinstance(outcomes, list):
        raise ValueError("UPSTREAM_OUTCOME_EVENTS_INVALID")
    outcome_by_id = {
        item.get("canonical_event_id", ""): item
        for item in outcomes
        if isinstance(item, dict)
    }
    if not set(event_by_id) <= set(outcome_by_id):
        raise ValueError("CANDIDATE_OUTCOME_COVERAGE_MISMATCH")

    legacy_summary = _read_json_object(repo_root / LEGACY_SUMMARY_RELATIVE)
    if (
        legacy_summary.get("population", {}).get(
            "post_only_v1_review_candidate_count"
        )
        != 123
        or legacy_summary.get("human_review_workload", {}).get("review_unit_count")
        != 36
        or legacy_summary.get("training_domain_relevance", {}).get(
            "all_candidates_still_require_human_decision"
        )
        is not True
    ):
        raise ValueError("LEGACY_SUMMARY_SEMANTICS_MISMATCH")

    calibration_human = load_immutable_human_gold_v1(repo_root)
    calibration_units_raw = calibration_human.get("units")
    if not isinstance(calibration_units_raw, list):
        raise ValueError("CALIBRATION_HUMAN_UNIT_COLLECTION_INVALID")
    calibration_human_unit_by_id = {
        item.get("review_unit_id", ""): item
        for item in calibration_units_raw
        if isinstance(item, dict)
    }
    if set(calibration_human_unit_by_id) != set(unit_by_id):
        raise ValueError("CALIBRATION_HUMAN_REVIEW_UNIT_COVERAGE_MISMATCH")
    for unit_id in HUMAN_RELEVANT_COUNTEREXAMPLE_UNITS:
        if calibration_human_unit_by_id[unit_id].get(
            "training_domain_relevance_decision"
        ) != "RELEVANT_FOR_COVAPIE_POST_ONLY_V1":
            raise ValueError("HUMAN_RELEVANT_COUNTEREXAMPLE_STATE_MISMATCH:" + unit_id)

    return {
        "input_hashes": input_hashes,
        "event_by_id": event_by_id,
        "outcome_by_id": outcome_by_id,
        "unit_by_id": unit_by_id,
        "unit_by_event": unit_by_event,
        "calibration_human": calibration_human,
        "calibration_human_unit_by_id": calibration_human_unit_by_id,
        "legacy_summary": legacy_summary,
    }


def _load_bound_evidence_v1(repo_root: Path) -> dict[str, Any]:
    """Load frozen evidence plus separately validated current runtime state."""

    evidence = _load_calibration_snapshot_evidence_v1(repo_root)
    current_human_payload = (repo_root / HUMAN_DECISIONS_RELATIVE).read_bytes()
    current_human = json.loads(current_human_payload)
    current_human_unit_by_id = validate_current_human_overlay_v1(current_human)
    if not set(evidence["unit_by_id"]) <= set(current_human_unit_by_id):
        raise ValueError("CURRENT_HUMAN_REVIEW_UNIT_COVERAGE_MISMATCH")
    return {
        **evidence,
        "current_human": current_human,
        "current_human_unit_by_id": current_human_unit_by_id,
        "current_human_overlay_sha256": _sha(current_human_payload),
    }


def _build_static_rule_context_v1(
    *, repo_root: Path, cache_root: Path
) -> dict[str, Any]:
    """Construct scientific rule inputs without any shadow population labels."""

    verify_bound_inputs_v1(repo_root)
    calibration_human = load_immutable_human_gold_v1(repo_root)
    calibration_unit = next(
        unit
        for unit in calibration_human["units"]
        if unit["review_unit_id"] == CALIBRATION_UNIT_ID
    )
    calibration_event_ids = {
        event["canonical_event_id"] for event in calibration_unit["events"]
    }
    with (repo_root / EVENT_INVENTORY_RELATIVE).open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        calibration_rows = {
            row["canonical_event_id"]: row
            for row in csv.DictReader(handle)
            if row.get("canonical_event_id") in calibration_event_ids
        }
    outcomes = _read_json_object(repo_root / UPSTREAM_OUTCOMES_RELATIVE).get(
        "events"
    )
    if not isinstance(outcomes, list):
        raise ValueError("CALIBRATION_MACHINE_OUTCOMES_INVALID")
    calibration_outcomes = {
        outcome.get("canonical_event_id"): outcome
        for outcome in outcomes
        if isinstance(outcome, Mapping)
        and outcome.get("canonical_event_id") in calibration_event_ids
    }
    if set(calibration_rows) != calibration_event_ids or set(
        calibration_outcomes
    ) != calibration_event_ids:
        raise ValueError("CALIBRATION_MACHINE_EVENT_COVERAGE_MISMATCH")
    calibration_family_keys: set[str] = set()
    for event_id in sorted(calibration_event_ids):
        row = calibration_rows[event_id]
        if (
            row.get("post_only_partition") != "POST_ONLY_V1_REVIEW_CANDIDATE"
            or row.get("ccd_component_graph_sha256") != DUMP_GRAPH_SHA256
            or row.get("ligand_reactive_atom") != DUMP_REACTIVE_ATOM
            or row.get("ligand_reactive_element") != DUMP_REACTIVE_ELEMENT
            or row.get("reactive_center_radius1_fingerprint")
            != DUMP_RADIUS1_SHA256
            or row.get("reactive_center_radius2_fingerprint")
            != DUMP_RADIUS2_SHA256
        ):
            raise ValueError("CALIBRATION_MACHINE_CHEMISTRY_MISMATCH:" + event_id)
        calibration_family_keys.add(
            _json_cell(
                _target_family_key_from_evidence(
                    row, calibration_outcomes[event_id]
                )
            )
        )
    family_context = build_independent_target_family_context_v1(
        repo_root=repo_root, cache_root=cache_root
    )
    registry_keys = {
        _json_cell(
            {
                "protein_accession": item["protein_accession"],
                "protein_sequence_sha256": item["protein_sequence_sha256"],
                "protein_reactive_atom": item["protein_reactive_atom"],
                "structured_target_family_id": item[
                    "structured_target_family_id"
                ],
            }
        )
        for item in family_context["authorized_target_family_registry"]
    }
    if not calibration_family_keys <= registry_keys:
        raise ValueError("TARGET_FAMILY_GENERALIZATION_EVIDENCE_INSUFFICIENT")
    return {
        "schema_version": SCHEMA_VERSION,
        "rule_id": RULE_ID,
        "exact_ligand_identity": {
            "ccd_component_graph_sha256": DUMP_GRAPH_SHA256,
            "reactive_atom": DUMP_REACTIVE_ATOM,
            "reactive_element": DUMP_REACTIVE_ELEMENT,
            "radius1_sha256": DUMP_RADIUS1_SHA256,
            "radius2_sha256": DUMP_RADIUS2_SHA256,
        },
        **family_context,
        "target_family_generalization_authorized": True,
        "calibration_machine_evidence_event_count": len(calibration_event_ids),
        "context_semantics": (
            "EXACT_DUMP_C6_LOCAL_CHEMISTRY_PLUS_EXPLICIT_CYS_SG_EVENT_PLUS_"
            "STRUCTURED_TS_EC_FAMILY; NO_STANDALONE_CATALYTIC_PREDICATE_CLAIM"
        ),
        "required_predicates": list(REQUIRED_PREDICATES),
        "forbidden_sole_predicates": list(FORBIDDEN_SOLE_PREDICATES),
        "source_reaction_annotation_mandatory": False,
    }


def _build_rule_manifest_base_v1(
    *, scientific_rule_context: Mapping[str, Any], evidence: Mapping[str, Any]
) -> dict[str, Any]:
    calibration_human = evidence["calibration_human"]
    calibration = evidence["calibration_human_unit_by_id"][CALIBRATION_UNIT_ID]
    history = [
        item
        for item in calibration_human["decision_history"]
        if item.get("review_unit_id") == CALIBRATION_UNIT_ID
    ]
    calibration_snapshot_positive_event_ids = sorted(
        event_id
        for unit_id in HUMAN_RELEVANT_COUNTEREXAMPLE_UNITS
        for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]
    )
    immutable_object = (
        CALIBRATION_COMMIT + ":" + HUMAN_DECISIONS_RELATIVE.as_posix()
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "rule_id": RULE_ID,
        "rule_role": "TASK_DOMAIN_AUTO_NEGATIVE_RULE",
        "implementation_mode": "SHADOW_EXACT_GATE_NOT_YET_LIVE_ROUTING",
        "artifact_semantics": ARTIFACT_SEMANTICS,
        "runtime_state_embedded_in_deterministic_artifacts": False,
        "current_human_overlay_embedded_in_deterministic_artifacts": False,
        "runtime_positive_override_evaluated_separately": True,
        "human_readable_meaning": (
            "Exact natural dUMP C6-to-Cys-SG adduct in an independently "
            "EC-authorized thymidylate-synthase target family context, "
            "outside the positive medicinal covalent-ligand generation domain."
        ),
        "not_authority_for": [
            "reaction_family",
            "warhead",
            "production_chemistry",
            "training_sample",
        ],
        "shadow_label_leakage_prohibited": True,
        "rule_context_is_independent_of_shadow_evaluation_population": True,
        "target_family_context_provenance": scientific_rule_context[
            "target_family_context_provenance"
        ],
        "target_family_context_input_sha256": scientific_rule_context[
            "target_family_context_input_sha256"
        ],
        "target_family_context_was_derived_from_shadow_matches": False,
        "descendant_repository_compatible": True,
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
            "reactive_atom_confirmation": calibration[
                "reactive_atom_confirmation"
            ],
            "warhead_family_decision": calibration["warhead_family_decision"],
            "warhead_atom_ids": calibration["warhead_atom_ids"],
            "roles": calibration["roles"],
            "event_decision_count": len(calibration["events"]),
            "all_event_decisions_blank": True,
            "review_rationale": calibration["review_rationale"],
        },
        "calibration_human_history_evidence": history,
        "input_artifact_sha256": evidence["input_hashes"],
        "scientific_rule_context": dict(scientific_rule_context),
        "runtime_positive_override_policy": RUNTIME_POSITIVE_OVERRIDE_POLICY,
        "calibration_snapshot_positive_counterexamples": {
            "review_unit_ids": list(HUMAN_RELEVANT_COUNTEREXAMPLE_UNITS),
            "canonical_event_ids": calibration_snapshot_positive_event_ids,
            "not_complete_future_override_universe": True,
        },
    }


def _human_state(unit: Mapping[str, Any]) -> str:
    workflow = str(unit.get("workflow_status") or "")
    decision = str(unit.get("training_domain_relevance_decision") or "")
    return workflow + (":" + decision if decision else "")


def _reason_failed_predicates(reason: str) -> set[str]:
    prefix = "PREDICATE_MISMATCH:"
    if not reason.startswith(prefix):
        return set()
    return set(reason[len(prefix) :].split(";", 1)[0].split(","))


def build_artifacts_v1(
    *,
    repo_root: Path,
    cache_root: Path | None = None,
) -> dict[str, bytes]:
    """Build three deterministic shadow artifacts entirely in memory."""

    repo_root = repo_root.resolve()
    resolved_cache_root = (
        cache_root.resolve()
        if cache_root is not None
        else repo_root.parent / CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    verify_repository_binding_v1(repo_root)
    input_hashes_before = verify_bound_inputs_v1(repo_root)
    scientific_rule_context = _build_static_rule_context_v1(
        repo_root=repo_root, cache_root=resolved_cache_root
    )
    evidence = _load_calibration_snapshot_evidence_v1(repo_root)
    override_context = build_calibration_snapshot_positive_override_context_v1(
        immutable_calibration_human=evidence["calibration_human"],
        frozen_outcome_by_id=evidence["outcome_by_id"],
    )
    manifest = _build_rule_manifest_base_v1(
        scientific_rule_context=scientific_rule_context,
        evidence=evidence,
    )

    event_results: dict[str, AutoNegativeEvaluationResult] = {}
    by_unit_results: dict[str, list[AutoNegativeEvaluationResult]] = defaultdict(list)
    for event_id in sorted(evidence["event_by_id"]):
        result = evaluate_neg_v1_ts_dump_catalytic_adduct_exact(
            event=evidence["event_by_id"][event_id],
            outcome=evidence["outcome_by_id"][event_id],
            rule_context=scientific_rule_context,
            override_context=override_context,
        )
        event_results[event_id] = result
        by_unit_results[evidence["unit_by_event"][event_id]].append(result)
    unit_results = {
        unit_id: aggregate_review_unit_shadow_v1(
            review_unit_id=unit_id, event_results=results
        )
        for unit_id, results in sorted(by_unit_results.items())
    }

    event_counts = Counter(result.status for result in event_results.values())
    matched_units = sorted(
        unit_id
        for unit_id, result in unit_results.items()
        if result.shadow_would_auto_negative
    )
    sibling_event_ids = list(
        evidence["unit_by_id"].get(SIBLING_UNIT_ID, {}).get(
            "canonical_event_ids", []
        )
    )
    sibling_matched_event_count = sum(
        event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in sibling_event_ids
    )
    generalization_without_sibling_label_leakage = bool(
        sibling_event_ids
        and sibling_matched_event_count == len(sibling_event_ids)
        and unit_results[SIBLING_UNIT_ID].shadow_would_auto_negative
        and scientific_rule_context[
            "rule_context_is_independent_of_shadow_evaluation_population"
        ]
        is True
        and scientific_rule_context[
            "target_family_context_was_derived_from_shadow_matches"
        ]
        is False
    )
    target_family_generalization_authorized = bool(
        scientific_rule_context["target_family_generalization_authorized"]
    )
    live_integration_ready = bool(
        generalization_without_sibling_label_leakage
        and target_family_generalization_authorized
        and event_counts[INVALID_EVIDENCE] == 0
    )
    readiness_mode = (
        GENERALIZATION_MODE if live_integration_ready else CALIBRATION_ONLY_MODE
    )

    for unit_id in UFP_COUNTEREXAMPLE_UNITS:
        for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]:
            result = event_results[event_id]
            required = {
                "exact_ccd_component_graph_sha256",
                "exact_radius2_sha256",
            }
            if result.status != NOT_MATCHED or not required <= _reason_failed_predicates(
                result.reason
            ):
                raise ValueError("UFP_COUNTEREXAMPLE_PROOF_FAILED:" + event_id)

    human_relevant_ids = {
        event_id
        for unit_id in HUMAN_RELEVANT_COUNTEREXAMPLE_UNITS
        for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]
    }
    pyr_ids = set(
        evidence["unit_by_id"][PYR_COUNTEREXAMPLE_UNIT]["canonical_event_ids"]
    )
    if any(
        event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in human_relevant_ids | pyr_ids
    ):
        raise ValueError("POSITIVE_OR_PYR_BOUNDARY_MATCHED")

    manifest.update(
        {
            "readiness_mode": readiness_mode,
            "generalization_without_sibling_label_leakage": (
                generalization_without_sibling_label_leakage
            ),
            "target_family_generalization_authorized": (
                target_family_generalization_authorized
            ),
            "live_integration_ready": live_integration_ready,
            "observed_shadow_counts": {
                "candidate_event_count": len(event_results),
                "matched_event_count": event_counts[
                    MATCHED_AUTO_NEGATIVE_EXACT
                ],
                "not_matched_event_count": event_counts[NOT_MATCHED],
                "invalid_evidence_count": event_counts[INVALID_EVIDENCE],
                "matched_unit_count": len(matched_units),
            },
            "leave_one_unit_out_generalization": {
                "reporting_unit_id": SIBLING_UNIT_ID,
                "rule_context_constructed_without_reporting_unit_or_event_ids": True,
                "observed_event_count": len(sibling_event_ids),
                "observed_matched_event_count": sibling_matched_event_count,
                "all_events_generalized": (
                    generalization_without_sibling_label_leakage
                ),
            },
            "counterexample_observations": {
                "UFP_match_count": sum(
                    event_results[event_id].status
                    == MATCHED_AUTO_NEGATIVE_EXACT
                    for unit_id in UFP_COUNTEREXAMPLE_UNITS
                    for event_id in evidence["unit_by_id"][unit_id][
                        "canonical_event_ids"
                    ]
                ),
                "calibration_snapshot_human_relevant_match_count": sum(
                    event_results[event_id].status
                    == MATCHED_AUTO_NEGATIVE_EXACT
                    for event_id in human_relevant_ids
                ),
                "PYR_match_count": sum(
                    event_results[event_id].status
                    == MATCHED_AUTO_NEGATIVE_EXACT
                    for event_id in pyr_ids
                ),
            },
        }
    )

    rows: list[dict[str, object]] = []
    for event_id in sorted(evidence["event_by_id"]):
        event = evidence["event_by_id"][event_id]
        outcome = evidence["outcome_by_id"][event_id]
        unit_id = evidence["unit_by_event"][event_id]
        target = _target_observation_from_evidence(event, outcome)
        result = event_results[event_id]
        unit_result = unit_results[unit_id]
        raw = {
            "canonical_event_id": event_id,
            "review_unit_id": unit_id,
            "pdb_id": event["pdb_id"],
            "ligand_component_id": event["ligand_component_id"],
            "target_cys_identity": target["target_cys_identity"],
            "protein_accession": target["protein_accession"],
            "protein_sequence_sha256": target["protein_sequence_sha256"],
            "ccd_component_graph_sha256": event["ccd_component_graph_sha256"],
            "ligand_reactive_atom": event["ligand_reactive_atom"],
            "ligand_reactive_element": event["ligand_reactive_element"],
            "radius1_sha256": event["reactive_center_radius1_fingerprint"],
            "radius2_sha256": event["reactive_center_radius2_fingerprint"],
            "rule_id": result.rule_id,
            "evaluation_status": result.status,
            "evaluation_reason": result.reason,
            "matched_predicates_json": _json_cell(list(result.matched_predicates)),
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
    human_units = list(evidence["calibration_human_unit_by_id"].values())
    calibration_snapshot_unreviewed_units = sum(
        unit.get("workflow_status") == "UNREVIEWED" for unit in human_units
    )
    unreviewed_matched_units = [
        unit_id
        for unit_id in matched_units
        if evidence["calibration_human_unit_by_id"][unit_id].get("workflow_status")
        == "UNREVIEWED"
    ]
    unreviewed_matched_events = sum(
        len(evidence["unit_by_id"][unit_id]["canonical_event_ids"])
        for unit_id in unreviewed_matched_units
    )
    calibration_matched_events = sum(
        event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
        for event_id in evidence["unit_by_id"][CALIBRATION_UNIT_ID][
            "canonical_event_ids"
        ]
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "rule_id": RULE_ID,
        "implementation_mode": "SHADOW_EXACT_GATE_NOT_YET_LIVE_ROUTING",
        "artifact_semantics": ARTIFACT_SEMANTICS,
        "runtime_state_embedded_in_deterministic_artifacts": False,
        "current_human_overlay_embedded_in_deterministic_artifacts": False,
        "runtime_positive_override_evaluated_separately": True,
        "readiness_mode": readiness_mode,
        "generalization_without_sibling_label_leakage": (
            generalization_without_sibling_label_leakage
        ),
        "target_family_generalization_authorized": (
            target_family_generalization_authorized
        ),
        "live_integration_ready": live_integration_ready,
        "shadow_label_leakage_removed": True,
        "rule_context_independent_of_shadow_population": True,
        "descendant_repository_compatible": True,
        "future_human_positive_override_supported": True,
        "immutable_calibration_gold_sha256": CALIBRATION_HUMAN_SHA256,
        "repository_binding_policy": {
            "branch_required": "main",
            "head_must_equal_origin_main": True,
            "ahead_behind_required": "0/0",
            "calibration_commit": CALIBRATION_COMMIT,
            "calibration_commit_must_be_ancestor": True,
            "descendant_repository_supported": True,
        },
        "input_artifact_sha256": evidence["input_hashes"],
        "historical_frozen_v1_state": {
            "source_summary_path": LEGACY_SUMMARY_RELATIVE.as_posix(),
            "source_summary_sha256": INPUT_SHA256[LEGACY_SUMMARY_RELATIVE],
            "all_candidates_still_require_human_decision": True,
            "artifact_modified": False,
        },
        "legacy_v1_all_candidates_still_require_human_decision": True,
        "shadow_exact_auto_negative_gate_available": True,
        "candidate_event_count": len(event_results),
        "historical_review_unit_count": 36,
        "observed_shadow_matched_event_count": event_counts[
            MATCHED_AUTO_NEGATIVE_EXACT
        ],
        "observed_shadow_matched_unit_count": len(matched_units),
        "rule_shadow_matched_event_count": event_counts[
            MATCHED_AUTO_NEGATIVE_EXACT
        ],
        "rule_shadow_matched_unit_count": len(matched_units),
        "human_calibration_matched_event_count": calibration_matched_events,
        "human_calibration_matched_unit_count": int(
            CALIBRATION_UNIT_ID in matched_units
        ),
        "calibration_snapshot_unreviewed_shadow_auto_negative_event_count": (
            unreviewed_matched_events
        ),
        "calibration_snapshot_unreviewed_shadow_auto_negative_unit_count": len(
            unreviewed_matched_units
        ),
        "UFP_counterexample_match_count": sum(
            event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
            for unit_id in UFP_COUNTEREXAMPLE_UNITS
            for event_id in evidence["unit_by_id"][unit_id]["canonical_event_ids"]
        ),
        "calibration_snapshot_human_relevant_match_count": sum(
            event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
            for event_id in human_relevant_ids
        ),
        "PYR_boundary_match_count": sum(
            event_results[event_id].status == MATCHED_AUTO_NEGATIVE_EXACT
            for event_id in pyr_ids
        ),
        "invalid_evidence_count": event_counts[INVALID_EVIDENCE],
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
        "calibration_snapshot_unreviewed_unit_workload": (
            calibration_snapshot_unreviewed_units
        ),
        "calibration_snapshot_projected_remaining_unreviewed_unit_workload": (
            calibration_snapshot_unreviewed_units - len(unreviewed_matched_units)
        ),
        "calibration_snapshot_workload_projection_label": (
            "CALIBRATION_SNAPSHOT_SHADOW_PROJECTION_ONLY"
        ),
        "legacy_triage_artifacts_modified": False,
        "human_review_overlay_modified": False,
        "production_chemistry_authority_created": False,
        "training_materialization_performed": False,
        "integration_into_live_triage_performed": False,
        "output_sha256_excluding_summary": {
            RULE_MANIFEST: _sha(manifest_bytes),
            SHADOW_INVENTORY: _sha(inventory_bytes),
        },
        "ready_for_gpt_review": True,
        "recommended_next_step_exactly": (
            "gpt_audit_descendant_determinism_fix_then_commit_push_fix"
            if live_integration_ready
            else "gpt_audit_revised_gate_then_resolve_target_family_generalization_blocker"
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
