"""Refresh GitHub stars and skills.sh install counts.

Writes data/stats/latest.json and a dated copy in data/stats/history/.
Any value that can't be fetched keeps its previous value, so a flaky run
never wipes data. Set GITHUB_TOKEN to avoid the 60-requests/hour limit.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import date

import requests

from common import STATS, load_stats, load_yaml

UA = "awesome-web-scraping-skills-stats/1.0 (+https://github.com/The-Web-Scraping-Insider/awesome-web-scraping-skills)"


def gh_repo(session: requests.Session, repo: str) -> dict | None:
    r = session.get(f"https://api.github.com/repos/{repo}", timeout=20)
    if r.status_code != 200:
        print(f"  ! {repo}: GitHub {r.status_code}", file=sys.stderr)
        return None
    j = r.json()
    return {
        "stars": j.get("stargazers_count"),
        "pushed_at": j.get("pushed_at"),
        "archived": j.get("archived", False),
        "license": (j.get("license") or {}).get("spdx_id"),
    }


def parse_count(text: str) -> int | None:
    text = text.strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*([KkMm]?)$", text)
    if not m:
        return None
    n = float(m.group(1))
    mult = {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1)
    return int(n * mult)


def skills_sh_installs(session: requests.Session, path: str) -> int | None:
    """Best effort: read the install count shown on a skills.sh skill page."""
    try:
        r = session.get(f"https://skills.sh/{path}", timeout=20)
    except requests.RequestException as e:
        print(f"  ! skills.sh {path}: {e}", file=sys.stderr)
        return None
    if r.status_code != 200:
        print(f"  ! skills.sh {path}: HTTP {r.status_code}", file=sys.stderr)
        return None
    text = re.sub(r"<[^>]+>", "\n", r.text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        if line.lower() in ("installs", "weekly installs", "total installs") and i + 1 < len(lines):
            n = parse_count(lines[i + 1])
            if n is not None:
                return n
    print(f"  ! skills.sh {path}: install count not found", file=sys.stderr)
    return None


def main() -> None:
    skills = load_yaml("skills.yaml")
    prev = load_stats()
    repos = dict(prev.get("repos", {}))
    installs = dict(prev.get("installs", {}))

    gh = requests.Session()
    gh.headers.update({"Accept": "application/vnd.github+json", "User-Agent": UA})
    if os.environ.get("GITHUB_TOKEN"):
        gh.headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"

    for repo in sorted({s["repo"] for s in skills if s.get("repo")}):
        info = gh_repo(gh, repo)
        if info:
            repos[repo] = {**repos.get(repo, {}), **{k: v for k, v in info.items() if v is not None}}
            print(f"  {repo}: ⭐ {info['stars']}")

    web = requests.Session()
    web.headers.update({"User-Agent": UA})
    for s in skills:
        if not s.get("skills_sh"):
            continue
        n = skills_sh_installs(web, s["skills_sh"])
        if n is not None:
            installs[s["id"]] = n
            print(f"  {s['id']}: ⬇ {n}")
        time.sleep(1)  # be polite

    today = date.today().isoformat()
    out = {"updated": today, "repos": repos, "installs": installs}
    STATS.mkdir(parents=True, exist_ok=True)
    (STATS / "history").mkdir(exist_ok=True)
    payload = json.dumps(out, indent=2, sort_keys=True) + "\n"
    (STATS / "latest.json").write_text(payload, encoding="utf-8")
    (STATS / "history" / f"{today}.json").write_text(payload, encoding="utf-8")
    print(f"Saved stats for {len(repos)} repos and {len(installs)} install counts.")


if __name__ == "__main__":
    main()
