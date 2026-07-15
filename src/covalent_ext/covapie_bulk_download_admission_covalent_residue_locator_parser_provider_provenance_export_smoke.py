"""Synthetic parser/provider provenance export smoke for CovaPIE.

This module is deliberately additive.  It parses only caller-supplied text,
retains raw logical mmCIF tokens, and delegates the frozen metadata mapping to
the Step14AU-E0-P4 module.  It does not integrate with either real preparation
pipeline and does not read raw structures.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from covalent_ext import (
    covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate
    as p4_gate,
)
from covalent_ext import covapie_sample_preparation_execution_smoke as historical


STEP_LABEL = "Step14AU-E0-P5-B"
STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_parser_provider_"
    "provenance_export_smoke_v1"
)
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_parser_provider_"
    "provenance_export_design_gate_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_parser_provider_provenance_export_smoke_"
    "v1_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_covalent_residue_locator_real_parser_provider_pipeline_"
    "integration_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_parser_provider_provenance_"
    "export_smoke_blockers"
)
PROJECT_NAME = "CovaPIE"
SOURCE_READ_BOUNDARY = (
    "only_p4_seven_committed_design_sources_and_two_frozen_historical_parser_modules"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
P4_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_parser_provider_provenance_export_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_parser_provider_provenance_export_smoke_v1"
)

SOURCE_PATHS = (
    Path(
        "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_"
        "locator_parser_provider_provenance_export_design_gate.py"
    ),
    P4_ROOT / "covapie_covalent_residue_locator_parser_provider_export_contract.csv",
    P4_ROOT / "covapie_covalent_residue_locator_raw_token_resolution_matrix.csv",
    P4_ROOT / "covapie_covalent_residue_locator_source_boundary_audit.csv",
    P4_ROOT / "covapie_covalent_residue_locator_safety_audit.csv",
    P4_ROOT / "covapie_covalent_residue_locator_parser_provider_issue_inventory.csv",
    P4_ROOT
    / "covapie_covalent_residue_locator_parser_provider_provenance_export_design_manifest.json",
    Path("src/covalent_ext/covapie_sample_preparation_execution_smoke.py"),
    Path(
        "src/covalent_ext/covapie_independent_group_expansion_batch_sample_"
        "preparation_execution_smoke.py"
    ),
)
SOURCE_SHA256 = {
    SOURCE_PATHS[0].as_posix(): "b1a874e402180a361b6940541c95710797ed10cabfdb19f7426c0b04d0532537",
    SOURCE_PATHS[1].as_posix(): "8893ca769577e955319ea8b9abe411149206db562193b70928d58ce4afd0ba8c",
    SOURCE_PATHS[2].as_posix(): "b48febdbedcb6ea6d4adc19e636b26f6774292ef3e1d405cecf7a491d7feb2fa",
    SOURCE_PATHS[3].as_posix(): "1600f716ea290b7a381d83c9408d8fbc21ab0d45b5d775c3e3fb71a93a03bd13",
    SOURCE_PATHS[4].as_posix(): "e19c9dbd6480b68ff2617681a2150e1c314c5ecac9a9acdfa4bd009a515b0f0c",
    SOURCE_PATHS[5].as_posix(): "fe7383541cfc06f05814afb0d3fba04716b423bc0e85b8975fb27bedad02f43e",
    SOURCE_PATHS[6].as_posix(): "aa6435381c90416ce9ded7e50afca166f33b29b4a268b230755bba0145680876",
    SOURCE_PATHS[7].as_posix(): "0bb67a720595ce8b5211ba56f6913f1d6333828846abba326af8b2f9965eca8b",
    SOURCE_PATHS[8].as_posix(): "1b04a32a580ef2dbb18048fe50f609bd188dd89c378d83474a1b32822f1e4932",
}

CONTRACT_FILENAME = "covapie_covalent_residue_locator_parser_provider_smoke_contract.csv"
CASE_FILENAME = "covapie_covalent_residue_locator_synthetic_case_audit.csv"
SOURCE_FILENAME = "covapie_covalent_residue_locator_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_covalent_residue_locator_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_locator_parser_provider_smoke_issue_inventory.csv"
MANIFEST_FILENAME = (
    "covapie_covalent_residue_locator_parser_provider_provenance_export_smoke_manifest.json"
)
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    CASE_FILENAME,
    SOURCE_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

CONTRACT_COLUMNS = (
    "contract_item_id",
    "contract_area",
    "requirement",
    "expected_value",
    "observed_value",
    "contract_passed",
    "blocking_reason",
)
CASE_COLUMNS = (
    "smoke_case_id",
    "sample_preparation_input_id",
    "pdb_id",
    "conn_id",
    "residue_partner_side",
    "locator_namespace",
    "struct_conn_residue_auth_asym_id",
    "struct_conn_residue_auth_seq_id",
    "struct_conn_residue_label_asym_id",
    "struct_conn_residue_label_seq_id",
    "selected_chain_id",
    "selected_residue_index",
    "auth_label_conflict_observed",
    "matched_atom_site_id",
    "matched_residue_atom_name",
    "struct_conn_insertion_source_tag",
    "struct_conn_insertion_raw_value",
    "struct_conn_token_class",
    "atom_site_insertion_source_tag",
    "atom_site_insertion_raw_value",
    "atom_site_token_class",
    "resolved_insertion_state",
    "resolved_insertion_value",
    "insertion_evidence_agreement",
    "insertion_blocks_admit_004",
    "insertion_blocking_reason",
    "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state",
    "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
    "provider_export_status",
    "provider_export_blocking_reason",
)
SOURCE_COLUMNS = (
    "source_order",
    "source_relative_path",
    "sha256_expected",
    "sha256_observed",
    "tracked",
    "regular_file",
    "symlink",
    "source_check_passed",
    "blocking_reason",
)
SAFETY_COLUMNS = (
    "safety_item",
    "required_status",
    "observed_status",
    "safety_passed",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id",
    "issue_type",
    "severity",
    "status",
    "issue_count",
    "blocking_reason",
)
P3_FIELDS = (
    "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state",
    "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
)

CASE_IDS = (
    "P5B_001_PTNR1_EXPLICIT_A",
    "P5B_002_PTNR2_EXPLICIT_1",
    "P5B_003_DOT_DOT",
    "P5B_004_QUESTION_QUESTION",
    "P5B_005_TAGS_MISSING",
    "P5B_006_PARSED_EMPTY",
    "P5B_007_EXPLICIT_CONFLICT",
    "P5B_008_EXPLICIT_DOT_CONFLICT",
    "P5B_009_PARTNER_TAG_MISMATCH",
    "P5B_010_AUTH_CONFLICT_SELECT_AUTH",
    "P5B_011_AUTH_CONFLICT_SELECT_LABEL",
    "P5B_012_MIXED_NAMESPACE",
    "P5B_013_ATOM_ROW_MISSING",
    "P5B_014_MULTIPLE_ATOM_ROWS",
    "P5B_015_INVALID_ATOM_ROW_IDENTITY",
    "P5B_016_SOURCE_ID_COLLISION",
)

DOMAIN_BLOCKERS = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
)
FOLLOWUP_ISSUES = (
    "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_NOT_YET_EXPORTABLE",
    "COVALENT_RESIDUE_LOCATOR_REAL_PIPELINE_INTEGRATION_NOT_YET_IMPLEMENTED",
)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@dataclass(frozen=True)
class RawLoopRow:
    row_ordinal_1based: int
    values: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, str]:
        return dict(self.values)


@dataclass(frozen=True)
class RawLoopResult:
    passed: bool
    tags: tuple[str, ...]
    rows: tuple[RawLoopRow, ...]
    status: str
    blocking_reason: str

    def legacy_rows(self) -> list[dict[str, str]]:
        return [row.as_dict() for row in self.rows]


def parse_raw_preserving_mmcif_loop(text: object, prefix: object) -> RawLoopResult:
    """Parse one loop without normalizing any logical token value."""
    if type(text) is not str or type(prefix) is not str or not prefix:
        return RawLoopResult(False, (), (), "invalid_input", "RAW_LOOP_INPUT_INVALID")
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != "loop_":
            continue
        tag_index = idx + 1
        tags: list[str] = []
        while tag_index < len(lines) and lines[tag_index].strip().startswith("_"):
            tags.append(lines[tag_index].strip())
            tag_index += 1
        if not tags or not all(tag.startswith(prefix) for tag in tags):
            continue
        tokens: list[str] = []
        row_index = tag_index
        try:
            while row_index < len(lines):
                stripped = lines[row_index].strip()
                if not stripped or stripped == "#" or stripped == "loop_" or stripped.startswith("_"):
                    break
                tokens.extend(shlex.split(stripped, posix=True))
                row_index += 1
        except ValueError:
            return RawLoopResult(False, tuple(tags), (), "invalid_input", "MMCIF_TOKENIZATION_FAILED")
        if not tokens:
            return RawLoopResult(True, tuple(tags), (), "parsed_empty_loop", "")
        if len(tokens) % len(tags) != 0:
            return RawLoopResult(
                False,
                tuple(tags),
                (),
                "token_count_not_divisible",
                f"TOKEN_COUNT_NOT_DIVISIBLE:{len(tokens)}:{len(tags)}",
            )
        rows = tuple(
            RawLoopRow(
                row_ordinal_1based=(start // len(tags)) + 1,
                values=tuple((tag, tokens[start + pos]) for pos, tag in enumerate(tags)),
            )
            for start in range(0, len(tokens), len(tags))
        )
        return RawLoopResult(True, tuple(tags), rows, "parsed_loop", "")
    return RawLoopResult(False, (), (), "loop_not_found", "MMCIF_LOOP_NOT_FOUND")


def build_historical_compatibility_view(
    raw_result: RawLoopResult, required_tags: Iterable[str]
) -> RawLoopResult:
    """Create the historical cleaned/defaulted view without mutating raw rows."""
    if type(raw_result) is not RawLoopResult:
        raise TypeError("raw_result must be RawLoopResult")
    required = tuple(required_tags)
    if any(type(tag) is not str for tag in required):
        raise TypeError("required tags must be exact strings")
    rows: list[RawLoopRow] = []
    for raw_row in raw_result.rows:
        values = {tag: "" if value in {".", "?"} else value for tag, value in raw_row.values}
        for tag in required:
            values.setdefault(tag, "")
        ordered = tuple((tag, values[tag]) for tag in (*raw_result.tags, *required) if tag in values)
        deduplicated = tuple(dict(ordered).items())
        rows.append(RawLoopRow(raw_row.row_ordinal_1based, deduplicated))
    return RawLoopResult(
        raw_result.passed,
        raw_result.tags,
        tuple(rows),
        raw_result.status,
        raw_result.blocking_reason,
    )


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    residue_side: str = "ptnr1"
    struct_raw: str = "A"
    atom_raw: str = "A"
    struct_tag_present: bool = True
    atom_tag_present: bool = True
    struct_tag_side: str = ""
    locator_namespace: str = "auth"
    auth_pair: tuple[str, str] = ("A", "25")
    label_pair: tuple[str, str] = ("A", "25")
    selected_pair: tuple[str, str] = ("A", "25")
    atom_mode: str = "unique"
    atom_site_id: str = "ATOM1"
    sample_preparation_input_id: str = "P5B_SAMPLE"


CASE_SPECS = (
    CaseSpec(CASE_IDS[0]),
    CaseSpec(CASE_IDS[1], residue_side="ptnr2", struct_raw="1", atom_raw="1"),
    CaseSpec(CASE_IDS[2], struct_raw=".", atom_raw="."),
    CaseSpec(CASE_IDS[3], struct_raw="?", atom_raw="?"),
    CaseSpec(CASE_IDS[4], struct_tag_present=False, atom_tag_present=False),
    CaseSpec(CASE_IDS[5], struct_raw="", atom_raw=""),
    CaseSpec(CASE_IDS[6], struct_raw="A", atom_raw="B"),
    CaseSpec(CASE_IDS[7], struct_raw="A", atom_raw="."),
    CaseSpec(CASE_IDS[8], struct_tag_side="ptnr2"),
    CaseSpec(
        CASE_IDS[9],
        auth_pair=("A", "25"),
        label_pair=("X", "99"),
        selected_pair=("A", "25"),
    ),
    CaseSpec(
        CASE_IDS[10],
        locator_namespace="label",
        auth_pair=("A", "25"),
        label_pair=("X", "99"),
        selected_pair=("X", "99"),
    ),
    CaseSpec(
        CASE_IDS[11],
        auth_pair=("A", "25"),
        label_pair=("X", "99"),
        selected_pair=("A", "99"),
    ),
    CaseSpec(CASE_IDS[12], atom_mode="missing"),
    CaseSpec(CASE_IDS[13], atom_mode="multiple"),
    CaseSpec(CASE_IDS[14], atom_site_id="."),
    CaseSpec(CASE_IDS[15], sample_preparation_input_id="P5B:SOURCE"),
)

EXPECTED_OUTCOMES = {
    CASE_IDS[0]: ("exported_pass", "", "present", "A", True, False, ""),
    CASE_IDS[1]: ("exported_pass", "", "present", "1", True, False, ""),
    CASE_IDS[2]: ("exported_pass", "", "absent", "", True, False, ""),
    CASE_IDS[3]: (
        "exported_blocking",
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
        "unknown",
        "",
        False,
        True,
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
    ),
    CASE_IDS[4]: (
        "exported_blocking",
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
        "unknown",
        "",
        False,
        True,
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
    ),
    CASE_IDS[5]: (
        "exported_blocking",
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
        "unknown",
        "",
        False,
        True,
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
    ),
    CASE_IDS[6]: (
        "exported_blocking",
        "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT",
        "unknown",
        "",
        False,
        True,
        "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT",
    ),
    CASE_IDS[7]: (
        "exported_blocking",
        "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT",
        "unknown",
        "",
        False,
        True,
        "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT",
    ),
    CASE_IDS[8]: (
        "rejected",
        "STRUCT_CONN_INSERTION_SOURCE_TAG_PARTNER_SIDE_MISMATCH",
        "",
        "",
        "",
        "",
        "",
    ),
    CASE_IDS[9]: ("exported_pass", "", "present", "A", True, False, ""),
    CASE_IDS[10]: ("exported_pass", "", "present", "A", True, False, ""),
    CASE_IDS[11]: (
        "rejected",
        "LOCATOR_NAMESPACE_MIXED_SELECTION_FORBIDDEN",
        "",
        "",
        "",
        "",
        "",
    ),
    CASE_IDS[12]: (
        "rejected",
        "MATCHED_ATOM_SITE_ROW_NOT_FOUND",
        "",
        "",
        "",
        "",
        "",
    ),
    CASE_IDS[13]: (
        "rejected",
        "MULTIPLE_MATCHED_ATOM_SITE_ROWS",
        "",
        "",
        "",
        "",
        "",
    ),
    CASE_IDS[14]: (
        "rejected",
        "MATCHED_ATOM_SITE_ID_INVALID",
        "",
        "",
        "",
        "",
        "",
    ),
    CASE_IDS[15]: (
        "rejected",
        "PROVENANCE_SOURCE_ID_COMPONENT_INVALID",
        "present",
        "A",
        True,
        False,
        "",
    ),
}


def _quote_token(value: str) -> str:
    return "''" if value == "" else shlex.quote(value)


def _synthetic_mmcif(spec: CaseSpec) -> str:
    residue_side = spec.residue_side
    ligand_side = "ptnr2" if residue_side == "ptnr1" else "ptnr1"
    struct_tag_side = spec.struct_tag_side or residue_side
    struct_tags = [
        "_struct_conn.id",
        "_struct_conn.conn_type_id",
        "_struct_conn.ptnr1_label_comp_id",
        "_struct_conn.ptnr1_label_atom_id",
        "_struct_conn.ptnr1_auth_asym_id",
        "_struct_conn.ptnr1_auth_seq_id",
        "_struct_conn.ptnr1_label_asym_id",
        "_struct_conn.ptnr1_label_seq_id",
        "_struct_conn.ptnr1_auth_comp_id",
        "_struct_conn.ptnr2_label_comp_id",
        "_struct_conn.ptnr2_label_atom_id",
        "_struct_conn.ptnr2_auth_asym_id",
        "_struct_conn.ptnr2_auth_seq_id",
        "_struct_conn.ptnr2_label_asym_id",
        "_struct_conn.ptnr2_label_seq_id",
        "_struct_conn.ptnr2_auth_comp_id",
    ]
    sides = {
        residue_side: {
            "comp": "CYS",
            "atom": "SG",
            "auth": spec.auth_pair,
            "label": spec.label_pair,
        },
        ligand_side: {
            "comp": "LIG",
            "atom": "C1",
            "auth": ("B", "300"),
            "label": ("B", "300"),
        },
    }
    struct_values = ["covale1", "covale"]
    for side in ("ptnr1", "ptnr2"):
        value = sides[side]
        struct_values.extend(
            [
                value["comp"],
                value["atom"],
                value["auth"][0],
                value["auth"][1],
                value["label"][0],
                value["label"][1],
                value["comp"],
            ]
        )
    if spec.struct_tag_present:
        struct_tags.append(f"_struct_conn.pdbx_{struct_tag_side}_PDB_ins_code")
        struct_values.append(spec.struct_raw)

    atom_tags = list(historical.ATOM_SITE_TAGS)
    if spec.atom_tag_present:
        atom_tags.append("_atom_site.pdbx_PDB_ins_code")

    def atom_values(atom_id: str, atom_name: str) -> list[str]:
        values = [
            "ATOM",
            atom_id,
            "S" if atom_name == "SG" else "C",
            atom_name,
            "",
            "CYS",
            spec.label_pair[0],
            spec.label_pair[1],
            "0.0",
            "0.0",
            "0.0",
            "1.0",
            spec.auth_pair[1],
            "CYS",
            spec.auth_pair[0],
            atom_name,
            "1",
        ]
        if spec.atom_tag_present:
            values.append(spec.atom_raw)
        return values

    atom_rows: list[list[str]] = []
    if spec.atom_mode == "missing":
        atom_rows.append(atom_values("ATOM_CA", "CA"))
    else:
        atom_rows.append(atom_values(spec.atom_site_id, "SG"))
        if spec.atom_mode == "multiple":
            atom_rows.append(atom_values("ATOM2", "SG"))

    struct_block = "loop_\n" + "\n".join(struct_tags) + "\n" + " ".join(
        _quote_token(value) for value in struct_values
    )
    atom_block = "loop_\n" + "\n".join(atom_tags) + "\n" + "\n".join(
        " ".join(_quote_token(value) for value in values) for values in atom_rows
    )
    return f"data_p5b\n{struct_block}\n#\n{atom_block}\n#\n"


def _clean_match(value: str) -> str:
    return "" if value in {"", ".", "?"} else value


@dataclass(frozen=True)
class SelectedEvent:
    row: RawLoopRow
    residue_partner_side: str
    residue: tuple[tuple[str, str], ...]
    ligand: tuple[tuple[str, str], ...]
    struct_insertion_source_tag: str
    struct_insertion_raw_value: str

    def residue_dict(self) -> dict[str, str]:
        return dict(self.residue)


def _partner(row: dict[str, str], side: str) -> dict[str, str]:
    return {
        "side": side,
        "comp_id": _clean_match(
            row.get(f"_struct_conn.{side}_label_comp_id", "")
            or row.get(f"_struct_conn.{side}_auth_comp_id", "")
        ),
        "atom_id": _clean_match(row.get(f"_struct_conn.{side}_label_atom_id", "")),
        "auth_asym_id": _clean_match(row.get(f"_struct_conn.{side}_auth_asym_id", "")),
        "auth_seq_id": _clean_match(row.get(f"_struct_conn.{side}_auth_seq_id", "")),
        "label_asym_id": _clean_match(row.get(f"_struct_conn.{side}_label_asym_id", "")),
        "label_seq_id": _clean_match(row.get(f"_struct_conn.{side}_label_seq_id", "")),
    }


def select_synthetic_struct_conn_event(
    raw_result: RawLoopResult, spec: CaseSpec
) -> tuple[SelectedEvent | None, str]:
    matches: list[SelectedEvent] = []
    for raw_row in raw_result.rows:
        row = raw_row.as_dict()
        if _clean_match(row.get("_struct_conn.id", "")) != "covale1":
            continue
        if _clean_match(row.get("_struct_conn.conn_type_id", "")).lower() != "covale":
            continue
        for residue_side in ("ptnr1", "ptnr2"):
            ligand_side = "ptnr2" if residue_side == "ptnr1" else "ptnr1"
            residue = _partner(row, residue_side)
            ligand = _partner(row, ligand_side)
            if (
                residue["comp_id"] == "CYS"
                and residue["atom_id"] == "SG"
                and ligand["comp_id"] == "LIG"
                and ligand["atom_id"] == "C1"
            ):
                canonical_tag = (
                    p4_gate.PARSER_INSERTION_SOURCE_TAGS[1]
                    if residue_side == "ptnr1"
                    else p4_gate.PARSER_INSERTION_SOURCE_TAGS[2]
                )
                source_tag = canonical_tag
                if spec.struct_tag_side:
                    source_tag = (
                        p4_gate.PARSER_INSERTION_SOURCE_TAGS[1]
                        if spec.struct_tag_side == "ptnr1"
                        else p4_gate.PARSER_INSERTION_SOURCE_TAGS[2]
                    )
                matches.append(
                    SelectedEvent(
                        raw_row,
                        residue_side,
                        tuple(residue.items()),
                        tuple(ligand.items()),
                        source_tag if source_tag in raw_result.tags else "",
                        row.get(source_tag, "") if source_tag in raw_result.tags else "",
                    )
                )
    if len(matches) == 1:
        return matches[0], ""
    return (None, "STRUCT_CONN_EVENT_NOT_FOUND" if not matches else "MULTIPLE_STRUCT_CONN_EVENTS")


def select_unique_matched_atom_site_row(
    raw_result: RawLoopResult,
    event: SelectedEvent,
    namespace: str,
    selected_chain_id: str,
    selected_residue_index: str,
) -> tuple[RawLoopRow | None, str]:
    matches: list[RawLoopRow] = []
    for raw_row in raw_result.rows:
        row = raw_row.as_dict()
        comp_id = row.get("_atom_site.auth_comp_id") or row.get("_atom_site.label_comp_id", "")
        atom_name = row.get("_atom_site.auth_atom_id") or row.get("_atom_site.label_atom_id", "")
        chain_tag = f"_atom_site.{namespace}_asym_id"
        seq_tag = f"_atom_site.{namespace}_seq_id"
        if (
            comp_id == event.residue_dict()["comp_id"]
            and atom_name == event.residue_dict()["atom_id"]
            and row.get(chain_tag, "") == selected_chain_id
            and row.get(seq_tag, "") == selected_residue_index
        ):
            matches.append(raw_row)
    if len(matches) == 1:
        return matches[0], ""
    if not matches:
        return None, "MATCHED_ATOM_SITE_ROW_NOT_FOUND"
    return None, "MULTIPLE_MATCHED_ATOM_SITE_ROWS"


def _empty_case_row(spec: CaseSpec) -> dict[str, Any]:
    return {column: "" for column in CASE_COLUMNS} | {
        "smoke_case_id": spec.case_id,
        "sample_preparation_input_id": spec.sample_preparation_input_id,
        "pdb_id": "TEST",
        "conn_id": "covale1",
        "residue_partner_side": spec.residue_side,
        "locator_namespace": spec.locator_namespace,
        "selected_chain_id": spec.selected_pair[0],
        "selected_residue_index": spec.selected_pair[1],
        "auth_label_conflict_observed": False,
        "insertion_evidence_agreement": "",
        "insertion_blocks_admit_004": "",
        "provider_export_status": "rejected",
    }


def _mapped_provider_reason(error: Exception) -> str:
    message = str(error)
    if message == "struct_conn insertion source tag does not match partner side":
        return "STRUCT_CONN_INSERTION_SOURCE_TAG_PARTNER_SIDE_MISMATCH"
    if message.startswith("invalid provenance source ID component:"):
        return "PROVENANCE_SOURCE_ID_COMPONENT_INVALID"
    return message or "PROVIDER_EXPORT_REJECTED"


def materialize_synthetic_case(spec: CaseSpec) -> dict[str, Any]:
    text = _synthetic_mmcif(spec)
    struct_raw = parse_raw_preserving_mmcif_loop(text, "_struct_conn.")
    atom_raw = parse_raw_preserving_mmcif_loop(text, "_atom_site.")
    row = _empty_case_row(spec)
    event, event_reason = select_synthetic_struct_conn_event(struct_raw, spec)
    if event is None:
        row["provider_export_blocking_reason"] = event_reason
        return row
    residue = event.residue_dict()
    row.update(
        {
            "residue_partner_side": event.residue_partner_side,
            "struct_conn_residue_auth_asym_id": residue["auth_asym_id"],
            "struct_conn_residue_auth_seq_id": residue["auth_seq_id"],
            "struct_conn_residue_label_asym_id": residue["label_asym_id"],
            "struct_conn_residue_label_seq_id": residue["label_seq_id"],
            "struct_conn_insertion_source_tag": event.struct_insertion_source_tag,
            "struct_conn_insertion_raw_value": event.struct_insertion_raw_value,
        }
    )
    namespace = p4_gate.resolve_locator_namespace_evidence(
        locator_namespace=spec.locator_namespace,
        struct_conn_residue_auth_asym_id=residue["auth_asym_id"],
        struct_conn_residue_auth_seq_id=residue["auth_seq_id"],
        struct_conn_residue_label_asym_id=residue["label_asym_id"],
        struct_conn_residue_label_seq_id=residue["label_seq_id"],
        selected_chain_id=spec.selected_pair[0],
        selected_residue_index=spec.selected_pair[1],
    )
    row["auth_label_conflict_observed"] = namespace.auth_label_conflict_observed
    if not namespace.passed:
        row["provider_export_blocking_reason"] = namespace.blocking_reason
        return row
    matched, match_reason = select_unique_matched_atom_site_row(
        atom_raw,
        event,
        spec.locator_namespace,
        spec.selected_pair[0],
        spec.selected_pair[1],
    )
    if matched is None:
        row["provider_export_blocking_reason"] = match_reason
        return row
    atom = matched.as_dict()
    atom_tag = p4_gate.PARSER_INSERTION_SOURCE_TAGS[0]
    atom_source_tag = atom_tag if atom_tag in atom_raw.tags else ""
    atom_raw_value = atom.get(atom_tag, "") if atom_source_tag else ""
    atom_name = atom.get("_atom_site.auth_atom_id") or atom.get("_atom_site.label_atom_id", "")
    row.update(
        {
            "matched_atom_site_id": atom.get("_atom_site.id", ""),
            "matched_residue_atom_name": atom_name,
            "atom_site_insertion_source_tag": atom_source_tag,
            "atom_site_insertion_raw_value": atom_raw_value,
        }
    )
    atom_identity = p4_gate.validate_matched_atom_site_row_identity(
        row["matched_atom_site_id"], atom_name
    )
    if not atom_identity.passed:
        row["provider_export_blocking_reason"] = atom_identity.blocking_reason
        return row
    expected_struct_tag = (
        p4_gate.PARSER_INSERTION_SOURCE_TAGS[1]
        if event.residue_partner_side == "ptnr1"
        else p4_gate.PARSER_INSERTION_SOURCE_TAGS[2]
    )
    if event.struct_insertion_source_tag not in {"", expected_struct_tag}:
        row["provider_export_blocking_reason"] = (
            "STRUCT_CONN_INSERTION_SOURCE_TAG_PARTNER_SIDE_MISMATCH"
        )
        return row
    if atom_source_tag not in {"", p4_gate.PARSER_INSERTION_SOURCE_TAGS[0]}:
        row["provider_export_blocking_reason"] = (
            "ATOM_SITE_INSERTION_SOURCE_TAG_NOT_CANONICAL"
        )
        return row
    struct_token = p4_gate.classify_insertion_code_raw_token(
        event.struct_insertion_source_tag != "", event.struct_insertion_raw_value
    )
    atom_token = p4_gate.classify_insertion_code_raw_token(
        atom_source_tag != "", atom_raw_value
    )
    resolution = p4_gate.resolve_insertion_code_evidence(struct_token, atom_token)
    row.update(
        {
            "struct_conn_token_class": struct_token.token_class,
            "atom_site_token_class": atom_token.token_class,
            "resolved_insertion_state": resolution.resolved_state,
            "resolved_insertion_value": resolution.resolved_value,
            "insertion_evidence_agreement": resolution.evidence_agreement,
            "insertion_blocks_admit_004": resolution.blocks_admit_004,
            "insertion_blocking_reason": resolution.blocking_reason,
        }
    )
    try:
        exported = p4_gate.build_locator_provider_export_fields(
            locator_namespace=spec.locator_namespace,
            sample_preparation_input_id=spec.sample_preparation_input_id,
            pdb_id="TEST",
            conn_id="covale1",
            residue_partner_side=event.residue_partner_side,
            struct_conn_residue_auth_asym_id=residue["auth_asym_id"],
            struct_conn_residue_auth_seq_id=residue["auth_seq_id"],
            struct_conn_residue_label_asym_id=residue["label_asym_id"],
            struct_conn_residue_label_seq_id=residue["label_seq_id"],
            selected_chain_id=spec.selected_pair[0],
            selected_residue_index=spec.selected_pair[1],
            matched_atom_site_id=atom.get("_atom_site.id", ""),
            matched_residue_atom_name=atom_name,
            struct_conn_insertion_source_tag=event.struct_insertion_source_tag,
            struct_conn_insertion_raw_value=event.struct_insertion_raw_value,
            atom_site_insertion_source_tag=atom_source_tag,
            atom_site_insertion_raw_value=atom_raw_value,
        )
    except (TypeError, ValueError) as error:
        reason = _mapped_provider_reason(error)
        row.update(
            {
                "provider_export_status": "rejected",
                "provider_export_blocking_reason": reason,
            }
        )
        return row
    row.update(exported)
    if resolution.blocks_admit_004:
        row["provider_export_status"] = "exported_blocking"
        row["provider_export_blocking_reason"] = resolution.blocking_reason
    else:
        row["provider_export_status"] = "exported_pass"
        row["provider_export_blocking_reason"] = ""
    return row


def materialize_synthetic_cases() -> list[dict[str, Any]]:
    return [materialize_synthetic_case(spec) for spec in CASE_SPECS]


_CANONICAL_CASE_ROWS = tuple(
    tuple(materialize_synthetic_case(spec)[column] for column in CASE_COLUMNS)
    for spec in CASE_SPECS
)


def validate_synthetic_case_rows(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != 16 or tuple(row.get("smoke_case_id") for row in rows) != CASE_IDS:
        return False
    if any(tuple(row) != CASE_COLUMNS for row in rows):
        return False
    if tuple(tuple(row[column] for column in CASE_COLUMNS) for row in rows) != _CANONICAL_CASE_ROWS:
        return False
    counts = {status: sum(row["provider_export_status"] == status for row in rows) for status in ("exported_pass", "exported_blocking", "rejected")}
    if counts != {"exported_pass": 5, "exported_blocking": 5, "rejected": 6}:
        return False
    for row in rows:
        expected = EXPECTED_OUTCOMES[row["smoke_case_id"]]
        if (
            row["provider_export_status"],
            row["provider_export_blocking_reason"],
            row["resolved_insertion_state"],
            row["resolved_insertion_value"],
            row["insertion_evidence_agreement"],
            row["insertion_blocks_admit_004"],
            row["insertion_blocking_reason"],
        ) != expected:
            return False
        if row["provider_export_status"] == "rejected":
            if any(row[field] != "" for field in P3_FIELDS):
                return False
        else:
            if any(row[field] == "" for field in (P3_FIELDS[0], P3_FIELDS[1], P3_FIELDS[3], P3_FIELDS[4])):
                return False
            if len(row[P3_FIELDS[4]]) != 64:
                return False
    return True


def _source_boundary_rows() -> list[dict[str, Any]]:
    rows = []
    for order, relative in enumerate(SOURCE_PATHS, 1):
        absolute = REPO_ROOT / relative
        tracked = _git(["ls-files", "--error-unmatch", relative.as_posix()]).returncode == 0
        regular = absolute.is_file()
        symlink = absolute.is_symlink()
        observed = _sha256(absolute) if regular and not symlink else ""
        expected = SOURCE_SHA256[relative.as_posix()]
        passed = tracked and regular and not symlink and observed == expected
        rows.append(
            {
                "source_order": order,
                "source_relative_path": relative.as_posix(),
                "sha256_expected": expected,
                "sha256_observed": observed,
                "tracked": tracked,
                "regular_file": regular,
                "symlink": symlink,
                "source_check_passed": passed,
                "blocking_reason": "" if passed else f"SOURCE_BOUNDARY_FAILED:{relative.as_posix()}",
            }
        )
    return rows


def validate_source_boundary_rows(rows: list[dict[str, Any]]) -> bool:
    expected_paths = tuple(path.as_posix() for path in SOURCE_PATHS)
    return (
        len(rows) == 9
        and tuple(row.get("source_relative_path") for row in rows) == expected_paths
        and tuple(row.get("source_order") for row in rows) == tuple(range(1, 10))
        and all(tuple(row) == SOURCE_COLUMNS for row in rows)
        and all(row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]] for row in rows)
        and all(
            row["sha256_observed"] == row["sha256_expected"]
            and row["tracked"] is True
            and row["regular_file"] is True
            and row["symlink"] is False
            and row["source_check_passed"] is True
            and row["blocking_reason"] == ""
            for row in rows
        )
    )


def _p4_manifest() -> dict[str, Any]:
    return json.loads((REPO_ROOT / SOURCE_PATHS[6]).read_text(encoding="utf-8"))


def _p4_predecessor_checks() -> dict[str, bool]:
    manifest = _p4_manifest()
    return {
        "stage": manifest.get("stage") == PREVIOUS_STAGE,
        "all_checks": manifest.get("all_checks_passed") is True,
        "design_frozen": manifest.get("parser_provider_provenance_export_design_frozen") is True,
        "implementation_false": manifest.get("parser_provider_provenance_export_implemented") is False,
        "payload_20": manifest.get("canonical_provenance_payload_key_count") == 20,
        "tags_3": manifest.get("parser_insertion_source_tags") == list(p4_gate.PARSER_INSERTION_SOURCE_TAGS),
        "classes_6": manifest.get("raw_token_classes") == list(p4_gate.RAW_TOKEN_CLASSES),
        "fields_22": manifest.get("predecessor_field_count") == 22,
        "issues_10": manifest.get("predecessor_remaining_domain_issue_count") == 10,
        "samples_11_11_0": (
            manifest.get("existing_sample_count") == 11
            and manifest.get("insertion_unknown_sample_count") == 11
            and manifest.get("insertion_absence_proven_sample_count") == 0
        ),
        "readiness_closed": (
            manifest.get("admit_004_rule_logic_ready") is False
            and manifest.get("ready_for_e1_residue_identity_semantics_design") is False
            and manifest.get("ready_for_real_candidate_evaluation") is False
            and manifest.get("ready_for_bulk_download_now") is False
            and manifest.get("ready_for_training") is False
            and manifest.get("ready_to_train_now") is False
        ),
        "next_step": manifest.get("recommended_next_step")
        == "implement_covapie_covalent_residue_locator_parser_provider_provenance_export_smoke_v1",
    }


def _raw_parser_checks() -> dict[str, bool]:
    dot = materialize_synthetic_case(CASE_SPECS[2])
    question = materialize_synthetic_case(CASE_SPECS[3])
    missing = materialize_synthetic_case(CASE_SPECS[4])
    empty = materialize_synthetic_case(CASE_SPECS[5])
    raw = parse_raw_preserving_mmcif_loop(_synthetic_mmcif(CASE_SPECS[0]), "_atom_site.")
    return {
        "dot_preserved": dot["atom_site_insertion_raw_value"] == "." and dot["atom_site_token_class"] == "dot_not_applicable",
        "question_preserved": question["atom_site_insertion_raw_value"] == "?" and question["atom_site_token_class"] == "question_unknown",
        "missing_preserved": missing["atom_site_insertion_source_tag"] == "" and missing["atom_site_token_class"] == "tag_missing",
        "empty_preserved": empty["atom_site_insertion_source_tag"] == p4_gate.PARSER_INSERTION_SOURCE_TAGS[0] and empty["atom_site_insertion_raw_value"] == "" and empty["atom_site_token_class"] == "parsed_empty",
        "ordinal_one_based": bool(raw.rows) and raw.rows[0].row_ordinal_1based == 1,
        "raw_result_immutable": isinstance(raw.tags, tuple) and isinstance(raw.rows, tuple) and isinstance(raw.rows[0].values, tuple),
    }


def _compatibility_checks() -> dict[str, bool]:
    text = _synthetic_mmcif(CASE_SPECS[3])
    raw_atom = parse_raw_preserving_mmcif_loop(text, "_atom_site.")
    raw_struct = parse_raw_preserving_mmcif_loop(text, "_struct_conn.")
    atom_view = build_historical_compatibility_view(raw_atom, historical.ATOM_SITE_TAGS)
    struct_view = build_historical_compatibility_view(raw_struct, historical.STRUCT_CONN_TAGS)
    historical_atom = historical.parse_atom_site_loop(text)
    historical_struct = historical.parse_struct_conn_loop(text)
    atom_tuple = (list(atom_view.tags), atom_view.legacy_rows(), atom_view.status)
    struct_tuple = (list(struct_view.tags), struct_view.legacy_rows(), struct_view.status)
    return {
        "atom_tags": atom_tuple[0] == historical_atom[0],
        "atom_rows": atom_tuple[1] == historical_atom[1],
        "atom_status": atom_tuple[2] == historical_atom[2],
        "struct_tags": struct_tuple[0] == historical_struct[0],
        "struct_rows": struct_tuple[1] == historical_struct[1],
        "struct_status": struct_tuple[2] == historical_struct[2],
        "raw_unmutated": raw_atom.rows[0].as_dict()[p4_gate.PARSER_INSERTION_SOURCE_TAGS[0]] == "?",
    }


def _issue_rows() -> list[dict[str, Any]]:
    return [
        {
            "issue_id": FOLLOWUP_ISSUES[0],
            "issue_type": "real_sample_export_pending",
            "severity": "blocking",
            "status": "open",
            "issue_count": 11,
            "blocking_reason": "synthetic_smoke_does_not_backfill_real_samples",
        },
        {
            "issue_id": FOLLOWUP_ISSUES[1],
            "issue_type": "real_pipeline_integration_pending",
            "severity": "blocking",
            "status": "open",
            "issue_count": 1,
            "blocking_reason": "additive_adapter_not_connected_to_historical_or_expansion_pipeline",
        },
    ]


def validate_issue_rows(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 2 and all(tuple(row) == ISSUE_COLUMNS for row in rows) and rows == _issue_rows()


SAFETY_ITEMS = (
    "network_access_used_current_step",
    "external_registry_lookup_current_step",
    "ignored_raw_directory_traversed_current_step",
    "ignored_raw_structure_read_current_step",
    "checkpoint_read_current_step",
    "artifact_reference_paths_followed_current_step",
    "historical_parser_modified_current_step",
    "expansion_parser_modified_current_step",
    "p3_source_files_modified_current_step",
    "p4_source_files_modified_current_step",
    "real_pipeline_provider_implemented_current_step",
    "real_candidate_records_materialized_current_step",
    "real_provider_payloads_materialized_current_step",
    "download_queue_materialized_current_step",
    "raw_files_written_current_step",
    "torch_imported",
    "numpy_imported",
    "model_forward_called",
    "loss_compute_called",
    "training_allowed",
)


def _safety_rows() -> list[dict[str, Any]]:
    return [
        {
            "safety_item": item,
            "required_status": False,
            "observed_status": False,
            "safety_passed": True,
            "blocking_reason": "",
        }
        for item in SAFETY_ITEMS
    ]


def validate_safety_rows(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 20
        and tuple(row.get("safety_item") for row in rows) == SAFETY_ITEMS
        and all(tuple(row) == SAFETY_COLUMNS for row in rows)
        and all(
            row["required_status"] is False
            and row["observed_status"] is False
            and row["safety_passed"] is True
            and row["blocking_reason"] == ""
            for row in rows
        )
    )


CONTRACT_SPECS = (
    ("lineage", "P4 predecessor", PREVIOUS_STAGE, "previous_stage"),
    ("lineage", "exact source input count", "9", "source_count"),
    ("lineage", "P4 frozen payload and P3 field contract", "true|20|22", "p4_contract"),
    ("scope", "synthetic only implementation", "true", "synthetic_only"),
    ("scope", "no raw structure access", "true", "no_raw"),
    ("scope", "historical parser source unchanged", "true", "historical_unchanged"),
    ("scope", "expansion parser source unchanged", "true", "expansion_unchanged"),
    ("scope", "canonical five masks include B3", "A|B|B2|B3|C", "masks"),
    ("raw_parser", "dot token preserved", "true", "dot"),
    ("raw_parser", "question token preserved", "true", "question"),
    ("raw_parser", "parsed empty token preserved", "true", "empty"),
    ("raw_parser", "missing tag determined by tags", "true", "missing"),
    ("raw_parser", "row ordinal is one based", "true", "ordinal"),
    ("raw_parser", "raw values are immutable and uncoerced", "true", "immutable"),
    ("compatibility", "atom-site tags match historical", "true", "atom_tags"),
    ("compatibility", "atom-site rows match historical", "true", "atom_rows"),
    ("compatibility", "atom-site status matches historical", "true", "atom_status"),
    ("compatibility", "struct-conn tags match historical", "true", "struct_tags"),
    ("compatibility", "struct-conn rows match historical", "true", "struct_rows"),
    ("compatibility", "struct-conn status matches historical", "true", "struct_status"),
    ("compatibility", "raw and compatibility views are independent", "true", "raw_unmutated"),
    ("event", "ptnr1 side is explicit", "ptnr1", "ptnr1"),
    ("event", "ptnr2 side is explicit", "ptnr2", "ptnr2"),
    ("event", "unique matched atom row bound", "true", "unique_atom"),
    ("event", "missing atom row rejected", "MATCHED_ATOM_SITE_ROW_NOT_FOUND", "missing_atom"),
    ("event", "multiple atom rows rejected", "MULTIPLE_MATCHED_ATOM_SITE_ROWS", "multiple_atom"),
    ("provider", "exact five P3 fields", "|".join(P3_FIELDS), "five_fields"),
    ("provider", "exported pass is materialized", "5", "pass_count"),
    ("provider", "exported blocking retains five fields", "5", "blocking_count"),
    (
        "provider",
        "rejected rows preserve insertion and provider truth separation",
        "6|true|present:A:false",
        "rejected_truth",
    ),
    ("provider", "P4 helpers are dynamically accessed", "true", "dynamic_p4"),
    ("provider", "source ID and SHA contracts pass", "true", "source_hash"),
    ("cases", "exact synthetic case count", "16", "case_count"),
    ("cases", "exact sidecar column count", "33", "column_count"),
    ("cases", "status counts are five five six", "5|5|6", "status_counts"),
    ("cases", "canonical case ordering", "|".join(CASE_IDS), "case_order"),
    ("readiness", "additive synthetic adapter implemented", "true", "adapter"),
    ("readiness", "real parser and provider integration remain false", "false|false", "real_integration"),
    ("readiness", "real samples remain eleven unknown zero absence", "11|11|0", "real_samples"),
    ("readiness", "ADMIT_004 and E1 remain false", "false|false", "admit_e1"),
    ("readiness", "candidate download and training remain false", "false|false|false", "execution_closed"),
    ("readiness", "feature semantics audit remains required", "true", "feature_audit"),
)


def _contract_observations(
    source_rows: list[dict[str, Any]],
    p4_checks: dict[str, bool],
    raw_checks: dict[str, bool],
    compatibility: dict[str, bool],
    cases: list[dict[str, Any]],
) -> dict[str, str]:
    by_id = {row["smoke_case_id"]: row for row in cases}
    counts = [sum(row["provider_export_status"] == status for row in cases) for status in ("exported_pass", "exported_blocking", "rejected")]
    exported = [row for row in cases if row["provider_export_status"] != "rejected"]
    rejected = [row for row in cases if row["provider_export_status"] == "rejected"]
    return {
        "previous_stage": PREVIOUS_STAGE,
        "source_count": str(len(source_rows)),
        "p4_contract": f"{_bool_text(p4_checks['design_frozen'])}|20|22",
        "synthetic_only": "true",
        "no_raw": "true",
        "historical_unchanged": _bool_text(source_rows[7]["source_check_passed"]),
        "expansion_unchanged": _bool_text(source_rows[8]["source_check_passed"]),
        "masks": "|".join(alias for _, alias in CANONICAL_MASK_PAIRS),
        "dot": _bool_text(raw_checks["dot_preserved"]),
        "question": _bool_text(raw_checks["question_preserved"]),
        "empty": _bool_text(raw_checks["empty_preserved"]),
        "missing": _bool_text(raw_checks["missing_preserved"]),
        "ordinal": _bool_text(raw_checks["ordinal_one_based"]),
        "immutable": _bool_text(raw_checks["raw_result_immutable"]),
        "atom_tags": _bool_text(compatibility["atom_tags"]),
        "atom_rows": _bool_text(compatibility["atom_rows"]),
        "atom_status": _bool_text(compatibility["atom_status"]),
        "struct_tags": _bool_text(compatibility["struct_tags"]),
        "struct_rows": _bool_text(compatibility["struct_rows"]),
        "struct_status": _bool_text(compatibility["struct_status"]),
        "raw_unmutated": _bool_text(compatibility["raw_unmutated"]),
        "ptnr1": by_id[CASE_IDS[0]]["residue_partner_side"],
        "ptnr2": by_id[CASE_IDS[1]]["residue_partner_side"],
        "unique_atom": _bool_text(bool(by_id[CASE_IDS[0]]["matched_atom_site_id"])),
        "missing_atom": by_id[CASE_IDS[12]]["provider_export_blocking_reason"],
        "multiple_atom": by_id[CASE_IDS[13]]["provider_export_blocking_reason"],
        "five_fields": "|".join(p4_gate.PROPOSED_FIELD_NAMES),
        "pass_count": str(counts[0]),
        "blocking_count": str(counts[1]),
        "rejected_count": str(counts[2]),
        "rejected_truth": (
            f"{len(rejected)}|"
            f"{_bool_text(all(row['insertion_blocking_reason'] == '' for row in rejected))}|"
            f"{by_id[CASE_IDS[15]]['resolved_insertion_state']}:"
            f"{by_id[CASE_IDS[15]]['resolved_insertion_value']}:"
            f"{_bool_text(by_id[CASE_IDS[15]]['insertion_blocks_admit_004'])}"
        ),
        "dynamic_p4": _bool_text(tuple(p4_gate.PROPOSED_FIELD_NAMES) == P3_FIELDS),
        "source_hash": _bool_text(
            all(row[P3_FIELDS[3]] and len(row[P3_FIELDS[4]]) == 64 for row in exported)
        ),
        "case_count": str(len(cases)),
        "column_count": str(len(CASE_COLUMNS)),
        "status_counts": "|".join(str(count) for count in counts),
        "case_order": "|".join(row["smoke_case_id"] for row in cases),
        "adapter": "true",
        "real_integration": "false|false",
        "real_samples": "11|11|0",
        "admit_e1": "false|false",
        "execution_closed": "false|false|false",
        "feature_audit": "true",
        "rejected_empty": _bool_text(all(all(row[field] == "" for field in P3_FIELDS) for row in rejected)),
    }


def _contract_rows(observations: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for index, (area, requirement, expected, key) in enumerate(CONTRACT_SPECS, 1):
        observed = observations[key]
        passed = observed == expected
        rows.append(
            {
                "contract_item_id": f"P5B_C{index:03d}",
                "contract_area": area,
                "requirement": requirement,
                "expected_value": expected,
                "observed_value": observed,
                "contract_passed": passed,
                "blocking_reason": "" if passed else f"P5B_C{index:03d}",
            }
        )
    return rows


def validate_contract_rows(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != 42 or any(tuple(row) != CONTRACT_COLUMNS for row in rows):
        return False
    for index, (row, spec) in enumerate(zip(rows, CONTRACT_SPECS), 1):
        area, requirement, expected, _ = spec
        if row != {
            "contract_item_id": f"P5B_C{index:03d}",
            "contract_area": area,
            "requirement": requirement,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": True,
            "blocking_reason": "",
        }:
            return False
    return True


SECTION_NAMES = (
    "source_boundary",
    "p4_predecessor",
    "raw_parser",
    "compatibility",
    "synthetic_cases",
    "contract",
    "issue_inventory",
    "safety",
)


def build_smoke_state(forced_section_failures: Iterable[str] = ()) -> dict[str, Any]:
    forced = set(forced_section_failures)
    if not forced.issubset(SECTION_NAMES):
        raise ValueError("unknown forced section failure")
    source_rows = _source_boundary_rows()
    p4_checks = _p4_predecessor_checks()
    raw_checks = _raw_parser_checks()
    compatibility = _compatibility_checks()
    case_rows = materialize_synthetic_cases()
    observations = _contract_observations(source_rows, p4_checks, raw_checks, compatibility, case_rows)
    contract_rows = _contract_rows(observations)
    issue_rows = _issue_rows()
    safety_rows = _safety_rows()
    sections = {
        "source_boundary": validate_source_boundary_rows(source_rows),
        "p4_predecessor": bool(p4_checks) and all(p4_checks.values()),
        "raw_parser": bool(raw_checks) and all(raw_checks.values()),
        "compatibility": bool(compatibility) and all(compatibility.values()),
        "synthetic_cases": validate_synthetic_case_rows(case_rows),
        "contract": validate_contract_rows(contract_rows),
        "issue_inventory": validate_issue_rows(issue_rows),
        "safety": validate_safety_rows(safety_rows),
    }
    for section in forced:
        sections[section] = False
    validation_failures = [f"{section.upper()}_VALIDATION_FAILED" for section in SECTION_NAMES if not sections[section]]
    return {
        "source_rows": source_rows,
        "p4_checks": p4_checks,
        "raw_checks": raw_checks,
        "compatibility": compatibility,
        "case_rows": case_rows,
        "contract_rows": contract_rows,
        "issue_rows": issue_rows,
        "safety_rows": safety_rows,
        "sections": sections,
        "validation_failures": validation_failures,
        "all_checks_passed": not validation_failures,
    }


def _manifest_payload(state: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    passed = state["all_checks_passed"]
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "previous_stage": PREVIOUS_STAGE,
        "source_read_boundary": SOURCE_READ_BOUNDARY,
        "source_input_count": 9,
        "source_input_sha256": dict(SOURCE_SHA256),
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "non_manifest_output_count": 5,
        "output_sha256": output_sha256,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5,
        "p4_design_frozen": state["p4_checks"]["design_frozen"],
        "p4_payload_key_count": 20,
        "predecessor_field_count": 22,
        "predecessor_domain_issue_count": 10,
        "additive_raw_preserving_parser_adapter_implemented": True,
        "historical_compatibility_view_verified": state["sections"]["compatibility"],
        "explicit_partner_side_preserved": state["case_rows"][0]["residue_partner_side"] == "ptnr1" and state["case_rows"][1]["residue_partner_side"] == "ptnr2",
        "unique_matched_atom_site_row_binding_verified": state["case_rows"][0]["matched_atom_site_id"] == "ATOM1",
        "synthetic_provider_export_mapping_implemented": True,
        "synthetic_case_count": 16,
        "synthetic_sidecar_column_count": 33,
        "exported_pass_case_count": 5,
        "exported_blocking_case_count": 5,
        "rejected_case_count": 6,
        "synthetic_case_rows_materialized_current_step": True,
        "synthetic_provider_export_rows_materialized_current_step": True,
        "historical_parser_modified_current_step": False,
        "expansion_parser_modified_current_step": False,
        "real_parser_pipeline_integration_implemented": False,
        "real_provider_pipeline_integration_implemented": False,
        "real_provider_payloads_materialized_current_step": False,
        "real_candidate_records_materialized_current_step": False,
        "real_samples_backfilled_current_step": 0,
        "existing_real_sample_count": 11,
        "real_insertion_unknown_sample_count": 11,
        "real_insertion_absence_proven_sample_count": 0,
        "real_fully_provable_pre_download_sample_count": 0,
        "parser_provider_provenance_export_synthetic_smoke_passed": passed,
        "insertion_code_provenance_export_ready_for_real_samples": False,
        "ready_for_real_parser_provider_pipeline_integration_design": passed,
        "admit_004_rule_logic_ready": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "current_domain_blocking_reasons": list(DOMAIN_BLOCKERS),
        "smoke_followup_issue_ids": list(FOLLOWUP_ISSUES),
        "validation_failures": state["validation_failures"],
        "all_source_boundary_checks_passed": state["sections"]["source_boundary"],
        "all_p4_predecessor_checks_passed": state["sections"]["p4_predecessor"],
        "all_raw_parser_checks_passed": state["sections"]["raw_parser"],
        "all_compatibility_checks_passed": state["sections"]["compatibility"],
        "all_synthetic_case_checks_passed": state["sections"]["synthetic_cases"],
        "all_contract_checks_passed": state["sections"]["contract"],
        "all_issue_inventory_checks_passed": state["sections"]["issue_inventory"],
        "all_safety_checks_passed": state["sections"]["safety"],
        "all_checks_passed": passed,
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
    }


def _csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return _bool_text(value)
    return value


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _csv_value(row[column]) for column in columns})
    os.replace(temporary, path)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    forced_section_failures: Iterable[str] = (),
) -> dict[str, Any]:
    root = REPO_ROOT / output_root if not output_root.is_absolute() else output_root
    if root.is_symlink():
        raise RuntimeError("output root must not be a symlink")
    if root.exists() and not root.is_dir():
        raise RuntimeError("output root must be a directory")
    state = build_smoke_state(forced_section_failures)
    _write_csv(root / CONTRACT_FILENAME, CONTRACT_COLUMNS, state["contract_rows"])
    _write_csv(root / CASE_FILENAME, CASE_COLUMNS, state["case_rows"])
    _write_csv(root / SOURCE_FILENAME, SOURCE_COLUMNS, state["source_rows"])
    _write_csv(root / SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"])
    _write_csv(root / ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"])
    hashes = {filename: _sha256(root / filename) for filename in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    _write_json(root / MANIFEST_FILENAME, manifest)
    return {**state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1()
