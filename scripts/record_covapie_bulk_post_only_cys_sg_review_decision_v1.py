#!/usr/bin/env python3
"""Record one audited change in the post-only CYS-SG decision overlay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import covapie_bulk_post_only_cys_sg_human_review_v1 as review


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--unit-id", required=True)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--reviewed-at-utc", required=True)
    parser.add_argument("--review-rationale", required=True)


def _atom_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError("expected JSON atom-ID list") from error
    if type(parsed) is not list or any(type(item) is not str for item in parsed):
        raise argparse.ArgumentTypeError("expected JSON atom-ID list")
    return parsed


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)

    relevance = commands.add_parser("unit-relevance")
    _common(relevance)
    relevance.add_argument("--decision", choices=review.RELEVANCE_DECISIONS, required=True)
    relevance.add_argument(
        "--workflow-status",
        choices=("IN_PROGRESS", "COMPLETED", "DEFERRED"),
        required=True,
    )
    relevance.add_argument(
        "--clear-downstream",
        action="store_true",
        help=(
            "Explicitly append audited clears for existing chemistry/event "
            "decisions before changing relevance to NOT_RELEVANT or DEFERRED."
        ),
    )

    chemistry = commands.add_parser("unit-chemistry")
    _common(chemistry)
    chemistry.add_argument(
        "--reactive-atom-status", choices=review.REACTIVE_ATOM_STATUSES, required=True
    )
    chemistry.add_argument("--confirmed-atom-id", default="")
    chemistry.add_argument(
        "--family-decision",
        choices=(review.EXISTING_FAMILY, review.NEW_FAMILY_REVIEW),
        required=True,
    )
    chemistry.add_argument("--canonical-reaction-family-id", default="")
    chemistry.add_argument("--proposed-warhead-family-label", default="")
    chemistry.add_argument("--warhead-atom-ids", type=_atom_list, required=True)
    chemistry.add_argument("--scaffold-atom-ids", type=_atom_list, required=True)
    chemistry.add_argument("--linker-atom-ids", type=_atom_list, required=True)
    chemistry.add_argument("--warhead-role-atom-ids", type=_atom_list, required=True)

    event = commands.add_parser("event")
    _common(event)
    event.add_argument("--event-id", required=True)
    event.add_argument(
        "--post-geometry-training-usable",
        choices=review.GEOMETRY_USABILITY,
        required=True,
    )
    event.add_argument(
        "--event-training-use-decision",
        choices=review.EVENT_USE_DECISIONS,
        required=True,
    )
    event.add_argument("--event-exclusion-reason", default="")

    status = commands.add_parser("unit-status")
    _common(status)
    status.add_argument(
        "--workflow-status",
        choices=("IN_PROGRESS", "COMPLETED", "DEFERRED"),
        required=True,
    )
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    repo_root = arguments.repo_root.resolve()
    output_root = (
        arguments.output_root.resolve()
        if arguments.output_root
        else repo_root / review.OUTPUT_ROOT_RELATIVE
    )
    common = {
        "repo_root": repo_root,
        "output_root": output_root,
        "unit_id": arguments.unit_id,
        "reviewer_id": arguments.reviewer_id,
        "reviewed_at_utc": arguments.reviewed_at_utc,
        "review_rationale": arguments.review_rationale,
    }
    if arguments.command == "unit-relevance":
        result = review.record_unit_relevance_v1(
            **common,
            relevance_decision=arguments.decision,
            workflow_status=arguments.workflow_status,
            clear_downstream=arguments.clear_downstream,
        )
    elif arguments.command == "unit-chemistry":
        result = review.record_unit_chemistry_v1(
            **common,
            reactive_atom_status=arguments.reactive_atom_status,
            confirmed_atom_id=arguments.confirmed_atom_id,
            family_decision=arguments.family_decision,
            canonical_reaction_family_id=arguments.canonical_reaction_family_id,
            proposed_warhead_family_label=arguments.proposed_warhead_family_label,
            warhead_atom_ids=arguments.warhead_atom_ids,
            scaffold_atom_ids=arguments.scaffold_atom_ids,
            linker_atom_ids=arguments.linker_atom_ids,
            warhead_role_atom_ids=arguments.warhead_role_atom_ids,
        )
    elif arguments.command == "event":
        result = review.record_event_decision_v1(
            **common,
            event_id=arguments.event_id,
            post_geometry_training_usable=arguments.post_geometry_training_usable,
            event_training_use_decision=arguments.event_training_use_decision,
            event_exclusion_reason=arguments.event_exclusion_reason,
        )
    else:
        result = review.record_unit_status_v1(
            **common, workflow_status=arguments.workflow_status
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
