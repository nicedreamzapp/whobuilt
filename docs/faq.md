---
title: whobuilt FAQ - credits files, privacy, supported languages
description: Frequently asked questions about whobuilt. What it collects, which languages and registries it supports, why it needs a GitHub token, how it picks people, and whether it is on PyPI.
---

# FAQ

## What does whobuilt actually produce?

One Markdown file (printed, or saved as `CREDITS.md` with `--write`) that lists your
dependencies grouped by source, and under each one the up to four people with the most
commits in its GitHub repository.

## Which languages are supported?

Python (`requirements*.txt`, `pyproject.toml`), JavaScript (`package.json`) and Rust
(`Cargo.toml`), plus nested GitHub checkouts and Hugging Face model snapshot folders.
Other ecosystems such as Go modules, Ruby gems or Maven are not read.

## Does it collect email addresses?

No. It requests repository data, contributor lists and public user profiles from the
GitHub API, and only uses the login and the display name. Nothing is sent anywhere except
the lookups themselves, and nothing is saved except the Markdown file you ask for.

## Is it on PyPI? Can I `pip install` it?

Not yet. Clone the repository and run `python3 -m whobuilt`. See [Install](install.md).

## Why does it need a GitHub token?

It doesn't need one, but without one GitHub allows 60 requests an hour, which runs out
after about ten traced dependencies. With a token it is 5,000. If the GitHub CLI is logged
in, whobuilt borrows its token automatically.

## How does it decide who "built" a package?

The top four accounts by commit count in the GitHub contributors list, skipping bots. This
is a simple, public, mechanical measure. It misses people who review, design, write docs or
maintain without many commits. Treat the output as a draft.

## Does it include transitive dependencies?

No. It reads the names written in your manifests. It does not read lock files or resolve
the dependency tree.

## Does it read `devDependencies` or optional dependency groups?

For `package.json`, only `dependencies` and `peerDependencies`. For `pyproject.toml`, any
`dependencies = [ ... ]` list is read, so it depends on how the file is laid out.
For `Cargo.toml`, only `[dependencies]`.

## Which dependencies does `--max` keep?

The first N found, in scan order, not the most important ones. See
[Configuration](configuration.md#-max).

## Can I run it in CI?

Nothing in the repository sets this up. It is a plain command, so it can run anywhere
Python 3.12 runs. In GitHub Actions the built-in `GITHUB_TOKEN` would be picked up
if exposed as an environment variable. TODO-VERIFY: not tested.

## Does it have tests?

Yes. An offline `unittest` suite lives in `tests/` and needs nothing installed:

    python3 -m unittest discover -s tests -t . -v

Registry and GitHub calls are faked, and the suite blocks the network so a missing mock
fails loudly. GitHub Actions runs it on Python 3.12, 3.13 and 3.14 for every push and pull
request.

## What license is it under?

MIT.

## I was credited and something is wrong

Please [open an issue](https://github.com/nicedreamzapp/whobuilt/issues). The README says
getting that right is the entire point.
