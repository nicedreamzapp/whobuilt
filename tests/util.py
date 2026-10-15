import os
import shutil
import tempfile
import textwrap
import unittest


class TempProject(unittest.TestCase):
    """A throwaway project folder per test."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="whobuilt-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write(self, rel, text=""):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(text))
        return path

    def git_checkout(self, rel, url):
        """A folder that looks like a git clone of `url`."""
        return self.write(os.path.join(rel, ".git", "config"),
                          f'[core]\n\tbare = false\n[remote "origin"]\n\turl = {url}\n')
