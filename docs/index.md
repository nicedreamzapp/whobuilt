---
title: whobuilt - generate a CREDITS.md that names the people behind your dependencies
description: whobuilt is a free, MIT-licensed Python command-line tool that reads requirements.txt, pyproject.toml, package.json and Cargo.toml and writes a Markdown credits file naming the top GitHub contributors behind each dependency.
---

# whobuilt

**Write a credits file that names the people, not just the packages.**

`whobuilt` is a command-line tool written in standard-library Python. Point it at a
project folder. It reads the dependency files it finds, looks each package up on its
registry (PyPI, npm or crates.io), follows the package to its GitHub repository, and
writes a Markdown credits page naming the top human contributors to each one.

```bash
python3 -m whobuilt .          # print the credits page
python3 -m whobuilt . --write  # save it as CREDITS.md
```

## Who it is for

- Maintainers who want a `CREDITS.md` or acknowledgements page that names people.
- Anyone writing a README "built with" section who wants more than a list of package names.
- Projects with no manifest at all (research code, scripts) that still want to credit
  the libraries they import. Those names are marked as guesses.

## What the output looks like

This excerpt comes from the project's
[README](https://github.com/nicedreamzapp/whobuilt#what-comes-out). The real file links
every name to its GitHub profile.

```markdown
## Python

- **[numpy](https://github.com/numpy/numpy)** — Fundamental package for array computing
  Built by Charles Harris, Matti Picus, Sebastian Berg, Travis E. Oliphant
  and everyone else who has contributed.

- **[mlx](https://github.com/ml-explore/mlx)** — Machine learning on Apple silicon
  Built by Cheng, Angelos Katharopoulos, Jagrit Digani, Alex Barron
  and everyone else who has contributed.
```

Contributor lists change over time, so a run today can name different people. For what a
run with no dependencies looks like, see the project's own
[CREDITS.md](https://github.com/nicedreamzapp/whobuilt/blob/main/CREDITS.md).

!!! note "Screenshots"
    The repository has no screenshots or GIFs yet, so none are shown here.
    TODO-VERIFY: add a terminal recording once one exists in the repo.

## What it reads

| Source | Where names go next |
|---|---|
| `requirements*.txt`, `pyproject.toml` | PyPI, then GitHub |
| `package.json` | npm, then GitHub |
| `Cargo.toml` | crates.io, then GitHub |
| Git checkouts of other GitHub projects inside yours | GitHub directly |
| Hugging Face cache folders (`models--org--name/snapshots/...`) | Hugging Face Hub (credited to the model's author) |
| No manifest at all | Your `import` lines, marked as guesses |

Details are on [How it works](how-it-works.md).

## Two rules it follows

**Guesses are kept apart.** When names come from reading `import` lines, they go in a
separate section headed "check these before you publish them". An import name is not a
package name. `import comfy` usually means ComfyUI, but the PyPI package `comfy` is an
unrelated project.

**Gaps are shown.** Anything that could not be traced to a source repository is listed
under "Couldn't trace these" instead of being dropped.

## Privacy

It uses public profile data only: GitHub logins and the display name a person put on their
own GitHub profile. It does not read emails or commit metadata.

## Facts at a glance

- Language: Python 3.12 or newer, standard library only, no third-party dependencies.
- Size: three source files in `whobuilt/` (`__main__.py`, `resolve.py`, `scan.py`).
- License: MIT.
- Tests: offline `unittest` suite in `tests/`, run by CI on Python 3.12, 3.13 and 3.14.
- Packaging: not on PyPI. Run it from a clone. See [Install](install.md).

[Install it](install.md){ .md-button .md-button--primary }
[Quickstart](quickstart.md){ .md-button }
