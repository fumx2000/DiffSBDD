"""Thin CLI for the code-frozen CovaPIE Current11 train-only lane V1."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--legacy-init-checkpoint", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    from covalent_ext import (  # noqa: PLC0415
        covapie_current11_formal_trainer_v1 as formal_trainer,
    )

    session = formal_trainer.build_covapie_current11_formal_train_only_session_v1(
        repository_root=args.repository_root,
        state_root=args.state_root,
        legacy_init_checkpoint=args.legacy_init_checkpoint,
    )
    session.trainer.fit(model=session.model, ckpt_path=None)


if __name__ == "__main__":
    main()
