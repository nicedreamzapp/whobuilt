"""Manifest parsing and the project walk (whobuilt/scan.py)."""

import os
import unittest

from whobuilt import scan

from .util import TempProject


class NormTest(unittest.TestCase):
    def test_strips_version_specifiers_extras_and_markers(self):
        cases = {
            "requests": "requests",
            "Requests>=2.0": "requests",
            "numpy==1.26.4": "numpy",
            "torch~=2.1": "torch",
            "foo!=1.0": "foo",
            "bar<3": "bar",
            "uvicorn[standard]>=0.20": "uvicorn",
            'pywin32; sys_platform == "win32"': "pywin32",
            "mlx @ git+https://github.com/ml-explore/mlx": "mlx",
            "  padded  ": "padded",
        }
        for raw, want in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(scan._norm(raw), want)


class RequirementsTest(TempProject):
    def test_reads_names_and_skips_options_urls_and_comments(self):
        p = self.write("requirements.txt", """\
            # a comment
            numpy>=1.26  # trailing comment
            Pillow

            -r other.txt
            -e .
            --index-url https://example.com/simple
            https://example.com/pkg.whl
            git+https://github.com/a/b
            ./local/pkg
            mlx-lm==0.19.0 \\
                --hash=sha256:abc
            """)
        self.assertEqual(scan.from_requirements(p), ["numpy", "pillow", "mlx-lm"])

    def test_missing_file_is_empty(self):
        self.assertEqual(scan.from_requirements(os.path.join(self.root, "nope.txt")), [])


class PyprojectTest(TempProject):
    def test_pep621_dependencies_list(self):
        p = self.write("pyproject.toml", """\
            [project]
            name = "demo"
            version = "0.1"
            requires-python = ">=3.12"
            dependencies = [
                "mlx>=0.20",
                'mlx-lm',
                "Requests",
            ]
            """)
        self.assertEqual(scan.from_pyproject(p), ["mlx", "mlx-lm", "requests"])

    def test_poetry_style_tables(self):
        p = self.write("pyproject.toml", """\
            [tool.poetry]
            name = "demo"
            version = "0.1.0"
            description = "x"

            [tool.poetry.dependencies]
            python = "^3.12"
            numpy = "^1.26"
            torch = { version = "^2.1", optional = true }
            """)
        self.assertEqual(scan.from_pyproject(p), ["numpy", "torch"])

    def test_no_dependencies(self):
        p = self.write("pyproject.toml", '[project]\nname = "demo"\nversion = "1"\n')
        self.assertEqual(scan.from_pyproject(p), [])


class PackageJsonTest(TempProject):
    def test_dependencies_and_peer_dependencies_only(self):
        p = self.write("package.json", """\
            {"name": "demo",
             "dependencies": {"react": "^18", "@scope/pkg": "1"},
             "peerDependencies": {"react-dom": "^18"},
             "devDependencies": {"jest": "^29"},
             "optionalDependencies": {"fsevents": "*"}}
            """)
        self.assertEqual(scan.from_package_json(p), ["react", "@scope/pkg", "react-dom"])

    def test_invalid_json_is_skipped(self):
        p = self.write("package.json", "{ not json")
        self.assertEqual(scan.from_package_json(p), [])

    def test_null_sections_are_ignored(self):
        p = self.write("package.json", '{"dependencies": null}')
        self.assertEqual(scan.from_package_json(p), [])


class CargoTest(TempProject):
    def test_dependencies_table_only(self):
        p = self.write("Cargo.toml", """\
            [package]
            name = "demo"
            version = "0.1.0"

            [dependencies]
            serde = { version = "1", features = ["derive"] }
            Tokio = "1"
            rand_core = "0.6"

            [dev-dependencies]
            criterion = "0.5"
            """)
        self.assertEqual(scan.from_cargo(p), ["serde", "tokio", "rand_core"])

    def test_dependencies_table_at_end_of_file(self):
        p = self.write("Cargo.toml", '[package]\nname = "x"\n\n[dependencies]\nanyhow = "1"\n')
        self.assertEqual(scan.from_cargo(p), ["anyhow"])

    def test_no_dependencies_table(self):
        p = self.write("Cargo.toml", '[package]\nname = "x"\n')
        self.assertEqual(scan.from_cargo(p), [])


class GitSlugTest(TempProject):
    def test_https_and_ssh_remotes(self):
        cases = {
            "https://github.com/ml-explore/mlx.git": "ml-explore/mlx",
            "https://github.com/ml-explore/mlx-lm": "ml-explore/mlx-lm",
            "git@github.com:Blaizzy/mlx-vlm.git": "Blaizzy/mlx-vlm",
        }
        for i, (url, want) in enumerate(cases.items()):
            with self.subTest(url=url):
                self.git_checkout(f"c{i}", url)
                self.assertEqual(scan.git_slug(os.path.join(self.root, f"c{i}")), want)

    def test_non_github_remote(self):
        self.git_checkout("c", "https://gitlab.com/a/b.git")
        self.assertIsNone(scan.git_slug(os.path.join(self.root, "c")))

    def test_not_a_checkout(self):
        self.assertIsNone(scan.git_slug(self.root))

    def test_config_without_url(self):
        self.write("c/.git/config", "[core]\n\tbare = false\n")
        self.assertIsNone(scan.git_slug(os.path.join(self.root, "c")))


