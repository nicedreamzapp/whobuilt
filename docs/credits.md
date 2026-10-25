---
title: whobuilt credits - the services and projects it relies on
description: Credits for whobuilt. The PyPI, npm, crates.io, GitHub and Hugging Face APIs, Python's standard library, and the tools used to build this documentation site.
---

# Credits

whobuilt was written by Matt Macosko and is published under the MIT License by Matt
Macosko / Nice Dreamz LLC.

## What the program relies on

whobuilt has no third-party Python dependencies. Running it on itself prints "No
dependencies found". It does rely on these public services and projects, none of which
it wrote:

| | |
|---|---|
| [PyPI](https://pypi.org) JSON API | Python package metadata and source links |
| [npm registry](https://www.npmjs.com) | JavaScript package metadata |
| [crates.io](https://crates.io) API | Rust crate metadata |
| [GitHub REST API](https://docs.github.com/rest) | Repository details, contributor lists and profile display names |
| [GitHub CLI](https://cli.github.com/) | Optional. Its `gh auth token` is borrowed when no token is set |
| [Hugging Face Hub API](https://huggingface.co/docs/hub/api) | Model authorship |
| [Python](https://www.python.org/) and its standard library | `urllib`, `json`, `re`, `argparse`, `concurrent.futures`, `pathlib` and the rest. See the [Python developer guide](https://devguide.python.org/) for the people behind it |

The example output in the README credits [NumPy](https://github.com/numpy/numpy) and
[MLX](https://github.com/ml-explore/mlx) contributors. Those names come from those
projects' public GitHub contributor lists.

## This documentation site

Built with [MkDocs](https://www.mkdocs.org/) and
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), and hosted on
GitHub Pages.

The project's own credits file is
[CREDITS.md](https://github.com/nicedreamzapp/whobuilt/blob/main/CREDITS.md).

If your work is listed here and you would like the wording changed, open an issue.
