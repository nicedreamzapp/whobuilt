"""Registry and GitHub lookups (whobuilt/resolve.py), with every HTTP call faked."""

import io
import json
import os
import subprocess
import unittest
import urllib.error
from unittest import mock

from whobuilt import resolve


class FakeWeb:
    """Stands in for resolve._get: a dict of URL -> parsed JSON, recording every call."""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def __call__(self, url, headers=None):
        self.calls.append(url)
        return self.pages.get(url)


class ResolveTestCase(unittest.TestCase):
    def setUp(self):
        resolve._CACHE.clear()
        resolve._TOKEN = None
        self.addCleanup(resolve._CACHE.clear)
        self.addCleanup(setattr, resolve, "_TOKEN", None)

    def web(self, pages):
        fake = FakeWeb(pages)
        p = mock.patch.object(resolve, "_get", fake)
        p.start()
        self.addCleanup(p.stop)
        return fake


class GithubSlugTest(unittest.TestCase):
    def test_variants(self):
        cases = {
            "https://github.com/ml-explore/mlx": "ml-explore/mlx",
            "https://github.com/ml-explore/mlx.git": "ml-explore/mlx",
            "git+https://github.com/ml-explore/mlx-lm.git": "ml-explore/mlx-lm",
            "git://github.com/a/b.git": "a/b",
            "git@github.com:Blaizzy/mlx-vlm.git": "Blaizzy/mlx-vlm",
            "https://github.com/numpy/numpy/tree/main/doc": "numpy/numpy",
            "https://github.com/a/b#readme": "a/b",
            "https://github.com/a/b?tab=readme": "a/b",
            "https://www.github.com/a/b": "a/b",
        }
        for url, want in cases.items():
            with self.subTest(url=url):
                self.assertEqual(resolve.github_slug(url), want)

    def test_not_github(self):
        for url in (None, "", "https://gitlab.com/a/b", "https://numpy.org",
                    "https://github.com/onlyowner"):
            with self.subTest(url=url):
                self.assertIsNone(resolve.github_slug(url))


class PypiRepoTest(ResolveTestCase):
    URL = "https://pypi.org/pypi/{}/json"

    def test_lowercase_source_key(self):
        self.web({self.URL.format("numpy"): {"info": {
            "summary": "Fundamental package for array computing in Python",
            "project_urls": {"Homepage": "https://numpy.org",
                             "source": "https://github.com/numpy/numpy"}}}})
        self.assertEqual(resolve.pypi_repo("numpy"),
                         ("numpy/numpy", "Fundamental package for array computing in Python"))

    def test_prefers_source_over_homepage(self):
        self.web({self.URL.format("x"): {"info": {"summary": "s", "project_urls": {
            "Homepage": "https://github.com/someone/website",
            "Source Code": "https://github.com/someone/x"}}}})
        self.assertEqual(resolve.pypi_repo("x")[0], "someone/x")

    def test_falls_back_to_home_page_then_any_url(self):
        self.web({
            self.URL.format("a"): {"info": {"home_page": "https://github.com/o/a",
                                            "project_urls": None}},
            self.URL.format("b"): {"info": {"project_urls": {
                "Docs": "https://b.readthedocs.io",
                "Tracker": "https://github.com/o/b/issues"}}},
        })
        self.assertEqual(resolve.pypi_repo("a")[0], "o/a")
        self.assertEqual(resolve.pypi_repo("b")[0], "o/b")

    def test_no_github_link_keeps_summary(self):
        self.web({self.URL.format("c"): {"info": {"summary": "only docs",
                                                  "project_urls": {"Docs": "https://c.dev"}}}})
        self.assertEqual(resolve.pypi_repo("c"), (None, "only docs"))

    def test_unknown_package(self):
        self.web({})
        self.assertEqual(resolve.pypi_repo("does-not-exist"), (None, None))


