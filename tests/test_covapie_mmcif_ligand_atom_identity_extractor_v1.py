from __future__ import annotations

import gzip
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from covalent_ext import (
    covapie_ffq_direct_profile_role_mask_tensorizer_v1 as ffq_tensorizer,
)
from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as ffq_successor,
)
from covalent_ext import covapie_mmcif_ligand_atom_identity_extractor_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = (
    "_atom_site.id",
    "_atom_site.label_atom_id",
    "_atom_site.type_symbol",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_alt_id",
    "_atom_site.pdbx_PDB_model_num",
    "_atom_site.occupancy",
)
ALL_COLUMNS = REQUIRED_COLUMNS + ("_atom_site.group_PDB",)


def _row(
    atom_site_id: str,
    atom_id: str,
    type_symbol: str,
    *,
    component: str = "FFQ",
    asym_id: str = "E",
    alt_id: str = ".",
    model_num: str = "1",
    occupancy: str = "1.00",
    group_pdb: str = "HETATM",
) -> dict[str, str]:
    return {
        "_atom_site.id": atom_site_id,
        "_atom_site.label_atom_id": atom_id,
        "_atom_site.type_symbol": type_symbol,
        "_atom_site.label_comp_id": component,
        "_atom_site.label_asym_id": asym_id,
        "_atom_site.label_alt_id": alt_id,
        "_atom_site.pdbx_PDB_model_num": model_num,
        "_atom_site.occupancy": occupancy,
        "_atom_site.group_PDB": group_pdb,
    }


def _cif_gz(
    rows: list[dict[str, str]],
    *,
    columns: tuple[str, ...] = ALL_COLUMNS,
    skip_value: tuple[int, str] | None = None,
) -> bytes:
    lines = ["data_synthetic", "#", "loop_", *columns]
    for row_index, row in enumerate(rows):
        for column in columns:
            if skip_value == (row_index, column):
                continue
            lines.append(row[column])
    lines.append("#")
    return gzip.compress(("\n".join(lines) + "\n").encode("utf-8"), mtime=0)


def _extract(
    payload: bytes,
    *,
    component: str = "FFQ",
    asym_id: str = "E",
    model_num: int = 1,
) -> tuple[dict[str, object], ...]:
    return subject.extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1(
        cif_gz_payload=payload,
        ligand_component_id=component,
        label_asym_id=asym_id,
        model_num=model_num,
    )


def _published_ffq_record(pdb_id: str = "3VCY") -> dict[str, Any]:
    event_id = next(
        event_id
        for event_id in ffq_successor._CANONICAL_EVENT_IDS
        if f":{pdb_id}:" in event_id
    )
    return ffq_successor._expected_record(
        {
            "canonical_event_id": event_id,
            "pdb_id": pdb_id,
            "completed_lane": (
                "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                if pdb_id == "3VCY"
                else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
            ),
        }
    )


def test_valid_extraction_preserves_source_order_and_builds_local_indices() -> None:
    payload = _cif_gz(
        [
            _row("10", "CA", "C", component="ALA", asym_id="A", group_pdb="ATOM"),
            _row("11", "O1", "O"),
            _row("12", "OW", "O", component="HOH", asym_id="W"),
            _row("13", "C1", "C", alt_id="?", occupancy="0.75"),
        ]
    )

    rows = _extract(payload)

    assert rows == (
        {
            "atom_id": "O1",
            "type_symbol": "O",
            "parser_local_index": 0,
            "source_atom_site_row_index_0based": 1,
            "atom_site_id": "11",
            "label_comp_id": "FFQ",
            "label_asym_id": "E",
            "model_num": "1",
            "label_alt_id": ".",
            "occupancy": "1.00",
        },
        {
            "atom_id": "C1",
            "type_symbol": "C",
            "parser_local_index": 1,
            "source_atom_site_row_index_0based": 3,
            "atom_site_id": "13",
            "label_comp_id": "FFQ",
            "label_asym_id": "E",
            "model_num": "1",
            "label_alt_id": "?",
            "occupancy": "0.75",
        },
    )


def test_different_label_asym_id_selects_exact_instance() -> None:
    payload = _cif_gz(
        [
            _row("1", "C_E", "C", asym_id="E"),
            _row("2", "O_F", "O", asym_id="F"),
        ]
    )

    assert [row["atom_id"] for row in _extract(payload, asym_id="F")] == ["O_F"]


def test_different_component_selects_exact_component() -> None:
    payload = _cif_gz(
        [
            _row("1", "C_FFQ", "C"),
            _row("2", "N_LIG", "N", component="LIG"),
        ]
    )

    assert [
        row["atom_id"] for row in _extract(payload, component="LIG")
    ] == ["N_LIG"]


def test_model_num_filters_exact_model() -> None:
    payload = _cif_gz(
        [
            _row("1", "C_MODEL_1", "C", model_num="1"),
            _row("2", "C_MODEL_2", "C", model_num="2"),
        ]
    )

    rows = _extract(payload, model_num=2)
    assert [row["atom_id"] for row in rows] == ["C_MODEL_2"]
    assert rows[0]["model_num"] == "2"


