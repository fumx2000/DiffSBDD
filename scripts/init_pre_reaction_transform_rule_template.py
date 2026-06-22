#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


RULE_COLUMNS = [
    "sample_id",
    "warhead_type",
    "residue_name",
    "residue_atom",
    "ligand_reactive_atom",
    "covalent_bond_to_remove",
    "bond_order_to_restore",
    "atoms_requiring_charge_check",
    "atoms_requiring_valence_check",
    "protonation_note",
    "geometry_note",
    "confidence_level",
    "requires_manual_review",
    "rule_status",
    "rule_source",
    "training_ready_candidate",
    "pre_reaction_graph_ready",
    "curator_note",
]

WARHEAD_TYPE_BY_SAMPLE = {
    "BTK_C481_6DI9": "btk_c481_inhibitor_like_michael_acceptor_draft",
    "KRAS_G12C_5F2E": "kras_g12c_inhibitor_like_michael_acceptor_draft",
    "KRAS_G12C_6OIM": "kras_g12c_inhibitor_like_michael_acceptor_draft",
}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_template_rows(readiness_csv: str | Path) -> list[dict[str, str]]:
    readiness_rows = read_csv(readiness_csv)
    rows: list[dict[str, str]] = []
    for readiness in sorted(readiness_rows, key=lambda row: row["sample_id"]):
        sample_id = readiness["sample_id"]
        rows.append(
            {
                "sample_id": sample_id,
                "warhead_type": WARHEAD_TYPE_BY_SAMPLE.get(sample_id, "unknown_michael_acceptor_draft"),
                "residue_name": "CYS",
                "residue_atom": "SG",
                "ligand_reactive_atom": "",
                "covalent_bond_to_remove": "",
                "bond_order_to_restore": "",
                "atoms_requiring_charge_check": "",
                "atoms_requiring_valence_check": "",
                "protonation_note": "requires_manual_review",
                "geometry_note": "post_covalent_bound_pose_coordinates_do_not_claim_free_ligand_conformer",
                "confidence_level": "draft",
                "requires_manual_review": "true",
                "rule_status": "draft_not_reviewed",
                "rule_source": "pre_reaction_graph_design_plan",
                "training_ready_candidate": "false",
                "pre_reaction_graph_ready": "false",
                "curator_note": "template_only_no_transform_performed",
            }
        )
    return rows


def write_template(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RULE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a draft pre-reaction transform rule template.")
    parser.add_argument("--readiness_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command initializes a template only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_template_rows(args.readiness_csv)
    write_template(rows, args.output_csv)
    print(f"wrote pre-reaction transform rule template: {args.output_csv}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"warhead_type={row['warhead_type']} "
            f"requires_manual_review={row['requires_manual_review']} "
            f"training_ready_candidate={row['training_ready_candidate']} "
            f"pre_reaction_graph_ready={row['pre_reaction_graph_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