class NpmRepoTest(ResolveTestCase):
    def test_latest_version_repository(self):
        self.web({"https://registry.npmjs.org/react": {
            "dist-tags": {"latest": "18.3.1"},
            "versions": {"18.3.1": {
                "description": "React is a JavaScript library for building user interfaces.",
                "repository": {"type": "git", "url": "git+https://github.com/facebook/react.git"},
            }}}})
        slug, desc = resolve.npm_repo("react")
        self.assertEqual(slug, "facebook/react")
        self.assertTrue(desc.startswith("React is"))

    def test_scoped_name_keeps_at_and_slash(self):
        web = self.web({"https://registry.npmjs.org/@scope/pkg": {
            "repository": "https://github.com/scope/pkg", "description": "d"}})
        self.assertEqual(resolve.npm_repo("@scope/pkg"), ("scope/pkg", "d"))
        self.assertEqual(web.calls, ["https://registry.npmjs.org/@scope/pkg"])

    def test_unknown_package(self):
        self.web({})
        self.assertEqual(resolve.npm_repo("nope"), (None, None))


class CrateRepoTest(ResolveTestCase):
    def test_repository_then_homepage(self):
        base = "https://crates.io/api/v1/crates/"
        self.web({
            base + "serde": {"crate": {"repository": "https://github.com/serde-rs/serde",
                                       "description": "A serialization framework"}},
            base + "x": {"crate": {"repository": None, "homepage": "https://github.com/o/x"}},
        })
        self.assertEqual(resolve.crate_repo("serde"), ("serde-rs/serde", "A serialization framework"))
        self.assertEqual(resolve.crate_repo("x"), ("o/x", None))

    def test_unknown_crate(self):
        self.web({})
        self.assertEqual(resolve.crate_repo("nope"), (None, None))


class HuggingFaceTest(ResolveTestCase):
    def test_author_and_license(self):
        self.web({"https://huggingface.co/api/models/mlx-community/m": {
            "author": "mlx-community", "cardData": {"license": "apache-2.0"}}})
        self.assertEqual(resolve.hf_author("mlx-community/m"), ("mlx-community", "apache-2.0"))

    def test_missing_card(self):
        self.web({"https://huggingface.co/api/models/o/m": {"author": "o"}})
        self.assertEqual(resolve.hf_author("o/m"), ("o", None))


class ContributorsTest(ResolveTestCase):
    URL = "https://api.github.com/repos/o/r/contributors?per_page=25"

    def test_top_humans_bots_filtered(self):
        self.web({self.URL: [
            {"login": "dependabot[bot]", "type": "Bot", "contributions": 900},
            {"login": "alice", "type": "User", "contributions": 500},
            {"login": "ci-bot", "type": "User", "contributions": 400},
            {"login": "renovate[bot]", "type": "User", "contributions": 300},
            {"login": "bob", "type": "User", "contributions": 200},
            {"login": "org-account", "type": "Organization", "contributions": 150},
            {"login": "carol", "type": "User", "contributions": 100},
            {"login": "dave", "type": "User", "contributions": 50},
            {"login": "erin", "type": "User", "contributions": 10},
        ]})
        people = resolve.contributors("o/r")
        self.assertEqual([p["login"] for p in people], ["alice", "bob", "carol", "dave"])
        self.assertEqual(people[0]["commits"], 500)

    def test_top_argument(self):
        self.web({self.URL: [{"login": f"u{i}", "type": "User"} for i in range(10)]})
        self.assertEqual(len(resolve.contributors("o/r", top=2)), 2)

    def test_error_payload_is_not_a_list(self):
        self.web({self.URL: {"message": "API rate limit exceeded"}})
        self.assertEqual(resolve.contributors("o/r"), [])


class HumanizeTest(ResolveTestCase):
    def test_display_name(self):
        self.web({"https://api.github.com/users/a": {"name": "  Ada Lovelace "},
                  "https://api.github.com/users/b": {"name": ""},
                  "https://api.github.com/users/c": {"name": None}})
        self.assertEqual(resolve.humanize("a"), "Ada Lovelace")
        self.assertIsNone(resolve.humanize("b"))
        self.assertIsNone(resolve.humanize("c"))
        self.assertIsNone(resolve.humanize("missing"))


