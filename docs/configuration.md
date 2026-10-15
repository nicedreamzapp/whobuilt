---
title: whobuilt configuration - every command-line option and environment variable
description: Reference for whobuilt's command-line options (--write, -o, --depth, --max), the GITHUB_TOKEN and GH_TOKEN environment variables, the gh CLI fallback and the fixed limits built into the code.
---

# Configuration

Everything on this page is read from the source in
[`whobuilt/__main__.py`](https://github.com/nicedreamzapp/whobuilt/blob/main/whobuilt/__main__.py),
[`whobuilt/resolve.py`](https://github.com/nicedreamzapp/whobuilt/blob/main/whobuilt/resolve.py) and
[`whobuilt/scan.py`](https://github.com/nicedreamzapp/whobuilt/blob/main/whobuilt/scan.py).
There is no config file.

## Command line

```text
usage: whobuilt [-h] [--write] [-o OUT] [--depth DEPTH] [--max MAX] [path]
```

| Option | Default | What the code does |
|---|---|---|
| `path` | `.` | The project folder to scan. `~` is expanded and the path is made absolute. If it is not a directory, whobuilt exits with status 2 and `whobuilt: error: not a directory: <path>`. |
| `--write` | off | Write the page to a file in the project folder instead of printing it to standard output. Overwrites an existing file without asking. |
| `-o`, `--out` | `CREDITS.md` | File name used by `--write`. Ignored without `--write`. |
| `--depth` | `4` | How many directory levels to walk. See below. |
| `--max` | `60` | Cap on how many dependencies are looked up. See below. |
| `-h`, `--help` | | Print usage and exit. |

### `-o` / `--out`

The value is joined to the project folder with `pathlib.Path(root, out)`. A relative name
such as `docs/CREDITS.md` lands inside the project (the folder must already exist). An
**absolute** path replaces the project folder entirely, so `-o /tmp/credits.md` writes to
`/tmp/credits.md`. A path with `..` can also leave the project folder. The README's
phrase "inside the project" describes the usual case, not an enforced rule.

### `--depth`

The walk stops descending once a folder is `depth` levels below the project root. In
practice, `--depth N` reads manifests in the root folder and `N - 1` levels below it.
Tested behaviour with manifests at three levels:

| `--depth` | Folders read |
|---|---|
| `0` | none (not even the root) |
| `1` | root only |
| `2` | root and its direct subfolders |
| `4` (default) | root and three levels below |

The same depth limit applies to the import fallback.

### `--max`

Dependencies are collected per kind, de-duplicated, then flattened in this order: PyPI,
npm, crates.io, nested git checkouts, Hugging Face models. `--max N` keeps the **first N**
of that list (a Python slice, `jobs[:N]`). It is not a ranking. With `--max 0`, nothing is
looked up and whobuilt prints the "No dependencies found" message.

TODO-VERIFY: a negative value is not rejected. Because it is a slice, `--max -1` drops the
last dependency instead of erroring. Probably not intended.

## Environment variables

| Variable | Effect |
|---|---|
| `GITHUB_TOKEN` | Sent as `Authorization: Bearer <token>` on every request to `api.github.com`. Checked first. |
| `GH_TOKEN` | Used if `GITHUB_TOKEN` is empty or unset. |

No other environment variables are read by whobuilt itself. (`PYTHONPATH` is standard
Python, see [Install](install.md).)

### GitHub token

From `_github_token()` in `resolve.py`, in order:

1. `$GITHUB_TOKEN`, if set and not empty.
2. `$GH_TOKEN`, if set and not empty.
3. The output of `gh auth token`, if the [GitHub CLI](https://cli.github.com/) is installed
   and exits successfully within 6 seconds.
4. Otherwise no token. Requests are anonymous.

The token is looked up once per run and only sent to `api.github.com`, never to PyPI,
npm, crates.io or Hugging Face.

The code comment says anonymous access allows 60 requests an hour and a token allows
5,000. Those are GitHub's published limits, not something whobuilt controls.

!!! warning "No warning when unauthenticated"
    The docstring of `_github_token()` says it will "carry on unauthenticated and warn".
    The current code carries on but does **not** print a warning. TODO-VERIFY whether a
    warning was meant to be added.

A read-only token with no scopes is enough for public repositories.
TODO-VERIFY: not tested against fine-grained tokens.

## Fixed limits in the code

These are constants, not options. Change the source if you need different values.

| Setting | Value | Where |
|---|---|---|
| People named per project | top 4 non-bot contributors | `contributors(slug, top=4)` |
| Contributors fetched per repo | 25 (`per_page=25`) | `contributors()` |
| Parallel lookups | 8 threads | `ThreadPoolExecutor(max_workers=8)` |
| HTTP timeout | 12 seconds per request | `TIMEOUT` |
| `gh auth token` timeout | 6 seconds | `_github_token()` |
| User-Agent | `whobuilt (+https://github.com/nicedreamzapp/whobuilt)` | `UA` |
| Python files read for the import fallback | 4,000 files, first 60,000 characters each | `from_imports()` |
| Manifest read limit | first 200,000 characters | `_read()` |

### Folders that are never walked

`.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `site-packages`, `dist`, `build`,
`.next`, `target`, `.cache`, `vendor`, and any folder whose name starts with `.`.

### Packages that are always left out

Common low-level packages are dropped because they say little about a project:

- PyPI: `setuptools`, `wheel`, `pip`, `six`, `packaging`, `typing-extensions`, `certifi`,
  `charset-normalizer`, `idna`, `urllib3`, `python-dateutil`, `pytz`, `attrs`, `zipp`,
  `importlib-metadata`, `tomli`, `colorama`
- npm: `tslib`, `@types/node`, `typescript`
- crates.io: none

### Import name to PyPI name

When reading `import` lines, these names are translated before lookup:

| Import | PyPI package |
|---|---|
| `cv2` | `opencv-python` |
| `PIL` | `pillow` |
| `sklearn` | `scikit-learn` |
| `skimage` | `scikit-image` |
| `yaml` | `pyyaml` |
| `bs4` | `beautifulsoup4` |
| `dotenv` | `python-dotenv` |
| `serial` | `pyserial` |
| `OpenSSL` | `pyopenssl` |
| `dateutil` | `python-dateutil` |
| `google` | `google-api-python-client` |
| `websocket` | `websocket-client` |
| `PyQt5` | `pyqt5` |
| `mlx_lm` | `mlx-lm` |

Any other import is lowercased and looked up as-is.

## Exit status

| Status | When |
|---|---|
| `0` | Normal run, including when no dependencies were found and when every lookup failed. |
| `2` | Bad arguments or the path is not a directory (from `argparse`). |
