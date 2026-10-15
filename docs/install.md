---
title: Install whobuilt (Python 3.12+, no dependencies)
description: How to install whobuilt. Clone the repository and run it with Python 3.12 or newer. There is no pip package and nothing else to install.
---

# Install

There is no `pip install` package yet. You clone the repository and run the module with
Python.

## Requirements

- **Python 3.12 or newer.** `github_slug()` in `whobuilt/resolve.py` puts a backslash
  inside an f-string expression, which Python 3.11 and older reject with
  `SyntaxError: f-string expression part cannot include a backslash`.
- **git**, to clone the repository.
- **Network access** to `pypi.org`, `registry.npmjs.org`, `crates.io`, `api.github.com`
  and `huggingface.co`.
- **Optional:** a GitHub token or the [GitHub CLI](https://cli.github.com/) logged in.
  Strongly recommended. See [GitHub token](configuration.md#github-token).

No third-party Python packages are needed.

## Steps

```bash
git clone https://github.com/nicedreamzapp/whobuilt
cd whobuilt
python3 --version   # must print 3.12 or newer
python3 -m whobuilt /path/to/your/project
```

Run it from inside the clone, so Python can find the `whobuilt` package. The project you
want to credit can be anywhere. Pass its path as the argument.

!!! tip "Running from somewhere else"
    `python3 -m whobuilt` only works when the `whobuilt/` folder is importable. From
    another directory you can point Python at the clone:

    ```bash
    PYTHONPATH=/path/to/whobuilt python3 -m whobuilt .
    ```

    This is standard Python behaviour, not a feature of whobuilt.

## Check it works

```bash
python3 -m whobuilt --help
```

prints:

```text
usage: whobuilt [-h] [--write] [-o OUT] [--depth DEPTH] [--max MAX] [path]
```

followed by the option list. Next: [Quickstart](quickstart.md).