class FromImportsTest(TempProject):
    def test_third_party_imports_mapped_to_pypi_names(self):
        # Built line by line so whobuilt run on its own repo doesn't read these as imports.
        self.write("app.py", "\n".join([
            "import os",
            "import sys, json",
            "from pathlib import Path",
            "import numpy as np",
            "from PIL import Image",
            "import cv2",
            "from mlx_lm import load",
            "import _private",
            "from . import sibling",
            "from helpers import thing",
        ]))
        self.write("helpers.py", "import yaml\n")
        self.assertEqual(scan.from_imports(self.root, 4),
                         ["mlx-lm", "numpy", "opencv-python", "pillow", "pyyaml"])

    def test_skips_vendored_and_hidden_folders(self):
        self.write("main.py", "import requests\n")
        self.write("node_modules/x/y.py", "import leftpad\n")
        self.write(".venv/lib/z.py", "import flask\n")
        self.write(".hidden/z.py", "import django\n")
        self.assertEqual(scan.from_imports(self.root, 4), ["requests"])

    def test_respects_depth(self):
        self.write("a.py", "import alpha\n")
        self.write("one/b.py", "import beta\n")
        self.write("one/two/c.py", "import gamma\n")
        self.assertEqual(scan.from_imports(self.root, 1), ["alpha"])
        self.assertEqual(scan.from_imports(self.root, 2), ["alpha", "beta"])
        self.assertEqual(scan.from_imports(self.root, 3), ["alpha", "beta", "gamma"])

    def test_file_limit(self):
        for i in range(5):
            self.write(f"m{i}.py", f"import pkg{i}\n")
        self.assertEqual(len(scan.from_imports(self.root, 4, limit=2)), 2)


class ScanTest(TempProject):
    def test_empty_project(self):
        found, inferred = scan.scan(self.root)
        self.assertEqual(found, {"pypi": [], "npm": [], "cargo": [],
                                 "github": [], "huggingface": []})
        self.assertEqual(inferred, set())

    def test_collects_every_manifest_kind_and_dedupes(self):
        self.write("requirements.txt", "numpy\nmlx\n")
        self.write("requirements-dev.txt", "numpy\npytest\n")
        self.write("web/package.json", '{"dependencies": {"react": "1", "tslib": "2"}}')
        self.write("native/Cargo.toml", '[dependencies]\nserde = "1"\n')
        found, inferred = scan.scan(self.root)
        self.assertEqual(sorted(found["pypi"]), ["mlx", "numpy", "pytest"])
        self.assertEqual(found["npm"], ["react"])          # tslib is BORING
        self.assertEqual(found["cargo"], ["serde"])
        self.assertEqual(inferred, set())

    def test_boring_packages_are_dropped(self):
        self.write("requirements.txt", "setuptools\nwheel\ncertifi\nmlx\n")
        found, _ = scan.scan(self.root)
        self.assertEqual(found["pypi"], ["mlx"])

    def test_skipped_folders_are_not_read(self):
        self.write("node_modules/dep/package.json", '{"dependencies": {"left-pad": "1"}}')
        self.write("venv/requirements.txt", "flask\n")
        self.write("requirements.txt", "mlx\n")
        found, _ = scan.scan(self.root)
        self.assertEqual(found["pypi"], ["mlx"])
        self.assertEqual(found["npm"], [])

    def test_nested_checkout_is_credited_and_not_descended(self):
        self.write("requirements.txt", "mlx\n")
        self.git_checkout("third_party/mlx-vlm", "https://github.com/Blaizzy/mlx-vlm.git")
        self.write("third_party/mlx-vlm/sub/requirements.txt", "should-not-appear\n")
        found, _ = scan.scan(self.root)
        self.assertEqual(found["github"], ["Blaizzy/mlx-vlm"])
        self.assertNotIn("should-not-appear", found["pypi"])

    def test_own_repo_is_not_credited(self):
        self.write("requirements.txt", "mlx\n")
        self.git_checkout(".", "https://github.com/nicedreamzapp/whobuilt.git")
        self.git_checkout("copy", "https://github.com/nicedreamzapp/whobuilt")
        found, _ = scan.scan(self.root)
        self.assertEqual(found["github"], [])

    def test_hugging_face_snapshot(self):
        self.write("requirements.txt", "mlx-lm\n")
        self.write("models/models--mlx-community--Qwen2.5-7B-Instruct-4bit/snapshots/"
                   "0123abcd/config.json", "{}")
        found, _ = scan.scan(self.root, max_depth=6)
        self.assertEqual(found["huggingface"], ["mlx-community/Qwen2.5-7B-Instruct-4bit"])

    def test_import_fallback_only_without_manifest(self):
        self.write("tool.py", "import numpy\nimport mlx\n")
        found, inferred = scan.scan(self.root)
        self.assertEqual(sorted(found["pypi"]), ["mlx", "numpy"])
        self.assertEqual(inferred, {"mlx", "numpy"})

        self.write("requirements.txt", "requests\n")
        found, inferred = scan.scan(self.root)
        self.assertEqual(found["pypi"], ["requests"])
        self.assertEqual(inferred, set())

    def test_depth_limits_manifests(self):
        self.write("requirements.txt", "a\n")
        self.write("x/requirements.txt", "b\n")
        self.write("x/y/requirements.txt", "c\n")
        self.assertEqual(scan.scan(self.root, 0)[0]["pypi"], [])
        self.assertEqual(scan.scan(self.root, 1)[0]["pypi"], ["a"])
        self.assertEqual(sorted(scan.scan(self.root, 2)[0]["pypi"]), ["a", "b"])
        self.assertEqual(sorted(scan.scan(self.root, 3)[0]["pypi"]), ["a", "b", "c"])


class SelfScanTest(unittest.TestCase):
    def test_this_repo_has_nothing_to_credit(self):
        # CREDITS.md promises that whobuilt run on itself finds no dependencies.
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        found, inferred = scan.scan(repo)
        self.assertEqual({k: v for k, v in found.items() if v}, {})
        self.assertEqual(inferred, set())


if __name__ == "__main__":
    unittest.main()
