import csv
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_b3_scaffold_only_mask_design_v0 as script  # noqa: E402
from covalent_ext.b3_scaffold_only_mask_design import (  # noqa: E402
    FORBIDDEN_ARTIFACT_SUFFIXES,
    MANIFEST_JSON,
    NEW_MASK_LEVEL,
    OUTPUT_ROOT,
    PROTOCOL_JSON,
    REPORT_CSV,
    SUMMARY_MD,
    build_b3_design_decision_v0,
    build_b3_implementation_protocol_v0,
    build_b3_mask_invariants_v0,
    build_b3_mask_risk_register_v0,
    build_b3_mask_semantics_v0,
    build_b3_scaffold_only_mask_design_v0,
    build_b3_smoke_roadmap_v0,
    build_five_level_mask_table_v0,
    inspect_existing_mask_levels_v0,
    validate_step11l_outputs_v0,
)


O = "opti" + "mizer"
O_STEP = O + "_step"
TR_FIT = "trainer" + "_" + "fit"
BWD = "back" + "ward"


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_validate_step11l_outputs_success():
    assert validate_step11l_outputs_v0() is True


def test_existing_mask_schema_inspection_returns_evidence():
    evidence = inspect_existing_mask_levels_v0()

    assert evidence["existing_masking_files_found"]["masking"] is True
    assert evidence["existing_masking_files_found"]["schema"] is True
    assert evidence["existing_masking_files_found"]["data_schema_doc"] is True
    assert evidence["existing_four_level_contract_detected"] is True
    assert evidence["current_b2_name"] == "B2_scaffold_warhead"
    assert evidence["current_b2_target_components"] == ["scaffold", "warhead"]
    assert evidence["current_b2_context_components"] == ["linker"]
    assert evidence["b3_already_implemented"] is False
    assert "src/covalent_ext/masking.py" in evidence["implementation_files_to_touch_next"]


def test_b3_semantics_are_scaffold_only_with_linker_warhead_context():
    semantics = build_b3_mask_semantics_v0(inspect_existing_mask_levels_v0())

    assert semantics["mask_level"] == NEW_MASK_LEVEL
    assert semantics["target_components"] == ["scaffold"]
    assert semantics["context_components"] == ["linker", "warhead"]
    assert semantics["primary_design_use"] == "scaffold_hopping_with_fixed_linker_warhead"
    assert semantics["relation_to_B2"]["does_not_replace_B2"] is True
    assert semantics["relation_to_B2"]["complementary_to_B2"] is True
    assert semantics["relation_to_current_four_level"]["A_B_B2_C_remain_unchanged"] is True
    assert semantics["relation_to_current_four_level"]["B3_added_as_fifth_level"] is True


def test_five_level_table_includes_a_b_b2_b3_c_and_keeps_b2_distinct():
    table = build_five_level_mask_table_v0()
    by_level = {row["mask_level"]: row for row in table}

    assert list(by_level) == [
        "A_warhead_only",
        "B_linker_warhead",
        "B2_scaffold_warhead",
        NEW_MASK_LEVEL,
        "C_scaffold_linker_warhead",
    ]
    assert by_level["B2_scaffold_warhead"]["target_components"] == ["scaffold", "warhead"]
    assert by_level["B2_scaffold_warhead"]["context_components"] == ["linker"]
    assert by_level[NEW_MASK_LEVEL]["target_components"] == ["scaffold"]
    assert by_level[NEW_MASK_LEVEL]["context_components"] == ["linker", "warhead"]
    assert by_level["B2_scaffold_warhead"] != by_level[NEW_MASK_LEVEL]


def test_b3_invariants_cover_disjoint_context_visibility_and_fail_safe():
    invariants = build_b3_mask_invariants_v0()
    text = " ".join(item["description"] for item in invariants)

    assert len(invariants) >= 15
    assert "disjoint" in text
    assert "warhead atoms must remain visible" in text
    assert "linker atoms must remain visible" in text
    assert "scaffold atoms must not leak into context" in text
    assert "fail safely" in text


