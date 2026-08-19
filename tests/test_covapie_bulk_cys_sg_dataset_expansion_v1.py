from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import gzip
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk
from covalent_ext import covapie_bulk_source_adapters_v1 as adapters


ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 64


def _ccd(
    *, component: str = "XYZ", terminal_element: str = "O",
    terminal_order: str = "DOUB",
) -> bytes:
    return f"""data_{component}
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
_chem_comp_atom.pdbx_aromatic_flag
C1 C 0 N
C2 C 0 N
X1 {terminal_element} 0 N
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
C1 C2 SING N
C2 X1 {terminal_order} N
#
""".encode()


def _pdb_line(record: str = "9XYZ", *, with_link: bool = True) -> bytes:
    header = list(" " * 80)
    header[:6] = "HEADER"
    header[62:66] = record
    lines = ["".join(header)]
    het = list(" " * 80)
    het[:6] = "HETATM"
    het[17:20] = "XYZ"
    het[21:22] = "L"
    het[22:26] = f"{501:4d}"
    lines.append("".join(het))
    if with_link:
        link = list(" " * 80)
        link[:6] = "LINK  "
        link[12:16] = " SG "
        link[17:20] = "CYS"
        link[21:22] = "A"
        link[22:26] = f"{10:4d}"
        link[42:46] = " C1 "
        link[47:50] = "XYZ"
        link[51:52] = "L"
        link[52:56] = f"{501:4d}"
        lines.append("".join(link))
    return ("\n".join(lines) + "\n").encode()


def _connection(
    *,
    comp: str = "XYZ",
    ligand_atom: str = "C1",
    ligand_asym: str = "L",
    protein_asym: str = "A",
    protein_comp: str = "CYS",
    protein_atom: str = "SG",
    protein_seq: object = 1,
    connect_type: str = "covalent bond",
    identity: str = "covale1",
    altloc: str | None = None,
) -> dict[str, object]:
    return {
        "id": identity,
        "connect_type": connect_type,
        "description": None,
        "dist_value": 1.8,
        "value_order": "sing",
        "connect_target": {
            "auth_asym_id": protein_asym,
            "auth_seq_id": "10",
            "label_alt_id": None,
            "label_asym_id": protein_asym,
            "label_atom_id": protein_atom,
            "label_comp_id": protein_comp,
            "label_seq_id": protein_seq,
            "symmetry": "1_555",
        },
        "connect_partner": {
            "label_alt_id": altloc,
            "label_asym_id": ligand_asym,
            "label_atom_id": ligand_atom,
            "label_comp_id": comp,
            "label_seq_id": None,
            "symmetry": "1_555",
        },
    }


def _rcsb_record(
    *, pdb: str = "9XYZ", comp: str = "XYZ", ligand_atom: str = "C1",
    ligand_asym: str = "L", protein_asym: str = "A", identity: str = "covale1",
    altloc: str | None = None,
) -> dict[str, object]:
    record = adapters.normalize_rcsb_connection_record_v1(
        entry_id=pdb,
        polymer_instance_id=f"{pdb}.{protein_asym}",
        connection=_connection(
            comp=comp, ligand_atom=ligand_atom, ligand_asym=ligand_asym,
            protein_asym=protein_asym, identity=identity, altloc=altloc,
        ),
        source_payload_sha256=SHA,
        search_request_sha256=SHA,
        search_result_identity_digest=SHA,
        data_api_endpoint_descriptor="https://data.rcsb.org/graphql#test",
    )
    assert record is not None
    return record


def _specialist(
    *, pdb: str = "9XYZ", comp: str = "XYZ", source: str = adapters.SOURCE_COVBINDERINPDB,
    record_id: str = "CBR1", warhead: str = "Acrylamide", chain: str = "A",
    smiles: str = "CC",
) -> dict[str, object]:
    record = adapters.normalize_covbinderinpdb_record_v1({
        "record_id": record_id,
        "full_residue_name": "Cysteine",
        "pdb_id": pdb,
        "chain_id": chain,
        "res_num": "10",
        "binder_type": "inhibitor",
        "warhead_name": warhead,
        "binder_chain_id": "L",
        "binder_num": "501",
        "binder_id_in_adduct": comp,
        "binder_smiles": smiles,
        "adduct_smiles": "CC",
        "unp_accessionid": "P12345",
        "doi": "10.1/test",
    }, source_payload_sha256=SHA)
    record["source_dataset"] = source
    adapters.validate_canonical_source_record_v1(record)
    return record


def _merged_event(
    *, pdb: str = "9XYZ", comp: str = "XYZ", ligand_asym: str = "L",
    protein_asym: str = "A", smiles: str | None = None,
) -> dict[str, object]:
    rcsb = _rcsb_record(
        pdb=pdb, comp=comp, ligand_asym=ligand_asym, protein_asym=protein_asym,
    )
    specialists = [] if smiles is None else [
        _specialist(
            pdb=pdb, comp=comp, chain=protein_asym, smiles=smiles,
        )
    ]
    merged, unmatched = adapters.merge_cross_source_events_v1([rcsb], specialists)
    assert len(merged) == 1 and not unmatched
    return merged[0]


