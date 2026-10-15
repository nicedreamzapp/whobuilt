---
title: whobuilt troubleshooting - empty credits, untraced packages, SyntaxError
description: Fixes for common whobuilt problems. Everything under "Couldn't trace these", nobody named, SyntaxError on Python 3.11, "No dependencies found", "not a directory", and stray names like build-backend.
---

# Troubleshooting

The repository has no GitHub issues yet, so this page is built from the messages and
behaviour in the code. If you hit something not covered here, please
[open an issue](https://github.com/nicedreamzapp/whobuilt/issues).

## Everything is under "Couldn't trace these" and nobody is named

The summary line reads `0 people named across 0 projects`, or far fewer than expected.

whobuilt does not report network errors. Every failed request is treated as "no data", so
the dependency drops into "Couldn't trace these". Common causes:

1. **Out of anonymous GitHub requests.** Without a token GitHub allows 60 requests an
   hour. Each traced dependency costs about six (repo, contributors, and one per person).
   Set `GITHUB_TOKEN` or run `gh auth login`. See
   [GitHub token](configuration.md#github-token).
2. **No network, or a proxy or firewall in the way.** whobuilt uses Python's `urllib`,
   which honours the usual `HTTPS_PROXY` variables. Check you can reach `pypi.org` and
   `api.github.com`:

    ```bash
    curl -sI https://pypi.org/pypi/requests/json | head -1
    curl -s https://api.github.com/rate_limit
    ```

    The second command also shows how many GitHub requests you have left.
3. **Slow responses.** Each request times out after 12 seconds.

Results are not saved between runs, so after fixing the cause just run it again.

## Some packages are untraced even with a token

A dependency is only traced if its registry entry points at a **GitHub** URL. Packages
hosted on GitLab, Codeberg, Bitbucket or a private server, or with no repository link on
PyPI, npm or crates.io, cannot be traced. This is a current limit of the tool.

## `SyntaxError: f-string expression part cannot include a backslash`

You are running Python 3.11 or older. whobuilt needs Python 3.12 or newer. Check with
`python3 --version`, and run it with a newer interpreter, for example `python3.12 -m whobuilt .`.

## `No module named whobuilt`

`python3 -m whobuilt` must be run from inside the cloned repository, or with
`PYTHONPATH` pointing at it. See [Install](install.md).

## `No dependencies found. Nothing to credit — which is its own kind of achievement.`

whobuilt found nothing to look up. Check:

- The path is the project root, not a subfolder.
- The manifests are within `--depth` levels (default 4). Note `--depth 0` reads nothing.
- The manifests are not inside a skipped folder such as `vendor`, `build`, `dist` or a
  folder whose name starts with `.`.
- The dependencies are not all in the always-skipped list (for example a project that
  only depends on `setuptools`).
- `--max` is not `0`.
- For `package.json`, only `dependencies` and `peerDependencies` are read. A project with
  only `devDependencies` finds nothing.

The full lists are on [Configuration](configuration.md).

## `whobuilt: error: not a directory: <path>`

The path argument must be an existing folder. Pass the project folder, not a single file
like `requirements.txt`.

## A dependency called `build-backend` (or `homepage`) appears

`pyproject.toml` is read with regular expressions, and any `key = "value"` line outside
a short list of known keys is taken as a dependency name. A standard `[build-system]`
table adds `build-backend`. Delete the line from the generated file. See
[How it works](how-it-works.md#1-scan-the-project-scanpy).

## The "Guessed from imports" section names the wrong project

That section only appears when there is no manifest, and the names come from `import`
lines. An import name is often not the PyPI name. The best fix is to add a
`requirements.txt` to your project. Then the import fallback does not run at all.

## Only the first of several imports on one line is found

`import numpy, scipy` only yields `numpy`. Put imports on separate lines or add a
`requirements.txt`.

## The wrong people, or a person's name is wrong

whobuilt names the top four non-bot accounts by commit count on GitHub and shows the
display name each person set on their GitHub profile. Commit count is not the same as
authorship or maintainership, so edit the generated file if it is misleading. If
whobuilt credited you and got something wrong,
[open an issue](https://github.com/nicedreamzapp/whobuilt/issues).

## `--write` replaced my existing CREDITS.md

`--write` overwrites without asking. Use `-o` to pick another file name, or print to
standard output and copy what you want.
