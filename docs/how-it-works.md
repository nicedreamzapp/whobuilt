---
title: How whobuilt works - from manifest to registry to GitHub contributors
description: Architecture of whobuilt. How it scans manifests, falls back to import lines, resolves packages through PyPI, npm and crates.io to GitHub, picks the top human contributors and renders the Markdown credits page.
---

# How it works

whobuilt is three files of standard-library Python. A run goes through four steps.

```text
scan.py            resolve.py                                  __main__.py
manifests  ──►  registry ──► GitHub repo ──► contributors ──►  Markdown page
(or imports)    (PyPI/npm/   (repo_meta)     (top 4 humans,
                 crates.io)                   display names)
```

## 1. Scan the project (`scan.py`)

`scan(root, max_depth)` walks the folder with `os.walk`, skipping the folders listed on
[Configuration](configuration.md#folders-that-are-never-walked), and parses each manifest
without third-party libraries.

| File | How it is read |
|---|---|
| `requirements.txt`, `requirements*.txt` | One name per line. Comments are stripped. Lines starting with `-`, `http`, `git+` or `.` are skipped. The name is cut at the first `<`, `>`, `=`, `!`, `~`, `;`, `[` or space and lowercased. |
| `pyproject.toml` | Regular expressions, not a TOML parser. Every quoted string inside any `dependencies = [ ... ]` block is taken. In addition, every line that looks like `name = "..."` or `name = {` is taken as a dependency name (this is meant for Poetry-style tables) unless the key is `python`, `name`, `version`, `description`, `readme`, `requires-python`, `license` or `authors`. |
| `package.json` | Keys of `dependencies` and `peerDependencies`. `devDependencies` and `optionalDependencies` are not read. Invalid JSON is skipped. |
| `Cargo.toml` | Keys in the `[dependencies]` table only. |

!!! warning "Stray names from pyproject.toml"
    Because of the second `pyproject.toml` rule, a standard `[build-system]` table with
    `build-backend = "setuptools.build_meta"` adds a dependency called `build-backend`.
    This was reproduced while writing these docs. It then shows up under "Couldn't trace
    these". Keys like `homepage = "..."` in `[project.urls]` would do the same.

### Nested git checkouts

If a subfolder contains a `.git` folder, whobuilt reads the first `url = ...` line from its
`.git/config`. If that URL is on GitHub and is not the project's own repo, it is credited
under "Vendored source". The walk does not go further into that checkout, but manifests
sitting directly in its top folder are still read, because files are handled before the
check.

### Hugging Face snapshots

A folder path matching `models--<org>--<name>/snapshots/<hex hash>` is credited to the
Hugging Face model `<org>/<name>` under "Model weights".

### Import fallback

Only when **no** `requirements*.txt`, `pyproject.toml`, `package.json` or `Cargo.toml`
dependency was found does `from_imports()` run. It reads `import x` and `from x import`
lines in `.py` files and keeps third-party names:

- Standard-library modules (`sys.stdlib_module_names`) and names starting with `_` are dropped.
- Names in the [import map](configuration.md#import-name-to-pypi-name) are translated.
- Names that match a file or folder in the project root are treated as the project's own
  code and dropped.
- Only the **first** module on a line is seen. `import numpy, comfy` yields `numpy` only.
  (Reproduced while writing these docs.)

These names are flagged as inferred and rendered in their own section.

Finally each list is de-duplicated and the [always-skipped
packages](configuration.md#packages-that-are-always-left-out) are removed.

## 2. Find the source repository (`resolve.py`)

`resolve(name, kind)` is called once per dependency, eight at a time in a thread pool.

| Kind | Lookup | How the GitHub repo is found |
|---|---|---|
| PyPI | `https://pypi.org/pypi/<name>/json` | `project_urls` keys `source`, `source code`, `repository`, `code`, `github`, `homepage` (case-insensitive, in that order), then `home_page`, `package_url`, then any other project URL that points at GitHub. |
| npm | `https://registry.npmjs.org/<name>` | `repository` of the `latest` version, falling back to the top-level `repository`. |
| crates.io | `https://crates.io/api/v1/crates/<name>` | `repository`, falling back to `homepage`. |
| Nested checkout | none | Already known. |
| Hugging Face | `https://huggingface.co/api/models/<org>/<name>` | Not GitHub. The model's `author` is credited as an organisation and no people are named. |

Only GitHub URLs count. A package hosted on GitLab, Codeberg or elsewhere is not traced
and ends up under "Couldn't trace these".

## 3. Find the people

For a GitHub repo `owner/name`:

1. `GET /repos/owner/name` gives the description, license, star count and owner.
2. `GET /repos/owner/name/contributors?per_page=25` gives contributors ordered by commit
   count. Accounts whose type is not `User`, or whose login ends in `[bot]` or `-bot`,
   are skipped. The first four left are kept.
3. `GET /users/<login>` for each of those gives the display name they set on their profile.
   If there is none, the `@login` is shown instead.

### Caching and errors

Every URL is fetched at most once per run (an in-memory dictionary). Any network error,
timeout, HTTP error status or invalid JSON is turned into "no data" without a message.
That is why rate limits and outages show up as untraced entries instead of errors.

`resolve.py` also defines `rate_limit_left()`, which reads `/rate_limit`. Nothing calls it
in the current code.

## 4. Render the page (`__main__.py`)

`render()` builds the Markdown:

- Title: `# 🙏 Whose work <folder name> stands on`, then a short intro line.
- One section per kind, in the order Python, JavaScript, Rust, Vendored source, Model
  weights. Within a section, entries are sorted by GitHub star count, highest first.
- Each entry: linked name, the registry summary (or the GitHub description), then
  "Built by ..." with up to four linked people. "and everyone else who has contributed" is
  added only when four people were named. If no people were found but an owner was, it
  says "By **owner**."
- "Guessed from imports — check these before you publish them": the inferred names, with
  "Possibly ..." before the people.
- "Couldn't trace these": names with neither people nor an owner, sorted alphabetically.
- A closing line inviting corrections by issue.

Progress and the summary count go to standard error. The page goes to standard output,
or to the file chosen with `--write`.