class RepoMetaTest(ResolveTestCase):
    def test_fields(self):
        self.web({"https://api.github.com/repos/ml-explore/mlx": {
            "description": "MLX: An array framework for Apple silicon",
            "license": {"spdx_id": "MIT"}, "stargazers_count": 123,
            "owner": {"login": "ml-explore", "type": "Organization"}}})
        self.assertEqual(resolve.repo_meta("ml-explore/mlx"), {
            "description": "MLX: An array framework for Apple silicon", "license": "MIT",
            "stars": 123, "org": "ml-explore", "is_org": True})

    def test_missing_license_and_owner(self):
        self.web({"https://api.github.com/repos/o/r": {"license": None}})
        meta = resolve.repo_meta("o/r")
        self.assertIsNone(meta["license"])
        self.assertIsNone(meta["org"])
        self.assertFalse(meta["is_org"])

    def test_unreachable(self):
        self.web({})
        self.assertEqual(resolve.repo_meta("o/r"), {})


class ResolveTest(ResolveTestCase):
    def test_pypi_end_to_end(self):
        self.web({
            "https://pypi.org/pypi/mlx/json": {"info": {
                "summary": "", "project_urls": {"Repository": "https://github.com/ml-explore/mlx"}}},
            "https://api.github.com/repos/ml-explore/mlx": {
                "description": "An array framework", "license": {"spdx_id": "MIT"},
                "stargazers_count": 10, "owner": {"login": "ml-explore", "type": "Organization"}},
            "https://api.github.com/repos/ml-explore/mlx/contributors?per_page=25": [
                {"login": "alice", "type": "User", "contributions": 9},
                {"login": "bob", "type": "User", "contributions": 3}],
            "https://api.github.com/users/alice": {"name": "Alice A"},
            "https://api.github.com/users/bob": {"name": None},
        })
        r = resolve.resolve("mlx", "pypi")
        self.assertEqual(r["slug"], "ml-explore/mlx")
        self.assertEqual(r["url"], "https://github.com/ml-explore/mlx")
        self.assertEqual(r["summary"], "An array framework")   # empty PyPI summary -> repo's
        self.assertEqual((r["license"], r["org"], r["stars"], r["is_org"]),
                         ("MIT", "ml-explore", 10, True))
        self.assertEqual(r["people"], [
            {"login": "alice", "commits": 9, "name": "Alice A"},
            {"login": "bob", "commits": 3, "name": None}])

    def test_registry_summary_wins_over_repo_description(self):
        self.web({
            "https://crates.io/api/v1/crates/serde": {"crate": {
                "repository": "https://github.com/serde-rs/serde", "description": "from crates"}},
            "https://api.github.com/repos/serde-rs/serde": {"description": "from github"},
        })
        self.assertEqual(resolve.resolve("serde", "cargo")["summary"], "from crates")

    def test_npm_dispatch(self):
        web = self.web({})
        r = resolve.resolve("react", "npm")
        self.assertEqual(web.calls, ["https://registry.npmjs.org/react"])
        self.assertIsNone(r["slug"])

    def test_untraceable(self):
        web = self.web({})
        r = resolve.resolve("ghost", "pypi")
        self.assertEqual(r, {"name": "ghost", "kind": "pypi", "slug": None, "summary": None,
                             "people": [], "license": None, "org": None, "stars": None,
                             "url": None})
        self.assertEqual(web.calls, ["https://pypi.org/pypi/ghost/json"])  # no GitHub calls

    def test_vendored_github_checkout_skips_registries(self):
        web = self.web({})
        r = resolve.resolve("Blaizzy/mlx-vlm", "github")
        self.assertEqual(r["slug"], "Blaizzy/mlx-vlm")
        self.assertEqual(r["url"], "https://github.com/Blaizzy/mlx-vlm")
        self.assertTrue(all(u.startswith("https://api.github.com/") for u in web.calls))

    def test_hugging_face(self):
        self.web({"https://huggingface.co/api/models/mlx-community/m": {
            "author": "mlx-community", "cardData": {"license": "mit"}}})
        r = resolve.resolve("mlx-community/m", "huggingface")
        self.assertEqual(r["org"], "mlx-community")
        self.assertEqual(r["license"], "mit")
        self.assertEqual(r["people"], [])
        self.assertEqual(r["url"], "https://huggingface.co/mlx-community/m")


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class GetTest(ResolveTestCase):
    """The one function that talks to the network, with urlopen replaced."""

    def setUp(self):
        super().setUp()
        resolve._TOKEN = ""      # no token unless a test sets one

    def urlopen(self, payload=None, error=None):
        def fake(req, timeout=None):
            fake.requests.append(req)
            if error:
                raise error
            return FakeResponse(payload if isinstance(payload, bytes)
                                else json.dumps(payload).encode())
        fake.requests = []
        p = mock.patch("urllib.request.urlopen", fake)
        p.start()
        self.addCleanup(p.stop)
        return fake

    def test_parses_json_and_sets_user_agent(self):
        fake = self.urlopen({"ok": True})
        self.assertEqual(resolve._get("https://pypi.org/pypi/x/json"), {"ok": True})
        req = fake.requests[0]
        self.assertEqual(req.get_header("User-agent"), resolve.UA)
        self.assertIsNone(req.get_header("Authorization"))

    def test_caches_by_url(self):
        fake = self.urlopen({"n": 1})
        resolve._get("https://example.org/a")
        resolve._get("https://example.org/a")
        self.assertEqual(len(fake.requests), 1)

    def test_failures_become_none_and_are_cached(self):
        errors = [
            urllib.error.HTTPError("https://x", 404, "Not Found", {}, None),
            urllib.error.URLError("no route"),
            TimeoutError(),
            OSError("reset"),
        ]
        for i, err in enumerate(errors):
            with self.subTest(err=type(err).__name__):
                fake = self.urlopen(error=err)
                url = f"https://example.org/{i}"
                self.assertIsNone(resolve._get(url))
                self.assertIsNone(resolve._get(url))
                self.assertEqual(len(fake.requests), 1)

    def test_invalid_json_becomes_none(self):
        self.urlopen(b"<html>rate limited</html>")
        self.assertIsNone(resolve._get("https://example.org/html"))

    def test_token_only_sent_to_github_api(self):
        resolve._TOKEN = "t0ken"
        fake = self.urlopen({})
        resolve._get("https://api.github.com/repos/o/r")
        resolve._get("https://pypi.org/pypi/x/json")
        self.assertEqual(fake.requests[0].get_header("Authorization"), "Bearer t0ken")
        self.assertIsNone(fake.requests[1].get_header("Authorization"))

    def test_rate_limit_left(self):
        self.urlopen({"resources": {"core": {"remaining": 42}}})
        self.assertEqual(resolve.rate_limit_left(), 42)

    def test_rate_limit_left_unavailable(self):
        self.urlopen(error=urllib.error.URLError("offline"))
        self.assertIsNone(resolve.rate_limit_left())


