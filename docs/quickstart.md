---
title: whobuilt quickstart - make a CREDITS.md in one command
description: Generate a Markdown credits file for a Python, JavaScript or Rust project with whobuilt. Print it, save it as CREDITS.md, and read the guessed and untraced sections before publishing.
---

# Quickstart

## 1. Make sure GitHub lookups will work

Without a token, GitHub allows 60 API requests an hour, and whobuilt makes several per
dependency. Either log in with the GitHub CLI:

```bash
gh auth login
```

or set a token:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

See [GitHub token](configuration.md#github-token) for the details.

## 2. Print the credits page

From inside your clone of whobuilt:

```bash
python3 -m whobuilt /path/to/your/project
```

Progress lines go to standard error:

```text
tracing <jobs> of <total> dependencies back to their authors…
<people> people named across <projects> projects
```

The Markdown
page goes to standard output, so you can redirect it:

```bash
python3 -m whobuilt /path/to/your/project > credits-draft.md
```

## 3. Save it into the project

```bash
python3 -m whobuilt /path/to/your/project --write
```

This writes `CREDITS.md` in the project folder and prints `wrote /path/to/your/project/CREDITS.md`.
It overwrites any existing file with that name. To use another name:

```bash
python3 -m whobuilt /path/to/your/project --write -o ACKNOWLEDGEMENTS.md
```

## 4. Read it before you publish

The page can have up to three kinds of section:

1. **One section per source** (Python, JavaScript, Rust, Vendored source, Model weights).
   Each entry links the project and lists up to four people.
2. **"Guessed from imports — check these before you publish them"**. Only appears when the
   project has no manifest. These names came from `import` lines and some are probably
   wrong. Confirm each one by hand.
3. **"Couldn't trace these"**. Dependencies with no GitHub repository found, or where a
   lookup failed. If this list is long, you are probably out of GitHub API requests. See
   [Troubleshooting](troubleshooting.md).

Next: [Configuration](configuration.md) for every option.
