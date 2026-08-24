"""Extract source-ordered ligand atom identities from gzip-compressed mmCIF.

The caller supplies in-memory gzip bytes and the exact ligand instance to
select.  This module does not access the filesystem, resolve chemistry roles,
filter hydrogens, or mutate external state.
"""

from __future__ import annotations

import gzip
from io import StringIO
from typing import NoReturn

from Bio.PDB.MMCIF2Dict import MMCIF2Dict


__all__ = (
    "CovapieMMCIFLigandAtomIdentityExtractorError",
    "extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1",
)


_ERROR = "COVAPIE_MMCIF_LIGAND_ATOM_IDENTITY_EXTRACTOR_V1_ERROR"
_REQUIRED_ATOM_SITE_COLUMNS = (
    "_atom_site.id",
    "_atom_site.label_atom_id",
    "_atom_site.type_symbol",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_alt_id",
    "_atom_site.pdbx_PDB_model_num",
    "_atom_site.occupancy",
)
_OPTIONAL_ROW_ALIGNED_ATOM_SITE_COLUMNS = ("_atom_site.group_PDB",)


class CovapieMMCIFLigandAtomIdentityExtractorError(ValueError):
    """Raised unless exact source-ordered ligand atom identity is proven."""


def _fail(reason: str) -> NoReturn:
    raise CovapieMMCIFLigandAtomIdentityExtractorError(f"{_ERROR}:{reason}")


def _require_nonempty_exact_string(value: object, *, reason: str) -> str:
    if (
        type(value) is not str
        or not value
        or value in (".", "?")
        or value.strip() != value
    ):
        _fail(reason)
    return value


def _parse_cif_gz_payload(cif_gz_payload: object) -> dict[str, object]:
    if type(cif_gz_payload) is not bytes:
        _fail("CIF_GZ_PAYLOAD_EXACT_BYTES_REQUIRED")
    try:
        cif_payload = gzip.decompress(cif_gz_payload)
    except (EOFError, OSError) as error:
        raise CovapieMMCIFLigandAtomIdentityExtractorError(
            f"{_ERROR}:MALFORMED_GZIP"
        ) from error
    try:
        cif_text = cif_payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CovapieMMCIFLigandAtomIdentityExtractorError(
            f"{_ERROR}:MMCIF_UTF8_DECODE_FAILED"
        ) from error
    try:
        parsed = MMCIF2Dict(StringIO(cif_text))
    except Exception as error:
        raise CovapieMMCIFLigandAtomIdentityExtractorError(
            f"{_ERROR}:MALFORMED_MMCIF"
        ) from error
    return dict(parsed)


def _validated_atom_site_columns(
    parsed: dict[str, object],
) -> dict[str, list[str]]:
    columns: dict[str, list[str]] = {}
    for column_name in _REQUIRED_ATOM_SITE_COLUMNS:
        if column_name not in parsed:
            _fail(f"REQUIRED_ATOM_SITE_COLUMN_MISSING:{column_name}")
        values = parsed[column_name]
        if type(values) is not list:
            _fail(f"ATOM_SITE_COLUMN_EXACT_LIST_REQUIRED:{column_name}")
        columns[column_name] = values

    expected_length = len(columns["_atom_site.id"])
    for column_name, values in columns.items():
        if len(values) != expected_length:
            _fail(
                "ATOM_SITE_COLUMN_LENGTH_MISMATCH:"
                f"{column_name}:expected={expected_length}:actual={len(values)}"
            )

    for column_name in _OPTIONAL_ROW_ALIGNED_ATOM_SITE_COLUMNS:
        if column_name not in parsed:
            continue
        values = parsed[column_name]
        if type(values) is not list:
            _fail(f"ATOM_SITE_COLUMN_EXACT_LIST_REQUIRED:{column_name}")
        if len(values) != expected_length:
            _fail(
                "ATOM_SITE_COLUMN_LENGTH_MISMATCH:"
                f"{column_name}:expected={expected_length}:actual={len(values)}"
            )
    return columns


def extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1(
    *,
    cif_gz_payload: object,
    ligand_component_id: object,
    label_asym_id: object,
    model_num: object = 1,
) -> tuple[dict[str, object], ...]:
    """Return one exact ligand instance in original ``_atom_site`` row order."""

    component_id = _require_nonempty_exact_string(
        ligand_component_id,
        reason="LIGAND_COMPONENT_ID_NONEMPTY_EXACT_STRING_REQUIRED",
    )
    asym_id = _require_nonempty_exact_string(
        label_asym_id,
        reason="LABEL_ASYM_ID_NONEMPTY_EXACT_STRING_REQUIRED",
    )
    if type(model_num) is not int or model_num < 1:
        _fail("MODEL_NUM_EXACT_POSITIVE_INT_REQUIRED")
    requested_model_num = str(model_num)

    columns = _validated_atom_site_columns(_parse_cif_gz_payload(cif_gz_payload))
    selected: list[dict[str, object]] = []
    selected_atom_ids: set[str] = set()
    row_count = len(columns["_atom_site.id"])
    for source_row_index in range(row_count):
        if not (
            columns["_atom_site.label_comp_id"][source_row_index] == component_id
            and columns["_atom_site.label_asym_id"][source_row_index] == asym_id
            and columns["_atom_site.pdbx_PDB_model_num"][source_row_index]
            == requested_model_num
        ):
            continue

        atom_id = _require_nonempty_exact_string(
            columns["_atom_site.label_atom_id"][source_row_index],
            reason="ATOM_ID_NONEMPTY_EXACT_STRING_REQUIRED",
        )
        type_symbol = _require_nonempty_exact_string(
            columns["_atom_site.type_symbol"][source_row_index],
            reason="TYPE_SYMBOL_NONEMPTY_EXACT_STRING_REQUIRED",
        )
        atom_site_id = _require_nonempty_exact_string(
            columns["_atom_site.id"][source_row_index],
            reason="ATOM_SITE_ID_NONEMPTY_EXACT_STRING_REQUIRED",
        )
        alt_id = columns["_atom_site.label_alt_id"][source_row_index]
        if alt_id not in (".", "?"):
            _fail("ALTLOC_NOT_SUPPORTED_V1")
        if atom_id in selected_atom_ids:
            _fail("DUPLICATE_LABEL_ATOM_ID")
        selected_atom_ids.add(atom_id)

        selected.append(
            {
                "atom_id": atom_id,
                "type_symbol": type_symbol,
                "parser_local_index": len(selected),
                "source_atom_site_row_index_0based": source_row_index,
                "atom_site_id": atom_site_id,
                "label_comp_id": columns["_atom_site.label_comp_id"][
                    source_row_index
                ],
                "label_asym_id": columns["_atom_site.label_asym_id"][
                    source_row_index
                ],
                "model_num": columns["_atom_site.pdbx_PDB_model_num"][
                    source_row_index
                ],
                "label_alt_id": alt_id,
                "occupancy": columns["_atom_site.occupancy"][source_row_index],
            }
        )

    if not selected:
        _fail("NO_MATCHING_LIGAND_ROWS")
    return tuple(selected)