def _mmcif(
    *, pdb: str = "9XYZ", comp: str = "XYZ", ligand_atom: str = "C1",
    ligand_asym: str = "L", protein_asym: str = "A", altloc: str = ".",
    ligand_element: str = "C",
) -> bytes:
    text = f"""data_{pdb}
_entry.id {pdb}
loop_
_struct_conn.id
_struct_conn.conn_type_id
_struct_conn.ptnr1_label_asym_id
_struct_conn.ptnr1_label_comp_id
_struct_conn.ptnr1_label_seq_id
_struct_conn.ptnr1_label_atom_id
_struct_conn.ptnr1_auth_asym_id
_struct_conn.ptnr1_auth_comp_id
_struct_conn.ptnr1_auth_seq_id
_struct_conn.ptnr1_auth_atom_id
_struct_conn.pdbx_ptnr1_label_alt_id
_struct_conn.ptnr2_label_asym_id
_struct_conn.ptnr2_label_comp_id
_struct_conn.ptnr2_label_seq_id
_struct_conn.ptnr2_label_atom_id
_struct_conn.ptnr2_auth_asym_id
_struct_conn.ptnr2_auth_comp_id
_struct_conn.ptnr2_auth_seq_id
_struct_conn.ptnr2_auth_atom_id
_struct_conn.pdbx_ptnr2_label_alt_id
_struct_conn.pdbx_dist_value
covale1 covale {protein_asym} CYS 1 SG {protein_asym} CYS 10 SG . {ligand_asym} {comp} . {ligand_atom} {ligand_asym} {comp} 501 {ligand_atom} {altloc} 1.8
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
ATOM 1 S SG . CYS {protein_asym} 1 0.0 0.0 0.0 1.0 10 CYS {protein_asym} SG 1
ATOM 2 C CA . CYS {protein_asym} 1 -1.0 0.0 0.0 1.0 10 CYS {protein_asym} CA 1
ATOM 3 N N . CYS {protein_asym} 1 -1.0 1.0 0.0 1.0 10 CYS {protein_asym} N 1
HETATM 4 {ligand_element} {ligand_atom} {altloc} {comp} {ligand_asym} . 1.8 0.0 0.0 1.0 501 {comp} {ligand_asym} {ligand_atom} 1
HETATM 5 C C2 {altloc} {comp} {ligand_asym} . 2.8 0.0 0.0 1.0 501 {comp} {ligand_asym} C2 1
#
"""
    return gzip.compress(text.encode("utf-8"), mtime=0)


def test_four_adapter_registrations_share_contract() -> None:
    assert tuple(sorted(adapters.adapter_registry_v1())) == tuple(sorted(
        adapters.SOURCE_DATASETS
    ))


def test_canonical_source_record_schema_and_missing_fields() -> None:
    record = adapters.normalize_covpdb_ligand_record_v1(
        record_id="COVPDB1", source_payload_sha256=SHA,
    )
    adapters.validate_canonical_source_record_v1(record)
    assert set(adapters.CANONICAL_SOURCE_RECORD_FIELDS) <= set(record)
    assert "pdb_id" in record["source_fields_missing"]
    assert record["pdb_id"] is None


def test_specialized_source_cannot_create_production_authority() -> None:
    record = _specialist()
    record["source_record_provenance"].append(
        adapters.PRODUCTION_CHEMISTRY_AUTHORITY
    )
    with pytest.raises(ValueError, match="CANNOT_CREATE_PRODUCTION"):
        adapters.validate_canonical_source_record_v1(record)


def test_source_access_statuses_validate_and_covalentindb_does_not_scrape() -> None:
    records = bulk.source_access_resolution_v1()
    assert len(records) == 4
    by_name = {item["source_name"]: item for item in records}
    deferred = by_name[adapters.SOURCE_COVALENTINDB]
    assert deferred["current_lane_status"] == "DEFERRED_NO_MACHINE_READABLE_BULK_ACCESS"
    assert deferred["automated_scraping_allowed"] is False
    assert deferred["programmatic_access_allowed"] is False


def test_operational_status_fails_without_programmatic_permission() -> None:
    record = deepcopy(bulk.source_access_resolution_v1()[0])
    record["current_lane_status"] = "OPERATIONAL_BULK_API"
    record["programmatic_access_allowed"] = "unresolved"
    with pytest.raises(ValueError, match="PROGRAMMATIC_ACCESS"):
        adapters.validate_source_access_resolution_v1(record)


def test_rcsb_request_canonicalization_and_budget() -> None:
    left = bulk.build_rcsb_search_request_v1(start=0, rows=1000)
    right = bulk.build_rcsb_search_request_v1(start=0, rows=1000)
    assert bulk._canonical_json(left) == bulk._canonical_json(right)
    with pytest.raises(ValueError, match="PAGINATION_BUDGET"):
        bulk.build_rcsb_search_request_v1(start=4500, rows=1000)


def test_covpdb_official_download_page_resolves_all_complexes_href() -> None:
    page = b"""<table><tr><td>All Complexes</td><td><a href='/official/all.zip'>Download</a></td><td>ZIP</td></tr></table>"""
    assert bulk.resolve_covpdb_complexes_href_v1(page) == (
        "https://drug-discovery.vm.uni-freiburg.de/official/all.zip"
    )


def test_covpdb_complex_archive_parsing_and_exact_link_recovery() -> None:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("complexes/9XYZ.pdb", _pdb_line())
    records, facts = bulk.parse_covpdb_complex_archive_v1(
        buffer.getvalue(), archive_sha256=SHA,
    )
    assert facts == {"archive_entry_count": 1, "pdb_member_count": 1}
    assert len(records) == 1
    assert records[0]["pdb_id"] == "9XYZ"
    assert records[0]["protein_reactive_atom"] == "SG"
    assert records[0]["ligand_component_id"] == "XYZ"
    assert records[0]["ligand_reactive_atom"] == "C1"


def test_covpdb_pdb_only_seed_fallback_does_not_invent_event() -> None:
    records = bulk.parse_covpdb_complex_member_v1(
        member_name="9XYZ.pdb", member_payload=_pdb_line(with_link=False),
        archive_sha256=SHA,
    )
    assert len(records) == 1 and records[0]["pdb_id"] == "9XYZ"
    assert records[0]["ligand_component_id"] is None
    assert "PARTIAL_PDB_SEED_NO_EXACT_EVENT" in records[0]["source_quality_flags"]


