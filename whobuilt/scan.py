"""Find what a project depends on, from whatever manifests it happens to have."""

import json
import os
import re
import sys

SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", "site-packages",
        "dist", "build", ".next", "target", ".cache", "vendor"}

# Things that are in everyone's tree and tell you nothing about the project.
BORING = {
    "pypi": {"setuptools", "wheel", "pip", "six", "packaging", "typing-extensions",
             "certifi", "charset-normalizer", "idna", "urllib3", "python-dateutil",
             "pytz", "attrs", "zipp", "importlib-metadata", "tomli", "colorama"},
    "npm": {"tslib", "@types/node", "typescript"},
    "cargo": set(),
}


def _read(p, limit=200000):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def _norm(name):
    return re.split(r"[<>=!~;\[\s]", name.strip(), 1)[0].strip().lower()


def from_requirements(path):
    out = []
    for line in _read(path).splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith(("-", "http", "git+", ".")):
            continue
        n = _norm(line)
        if n:
            out.append(n)
    return out


def from_pyproject(path):
    txt = _read(path)
    out = []
    # dependencies = [ "foo>=1", ... ] — deliberately not adding a TOML dependency
    # to a tool whose whole point is being honest about dependencies.
    for block in re.findall(r"dependencies\s*=\s*\[(.*?)\]", txt, re.S):
        for m in re.findall(r'"([^"]+)"|\'([^\']+)\'', block):
            n = _norm(m[0] or m[1])
            if n:
                out.append(n)
    for m in re.findall(r'^\s*([A-Za-z0-9_.-]+)\s*=\s*["\{]', txt, re.M):
        if m.lower() not in ("python", "name", "version", "description", "readme",
                             "requires-python", "license", "authors"):
            out.append(m.lower())
    return out


def from_package_json(path):
    try:
        d = json.loads(_read(path))
    except json.JSONDecodeError:
        return []
    out = []
    for key in ("dependencies", "peerDependencies"):
        out += list((d.get(key) or {}).keys())
    return out


def from_cargo(path):
    txt = _read(path)
    m = re.search(r"\[dependencies\](.*?)(\n\[|\Z)", txt, re.S)
    if not m:
        return []
    return [x.lower() for x in re.findall(r"^\s*([A-Za-z0-9_-]+)\s*=", m.group(1), re.M)]


# Plenty of real projects — research code, hobby code, anything that grew rather than
# being planned — have no manifest at all. Reading the imports is the only way to credit
# anyone for those, and they're often the projects most in need of it.
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)

# pip name != import name in a handful of common cases.
IMPORT_TO_PYPI = {
    "cv2": "opencv-python", "PIL": "pillow", "sklearn": "scikit-learn",
    "yaml": "pyyaml", "bs4": "beautifulsoup4", "dotenv": "python-dotenv",
    "serial": "pyserial", "OpenSSL": "pyopenssl", "dateutil": "python-dateutil",
    "google": "google-api-python-client", "websocket": "websocket-client",
    "PyQt5": "pyqt5", "skimage": "scikit-image", "mlx_lm": "mlx-lm",
}


def from_imports(root, max_depth, limit=4000):
    """Third-party top-level imports across the .py files in a project."""
    try:
        stdlib = set(sys.stdlib_module_names)          # 3.10+
    except AttributeError:                              # pragma: no cover
        stdlib = set()
    names, seen_files = set(), 0
    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath[len(root):].count(os.sep) >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith(".py") or seen_files >= limit:
                continue
            seen_files += 1
            for m in IMPORT_RE.findall(_read(os.path.join(dirpath, fn), 60000)):
                if m in stdlib or m.startswith("_"):
                    continue
                names.add(IMPORT_TO_PYPI.get(m, m.lower()))
    # anything that's a directory or .py file right here is the project's own code
    local = {p.split(".")[0].lower() for p in os.listdir(root)} if os.path.isdir(root) else set()
    return sorted(n for n in names if n not in local)


def git_slug(d):
    cfg = os.path.join(d, ".git", "config")
    if not os.path.exists(cfg):
        return None
    m = re.search(r"url\s*=\s*(\S+)", _read(cfg, 20000))
    if not m:
        return None
    g = re.search(r"github\.com[:/]+([^/\s]+)/([^/\s]+)", m.group(1))
    return f"{g.group(1)}/{re.sub(r'.git$', '', g.group(2))}" if g else None


HF_SNAPSHOT = re.compile(r"models--([^/]+)--([^/]+)/snapshots/[0-9a-f]{6,}")


def scan(root, max_depth=4):
    """Return {kind: [names]} for everything this project leans on."""
    root = os.path.abspath(os.path.expanduser(root))
    found = {"pypi": [], "npm": [], "cargo": [], "github": [], "huggingface": []}
    own_slug = git_slug(root)

    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath[len(root):].count(os.sep) >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]

        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if fn == "requirements.txt" or re.match(r"requirements.*\.txt$", fn):
                found["pypi"] += from_requirements(p)
            elif fn == "pyproject.toml":
                found["pypi"] += from_pyproject(p)
            elif fn == "package.json":
                found["npm"] += from_package_json(p)
            elif fn == "Cargo.toml":
                found["cargo"] += from_cargo(p)

        # a checkout of someone else's project living inside yours
        if dirpath != root and os.path.isdir(os.path.join(dirpath, ".git")):
            s = git_slug(dirpath)
            if s and s != own_slug:
                found["github"].append(s)
            dirnames[:] = []
            continue

        m = HF_SNAPSHOT.search(dirpath.replace(os.sep, "/"))
        if m:
            found["huggingface"].append(f"{m.group(1)}/{m.group(2)}")
            dirnames[:] = []

    # No manifest anywhere? Fall back to reading the imports. These are GUESSES —
    # an import name is not a package name, and PyPI is full of unrelated projects that
    # happen to own a common word. `comfy` on PyPI is a config library, not ComfyUI.
    # Crediting the wrong person is worse than crediting nobody, so they stay marked.
    inferred = set()
    if not any(found[k] for k in ("pypi", "npm", "cargo")):
        guesses = from_imports(root, max_depth)
        found["pypi"] += guesses
        inferred = set(guesses)

    for kind in found:
        seen, uniq = set(), []
        for n in found[kind]:
            if n in BORING.get(kind, set()) or n in seen:
                continue
            seen.add(n)
            uniq.append(n)
        found[kind] = uniq
    return found, inferred