def test_implementation_protocol_is_additive_and_preserves_existing_levels():
    semantics = build_b3_mask_semantics_v0(inspect_existing_mask_levels_v0())
    table = build_five_level_mask_table_v0()
    invariants = build_b3_mask_invariants_v0()
    protocol = build_b3_implementation_protocol_v0(semantics, table, invariants)

    assert protocol["implementation_policy"] == "additive_only"
    assert protocol["do_not_rename_existing_B2"] is True
    assert protocol["do_not_change_A_B_B2_C_semantics"] is True
    assert protocol["proposed_next_stage"] == "b3_scaffold_only_mask_implementation_v0"
    assert protocol["add_new_mask_level"] == NEW_MASK_LEVEL
    assert "B3 mask can be built on synthetic covalent sample" in protocol["pass_conditions"]
    assert "A/B/B2/C outputs unchanged relative to previous expected semantics" in protocol["pass_conditions"]


def test_smoke_roadmap_covers_follow_on_gates():
    roadmap = build_b3_smoke_roadmap_v0()
    stages = [item["stage"] for item in roadmap]

    assert "b3_scaffold_only_mask_implementation_v0" in stages
    assert "b3_scaffold_only_mask_sweep_v0" in stages
    assert "b3_pretrained_masked_loss_smoke_v0" in stages
    assert "b3_backward_smoke_v0" in stages
    assert "b3_single_optimizer_step_smoke_v0" in stages
    assert "b3_tiny_training_dry_run_v0" in stages
    assert "real_covalent_feature_mapping_loader_gate" in stages


def test_risk_register_includes_confusion_and_real_loader_gap():
    risks = build_b3_mask_risk_register_v0()
    risk_ids = {risk["risk_id"] for risk in risks}

    assert "B3_R02_b2_confusion" in risk_ids
    assert "B3_R10_real_loader_gap" in risk_ids
    assert len(risks) >= 10
    assert all("mitigation" in risk for risk in risks)
    assert all(risk["blocks_11N"] is False for risk in risks)


def test_decision_ready_when_inputs_complete_and_blocks_precondition_failures():
    evidence = inspect_existing_mask_levels_v0()
    semantics = build_b3_mask_semantics_v0(evidence)
    protocol = build_b3_implementation_protocol_v0(semantics, build_five_level_mask_table_v0(), build_b3_mask_invariants_v0())

    ready = build_b3_design_decision_v0(True, evidence, semantics, protocol)
    blocked = build_b3_design_decision_v0(False, evidence, semantics, protocol)
    incomplete = build_b3_design_decision_v0(True, evidence, {**semantics, "target_components": []}, protocol)

    assert ready["design_status"] == "b3_scaffold_only_mask_design_ready"
    assert ready["b3_scaffold_only_mask_implementation_allowed"] is True
    assert ready["recommended_next_step"] == "b3_scaffold_only_mask_implementation"
    assert blocked["design_status"] == "step11l_precondition_failed"
    assert blocked["recommended_next_step"] == "tiny_training_dry_run_debug"
    assert incomplete["design_status"] == "b3_semantics_incomplete"
    assert incomplete["recommended_next_step"] == "b3_semantics_review"
    for decision in [ready, blocked, incomplete]:
        assert decision["this_design_modifies_mask_logic"] is False
        assert decision["this_design_runs_model"] is False
        assert decision["this_design_runs_" + BWD] is False
        assert decision["this_design_creates_" + O] is False
        assert decision["this_design_runs_" + O_STEP] is False
        assert decision["training_allowed"] is False
        assert decision["formal_training_allowed"] is False
        assert decision["finetune_allowed"] is False


