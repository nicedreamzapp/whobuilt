"""Turn dependencies into the people who wrote them.

Every credits file in the world lists packages. Packages didn't write themselves. This
walks the same manifests everyone else reads, then keeps going: package registry → source
repository → the handful of humans with the most commits in it.

Public data only — GitHub handles and the display name people chose to put on their own
profile. No emails, no scraping, nothing a maintainer hasn't already published about
themselves.
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

UA = "whobuilt (+https://github.com/nicedreamzapp/whobuilt)"
TIMEOUT = 12
_CACHE = {}
_TOKEN = None


def _github_token():
    """Anonymous GitHub API access is 60 requests an hour, which one medium project
    burns through immediately — you get a credits file with nobody in it. A token takes
    it to 5,000. Use the environment if set, otherwise borrow the one `gh` already has,
    otherwise carry on unauthenticated and warn."""
    global _TOKEN
    if _TOKEN is not None:
        return _TOKEN or None
    _TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not _TOKEN:
        try:
            import subprocess
            r = subprocess.run(["gh", "auth", "token"], capture_output=True,
                               text=True, timeout=6)
            if r.returncode == 0:
                _TOKEN = r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return _TOKEN or None


def rate_limit_left():
    d = _get("https://api.github.com/rate_limit")
    try:
        return d["resources"]["core"]["remaining"]
    except (TypeError, KeyError):
        return None


def _get(url, headers=None):
    if url in _CACHE:
        return _CACHE[url]
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    if "api.github.com" in url:
        tok = _github_token()
        if tok:
            h["Authorization"] = f"Bearer {tok}"
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            out = json.load(r)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError, ValueError):
        out = None
    _CACHE[url] = out
    return out


# --------------------------------------------------------------- find the source repo

def github_slug(url):
    if not url:
        return None
    m = re.search(r"github\.com[:/]+([^/\s]+)/([^/\s#?]+)", str(url))
    if not m:
        return None
    return f"{m.group(1)}/{re.sub(r'\.git$', '', m.group(2))}"


def pypi_repo(name):
    """PyPI records the source repo inconsistently — check every field people use."""
    d = _get(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
    if not d:
        return None, None
    info = d.get("info") or {}
    urls = info.get("project_urls") or {}
    # Key casing is not consistent across PyPI — numpy publishes "source" lowercase while
    # most packages use "Source". Match case-insensitively, preferring the keys that
    # actually mean "the code lives here", then fall back to any GitHub URL at all.
    lower = {str(k).lower(): v for k, v in urls.items()}
    ordered = [lower.get(k) for k in
               ("source", "source code", "repository", "code", "github", "homepage")]
    ordered += [info.get("home_page"), info.get("package_url")]
    ordered += list(urls.values())          # last resort: anything pointing at GitHub
    for c in ordered:
        slug = github_slug(c)
        if slug:
            return slug, info.get("summary")
    return None, info.get("summary")


def npm_repo(name):
    d = _get(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@/')}")
    if not d:
        return None, None
    latest = (d.get("dist-tags") or {}).get("latest")
    meta = (d.get("versions") or {}).get(latest, {}) if latest else {}
    repo = (meta.get("repository") or d.get("repository") or {})
    url = repo.get("url") if isinstance(repo, dict) else repo
    return github_slug(url), (meta.get("description") or d.get("description"))


def crate_repo(name):
    d = _get(f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}")
    if not d:
        return None, None
    c = d.get("crate") or {}
    return github_slug(c.get("repository") or c.get("homepage")), c.get("description")


def hf_author(repo_id):
    d = _get(f"https://huggingface.co/api/models/{repo_id}")
    if not d:
        return None, None
    return d.get("author"), (d.get("cardData") or {}).get("license")


# ------------------------------------------------------------------- find the people

def contributors(slug, top=4):
    """The handful of humans with the most commits. Bots filtered out."""
    data = _get(f"https://api.github.com/repos/{slug}/contributors?per_page=25")
    if not isinstance(data, list):
        return []
    people = []
    for c in data:
        login = c.get("login") or ""
        if c.get("type") != "User" or login.endswith("[bot]") or login.endswith("-bot"):
            continue
        people.append({"login": login, "commits": c.get("contributions", 0)})
        if len(people) >= top:
            break
    return people


def humanize(login):
    """The display name someone chose to publish on their own profile, if any."""
    d = _get(f"https://api.github.com/users/{login}")
    if not d:
        return None
    name = (d.get("name") or "").strip()
    return name or None


def repo_meta(slug):
    d = _get(f"https://api.github.com/repos/{slug}")
    if not d:
        return {}
    return {
        "description": d.get("description"),
        "license": ((d.get("license") or {}).get("spdx_id") or None),
        "stars": d.get("stargazers_count"),
        "org": (d.get("owner") or {}).get("login"),
        "is_org": ((d.get("owner") or {}).get("type") == "Organization"),
    }


def resolve(name, kind):
    """One dependency -> everything we can honestly say about who made it."""
    slug = summary = None
    if kind == "pypi":
        slug, summary = pypi_repo(name)
    elif kind == "npm":
        slug, summary = npm_repo(name)
    elif kind == "cargo":
        slug, summary = crate_repo(name)
    elif kind == "github":
        slug = name
    elif kind == "huggingface":
        author, lic = hf_author(name)
        return {"name": name, "kind": kind, "slug": None, "org": author,
                "license": lic, "people": [], "summary": None,
                "url": f"https://huggingface.co/{name}"}

    out = {"name": name, "kind": kind, "slug": slug, "summary": summary,
           "people": [], "license": None, "org": None, "stars": None,
           "url": f"https://github.com/{slug}" if slug else None}
    if not slug:
        return out

    meta = repo_meta(slug)
    out.update({k: meta.get(k) for k in ("license", "org", "stars")})
    out["summary"] = out["summary"] or meta.get("description")
    out["is_org"] = meta.get("is_org", False)

    for p in contributors(slug):
        p["name"] = humanize(p["login"])
        out["people"].append(p)
    return out
