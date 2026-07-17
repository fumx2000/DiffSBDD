#!/usr/bin/env python3
"""Check Step14AU-E1-E2 frozen sources and exact materialized outputs."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_gate
    as gate,
)


def _check_materializer_symlink_fail_closed() -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        destination = root / "outputs"
        destination.mkdir()
        victim = root / "victim.bin"
        victim_bytes = b"E1-E2-CHECKER-VICTIM"
        victim.write_bytes(victim_bytes)
        (destination / gate.RULE_OUTPUT).symlink_to(victim)
        try:
            gate.materialize(destination, repo_root=REPO_ROOT)
        except gate.IntegrationGateError:
            pass
        else:
            raise AssertionError("materializer accepted a symlink output entry")
        assert victim.read_bytes() == victim_bytes
    return True


def check() -> tuple[dict[str, str], bool]:
    hashes = gate.validate_output_directory(repo_root=REPO_ROOT)
    manifest_path = REPO_ROOT / gate.OUTPUT_RELATIVE_DIR / gate.MANIFEST_OUTPUT
    manifest = json.loads(manifest_path.read_bytes().decode("utf-8"))

    assert manifest["all_checks_passed"] is True
    assert manifest["integration_readiness"] is True
    assert manifest["integrated_rule_count"] == 15
    assert manifest["integrated_field_count"] == 22
    assert manifest["integrated_context_count"] == 19
    assert manifest["active_issue_count"] == 9
    assert manifest["semantics_complete_rule_count"] == 7
    assert manifest["implementation_semantics_complete_field_count"] == 12
    assert manifest["implementation_ready_context_count"] == 10
    assert manifest["exact11_count"] == 11
    assert manifest["exact11_insertion_unknown_count"] == 11
    assert manifest["exact11_insertion_value_empty_count"] == 11
    assert manifest["exact11_effective_blocked_count"] == 11
    assert manifest["exact11_passed_count"] == 0
    assert manifest["provider_blocking_issue_count"] == 11
    assert manifest["reconciled_admit_004_interface_implementation_ready"] is True
    assert manifest["ready_for_admit_004_rule_logic_interface_implementation"] is True
    assert manifest["admit_004_evaluator_implemented"] is False
    assert manifest["unified_rule_engine_integrated"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    materializer_symlink_fail_closed = _check_materializer_symlink_fail_closed()
    assert materializer_symlink_fail_closed is True
    return hashes, materializer_symlink_fail_closed


def main() -> int:
    hashes, materializer_symlink_fail_closed = check()
    print(
        "PASS Step14AU-E1-E2: exact12 verified; overlays/counts/readiness/"
        "Exact11/safety and exact six outputs validated"
    )
    for name in gate.OUTPUT_FILENAMES:
        print(f"{name} {hashes[name]}")
    print(
        "materializer_symlink_fail_closed="
        f"{str(materializer_symlink_fail_closed).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
