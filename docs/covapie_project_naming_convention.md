# CovaPIE Project Naming Convention

This repository uses **CovaPIE** as the project name from this point forward.

## Naming Boundary

- **CovaPIE** is the name of this project.
- **CovaGEN** is an external model or project name owned by others. Do not use CovaGEN as the name of this project unless explicitly citing or discussing that external model or literature.
- New experiment reports, summaries, gate documents, and Codex prompts should use CovaPIE when referring to this project.

## No Bulk Rename

Historical artifact paths, historical filenames, and historical step names are retained for now. Do not perform a bulk migration just to replace older names in existing artifacts.

The `src/covalent_ext/` package is a functional module name and is not renamed by this convention.

Do not change Python import paths, test paths, data paths, or existing `data/derived/` artifact paths for this naming convention.

If a future naming migration is required, it must be handled as a dedicated migration design gate. Codex must not perform an ad hoc or automatic bulk replacement.

## Unchanged Scientific Boundaries

This naming convention does not change the canonical mask tasks:

- `warhead_only` / `A`
- `linker_plus_warhead` / `B`
- `scaffold_plus_warhead` / `B2`
- `scaffold_only` / `B3`
- `scaffold_plus_linker_plus_warhead` / `C`

Feature semantics audit remains required before formal training, fine-tuning, or real parameter updates.