def test_no_matching_ligand_rows_fails_closed() -> None:
    payload = _cif_gz([_row("1", "C1", "C")])

    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="NO_MATCHING_LIGAND_ROWS",
    ):
        _extract(payload, asym_id="Z")


@pytest.mark.parametrize("missing_column", REQUIRED_COLUMNS)
def test_each_missing_required_atom_site_column_fails_closed(
    missing_column: str,
) -> None:
    columns = tuple(column for column in ALL_COLUMNS if column != missing_column)
    payload = _cif_gz([_row("1", "C1", "C")], columns=columns)

    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="REQUIRED_ATOM_SITE_COLUMN_MISSING",
    ):
        _extract(payload)


def test_atom_site_column_length_mismatch_fails_closed() -> None:
    payload = _cif_gz(
        [_row("1", "C1", "C"), _row("2", "O1", "O")],
        columns=REQUIRED_COLUMNS,
        skip_value=(1, "_atom_site.occupancy"),
    )

    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="ATOM_SITE_COLUMN_LENGTH_MISMATCH",
    ):
        _extract(payload)


def test_duplicate_label_atom_id_in_selected_instance_fails_closed() -> None:
    payload = _cif_gz([_row("1", "C1", "C"), _row("2", "C1", "C")])

    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="DUPLICATE_LABEL_ATOM_ID",
    ):
        _extract(payload)


@pytest.mark.parametrize("alt_id", ("A", "B"))
def test_real_altloc_fails_closed(alt_id: str) -> None:
    payload = _cif_gz([_row("1", "C1", "C", alt_id=alt_id)])

    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="ALTLOC_NOT_SUPPORTED_V1",
    ):
        _extract(payload)


def test_malformed_gzip_fails_closed() -> None:
    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="MALFORMED_GZIP",
    ):
        _extract(b"not-a-gzip-stream")


def test_malformed_mmcif_fails_closed() -> None:
    payload = gzip.compress(b"data_broken\n_broken 'unterminated\n", mtime=0)

    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="MALFORMED_MMCIF",
    ):
        _extract(payload)


def test_explicit_hydrogen_is_preserved_before_downstream_projection() -> None:
    payload = _cif_gz(
        [
            _row("1", "C1", "C"),
            _row("2", "H1", "H"),
            _row("3", "O1", "O"),
        ]
    )

    rows = _extract(payload)
    assert [(row["atom_id"], row["type_symbol"]) for row in rows] == [
        ("C1", "C"),
        ("H1", "H"),
        ("O1", "O"),
    ]
    assert [row["parser_local_index"] for row in rows] == [0, 1, 2]


def test_double_call_is_deterministic() -> None:
    payload = _cif_gz([_row("1", "O1", "O"), _row("2", "C1", "C")])

    assert _extract(payload) == _extract(payload)


def test_extractor_rows_feed_published_ffq_role_mask_tensorizer() -> None:
    atom_ids = ("C1", "O1", "P1", "C2", "O2", "C3", "O3", "O4")
    payload = _cif_gz(
        [
            _row(str(index + 1), atom_id, atom_id[0])
            for index, atom_id in enumerate(atom_ids)
        ]
    )
    extracted = _extract(payload)

    result = ffq_tensorizer.tensorize_covapie_ffq_direct_profile_role_masks_v1(
        effective_supervision_record=_published_ffq_record(),
        ligand_atom_rows=extracted,
        canonical_task_id=0,
    )

    generated = result.ligand_base_generation_mask.squeeze(1).nonzero().flatten()
    fixed = result.ligand_base_fixed_mask.squeeze(1).nonzero().flatten()
    assert [row["atom_id"] for row in extracted] == list(atom_ids)
    assert generated.tolist() == [0, 1, 3, 5]
    assert fixed.tolist() == [2, 4, 6, 7]


def test_non_bytes_payload_fails_closed() -> None:
    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match="CIF_GZ_PAYLOAD_EXACT_BYTES_REQUIRED",
    ):
        subject.extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1(
            cif_gz_payload=bytearray(),
            ligand_component_id="FFQ",
            label_asym_id="E",
        )


@pytest.mark.parametrize(
    ("row_override", "error"),
    (
        ({"_atom_site.id": "?"}, "ATOM_SITE_ID_NONEMPTY_EXACT_STRING_REQUIRED"),
        ({"_atom_site.label_atom_id": "."}, "ATOM_ID_NONEMPTY_EXACT_STRING_REQUIRED"),
        ({"_atom_site.type_symbol": "?"}, "TYPE_SYMBOL_NONEMPTY_EXACT_STRING_REQUIRED"),
    ),
)
def test_selected_identity_missing_markers_fail_closed(
    row_override: dict[str, str], error: str
) -> None:
    row = _row("1", "C1", "C")
    row.update(row_override)

    with pytest.raises(
        subject.CovapieMMCIFLigandAtomIdentityExtractorError,
        match=error,
    ):
        _extract(_cif_gz([row]))


def test_production_import_has_no_stdout_or_stderr() -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        (
            sys.executable,
            "-c",
            "import covalent_ext.covapie_mmcif_ligand_atom_identity_extractor_v1",
        ),
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
