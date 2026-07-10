from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from covalent_ext import covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke as smoke


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquire-missing-ccd", action="store_true")
    args = parser.parse_args()
    result = smoke.run(acquire_missing_ccd=args.acquire_missing_ccd)
    manifest = result["manifest"]
    for key in [
        "future_unified_sample_count",
        "unique_ligand_component_count",
        "ccd_component_count",
        "ccd_downloaded_by_step14ao_count",
        "ligand_graph_scaffold_evidence_row_count",
        "ligand_pairwise_similarity_evidence_row_count",
        "protein_sequence_accession_evidence_row_count",
        "protein_pairwise_sequence_identity_evidence_row_count",
        "combined_pairwise_independence_evidence_row_count",
        "confirmed_new_independent_group_count_current_step",
        "ready_for_covapie_unified_independence_group_assignment_and_sample_index_merge_smoke",
        "ready_for_training",
    ]:
        print(f"{key}={manifest[key]}")
    if not manifest["all_checks_passed"]:
        print("blocking_reasons=" + ";".join(dict.fromkeys(manifest["blocking_reasons"])))
        return 1
    print("covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
