# 🙏 Whose work whobuilt stands on

Awkwardly, almost nobody — this is Python's standard library and nothing else, so running
`whobuilt` on itself prints *"No dependencies found. Nothing to credit, which is its own
kind of achievement."*

That is deliberate. A tool that exists to name the people behind your dependencies should
be honest about having very few of its own.

What it does lean on:

| | |
|---|---|
| [PyPI](https://pypi.org), [npm](https://www.npmjs.com), [crates.io](https://crates.io) | Public registry APIs, free, no key, no rate-limit theatre |
| [GitHub REST API](https://docs.github.com/rest) | Contributor lists and profile display names |
| [Hugging Face Hub API](https://huggingface.co/docs/hub/api) | Model authorship |
| Python's standard library | Everything else — written by [thousands of volunteers](https://devguide.python.org/) over thirty years |

That last row is the one worth sitting with. `urllib`, `json`, `re` and
`concurrent.futures` are doing most of the work in this program, and no credits file
anywhere ever mentions them.

---

If your work is listed here and you'd like the wording changed, open an issue.