def test_rcsb_pagination_uses_five_bounded_pages_without_network() -> None:
    class Cache:
        def __init__(self) -> None:
            self.entries: dict[str, dict[str, object]] = {}

        def fetch(self, **kwargs: object):  # type: ignore[no-untyped-def]
            path = str(kwargs["relative_path"])
            entry = {
                "sha256": SHA,
                "cache_reuse_status": "DOWNLOADED_BY_BULK_PILOT",
            }
            self.entries[path] = entry
            if path.startswith("rcsb/search_"):
                page = int(path[-9:-5])
                result = [f"X{page * 1000 + index:06d}" for index in range(1000)]
                payload = json.dumps({
                    "total_count": 5000, "result_set": result,
                }).encode()
            else:
                payload = b'{"data":{"entries":[]}}'
            return payload, entry

    records, snapshot = bulk.discover_rcsb_direct_v1(Cache())  # type: ignore[arg-type]
    assert records == []
    assert len(snapshot["search_pages"]) == 5
    assert snapshot["rcsb_search_results_examined"] == 5000
    assert snapshot["real_rcsb_network_discovery_performed"] is True


def test_specialist_seeded_rcsb_recovers_pdb_outside_direct_window() -> None:
    class Cache:
        def fetch(self, **kwargs: object):  # type: ignore[no-untyped-def]
            request = json.loads(bytes(kwargs["request_body"]))
            pdb_id = request["variables"]["ids"][0]
            payload = json.dumps({
                "data": {"entries": [{
                    "rcsb_id": pdb_id,
                    "polymer_entities": [{"polymer_entity_instances": [{
                        "rcsb_id": f"{pdb_id}.A",
                        "rcsb_polymer_struct_conn": [_connection()],
                    }]}],
                }]},
            }).encode()
            return payload, {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "cache_reuse_status": "DOWNLOADED_BY_BULK_PILOT",
            }

    specialist = _specialist()
    records, snapshot, statuses = bulk.discover_rcsb_specialist_seeded_v1(
        Cache(), specialist_records=[specialist], direct_records=[],  # type: ignore[arg-type]
    )
    assert statuses == {"9XYZ": "EXAMINED"}
    assert len(records) == 1
    assert snapshot["specialist_seeded_exact_cys_sg_event_count"] == 1
    merged, unmatched = adapters.merge_cross_source_events_v1(
        records, [specialist], specialist_pdb_statuses=statuses,
    )
    assert len(merged) == 1 and not unmatched
    assert adapters.SOURCE_COVBINDERINPDB in merged[0]["source_datasets"]


def test_ambiguous_specialist_event_mapping_remains_fail_closed() -> None:
    first = _rcsb_record(ligand_atom="C1", identity="covale1")
    second = _rcsb_record(ligand_atom="C2", identity="covale2")
    specialist = _specialist()
    matches, reason = adapters.resolve_specialist_event_mapping_v1(
        specialist, [first, second], pdb_recovery_status="EXAMINED",
    )
    assert len(matches) == 2
    assert reason == "SPECIALIST_EVENT_MAPPING_AMBIGUOUS"
    _merged, unmatched = adapters.merge_cross_source_events_v1(
        [first, second], [specialist], specialist_pdb_statuses={"9XYZ": "EXAMINED"},
    )
    assert unmatched[0]["reason"] == "SPECIALIST_EVENT_MAPPING_AMBIGUOUS"


@pytest.mark.parametrize(
    ("records", "status", "expected"),
    [
        ([], "NOT_AVAILABLE", "SPECIALIST_PDB_NOT_AVAILABLE"),
        ([], "EXAMINED", "SPECIALIST_PDB_NO_EXACT_CYS_SG_EVENT"),
        ([_rcsb_record(comp="ABC")], "EXAMINED", "SPECIALIST_LIGAND_NOT_FOUND_IN_EXACT_EVENT"),
    ],
)
def test_specialist_unmatched_reasons_are_specific(
    records: list[dict[str, object]], status: str, expected: str,
) -> None:
    _matches, reason = adapters.resolve_specialist_event_mapping_v1(
        _specialist(), records, pdb_recovery_status=status,
    )
    assert reason == expected


@pytest.mark.parametrize("connection", [
    _connection(connect_type="metal coordination"),
    _connection(protein_comp="CYS", protein_atom="CA"),
    _connection(protein_comp="SER", protein_atom="OG"),
])
def test_exact_connection_filter_rejects_non_cys_sg_and_metal(
    connection: dict[str, object],
) -> None:
    assert adapters.exact_cys_sg_rcsb_connection_v1(connection) is None


def test_disulfide_rejected() -> None:
    connection = _connection(comp="CYS", ligand_atom="SG")
    connection["connect_partner"]["label_seq_id"] = 2  # type: ignore[index]
    assert adapters.exact_cys_sg_rcsb_connection_v1(connection) is None


def test_polymer_polymer_connection_rejected() -> None:
    connection = _connection()
    connection["connect_partner"]["label_seq_id"] = 4  # type: ignore[index]
    assert adapters.exact_cys_sg_rcsb_connection_v1(connection) is None


def test_distance_only_record_cannot_invent_event() -> None:
    connection = _connection()
    connection["connect_type"] = "hydrogen bond"
    assert adapters.exact_cys_sg_rcsb_connection_v1(connection) is None


def test_canonical_event_identity_is_source_independent_and_deterministic() -> None:
    record = _rcsb_record()
    first = adapters.build_canonical_event_id_v1(record)
    changed = dict(record, source_dataset=adapters.SOURCE_COVPDB)
    assert adapters.build_canonical_event_id_v1(changed) == first
    assert adapters.SOURCE_RCSB_PDB_DIRECT not in first


@pytest.mark.parametrize("source_count", [2, 3, 4])
def test_same_event_from_multiple_sources_merges_once_with_provenance(
    source_count: int,
) -> None:
    sources = [
        adapters.SOURCE_COVBINDERINPDB,
        adapters.SOURCE_COVPDB,
        adapters.SOURCE_COVALENTINDB,
    ][:source_count - 1]
    specialists = [
        _specialist(source=source, record_id=f"S{index}")
        for index, source in enumerate(sources)
    ]
    merged, unmatched = adapters.merge_cross_source_events_v1(
        [_rcsb_record()], specialists,
    )
    assert not unmatched and len(merged) == 1
    assert merged[0]["source_count"] == source_count
    assert merged[0]["source_datasets"] == sorted(
        [adapters.SOURCE_RCSB_PDB_DIRECT, *sources]
    )


