from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_covpdb_complex_card_metadata_acquisition_smoke as smoke


SYNTHETIC_FOUND_HTML = """
<html><head><style>.x{display:none}</style><script>raw pdb sdf zip</script></head>
<body>
<table>
<tr><th>Chain ID</th><td>A</td></tr>
<tr><th>Residue name</th><td>CYS</td></tr>
<tr><th>Residue number</th><td>145</td></tr>
<tr><th>Residue atom</th><td>SG</td></tr>
<tr><th>Covalent bond</th><td>SG-C10</td></tr>
<tr><th>Mechanism</th><td>Michael addition</td></tr>
<tr><th>Warhead</th><td>acrylamide</td></tr>
</table>
</body></html>
"""

SYNTHETIC_AMBIGUOUS_HTML = """
<html><body>
Chain: A; Chain: B
Residue name: CYS
Residue number: 145
Residue atom: SG
Covalent bond: SG-C10
</body></html>
"""

SYNTHETIC_MISSING_HTML = "<html><body><p>Protein card without event-key labels.</p></body></html>"


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    assert smoke.MANIFEST_JSON.is_file(), "Run the Step 13AS check script before artifact read-only tests"
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_synthetic_parser_finds_event_key_fields() -> None:
    text, links = smoke.parse_visible_text_and_links(SYNTHETIC_FOUND_HTML)
    assert links == []
    assert "raw pdb sdf zip" not in text
    assert smoke.find_label_evidence(text, "chain")["label_found"] is True
    assert smoke.find_label_evidence(text, "mechanism")["label_found"] is True
    assert smoke.probe_event_field(text, "chain_id")["field_probe_status"] == "found"
    assert smoke.probe_event_field(text, "chain_id")["parsed_value"] == "A"
    assert smoke.probe_event_field(text, "residue_name")["parsed_value"] == "CYS"
    assert smoke.probe_event_field(text, "residue_index")["parsed_value"] == "145"
    assert smoke.probe_event_field(text, "residue_atom_name")["parsed_value"] == "SG"
    assert smoke.probe_event_field(text, "covalent_bond_atom_pair")["parsed_value"] == "SG-C10"


def test_synthetic_parser_does_not_fabricate_missing_fields() -> None:
    text, _ = smoke.parse_visible_text_and_links(SYNTHETIC_MISSING_HTML)
    for field in smoke.CRITICAL_EVENT_KEY_FIELDS:
        probe = smoke.probe_event_field(text, field)
        assert probe["field_probe_status"] == "not_found"
        assert probe["parsed_value"] == ""
        assert probe["parse_confidence"] == "none"


def test_synthetic_parser_marks_ambiguous_fields() -> None:
    text, _ = smoke.parse_visible_text_and_links(SYNTHETIC_AMBIGUOUS_HTML)
    chain = smoke.probe_event_field(text, "chain_id")
    assert chain["field_probe_status"] == "ambiguous"
    assert chain["parsed_value"] == "A;B"
    assert smoke.probe_event_field(text, "residue_name")["field_probe_status"] == "found"


def test_committed_artifacts_are_read_only_and_have_expected_counts() -> None:
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["attempted_card_count"] == 5
    assert manifest["first_5_complex_card_urls"] == smoke.EXPECTED_FIRST_5_URLS
    assert manifest["full_html_written"] is False
    assert manifest["raw_html_artifact_written"] is False
    assert manifest["raw_structure_downloaded"] is False
    assert manifest["raw_ligand_downloaded"] is False
    assert manifest["candidate_metadata_materialized"] is False
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert len(_csv_rows(smoke.FETCH_AUDIT_CSV)) == 5
    assert len(_csv_rows(smoke.HTML_METADATA_SAFETY_AUDIT_CSV)) == 5
    assert len(_csv_rows(smoke.EVENT_FIELD_PROBE_CSV)) == 25
    assert len(_csv_rows(smoke.EVENT_KEY_RESOLUTION_AUDIT_CSV)) == 5


def test_fetch_safety_and_snippet_contracts() -> None:
    fetch = _csv_rows(smoke.FETCH_AUDIT_CSV)
    safety = _csv_rows(smoke.HTML_METADATA_SAFETY_AUDIT_CSV)
    snippets = _csv_rows(smoke.EVIDENCE_SNIPPET_AUDIT_CSV)
    assert [row["complex_card_url"] for row in fetch] == smoke.EXPECTED_FIRST_5_URLS
    assert {row["url_allowed"] for row in fetch} == {"True"}
    assert {row["fetch_attempted"] for row in fetch} == {"True"}
    assert {row["full_html_written"] for row in fetch} == {"False"}
    assert {row["raw_download_attempted"] for row in fetch} == {"False"}
    assert {row["download_links_followed"] for row in fetch} == {"False"}
    assert {row["raw_html_artifact_written"] for row in safety} == {"False"}
    assert {row["forbidden_suffix_url_requested"] for row in safety} == {"False"}
    assert {row["forbidden_suffix_links_followed"] for row in safety} == {"False"}
    assert {row["external_raw_links_followed"] for row in safety} == {"False"}
    assert {row["raw_structure_downloaded"] for row in safety} == {"False"}
    assert {row["raw_ligand_downloaded"] for row in safety} == {"False"}
    for row in snippets:
        assert int(row["snippet_length"]) <= 240
        assert row["evidence_snippet_audit_passed"] == "True"


def test_resolution_and_readiness_boundaries() -> None:
    manifest = _manifest()
    resolution = _csv_rows(smoke.EVENT_KEY_RESOLUTION_AUDIT_CSV)
    readiness = {row["readiness_item"]: row for row in _csv_rows(smoke.READINESS_BOUNDARY_AUDIT_CSV)}
    assert len(resolution) == 5
    assert {row["candidate_metadata_can_proceed"] for row in resolution} == {"False"}
    assert {row["candidate_allowlist_can_proceed"] for row in resolution} == {"False"}
    assert manifest["future_candidate_metadata_possible_count"] == manifest["minimal_event_key_resolved_card_count"]
    assert manifest["future_automatic_allowlist_possible_count"] == manifest["preferred_event_key_resolved_card_count"]
    assert readiness["ready_for_covapie_covpdb_complex_card_metadata_acquisition_qa_gate"]["current_step_status"] == "True"
    assert readiness["ready_for_covapie_candidate_metadata_materialization"]["current_step_status"] == "False"
    assert readiness["ready_for_covapie_candidate_allowlist_materialization_smoke"]["current_step_status"] == "False"
    assert readiness["ready_for_covapie_batch_scale_raw_read_smoke"]["current_step_status"] == "False"
    assert readiness["ready_for_training"]["current_step_status"] == "False"
    assert readiness["ready_to_train_now"]["current_step_status"] == "False"


def test_no_forbidden_runtime_imports_and_canonical_masks() -> None:
    module_path = Path("src/covalent_ext/covapie_covpdb_complex_card_metadata_acquisition_smoke.py")
    script_path = Path("scripts/check_covapie_covpdb_complex_card_metadata_acquisition_smoke_v0.py")
    for name in ["requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    assert _imports_name(module_path, "urllib")
    mask = _csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == smoke.CANONICAL_MASK_TASK_ALIASES
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
