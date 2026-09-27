# whobuilt

**Write a credits file that names the people, not just the packages.**

`whobuilt` is a command-line tool that reads a project's dependency files and writes a
Markdown credits page naming the top human contributors behind each dependency.

```
python3 -m whobuilt .          # print it
python3 -m whobuilt . --write  # save it as CREDITS.md
```

Every credits file in the world lists packages. Packages didn't write themselves.

`whobuilt` reads the same manifests everyone else reads, then keeps going — package
registry, source repository, and finally the handful of humans with the most commits in
it. Those names go in your credits.

## What comes out

```markdown
## Python

- **[numpy](https://github.com/numpy/numpy)** — Fundamental package for array computing
  Built by Charles Harris, Matti Picus, Sebastian Berg, Travis E. Oliphant
  and everyone else who has contributed.

- **[mlx](https://github.com/ml-explore/mlx)** — Machine learning on Apple silicon
  Built by Cheng, Angelos Katharopoulos, Jagrit Digani, Alex Barron
  and everyone else who has contributed.
```

Six dependencies, twenty-three people named. Most of whom will never hear about it
otherwise. (Excerpt, trimmed for reading. The real file links every name to its GitHub
profile; see `render()` in [`whobuilt/__main__.py`](whobuilt/__main__.py). For what a run
with no dependencies looks like, see this repo's own [CREDITS.md](CREDITS.md).)

## What I built

Written by Matt Macosko. About 520 lines of standard-library Python, three files:

- **Manifest scanner** ([`whobuilt/scan.py`](whobuilt/scan.py)): walks the project, parses
  `requirements*.txt`, `pyproject.toml`, `package.json` and `Cargo.toml` without extra
  libraries, spots nested git checkouts and Hugging Face snapshot folders, and falls back
  to reading `import` lines when there is no manifest.
- **Resolver** ([`whobuilt/resolve.py`](whobuilt/resolve.py)): package name to registry to
  GitHub repo to the top 4 human contributors (bots filtered out) and their public display
  names, with a request cache and GitHub token pickup.
- **CLI and renderer** ([`whobuilt/__main__.py`](whobuilt/__main__.py)): options, 8 parallel
  lookups, and the Markdown output, including the separate "guessed" and "couldn't trace"
  sections.

Upstream, not mine: the PyPI, npm, crates.io, GitHub REST and Hugging Face Hub APIs, and
Python's standard library. [CREDITS.md](CREDITS.md) says so.

## Why

I spent an afternoon hand-writing credits pages for twenty-eight repositories, and the
thing that struck me was how invisible everyone is by default. Open a hundred projects and
you'll find "built with love" and a list of package names. The people whose work
everything actually rests on are nowhere.

It's also completely mechanical, which is the annoying part. So here.

## What it reads

- `requirements*.txt`, `pyproject.toml` → PyPI → GitHub
- `package.json` → npm → GitHub
- `Cargo.toml` → crates.io → GitHub
- git checkouts of other people's GitHub projects living inside yours
- Hugging Face cache folders (`models--org--name/snapshots/...`), credited to their author
- **no manifest at all?** it falls back to reading your `import` statements

## The honesty part

A tool for crediting people that credits the *wrong* people is worse than nothing. Two
things follow from that.

**Guesses are quarantined.** When there's no manifest and names come from reading imports,
they land in a separate section headed *"check these before you publish them."* An import
name is not a package name — `import comfy` in an AI project means ComfyUI, but PyPI's
`comfy` is an unrelated config library by someone entirely different. That attribution
would be wrong, so it never gets stated as fact.

**Failures are visible.** Anything that couldn't be traced to a source repository is listed
under *"couldn't trace these"*, described as a gap in the tool rather than a judgement about
the work. No silent omissions.

## Privacy

Public profile data only: GitHub handles, and the display name someone chose to publish
about themselves. No emails, no commit metadata, nothing scraped, nothing a maintainer
hasn't already put on their own profile page.

## GitHub token

Anonymous GitHub API access is 60 requests an hour, which one medium project burns through
immediately — you'd get a credits file with nobody in it. `whobuilt` uses `$GITHUB_TOKEN`
(or `$GH_TOKEN`) if set, and otherwise borrows the token `gh` already has. If you have the GitHub CLI
installed and logged in, there's nothing to configure.

## Install

There's nothing to install. Python 3.12+, standard library only. (It needs 3.12:
`whobuilt/resolve.py` uses a backslash inside an f-string, which older versions reject
with a `SyntaxError`.)

```
git clone https://github.com/nicedreamzapp/whobuilt
cd whobuilt && python3 -m whobuilt /path/to/your/project
```

Run it from inside the clone. There is no `pip install` package yet.

## Options

```
--write          save to CREDITS.md instead of printing
-o FILE          with --write, use a different file name (inside the project)
--depth N        how deep to walk (default 4)
--max N          cap on dependencies resolved (default 60)
```

## Known limits

- **No tests** in the repo yet.
- **Rate limits look like gaps.** If GitHub is unreachable or you run out of anonymous
  requests, there is no error message. The affected projects just land under
  *"couldn't trace these"*.
- **Partial manifest coverage.** `package.json`: `dependencies` and `peerDependencies`
  only. `Cargo.toml`: the `[dependencies]` table only. `pyproject.toml` is read with regexes,
  not a TOML parser, so unusual layouts can add stray names.
- **Registries:** PyPI, npm and crates.io only, and only projects hosted on GitHub get
  people named.
- `--max` keeps the first N dependencies found, not the most important ones.

## License

MIT. Use it on anything.

---

If `whobuilt` credited you and got something wrong — your name, your role, or the project
itself — open an issue. Getting that right is the entire point.