def test_annotation_disagreement_is_preserved() -> None:
    merged, unmatched = adapters.merge_cross_source_events_v1(
        [_rcsb_record()],
        [
            _specialist(record_id="A", warhead="Acrylamide"),
            _specialist(record_id="B", warhead="Nitrile"),
        ],
    )
    assert not unmatched
    assert merged[0]["source_annotation_conflict"] is True
    assert merged[0]["supporting_warhead_annotations"] == ["Acrylamide", "Nitrile"]


def test_multiple_events_in_same_pdb_remain_distinct() -> None:
    first = _rcsb_record(ligand_asym="L", identity="covale1")
    second = _rcsb_record(
        comp="ABC", ligand_atom="N1", ligand_asym="M", identity="covale2",
    )
    merged, _ = adapters.merge_cross_source_events_v1([first, second], [])
    assert len(merged) == 2
    assert len({item["canonical_event_id"] for item in merged}) == 2


def test_cache_atomic_write_and_conflict_failure(tmp_path: Path) -> None:
    target = tmp_path / "cache" / "payload.bin"
    assert bulk.atomic_cache_write_v1(target, b"first") == hashlib.sha256(b"first").hexdigest()
    assert bulk.atomic_cache_write_v1(target, b"first")
    with pytest.raises(ValueError, match="CONFLICT"):
        bulk.atomic_cache_write_v1(target, b"second")
    assert not list(tmp_path.rglob("*.part"))


def test_gzip_mmcif_and_pdb_identity_validation() -> None:
    payload = _mmcif()
    assert "_struct_conn" in bulk._validate_mmcif_payload(payload, "9XYZ")
    with pytest.raises(ValueError, match="ENTRY_ID_MISMATCH"):
        bulk._validate_mmcif_payload(payload, "8ABC")
    with pytest.raises(ValueError, match="GZIP"):
        bulk._validate_mmcif_payload(b"not gzip", "9XYZ")


def test_struct_conn_recovery_altloc_and_post_distance() -> None:
    event = _merged_event()
    outcome = bulk.process_event_structure_v1(
        event,
        mmcif_payload=_mmcif(),
        authorities=(),
        known_historical=set(),
    )
    assert outcome["structural_processing"]["explicit_covalent_evidence"] is True
    assert outcome["structural_processing"]["post_distance_angstrom"] == 1.8
    assert outcome["structural_processing"]["distance_only_event_inference_used"] is False


def test_explicit_altloc_is_deterministic() -> None:
    record = _rcsb_record(altloc="A")
    merged, _ = adapters.merge_cross_source_events_v1([record], [])
    outcome = bulk.process_event_structure_v1(
        merged[0],
        mmcif_payload=_mmcif(altloc="A"),
        authorities=(),
        known_historical=set(),
    )
    assert outcome["structural_processing"]["selected_ligand_altloc"] == "A"


def test_feature_compatibility_rejects_unsupported_heavy_atom() -> None:
    outcome = bulk.process_event_structure_v1(
        _merged_event(),
        mmcif_payload=_mmcif(ligand_element="Se"),
        authorities=(),
        known_historical=set(),
    )
    assert outcome["terminal_outcome"] == "REJECTED_FEATURE_INCOMPATIBLE"
    assert "UNSUPPORTED_NONHYDROGEN_MODEL_ATOM" in outcome["terminal_reasons"]


def test_pre_only_atom_is_quarantined_and_not_removed() -> None:
    facts = bulk._rdkit_pre_facts(["CCCl"], retained_heavy_atom_count=2)
    assert facts["status"] == "PRE_ATOM_LOSS_REPRESENTATION_GAP"
    assert facts["supporting_pre_heavy_atom_counts"] == [3]


def test_ccd_cif_atom_bond_and_charge_parsing() -> None:
    parsed = bulk.parse_ccd_cif_v1(_ccd(), ccd_id="XYZ")
    assert parsed["ccd_atom_inventory"] == [
        {"atom_id": "C1", "type_symbol": "C", "charge": 0, "aromatic_flag": "N"},
        {"atom_id": "C2", "type_symbol": "C", "charge": 0, "aromatic_flag": "N"},
        {"atom_id": "X1", "type_symbol": "O", "charge": 0, "aromatic_flag": "N"},
    ]
    assert parsed["ccd_bond_inventory"][1]["value_order"] == "DOUB"
    assert parsed["ccd_formal_charge_pattern"] == [["C1", 0], ["C2", 0], ["X1", 0]]
    assert len(parsed["ccd_component_graph_sha256"]) == 64


def test_ccd_retained_atom_coverage_and_pre_only_detection() -> None:
    ccd = bulk.parse_ccd_cif_v1(_ccd(), ccd_id="XYZ")
    complete = bulk._rdkit_pre_facts(
        [], retained_heavy_atom_count=3, ccd=ccd,
        retained_heavy_atom_names=["C1", "C2", "X1"], reactive_atom_id="C1",
    )
    assert complete["ccd_retained_atom_coverage_complete"] is True
    assert complete["status"] == "PRE_REACTION_UNRESOLVED"
    missing = bulk._rdkit_pre_facts(
        [], retained_heavy_atom_count=2, ccd=ccd,
        retained_heavy_atom_names=["C1", "C2"], reactive_atom_id="C1",
    )
    assert missing["ccd_atoms_missing_from_retained"] == ["X1"]
    assert missing["status"] == "PRE_ONLY_ATOMS_DETECTED"


def test_ccd_topology_is_not_automatic_pre_authority() -> None:
    ccd = bulk.parse_ccd_cif_v1(_ccd(), ccd_id="XYZ")
    facts = bulk._rdkit_pre_facts(
        [], retained_heavy_atom_count=3, ccd=ccd,
        retained_heavy_atom_names=["C1", "C2", "X1"], reactive_atom_id="C1",
    )
    assert facts["formal_charge_pattern_authoritative"] is False
    assert facts["status"] == "PRE_REACTION_UNRESOLVED"


