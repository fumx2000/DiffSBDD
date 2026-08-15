from __future__ import annotations

import copy
import inspect
import json
import stat
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1 as context,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_v1 as adapter,
)
from scripts import (
    check_covapie_current11_task2_batch_index_remap_adapter_context_v1 as checker,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = REPO_ROOT.parent / "covapie-state"


@pytest.fixture(scope="module")
def audit() -> tuple[dict[str, object], dict[str, object]]:
    return checker._candidate_audit(repo_root=REPO_ROOT, state_root=STATE_ROOT)


def test_public_api_exact2_and_keyword_only() -> None:
    assert context.__all__ == (
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        "remap_covapie_current11_task2_batch_index_with_context_v1",
    )
    build = getattr(context, context.__all__[0])
    fast = getattr(context, context.__all__[1])
    assert str(inspect.signature(build)) == (
        "(*, repo_root: 'Path', state_root: 'Path') -> 'object'"
    )
    assert str(inspect.signature(fast)) == (
        "(*, context: 'object', adapter_input: 'dict[str, object]') -> "
        "'dict[str, object]'"
    )
    with pytest.raises(TypeError):
        build(REPO_ROOT, STATE_ROOT)
    with pytest.raises(TypeError):
        fast({}, {})


def test_single_error_token_and_no_public_context_class(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, internal = audit
    assert report["error_token"] == (
        "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_CONTEXT_V1_ERROR"
    )
    assert not hasattr(context, "AdapterContext")
    assert not hasattr(context, "Context")
    with pytest.raises(ValueError, match=f"^{context.ERROR_TOKEN}$"):
        context.remap_covapie_current11_task2_batch_index_with_context_v1(
            context=internal["first_context"],
            adapter_input=[],
        )


def test_repository_exact4_safety_and_identities(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, internal = audit
    identities = internal["api"]["repository_exact4_identities"]
    assert [row["relative_path"] for row in identities] == list(
        context.REPOSITORY_EXACT4
    )
    assert len(identities) == 4
    for row in identities:
        path = REPO_ROOT / row["relative_path"]
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert b"\0" not in payload and b"\r" not in payload
    lifecycle = context._repository_lifecycle(REPO_ROOT)
    assert lifecycle in (
        "precommit-untracked",
        "clean-tracked-successor",
    )
    assert report["repository_lifecycle"] == lifecycle


def test_fifth_repository_file_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = "\n".join(
        [*(f"?? {name}" for name in context.REPOSITORY_EXACT4), "?? fifth.txt"]
    )

    def fake_git(unused_root: Path, arguments: tuple[str, ...]) -> str:
        if arguments == ("branch", "--show-current"):
            return "main\n"
        if arguments[:2] in (("cat-file", "-e"), ("merge-base", "--is-ancestor")):
            return ""
        if arguments == ("status", "--porcelain=v1", "--untracked-files=all"):
            return expected + "\n"
        if arguments[:2] == ("ls-files", "--stage"):
            return ""
        raise AssertionError(arguments)

    monkeypatch.setattr(context, "_run_git", fake_git)
    with pytest.raises(context._ContextInvariantError):
        context._repository_lifecycle(REPO_ROOT)


def test_public_precommit_lifecycle_fails_before_all_predecessors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        context,
        "_repository_lifecycle",
        lambda unused: "precommit-untracked",
    )
    counts = checker._public_precommit_negative(
        repo_root=REPO_ROOT,
        state_root=STATE_ROOT,
    )
    assert counts == {
        "reconciliation": 0,
        "successor": 0,
        "B2": 0,
    }


def test_clean_lifecycle_simulation_exact_call_graph(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    simulation = report["clean_lifecycle_simulation"]
    assert simulation["clean_lifecycle_simulation_passed"] is True
    assert simulation["reconciliation_public_call_count"] == 1
    assert simulation["successor_public_call_count"] == 1
    assert simulation["formal_before_after_call_count"] == 2
    assert simulation["context_direct_B2_call_count"] == 0
    lifecycle = report["repository_lifecycle"]
    if lifecycle == "precommit-untracked":
        assert simulation["real_predecessor_calls_replaced_by_fixture"] is True
        assert "successor_internal_B2_call_count" not in simulation
    elif lifecycle == "clean-tracked-successor":
        assert simulation["real_predecessor_calls_replaced_by_fixture"] is False
        assert simulation["successor_internal_B2_call_count"] == 1
    else:
        pytest.fail(f"unexpected repository lifecycle: {lifecycle!r}")


def test_predecessor_acquisition_harness_matches_repository_lifecycle(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    harness = report["fixture_harness"]
    assert harness["predecessor_public_call_counts"] == {
        "reconciliation": 1,
        "successor": 1,
        "B2": 1,
    }
    assert harness["patch_restoration_passed"] is True
    assert harness["production_monkeypatch_used"] is False
    lifecycle = report["repository_lifecycle"]
    if lifecycle == "precommit-untracked":
        assert harness["test_harness_only"] is True
    elif lifecycle == "clean-tracked-successor":
        assert harness["test_harness_only"] is False
        assert harness["formal_before_after_call_count"] == 2
        assert harness["counter_wrappers_delegated_originals"] is True
    else:
        pytest.fail(f"unexpected repository lifecycle: {lifecycle!r}")


def test_owner_identities_and_frozen_helper_contracts(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    owners = {row["owner_name"]: row for row in report["owner_identities"]}
    assert owners["published_hot_loop_contract_gate"]["sha256"] == (
        "5acc793c40d1a899371fd08a02713cd8f1d6105cce04d177317bf03bbdb3cd29"
    )
    assert owners["published_output17_reconciliation_gate"]["sha256"] == (
        "15f639ef955a975cbfbeebce9bde452ee65d4acdf67b2feec56871786603e1de"
    )
    assert owners["published_remap_predecessor_successor"]["sha256"] == (
        "c1e4b207a6432b6495d85fb799a196cb2370edd41402000fbfcbfcf3514acb05"
    )
    assert owners["current_public_runtime_adapter"]["sha256"] == (
        "d09bd5648a3c47851efd933fa8c0523c4ab7c67f8cce765b08fb8423a4e57dd2"
    )
    assert len(report["frozen_adapter_helper_exact6"]) == 6
    assert len(report["successor_parser_helper_exact5"]) == 5


def test_reconciliation_and_successor_artifacts_independently_validated(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, internal = audit
    reconciliation = report["reconciliation_evidence"]
    successor = report["successor_evidence"]
    assert reconciliation["stable_contract_digest"] == context.RECONCILIATION_DIGEST
    assert reconciliation["runtime_target"] == context.RUNTIME_TARGET
    assert reconciliation["runtime_success_whole_exact"] is True
    assert reconciliation["runtime_failure_whole_exact"] is True
    assert reconciliation["historical_failure_runtime_golden"] is False
    assert reconciliation["failure_normalization_forbidden"] is True
    assert successor["stable5_digest"] == context.SUCCESSOR_STABLE5_DIGEST
    assert successor["B2_transition_consumed_and_passed"] is True
    assert successor["production_monkeypatch_used"] is False
    assert context._HISTORICAL_REPORT_NAME not in internal["successor_artifacts"]


def test_successor_aware_parser_exact11_exact22_and_atom_exact8(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, internal = audit
    parser = report["successor_parser_evidence"]
    assert parser == {
        "source_sample_count": 11,
        "authority_table_count": 11,
        "authority_role_count": 22,
        "selected_atom_identity_field_count": 8,
    }
    parsed = context._parse_successor_stable5_v1(internal["successor_artifacts"])
    for index, table in enumerate(parsed["authority_tables"]):
        assert table["sample_identity"]["source_sample_index"] == index
        assert tuple(table["roles"]) == ("pocket", "ligand")
        for role in table["roles"].values():
            source_row = role["selected_source_row_index_0based"]
            assert role["source_to_parser_local"] == {
                str(source_row): role["selected_parser_local_index"]
            }


def test_private_context_logical_exact20_formal_and_freshness(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, internal = audit
    value = context._logical_context_value(internal["first_context"])
    assert tuple(value) == context._LOGICAL_FIELD_ORDER
    assert len(value) == 20
    assert value["context_schema_version"] == context.CONTEXT_SCHEMA_VERSION
    assert value["context_contract_version"] == context.CONTEXT_CONTRACT_VERSION
    assert value["runtime_output17_target"] == context.RUNTIME_TARGET
    assert value["context_freshness_model"] == "explicit_rebuild_by_owner"
    formal = value["formal_authority_identity"]
    assert set(formal) == {
        "canonical_relative_path",
        "canonical_readlink",
        "formal_aggregate_sha256",
        "formal_snapshot_sha256",
        "formal_exact4_sha256",
    }
    assert not set(formal) & {
        "st_dev",
        "inode",
        "mount_id",
        "parent_mount_id",
        "mtime",
        "pid",
    }
    assert report["context_evidence"]["formal_validation_count_per_context"] == 2


def test_context_deep_immutable_sealed_and_deterministic(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, internal = audit
    first = internal["first_context"]
    second = internal["second_context"]
    assert type(first) is context._AdapterContext
    assert first is not second
    assert first._seal == second._seal
    assert type(first._semantic) is context._FrozenDictionary
    assert report["context_evidence"]["two_context_object_identities_distinct"] is True
    assert report["context_evidence"]["same_authority_seal_deterministic"] is True
    assert all(report["context_tamper_matrix"].values())


def test_fast_success_whole_slow_public_output17_parity(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    matrix = report["fast_parity_matrix"]
    assert matrix["canonical_success"] is True
    assert matrix["subset_10_4_0"] is True
    assert matrix["no_joint"] is True
    assert report["fast_parity_evidence"]["caller_inputs_unchanged"] is True
    assert report["fast_parity_evidence"]["context_unchanged"] is True
    assert report["fast_parity_evidence"]["output_exact17_only"] is True


def test_fast_failure_whole_slow_public_output17_parity_without_normalization(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    matrix = report["fast_parity_matrix"]
    assert matrix["schema_mismatch"] is True
    assert matrix["hard_failure_entry2"] is True
    assert matrix["hard_failure_entry2_preserved"] is True
    assert (
        report["fast_parity_evidence"][
            "historical_failure_normalization_performed"
        ]
        is False
    )


def test_fast_input_and_output_are_fresh_builtins(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    unused_report, internal = audit
    case = checker._canonical_input(internal["first_context"], order=[10, 4, 0])
    before = copy.deepcopy(case)
    output = context.remap_covapie_current11_task2_batch_index_with_context_v1(
        context=internal["first_context"],
        adapter_input=case,
    )
    assert case == before
    assert type(output) is dict
    assert tuple(output) == adapter._OUTPUT_FIELD_ORDER
    assert len(output) == 17
    assert all(type(pair) is list for pair in output["pair_values_source_row_indices"])


def test_fast_no_io_exact15_and_no_adapter_public(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    counts = report["fast_no_io_contract_counts"]
    assert len(counts) == 15
    assert set(counts.values()) == {0}
    assert report["adapter_public_fast_path_count"] == 0
    assert counts["reconciliation_public_build_count"] == 0
    assert counts["successor_public_build_count"] == 0
    assert counts["B2_public_build_count"] == 0
    assert counts["report_generation_count"] == 0
    assert counts["global_cache_lookup_count"] == 0


def test_source_architecture_reuses_frozen_adapter_without_cache(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    architecture = report["source_architecture"]
    assert all(architecture.values())
    source = (REPO_ROOT / context.MODULE_PATH).read_text(encoding="utf-8")
    assert "def _remap_engine" not in source
    assert "_adapter_owner._remap_engine" in source
    assert "_adapter_owner._failure_output" in source
    assert "lru_cache" not in source


def test_checker_status_and_readiness_match_repository_lifecycle(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    assert report["ready_for_context_runtime_commit_review"] is True
    assert report["production_monkeypatch_used"] is False
    assert report["ready_for_dataloader_integration"] is False
    assert report["ready_for_model_integration"] is False
    assert report["ready_for_loss_integration"] is False
    assert report["current_compiler_context_uses_successor_authority"] is False
    assert report["compiler_context_rebuild_device_identity_risk"] is True
    assert report["feature_semantics_reaudit_required_before_training"] is True
    assert report["ready_for_training"] is False
    lifecycle = report["repository_lifecycle"]
    if lifecycle == "precommit-untracked":
        assert report["status"] == (
            "PASS_REMAP_ADAPTER_CONTEXT_PRECOMMIT_CANDIDATE_ONLY"
        )
        assert report["precommit_candidate_validation_passed"] is True
        assert report["real_public_context_build_performed"] is False
        assert report["clean_successor_live_validation_pending"] is True
        assert report["ready_for_context_runtime_publication"] is False
    elif lifecycle == "clean-tracked-successor":
        assert report["status"] == "PASS_REMAP_ADAPTER_CONTEXT_RUNTIME_ONLY"
        assert report["precommit_candidate_validation_passed"] is False
        assert report["real_public_context_build_performed"] is True
        assert report["clean_successor_live_validation_pending"] is False
        assert report["ready_for_context_runtime_publication"] is True
    else:
        pytest.fail(f"unexpected repository lifecycle: {lifecycle!r}")


def test_audit_lifecycle_fields_are_internally_consistent(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    lifecycle = report["repository_lifecycle"]
    assert lifecycle in (
        "precommit-untracked",
        "clean-tracked-successor",
    )
    assert report["real_public_context_build_performed"] is (
        lifecycle == "clean-tracked-successor"
    )
    assert report["clean_successor_live_validation_pending"] is (
        lifecycle == "precommit-untracked"
    )
    assert report["ready_for_context_runtime_publication"] is (
        lifecycle == "clean-tracked-successor"
    )
    assert report["precommit_candidate_validation_passed"] is (
        lifecycle == "precommit-untracked"
    )


def test_canonical_mask_exact5_including_scaffold_only(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    assert report["canonical_mask_semantics"] == [
        {"semantic_name": "warhead_only", "display_alias": "A"},
        {"semantic_name": "linker_plus_warhead", "display_alias": "B"},
        {"semantic_name": "scaffold_plus_warhead", "display_alias": "B2"},
        {"semantic_name": "scaffold_only", "display_alias": "B3"},
        {
            "semantic_name": "scaffold_plus_linker_plus_warhead",
            "display_alias": "C",
        },
    ]


def test_report_is_compact_json_serializable(
    audit: tuple[dict[str, object], dict[str, object]],
) -> None:
    report, unused_internal = audit
    payload = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    assert "\n" not in payload
    assert json.loads(payload)["status"] == report["status"]
