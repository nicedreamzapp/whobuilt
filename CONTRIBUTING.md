# Contributing

Thanks for taking a look. A tool for crediting people has to get the people right, so a report of
a wrong or missing name is as useful as a code change.

## Reporting a problem

Open an [issue](https://github.com/nicedreamzapp/whobuilt/issues/new/choose). The things that
make it quick to fix:

- your Python version and OS
- the exact command you ran
- which manifest files the project has (`requirements*.txt`, `pyproject.toml`, `package.json`,
  `Cargo.toml`) or whether it had none
- the part of the output that is wrong, and whether a GitHub token was set
- if it credited the wrong person, the package name and who should be credited instead

## Running it locally

Python 3.12 or newer, standard library only:

```bash
git clone https://github.com/nicedreamzapp/whobuilt
cd whobuilt && python3 -m whobuilt /path/to/your/project
```

Run it from inside the clone. Add `--write` to save the result as `CREDITS.md`.

## Tests

```bash
python3 -m unittest discover -s tests -t . -v
```

Every registry and GitHub call is faked and the suite blocks the network, so it runs offline in
under a second. CI runs it on Python 3.12, 3.13 and 3.14 for every push and pull request. If you
fix a parsing or lookup bug, a test with the input that broke it is the most helpful thing to add.

## Pull requests

Small and focused is easiest to review. For big changes, open an issue first so we can talk it
through. Please keep it standard library only.

Everyone taking part is expected to follow the [code of conduct](CODE_OF_CONDUCT.md).
