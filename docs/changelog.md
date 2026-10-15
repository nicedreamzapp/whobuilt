---
title: whobuilt changelog
description: Change history for whobuilt, taken from the git history. There are no tagged releases yet.
---

# Changelog

whobuilt has **no tags or releases** yet, so there are no version numbers. This page is
built from the git history on `main`.

## 2026-09-27: README rewrite

Merged in [pull request #1](https://github.com/nicedreamzapp/whobuilt/pull/1)
(commit `eff23f3`, merge `ba06475`). Documentation only, no code changes.

- README says what the tool does up front.
- New "What I built" section describing the three source files.
- Python requirement corrected to 3.12+ (the code uses a backslash inside an f-string).
- Options documented, including `-o` and `--max`.
- "Known limits" section added.

## 2026-08-06: first release

Commit `b8dd7f2`, "whobuilt: credits files that name people, not packages".

- Manifest scanner for `requirements*.txt`, `pyproject.toml`, `package.json` and `Cargo.toml`.
- Nested GitHub checkout and Hugging Face snapshot detection.
- Import fallback, with guesses kept in their own section.
- Resolver through PyPI, npm and crates.io to GitHub, top four human contributors,
  display names, request cache, GitHub token pickup from the environment or `gh`.
- Markdown renderer with "Guessed from imports" and "Couldn't trace these" sections.
- `CREDITS.md`, `LICENSE` (MIT) and `README.md`.