class GithubTokenTest(ResolveTestCase):
    def env(self, **values):
        p = mock.patch.dict(os.environ, values)
        p.start()
        self.addCleanup(p.stop)
        for k in ("GITHUB_TOKEN", "GH_TOKEN"):
            if k not in values:
                os.environ.pop(k, None)

    def gh(self, **kwargs):
        p = mock.patch("subprocess.run", **kwargs)
        m = p.start()
        self.addCleanup(p.stop)
        return m

    def test_github_token_env_first(self):
        self.env(GITHUB_TOKEN="from-github", GH_TOKEN="from-gh")
        run = self.gh()
        self.assertEqual(resolve._github_token(), "from-github")
        run.assert_not_called()

    def test_gh_token_env(self):
        self.env(GH_TOKEN="from-gh")
        self.gh()
        self.assertEqual(resolve._github_token(), "from-gh")

    def test_borrows_gh_cli_token(self):
        self.env()
        run = self.gh(return_value=subprocess.CompletedProcess([], 0, "cli-token\n", ""))
        self.assertEqual(resolve._github_token(), "cli-token")
        self.assertEqual(run.call_args.args[0], ["gh", "auth", "token"])

    def test_gh_not_logged_in(self):
        self.env()
        self.gh(return_value=subprocess.CompletedProcess([], 1, "", "not logged in"))
        self.assertIsNone(resolve._github_token())

    def test_gh_not_installed_or_hangs(self):
        for err in (FileNotFoundError("gh"), subprocess.TimeoutExpired("gh", 6)):
            with self.subTest(err=type(err).__name__):
                resolve._TOKEN = None
                self.env()
                self.gh(side_effect=err)
                self.assertIsNone(resolve._github_token())

    def test_looked_up_once_per_run(self):
        self.env()
        run = self.gh(return_value=subprocess.CompletedProcess([], 1, "", ""))
        resolve._github_token()
        resolve._github_token()
        self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