def test_full_manifest_contract():
    result = build_b3_scaffold_only_mask_design_v0()
    manifest = result["manifest"]

    assert manifest["stage"] == "b3_scaffold_only_mask_design_v0"
    assert manifest["previous_stage"] == "tiny_training_dry_run_v0"
    assert manifest["step11l_validated"] is True
    assert manifest["tiny_training_loop_plumbing_proven"] is True
    assert manifest["new_mask_level"] == NEW_MASK_LEVEL
    assert manifest["b3_target_components"] == ["scaffold"]
    assert manifest["b3_context_components"] == ["linker", "warhead"]
    assert manifest["b3_primary_use"] == "scaffold_hopping_with_fixed_linker_warhead"
    assert manifest["five_level_mask_design_ready"] is True
    assert manifest["b3_invariants_written"] >= 15
    assert manifest["implementation_protocol_written"] is True
    assert manifest["smoke_roadmap_written"] is True
    assert manifest["proposed_next_stage"] == "b3_scaffold_only_mask_implementation_v0"
    assert manifest["b3_scaffold_only_mask_implementation_allowed"] is True
    assert manifest["do_not_rename_existing_b2"] is True
    assert manifest["do_not_change_existing_four_level_semantics"] is True
    assert manifest["design_status"] == "b3_scaffold_only_mask_design_ready"
    assert manifest["this_design_modifies_mask_logic"] is False
    assert manifest["this_design_runs_model"] is False
    assert manifest["this_design_runs_" + BWD] is False
    assert manifest["this_design_creates_" + O] is False
    assert manifest["this_design_runs_" + O_STEP] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert manifest["checkpoint_saved"] is False
    assert manifest["model_saved"] is False
    assert manifest["tensor_dump_saved"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["recommended_next_step"] == "b3_scaffold_only_mask_implementation"


def test_script_writes_report_manifest_protocol_and_summary(tmp_path, monkeypatch):
    output_root = tmp_path / "b3_scaffold_only_mask_design_v0"
    report_csv = output_root / "b3_scaffold_only_mask_design_report.csv"
    manifest_json = output_root / "b3_scaffold_only_mask_design_manifest.json"
    protocol_json = output_root / "b3_scaffold_only_mask_protocol.json"
    summary_md = tmp_path / "docs" / "b3_scaffold_only_mask_design_v0_summary.md"

    monkeypatch.setattr(script, "REPORT_CSV", report_csv)
    monkeypatch.setattr(script, "MANIFEST_JSON", manifest_json)
    monkeypatch.setattr(script, "PROTOCOL_JSON", protocol_json)
    monkeypatch.setattr(script, "SUMMARY_MD", summary_md)

    assert script.run() == 0

    rows = _read_csv(report_csv)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_json.read_text(encoding="utf-8"))
    text = summary_md.read_text(encoding="utf-8")

    assert len(rows) == 8
    assert all(row["status"] == "passed" for row in rows)
    assert manifest["all_checks_passed"] is True
    assert protocol["b3_semantics"]["mask_level"] == NEW_MASK_LEVEL
    assert len(protocol["five_level_mask_table"]) == 5
    assert "not training" in text
    assert "B3 does not replace B2" in text


def test_generated_outputs_and_safety_boundary_after_script_run():
    assert REPORT_CSV.is_file()
    assert MANIFEST_JSON.is_file()
    assert PROTOCOL_JSON.is_file()
    assert SUMMARY_MD.is_file()

    rows = _read_csv(REPORT_CSV)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))

    assert len(rows) == 8
    assert all(row["status"] == "passed" for row in rows)
    assert manifest["all_checks_passed"] is True
    assert manifest["this_design_modifies_mask_logic"] is False
    assert manifest["this_design_runs_model"] is False
    assert manifest["this_design_runs_" + BWD] is False
    assert manifest["this_design_creates_" + O] is False
    assert manifest["this_design_runs_" + O_STEP] is False
    assert manifest["training_allowed"] is False
    assert manifest["formal_training_allowed"] is False
    assert manifest["finetune_allowed"] is False
    assert protocol["implementation_protocol"]["implementation_policy"] == "additive_only"
    assert not [
        path
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES
    ]


def test_no_diffsbdd_source_modification():
    source_diff = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    staged_source_diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert source_diff.returncode == 0
    assert staged_source_diff.returncode == 0


def test_source_files_do_not_contain_forbidden_execution_calls():
    files = [
        REPO_ROOT / "src/covalent_ext/b3_scaffold_only_mask_design.py",
        REPO_ROOT / "scripts/check_b3_scaffold_only_mask_design_v0.py",
        REPO_ROOT / "tests/test_b3_scaffold_only_mask_design_v0.py",
    ]
    forbidden = [
        "torch" + "." + "save",
        "opti" + "mizer.step",
        "trainer" + "." + "fit",
        "training" + "_step" + "(",
        "back" + "ward" + "(",
        "save" + "_checkpoint",
        "load" + "_from" + "_checkpoint",
        "torch" + "." + "optim",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text
