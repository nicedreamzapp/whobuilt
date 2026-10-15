"""The Markdown renderer and the command line (whobuilt/__main__.py)."""

import contextlib
import io
import os
import unittest
from unittest import mock

from whobuilt import __main__ as cli

from .util import TempProject


def result(name, kind="pypi", people=(), org=None, stars=None, summary=None, url=None):
    return {"name": name, "kind": kind, "people": list(people), "org": org,
            "stars": stars, "summary": summary,
            "url": url if url is not None else f"https://github.com/o/{name}"}


ALICE = {"login": "alice", "name": "Alice A"}
BOB = {"login": "bob", "name": None}


class PersonTest(unittest.TestCase):
    def test_display_name_or_handle(self):
        self.assertEqual(cli.person(ALICE), "[Alice A](https://github.com/alice)")
        self.assertEqual(cli.person(BOB), "[@bob](https://github.com/bob)")
        self.assertEqual(cli.person({"login": "c"}), "[@c](https://github.com/c)")


class RenderTest(unittest.TestCase):
    def test_header_and_footer(self):
        text = cli.render("demo", [], [])
        self.assertTrue(text.startswith("# 🙏 Whose work demo stands on\n"))
        self.assertIn("open an issue", text)
        self.assertNotIn("## ", text)

    def test_sections_in_fixed_order(self):
        results = [
            result("model", kind="huggingface", org="mlx-community"),
            result("o/vendored", kind="github", people=[ALICE]),
            result("serde", kind="cargo", people=[ALICE]),
            result("react", kind="npm", people=[ALICE]),
            result("mlx", kind="pypi", people=[ALICE]),
        ]
        text = cli.render("demo", results, [])
        order = [text.index(h) for h in ("## Python", "## JavaScript", "## Rust",
                                         "## Vendored source", "## Model weights")]
        self.assertEqual(order, sorted(order))

    def test_sorted_by_stars_descending(self):
        results = [result("small", people=[ALICE], stars=1),
                   result("unknown", people=[ALICE], stars=None),
                   result("big", people=[ALICE], stars=1000)]
        text = cli.render("demo", results, [])
        self.assertLess(text.index("[big]"), text.index("[small]"))
        self.assertLess(text.index("[small]"), text.index("[unknown]"))

    def test_entry_line(self):
        r = result("mlx", people=[ALICE, BOB], summary="An array framework. ")
        text = cli.render("demo", [r], [])
        self.assertIn("- **[mlx](https://github.com/o/mlx)** — An array framework\n", text)
        self.assertIn("  <br>Built by [Alice A](https://github.com/alice), "
                      "[@bob](https://github.com/bob).", text)
        self.assertNotIn("everyone else", text)

    def test_four_people_adds_everyone_else(self):
        people = [{"login": f"u{i}", "name": None} for i in range(4)]
        text = cli.render("demo", [result("mlx", people=people)], [])
        self.assertIn("and everyone else who has contributed.", text)

    def test_org_only_and_no_url(self):
        r = result("model", kind="huggingface", org="mlx-community", url="")
        text = cli.render("demo", [r], [])
        self.assertIn("model", text)
        self.assertNotIn("](", text.split("## Model weights")[1].split("---")[0])
        self.assertIn("  <br>By **mlx-community**.", text)

    def test_nobody_found_is_left_out_of_main_sections(self):
        text = cli.render("demo", [result("ghost")], ["ghost"])
        self.assertNotIn("## Python", text)
        self.assertIn("## Couldn't trace these", text)
        self.assertIn("> ghost", text)

    def test_thin_list_is_sorted(self):
        text = cli.render("demo", [], ["zeta", "alpha", "mid"])
        self.assertIn("> alpha, mid, zeta\n", text)

    def test_inferred_names_are_quarantined(self):
        results = [result("comfy", people=[ALICE], summary="config library"),
                   result("numpy", people=[BOB])]
        text = cli.render("demo", results, [], inferred={"comfy"})
        guessed = text.index("## Guessed from imports")
        self.assertLess(text.index("## Python"), guessed)
        self.assertGreater(text.index("[comfy]"), guessed)
        self.assertIn("  <br>Possibly [Alice A](https://github.com/alice).", text)
        self.assertNotIn("Built by [Alice A]", text)


class MainTest(TempProject):
    def run_cli(self, *argv, results=None):
        calls = []

        def fake_resolve(name, kind):
            calls.append((name, kind))
            return (results or {}).get(name, result(name, kind=kind, url=None))

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "resolve", fake_resolve), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue(), calls

    def test_no_dependencies(self):
        code, out, err, calls = self.run_cli(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertIn("No dependencies found", err)
        self.assertEqual(calls, [])

    def test_prints_credits(self):
        self.write("requirements.txt", "mlx\nghost\n")
        code, out, err, calls = self.run_cli(
            self.root, results={"mlx": result("mlx", people=[ALICE, BOB])})
        self.assertEqual(code, 0)
        self.assertEqual(sorted(calls), [("ghost", "pypi"), ("mlx", "pypi")])
        self.assertIn(f"# 🙏 Whose work {os.path.basename(self.root)} stands on", out)
        self.assertIn("Built by [Alice A]", out)
        self.assertIn("> ghost", out)
        self.assertIn("tracing 2 of 2 dependencies", err)
        self.assertIn("2 people named across 1 projects", err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "CREDITS.md")))

    def test_write(self):
        self.write("requirements.txt", "mlx\n")
        code, out, err, _ = self.run_cli(
            self.root, "--write", results={"mlx": result("mlx", people=[ALICE])})
        self.assertEqual((code, out), (0, ""))
        path = os.path.join(self.root, "CREDITS.md")
        self.assertIn(f"wrote {path}", err)
        with open(path, encoding="utf-8") as f:
            self.assertIn("Built by [Alice A]", f.read())

    def test_write_custom_name(self):
        self.write("requirements.txt", "mlx\n")
        os.makedirs(os.path.join(self.root, "docs"))
        self.run_cli(self.root, "--write", "-o", "docs/THANKS.md")
        self.assertTrue(os.path.exists(os.path.join(self.root, "docs", "THANKS.md")))

    def test_max_caps_lookups(self):
        self.write("requirements.txt", "a\nb\nc\nd\n")
        _, _, err, calls = self.run_cli(self.root, "--max", "2")
        self.assertEqual(calls, [("a", "pypi"), ("b", "pypi")])
        self.assertIn("tracing 2 of 4 dependencies", err)

    def test_depth_is_passed_to_scan(self):
        self.write("deep/er/requirements.txt", "mlx\n")
        _, _, err, calls = self.run_cli(self.root, "--depth", "2")
        self.assertEqual(calls, [])
        _, _, _, calls = self.run_cli(self.root, "--depth", "3")
        self.assertEqual(calls, [("mlx", "pypi")])

    def test_not_a_directory(self):
        missing = os.path.join(self.root, "missing")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            cli.main([missing])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("not a directory", err.getvalue())

    def test_defaults_to_current_directory(self):
        self.write("requirements.txt", "mlx\n")
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)
        _, _, _, calls = self.run_cli()
        self.assertEqual(calls, [("mlx", "pypi")])


if __name__ == "__main__":
    unittest.main()