def test_supporting_pre_smiles_graph_parsing_and_unique_mapping() -> None:
    ccd = bulk.parse_ccd_cif_v1(_ccd(), ccd_id="XYZ")
    facts = bulk.supporting_source_graph_facts_v1(
        pre_smiles=["CC=O"], adduct_smiles=["CC=O"], ccd=ccd,
        reactive_atom_id="C1",
    )
    assert facts["pre_source_graph_sha256"]
    assert facts["adduct_source_graph_sha256"]
    assert facts["pre_source_graph_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_UNIQUE"
    assert facts["pre_reactive_center_radius2_sha256"]


def test_ambiguous_pre_graph_mapping_fails_closed() -> None:
    symmetric = b"""data_SYM
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
A1 C 0
A2 C 0
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
A1 A2 SING
#
"""
    ccd = bulk.parse_ccd_cif_v1(symmetric, ccd_id="SYM")
    facts = bulk.supporting_source_graph_facts_v1(
        pre_smiles=["CC"], adduct_smiles=[], ccd=ccd, reactive_atom_id="A1",
    )
    assert facts["pre_source_graph_mapping_status"] == "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"


def test_reactive_center_fingerprints_are_deterministic_and_sensitive() -> None:
    first = bulk.parse_ccd_cif_v1(_ccd(), ccd_id="XYZ")
    changed = bulk.parse_ccd_cif_v1(
        _ccd(terminal_element="N", terminal_order="SING"), ccd_id="XYZ",
    )
    left = bulk.build_reactive_center_facts_v1(first, reactive_atom_id="C1")
    replay = bulk.build_reactive_center_facts_v1(first, reactive_atom_id="C1")
    right = bulk.build_reactive_center_facts_v1(changed, reactive_atom_id="C1")
    assert left["reactive_center_radius1_sha256"] == replay["reactive_center_radius1_sha256"]
    assert left["reactive_center_radius2_sha256"] == replay["reactive_center_radius2_sha256"]
    assert left["reactive_center_radius2_sha256"] != right["reactive_center_radius2_sha256"]


def test_same_local_chemistry_different_distal_scaffold_has_same_fingerprint() -> None:
    from rdkit import Chem

    first = Chem.MolFromSmiles("CCCCO")
    second = Chem.MolFromSmiles("CCCCN")
    assert first is not None and second is not None
    first_hash, _ = bulk._rooted_local_fingerprint_v1(first, root_index=0, radius=2)
    second_hash, _ = bulk._rooted_local_fingerprint_v1(second, root_index=0, radius=2)
    assert first_hash == second_hash


def test_2djf_lossy_retained_pre_shortcut_forbidden() -> None:
    event = _merged_event(pdb="2DJF", comp="1ZB", protein_asym="B", smiles="CCCl")
    outcome = bulk.process_event_structure_v1(
        event,
        mmcif_payload=_mmcif(pdb="2DJF", comp="1ZB", protein_asym="B"),
        authorities=(),
        known_historical=set(),
    )
    assert outcome["terminal_outcome"] == "KNOWN_EXISTING_QUARANTINE"
    assert outcome["pre_representability"]["status"] == "PRE_ATOM_LOSS_REPRESENTATION_GAP"


def test_authority_registry_count_and_hash_remain_three() -> None:
    path = ROOT / bulk.AUTHORITY_REGISTRY_RELATIVE
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    authorities = bulk.production_pipeline.load_reusable_authority_registry_v1(path)
    assert len(authorities) == 3
    assert before == bulk.AUTHORITY_REGISTRY_SHA256


def test_no_family_level_acrylamide_auto_admission() -> None:
    event = _merged_event(smiles="CC")
    outcome = bulk.process_event_structure_v1(
        event, mmcif_payload=_mmcif(), authorities=(), known_historical=set(),
    )
    assert outcome["terminal_outcome"] == "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY"
    assert "NO_FAMILY_LEVEL_AUTO_ADMISSION" in outcome["terminal_reasons"]


def test_known_identity_dedup_is_separate_from_exact_matcher() -> None:
    authorities, _leakage, _historical = bulk._load_frozen_state_v1(ROOT)
    evaluation = bulk._authority_match_evaluation(
        authorities, known_authority_identity=True, pdb_id="5F2E",
    )
    assert all(
        item["candidate_match_result"]
        == "KNOWN_IDENTITY_DEDUPLICATION_NOT_MATCHER_PROOF"
        for item in evaluation
    )
    assert all(
        item["candidate_chemistry_signature_sha256"] is None
        for item in evaluation
    )


def test_new_candidate_exact_signature_match_is_identity_independent_and_sensitive() -> None:
    authorities, _leakage, _historical = bulk._load_frozen_state_v1(ROOT)
    authority = authorities[0]
    review = json.loads(authority.source_human_review_record_canonical_json)
    review["source_human_review_record_sha256"] = (
        authority.source_human_review_record_sha256
    )
    candidates = bulk.production_pipeline.load_current_non_exact16_candidates_v1(ROOT)
    original = next(
        item for item in candidates
        if item.candidate_identity == review["candidate_identity"]
    )
    effective, _created, reasons = (
        bulk.production_pipeline._approval_effective_candidate_and_authority_v1(
            original, review, (),
        )
    )
    assert effective is not None and not reasons
    fake_identity = replace(
        effective,
        candidate_identity="9ZZZ/TST",
        pdb_id="9ZZZ",
        ligand_comp_id="TST",
    )
    matched = bulk.evaluate_production_exact_authority_v1(
        fake_identity, authorities=authorities,
    )
    assert matched["exact_signature_status"] == "EXACT_SIGNATURE_COMPUTABLE"
    assert matched["candidate_chemistry_signature_sha256"] == (
        authority.chemistry_signature_sha256
    )
    assert matched["exact_authority_match"] is True

    first_bond = fake_identity.pre_reaction_bonds[0]
    changed_order = "double" if first_bond[2] == "single" else "single"
    perturbed = replace(
        fake_identity,
        pre_reaction_bonds=(
            (first_bond[0], first_bond[1], changed_order),
            *fake_identity.pre_reaction_bonds[1:],
        ),
    )
    rejected = bulk.evaluate_production_exact_authority_v1(
        perturbed, authorities=authorities,
    )
    assert rejected["exact_signature_status"] == "EXACT_SIGNATURE_COMPUTABLE"
    assert rejected["candidate_chemistry_signature_sha256"] != (
        authority.chemistry_signature_sha256
    )
    assert rejected["exact_authority_match"] is False


def test_cumulative_leakage_is_loaded_read_only() -> None:
    path = ROOT / bulk.LEAKAGE_REGISTRY_RELATIVE
    before = path.read_bytes()
    _authorities, leakage, historical = bulk._load_frozen_state_v1(ROOT)
    assert len(leakage.groups) == 2 and len(historical) == 16
    assert path.read_bytes() == before


def test_historical_baseline_extension_blocks_without_registry_mutation() -> None:
    historical = {("1ABC", "XYZ")}
    result = bulk.predict_leakage_read_only_v1(
        ("1ABC", "XYZ"), historical=historical,
        frozen_baseline_extension_required=True,
    )
    assert result == (
        "HISTORICAL_BASELINE_COMPONENT",
        "BLOCKED_READ_ONLY",
        "LEAKAGE_BASELINE_EXTENSION_BLOCKED",
    )


def test_new_leakage_evidence_resolves_through_current_policy_read_only() -> None:
    authority_path = ROOT / bulk.AUTHORITY_REGISTRY_RELATIVE
    leakage_path = ROOT / bulk.LEAKAGE_REGISTRY_RELATIVE
    before = (authority_path.read_bytes(), leakage_path.read_bytes())
    authorities, leakage, historical = bulk._load_frozen_state_v1(ROOT)
    context = bulk._load_leakage_prediction_context_v1(
        ROOT, authorities=authorities, leakage_registry=leakage,
    )
    event = _merged_event()
    evidence = {
        "complete": True,
        "ligand_graph_sha256": "1" * 64,
        "ligand_scaffold_sha256": "2" * 64,
        "protein_accession": "TEST_ACCESSION",
        "protein_sequence_sha256": "3" * 64,
        "protein_sequence": "ACDEFGHIKLMNPQRSTVWY",
        "linking_axes": [
            "LIGAND_GRAPH:" + "1" * 64,
            "PROTEIN_EXACT_SEQUENCE:" + "3" * 64,
        ],
    }
    outcome = bulk._terminal_outcome(
        event,
        phases={stage: "PASSED" for stage in bulk.BULK_STAGES},
        route="HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        reasons=("PRE",),
        structural={"leakage_evidence": evidence},
        pre={"status": "PRE_REACTION_UNRESOLVED", "atom_loss_flag": False},
    )
    bulk.apply_leakage_predictions_read_only_v1(
        [outcome], historical=historical, context=context,
    )
    assert outcome["leakage_classification"] == "NEW_EXPANSION_COMPONENT"
    assert outcome["leakage_key"].startswith("COVAPIE_BULK_READ_ONLY_COMPONENT_V1:")
    assert outcome["predicted_group_id"].startswith("COVAPIE_EXPANSION_LEAKAGE_GROUP_")
    assert outcome["predicted_split"] in {"train", "validation", "test"}
    assert (authority_path.read_bytes(), leakage_path.read_bytes()) == before


def test_leakage_lcs_upper_bound_skips_only_impossible_policy_alignment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bulk._policy_global_identity_at_least_half_v1.cache_clear()
    monkeypatch.setattr(
        bulk.production_pipeline.independence_evidence_owner,
        "global_identity",
        lambda *_args: (_ for _ in ()).throw(AssertionError("must be skipped")),
    )
    assert bulk._policy_global_identity_at_least_half_v1("A" * 100, "C" * 100) is False


def test_leakage_reachable_alignment_uses_existing_policy_owner() -> None:
    bulk._policy_global_identity_at_least_half_v1.cache_clear()
    left = "ACDEFGHIKLMNPQRSTVWY"
    right = "ACDEFGHIKLMNPQAAAAAA"
    expected = (
        bulk.production_pipeline.independence_evidence_owner.global_identity(left, right)
        >= 0.5
    )
    assert bulk._policy_global_identity_at_least_half_v1(left, right) is expected


def test_human_review_clustering_is_deterministic() -> None:
    event1 = _merged_event(pdb="9XYZ", comp="XYZ", smiles="CC")
    event2 = _merged_event(pdb="8ABC", comp="ABC", smiles="CC")
    outcome1 = bulk._terminal_outcome(
        event1,
        phases={stage: "PASSED" for stage in bulk.BULK_STAGES},
        route="HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        reasons=("PRE",),
        structural={"ligand_reactive_element": "C"},
        pre={"status": "PRE_REACTION_UNRESOLVED", "atom_loss_flag": False},
    )
    outcome2 = bulk._terminal_outcome(
        event2,
        phases={stage: "PASSED" for stage in bulk.BULK_STAGES},
        route="HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        reasons=("PRE",),
        structural={"ligand_reactive_element": "C"},
        pre={"status": "PRE_REACTION_UNRESOLVED", "atom_loss_flag": False},
    )
    events = {
        event1["canonical_event_id"]: event1,
        event2["canonical_event_id"]: event2,
    }
    left = bulk._cluster_human_review_v1([outcome1, outcome2], events)
    right = bulk._cluster_human_review_v1([outcome2, outcome1], events)
    assert left == right
    assert all(
        item["topology_coherent_for_joint_human_review"] is False
        and item["approvalable_as_one_chemistry_rule"] is False
        for item in left
    )


def _review_outcome(
    event: dict[str, object], *, ccd_sha: str, radius2: str,
    pre_status: str = "PRE_REACTION_UNRESOLVED",
    pre_radius2: str | None = None,
    transformation: str | None = None,
) -> dict[str, object]:
    return bulk._terminal_outcome(
        event,
        phases={stage: "PASSED" for stage in bulk.BULK_STAGES},
        route="HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        reasons=("PRE",),
        structural={
            "ccd_component_graph": {"ccd_component_graph_sha256": ccd_sha},
            "reactive_center_radius2_sha256": radius2,
            "reactive_center_local_topology": "[C:1]-C=O",
        },
        pre={
            "status": pre_status, "atom_loss_flag": False,
            "pre_source_graph_sha256": None,
            "pre_reactive_center_radius2_sha256": pre_radius2,
            "net_pre_adduct_local_transformation_sha256": transformation,
        },
    )


def test_review_unit_collapse_preserves_underlying_event_ids() -> None:
    first = _merged_event(pdb="9XYZ", comp="XYZ")
    second = _merged_event(pdb="8ABC", comp="XYZ")
    outcomes = [
        _review_outcome(first, ccd_sha="1" * 64, radius2="2" * 64),
        _review_outcome(second, ccd_sha="1" * 64, radius2="2" * 64),
    ]
    events = {
        first["canonical_event_id"]: first,
        second["canonical_event_id"]: second,
    }
    units = bulk.build_human_review_units_v1(outcomes, events)
    assert len(units) == 1 and units[0]["event_count"] == 2
    assert units[0]["canonical_event_ids"] == sorted(events)
    assert units[0]["reactive_atom"] == "C1"
    assert units[0]["atom_loss_state"] == "NO_ATOM_LOSS"
    assert units[0]["production_sample_approval_created"] is False


def test_chemistry_aware_clustering_groups_same_local_chemistry_across_scaffolds() -> None:
    first = _merged_event(pdb="9XYZ", comp="XYZ")
    second = _merged_event(pdb="8ABC", comp="ABC")
    outcomes = [
        _review_outcome(
            first, ccd_sha="1" * 64, radius2="3" * 64,
            pre_status="PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED",
            pre_radius2="4" * 64, transformation="5" * 64,
        ),
        _review_outcome(
            second, ccd_sha="2" * 64, radius2="3" * 64,
            pre_status="PRE_COMPONENT_TOPOLOGY_PRESENT_AUTHORITY_UNREVIEWED",
            pre_radius2="4" * 64, transformation="5" * 64,
        ),
    ]
    events = {
        first["canonical_event_id"]: first,
        second["canonical_event_id"]: second,
    }
    units = bulk.build_human_review_units_v1(outcomes, events)
    clusters = bulk.cluster_review_units_v1(
        units, outcomes=outcomes, event_by_id=events,
    )
    assert len(units) == 2 and len(clusters) == 1
    assert clusters[0]["event_count"] == 2
    assert clusters[0]["unique_reactive_center_radius2_fingerprint_count"] == 1
    assert clusters[0]["topology_coherent_for_joint_human_review"] is True
    assert clusters[0]["approvalable_as_one_chemistry_rule"] is True


def test_heterogeneous_local_chemistry_cannot_form_one_approvalable_cluster() -> None:
    first = _merged_event(pdb="9XYZ", comp="XYZ")
    second = _merged_event(pdb="8ABC", comp="ABC")
    outcomes = [
        _review_outcome(first, ccd_sha="1" * 64, radius2="3" * 64),
        _review_outcome(second, ccd_sha="2" * 64, radius2="4" * 64),
    ]
    events = {
        first["canonical_event_id"]: first,
        second["canonical_event_id"]: second,
    }
    units = bulk.build_human_review_units_v1(outcomes, events)
    clusters = bulk.cluster_review_units_v1(
        units, outcomes=outcomes, event_by_id=events,
    )
    assert len(clusters) == 2
    assert not any(
        item["event_count"] == 2
        and item["approvalable_as_one_chemistry_rule"]
        for item in clusters
    )


def test_incompatible_pre_labels_remain_joint_review_but_not_one_rule() -> None:
    first = _merged_event(pdb="9XYZ", comp="XYZ")
    second = _merged_event(pdb="8ABC", comp="ABC")
    first["supporting_warhead_annotations"] = ["α-diazomethyl_Ketone"]
    second["supporting_warhead_annotations"] = ["α-halomethyl_Ketone"]
    outcomes = [
        _review_outcome(
            first, ccd_sha="1" * 64, radius2="3" * 64,
            pre_status="PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        ),
        _review_outcome(
            second, ccd_sha="2" * 64, radius2="3" * 64,
            pre_status="PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        ),
    ]
    events = {
        first["canonical_event_id"]: first,
        second["canonical_event_id"]: second,
    }
    units = bulk.build_human_review_units_v1(outcomes, events)
    clusters = bulk.cluster_review_units_v1(
        units, outcomes=outcomes, event_by_id=events,
    )
    assert len(units) == 2 and len(clusters) == 1
    assert clusters[0]["supporting_source_annotations"] == [
        "α-diazomethyl_Ketone", "α-halomethyl_Ketone",
    ]
    assert clusters[0]["topology_coherent_for_joint_human_review"] is True
    assert clusters[0]["approvalable_as_one_chemistry_rule"] is False


def test_structure_cache_origin_counts_are_mutually_interpretable() -> None:
    rows = [
        {
            "acquisition_status": "SOURCE_VERIFIED",
            "compressed_byte_count": 10,
            "compressed_sha256": "1" * 64,
            "cache_reuse_status": "DOWNLOADED_BY_BULK_PILOT",
        },
        {
            "acquisition_status": "SOURCE_VERIFIED",
            "compressed_byte_count": 20,
            "compressed_sha256": "2" * 64,
            "cache_reuse_status": "REUSED_FROM_TASK_CACHE",
        },
        {
            "acquisition_status": "SOURCE_ACQUISITION_OR_VALIDATION_FAILED",
            "compressed_byte_count": 0,
            "compressed_sha256": None,
            "cache_reuse_status": "FAILED",
        },
    ]
    counts = bulk._structure_cache_origin_counts_v1(rows)
    assert counts == {
        "structure_payload_count": 2,
        "structure_source_verified_count": 2,
        "structure_cache_origin_downloaded_count": 1,
        "structure_cache_origin_reused_count": 1,
        "structures_downloaded_count": 1,
        "structures_reused_from_cache_count": 1,
    }
    assert (
        counts["structure_cache_origin_downloaded_count"]
        + counts["structure_cache_origin_reused_count"]
        == counts["structure_payload_count"]
        == counts["structure_source_verified_count"]
    )
    invalid = deepcopy(rows)
    invalid[0]["cache_reuse_status"] = "CURRENT_INVOCATION_REUSED"
    with pytest.raises(ValueError, match="CACHE_ORIGIN_INVALID"):
        bulk._structure_cache_origin_counts_v1(invalid)


def test_summary_reconciliation_success_and_failure() -> None:
    summary = {
        "canonical_unique_event_count": 2,
        "known_existing_event_count": 1,
        "new_unique_candidate_event_count": 1,
        "events_with_1_source": 1,
        "events_with_2_sources": 1,
        "events_with_3_sources": 0,
        "events_with_4_sources": 0,
        "all_source_normalized_record_count": 5,
        "records_without_canonical_event_identity_count": 1,
        "cross_source_duplicate_record_count": 2,
        "terminal_route_counts": {
            route: (2 if route == "STRUCTURAL_EVIDENCE_INCOMPLETE" else 0)
            for route in bulk.TERMINAL_ROUTES
        },
    }
    bulk.validate_summary_reconciliation_v1(summary)
    summary["new_unique_candidate_event_count"] = 2
    with pytest.raises(ValueError, match="KNOWN_NEW"):
        bulk.validate_summary_reconciliation_v1(summary)


def test_no_production_materialization_or_registry_write_in_outcome() -> None:
    event = _merged_event()
    outcome = bulk._terminal_outcome(
        event,
        phases={stage: "PASSED" for stage in bulk.BULK_STAGES},
        route="HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        reasons=("PRE",),
    )
    assert outcome["production_materialization_performed"] is False
    assert outcome["temporary_materialization_performed"] is False
    assert outcome["temporary_tensorization_performed"] is False


def test_canonical_json_replay_is_byte_identical() -> None:
    value = {"b": [2, 1], "a": {"x": True}}
    assert bulk._canonical_json(value) == bulk._canonical_json(deepcopy(value))
    assert bulk._canonical_json(value).endswith(b"\n")


def test_full_canonical_artifact_replay_is_byte_identical_and_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / bulk.REPOSITORY_OUTPUT_RELATIVE
    output.mkdir(parents=True)
    expected = {
        name: bulk._canonical_json({"artifact": name})
        for name in bulk.OUTPUT_FILENAMES
    }
    for name, payload in expected.items():
        (output / name).write_bytes(payload)
    monkeypatch.setattr(
        bulk, "build_covapie_bulk_cys_sg_dataset_expansion_artifacts_v1",
        lambda **_kwargs: dict(expected),
    )
    replay = bulk.verify_repository_output_determinism_v1(
        repo_root=tmp_path, cache_root=tmp_path / "cache",
    )
    assert set(replay) == set(bulk.OUTPUT_FILENAMES)
    changed = dict(expected)
    changed[bulk.OUTPUT_FILENAMES[0]] = b"{}\n"
    monkeypatch.setattr(
        bulk, "build_covapie_bulk_cys_sg_dataset_expansion_artifacts_v1",
        lambda **_kwargs: changed,
    )
    with pytest.raises(ValueError, match="NOT_BYTE_IDENTICAL"):
        bulk.verify_repository_output_determinism_v1(
            repo_root=tmp_path, cache_root=tmp_path / "cache",
        )


def test_real_revision_keeps_production_population_at_19() -> None:
    summary_path = ROOT / bulk.REPOSITORY_OUTPUT_RELATIVE / "bulk_summary_v1.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["authorized_data_population_before"] == 19
    assert summary["authorized_data_population_after"] == 19
    assert summary["production_trainable_new_sample_count"] == 0
    assert summary["production_materialization_performed"] is False
    assert summary["production_approval_written"] is False


def test_real_revision_has_unambiguous_cache_and_cluster_readiness_semantics() -> None:
    output = ROOT / bulk.REPOSITORY_OUTPUT_RELATIVE
    summary = json.loads(
        (output / "bulk_summary_v1.json").read_text(encoding="utf-8")
    )
    assert summary["cache_count_semantics_fixed"] is True
    assert summary["structure_payload_count"] == 175
    assert summary["structure_source_verified_count"] == 175
    assert summary["structure_cache_origin_downloaded_count"] == 175
    assert summary["structure_cache_origin_reused_count"] == 0
    assert (
        summary["structure_cache_origin_downloaded_count"]
        + summary["structure_cache_origin_reused_count"]
        == summary["structure_payload_count"]
        == summary["structure_source_verified_count"]
    )
    assert summary["feature_semantics_audit_completed"] is True
    assert summary["feature_semantics_known"] is True
    assert summary["unknown_atom_feature_policy_resolved"] is True
    assert summary["unknown_atom_policy_contract_resolved"] is True
    assert summary["feature_semantics_reopened"] is False
    assert summary["ready_for_full_training"] is False
    assert summary["ready_for_full_training_false_reason"] == (
        "LATER_TRAINING_PATH_OR_MIXED_RUNTIME_INTEGRATION_"
        "NOT_FEATURE_SEMANTICS"
    )

    cluster_artifact = json.loads(
        (output / "bulk_human_review_clusters_v1.json").read_text(
            encoding="utf-8"
        )
    )
    clusters = {item["cluster_id"]: item for item in cluster_artifact["clusters"]}
    for cluster_id in (
        "COVAPIE_BULK_REVIEW_CLUSTER_5848E0872E43A143",
        "COVAPIE_BULK_REVIEW_CLUSTER_6CE4B62C4537F70D",
    ):
        assert clusters[cluster_id][
            "topology_coherent_for_joint_human_review"
        ] is True
        assert clusters[cluster_id][
            "approvalable_as_one_chemistry_rule"
        ] is False
