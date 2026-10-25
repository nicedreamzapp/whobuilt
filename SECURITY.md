# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report them privately through GitHub: go to the **Security** tab of this repo and click **Report a vulnerability** ([direct link](https://github.com/nicedreamzapp/whobuilt/security/advisories/new)). Only the maintainer sees the report.

Helpful details: what you found, how to reproduce it (a small sample project helps), which commit, and your Python version and OS.

I aim to reply within 3 days and to ship a fix or a clear plan within 30 days, depending on severity. You will be credited in the advisory unless you ask not to be.

## Supported versions

Fixes go into the latest version on `main`. Please update before reporting if you are on an older version.

## What matters most here

The parts where a mistake could hurt someone:

- GitHub token handling in `whobuilt/resolve.py`: it reads `GITHUB_TOKEN` or `GH_TOKEN`, or runs `gh auth token`, and must only ever send the token to `api.github.com`
- the manifest scanner in `whobuilt/scan.py`, which parses files from whatever project you point it at
- `--write` and `-o` in `whobuilt/__main__.py`, which write a file into the scanned project
- names and descriptions from PyPI, npm, crates.io, GitHub and Hugging Face, which end up as Markdown in the credits file
